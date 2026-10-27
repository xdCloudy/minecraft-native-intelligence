package dev.minecraftnativeintelligence;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import it.unimi.dsi.fastutil.ints.Int2ObjectMaps;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.Consumer;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.network.protocol.game.ServerboundContainerClickPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundPlayerInputPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.network.protocol.game.ServerboundUseItemPacket;
import net.minecraft.network.HashedStack;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.inventory.ContainerInput;

/**
 * Server-thread action ingress and control executor for an owned AI player.
 * The caller must build the validation context from authoritative server state.
 */
public final class AgentActionExecutor {
    public record Submission(boolean accepted, String reasonCode) {}

    public record Outcome(
            String agentId,
            long sessionEpoch,
            String requestId,
            String traceId,
            long sequence,
            long gameTick,
            String status,
            String reasonCode,
            String targetRequestId) {
        public Outcome(String agentId, long sessionEpoch, String requestId, String traceId,
                long sequence, long gameTick, String status, String reasonCode) {
            this(agentId, sessionEpoch, requestId, traceId, sequence, gameTick, status, reasonCode, null);
        }

        public JsonObject toJson() {
            JsonObject json = new JsonObject();
            json.addProperty("schema_version", "action-outcome.v0");
            json.addProperty("agent_id", this.agentId);
            json.addProperty("session_epoch", this.sessionEpoch);
            json.addProperty("request_id", this.requestId);
            json.addProperty("trace_id", this.traceId);
            json.addProperty("sequence", this.sequence);
            json.addProperty("game_tick", this.gameTick);
            json.addProperty("status", this.status);
            if (this.reasonCode != null) json.addProperty("reason_code", this.reasonCode);
            if (this.targetRequestId != null) {
                JsonObject result = new JsonObject();
                result.addProperty("target_request_id", this.targetRequestId);
                json.add("result", result);
            }
            return json;
        }
    }

    private record ActiveControl(
            ServerPlayer player,
            String agentId,
            long sessionEpoch,
            String requestId,
            String traceId,
            String actionType,
            JsonObject action,
            long deadlineGameTick,
            int durationTicks,
            Input input,
            boolean hasInput,
            boolean started,
            boolean stopSent,
            int startingFoodLevel,
            int startingStackCount,
            int ticksApplied) {}

    private record SessionKey(UUID agentUuid, long sessionEpoch) {}

    private final AgentPlayerManager players;
    private final Consumer<Outcome> outcomeSink;
    private final Map<UUID, ActiveControl> active = new HashMap<>();
    private final Map<SessionKey, Set<String>> seenRequestIds = new HashMap<>();
    private final Map<UUID, Long> outcomeSequences = new HashMap<>();
    private final Map<UUID, Integer> packetSequences = new HashMap<>();

    public AgentActionExecutor(AgentPlayerManager players, Consumer<Outcome> outcomeSink) {
        this.players = players;
        this.outcomeSink = outcomeSink;
    }

    /**
     * Validates and queues one request. Calls must run on the owned player's
     * server thread; the context is trusted server-built input, never request data.
     */
    public Submission submit(ServerPlayer player, String requestJson, ActionValidationContext context) {
        if (!this.players.owns(player)) return new Submission(false, "unauthorized_agent");
        if (context == null) return this.reject(player, 0, "", "", "invalid_validation_context");
        MinecraftServer server = player.level().getServer();
        if (!server.isSameThread()) throw new IllegalStateException("action submission must run on the server thread");

        JsonObject request = parseObject(requestJson);
        String requestId = stringField(request, "request_id");
        String traceId = stringField(request, "trace_id");
        String authoritativeAgentId = player.getGameProfile().id().toString();
        if (!authoritativeAgentId.equals(context.agentId())) {
            return this.reject(player, context.sessionEpoch(), requestId, traceId, "unauthorized_agent");
        }
        if (context.gameTick() != player.level().getGameTime()) {
            return this.reject(player, context.sessionEpoch(), requestId, traceId, "stale_validation_context");
        }
        SessionKey sessionKey = new SessionKey(player.getUUID(), context.sessionEpoch());
        if (!requestId.isBlank() && this.seenRequestIds
                .computeIfAbsent(sessionKey, ignored -> new HashSet<>()).contains(requestId)) {
            return this.reject(player, context.sessionEpoch(), requestId, traceId, "duplicate_request_id");
        }

        Set<String> seen = new HashSet<>(context.seenRequestIds());
        seen.addAll(this.seenRequestIds.getOrDefault(sessionKey, Set.of()));
        Set<String> activeIds = new HashSet<>(context.activeRequestIds());
        ActiveControl current = this.active.get(player.getUUID());
        if (current != null && current.agentId().equals(context.agentId())
                && current.sessionEpoch() == context.sessionEpoch()) {
            activeIds.add(current.requestId());
        }
        ActionValidationContext requestContext = copyWithRequestState(context, seen, activeIds);
        ActionRequestValidator.Result validation = ActionRequestValidator.validate(request, requestContext);
        if (!requestId.isBlank()) {
            this.seenRequestIds.computeIfAbsent(sessionKey, ignored -> new HashSet<>()).add(requestId);
        }
        if (!validation.accepted()) {
            return this.reject(player, context.sessionEpoch(), validation.requestId(), validation.traceId(), validation.reasonCode());
        }
        JsonObject action = request.getAsJsonObject("action");
        String type = stringField(action, "type");
        if (type.equals("cancel")) {
            return this.cancelActive(player, context.sessionEpoch(), requestId, traceId,
                    stringField(action, "target_request_id"));
        }
        if (this.active.containsKey(player.getUUID())) {
            return this.reject(player, context.sessionEpoch(), requestId, traceId, "action_conflict");
        }
        if (!Set.of("move", "look", "jump", "mine", "eat", "select_slot", "drop").contains(type)) {
            return this.reject(player, context.sessionEpoch(), requestId, traceId, "executor_action_unsupported");
        }
        boolean hasInput = type.equals("move") || type.equals("jump");
        Input input = hasInput ? inputFor(action, type) : Input.EMPTY;
        int durationTicks = type.equals("drop")
                ? (action.has("whole_stack") && action.get("whole_stack").getAsBoolean()
                        ? 1 : action.get("count").getAsInt())
                : type.equals("move")
                ? optionalInt(action, "duration_ticks", 1)
                : type.equals("jump") ? optionalInt(action, "hold_ticks", 1) : 1;
        long deadline = optionalLong(request, "deadline_game_tick", Long.MAX_VALUE);
        int startingFoodLevel = -1;
        int startingStackCount = -1;
        if (type.equals("eat")) {
            startingFoodLevel = player.getFoodData().getFoodLevel();
            startingStackCount = player.getItemInHand(handFor(action)).getCount();
        } else if (type.equals("drop")) {
            int slot = action.get("slot").getAsInt();
            ActionValidationContext.ItemState observed = context.inventory().get(slot);
            if (slot >= player.getInventory().getContainerSize() || observed == null) {
                return this.reject(player, context.sessionEpoch(), requestId, traceId, "inventory_precondition_failed");
            }
            startingStackCount = player.getInventory().getItem(slot).getCount();
            if (startingStackCount != observed.count()) {
                return this.reject(player, context.sessionEpoch(), requestId, traceId, "inventory_precondition_failed");
            }
        }
        this.active.put(player.getUUID(), new ActiveControl(player, authoritativeAgentId, context.sessionEpoch(),
                requestId, traceId, type, action, deadline, durationTicks, input, hasInput, false, false,
                startingFoodLevel, startingStackCount, 0));
        this.emit(player, authoritativeAgentId, context.sessionEpoch(), requestId, traceId, "accepted", null);
        return new Submission(true, "accepted");
    }

    /** Call from Fabric START_SERVER_TICK so vanilla consumes the input this tick. */
    public void startServerTick(MinecraftServer server) {
        requireServerThread(server);
        for (ActiveControl control : new ArrayList<>(this.active.values())) {
            ServerPlayer player = control.player();
            if (!player.isAlive() || player.connection == null) {
                this.finishRejected(control, "agent_unavailable");
                continue;
            }
            long gameTick = player.level().getGameTime();
            if (gameTick > control.deadlineGameTick()) {
                this.finishRejected(control, "deadline_expired");
                continue;
            }
            if (control.actionType().equals("mine") && control.started()
                    && player.level().getBlockState(blockPos(control.action())).isAir()) {
                this.finishCompleted(control);
                continue;
            }
            if (control.actionType().equals("eat") && control.started()) continue;
            // Vanilla ignores most gameplay packets until the initial client-load
            // timeout expires; carried-slot selection does not use that packet gate.
            if (!Set.of("select_slot", "drop").contains(control.actionType()) && !player.connection.hasClientLoaded()) continue;

            try {
                if (control.actionType().equals("drop")) {
                    this.executeDrop(control);
                    continue;
                } else if (control.actionType().equals("select_slot")) {
                    int slot = hotbarSlot(control.action());
                    player.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot));
                    if (player.getInventory().getSelectedSlot() != slot) {
                        this.finishRejected(control, "slot_selection_failed");
                        continue;
                    }
                    this.emit(player, control.agentId(), control.sessionEpoch(), control.requestId(), control.traceId(), "started", null);
                    this.finishCompleted(control);
                    continue;
                } else if (control.actionType().equals("mine")) {
                    BlockPos pos = blockPos(control.action());
                    if (!player.isWithinBlockInteractionRange(pos, 1.0)) {
                        this.sendBlockAction(player, pos, control.action(), ServerboundPlayerActionPacket.Action.ABORT_DESTROY_BLOCK);
                        this.finishRejected(control, "target_out_of_reach");
                        continue;
                    }
                    if (!control.started()) {
                        this.sendBlockAction(player, pos, control.action(), ServerboundPlayerActionPacket.Action.START_DESTROY_BLOCK);
                        this.emit(player, control.agentId(), control.sessionEpoch(), control.requestId(), control.traceId(), "started", null);
                    } else if (!control.stopSent()) {
                        this.sendBlockAction(player, pos, control.action(), ServerboundPlayerActionPacket.Action.STOP_DESTROY_BLOCK);
                    }
                } else if (control.actionType().equals("eat")) {
                    player.connection.handleUseItem(new ServerboundUseItemPacket(
                            handFor(control.action()), this.nextPacketSequence(player), player.getYRot(), player.getXRot()));
                    if (!player.isUsingItem()) {
                        this.finishRejected(control, "use_not_started");
                        continue;
                    }
                    this.emit(player, control.agentId(), control.sessionEpoch(), control.requestId(), control.traceId(), "started", null);
                } else if (control.actionType().equals("look")) {
                    player.connection.handleMovePlayer(new ServerboundMovePlayerPacket.Rot(
                            (float) control.action().get("yaw_degrees").getAsDouble(),
                            (float) control.action().get("pitch_degrees").getAsDouble(),
                            player.onGround(), player.horizontalCollision));
                } else {
                    player.connection.handlePlayerInput(new ServerboundPlayerInputPacket(control.input()));
                }
                if (!control.started() && !control.actionType().equals("mine") && !control.actionType().equals("eat")) {
                    this.emit(player, control.agentId(), control.sessionEpoch(), control.requestId(), control.traceId(), "started", null);
                }
                this.active.put(player.getUUID(), new ActiveControl(player, control.agentId(), control.sessionEpoch(),
                        control.requestId(), control.traceId(), control.actionType(), control.action(),
                        control.deadlineGameTick(), control.durationTicks(), control.input(), control.hasInput(), true,
                        control.actionType().equals("mine") ? (control.started() || control.stopSent()) : control.stopSent(),
                        control.startingFoodLevel(), control.startingStackCount(),
                        control.ticksApplied() + 1));
            } catch (RuntimeException failure) {
                this.finishRejected(control, "action_execution_failed");
            }
        }
    }

    /** Call from Fabric END_SERVER_TICK after the player has consumed this tick's input. */
    public void endServerTick(MinecraftServer server) {
        requireServerThread(server);
        for (ActiveControl control : new ArrayList<>(this.active.values())) {
            if (control.actionType().equals("mine")) {
                if (control.started() && control.player().level().getBlockState(blockPos(control.action())).isAir()) {
                    this.finishCompleted(control);
                }
                continue;
            }
            if (control.actionType().equals("eat")) {
                if (!control.started() || control.player().isUsingItem()) continue;
                int foodLevel = control.player().getFoodData().getFoodLevel();
                int handCount = control.player().getItemInHand(handFor(control.action())).getCount();
                if (foodLevel > control.startingFoodLevel() || handCount < control.startingStackCount()) {
                    this.finishCompleted(control);
                } else {
                    this.finishRejected(control, "use_had_no_effect");
                }
                continue;
            }
            if (!control.started() || control.ticksApplied() < control.durationTicks()) continue;
            if (control.hasInput() && control.player().connection != null) {
                control.player().connection.handlePlayerInput(new ServerboundPlayerInputPacket(releasedInput()));
            }
            this.active.remove(control.player().getUUID());
            this.emit(control.player(), control.agentId(), control.sessionEpoch(), control.requestId(), control.traceId(), "completed", null);
        }
    }

    public void removeAgent(ServerPlayer player) {
        ActiveControl control = this.active.remove(player.getUUID());
        if (control != null) this.finishRejected(control, "agent_unavailable");
        this.seenRequestIds.keySet().removeIf(key -> key.agentUuid().equals(player.getUUID()));
        this.outcomeSequences.remove(player.getUUID());
        this.packetSequences.remove(player.getUUID());
    }

    public void stop(MinecraftServer server) {
        requireServerThread(server);
        for (ActiveControl control : new ArrayList<>(this.active.values())) {
            this.finishRejected(control, "server_stopping");
        }
        this.seenRequestIds.clear();
        this.outcomeSequences.clear();
        this.packetSequences.clear();
    }

    private Submission reject(ServerPlayer player, long epoch, String requestId, String traceId, String reason) {
        if (!requestId.isBlank() && requestId.length() <= 128 && !traceId.isBlank() && traceId.length() <= 128) {
            this.emit(player, player.getGameProfile().id().toString(), epoch, requestId, traceId, "rejected", reason);
        }
        return new Submission(false, reason);
    }

    private void finishRejected(ActiveControl control, String reason) {
        if (control.actionType().equals("mine") && control.started() && control.player().connection != null) {
            this.sendBlockAction(control.player(), blockPos(control.action()), control.action(),
                    ServerboundPlayerActionPacket.Action.ABORT_DESTROY_BLOCK);
        }
        if (control.hasInput() && control.player().connection != null) {
            control.player().connection.handlePlayerInput(new ServerboundPlayerInputPacket(releasedInput()));
        }
        if (control.actionType().equals("eat") && control.started() && control.player().connection != null) {
            this.sendPlayerAction(control.player(), ServerboundPlayerActionPacket.Action.RELEASE_USE_ITEM);
        }
        this.active.remove(control.player().getUUID());
        this.emit(control.player(), control.agentId(), control.sessionEpoch(), control.requestId(), control.traceId(), "rejected", reason);
    }

    private void finishCompleted(ActiveControl control) {
        this.active.remove(control.player().getUUID());
        this.emit(control.player(), control.agentId(), control.sessionEpoch(), control.requestId(), control.traceId(), "completed", null);
    }

    private void emit(ServerPlayer player, String agentId, long epoch, String requestId, String traceId, String status, String reason) {
        long sequence = this.outcomeSequences.getOrDefault(player.getUUID(), 0L);
        this.outcomeSequences.put(player.getUUID(), sequence + 1);
        this.outcomeSink.accept(new Outcome(agentId, epoch, requestId, traceId, sequence,
                player.level().getGameTime(), status, reason));
    }

    private static ActionValidationContext copyWithRequestState(
            ActionValidationContext c, Set<String> seenIds, Set<String> activeRequestIds) {
        return new ActionValidationContext(c.agentId(), c.sessionEpoch(), c.observationSequence(), c.gameTick(),
                c.maxObservationLag(), c.inventorySize(), c.hungry(), c.supportedCapabilities(), c.permittedActions(),
                c.visibleEntityRefs(), c.reachableEntityRefs(), c.visibleBlockRefs(), c.reachableBlockRefs(),
                c.mineableBlockRefs(), c.availableRecipeIds(), activeRequestIds, seenIds,
                c.blockedCooldowns(), c.inventory(), c.heldItems());
    }

    private Submission cancelActive(ServerPlayer player, long epoch, String requestId, String traceId, String targetRequestId) {
        ActiveControl target = this.active.get(player.getUUID());
        if (target == null || target.sessionEpoch() != epoch
                || !target.agentId().equals(player.getGameProfile().id().toString())
                || !target.requestId().equals(targetRequestId)) {
            return this.reject(player, epoch, requestId, traceId, "cancel_target_not_active");
        }
        if (target.actionType().equals("mine") && target.started()) {
            this.sendBlockAction(player, blockPos(target.action()), target.action(),
                    ServerboundPlayerActionPacket.Action.ABORT_DESTROY_BLOCK);
        } else if (target.actionType().equals("eat") && target.started() && player.connection != null) {
            this.sendPlayerAction(player, ServerboundPlayerActionPacket.Action.RELEASE_USE_ITEM);
        } else if (target.hasInput() && player.connection != null) {
            player.connection.handlePlayerInput(new ServerboundPlayerInputPacket(releasedInput()));
        }
        this.active.remove(player.getUUID());
        this.emitCancelled(player, target.agentId(), epoch, requestId, traceId, targetRequestId);
        return new Submission(true, "cancelled");
    }

    private void emitCancelled(ServerPlayer player, String agentId, long epoch, String requestId,
            String traceId, String targetRequestId) {
        long sequence = this.outcomeSequences.getOrDefault(player.getUUID(), 0L);
        this.outcomeSequences.put(player.getUUID(), sequence + 1);
        this.outcomeSink.accept(new Outcome(agentId, epoch, requestId, traceId, sequence,
                player.level().getGameTime(), "cancelled", null, targetRequestId));
    }

    private void sendBlockAction(ServerPlayer player, BlockPos pos, JsonObject action,
            ServerboundPlayerActionPacket.Action type) {
        player.connection.handlePlayerAction(new ServerboundPlayerActionPacket(type, pos, blockFace(action), this.nextPacketSequence(player)));
    }

    private void sendPlayerAction(ServerPlayer player, ServerboundPlayerActionPacket.Action type) {
        player.connection.handlePlayerAction(new ServerboundPlayerActionPacket(type, BlockPos.ZERO, Direction.DOWN, this.nextPacketSequence(player)));
    }

    private int nextPacketSequence(ServerPlayer player) {
        int sequence = this.packetSequences.getOrDefault(player.getUUID(), 0);
        this.packetSequences.put(player.getUUID(), sequence == Integer.MAX_VALUE ? 0 : sequence + 1);
        return sequence;
    }

    private void executeDrop(ActiveControl control) {
        ServerPlayer player = control.player();
        int inventorySlot = control.action().get("slot").getAsInt();
        int requestedCount = control.action().get("count").getAsInt();
        boolean wholeStack = control.action().has("whole_stack")
                && control.action().get("whole_stack").getAsBoolean();
        var menu = player.containerMenu;
        if (!menu.getCarried().isEmpty()) {
            this.finishRejected(control, "cursor_not_empty");
            return;
        }
        int menuSlot = menu.findSlot(player.getInventory(), inventorySlot).orElse(-1);
        if (menuSlot < 0) {
            this.finishRejected(control, "inventory_slot_unavailable");
            return;
        }
        int currentCount = player.getInventory().getItem(inventorySlot).getCount();
        int expectedBefore = control.startingStackCount() - control.ticksApplied();
        if (currentCount != expectedBefore || currentCount <= 0) {
            this.finishRejected(control, "inventory_changed_during_drop");
            return;
        }

        byte button = (byte) (wholeStack ? 1 : 0);
        player.connection.handleContainerClick(new ServerboundContainerClickPacket(
                menu.containerId, menu.getStateId(), (short) menuSlot, button, ContainerInput.THROW,
                Int2ObjectMaps.emptyMap(), HashedStack.EMPTY));
        int afterCount = player.getInventory().getItem(inventorySlot).getCount();
        int expectedAfter = wholeStack ? 0 : currentCount - 1;
        if (afterCount != expectedAfter) {
            this.finishRejected(control, control.started() ? "drop_interrupted" : "drop_had_no_effect");
            return;
        }
        if (!control.started()) {
            this.emit(player, control.agentId(), control.sessionEpoch(), control.requestId(), control.traceId(), "started", null);
        }
        if (wholeStack || control.startingStackCount() - afterCount >= requestedCount) {
            this.finishCompleted(control);
            return;
        }
        this.active.put(player.getUUID(), new ActiveControl(player, control.agentId(), control.sessionEpoch(),
                control.requestId(), control.traceId(), control.actionType(), control.action(),
                control.deadlineGameTick(), control.durationTicks(), control.input(), control.hasInput(), true,
                control.stopSent(), control.startingFoodLevel(), control.startingStackCount(), control.ticksApplied() + 1));
    }

    static BlockPos blockPos(JsonObject action) {
        JsonObject target = action.getAsJsonObject("target");
        return new BlockPos(target.get("x").getAsInt(), target.get("y").getAsInt(), target.get("z").getAsInt());
    }

    static Direction blockFace(JsonObject action) {
        return switch (stringField(action, "face")) {
            case "down" -> Direction.DOWN;
            case "north" -> Direction.NORTH;
            case "south" -> Direction.SOUTH;
            case "west" -> Direction.WEST;
            case "east" -> Direction.EAST;
            default -> Direction.UP;
        };
    }

    static InteractionHand handFor(JsonObject action) {
        return stringField(action, "hand").equals("off") ? InteractionHand.OFF_HAND : InteractionHand.MAIN_HAND;
    }

    static int hotbarSlot(JsonObject action) {
        return action.get("hotbar_slot").getAsInt();
    }

    static Input inputFor(JsonObject action, String type) {
        if (type.equals("jump")) {
            return new Input(false, false, false, false, true, false, false);
        }
        double forward = action.get("forward").getAsDouble();
        double strafe = action.get("strafe").getAsDouble();
        boolean sneak = action.has("sneak") && action.get("sneak").getAsBoolean();
        boolean sprint = action.has("sprint") && action.get("sprint").getAsBoolean();
        return new Input(forward > 0, forward < 0, strafe < 0, strafe > 0, false, sneak, sprint);
    }

    static Input releasedInput() {
        return Input.EMPTY;
    }

    private static JsonObject parseObject(String json) {
        try {
            JsonElement parsed = JsonParser.parseString(json);
            return parsed.isJsonObject() ? parsed.getAsJsonObject() : new JsonObject();
        } catch (RuntimeException malformed) {
            return new JsonObject();
        }
    }

    private static String stringField(JsonObject object, String field) {
        if (object == null || !object.has(field) || !object.get(field).isJsonPrimitive()
                || !object.get(field).getAsJsonPrimitive().isString()) return "";
        return object.get(field).getAsString();
    }

    private static int optionalInt(JsonObject object, String field, int fallback) {
        return object.has(field) ? object.get(field).getAsInt() : fallback;
    }

    private static long optionalLong(JsonObject object, String field, long fallback) {
        return object.has(field) ? object.get(field).getAsLong() : fallback;
    }

    private static void requireServerThread(MinecraftServer server) {
        if (!server.isSameThread()) throw new IllegalStateException("action execution must run on the server thread");
    }
}

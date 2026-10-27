package dev.minecraftnativeintelligence;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Map;
import java.util.Set;
import net.fabricmc.fabric.api.gametest.v1.CustomTestMethodInvoker;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.protocol.game.ServerboundPlayerInputPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;

public final class AgentPlayerGameTests implements CustomTestMethodInvoker {
    @GameTest
    public void usernameValidationMatchesProfileConstraints(GameTestHelper helper) {
        helper.assertTrue(AgentPlayerManager.isValidUsername("abc"), "three-character username is accepted");
        helper.assertTrue(AgentPlayerManager.isValidUsername("A_12345678901234"), "16-character username is accepted");
        helper.assertTrue(!AgentPlayerManager.isValidUsername("ab"), "two-character username is rejected");
        helper.assertTrue(!AgentPlayerManager.isValidUsername("A_123456789012345"), "17-character username is rejected");
        helper.assertTrue(!AgentPlayerManager.isValidUsername("bad-name"), "punctuation is rejected");
        helper.assertTrue(!AgentPlayerManager.isValidUsername(null), "missing username is rejected");
        helper.succeed();
    }

    @GameTest
    public void projectOwnedPlayerJoinsAndUnloads(GameTestHelper helper) {
        AgentPlayerManager manager = new AgentPlayerManager();
        var level = helper.getLevel();
        var server = level.getServer();
        var position = helper.absolutePos(new BlockPos(1, 1, 1));

        ServerPlayer player = manager.spawn(
                server,
                level,
                "MniTestAgent",
                position.getX() + 0.5,
                position.getY(),
                position.getZ() + 0.5);

        helper.assertTrue(server.getPlayerList().getPlayer(player.getUUID()) == player, "vanilla player list registers the agent");
        helper.assertTrue(level.players().contains(player), "server level tracks the agent as a player");
        helper.assertTrue(player.gameMode.getGameModeForPlayer() == net.minecraft.world.level.GameType.SURVIVAL, "agent starts in Survival");
        boolean caseVariantRejected = false;
        try {
            manager.spawn(server, level, "mNItEsTaGeNt", position.getX() + 1.5, position.getY(), position.getZ() + 0.5);
        } catch (IllegalArgumentException expected) {
            caseVariantRejected = true;
        }
        helper.assertTrue(caseVariantRejected, "case-insensitive online username collision is rejected");
        helper.assertTrue(server.getPlayerList().getPlayers().stream().filter(p -> p.getGameProfile().name().equalsIgnoreCase("MniTestAgent")).count() == 1,
                "case variant rejection leaves exactly one matching player");

        helper.runAtTickTime(3, () -> {
            helper.assertTrue(player.isAlive(), "agent survives normal server ticks without an authenticated client");
            boolean removed = manager.remove(server, player.getUUID());
            helper.assertTrue(removed, "agent cleanup reports removal");
            helper.assertTrue(server.getPlayerList().getPlayer(player.getUUID()) == null, "cleanup removes player-list registration");
            helper.assertTrue(!level.players().contains(player), "cleanup removes level tracking");
            helper.succeed();
        });
    }

    @GameTest
    public void vanillaInputHandlerReceivesProjectOwnedPlayerControl(GameTestHelper helper) {
        AgentPlayerManager manager = new AgentPlayerManager();
        var level = helper.getLevel();
        var server = level.getServer();
        var position = helper.absolutePos(new BlockPos(1, 1, 1));
        ServerPlayer player = manager.spawn(server, level, "MniInputAgent",
                position.getX() + 0.5, position.getY(), position.getZ() + 0.5);
        Input expected = new Input(true, false, false, false, true, false, false);

        player.connection.handlePlayerInput(new ServerboundPlayerInputPacket(expected));
        helper.assertTrue(expected.equals(player.getLastClientInput()),
                "vanilla server packet handler records the control frame without a client socket");

        manager.remove(server, player.getUUID());
        helper.succeed();
    }

    @GameTest
    public void eatActionUsesVanillaItemTimingAndReportsConsumption(GameTestHelper helper) {
        AgentPlayerManager manager = new AgentPlayerManager();
        var level = helper.getLevel();
        var server = level.getServer();
        var position = helper.absolutePos(new BlockPos(1, 1, 1));
        ServerPlayer player = manager.spawn(server, level, "MniEatAgent",
                position.getX() + 0.5, position.getY(), position.getZ() + 0.5);
        player.getFoodData().setFoodLevel(10);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.BREAD, 1));

        var outcomes = new ArrayList<AgentActionExecutor.Outcome>();
        AgentActionExecutor executor = new AgentActionExecutor(manager, outcomes::add);
        String agentId = player.getGameProfile().id().toString();
        ActionValidationContext context = new ActionValidationContext(agentId, 1, 0, level.getGameTime(), 0,
                41, true, Set.of(ActionValidationContext.actionCapability("eat")), Set.of("eat"),
                Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(),
                Map.of(), Map.of("main", new ActionValidationContext.ItemState("minecraft:bread", 1, true, false, "")));
        var submission = executor.submit(player,
                "{\"schema_version\":\"action-request.v0\",\"agent_id\":\"" + agentId
                        + "\",\"session_epoch\":1,\"request_id\":\"eat-1\",\"based_on_observation_seq\":0,"
                        + "\"trace_id\":\"eat-trace-1\",\"action\":{\"type\":\"eat\",\"hand\":\"main\"}}",
                context);
        helper.assertTrue(submission.accepted(), "legal eating request is accepted");
        tickEatingAction(helper, executor, server, player, manager, outcomes, 1);
    }

    @GameTest
    public void selectSlotUsesVanillaCarriedItemHandler(GameTestHelper helper) {
        AgentPlayerManager manager = new AgentPlayerManager();
        var level = helper.getLevel();
        var server = level.getServer();
        var position = helper.absolutePos(new BlockPos(1, 1, 1));
        ServerPlayer player = manager.spawn(server, level, "MniSlotAgent",
                position.getX() + 0.5, position.getY(), position.getZ() + 0.5);
        var outcomes = new ArrayList<AgentActionExecutor.Outcome>();
        AgentActionExecutor executor = new AgentActionExecutor(manager, outcomes::add);
        String agentId = player.getGameProfile().id().toString();
        ActionValidationContext context = new ActionValidationContext(agentId, 1, 0, level.getGameTime(), 0,
                41, false, Set.of(ActionValidationContext.actionCapability("select_slot")), Set.of("select_slot"),
                Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Map.of(), Map.of());
        var submission = executor.submit(player,
                "{\"schema_version\":\"action-request.v0\",\"agent_id\":\"" + agentId
                        + "\",\"session_epoch\":1,\"request_id\":\"slot-1\",\"based_on_observation_seq\":0,"
                        + "\"trace_id\":\"slot-trace-1\",\"action\":{\"type\":\"select_slot\",\"hotbar_slot\":4}}",
                context);
        helper.assertTrue(submission.accepted(), "valid hotbar selection is accepted");
        executor.startServerTick(server);
        helper.assertTrue(player.getInventory().getSelectedSlot() == 4,
                "vanilla carried-item handler selects the requested hotbar slot");
        helper.assertTrue(outcomes.stream().map(AgentActionExecutor.Outcome::status).toList()
                        .containsAll(java.util.List.of("accepted", "started", "completed")),
                "selection emits accepted, started, and completed outcomes");
        executor.removeAgent(player);
        manager.remove(server, player.getUUID());
        helper.succeed();
    }

    @GameTest
    public void dropActionUsesVanillaContainerClickAndHonorsCount(GameTestHelper helper) {
        AgentPlayerManager manager = new AgentPlayerManager();
        var level = helper.getLevel();
        var server = level.getServer();
        var position = helper.absolutePos(new BlockPos(1, 1, 1));
        ServerPlayer player = manager.spawn(server, level, "MniDropAgent",
                position.getX() + 0.5, position.getY(), position.getZ() + 0.5);
        player.getInventory().setItem(0, new ItemStack(Items.BREAD, 3));
        var outcomes = new ArrayList<AgentActionExecutor.Outcome>();
        AgentActionExecutor executor = new AgentActionExecutor(manager, outcomes::add);
        String agentId = player.getGameProfile().id().toString();
        ActionValidationContext context = new ActionValidationContext(agentId, 1, 0, level.getGameTime(), 0,
                41, false, Set.of(ActionValidationContext.actionCapability("drop")), Set.of("drop"),
                Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(),
                Map.of(0, new ActionValidationContext.ItemState("minecraft:bread", 3, true, false, "")), Map.of());
        var submission = executor.submit(player,
                "{\"schema_version\":\"action-request.v0\",\"agent_id\":\"" + agentId
                        + "\",\"session_epoch\":1,\"request_id\":\"drop-1\",\"based_on_observation_seq\":0,"
                        + "\"trace_id\":\"drop-trace-1\",\"action\":{\"type\":\"drop\",\"slot\":0,\"count\":2}}",
                context);
        helper.assertTrue(submission.accepted(), "valid partial drop request is accepted");
        executor.startServerTick(server);
        executor.endServerTick(server);
        helper.assertTrue(player.getInventory().getItem(0).getCount() == 2,
                "first vanilla throw click drops one item during its tick");

        helper.runAtTickTime(1, () -> {
            executor.startServerTick(server);
            executor.endServerTick(server);
            helper.assertTrue(player.getInventory().getItem(0).getCount() == 1,
                    "second vanilla throw click honors the requested total count");
            int droppedBread = level.getEntitiesOfClass(ItemEntity.class, player.getBoundingBox().inflate(4.0)).stream()
                    .filter(item -> item.getItem().is(Items.BREAD))
                    .mapToInt(item -> item.getItem().getCount())
                    .sum();
            helper.assertTrue(droppedBread == 2, "vanilla spawned exactly the requested dropped quantity");
            helper.assertTrue(outcomes.stream().anyMatch(outcome -> outcome.status().equals("completed")),
                    "drop completes after the requested inventory count is removed");
            player.getInventory().setItem(1, new ItemStack(Items.APPLE, 4));
            ActionValidationContext wholeStackContext = new ActionValidationContext(agentId, 1, 1,
                    level.getGameTime(), 0, 41, false,
                    Set.of(ActionValidationContext.actionCapability("drop")), Set.of("drop"),
                    Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(),
                    Map.of(1, new ActionValidationContext.ItemState("minecraft:apple", 4, true, false, "")), Map.of());
            var wholeStackSubmission = executor.submit(player,
                    "{\"schema_version\":\"action-request.v0\",\"agent_id\":\"" + agentId
                            + "\",\"session_epoch\":1,\"request_id\":\"drop-2\",\"based_on_observation_seq\":1,"
                            + "\"trace_id\":\"drop-trace-2\",\"action\":{\"type\":\"drop\",\"slot\":1,\"count\":4,\"whole_stack\":true}}",
                    wholeStackContext);
            helper.assertTrue(wholeStackSubmission.accepted(), "valid whole-stack drop is accepted");
            executor.startServerTick(server);
            executor.endServerTick(server);
            helper.assertTrue(player.getInventory().getItem(1).isEmpty(),
                    "vanilla stack-throw click removes the full requested stack");
            int droppedApples = level.getEntitiesOfClass(ItemEntity.class, player.getBoundingBox().inflate(4.0)).stream()
                    .filter(item -> item.getItem().is(Items.APPLE))
                    .mapToInt(item -> item.getItem().getCount())
                    .sum();
            helper.assertTrue(droppedApples == 4, "vanilla spawned the whole dropped stack");
            executor.removeAgent(player);
            manager.remove(server, player.getUUID());
            helper.succeed();
        });
    }

    @GameTest
    public void equipActionUsesVanillaInventoryClicksAndReturnsReplacedEquipment(GameTestHelper helper) {
        AgentPlayerManager manager = new AgentPlayerManager();
        var level = helper.getLevel();
        var server = level.getServer();
        var position = helper.absolutePos(new BlockPos(1, 1, 1));
        ServerPlayer player = manager.spawn(server, level, "MniEquipAgent",
                position.getX() + 0.5, position.getY(), position.getZ() + 0.5);
        player.getInventory().setItem(9, new ItemStack(Items.IRON_HELMET, 1));
        player.setItemSlot(EquipmentSlot.HEAD, new ItemStack(Items.LEATHER_HELMET, 1));
        var outcomes = new ArrayList<AgentActionExecutor.Outcome>();
        AgentActionExecutor executor = new AgentActionExecutor(manager, outcomes::add);
        String agentId = player.getGameProfile().id().toString();
        ActionValidationContext context = new ActionValidationContext(agentId, 1, 0,
                level.getGameTime(), 0, 41, false,
                Set.of(ActionValidationContext.actionCapability("equip")), Set.of("equip"),
                Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(),
                Map.of(9, new ActionValidationContext.ItemState("minecraft:iron_helmet", 1, false, false, "head")),
                Map.of());
        var submission = executor.submit(player,
                "{\"schema_version\":\"action-request.v0\",\"agent_id\":\"" + agentId
                        + "\",\"session_epoch\":1,\"request_id\":\"equip-1\",\"based_on_observation_seq\":0,"
                        + "\"trace_id\":\"equip-trace-1\",\"action\":{\"type\":\"equip\",\"slot\":\"head\","
                        + "\"inventory_slot\":9}}",
                context);
        helper.assertTrue(submission.accepted(), "legal equipment request is accepted");

        executor.startServerTick(server);
        helper.assertTrue(player.getItemBySlot(EquipmentSlot.HEAD).is(Items.IRON_HELMET),
                "vanilla inventory clicks equip the requested helmet");
        helper.assertTrue(player.getInventory().getItem(9).is(Items.LEATHER_HELMET),
                "the displaced helmet returns to the source inventory slot");
        helper.assertTrue(player.inventoryMenu.getCarried().isEmpty(),
                "the equip sequence leaves the cursor empty");
        helper.assertTrue(outcomes.stream().anyMatch(outcome -> outcome.requestId().equals("equip-1")
                        && outcome.status().equals("completed")),
                "equip completes after vanilla equipment and inventory state changes");

        executor.removeAgent(player);
        manager.remove(server, player.getUUID());
        helper.succeed();
    }

    @GameTest
    public void placeActionUsesVanillaGameModeAfterPacketEquivalentChecks(GameTestHelper helper) {
        AgentPlayerManager manager = new AgentPlayerManager();
        var level = helper.getLevel();
        var server = level.getServer();
        BlockPos target = helper.absolutePos(new BlockPos(2, 1, 3));
        level.setBlock(target, Blocks.STONE.defaultBlockState(), 3);
        ServerPlayer player = manager.spawn(server, level, "MniPlaceAgent",
                target.getX() + 0.5, target.getY() + 1.0, target.getZ() - 2.0);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.DIRT, 1));
        var outcomes = new ArrayList<AgentActionExecutor.Outcome>();
        AgentActionExecutor executor = new AgentActionExecutor(manager, outcomes::add);
        String agentId = player.getGameProfile().id().toString();
        String blockRef = target.getX() + "," + target.getY() + "," + target.getZ();
        ActionValidationContext context = new ActionValidationContext(agentId, 1, 0, level.getGameTime(), 0,
                41, false, Set.of(ActionValidationContext.actionCapability("place")), Set.of("place"),
                Set.of(), Set.of(), Set.of(blockRef), Set.of(blockRef), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(),
                Map.of(), Map.of("main", new ActionValidationContext.ItemState("minecraft:dirt", 1, false, true, "")));
        var submission = executor.submit(player,
                "{\"schema_version\":\"action-request.v0\",\"agent_id\":\"" + agentId
                        + "\",\"session_epoch\":1,\"request_id\":\"place-1\",\"based_on_observation_seq\":0,"
                        + "\"trace_id\":\"place-trace-1\",\"action\":{\"type\":\"place\",\"target\":{\"x\":"
                        + target.getX() + ",\"y\":" + target.getY() + ",\"z\":" + target.getZ()
                        + "},\"face\":\"up\",\"hand\":\"main\"}}",
                context);
        helper.assertTrue(submission.accepted(), "legal placement request is accepted");
        tickPlacementAction(helper, executor, server, player, manager, outcomes, target, 1);
    }

    @GameTest
    public void placeActionRechecksLiveReachBeforeChangingWorld(GameTestHelper helper) {
        AgentPlayerManager manager = new AgentPlayerManager();
        var level = helper.getLevel();
        var server = level.getServer();
        BlockPos target = helper.absolutePos(new BlockPos(2, 1, 3));
        level.setBlock(target, Blocks.STONE.defaultBlockState(), 3);
        ServerPlayer player = manager.spawn(server, level, "MniPlaceReachAgent",
                target.getX() + 0.5, target.getY() + 1.0, target.getZ() - 5.0);
        player.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.DIRT, 1));
        var outcomes = new ArrayList<AgentActionExecutor.Outcome>();
        AgentActionExecutor executor = new AgentActionExecutor(manager, outcomes::add);
        String agentId = player.getGameProfile().id().toString();
        String blockRef = target.getX() + "," + target.getY() + "," + target.getZ();
        ActionValidationContext reportedReachContext = new ActionValidationContext(agentId, 1, 0,
                level.getGameTime(), 0, 41, false,
                Set.of(ActionValidationContext.actionCapability("place")), Set.of("place"),
                Set.of(), Set.of(), Set.of(blockRef), Set.of(blockRef), Set.of(), Set.of(), Set.of(), Set.of(), Set.of(),
                Map.of(), Map.of("main", new ActionValidationContext.ItemState("minecraft:dirt", 1, false, true, "")));
        var submission = executor.submit(player,
                "{\"schema_version\":\"action-request.v0\",\"agent_id\":\"" + agentId
                        + "\",\"session_epoch\":1,\"request_id\":\"place-out-of-reach\",\"based_on_observation_seq\":0,"
                        + "\"trace_id\":\"place-out-of-reach-trace\",\"action\":{\"type\":\"place\",\"target\":{\"x\":"
                        + target.getX() + ",\"y\":" + target.getY() + ",\"z\":" + target.getZ()
                        + "},\"face\":\"up\",\"hand\":\"main\"}}",
                reportedReachContext);
        helper.assertTrue(submission.accepted(), "validated observation declares the block reachable");

        executor.startServerTick(server);
        helper.assertTrue(outcomes.stream().anyMatch(outcome -> outcome.requestId().equals("place-out-of-reach")
                        && outcome.status().equals("rejected") && "target_out_of_reach".equals(outcome.reasonCode())),
                "executor rejects a block that is outside the player's live interaction range");
        helper.assertTrue(level.getBlockState(target.above()).isAir(),
                "out-of-reach placement does not change the world");
        helper.assertTrue(player.getItemInHand(InteractionHand.MAIN_HAND).getCount() == 1,
                "out-of-reach placement does not consume the held item");

        manager.remove(server, player.getUUID());
        helper.succeed();
    }

    private static void tickPlacementAction(GameTestHelper helper, AgentActionExecutor executor,
            net.minecraft.server.MinecraftServer server, ServerPlayer player, AgentPlayerManager manager,
            ArrayList<AgentActionExecutor.Outcome> outcomes, BlockPos target, int tick) {
        helper.runAtTickTime(tick, () -> {
            executor.startServerTick(server);
            executor.endServerTick(server);
            var completion = outcomes.stream()
                    .filter(outcome -> outcome.requestId().equals("place-1"))
                    .filter(outcome -> outcome.status().equals("completed"))
                    .findFirst();
            if (completion.isPresent()) {
                helper.assertTrue(player.level().getBlockState(target.above()).is(Blocks.DIRT),
                        "vanilla placed the held block on the requested face");
                helper.assertTrue(player.getItemInHand(InteractionHand.MAIN_HAND).isEmpty(),
                        "vanilla consumed the placed item");
                executor.removeAgent(player);
                manager.remove(server, player.getUUID());
                helper.succeed();
            } else if (tick >= 99 || outcomes.stream().anyMatch(outcome ->
                    outcome.requestId().equals("place-1") && outcome.status().equals("rejected"))) {
                executor.removeAgent(player);
                manager.remove(server, player.getUUID());
                helper.fail("placement did not complete through vanilla game-mode interaction");
            } else {
                tickPlacementAction(helper, executor, server, player, manager, outcomes, target, tick + 1);
            }
        });
    }

    private static void tickEatingAction(GameTestHelper helper, AgentActionExecutor executor,
            net.minecraft.server.MinecraftServer server, ServerPlayer player, AgentPlayerManager manager,
            ArrayList<AgentActionExecutor.Outcome> outcomes, int tick) {
        helper.runAtTickTime(tick, () -> {
            executor.startServerTick(server);
            executor.endServerTick(server);
            if (outcomes.stream().anyMatch(outcome -> outcome.status().equals("completed"))) {
                helper.assertTrue(player.getFoodData().getFoodLevel() > 10,
                        "vanilla food mechanics increased hunger before completion");
                helper.assertTrue(player.getItemInHand(InteractionHand.MAIN_HAND).isEmpty(),
                        "vanilla item use consumed the bread");
                helper.assertTrue(outcomes.stream().anyMatch(outcome -> outcome.status().equals("started")),
                        "executor emitted started before completion");
                executor.removeAgent(player);
                manager.remove(server, player.getUUID());
                helper.succeed();
            } else if (tick >= 99) {
                executor.removeAgent(player);
                manager.remove(server, player.getUUID());
                helper.fail("eating did not complete before the GameTest timeout");
            } else {
                tickEatingAction(helper, executor, server, player, manager, outcomes, tick + 1);
            }
        });
    }

    @Override
    public void invokeTestMethod(GameTestHelper helper, Method method) throws ReflectiveOperationException {
        method.invoke(this, helper);
    }
}

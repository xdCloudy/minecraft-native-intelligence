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
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

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

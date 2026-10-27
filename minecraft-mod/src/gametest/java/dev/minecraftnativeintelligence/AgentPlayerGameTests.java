package dev.minecraftnativeintelligence;

import java.lang.reflect.Method;
import net.fabricmc.fabric.api.gametest.v1.CustomTestMethodInvoker;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.protocol.game.ServerboundPlayerInputPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Input;

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

    @Override
    public void invokeTestMethod(GameTestHelper helper, Method method) throws ReflectiveOperationException {
        method.invoke(this, helper);
    }
}

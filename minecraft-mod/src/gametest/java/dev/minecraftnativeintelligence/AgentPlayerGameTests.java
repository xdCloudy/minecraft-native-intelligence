package dev.minecraftnativeintelligence;

import java.lang.reflect.Method;
import net.fabricmc.fabric.api.gametest.v1.CustomTestMethodInvoker;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerPlayer;

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

        helper.runAtTickTime(3, () -> {
            helper.assertTrue(player.isAlive(), "agent survives normal server ticks without an authenticated client");
            boolean removed = manager.remove(server, player.getUUID());
            helper.assertTrue(removed, "agent cleanup reports removal");
            helper.assertTrue(server.getPlayerList().getPlayer(player.getUUID()) == null, "cleanup removes player-list registration");
            helper.assertTrue(!level.players().contains(player), "cleanup removes level tracking");
            helper.succeed();
        });
    }

    @Override
    public void invokeTestMethod(GameTestHelper helper, Method method) throws ReflectiveOperationException {
        method.invoke(this, helper);
    }
}

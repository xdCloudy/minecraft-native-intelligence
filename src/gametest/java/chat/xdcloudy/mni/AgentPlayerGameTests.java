package chat.xdcloudy.mni;

import java.lang.reflect.Method;
import java.util.UUID;
import net.fabricmc.fabric.api.gametest.v1.CustomTestMethodInvoker;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerPlayer;
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
    public void directRegistrationDoesNotRestoreSavedInventory(GameTestHelper helper) {
        AgentPlayerManager manager = new AgentPlayerManager();
        var level = helper.getLevel();
        var server = level.getServer();
        var position = helper.absolutePos(new BlockPos(1, 1, 1));
        UUID id = UUID.randomUUID();
        try {
            ServerPlayer player = manager.spawnWithId(server, level, id, "MniSaveProbe",
                    position.getX() + 0.5, position.getY(), position.getZ() + 0.5);
            // Evaluator setup, not an agent action or Survival parity claim.
            player.getInventory().setItem(0, new ItemStack(Items.APPLE, 3));
            boolean duplicateRejected = false;
            try {
                manager.spawnWithId(server, level, id, "MniOtherProbe",
                        position.getX() + 1.5, position.getY(), position.getZ() + 0.5);
            } catch (IllegalArgumentException expected) {
                duplicateRejected = true;
            }
            helper.assertTrue(duplicateRejected, "online UUID cannot be registered twice");
            helper.assertTrue(manager.remove(server, id), "first player removed and saved");
            var saved = server.getPlayerList().loadPlayerData(player.nameAndId());
            helper.assertTrue(saved.isPresent(), "vanilla player data exists after removal");
            helper.assertTrue(saved.orElseThrow().getListOrEmpty("Inventory").compoundStream()
                    .anyMatch(item -> item.getString("id").orElse("").equals("minecraft:apple")
                            && item.getInt("count").orElse(0) == 3),
                    "saved player data contains the three fixture apples");
            ServerPlayer rejoined = manager.spawnWithId(server, level, id, "MniSaveProbe",
                    position.getX() + 0.5, position.getY(), position.getZ() + 0.5);
            ItemStack restored = rejoined.getInventory().getItem(0);
            // This intentionally records a known limitation of the recovered
            // prototype: direct registration bypasses the normal load path.
            helper.assertTrue(restored.isEmpty(), "direct registration did not load saved inventory");
            helper.succeed();
        } finally {
            manager.removeAll(server);
        }
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
            helper.assertTrue(player.tickCount > 0, "registered player has actually ticked");
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

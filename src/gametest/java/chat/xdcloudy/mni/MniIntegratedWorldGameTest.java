package chat.xdcloudy.mni;

import java.util.UUID;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

/** Integrated-world and test-only player tracking smoke, not an AI agent. */
@SuppressWarnings("UnstableApiUsage")
public final class MniIntegratedWorldGameTest implements FabricClientGameTest {
    @Override
    public void runTest(ClientGameTestContext context) {
        try (TestSingleplayerContext singleplayer = context.worldBuilder().create()) {
            singleplayer.getConnection().waitForChunksRender();
            context.takeScreenshot("mni-integrated-world-smoke");
            // Evaluator-only fixture: no AI runtime or gameplay action.
            var manager = new AgentPlayerManager();
            UUID id = singleplayer.getServer().computeOnServer(server -> {
                var human = singleplayer.getConnection().getServerPlayer();
                return manager.spawn(server, human.level(), "MniClientProbe",
                        human.getX() + 2, human.getY(), human.getZ()).getUUID();
            });
            try {
                // Check both entity tracking and the player-list entry before
                // removal; a successful screenshot alone proves neither.
                context.waitFor(client -> client.level != null && client.level.getPlayerByUUID(id) != null
                        && client.getConnection() != null && client.getConnection().getPlayerInfo(id) != null, 200);
                singleplayer.getServer().runOnServer(server -> manager.remove(server, id));
                context.waitFor(client -> client.level != null && client.level.getPlayerByUUID(id) == null
                        && client.getConnection() != null && client.getConnection().getPlayerInfo(id) == null, 200);
            } finally {
                singleplayer.getServer().runOnServer(server -> manager.removeAll(server));
            }
        }
    }
}

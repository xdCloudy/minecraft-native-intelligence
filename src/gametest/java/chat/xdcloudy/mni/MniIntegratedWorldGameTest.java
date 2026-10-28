package chat.xdcloudy.mni;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

/**
 * Client-side test of an actual integrated single-player logical server.
 * No custom AI player, privileged action, or vanilla-only remote client is
 * involved; those require independent acceptance evidence.
 */
@SuppressWarnings("UnstableApiUsage")
public final class MniIntegratedWorldGameTest implements FabricClientGameTest {
    @Override
    public void runTest(ClientGameTestContext context) {
        try (TestSingleplayerContext singleplayer = context.worldBuilder().create()) {
            singleplayer.getClientLevel().waitForChunksRender();
            context.takeScreenshot("mni-integrated-world-smoke");
        }
    }
}

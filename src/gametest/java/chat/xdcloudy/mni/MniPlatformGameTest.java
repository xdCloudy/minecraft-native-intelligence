package chat.xdcloudy.mni;

import java.lang.reflect.Method;

import net.fabricmc.fabric.api.gametest.v1.CustomTestMethodInvoker;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.level.block.Blocks;

/**
 * T4 baseline: actually load a logical Minecraft server and run one world
 * assertion. This intentionally does not pretend that an AI player exists.
 * World mutation here is evaluator-only fixture setup, never an agent action.
 */
public final class MniPlatformGameTest implements CustomTestMethodInvoker {
    @GameTest
    public void serverWorldFixtureLoads(GameTestHelper context) {
        context.assertBlockPresent(Blocks.AIR, 0, 0, 0);
        context.succeed();
    }

    @Override
    public void invokeTestMethod(GameTestHelper context, Method method)
        throws ReflectiveOperationException {
        context.setBlock(0, 0, 0, Blocks.AIR);
        method.invoke(this, context);
    }
}

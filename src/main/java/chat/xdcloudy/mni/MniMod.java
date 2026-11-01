package chat.xdcloudy.mni;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Minimal logical-server platform probe. This is not an agent or player entity.
 */
public final class MniMod implements ModInitializer {
    public static final String MOD_ID = "minecraft-native-intelligence";
    private static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    @Override
    public void onInitialize() {
        LOGGER.info("MNI Fabric platform spike initialized; autonomous agent unavailable");
        ServerLifecycleEvents.SERVER_STARTED.register(server ->
            LOGGER.info("MNI logical server started (dedicated={}); no player spawned",
                server.isDedicatedServer())
        );
    }
}

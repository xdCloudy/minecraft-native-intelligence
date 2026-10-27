package dev.minecraftnativeintelligence;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public final class MniMod implements ModInitializer {
    public static final String MOD_ID = "minecraft_native_intelligence";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);
    private final AgentPlayerManager agentPlayers = new AgentPlayerManager();

    @Override
    public void onInitialize() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
            dispatcher.register(Commands.literal("spawn")
                    .then(Commands.literal("ai-agent")
                            .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                            .then(Commands.argument("username", StringArgumentType.word())
                                    .executes(context -> {
                                        var source = context.getSource();
                                        var level = source.getServer().overworld();
                                        BlockPos spawn = level.getRespawnData().pos();
                                        String username = StringArgumentType.getString(context, "username");
                                        try {
                                            var player = this.agentPlayers.spawn(
                                                    source.getServer(),
                                                    level,
                                                    username,
                                                    spawn.getX() + 0.5,
                                                    spawn.getY() + 1.0,
                                                    spawn.getZ() + 0.5);
                                            source.sendSuccess(
                                                    () -> Component.literal("Spawned project-owned AI player " + player.getGameProfile().name()),
                                                    true);
                                            return 1;
                                        } catch (IllegalArgumentException | IllegalStateException failure) {
                                            source.sendFailure(Component.literal(failure.getMessage()));
                                            return 0;
                                        } catch (RuntimeException failure) {
                                            LOGGER.error("AI player creation failed", failure);
                                            source.sendFailure(Component.literal("AI player creation failed; see server log."));
                                            return 0;
                                        }
                                    }))));

            dispatcher.register(Commands.literal("mni")
                    .then(Commands.literal("despawn")
                            .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                            .then(Commands.argument("username", StringArgumentType.word())
                                    .executes(context -> {
                                        var source = context.getSource();
                                        var player = this.agentPlayers.findByName(
                                                StringArgumentType.getString(context, "username"));
                                        if (player == null) {
                                            source.sendFailure(Component.literal("No active AI player has that name."));
                                            return 0;
                                        }
                                        this.agentPlayers.remove(source.getServer(), player.getUUID());
                                        source.sendSuccess(
                                                () -> Component.literal("Despawned AI player " + player.getGameProfile().name()),
                                                true);
                                        return 1;
                                    }))));
        });
        ServerLifecycleEvents.SERVER_STOPPING.register(this.agentPlayers::removeAll);
        LOGGER.info("Minecraft Native Intelligence mod initialized");
    }
}

package chat.xdcloudy.mni;

import com.mojang.authlib.GameProfile;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.regex.Pattern;
import net.minecraft.network.Connection;
import net.minecraft.network.PacketListener;
import net.minecraft.network.ProtocolInfo;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ClientInformation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.world.level.GameType;

/** Test-only recovery of the unmerged PR #125 player-lifecycle prototype. */
public final class AgentPlayerManager {
    private static final Pattern VALID_NAME = Pattern.compile("[A-Za-z0-9_]{3,16}");
    private final Map<UUID, ServerPlayer> agents = new HashMap<>();

    public ServerPlayer spawn(MinecraftServer server, ServerLevel level, String username, double x, double y, double z) {
        return spawnWithId(server, level, UUID.randomUUID(), username, x, y, z);
    }

    // Test-only explicit identity allows a remove/rejoin persistence probe.
    ServerPlayer spawnWithId(MinecraftServer server, ServerLevel level, UUID projectUuid,
                             String username, double x, double y, double z) {
        requireServerThread(server);
        if (!isValidUsername(username)) {
            throw new IllegalArgumentException("username must contain 3–16 ASCII letters, digits, or underscores");
        }
        if (server.getPlayerList().getPlayer(username) != null) {
            throw new IllegalArgumentException("a player with that name is already online");
        }
        if (projectUuid == null || server.getPlayerList().getPlayer(projectUuid) != null) {
            throw new IllegalArgumentException("invalid or already-online player identity");
        }

        GameProfile profile = new GameProfile(projectUuid, username);
        ServerPlayer player = new ServerPlayer(server, level, profile, ClientInformation.createDefault());
        player.setPos(x, y, z);
        player.setYRot(0.0F);
        player.setXRot(0.0F);

        SilentAgentConnection connection = new SilentAgentConnection();
        CommonListenerCookie cookie = CommonListenerCookie.createInitial(profile, false);

        try {
            // Reuse vanilla player-list, profile, scoreboard, and entity-tracking
            // lifecycle. No socket, login handshake, Mojang identity, or inbound
            // packet path is created for this project-owned player.
            server.getPlayerList().placeNewPlayer(connection, player, cookie);
            player.setGameMode(GameType.SURVIVAL);
            this.agents.put(projectUuid, player);
            return player;
        } catch (RuntimeException | Error failure) {
            if (server.getPlayerList().getPlayer(projectUuid) == player) {
                server.getPlayerList().remove(player);
            } else if (level.getEntity(projectUuid) == player) {
                level.removePlayerImmediately(player, net.minecraft.world.entity.Entity.RemovalReason.DISCARDED);
            }
            throw failure;
        }
    }

    public boolean remove(MinecraftServer server, UUID projectUuid) {
        requireServerThread(server);
        ServerPlayer player = this.agents.remove(projectUuid);
        if (player == null) {
            return false;
        }
        server.getPlayerList().remove(player);
        return true;
    }

    public ServerPlayer findByName(String username) {
        return this.agents.values().stream()
                .filter(player -> player.getGameProfile().name().equalsIgnoreCase(username))
                .findFirst()
                .orElse(null);
    }

    public void removeAll(MinecraftServer server) {
        requireServerThread(server);
        for (UUID projectUuid : this.agents.keySet().toArray(UUID[]::new)) {
            this.remove(server, projectUuid);
        }
    }

    private static void requireServerThread(MinecraftServer server) {
        if (!server.isSameThread()) {
            throw new IllegalStateException("AI player lifecycle must run on the Minecraft server thread");
        }
    }

    static boolean isValidUsername(String username) {
        return username != null && VALID_NAME.matcher(username).matches();
    }

    /**
     * A local output sink required by ServerPlayer's listener field. It has no
     * Netty channel and accepts no packets; AI input is injected through the
     * server-authoritative action adapter instead of a simulated client.
     */
    static final class SilentAgentConnection extends Connection {
        SilentAgentConnection() {
            super(PacketFlow.SERVERBOUND);
        }

        @Override
        public <T extends PacketListener> void setupInboundProtocol(ProtocolInfo<T> protocol, T packetListener) {
            // Deliberately no inbound protocol: this is not a client session.
        }

        @Override
        public void send(Packet<?> packet) {}

        @Override
        public void send(Packet<?> packet, io.netty.channel.ChannelFutureListener listener) {}

        @Override
        public void send(Packet<?> packet, io.netty.channel.ChannelFutureListener listener, boolean flush) {}

        @Override
        public void flushChannel() {}

        @Override
        public String getLoggableAddress(boolean logIps) {
            return "project-local-agent";
        }
    }
}

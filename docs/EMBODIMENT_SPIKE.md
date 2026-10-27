# Server player embodiment spike

Status: experimental prototype for issue #56. This is a server-only entity
lifecycle spike; it is not yet the production player adapter.

## Implementation

`minecraft-mod/` builds a single Fabric mod for Minecraft 26.3. The operator
command `/spawn ai-agent <username>` creates a `ServerPlayer` with a random,
project-owned UUID and no Mojang account identity. The command requires the
server's gamemaster permission. AI names use the vanilla username character
and length limits, and an online name collision is rejected.

The prototype routes registration through vanilla `PlayerList.placeNewPlayer`
so the player list, profile initialization, scoreboard state, and
`ServerLevel.addNewPlayer` entity-tracking path run. Its `SilentAgentConnection`
has no socket or Netty channel, accepts no inbound protocol, and discards
packets sent to the agent itself. It exists because the 26.3 `ServerPlayer`
constructor creates player state but `ServerPlayer.tick()` requires a
`ServerGamePacketListenerImpl`. Other online clients receive normal player
info and entity-tracking packets through the server's existing player list.

`/mni despawn <username>` uses vanilla player removal and saving. Runtime
shutdown removes every active prototype player. A failed registration rolls
back player-list or level registration when that state was already reached.
All lifecycle calls are restricted to the Minecraft server thread.

## API evidence and risk

The 26.3 mapped sources were generated locally from the configured official
Minecraft distribution and inspected without committing game sources. The
public `ServerPlayer` constructor takes `(MinecraftServer, ServerLevel,
GameProfile, ClientInformation)`. `ServerLevel.addNewPlayer` registers the
entity with the level's entity manager. `PlayerList.placeNewPlayer` performs
player-list/profile setup and calls `ServerLevel.addNewPlayer`. `ServerPlayer`
stores a packet listener and calls it from its tick method.

This path bypasses Minecraft's network login/authentication flow by design; it
does not present an authenticated profile or account. It does use vanilla's
player-registration routine, whose assumptions may change across versions.
The silent connection shim and the registration routine are internal
integration seams that need scrutiny during the real-server spike. The
prototype does not yet persist an agent registry or reconnect identity after
restart; those belong to the later persistent-agent identity work.

## Verification status

Verified locally with Java 25, Gradle 9.8.2, Loom 1.19.3, Fabric Loader 0.20.1,
and Fabric API 0.165.0+26.3:

- Main mod sources compile against the Minecraft 26.3 mapped classes.
- The server GameTest source compiles. It checks project-owned player
  registration, Survival mode, and cleanup from the vanilla player list and
  server level.
- Gradle wrapper distribution SHA-256 is pinned.

The GameTest has not been run. Fabric's GameTest launcher starts a Minecraft
server, and its configuration requires explicit acceptance of the Mojang EULA.
This work does not accept that agreement on the operator's behalf. No integrated
server, dedicated server, vanilla-client rendering, tracked movement,
disconnect, or runtime-failure result is claimed yet. Movement is not
implemented; the eventual action adapter must move the player through
server-authoritative vanilla mechanics rather than setting arbitrary position.

Before this becomes the v0.2 embodiment baseline, run the gated server test in
both integrated and dedicated environments, then connect an unmodded client to
verify profile/model/nameplate and entity movement synchronization. Compare
interaction, damage, inventory, death, and removal against an ordinary player.

## Reproduction

Use JDK 25 and run:

```powershell
cd minecraft-mod
./gradlew.bat compileJava compileGametestJava jar --no-daemon
```

This compile/package command avoids starting Minecraft. `runGameTest` is a
separate, EULA-gated task. Fabric's current [Loom documentation](https://docs.fabricmc.net/develop/loom/),
[automated testing guide](https://docs.fabricmc.net/develop/automatic-testing),
and [26.3 example mod](https://github.com/FabricMC/fabric-example-mod/tree/26.3)
are the upstream toolchain references used for this spike.

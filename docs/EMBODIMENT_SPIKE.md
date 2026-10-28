# Test-only server-player embodiment spike

This experiment recovers the lifecycle prototype from closed, unmerged
[PR #125](https://github.com/xdCloudy/minecraft-native-intelligence/pull/125),
head `d177480a8a498888a008319adbb036f00e4af040`, into the `gametest` source
set. It does not register a spawn command or ship an agent in the main mod.

The fixture constructs a project-owned random profile, uses vanilla player-list
registration with a no-socket packet sink, checks the player list and server
level, rejects a case-insensitive name collision, waits for server ticks, and
removes the player. Fixture placement is evaluator setup, not an agent action.
The sink is a version-specific internal seam, not a validated replacement for
Minecraft authentication or a general compatibility guarantee.

## Results and reproduction

On 2026-10-28, using Ubuntu 24.04 under WSL2, Temurin Java 25.0.4.1, Gradle
9.8.2, Minecraft 26.3, Fabric Loader 0.20.1, Loom 1.19.3 and Fabric API
0.165.0+26.3, the recovered code compiled but the first dedicated-server
GameTest failed: setting Survival mode before player registration dereferenced
the absent `ServerGamePacketListenerImpl` while constructing player-info
updates. Moving that call after `placeNewPlayer` allowed the second run to
complete: all four required server GameTests passed, including the two
embodiment tests. The server's random GameTest placement and profile UUID were
not fixed; this is a bounded smoke result, not a statistical experiment.

Reproduce in a disposable test environment, after reviewing the
[Minecraft EULA](https://www.minecraft.net/en-us/eula):

```sh
./gradlew --no-daemon -Pmni.acceptTestEula=true runGameTest
```

The flag is explicit per invocation; normal builds do not imply consent. Tests
must be run on a disposable world. The initial failure was observed before the
ordering change; the current fixture asserts the corrected behavior rather than
deliberately leaving CI red.

## Remaining gates

The experiment does not demonstrate an intelligent agent, learned behavior,
stable identity, recovery across restart, human-client rendering, tab-list
parity, interactions, death or respawn. It does not compare an ordinary player
under matched conditions, nor test integrated-server, LAN or third-party mod
compatibility. The sink and player-list lifecycle must be reviewed for failure
rollback, network and threading assumptions before any production adoption.
Keep [issue #151](https://github.com/xdCloudy/minecraft-native-intelligence/issues/151)
open until its independently tracked criteria are met.

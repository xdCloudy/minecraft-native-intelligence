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

A further local dedicated-server probe set three apples as evaluator-only
inventory setup, removed the test player and confirmed vanilla player data
contained those apples. Re-registering the same UUID through this prototype
produced an empty slot. The original expectation of restored inventory failed;
the checked-in negative test records this limitation rather than calling it a
persistence success. Source inspection of Minecraft 26.3 shows that its normal
`PrepareSpawnTask` loads player data before player placement; this prototype
constructs and registers a fresh `ServerPlayer` directly and omits that path.
The test also rejects an attempt to register the same online UUID twice.
A separate local comparison using `PrepareSpawnTask` with the same no-socket
test connection restored the three apples in the same-server rejoin. The
preparation runs asynchronously and the fixture allows up to 2,000 GameTest
ticks for chunk preparation; the first 20-tick trial timed out before it was
ready. This is not yet evidence of behavior across server restarts or of
compatibility with ordinary clients.
Loading a slot alone would not establish correct spawn location, dimension,
vehicles, identity ownership, crash recovery or restart semantics.

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

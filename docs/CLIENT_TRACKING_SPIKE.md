# Integrated-client player tracking spike

The test-only player prototype from [the embodiment spike](EMBODIMENT_SPIKE.md)
can be registered in the integrated server. This client GameTest observes the
same UUID in the modded client's level and player list, removes the fixture via
the server thread, then waits for both client records to disappear. The fixture
is created beside the local player for observation; this is evaluator setup,
not an agent action. Both waits have a 200-tick limit and cleanup runs in a
`finally` block.

On 2026-10-28, a disposable Ubuntu 24.04 container with Java 25.0.4.1,
Minecraft 26.3, Fabric Loader 0.20.1, Fabric API 0.165.0+26.3, Xvfb and Mesa
25.2.8 software Vulkan completed the production client GameTest and both
tracking checks. A separate local negative control made the arrival condition
impossible; the test failed with a predicate timeout. The positive test then
passed again using the main-branch test-only player fixture.

Reproduce on a machine with a suitable display or in the configured Linux CI
job, after reviewing the [Minecraft EULA](https://www.minecraft.net/en-us/eula):

```sh
./gradlew --no-daemon -Pmni.acceptTestEula=true runProductionClientGameTest
```

The CI job configures its virtual display and Vulkan software renderer. The
screenshot is taken before the fixture appears and is only a world-render smoke
artifact; it is not visual proof of the fixture's model. This experiment does
not establish unmodified remote-client behavior, LAN, player appearance, skin,
animation, movement, restart continuity, or Survival action parity. The
connection sink and test player remain experimental, and no intelligence or
production player is demonstrated.

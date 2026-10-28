# Minecraft mod platform and version decision

Status: recommendation for issue #1, researched 2026-09-22.

## Decision summary

Use **Fabric** as the first implementation target, pin **Minecraft Java Edition
26.3** exactly, and use **Java 25**. Keep the Minecraft-facing module
server-authoritative and avoid requiring the project mod on human clients unless a
later compatibility test proves that a client component is necessary.

This is a deliberately falsifiable recommendation. It becomes the accepted
platform decision only after the player-embodiment spike proves that an
AI-controlled, project-owned player can participate in normal vanilla player
tracking and Survival mechanics without an authenticated fake client, a required
client mod, or an unmaintainable set of core lifecycle mixins.

If that spike fails on Fabric and the equivalent NeoForge spike succeeds with
materially less loader-internal patching, prefer NeoForge instead.

## Constraints from this repository

The platform must preserve the existing project decisions:

- Java Edition mod attached to the logical server.
- `/spawn ai-agent <username>` is an operator lifecycle command.
- The AI is represented through the closest maintainable player-compatible
  server abstraction, not a custom NPC mob or authenticated bot account.
- Single-player/LAN and dedicated servers are both required.
- Human clients should remain vanilla-compatible where practical.
- Normal Minecraft health, hunger, inventory, damage, death, respawn, movement,
  interactions, permissions, scoreboards, and other Survival mechanics remain
  authoritative.
- Model/runtime process boundaries must not leak into Minecraft-facing
  semantics.

## Current upstream state

Minecraft 26.3 released on 2026-09-15. Fabric published same-day 26.3 guidance
and, at that time, specified Loom 1.17, Gradle 9.6.0, and Fabric Loader 0.19.5.
Minecraft 26.x uses Java 25.

NeoForge has an active 26.3 branch and a 26.2-to-26.3 migration primer, but its
public project listing still identified 26.2.0 as the stable line during this
review. That does not make NeoForge unsuitable; it does make Fabric the lower
risk choice for starting a new 26.3 spike today.

Quilt Loader remains active and Fabric-compatible, but Quilt Standard Libraries
were discontinued in December 2025. Quilt therefore adds another compatibility
surface without a clear project-specific advantage for the first integration.

## Comparison

| Criterion | Fabric | NeoForge | Quilt |
| --- | --- | --- | --- |
| Current 26.3 path | Official 26.3 guidance published on release day | 26.3 branch/primer active; public stable listing lagged on 26.2 during review | Loader active; relies heavily on Fabric compatibility |
| One distributable mod JAR | Supported by Loom | Supported by ModDevGradle/NeoForge | Supported |
| Integrated + dedicated logical server | Strong fit; keep common entrypoint available on the physical client and gate game logic to the logical server | Strong fit; explicit logical/physical side model | Similar to Fabric |
| Server command registration | Fabric API `CommandRegistrationCallback` | NeoForge command events/vanilla Brigadier | Fabric-compatible routes available |
| Automated in-game testing | Fabric Loader JUnit + vanilla/Fabric GameTest support | NeoForge GameTest/test framework and ephemeral test-server support | Less project-specific value than Fabric |
| Player lifecycle hooks | Fabric API exposes server-player join/leave/respawn events; deeper synthetic-player creation still needs a spike | Rich player event surface; also exposes `FakePlayer`, though its documented purpose is a player context rather than a guaranteed fully tracked remote player | Primarily inherits Fabric ecosystem options |
| Vanilla-client target | Plausible if the mod sends only vanilla-compatible state and does not require client payload handlers; must be tested | Plausible for server-only behavior when no mandatory client synchronization is introduced; must be tested | Plausible, but no advantage over Fabric for this requirement |
| Loader-specific surface | Small/lightweight; mixins are available when API hooks are insufficient | Broader patched/event API surface | Additional loader compatibility layer |
| Main risk for this project | Full player-compatible synthetic lifecycle may require too much vanilla-internal work | Extra loader/API surface and current-version release cadence; `FakePlayer` is not proof of tab-list/network/player parity | QSL discontinuation and no compelling embodiment benefit |

## Why Fabric is the initial recommendation

### 1. It is ready on the selected current Minecraft baseline

Fabric published explicit 26.3 development guidance when Minecraft 26.3
released. Starting on 26.3 avoids creating a new implementation on a game
version that would immediately need porting.

### 2. The project can keep a single server-authoritative codebase

Fabric distinguishes physical environment from logical server behavior. The mod
must **not** use a dedicated-server-only loader declaration because that would
exclude single-player/LAN, whose logical server runs inside the physical client.
Instead, load the common mod in both physical environments and execute
Minecraft-changing logic only on the logical server.

That directly matches the project's existing integrated/dedicated server model.

### 3. Commands and tests are first-class enough for the v0.2 spike

Fabric API provides Brigadier command registration, including server-environment
information and permission predicates. Fabric also documents unit tests,
server/client GameTests, and production-like server run tasks. Those are enough
to build the first reproducible embodiment and Survival-parity harness without
using GitHub Actions as the development loop.

### 4. Fabric does not prematurely dictate the research runtime

The Minecraft module can remain a small Java boundary and later communicate
with an in-process or out-of-process research runtime. Selecting Fabric does not
select Python versus Java, an inference runtime, model family, persistence
engine, or training framework.

## The important uncertainty: player embodiment

Neither loader's existence proves the hard requirement: a persistent
AI-controlled player that vanilla clients and server systems treat sufficiently
like an ordinary player while no authenticated network client exists.

NeoForge documents `FakePlayer` as a `ServerPlayer` subclass intended to provide
a player context for non-player mechanisms. That is useful evidence, but it is
not itself evidence that a fake player is automatically:

- added to ordinary player tracking and the tab list;
- synchronized to unmodified clients exactly like a connected player;
- covered by normal death/respawn/dimension transitions;
- saved and loaded through the desired persistent lifecycle; or
- compatible with third-party systems that assume a real connection/session.

Fabric exposes ordinary `ServerPlayer` lifecycle events but does not provide an
equivalent high-level guarantee for a synthetic player. The next step therefore
must be a narrow comparative embodiment spike, not an assumption.

## Required embodiment spike

Implement the smallest possible Fabric 26.3 prototype on a dedicated branch.

1. Build one mod JAR with pinned Minecraft, Fabric Loader, Fabric API, Loom,
   Gradle, and Java versions.
2. Register an authorized `/spawn ai-agent <username>` command using vanilla
   Brigadier/Fabric command registration.
3. Allocate a project-owned UUID/profile without authenticating or
   impersonating a real Minecraft account.
4. Create the closest maintainable `ServerPlayer`-compatible instance.
5. Integrate it through the least invasive vanilla player tracking/lifecycle
   path available.
6. Connect an **unmodified 26.3 client** to the dedicated server.
7. Verify at minimum:
   - visible player model, nameplate, skin path, held item and equipment;
   - entity tracking, collision, damage, knockback and effects;
   - tab-list and scoreboard/team behavior;
   - movement and ordinary block/entity interaction;
   - inventory, hunger, health and game mode;
   - death and respawn;
   - dimension transition;
   - save, server restart and reload of the same project identity.
8. Repeat the lifecycle-relevant checks in the integrated single-player server.
9. Capture every mixin/invasive hook required by the spike and classify it as
   stable API, vanilla call, access widening, or bytecode injection.
10. Add automated GameTests/contract tests wherever the behavior can be tested
    headlessly.

The spike is not the intelligence implementation. It should use deterministic,
minimal movement/actions only to prove the platform boundary.

## Falsifiers

Reject Fabric as the preferred loader if any of these remain true after a
reasonable focused spike:

- Vanilla clients cannot observe/interact with the synthetic player without
  installing a project client mod.
- Correct tracking requires constructing a fake authenticated network session.
- The player cannot survive save/load, death/respawn, or dimension changes using
  maintainable vanilla/server lifecycle paths.
- Correct behavior needs broad patches across multiple unrelated core classes
  rather than a small, documented compatibility layer.
- A minor supported Minecraft update repeatedly breaks the same lifecycle hooks
  with no stable API boundary.
- A matched NeoForge spike satisfies the same tests with substantially less
  invasive loader-internal or vanilla-internal patching.

Conversely, do **not** switch to NeoForge merely because it exposes `FakePlayer`;
the NeoForge spike must prove the same visibility, lifecycle and vanilla-client
requirements.

## Version policy

For the first implementation:

- Minecraft: pin exactly 26.3.
- Java: pin toolchain 25.
- Loader/API/build plugins: pin exact versions known to support 26.3; do not use
  floating latest dependencies in reproducible builds.
- Snapshots, pre-releases and release candidates are research-only and never
  silently replace the baseline.
- Support one production research baseline at a time until the v0.2
  compatibility suite exists.

For upgrades:

1. Open an explicit version-upgrade issue/PR.
2. Record Minecraft, Java, loader, API, mappings/naming, Gradle and plugin
   changes.
3. Run the embodiment, Survival-parity, information-access and persistence
   suites locally.
4. Test both integrated and dedicated servers.
5. Test an unmodified client whenever vanilla-client compatibility is claimed.
6. Record migration/save implications.
7. Promote the new baseline only after the suite passes; do not make normal
   feature PRs double as version migrations.

This gives reproducibility without treating 26.3 as a permanent lock-in.

## Installation/update user journey

Initial operator journey:

1. Install the exact supported Java and Fabric Loader versions.
2. Place the project mod JAR (and declared Fabric API dependency, if not bundled)
   in the instance/server mods directory.
3. Launch the world/server and check the mod's startup compatibility report.
4. Run `/spawn ai-agent <username>` as an authorized operator.

A dedicated server should not require ordinary human players to install the
project mod if the compatibility spike confirms vanilla protocol behavior.

Upgrades should be explicit: back up the world and agent state, replace the
pinned mod/loader versions according to release notes, run startup migration
checks, then start the world. Downgrades across save/schema migrations are not
assumed safe.

## Migration cost

Changing loader after substantial implementation would cost:

- build metadata and Gradle plugin changes;
- event/command/test API replacements;
- mixin/access-widener versus NeoForge patch/access-transformer differences;
- packaging/install documentation;
- compatibility test updates; and
- potentially the synthetic-player lifecycle implementation itself.

To limit lock-in, keep the core project contracts loader-neutral: observations,
actions, identity/persistence messages, runtime IPC, and evaluation schemas must
not contain Fabric types. Loader-specific code belongs behind the Minecraft
integration boundary.

## Primary sources

Fabric:

- [Fabric for Minecraft 26.3](https://www.fabricmc.net/2026/09/15/263.html)
- [Fabric developer guides](https://docs.fabricmc.net/develop/)
- [Fabric Loader](https://docs.fabricmc.net/develop/loader/)
- [fabric.mod.json environments](https://docs.fabricmc.net/develop/loader/fabric-mod-json)
- [Fabric command registration](https://docs.fabricmc.net/develop/commands/basics)
- [Fabric automated testing](https://docs.fabricmc.net/develop/automatic-testing)
- [Fabric production run tasks](https://docs.fabricmc.net/develop/loom/production-run-tasks)

NeoForge:

- [NeoForge documentation](https://docs.neoforged.net/)
- [NeoForge player/entity hierarchy](https://docs.neoforged.net/docs/entities/livingentity/)
- [NeoForge GameTests](https://docs.neoforged.net/docs/misc/gametest/)
- [NeoForge events](https://docs.neoforged.net/docs/concepts/events/)
- [NeoForge 26.2 to 26.3 migration primer](https://docs.neoforged.net/primer/docs/26.3/)
- [NeoForge project listing](https://projects.neoforged.net/neoforged/neoforge/)
- [NeoForge 26.3 branch](https://github.com/neoforged/NeoForge/tree/26.3.x)

Quilt:

- [Quilt project overview](https://quiltmc.org/en/about/)
- [Quilt FAQ](https://quiltmc.org/en/about/faq/)

## 2026-10-27 executable Fabric 26.3 baseline spike (#151)

The root Gradle project introduces an installable *platform probe*
only; it logs Fabric initialization and logical-server start without modifying
world state or creating a player. It does **not** prove Minecraft-native AI
embodiment or complete the spike defined above.

The merged platform probe pins Minecraft `26.3`, Java `25`, Fabric Loader
`0.20.1`, Fabric API `0.165.0+26.3`, Fabric Loom `1.19.3`, and Gradle
`9.8.2`. These follow the [official Fabric 26.3 example template](https://github.com/FabricMC/fabric-example-mod/tree/26.3)
and the current [Fabric API releases](https://github.com/FabricMC/fabric-api/releases).
The [release-day Fabric guide](https://www.fabricmc.net/2026/09/15/263.html)
listed older tool versions; those historical values above were valid at its
publication, but are not this experiment's exact pinned build inputs.

The Gradle wrapper scripts/JAR were taken from the official 26.3 example
template; wrapper JAR SHA-256 is
`3b8a25775a69158b5ad2b1d17a80a88dc7b40a352a73eb27d06c612a7ce68e98`.
No game JAR, Mojang assets, skins, player data or model checkpoints are bundled.

### Evidence gates (all distinct)

| Gate | Evidence status |
| --- | --- |
| Java 25 Gradle compile and build JAR | **Build passed** in [GitHub Actions run 64](https://github.com/xdCloudy/minecraft-native-intelligence/actions/runs/40604852954), using JDK 25.0.4 and Loom 1.19.3; Java test task had NO-SOURCE |
| Dedicated logical-server launch and mod event | **T4 smoke validated:** [CI run 75](https://github.com/xdCloudy/minecraft-native-intelligence/actions/runs/40615220964) logged `dedicated=true`, loaded both main and test mods, and passed the GameTest suite |
| Integrated single-player/LAN logical-server launch | **Single-player smoke passed:** [CI run 40659615906](https://github.com/xdCloudy/minecraft-native-intelligence/actions/runs/40659615906); LAN is still untested. |
| Vanilla-client compatibility and profile/tab-list presentation | Untested |
| Project-owned player embodiment, Survival parity, death/respawn | Untested |
| Loader comparison/decision and accepted ADR | Untested; ADR-0008 stays proposed |

Use Java 25 for this pinned Minecraft version. A Java 17 build failure is not
evidence of a Fabric incompatibility. Player parity requires separate tests.

### Opt-in dedicated-server GameTest gate (2026-10-28)

The spike now registers an experimental Fabric server GameTest from
`src/gametest`. Its evaluator-only world fixture asserts that a real server can
load and execute the test mod. The test is intentionally **not** an AI player,
Survival legality, vanilla-client, integrated-server or autonomy test.

The repository owner authorised accepting the Minecraft EULA for disposable
development/CI test environments on 2026-10-28. **Consent is invocation-scoped.**
Running a normal local build does not silently accept the EULA. An operator
must explicitly pass:

```sh
./gradlew --no-daemon -Pmni.acceptTestEula=true build test
```

Read the [Minecraft EULA](https://www.minecraft.net/en-us/eula) before setting
this flag in another environment. The Minecraft CI job uses this flag for its
temporary hosted test world; test logs/reports are retained on failure and test
worlds are not committed. A successful GameTest proves server boot and a
minimal world assertion **only**. It cannot promote MI-01/MI-004/MI-005/MI-008/
MI-009 or ADR-0008 without the substantive player lifecycle/parity evidence
listed earlier. [CI run 75](https://github.com/xdCloudy/minecraft-native-intelligence/actions/runs/40615220964)
reported `runGameTest`, actual server initialization (`dedicated=true`),
**2/2 required tests passed in 1.916 seconds**, and a successful Java 25 Gradle
build in 57 seconds. The MNI-specific server-world fixture is one of those
GameTests; no player lifecycle or end-to-end model behavior was tested. The
server's initial missing `eula.txt`/properties warnings did not prevent the
Fabric test runner from starting under its explicit EULA test configuration.
The probe and its CI evidence were merged in [PR #221](https://github.com/xdCloudy/minecraft-native-intelligence/pull/221).

### Integrated single-player client GameTest (#151)

Fabric provides a separate client GameTest mechanism: `runClientGameTest` for
development and a [production client test task](https://docs.fabricmc.net/develop/automatic-testing)
for CI. The project now adds `MniIntegratedWorldGameTest` and an independent
`runProductionClientGameTest` CI job. The test creates an integrated single-player
world, waits for client chunks to render, and captures a screenshot; the hosted
job uses a virtual framebuffer and software rendering. The main dedicated-server
GameTest remains a separate gate, so failure of the client test cannot be
mistaken for a successful world-parity check.

The pinned Fabric API `0.165.0+26.3` exposes
`TestSingleplayerContext.getConnection().waitForChunksRender()`; earlier
Fabric tutorials show `getClientLevel()`, which is not present in this pinned
version. Compilation must be checked against the exact API, not a floating doc.

The first hosted production-client trial ([CI run #81](https://github.com/xdCloudy/minecraft-native-intelligence/actions/runs/40617975160))
compiled and passed the dedicated-server tests but **did not boot the client**:
Minecraft SDL3 reported `Couldn't find matching GLX visual`; Vulkan also
lacked its surface extension. The job timed out after 20 minutes. The retry
also failed in [CI run #83](https://github.com/xdCloudy/minecraft-native-intelligence/actions/runs/40620255071)
after `glxinfo` reported OpenGL 4.5: the SDL window could not obtain a matching
visual, and Vulkan lacked its surface extension. A passing `glxinfo` is therefore
not proof that the Minecraft window can start.

In a local disposable Ubuntu 24.04 container, Java 25.0.4.1, Mesa 25.2.8,
Xvfb and Mesa's software Vulkan driver launched the client after OpenGL failed.
The production task initially exited successfully without loading the test mod
or running any tests. Packaging the separate GameTest source set as a test-only
JAR and including it in the production launch loaded the entrypoint, started an
integrated world, rendered chunks and produced the screenshot. The CI job now
installs the Vulkan driver and requires a fresh screenshot so an empty test run
cannot pass silently. The screenshot is an execution marker, not an automated
visual correctness assertion. [Hosted CI run 40659615906](https://github.com/xdCloudy/minecraft-native-intelligence/actions/runs/40659615906)
passed against PR head `84d355b5f106082ccb65884dd508cf461229a353` and retained
the screenshot and logs as a short-lived artifact.

This integrated world smoke test does not establish LAN networking,
vanilla remote-client presentation, a player-compatible AI, persistence,
Survival mechanics or a Fabric-vs-NeoForge comparison. Each needs its own
reproducible acceptance test before associated tracker statuses advance.

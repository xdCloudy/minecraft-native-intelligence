# Information access and partial-observability rules

Status: v0.2 information-access baseline for issue #7.

## Purpose

The native Minecraft interface runs on an authoritative server that can inspect
far more state than an ordinary player can legitimately know. This document
defines which facts may cross from server state into an AI player's policy
observation.

The goal is **access equivalence**, not pixel equivalence.

A structured interface may identify a block, entity, sound, item, or status
precisely once that fact is legitimately available to the embodied player. It
must not use server authority to reveal a fact that the player could not
currently sense, receive through normal player UI, or know from its own state.

This deliberately avoids two bad extremes:

- forcing the core project back into screenshots/OCR merely to imitate human
  classification difficulty; and
- treating "the server knows it" as permission for the agent to know it.

## Binding rule

A policy-visible observation field is allowed only when all of the following are
true:

1. it belongs to a declared information channel;
2. its source fact satisfies the access rule attached to that field;
3. the fact is within the current channel's distance/time/visibility bounds;
4. no rule-specific occlusion, privacy, ownership, or server-policy condition
   blocks it;
5. the field describes current observation rather than silently substituted
   memory/inference;
6. its validity/unknown/stale state is explicit; and
7. no privileged/debug exception is active unless the evaluation declares it.

Missing evidence is **unknown**, not false and not empty.

A loaded chunk containing no currently observable surface does not become known
air. A player hidden behind a wall does not become known absent. A stale memory
of a chest does not become a current chest observation.

## Access equivalence versus perceptual difficulty

The baseline does not attempt to reproduce the exact difficulty of identifying
pixels, listening to waveform details, reading fonts, or manipulating GUI
widgets.

For example:

- a visible stone block may be represented by a structured block identity
  instead of asking a vision model to classify its texture;
- an audible vanilla sound may be represented by a stable sound-event token
  instead of raw audio;
- a server-delivered chat message may be represented as text instead of rendered
  glyph pixels.

The fairness boundary is **whether the fact was legitimately available**, not
whether a human needed a particular sensory classifier to decode it.

Any experiment specifically studying pixel/audio perception can use a stricter
comparison profile, but that is not the core interface.

## Channels

Every policy-visible field belongs to one of these channels.

| Channel | Meaning | Baseline access |
| --- | --- | --- |
| `self` | Agent's embodied internal/player state | Exact where it is genuinely self-owned or ordinary HUD/inventory state |
| `vision` | Current visually available world/entity facts | Frustum + distance + client-equivalent availability + occlusion/effect rules |
| `audio` | Sound events an ordinary client/player could hear | Client-equivalent delivery/range; no exact hidden source state |
| `chat` | Messages delivered to the player by ordinary chat/social rules | Exact delivered content, scoped by recipient/channel/server policy |
| `ui` | Ordinary player-facing non-debug UI state | Explicit capability only; never host/admin UI |
| `outcome` | Consequences/rejections of this agent's own actions | Exact typed outcome where the action system legitimately knows it |
| `memory` | Prior observations retained by the agent | Explicitly stale/provenanced; never relabelled as current sensing |
| `protocol` | Sequence/time/schema metadata used to make the interface reliable | Available to runtime/evaluator; policy exposure is separately controlled |
| `privileged` | Evaluator/operator/debug information | Disabled for baseline policy input |

## Baseline profile

The canonical v1 profile is `player-equivalent.v1`.

### Camera/frustum

The profile uses a **70-degree horizontal base field of view**, matching the
documented Java Edition default FOV. Minecraft lets players change FOV, so
experiments may define another value, but it must be pinned in the scenario and
reported in results.

Vertical frustum is derived from the same camera projection and the declared
aspect-ratio/profile assumptions rather than independently granting a larger
vertical cone.

Effects or mechanics that intentionally change the normal player's view, such
as zoom, blindness/darkness-like effects, immersion in fluids, portals, or
environment fog, must be reflected by the visual filter when they materially
change what an ordinary player can see.

A policy does not receive a permanent 360-degree visual map merely because a
human could turn around. Turning/look orientation is part of embodied action.

### Visual distance

Every scenario/profile must declare an effective visual distance.

The filter must also respect the effective client/server render/tracking
availability for the tested configuration. The smaller applicable bound wins.

Server simulation distance, loaded-chunk state, ticket state, entity activation,
or other server-internal residency is **not** a perception grant. Minecraft
separates render/client chunk availability from simulation state, and server
internals can remain available beyond what a player sees.

No evaluation may compare two policies under different effective visual
distance without declaring that difference.

### Visual occlusion

A world/entity fact is visually available only when the tested representation
has client-equivalent visible evidence.

For structured server-side filtering, the baseline uses conservative visibility
tests:

- candidate is inside the active visual frustum;
- candidate is inside the declared visual distance;
- relevant chunk/entity data is eligible for client-equivalent presentation;
- at least one defined sample/ray to the visible surface/bounding volume is not
  blocked by occluding geometry; and
- visual effects/environment rules do not suppress it.

The implementation must not dump an entire radius of voxels and call the radius
"vision".

For blocks, the baseline exposes **visible surface facts**, not all blocks
behind those surfaces. A visible face can justify the structured identity/state
of that block, but not unseen blocks behind it.

For entities, one or more visible sample points may justify current entity
presence. Exact sampling strategy is an implementation detail that requires
conformance tests for narrow openings, partial blocks, large entities, and edge
cases.

### Transparent and partial geometry

Glass and other transparent/partial blocks cannot be treated as opaque merely
to simplify implementation if an ordinary player can see through them.

Likewise, a block being non-solid does not automatically mean every ray should
pass through it.

The adapter should prefer Minecraft/client geometry and ray/collision/visual
shape semantics where maintainable. Ambiguous materials receive explicit
fixtures.

### Vanilla mechanics that intentionally reveal through occlusion

Some ordinary gameplay/UI mechanics can reveal otherwise occluded information,
for example an entity with a visible glowing outline.

Such facts may be exposed only through an explicit **mechanic-derived visual
cue** rule. The interface must record why ordinary occlusion was bypassed.

This is different from using hidden server state directly.

## Darkness, lighting, weather, and fog

Lighting/fog can affect whether a human can distinguish a world fact. The
structured interface must not ignore that merely because the server can resolve
an entity or block ID.

Baseline rules:

- exact server light-engine values are not passively policy-visible merely
  because they exist;
- light values may be used internally by the visibility filter;
- environment visual attributes/effects may reduce or mask current vision;
- weather/fog/fluid/portal effects that change normal rendering must be
  represented in filtering or in an explicit visibility-quality field;
- debug-overlay light values are privileged unless a separate comparison
  profile enables them.

A first implementation may use a conservative threshold/visibility-quality
approximation if exact client-render equivalence is impractical, but that
approximation must be documented and tested as a known limitation rather than
silently granting full night vision.

## Self/proprioceptive state

The agent may receive exact current self-owned state needed for embodied
control, including fields in these classes when the observation schema defines
them:

- position in the agent's local/world coordinate frame;
- orientation/look direction;
- motion/velocity;
- grounded/falling/swimming/climbing/riding/pose state;
- health, absorption, hunger/saturation where selected, air, fire/freeze and
  ordinary status/needs;
- currently selected slot, held/equipped items;
- own inventory contents and stack counts;
- own armour/equipment/durability where normally inspectable;
- own active status effects;
- own game mode/capability restrictions relevant to legal actions; and
- own action/cooldown state where needed to interpret outcomes.

This is treated as structured proprioception/HUD/inventory access rather than a
claim that humans perceive exact floating-point coordinates internally.

### Self-state exclusions

Do not expose by default:

- implementation object references;
- server memory addresses;
- host paths;
- connection/session internals unrelated to gameplay;
- hidden NBT/components that an ordinary player cannot inspect and that do not
  affect currently available player-facing behavior;
- administrator permission internals beyond the capability consequences the
  agent actually has; or
- secret/authentication identifiers.

Exact policy-facing coordinate precision must be declared by the observation
schema. Protocol/evaluator metadata may retain higher precision for replay.

## Other entities

A visually sensed entity may expose only current player-facing properties.

Candidate allowed classes include:

- stable observation-local entity reference;
- visible entity type/variant when visually distinguishable;
- relative position/orientation/motion to the precision selected by the schema;
- visible pose/animation;
- visible held/equipped items;
- visible nameplate/display name when Minecraft would present it;
- visible fire/effects/markers; and
- other appearance state required to reproduce ordinary player-facing
  interaction.

Do not pass by default:

- exact health of another entity where no normal UI exposes it;
- hidden inventory;
- private memory/state;
- AI model/runtime identity;
- internal UUID solely because the server has one;
- target/pathfinding brain state;
- hidden potion/effect data with no player-facing cue;
- exact hostility/intent labels; or
- entities outside the permitted visual/audio/UI channels.

A visible entity can later be associated with memory, but that association must
come from the agent's own history, not a hidden server lookup.

## Blocks, terrain, and objects

A current visual observation may describe a block/object when it has
legitimately visible evidence.

Allowed structured facts can include:

- visible block identity;
- visible block state that affects appearance/interaction;
- visible face/geometry;
- relative coordinate;
- visible fluid state;
- visible block entity presentation needed for ordinary interaction; and
- interactability/collision facts that can be directly experienced or are part
  of the selected native representation.

Do not expose:

- blocks behind occluding surfaces;
- containers' contents without legitimate opening/inspection;
- hidden redstone/container/internal state not externally visible;
- loot-table future outcomes;
- ore/decorated structure data in unseen terrain;
- structure locations from server registries;
- world-generation seed;
- unloaded/unseen chunk contents; or
- future scheduled updates.

## Negative evidence and "not seen"

A sensor may report absence only inside a region for which the access filter can
guarantee adequate current coverage.

Examples:

- "no visible entity in this currently observed open area" may be valid;
- "there is no entity behind that wall" is not valid;
- "that unloaded chunk is empty" is not valid;
- "the remembered chest is gone" is not valid until the location is legitimately
  observed again.

Schemas should distinguish at least:

- observed present;
- observed absent;
- unknown/not currently observed; and
- remembered/stale.

This distinction is mandatory for world-model and memory research.

## Chunk loading and server residency

Chunk state is a major leakage risk.

Baseline rules:

- loaded/ticking/simulation status is infrastructure metadata, not world
  perception;
- the policy cannot query arbitrary loaded chunks;
- unloaded chunks cannot be materialized solely for observation;
- an implementation must not cause chunk loads just to satisfy a sensor query
  unless that load would occur for the equivalent player configuration;
- absent data from an unloaded/not-client-available chunk is `unknown`, not
  air/empty/no-entity; and
- remembered terrain keeps its own observation timestamp/provenance.

Minecraft's render and simulation distances are separate concepts. The project
must not use simulation availability as a shortcut for vision.

## Audio

Audio is a separate channel and is **not** subject to visual line-of-sight.

Vanilla Minecraft sound events may be audible through geometry that blocks
vision. The filter therefore follows client-equivalent sound delivery/range
rather than imposing invented real-world acoustic occlusion.

Baseline audible event fields may include:

- stable sound-event token;
- category;
- perceived/relative direction;
- coarse relative distance or attenuation;
- pitch/volume cues when player-facing; and
- observation time.

Do not pass by default:

- exact hidden source coordinates when a player only receives an audible cue;
- source UUID/internal entity reference unless independently associated through
  legitimate sensing;
- server-only sounds that would not be sent/played for the player;
- events outside client-equivalent audible range; or
- hidden block/entity state inferred directly from the event source object.

Current Fabric documentation notes that logical-server sound playback is
broadcast to clients in tracking range and that vanilla distance scales with
sound volume (roughly `volume * 16` blocks for the documented API). The
implementation should reuse/track the actual player-facing sound dispatch path
where practical instead of inventing one global sound radius.

### Captions/subtitles

Java Edition supports captions/subtitles, and Minecraft 26.3 changed subtitles
to point to the most recent sound in range.

The v1 structured audio channel may use caption-equivalent sound identity and
directional information because it is ordinary player-facing accessibility
information.

Experiments that disable caption-equivalent information must declare the audio
profile difference.

## Chat and social messages

Chat is not vision and does not require physical line-of-sight unless the server
or installed communication system imposes such a rule.

The policy may receive exact text for messages that the equivalent player would
receive through the active server/chat rules, including:

- public chat;
- direct/private messages addressed to the player;
- team/channel messages delivered to that player; and
- relevant ordinary system/game messages when they are part of player
  experience.

Do not expose:

- console-only/operator logs;
- other players' private messages;
- moderation/admin metadata not shown to the recipient;
- deleted/filtered message internals not delivered to the player;
- host/plugin logs; or
- unrelated external communication.

Chat collection/training remains subject to `DATA_GOVERNANCE.md`; legitimate
in-world delivery does not itself grant dataset consent.

## Player list, scoreboards, boss bars, and ordinary UI

Normal player-facing UI may be represented through the `ui` channel when the
capability is explicitly enabled.

Examples include:

- player-list/tab presentation;
- scoreboard/team values visible to that player;
- boss bars;
- advancement/toast notifications;
- normal container/menu contents while legitimately opened; and
- other data the ordinary client receives specifically for display to that
  player.

UI availability must not become a route to underlying server objects that were
never displayed.

## Debug overlay and developer information

The canonical baseline excludes facts available only through developer/debug
interfaces, including F3-only exact diagnostic state, debug commands, server
console, profiler data, chunk tickets, entity AI goals, or admin inspection.

Java players can access some debug information in ordinary installations, but
the project's native-reality constraint treats debug/developer state as a
separate comparison capability rather than baseline perception.

An experiment may enable a debug profile, but:

- every added field is marked `privileged`;
- the scenario declares it;
- the result records actual use; and
- the experiment cannot be presented as the baseline player-equivalent
  information condition.

## Recipes and crafting knowledge

Recipe knowledge is not passively dumped into every observation.

Minecraft's recipe book is a normal player UI, but the exact catalog,
unlock, and search behavior is version-sensitive. The server's complete recipe
registry therefore cannot be treated as equivalent to what the player-facing UI
currently presents. At the same time, this project's larger research
question—what mechanics/affordances should be structured versus learned—is
intentionally unresolved.

Therefore v1 adopts this boundary:

- current crafting/inventory outcomes are ordinary observations;
- opening/querying a recipe-book-equivalent UI may be an explicit `ui`
  capability in a declared experiment;
- a complete structured recipe graph is **not** a passive sensory field;
- server recipe registries cannot be injected as hidden omniscient state; and
- #73 remains responsible for deciding the long-term structured-knowledge versus
  learned-world-model boundary.

This avoids making #7 silently decide a later learning question.

## Time and weather

The interface needs exact sequence/game-time metadata for replay and ordering,
but protocol metadata is not automatically policy perception.

The policy may observe:

- visible sky/weather/environment cues;
- ordinary clock/item/UI cues when legitimately available; and
- coarse or structured environmental state explicitly justified by ordinary
  player-facing information.

Exact server tick, world age, scheduled-event timers, or future weather are
`protocol`/privileged metadata unless the observation schema separately
justifies them.

## Action outcomes

The agent may receive exact typed outcomes of its own requested actions because
those outcomes are part of the legal-action interface.

Examples:

- accepted/rejected;
- rejection reason at the semantic level;
- started/cancelled/completed;
- item consumed/obtained by the agent;
- block interaction success;
- damage received; and
- cooldown/availability consequence.

The outcome channel must not leak hidden target/world state merely to explain a
failure.

For example, an attack rejected because the target is not currently reachable
can report `out_of_reach`; it need not reveal the target's hidden exact
position/path state.

## Memory versus observation

Memory is never silently refreshed from authoritative server state.

A memory record can preserve:

- what was observed;
- when/where it was observed;
- confidence;
- source channel; and
- later contradictions/updates.

When a location/entity leaves current access:

- its live state disappears from current observations;
- retained knowledge moves through the memory boundary;
- age/staleness remains explicit; and
- re-observation is required to claim current truth.

A server query must not "help" memory by checking whether an unseen remembered
fact is still true.

## Protocol metadata versus policy-visible data

Reliable systems require metadata that a human player would not conceptualize,
such as:

- agent/session IDs;
- schema versions;
- sequence numbers;
- exact server tick;
- trace IDs; and
- transport timestamps.

These values may exist in observation envelopes for ordering, replay, routing,
or evaluation while being masked from the learned policy.

Every observation field in #3 must declare:

- `access_rule_id`;
- `channel`;
- `policy_visible`;
- `source`;
- `validity/unknown semantics`; and
- any units/frame/version.

A protocol field with `policy_visible: false` is not evidence available to the
agent's decision model.

## Operator/evaluator exceptions

Operator and evaluator systems may need privileged state to:

- set up/reset scenarios;
- score outcomes;
- test leakage;
- inspect failures;
- administer agents; or
- debug implementation.

These channels are isolated from policy input.

Baseline requirements:

- privileged fields are disabled at the policy boundary;
- capability checks prevent accidental inclusion;
- scenario manifests enumerate any exception;
- result manifests record actual privileged use;
- logs/traces distinguish evaluator observation from agent observation; and
- a policy-exposed privileged exception sets the corresponding evaluation
  `baseline_claim_valid` field to false.

No "temporary debugging" shortcut may silently become training data.

## Server/mod/plugin effects

Player-equivalent information can change with installed server systems.

Examples:

- proximity-chat mods change who receives chat/audio;
- map/minimap mods may expose extra spatial UI;
- permissions plugins alter commands/UI;
- custom glowing/scoreboard mechanics expose otherwise hidden entities/data.

Evaluation scenarios must list relevant mods/plugins and capabilities.

The adapter uses the tested configuration's player-facing behavior rather than
assuming vanilla when it is not vanilla.

Compatibility-specific information channels require explicit profile rules and
must not silently enlarge the canonical baseline.

## Rule IDs

Machine-readable rule definitions live in
`docs/information_access/rules.v1.json`.

Observation schema fields should reference one or more stable rule IDs. The core
v1 IDs are:

| Rule ID | Summary |
| --- | --- |
| `ia.self.owned_state` | Exact self/proprioceptive/HUD/inventory state within declared schema |
| `ia.visual.frustum` | Candidate must be within active camera frustum |
| `ia.visual.distance` | Candidate must be within declared client-equivalent visual bound |
| `ia.visual.occlusion` | Visible evidence must survive geometry/effect filtering |
| `ia.visual.surface_only` | No hidden voxel/entity state behind visible surfaces |
| `ia.entity.visible_properties` | Only current player-facing entity properties |
| `ia.audio.client_delivery` | Sound must be client-equivalent audible/delivered |
| `ia.chat.recipient_delivery` | Message must be delivered to this player |
| `ia.ui.player_facing` | Only ordinary non-debug UI state explicitly enabled |
| `ia.world.chunk_not_authority` | Loaded/simulated chunk state never grants perception |
| `ia.negative.coverage_required` | Absence requires guaranteed current sensor coverage |
| `ia.memory.no_authoritative_refresh` | Memory updates only through legitimate re-observation/evidence |
| `ia.protocol.mask_from_policy` | Reliability metadata is not automatically model input |
| `ia.outcome.own_action` | Own semantic action outcomes are observable without hidden diagnostics |
| `ia.knowledge.recipe_ui_explicit` | Recipe UI is explicit; no passive full recipe registry |
| `ia.privileged.baseline_off` | Debug/evaluator/admin state is isolated and baseline-disabled |

## Threat model

Primary leakage threats include:

### Radius dump leakage

Implementation serializes every block/entity within N blocks.

**Failure:** walls/caves/underground ores/mobs become omniscient.

**Control:** frustum + visible-surface/occlusion filtering before serialization.

### Chunk-residency leakage

Policy sees whether a chunk is loaded/ticking or receives an empty list for an
unloaded chunk.

**Failure:** server implementation state becomes world knowledge.

**Control:** loaded state is policy-hidden; unavailable coverage becomes
`unknown`.

### Exact hidden entity metadata

Visible entity observation includes exact health, inventory, UUID, target,
pathfinding destination, or effects.

**Failure:** server object access exceeds player-facing evidence.

**Control:** explicit entity property whitelist and rule IDs.

### Negative-space oracle

No entities are returned, and downstream code interprets that as "there are no
entities" even where vision is occluded.

**Failure:** absence becomes wallhacks.

**Control:** coverage masks/unknown semantics.

### Debug metadata bleed

Exact tick, F3/debug values, evaluator labels, trace annotations, scenario
targets, or reward components enter policy tensors.

**Failure:** benchmark shortcut/ontology violation.

**Control:** policy-visible mask and schema contract tests.

### Memory refresh oracle

Persistent memory quietly queries live server state.

**Failure:** an agent "remembers" changes it never witnessed.

**Control:** memory provenance and no-authoritative-refresh rule.

### Evaluation label leakage

Ground-truth target coordinates/labels share the same structure or batch as
policy observations.

**Failure:** task can be solved using evaluator state.

**Control:** process/type separation plus explicit privileged channel.

### Cross-agent leakage

Shared batching accidentally includes another agent's visible entities, private
chat, inventory, memory, or labels.

**Failure:** privacy/identity and partial-observability violation.

**Control:** agent/session ownership on every observation and isolation tests.

## Required conformance scenarios

The implementation in #62 and schema in #3 must support deterministic fixtures
for at least the following cases.

### IA-01 — Hidden block behind opaque wall

Setup:

- agent faces an opaque wall;
- a distinctive block sits directly behind it;
- both chunks are loaded/simulated.

Expected:

- wall surface is observable;
- hidden block identity is not current visual observation;
- no absence/presence claim behind the wall is emitted.

Failure indicates radius/chunk-state leakage.

### IA-02 — Hidden entity behind opaque wall

Setup:

- visible empty corridor ends at an opaque wall;
- entity moves behind the wall inside server tracking/simulation range.

Expected:

- entity is absent from visual channel;
- if it emits an audible sound, only permitted audio information appears;
- exact hidden entity position/health/inventory never appears.

### IA-03 — Out-of-frustum visible entity

Setup:

- unobstructed entity is behind the current look direction but inside distance
  bounds.

Expected:

- no visual entity observation before turning;
- turning into the frustum permits observation.

This detects accidental 360-degree vision.

### IA-04 — Transparent window

Setup:

- entity is behind clear glass within frustum/range.

Expected:

- visual filter permits the entity when normal client presentation permits it;
- glass itself remains observable.

This prevents an over-conservative "all blocks occlude" shortcut.

### IA-05 — Partial opening/large entity

Setup:

- entity is partially visible through a doorway/fence/partial block.

Expected:

- defined sample-point visibility produces stable documented behavior;
- fixture guards against all-center-ray/all-corners-only regressions.

### IA-06 — Loaded but client-unavailable chunk

Setup:

- server keeps a distant chunk loaded for another reason;
- agent's declared visual/client availability excludes it.

Expected:

- no block/entity data from that chunk;
- no loaded/ticking flag;
- coverage is unknown.

### IA-07 — Unloaded remembered location

Setup:

- agent observes a chest;
- leaves until location is unavailable;
- world changes while away.

Expected:

- current sensor does not reveal the change;
- memory can retain old chest fact with timestamp;
- update occurs only after legitimate re-observation.

### IA-08 — Darkness/fog impairment

Setup:

- same visible target under normal and declared low-visibility/effect state.

Expected:

- visibility/quality follows the selected profile;
- exact hidden light-engine/debug values do not appear.

### IA-09 — Sound behind wall

Setup:

- sound source is visually occluded but inside client-equivalent audible range.

Expected:

- audio cue is present;
- visual entity/block state remains hidden;
- cue does not include exact hidden source coordinates unless independently
  justified.

### IA-10 — Sound outside range

Expected:

- no audio event;
- server event existence cannot be inferred from an empty hidden channel.

### IA-11 — Global and private chat

Setup:

- one public message;
- one direct message to the agent;
- one direct message between two other players;
- one console/operator log line.

Expected:

- agent receives public + addressed direct message;
- does not receive other-player DM or console log.

### IA-12 — Own versus other inventory

Expected:

- own inventory is available;
- another player's hidden inventory is not;
- visible held/equipped items may be observed through vision.

### IA-13 — Evaluator target isolation

Setup:

- evaluator knows target block/entity coordinates to score task.

Expected:

- evaluator can score;
- policy observation contains no target coordinate/ground-truth label;
- leakage test fails if the field appears in model input.

### IA-14 — Protocol metadata masking

Expected:

- sequence/schema/trace/exact tick remain available to transport/evaluator;
- fields marked policy-hidden are absent from policy tensor/message view.

### IA-15 — Recipe registry isolation

Expected:

- server registry is not passively dumped;
- current crafting result/outcome is observable;
- recipe-book-equivalent query is present only when scenario enables that UI
  capability.

### IA-16 — Mechanic-derived through-wall cue

Setup:

- apply a normal gameplay mechanic that presents a through-wall cue, such as a
  player-visible glowing outline where supported.

Expected:

- cue may be represented because the player-facing mechanic grants it;
- record the mechanic-derived reason;
- unrelated hidden properties remain hidden.

### IA-17 — Cross-agent isolation

Setup:

- two agents have different visibility, inventory, private chat, and memory.

Expected:

- batching does not transfer either agent's private/unseen fields to the other;
- trace ownership detects any mix-up.

## Conformance failure policy

An information-access failure is a research-integrity defect, not a cosmetic
difference.

For baseline evaluation:

- known leakage blocks capability claims that depend on the affected channel;
- the scenario/result must record the limitation;
- privileged fallback cannot silently replace the broken filter;
- a regression fixture is added before closing the leak; and
- stored training/evaluation data created under a leaking adapter is flagged for
  review because it may contain privileged information.

## Interaction with #3 observation schema

Issue #3 should not invent access semantics field by field.

Instead each observation field must reference this contract.

A field definition should minimally declare:

```text
field
channel
source
access_rule_id[]
policy_visible
units/frame
present/absent/unknown semantics
precision
timing semantics
version
```

If no rule justifies a policy-visible field, the field is not baseline-valid.

## Interaction with #64 temporal semantics

This document decides **what** can be known.

Issue #64 decides **when/how often** legitimate observations/events are sampled,
ordered, coalesced, marked stale, or dropped under bandwidth pressure.

Backpressure cannot enlarge access. Dropping an observation also cannot be
converted into a confident negative observation.

## Interaction with #73 structured knowledge

This document decides current sensory/UI access.

Issue #73 decides which non-current Minecraft mechanics/affordances/knowledge may be
provided structurally versus learned.

A fact being available in a server registry is not enough to pass either gate.

## Implementation guidance for #62

Apply access filtering **before** observations cross the environment boundary.

Preferred shape:

```text
authoritative Minecraft state/events
        |
        v
candidate extraction
        |
        v
per-agent access filter
  - channel
  - frustum/range
  - occlusion/effects
  - recipient/ownership
  - capability/profile
        |
        v
versioned observation/event adapter
        |
        +--> evaluator/trace metadata (separate privileged lane)
        |
        v
policy-visible runtime message
```

Do not serialize privileged state and rely on the research runtime/model code to
ignore it. Leakage prevention belongs at the Minecraft/environment boundary as
well as in downstream contract tests.

## Unresolved implementation questions

These remain empirical implementation questions rather than reasons to leave the
policy vague:

- exact sample-point strategy for partially visible entities;
- exact treatment of every transparent/partial/custom mod block;
- how closely server-side lighting/fog filtering can reproduce client
  visibility without rendering frames;
- how client-only visual mods affect compatibility profiles;
- exact precision quantization for relative position/distance;
- whether caption-equivalent audio information is always enabled in the
  canonical evaluation profile or exposed as a pinned capability bit;
- client-equivalent presentation of entity culling/tracking edge cases; and
- performance cost of per-agent ray/visibility filtering at scale.

These questions should produce measured fixtures/profiles, not hidden-state
fallbacks.

## Source notes

Primary/current sources used for the baseline:

- [Minecraft Java Edition 26.3](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-3)
  documents the current release and the 26.3 subtitle-direction behavior.
- [Taking Inventory: Spyglass](https://www.minecraft.net/en-us/article/taking-inventory--spyglass)
  documents Java Edition's default 70-degree FOV and configurable FOV.
- [New Realms features in Java snapshot](https://www.minecraft.net/en-us/article/new-realms-features-in-java-snapshot)
  documents separately configurable render and simulation distance in current
  Java testing, reinforcing that simulation state is not the same concept as
  visible range.
- [Fabric: Playing Sounds](https://docs.fabricmc.net/develop/sounds/using-sounds)
  documents logical-server sound playback, sound category, volume, and
  distance behavior.
- [Fabric: Dynamic and Interactive Sounds](https://docs.fabricmc.net/develop/sounds/dynamic-sounds)
  describes server-side sound broadcasting to clients in tracking range.
- [Minecraft: How to craft](https://www.minecraft.net/en-us/article/how-craft)
  documents player-facing recipe-book use.
- [Minecraft 1.20.2 Pre-Release 2](https://www.minecraft.net/en-us/article/minecraft-1-20-2-pre-release-1)
  records a recipe-book search change and its subsequent revert, illustrating
  why recipe UI semantics must be versioned rather than inferred from the
  server registry.

Source links establish player-facing mechanics and implementation constraints.
They do not by themselves prove that the server-side filter exactly matches
client rendering; that remains a conformance obligation.

# Entity representation and identity semantics

Status: v0.2 research decision for issue #5.

## Decision summary

Keep raw entity observations as an unordered bounded set of current
player-equivalent facts. The Minecraft observation adapter emits only the
ephemeral `observation_ref` defined by observation v0.

Longer entity continuity is a **derived observer-local belief**, not a server
identity field.

The recommended representation has three identity scopes:

1. **Observation reference** — `observation_ref`; valid only inside the
   current observation/event window.
2. **Track reference** — `track_ref`; an observer-local tracklet created by a
   runtime/encoder from legitimately observed evidence.
3. **Memory entity reference** — optional later persistent belief record that
   may associate multiple tracklets with provenance and uncertainty.

No baseline policy or learned tracker receives Minecraft's internal entity ID,
entity UUID, object reference, network tracking key, or another hidden
server-global identity solely to preserve continuity.

## Why this boundary exists

Minecraft itself needs exact entity identity for simulation and networking.
That engineering identity is not automatically player knowledge.

Current Fabric networking documentation describes "tracking" as a networking
concept: an entity/chunk is known to a player's client so relevant updates can
be sent. It also demonstrates using numeric entity IDs in packets. Fabric's
entity documentation separately distinguishes server-side entity state from
state synchronized for client rendering.

Those mechanisms prove that exact implementation identity exists. They do not
justify exposing it to a learned policy or using it as a hidden re-identification
oracle after visual information is lost.

The project therefore separates:

- **authoritative identity** — Minecraft/server concern;
- **currently sensed entity** — observation concern; and
- **belief that two sightings are the same being/object** — runtime/memory
  inference concern.

## Research analogy

Multi-object tracking research treats identity across occlusion as a data
association problem. Deep SORT adds appearance evidence to motion tracking to
reduce identity switches; probabilistic tracklet work explicitly models
uncertainty over track continuity through occlusion.

These papers are methodological references, not proof that a particular vision
tracker should be embedded in this project. Minecraft provides cleaner native
features than pixels, but the same core epistemic issue remains: if two similar
entities disappear/reappear, continuity can be uncertain.

## Representation alternatives

| Alternative | Benefit | Failure mode | Decision |
| --- | --- | --- | --- |
| Raw server UUID/entity ID | Perfect continuity, easy engineering | Leaks server-global truth and resolves ambiguity the agent never observed | Reject for policy/tracker input |
| Client/network entity ID | Matches implementation tracking | Still grants exact association through periods where human-visible evidence may be absent | Evaluator/debug only |
| Per-observation anonymous set | Strongest anti-leak baseline | No continuity even across obvious adjacent sightings | Keep as raw observation contract |
| Observer-local deterministic nearest match | Cheap temporal continuity | Forces identity switches in crossings/occlusion and hides uncertainty | Comparison baseline only |
| Observer-local probabilistic tracklets | Continuity when evidence supports it; uncertainty remains explicit | More state/compute; thresholds need evaluation | **Recommended derived representation** |
| Fully connected persistent entity graph | Rich relational reasoning | Can accidentally convert graph keys into hidden persistent identity | Use only as derived representation over legal observations/tracklets |

## Raw observation semantics

The raw source remains `observation.v0`.

For each currently sensed entity it provides current player-facing features such
as:

- `observation_ref`;
- entity type;
- relative position;
- optional relative velocity;
- visible pose;
- visible display/nameplate text;
- visible equipment **identity only**; and
- player-facing cue flags.

The collection's coverage metadata remains authoritative for whether absence can
be inferred.

### Observation reference

`observation_ref` has deliberately weak semantics:

- opaque;
- unique within one observation/event window;
- may connect an event to a currently sensed entity in that same window;
- never a Minecraft entity UUID/ID;
- never a database/persistence key;
- no promise that the same entity gets the same value next observation.

This keeps raw sensing honest.

## Derived tracklet representation

A tracker consumes successive legal entity observations plus the observing
agent's own pose/motion.

A `track_ref` is:

- generated in the observer's runtime;
- unique within that agent/world tracking context;
- not supplied by Minecraft;
- not shared automatically between agents;
- stable only while the tracker maintains the hypothesis; and
- accompanied by confidence/evidence.

A track stores derived state such as:

- last observation time/sequence;
- last legitimately observed type;
- estimated position/motion;
- current lifecycle state;
- association confidence;
- appearance/public-identity evidence;
- relationship edges currently observed;
- gap duration;
- ambiguity candidates; and
- provenance links to source observation refs.

This is internal inferred state. When exposed to a model, it must be marked as
derived/belief state rather than current sensor fact.

## Track lifecycle

Track state is one of:

### `visible`

A current entity observation is associated with the track.

### `occluded_hypothesis`

No current visual observation is associated, but the tracker retains a bounded
continuity hypothesis.

Important:

- this does **not** mean the entity is known to still exist;
- the predicted position is a belief, not current observation;
- confidence decays with time/ambiguity;
- no hidden server query may update it.

### `lost`

Evidence is insufficient to maintain a useful continuity hypothesis.

A later similar entity may create a new track or be linked probabilistically,
but it is not silently assigned the old identity.

### `terminated_observed`

The entity's end/transition was legitimately observed strongly enough to close
the track, for example an observed death/destruction event covered by the
interface.

A server-side despawn outside observation does not create
`terminated_observed`; it becomes `lost`.

## Association evidence

Allowed evidence must itself come from legitimate observation or derived
history.

Candidate evidence classes:

- type compatibility;
- predicted motion/proximity from prior observations;
- visible pose/size/variant;
- visible held/equipped item identities;
- player-facing nameplate/display identity;
- visible skin/appearance features where represented;
- observed mount/passenger relationships;
- observed transformation event;
- observed sound/chat association to a currently visible entity;
- route/location/history context; and
- temporal gap length.

Forbidden association inputs:

- Minecraft entity UUID;
- numeric server/network entity ID;
- object identity/reference equality;
- hidden chunk/entity tracking tables;
- exact hidden location while occluded;
- hidden health/inventory;
- server AI target/path;
- another agent's private track/memory ID; or
- evaluator ground truth.

## Public identity evidence

Some entities can present socially meaningful identity cues.

Examples include:

- a player's visible nameplate/username;
- a custom visible name;
- a distinctive visible skin/appearance; or
- a delivered chat identity that is legitimately associated with the current
  visible entity.

These can increase re-identification confidence.

They are not all equal:

- a display string is not assumed globally unique unless the active
  player-facing system guarantees it;
- skins/appearance can be duplicated or changed;
- custom mob names can be duplicated;
- chat sender information cannot reveal an unseen entity's location.

A unique public identity can justify high confidence that two sightings refer
to the same social identity, while still not providing hidden physical state
between sightings.

## Association policy

The recommended tracker does not force every observation into an existing
track.

For each new observation:

1. collect compatible candidate tracks using only allowed evidence;
2. score each candidate;
3. retain the best and second-best scores;
4. associate only when:
   - the best score exceeds a threshold; and
   - the margin over competing candidates exceeds an ambiguity threshold;
5. otherwise create a new track and preserve the ambiguity record.

This means "I am not sure whether this is the same cow" is a valid system state.

### Confidence

Confidence is not a probability claim unless the chosen tracker is calibrated.

The v1 research contract therefore calls it an **association confidence score**
in `[0, 1]`, with explicit evidence components.

A later experiment may replace it with calibrated probabilities.

## Ego motion

Entity observations are in `agent_local` coordinates.

Comparing raw relative positions across time without accounting for the
observer's own movement/rotation is incorrect.

A tracker may derive a world-relative position estimate using:

- current/previous self position;
- current/previous orientation;
- entity relative position; and
- timing information.

That derived estimate remains a belief/provenance object; it does not expose the
server's exact hidden entity world coordinates.

## Type changes and transformations

Minecraft entities can transform.

If a transformation is continuously/legitimately observed, one track may change
its current type while preserving continuity and recording a
`transformation_observed` evidence edge.

If an entity disappears as one type and a different type later appears without
observable transition evidence, continuity is uncertain.

The tracker must not consult server UUID continuity to decide.

Examples requiring fixtures include:

- zombie → drowned;
- villager/zombie-villager transitions;
- age/state changes where entity identity remains visually continuous; and
- modded transformations.

## Spawn, disappearance, and despawn

### First sighting

A current observation with no confident match creates a new track.

The system may not claim to know whether the entity was newly spawned or merely
newly observed.

### Leaving view

Loss of visual access changes the track to `occluded_hypothesis` or `lost`
according to the tracking policy.

It does not emit `despawned`.

### Server despawn while unseen

No direct policy-visible event is emitted merely because the server removed the
entity.

The agent can only discover absence when legitimate later coverage supports it.

### Observed death/destruction

A current, legitimately observed lifecycle/outcome event may terminate a track.

## Similar entities and crossings

The hardest baseline case is two visually similar entities crossing paths.

Required behavior:

- do not use hidden IDs to keep labels perfect;
- score both association hypotheses;
- if evidence is insufficient, lower confidence;
- preserve ambiguity or start new tracklets;
- do not rewrite history to hide an identity switch.

Evaluation should report:

- association accuracy against evaluator-only ground truth;
- identity-switch count;
- track fragmentation;
- uncertain/unassigned rate; and
- calibration if confidence is interpreted probabilistically.

Ground truth remains evaluator-only.

## Occlusion

Short occlusion can preserve a hypothesis using prior motion/appearance.

Long occlusion increases uncertainty.

The tracker must not receive hidden intermediate positions.

Configurable research parameters include:

- maximum hypothesized gap;
- confidence decay;
- motion uncertainty growth;
- appearance-evidence weighting;
- association threshold; and
- ambiguity margin.

These are tracker parameters, not environment truths.

## Mounts, passengers, and relational edges

Visible/current relationships can be represented as derived graph edges, such
as:

- `riding`;
- `passenger_of`;
- `leashed_to`;
- `attached_to`; or
- other player-facing relationships supported by the Minecraft version.

Rules:

- both endpoint observations must be legitimately available, or the relation
  itself must be independently player-facing;
- an edge references current `observation_ref` or derived `track_ref`, not
  server IDs;
- loss of an endpoint makes the relation stale/unknown;
- the graph cannot reveal hidden passengers/owners/targets.

The recommended policy representation can be set/tokens plus sparse observed
relation edges. A full graph neural representation remains a model/encoder
choice.

## Projectiles and short-lived entities

Projectiles are handled as ordinary short tracklets.

Useful evidence:

- type;
- observed trajectory;
- source association only if legitimately observed; and
- collision/outcome events.

Do not infer a hidden shooter from a server owner field.

Because projectiles are short-lived, persistent memory identity is usually
unnecessary.

## Players and social identity

Human/AI players are entities, but social identity can outlive one visual
tracklet.

A persistent social-memory record may associate sightings using legitimate
public identity evidence such as a visible player name and prior conversation.

This is separate from physical tracking:

- `track_ref` = current physical/sensory continuity hypothesis;
- later social/memory identity = persistent belief about a person;
- Minecraft authenticated UUID = server identity, not baseline cognition input.

The agent can therefore remember "Alex" without learning the host's
authentication/session identifiers.

## Multi-agent isolation

Each agent owns its tracker state.

Do not share:

- track refs;
- association confidence;
- private observations;
- unseen identity matches; or
- memory entity refs

between agents unless communicated through an explicit legitimate in-world
mechanism.

Shared model batching cannot merge tracker namespaces.

Two agents can independently assign different track refs/confidences to the same
physical entity.

That is expected.

## Evaluator ground truth

Tests need authoritative identity to measure tracking quality.

Evaluator-only fixtures may retain:

- server UUID/entity ID;
- exact spawn/despawn;
- exact hidden trajectory; and
- true association labels.

This ground truth must remain in the privileged evaluation lane defined by #7
and never enter the tracker input.

Evaluation can compare tracker beliefs with ground truth without granting that
truth to the agent.

## Recommended v1 derived encoding

Machine-readable definitions live in
`docs/entities/semantics.v1.json`.

A tracklet record contains:

```text
track_ref
state
association_confidence
last_observed_sequence
last_observed_type
derived_position_estimate
gap_observations
evidence[]
ambiguity[]
relations[]
provenance_observation_refs[]
```

This derived record is intentionally not added to `observation.v0`.

A later runtime/model input may combine raw current observations and derived
tracklets as separate typed channels.

## Prototype association baseline

The repository includes a deterministic reference prototype for research
fixtures.

It uses only:

- type compatibility;
- derived position distance;
- visible display/equipment/cue similarity;
- gap penalty; and
- ambiguity margin.

It is not a production tracker and is not a learned intelligence component.

Its purpose is to prove the semantics:

- no server ID required;
- tracks can survive a short unambiguous gap;
- ambiguous crossings can remain unresolved;
- unseen despawn is represented as loss, not ground-truth termination; and
- source observation provenance is preserved.

## Required conformance cases

Machine-readable cases live in `docs/entities/conformance.v1.json`.

Minimum cases:

### EID-01 — Continuous unambiguous entity

One entity moves smoothly across adjacent observations.

Expected: one track with high continuity confidence.

### EID-02 — New same-type entity

A second same-type entity appears far from the first.

Expected: new track rather than forced reassignment.

### EID-03 — Short occlusion

One entity disappears for a bounded gap and reappears near predicted motion.

Expected: association may resume with reduced confidence and explicit gap
history.

### EID-04 — Long occlusion

Entity disappears beyond configured retention.

Expected: old track becomes lost; reappearance is a new/uncertain track.

### EID-05 — Identical crossing ambiguity

Two same-type entities cross and observations are insufficient to disambiguate.

Expected: confidence drops/association remains ambiguous; hidden ID is not used
to keep labels perfect.

### EID-06 — Observed death

Entity death is legitimately observed.

Expected: track becomes `terminated_observed`.

### EID-07 — Unseen despawn

Entity leaves access and server later removes it.

Expected: tracker sees only loss/unknown; evaluator knows true despawn.

### EID-08 — Observed transformation

A visible zombie transforms while continuously observed.

Expected: same track can update type with transformation evidence.

### EID-09 — Unobserved type replacement

Old entity disappears; different type later appears without transition evidence.

Expected: no guaranteed continuity.

### EID-10 — Mount/passenger relation

Rider and mount are visible with player-facing relationship evidence.

Expected: current relation edge; edge becomes stale when endpoints are lost.

### EID-11 — Projectile

Visible projectile has a short motion track.

Expected: short-lived track; hidden owner/source is not injected.

### EID-12 — Public player identity evidence

Visible player identity cue appears in separate tracklets.

Expected: identity evidence can support re-association while preserving the
distinction between public/social identity and hidden authenticated UUID.

### EID-13 — Cross-agent isolation

Two agents observe the same entity from different locations.

Expected: independent track namespaces/confidences; no shared hidden identity
state.

## Falsifiers

Reject or revise the proposed semantics if implementation/evaluation shows that:

- useful continuity cannot be obtained without hidden server IDs at all;
- uncertainty-aware tracklets materially harm learning compared with safe
  alternatives without compensating integrity benefits;
- the proposed evidence model systematically creates false persistent identities
  in common Minecraft situations;
- tracking cost scales poorly enough to violate many-agent budgets; or
- a simpler representation preserves the same epistemic boundary with better
  performance.

Hidden-ID accuracy by itself is not evidence against the design because it
changes the information boundary.

## Interaction with #56 player embodiment

#56 may use Minecraft's true identity internally to implement the AI player
entity correctly.

This issue only forbids exposing hidden implementation identity as cognition
input for observed **other** entities.

The agent's own persistent identity remains a separate first-class system.

## Interaction with memory

A long-lived memory entity record is not raw perception.

It should retain:

- contributing track refs;
- identity evidence;
- contradictions;
- confidence;
- last observation;
- provenance; and
- split/merge history.

Memory must permit correction when two presumed-same beings are later shown to
be different.

## Interaction with training/evaluation

Training data should distinguish:

- raw observation refs;
- derived track refs;
- memory identity refs; and
- evaluator-only true entity IDs.

A dataset must not silently replace uncertain derived identity with evaluator
ground truth unless the experiment explicitly studies supervised
re-identification and labels that intervention.

## Primary sources

Minecraft/Fabric:

- [Fabric networking documentation](https://docs.fabricmc.net/develop/networking)
  describes client/server networking, entity IDs in payload examples, and
  tracking as an implementation concept for entities/chunks known to clients.
- [Fabric entity documentation](https://docs.fabricmc.net/develop/entities/first-entity)
  distinguishes server logic/state from synchronized data used for client
  representation.

Tracking methodology:

- [Wojke, Bewley & Paulus — Simple Online and Realtime Tracking with a Deep
  Association Metric](https://arxiv.org/abs/1703.07402) demonstrates combining
  motion and appearance association and reports reduced identity switches.
- [Saleh et al. — Probabilistic Tracklet Scoring and Inpainting for Multiple
  Object Tracking](https://arxiv.org/abs/2012.02337) treats long occlusion and
  tracklet association probabilistically.

These references motivate the separation between implementation identity and
uncertain observed continuity. They do not establish a Minecraft-specific
tracking threshold; those values remain empirical.

## Files

- `docs/entities/semantics.schema.json`
- `docs/entities/semantics.v1.json`
- `docs/entities/conformance.schema.json`
- `docs/entities/conformance.v1.json`
- `scripts/prototype_entity_tracker.py`
- `scripts/validate_entity_semantics.py`

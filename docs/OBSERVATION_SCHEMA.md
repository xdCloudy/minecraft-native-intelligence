# Structured observation schema v0

Status: v0.2 environment contract for issue #3.

## Purpose

The observation contract is the language-neutral boundary between the
server-authoritative Minecraft adapter and downstream agent/runtime research.

It defines a **minimal structured native observation** without selecting:

- a final terrain encoder;
- long-term entity identity semantics;
- temporal/bandwidth policy;
- model tokenization;
- a training framework; or
- a transport implementation.

Those remain separate issues.

The canonical JSON contract and fixtures live under `docs/observations/`.
Future Protobuf/generated-language bindings must preserve the same semantics.

## Design goals

The v0 contract must make these properties explicit:

- which fields are policy-visible;
- source and information-access rule for each field class;
- world/local coordinate frames and units;
- current/unknown/not-applicable semantics;
- collection coverage and negative-evidence rules;
- exact self-owned state versus bounded external sensing;
- separation of protocol/evaluator metadata from policy input;
- event/action-outcome correlation;
- schema/capability identity; and
- a controlled extension surface.

## Envelope split

Every observation has two top-level sections:

```text
observation.v0
├── meta    # transport/replay/evaluator metadata; policy-hidden
└── policy  # the only baseline learned-policy observation
```

### `meta`

The runtime/adapter may require exact values such as:

- immutable agent ID;
- world/session ID;
- monotonic sequence;
- exact game tick;
- trace ID;
- schema/field-registry versions;
- producer version; and
- capability IDs.

These fields are required for routing, ordering, replay, diagnostics, and
compatibility. They are **not baseline policy features**.

A model-input builder must consume `policy`, not serialize the whole envelope.

### `policy`

Contains only facts justified by
[INFORMATION_ACCESS.md](INFORMATION_ACCESS.md).

The core v0 groups are:

- `self`;
- `world_cues`;
- `geometry`;
- `entities`; and
- `events`.

Optional future/player-UI data enters through declared capabilities/extensions,
not hidden server fields.

## Field registry

`docs/observations/fields.v0.json` is the semantic registry.

Every field class declares:

- JSON path/pattern;
- channel;
- source;
- `access_rule_ids`;
- policy visibility;
- units;
- coordinate frame;
- precision guidance;
- unknown/absence semantics;
- stability; and
- notes.

If a new policy-visible field has no field-registry entry and no access rule, it
is not valid v0 baseline input.

The registry is part of the schema contract and is versioned separately as
`observation-fields.v0`.

## Value-state model

Scalar/structured values that may be unavailable use an explicit state wrapper.

### Observed

```json
{
  "status": "observed",
  "value": 20
}
```

### Unknown

```json
{
  "status": "unknown",
  "reason": "not_currently_observable"
}
```

### Not applicable

```json
{
  "status": "not_applicable",
  "reason": "no_active_effect"
}
```

A missing JSON property is **not** a substitute for unknown when the field is
part of the declared schema.

Missing properties are reserved for genuinely optional capabilities/extensions.

## Collection coverage model

Lists of world facts can otherwise create a hidden negative-information oracle.

Every sensed collection has:

```json
{
  "coverage": {
    "status": "partial",
    "negative_evidence": "observed_items_only",
    "reason_codes": ["occlusion", "outside_frustum"]
  },
  "items": []
}
```

Coverage status is one of:

- `complete` — collection is complete for its **declared sensor scope**;
- `partial` — some legitimate scope is unavailable/occluded/dropped; or
- `unavailable` — no current collection coverage.

Negative-evidence mode is:

- `scope_complete` — an empty collection supports absence within the declared
  scope;
- `observed_items_only` — only listed positive observations are known; absence
  elsewhere is unknown; or
- `none` — the collection cannot currently support absence claims.

Rules:

- `complete + [] + scope_complete` may mean no currently sensed item in the
  declared scope;
- `partial + []` does **not** mean none exist;
- `unavailable + []` means unknown;
- loaded/unloaded chunk state never changes these semantics by itself.

Issue #7 remains authoritative for access legality. #64 will later define temporal
windowing, sampling, coalescing, and bandwidth behavior.

## Coordinate frames

v0 defines these frames.

### `world_continuous`

Minecraft world coordinates in blocks using floating-point `x/y/z`.

Used for the agent's own position in the self channel.

### `world_block`

Integer block coordinates.

Used only where a current visible/owned fact legitimately requires a block
location.

### `agent_local`

Right-handed egocentric coordinates in blocks/metres-equivalent Minecraft
units:

- origin: current agent eye/body reference defined by the producer;
- forward/right/up orientation derived from current look/body frame;
- external geometry/entity positions use this frame by default.

The exact basis convention must be held stable within v0 and recorded in field
metadata.

### Angles

Degrees.

Yaw/pitch convention follows the supported Minecraft integration and is
documented by the adapter; downstream model code must not infer an alternate
convention.

## Precision

Precision is a contract property, not an accidental Java serialization detail.

v0 rules:

- own continuous position/orientation/velocity may retain implementation
  precision needed for legal control/replay;
- external positions are relative and may later be quantized;
- #3 does not select final quantization;
- any precision reduction must preserve field units/frame and be versioned or
  capability-declared; and
- hidden exact server coordinates must not survive in extensions/diagnostics
  visible to policy.

## Self state

The `self` group contains native embodied state owned by this agent.

Core v0 fields:

- `position`;
- `orientation`;
- `velocity`;
- `pose`;
- `on_ground`;
- `health`;
- `food`;
- `air`;
- `experience`;
- `selected_hotbar_slot`;
- `inventory`;
- `equipment`; and
- `status_effects`.

### Position

Current own `world_continuous` position.

### Orientation

Current yaw/pitch in degrees.

### Velocity

Current own velocity in blocks per tick (or documented conversion), with units
fixed by the field registry.

### Pose/movement state

Finite semantic state such as:

- standing;
- crouching;
- swimming;
- fall_flying;
- sleeping;
- dying; or
- other versioned Minecraft pose.

The schema uses strings with a namespaced extension path rather than assuming
all future game poses today.

### Needs/status

Health/food/air/experience are self-owned player state.

The schema intentionally does not expose arbitrary hidden player NBT/components.

### Inventory/equipment

Own inventory is structurally visible.

Core item observation includes:

- slot;
- item ID;
- count;
- damage/max-damage when inspectable/relevant; and
- selected/equipment placement.

Arbitrary item component/NBT dumps are prohibited. New item metadata requires an
explicit field definition/access review.

## World cues

`world_cues` contains currently player-facing environmental context rather
than exact server timers.

v0 includes:

- dimension ID;
- coarse day phase; and
- coarse weather cue.

The active information-access profile is recorded in policy-hidden
`meta.information_access_profile_id`, alongside exact `game_tick`.

Possible day phase values:

- `day`;
- `sunset`;
- `night`;
- `sunrise`; and
- `unknown`.

Weather cue:

- `clear`;
- `rain`;
- `thunder`; and
- `unknown`.

This is intentionally not a future-weather oracle.

## Geometry

v0 provides a minimal **surface sample** representation only so the observation
contract is executable before #6 compares richer terrain encodings.

The core v0 geometry shape is a visible-surface sample collection. Its
representation identity belongs in hidden capability/protocol metadata rather
than the learned policy payload. Each item may contain:

- observation-local `sample_id`;
- relative block position in `agent_local`;
- block ID;
- approved visible block-state properties;
- visible faces;
- optional visible fluid ID; and
- visibility quality.

This is not a radius dump.

Only legitimately visible surfaces enter the collection.

Issue #6 may later propose dense/sparse/graph/multiscale encodings. A replacement must
preserve #7 access semantics and either:

- define a new representation capability; or
- trigger a schema-version decision if core semantics change.

## Entities

v0 intentionally uses **ephemeral sensed entity references**. The entity
representation/profile identity is protocol/capability metadata rather than a
policy feature.

Each entity has:

- `observation_ref`;
- visible type ID;
- relative position;
- optional relative velocity;
- visible pose;
- optional display/nameplate text;
- visible held/equipped **item identities only** (no hidden stack count,
  durability, enchantments, or inventory metadata); and
- visible cue flags.

An `observation_ref` only correlates fields/events inside the declared current
observation/event window. It is **not** a server UUID and is not guaranteed to
represent persistent identity across occlusion/re-observation.

Issue #5 owns the next decision: when/how sensed entity identity may persist or
be probabilistically re-associated without server-global truth leakage.

Hidden health, inventory, internal UUID, target AI, pathing state, and unseen
effects are not v0 entity fields.

## Events

The `events` collection carries bounded player-facing events.

Core event kinds:

- `sound`;
- `chat`;
- `action_outcome`; and
- `self_lifecycle`.

The event collection also uses coverage metadata because dropped/unavailable
event windows must not masquerade as "nothing happened".

### Sound event

May include:

- stable sound event ID/token;
- sound category;
- relative direction;
- coarse distance band;
- volume/pitch cue; and
- optional independently-observed entity reference.

No hidden exact source position is required.

### Chat event

May include:

- delivered channel;
- sender display identity as legitimately presented;
- optional independently-observed entity reference;
- text; and
- player-facing message type.

Data/training use of chat remains governed by `DATA_GOVERNANCE.md`.

### Action outcome

Carries:

- request ID;
- phase;
- stable semantic result/rejection code; and
- optional concise player-facing detail.

This event refers only to this agent's own action.

Action semantics themselves are #4/#8.

### Self lifecycle

Covers current self-visible events such as:

- damage received;
- death;
- respawn;
- dimension transition; and
- similar player lifecycle cues.

It does not carry operator-only lifecycle controls.

## Inventory item summary

The item summary deliberately stays narrow.

Allowed for **own inventory/equipment** in v0:

- item ID;
- count;
- durability fields where relevant;
- custom display name when player-visible; and
- coarse enchantment/effect information only when normal own-inventory UI makes
  it available and the field registry explicitly permits it.

For **other sensed entities**, equipment summaries use a separate visible-item
shape containing only the visible item identity. The schema does not expose
another entity's stack count, durability, custom item name, enchantments, or
hidden inventory through visual equipment fields.

Not allowed as a generic escape hatch:

- arbitrary component maps;
- arbitrary NBT;
- hidden loot data;
- owner/plugin internals;
- server object serialization.

## Extensions

Top-level `extensions` under `policy` is the only general additive extension
surface in v0.

Extension keys must be namespaced, for example:

```text
mni.experimental.recipe_ui.v0
examplemod.map_overlay.v1
```

Rules:

- unknown extension keys are ignored safely by generic v0 readers;
- a required extension must appear in `meta.required_capabilities`;
- optional extensions appear in `meta.capabilities`;
- extension policy-visible fields still require information-access rules;
- extensions cannot redefine core field semantics;
- hidden server/evaluator data cannot be smuggled through an extension; and
- stable promotion from an extension into core requires a contract review.

## Capability markers

`meta.capabilities` identifies optional features/representations present.

`meta.required_capabilities` identifies capabilities the consumer must
understand to interpret the observation correctly.

A v0 consumer:

- may ignore unknown optional capabilities/extensions;
- must reject an observation with an unknown required capability; and
- must reject an unsupported schema major/version.

Issue #61 will later define complete peer negotiation, compatibility ranges,
deprecation, and stable/experimental policy.

## Compatibility policy

Within `observation.v0`:

Allowed without semantic break:

- add an optional namespaced extension;
- add an optional capability understood only when advertised;
- add enum values only where the field explicitly permits unknown namespaced
  values and old consumers degrade safely;
- clarify documentation without changing meaning.

Requires a new schema version/compatibility decision:

- rename/remove a core field;
- change units/frame/precision semantics materially;
- change observed/unknown/absence semantics;
- change a field's information-access rules;
- make an optional field mandatory;
- change ephemeral entity-reference guarantees;
- reinterpret an existing enum value; or
- expose previously privileged state.

## Unknown fields and strictness

Core schema objects set `additionalProperties: false` where practical.

This catches accidental leakage/typos.

Forward-compatible experimentation goes through the explicit `extensions`
object rather than arbitrary unknown core keys.

That gives both:

- strict core contracts; and
- a controlled additive surface.

## Version tests

`docs/observations/compatibility.v0.json` defines deterministic cases.

Required cases:

1. canonical v0 observation is accepted;
2. v0 observation containing an unknown optional extension is accepted;
3. v0 observation with unknown **required** capability is rejected by a
   consumer that does not support it;
4. `observation.v1` is rejected by a v0-only consumer;
5. a malformed field with wrong units/shape/type is rejected;
6. a core unknown property outside `extensions` is rejected;
7. partial empty sensed collection remains unknown, not absent;
8. complete empty sensed collection can support absence within declared scope.

## Example fixtures

### `example-observation.v0.json`

A normal synthetic observation containing:

- self state;
- visible stone/grass surface samples;
- one visible entity;
- one sound;
- one own action outcome; and
- complete/partial coverage examples.

### `example-unknowns.v0.json`

Demonstrates:

- geometry unavailable/partial;
- zero sensed entities with partial coverage;
- unknown optional self value; and
- no false empty-world claim.

### `example-extension.v0.json`

Demonstrates an unknown optional namespaced extension that a generic v0 reader
can ignore safely.

All examples are synthetic contract fixtures, not benchmark evidence.

## Relationship to #5

Issue #3 intentionally does **not** decide persistent sensed-entity identity.

The v0 `observation_ref` is ephemeral.

Issue #5 may introduce:

- re-identification hypotheses;
- stable sensed handles;
- uncertainty/confidence;
- graph/token representation; and
- spawn/despawn/occlusion semantics.

That work can extend/refine the entity representation without changing the rest
of the observation envelope.

## Relationship to #6

Issue #3 uses only a minimal visible-surface representation.

Issue #6 is free to compare dense/sparse/octree/graph/egocentric/multiscale
representations under identical #7 access constraints.

## Relationship to #64

Issue #3 includes sequence/game tick in hidden metadata and basic event collection
coverage.

Issue #64 decides:

- snapshot/event cadence;
- temporal windows;
- coalescing;
- staleness;
- dropped-event signaling;
- sensory frequency;
- bandwidth budgets; and
- backpressure semantics.

A future #64 decision may add capability/version fields but cannot reinterpret
unknown as absent.

## Relationship to runtime transport

[RUNTIME_BOUNDARY.md](RUNTIME_BOUNDARY.md) requires agent/session identity,
sequence, game time, schema version, and trace correlation.

The v0 `meta` section provides those semantics while making their policy-hidden
status explicit.

The future Protobuf transport may encode the same fields differently on the
wire; JSON remains the inspection/fixture contract.

## Relationship to telemetry

Telemetry/dataset formats may retain both `meta` and `policy` for replay and
research integrity where data governance permits.

Training pipelines must explicitly choose which parts become model inputs.

The baseline policy view is `policy`, not the raw envelope.

## Security and leakage requirements

An observation producer must fail closed when it cannot determine whether a
field is permitted.

Required properties:

- no host paths/credentials/environment variables;
- no arbitrary server object serialization;
- no hidden chunk/entity state;
- no other-agent private state;
- no evaluator labels in `policy`;
- no debug/admin state in `policy`;
- no arbitrary item NBT/component dump;
- no server UUID as entity identity shortcut; and
- no conversion of unavailable coverage into empty observed state.

## Implementation guidance for #62

The adapter should construct the observation in this order:

```text
authoritative Minecraft state/events
        |
        v
candidate extraction
        |
        v
Issue #7 per-agent access filter
        |
        v
typed v0 policy fields
        |
        +--> meta envelope (routing/replay; policy-hidden)
        |
        v
schema validation / contract assertions
        |
        v
runtime transport
```

Do not build a rich omniscient object and strip fields only inside the model
process.

## Acceptance checklist for new fields

A proposed core/extension field is valid only if:

- [ ] source is named;
- [ ] channel is named;
- [ ] access rule IDs exist;
- [ ] policy visibility is explicit;
- [ ] units are explicit;
- [ ] frame is explicit;
- [ ] precision is intentional;
- [ ] current/unknown/not-applicable semantics are explicit;
- [ ] absence semantics are defined for collections;
- [ ] version/compatibility effect is assessed;
- [ ] privacy/security consequences are assessed; and
- [ ] fixture/contract tests exist.

## Files

- `docs/observations/observation.schema.json`
- `docs/observations/fields.schema.json`
- `docs/observations/fields.v0.json`
- `docs/observations/compatibility.schema.json`
- `docs/observations/compatibility.v0.json`
- `docs/observations/example-observation.v0.json`
- `docs/observations/example-unknowns.v0.json`
- `docs/observations/example-extension.v0.json`
- `scripts/validate_observation_contract.py`

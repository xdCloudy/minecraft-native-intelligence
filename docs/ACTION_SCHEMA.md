# Native action contract v0

This document defines the transport-neutral request and outcome shapes for the
v0 Minecraft interface. It makes the action-schema prerequisite concrete so a
later legal-action validator can check requests before dispatching them through
ordinary server mechanics.

## Request envelope

[`action-request.schema.json`](actions/action-request.schema.json) defines one
action request per envelope. Every request identifies the agent, runtime
session epoch, unique request ID, observation sequence it was based on, trace
ID, and `action-request.v0` schema version. `deadline_game_tick` is optional;
when present, the server rejects a request after that Minecraft game tick.
Duplicate IDs within an agent/session are rejected idempotently and never
execute twice. A request from an old session epoch is rejected.

The typed action union covers movement, look, jump, attack, mine, place,
interaction, hotbar selection, drop, pickup, craft, equip, eat, chat, and
cancellation. Coordinates are absolute block coordinates. Entity and item
references are IDs from the current observation, not arbitrary server entity
lookups. `move` values are normalized inputs, not destinations or velocity
assignments. Durations are bounded hints for input-equivalent controls; the
server still applies collision, reach, cooldown, permissions, inventory,
recipes, and normal game timing.

`interact.target_kind` must agree with its target property: `block` requires
`target_block`, and `entity` requires `target_entity_id`. The schema bounds
shape and primitive values; the authoritative validator must check that
cross-field rule plus observation freshness, visibility, capabilities, world
state, and every Minecraft precondition. Unknown action types and unknown
properties fail closed.

## Outcomes and lifecycle

[`action-outcome.schema.json`](actions/action-outcome.schema.json) defines
versioned outcomes correlated by agent ID, session epoch, request ID, and trace
ID. Each outcome has a monotonic per-agent sequence and authoritative Minecraft
game tick.

`accepted` means queued by the authoritative server. `started` means execution
began. `completed` means the action reached its terminal success condition;
`result` may include observed effects but never substitutes for an observation.
`rejected` is terminal and requires a stable machine-readable `reason_code`.
`cancelled` is terminal and reports cancellation of the referenced request.
Implementations may emit only the applicable lifecycle events (for example,
an immediate rejection need not first emit `accepted`). Sending a request is
never evidence of success.

Cancellation is best-effort and only applies to an active request owned by the
same agent and session. It cannot roll back effects already committed by
Minecraft. A cancellation outcome uses the cancellation request ID and names
the target ID in `result.target_request_id`.

## Compatibility and limits

V0 requires an exact schema version. A consumer that does not support
`action-request.v0` or `action-outcome.v0` fails closed before accepting
actions. Additive action kinds, fields, or lifecycle semantics require a new
schema version; v0 consumers must not silently ignore unknown fields.

These contracts do not implement tick scheduling, player embodiment, or
adapter transport. Minecraft remains the final authority. See
[`ACTION_SPACE.md`](ACTION_SPACE.md), [`INFORMATION_ACCESS.md`](INFORMATION_ACCESS.md),
and [`RUNTIME_BOUNDARY.md`](RUNTIME_BOUNDARY.md) for surrounding constraints.

The current pure validation core and its adapter requirements are described in
[`LEGAL_ACTION_VALIDATION.md`](LEGAL_ACTION_VALIDATION.md). It does not provide
a transport adapter.

The initial server-side control executor is documented in
[`NATIVE_ACTION_EXECUTION.md`](NATIVE_ACTION_EXECUTION.md); it currently
supports movement, look, jump, mining, eating, hotbar selection, dropping,
and cancellation intentions.

Examples: [request](actions/example-action-request.v0.json),
[started outcome](actions/example-action-outcome.v0.json).

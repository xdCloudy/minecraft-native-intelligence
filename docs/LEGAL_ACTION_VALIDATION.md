# Legal action validation core

`ActionRequestValidator` is a pure Java validation core for
`action-request.v0`. It parses the request envelope, rejects unknown fields and
unsupported action types, applies the schema's primitive bounds, checks the
agent/session/observation/deadline, and evaluates server-derived capability,
permission, visibility, reach, cooldown, inventory, recipe, hunger, and
cancellation facts. It returns a stable reason code and never mutates a player,
inventory, entity, block, or world.

The `ActionValidationContext` is an adapter boundary. Every value in it must be
read from authoritative server state and the current observation ledger; none
may be copied from the request. Action capabilities use the form
`mni.actions.<action-type>.v0`, for example `mni.actions.move.v0`. The caller
must intersect negotiated capabilities with server policy before supplying
`supportedCapabilities` and `permittedActions`.

The server adapter must serialize request validation, request-ID reservation,
and dispatch for an agent/session. It must reserve each accepted ID before
another request can validate, and pass previously seen IDs in the context.
This core detects a known duplicate but does not itself own a concurrent ID
ledger. Cancellation IDs must refer to active requests owned by that same
agent/session; the adapter must scope `activeRequestIds` accordingly.

Acceptance by this core is only permission to enqueue an intention. The
execution layer must still call ordinary player control and Minecraft
mechanics, recheck mutable preconditions at execution time, and emit the
correlated outcome. In particular, the context's recipe IDs currently express
recipe availability, not a reservation of ingredients; crafting must use the
normal recipe/inventory path and can still fail if state changes. Cooldown,
reach, inventory, and world facts can also change between validation and
execution. This repository does not yet wire this core to a server transport or
an embodied player executor, so it does not establish Survival parity or prove
that requests are dispatched safely.

Run `./gradlew actionContractTest` from `minecraft-mod` to execute the
deterministic no-server contract checks. The GameTest source is compiled by CI,
but is not launched by this task and no Mojang EULA is accepted.

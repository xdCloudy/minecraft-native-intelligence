# Native action execution slice

`AgentActionExecutor` is the first server-side execution path for the v0 action
contract. It accepts already-decoded request JSON with a server-built
`ActionValidationContext`, verifies that the target `ServerPlayer` is owned by
the mod, runs `ActionRequestValidator`, applies one-action-at-a-time arbitration,
and emits correlated `action-outcome.v0` records with per-agent sequence and
world game tick.

This slice executes `move`, `look`, `jump`, and `mine`, and can cancel the
currently active action for that player. Movement and jump controls are
translated into Minecraft's `Input` value and passed through the player's
`ServerGamePacketListenerImpl.handlePlayerInput`; look uses its ordinary
rotation packet handler. A tick-bounded control is started from
`START_SERVER_TICK`, consumed by the ordinary player tick, and released at
`END_SERVER_TICK`. The server packet handlers and game mode remain responsible
for collisions, movement, reach, and other mechanics. Positive strafe means
right; negative strafe means left. Minecraft's digital input path reduces each
normalized axis to its sign and applies the game's normal diagonal movement
normalization.

Mining sends vanilla `START_DESTROY_BLOCK`, then `STOP_DESTROY_BLOCK` on the
following server tick through the same packet handler a client uses. Vanilla
`ServerPlayerGameMode` owns break progress, tool effects, spawn protection,
permission checks, and drops. The executor reports completion only after the
target position is observed as air; cancellation sends
`ABORT_DESTROY_BLOCK`. The action's optional face is forwarded for the normal
crack direction, defaulting to `up` when omitted.

The silent player has no client to acknowledge initial loading. The executor
waits for vanilla's 60-tick client-load timeout before dispatching these
controls, because the corresponding packet handlers gate gameplay input on
that state. A request deadline can expire during this wait and produces a
rejection outcome. Malformed requests without usable request and trace IDs
return a deterministic submission error but cannot be represented as a
correlated schema outcome.

Other valid schema actions currently fail closed with
`executor_action_unsupported`. Combat, placement, inventory, crafting, eating,
block/entity interaction, pickup, and chat still need executor paths and
ordinary-mechanics conformance evidence. The outcome sink is currently the
mod log; `MniMod.submitAgentAction` is an ingress seam, not a network transport.
Its caller must construct the context from current authoritative state and
invoke it on the server thread. The profile UUID is used as the current
session-scoped agent ID; persistent identity binding remains future work.

`actionContractTest` covers request validation, control-value translation,
mining-target mapping, and outcome serialization.
CI compiles the GameTest sources but does not launch a Minecraft server. The
runtime control path therefore remains unverified until an operator runs the
GameTest server under the project's EULA opt-in procedure.

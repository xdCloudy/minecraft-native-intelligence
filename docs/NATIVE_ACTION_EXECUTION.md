# Native action execution slice

`AgentActionExecutor` is the first server-side execution path for the v0 action
contract. It accepts already-decoded request JSON with a server-built
`ActionValidationContext`, verifies that the target `ServerPlayer` is owned by
the mod, runs `ActionRequestValidator`, applies one-action-at-a-time arbitration,
and emits correlated `action-outcome.v0` records with per-agent sequence and
world game tick.

This slice executes `move`, `look`, `jump`, `mine`, `place`, `equip`, `eat`,
`select_slot`, and `drop`, and can cancel the currently active action for that
player. Movement and jump controls are translated into Minecraft's `Input` value and passed through the
player's `ServerGamePacketListenerImpl.handlePlayerInput`; look uses its
ordinary rotation packet handler. A tick-bounded control is started from
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

Eating sends vanilla `ServerboundUseItemPacket` for the requested hand. Vanilla
item-use timing consumes the food and applies hunger; the executor reports
completion only after hunger rises or the held stack count falls. Cancellation,
deadline expiry, and server cleanup release item use through the ordinary
`RELEASE_USE_ITEM` handler.

Hotbar selection sends `ServerboundSetCarriedItemPacket` through vanilla's
carried-item handler and completes only after the player's selected slot
matches the requested slot. Vanilla handles stopping a main-hand use when the
selection changes.

Dropping sends `ServerboundContainerClickPacket` with vanilla's `THROW` input
through the player's active container handler. Partial drops remove one item
per server tick; whole-stack drops use the ordinary stack-throw click. The
executor maps the observed inventory slot through the active menu and completes
only after the authoritative source stack reaches the requested count.

Equipping uses ordinary `PICKUP` clicks in the player's active `InventoryMenu`.
The executor checks the live source stack and its equipment slot, rejects a
nonempty cursor or a different active menu, moves the requested stack through
the cursor, and returns displaced equipment to that same source slot. It
reports completion only after the requested item is equipped, the previous
equipment is recovered, and the cursor is empty.

Placement builds the requested face hit and calls vanilla
`ServerPlayerGameMode.useItemOn` with the held hand. Before invoking it, the
server rechecks item feature enablement, block interaction reach, build height,
spawn protection, and `level.mayInteract`; the vanilla game mode retains
replaceability, collision, item, and placement mechanics. The packet handler
cannot be used for this action because it also requires an initial client
teleport acknowledgement that the silent player cannot send. This path does
not create a connection or synthesize protocol acknowledgements. The executor
reports completion only if the clicked/adjacent block state or held stack
changes.

The silent player has no client to acknowledge initial loading. The executor
waits for vanilla's 60-tick client-load timeout before dispatching movement,
look, mining, and eating controls because their packet handlers gate those
actions on that state. Hotbar selection, dropping, and the bounded placement
adapter do not wait for this timeout. A request deadline can expire during a
gated action's wait and produces a rejection outcome.
Malformed requests without usable request and trace IDs return a deterministic
submission error but cannot be represented as a correlated schema outcome.

Other valid schema actions currently fail closed with
`executor_action_unsupported`. Combat, crafting, block/entity
interaction, pickup, and chat still need executor paths and
ordinary-mechanics conformance evidence. The outcome sink is currently the
mod log; `MniMod.submitAgentAction` is an ingress seam, not a network transport.
Its caller must construct the context from current authoritative state and
invoke it on the server thread. The profile UUID is used as the current
session-scoped agent ID; persistent identity binding remains future work.

`actionContractTest` covers request validation, control-value translation,
mining-target, hand, and hotbar-slot mapping, and outcome serialization.
GameTests cover vanilla-timed food consumption, carried-item selection, counted
drops, equipment swaps through inventory clicks, placement through the
executor's vanilla `ServerPlayerGameMode` path, and rejection when the
validated reach set contains a block outside the player's live interaction
range. CI only compiles these GameTests.
CI compiles the GameTest sources but does not launch a Minecraft server. The
runtime control path therefore remains unverified until an operator runs the
GameTest server under the project's EULA opt-in procedure.

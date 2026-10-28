# Native Action Space

Actions express player capabilities directly: move, look, jump, attack, mine, place, use/interact, select/equip, manipulate inventory, craft, eat, and communicate. They should be typed, temporally explicit, interruptible where appropriate, and report accepted/rejected/completed outcomes.

The integration remains authoritative for reach, collision, cooldowns, inventory contents, recipes, block hardness, permissions, health, and tick timing. An action request never teleports, edits inventory, bypasses mining duration, or accesses commands unavailable to an ordinary player.

AI-controlled players spawn in Survival by default. Health, hunger/saturation, air, experience, inventory slots, crafting, armour/equipment, status effects, damage, knockback, pickup/drop, block breaking/placement, attack cooldowns, death, drops, and respawn must flow through the same server mechanics used for human players. The agent policy emits intentions or input-equivalent actions; it never directly sets the resulting inventory, position, health, or crafted output.

`/spawn ai-agent <username>` is an authorized operator lifecycle command outside the agent action space. The agent cannot invoke it to create peers unless a future, explicit server policy adds that capability.

Research must choose the boundary between continuous controls, atomic semantic actions, and temporally extended skills. Evaluation should measure legality, latency, responsiveness, compositionality, failure recovery, and parity with ordinary mechanics. Invalid actions become observable learning signals, not silent corrections. A dedicated Survival parity suite should compare equivalent human and AI player operations at the server-event/state-transition level.

## Experimental typed action interchange (issue #158)

The initial, **non-integrated** `action.v0` contract lives in
[`actions/action.schema.json`](actions/action.schema.json), with a
[golden request](actions/example-action.v0.json) and
[authoritative outcome lifecycle](actions/outcome.schema.json).
Run `python scripts/validate_action_contract.py docs/actions/example-action.v0.json`
or `python -m unittest discover -s tests -p 'test_action_contract.py'`.
Audit an ordered outcome stream against its original request with:

```sh
python scripts/validate_action_contract.py docs/actions/example-outcomes.v0.json \
  --request docs/actions/example-action.v0.json
```

- Envelopes carry explicit agent/session identity, action ID, trace ID,
  observation sequence, issue/expiry ticks, schema version and one typed intent.
- The initial intent vocabulary is movement, looking, jumping, attacking, mining,
  placing, interacting, hotbar selection, crafting, chat and cancellation of the
  *agent's own* active intent. These are requests, not privileged state edits.
- A consumer rejects unknown schema versions, unsupported actions, malformed
  variants, stale observations, mismatched sessions, expired requests and
  non-chat commands. Runtime replay/deduplication and target visibility still
  require server-side enforcement; the schema cannot grant authorization.
- A successful preflight is **not** an action completion. Only server-confirmed
  outcome events can report accepted, started, completed, rejected or cancelled.
  Any reason returned to the agent must not reveal hidden Minecraft state.
- The offline outcome-sequence auditor correlates all four identity fields,
  rejects inverted/nonmonotonic ticks, permits only `accepted → started →
  completed/cancelled`, `accepted → completed/cancelled`, or immediate
  `rejected`, and treats exact transport replays as idempotent. Conflicting
  replays, phase regressions and new events after a terminal event fail closed.
  An empty or merely accepted history is **pending**, never "success".
  This is a check on already authenticated server events; it neither validates
  the event producer nor executes an action.
- The first published wire revision is v0. There is no previous supported
  release to migrate from. Future revisions require explicit upgrade/downgrade
  fixtures, capability negotiation, deterministic rejection of incompatible
  versions, and documented replay behavior.

This is an offline contract prototype only. It has **not** been exercised against
a Fabric mod, server player, permission system, Survival mechanics, or old client.
In-game legality, lifecycle ordering, observational reference authorization and
version migration remain open evidence gates before #158 can close.

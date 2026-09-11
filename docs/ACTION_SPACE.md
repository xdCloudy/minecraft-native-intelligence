# Native Action Space

Actions express player capabilities directly: move, look, jump, attack, mine, place, use/interact, select/equip, manipulate inventory, craft, eat, and communicate. They should be typed, temporally explicit, interruptible where appropriate, and report accepted/rejected/completed outcomes.

The integration remains authoritative for reach, collision, cooldowns, inventory contents, recipes, block hardness, permissions, health, and tick timing. An action request never teleports, edits inventory, bypasses mining duration, or accesses commands unavailable to an ordinary player.

AI-controlled players spawn in Survival by default. Health, hunger/saturation, air, experience, inventory slots, crafting, armour/equipment, status effects, damage, knockback, pickup/drop, block breaking/placement, attack cooldowns, death, drops, and respawn must flow through the same server mechanics used for human players. The agent policy emits intentions or input-equivalent actions; it never directly sets the resulting inventory, position, health, or crafted output.

`/spawn ai-agent <username>` is an authorized operator lifecycle command outside the agent action space. The agent cannot invoke it to create peers unless a future, explicit server policy adds that capability.

Research must choose the boundary between continuous controls, atomic semantic actions, and temporally extended skills. Evaluation should measure legality, latency, responsiveness, compositionality, failure recovery, and parity with ordinary mechanics. Invalid actions become observable learning signals, not silent corrections. A dedicated Survival parity suite should compare equivalent human and AI player operations at the server-event/state-transition level.

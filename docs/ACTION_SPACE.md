# Native Action Space

Actions express player capabilities directly: move, look, jump, attack, mine, place, use/interact, select/equip, manipulate inventory, craft, eat, and communicate. They should be typed, temporally explicit, interruptible where appropriate, and report accepted/rejected/completed outcomes.

The integration remains authoritative for reach, collision, cooldowns, inventory contents, recipes, block hardness, permissions, health, and tick timing. An action request never teleports, edits inventory, bypasses mining duration, or accesses commands unavailable to an ordinary player.

Research must choose the boundary between continuous controls, atomic semantic actions, and temporally extended skills. Evaluation should measure legality, latency, responsiveness, compositionality, failure recovery, and parity with ordinary mechanics. Invalid actions become observable learning signals, not silent corrections.

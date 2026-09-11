# Design Principles

1. **Minecraft-native grounding.** Prefer structured, bounded game state and events over pixels, OCR, desktop automation, or hidden-state access.
2. **Legal embodiment.** Actions pass through ordinary mechanics, reachability, timing, inventory, and permission checks.
3. **Player-compatible presence.** Ship as a Java Edition mod; represent each AI through ordinary player-facing systems and default it to Survival rather than implementing an NPC-only ruleset.
4. **Persistent individuality.** Foundation competence may be shared; identity, assigned skin, and lived state remain isolated and durable.
5. **Memory before constant retraining.** Durable knowledge should usually enter explicit persistent state first. Parameter updates require evaluation and rollback.
6. **One grounded communication system.** Language connects current state, memory, relationships, planning, and action for human and AI interlocutors alike.
7. **Autonomy, not servitude.** External suggestions are social inputs, not the sole source of goals.
8. **Emergence over scripting.** Implement learning conditions and affordances, not predetermined personalities or societies.
9. **Partial observability is real.** Do not expose unseen chunks, omniscient entity state, recipes or facts not legitimately known, or future outcomes.
10. **Many-agent viability.** Every persistent structure and inference path must have an explicit scaling story.
11. **Evidence over demos.** Record baselines, negative results, uncertainty, and learned-versus-scripted contributions.
12. **Operator transparency and control.** An agent's native ontology never removes human disclosure, administration, privacy, deletion, or safety obligations.
13. **Technical neutrality until evidence.** The mod delivery boundary is decided; loader/version, research stack, storage, and model choices remain open until evaluated.

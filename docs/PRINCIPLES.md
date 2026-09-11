# Design Principles

1. **Minecraft-native grounding.** Prefer structured, bounded game state and events over pixels, OCR, desktop automation, or hidden-state access.
2. **Legal embodiment.** Actions pass through ordinary mechanics, reachability, timing, inventory, and permission checks.
3. **Persistent individuality.** Foundation competence may be shared; identity and lived state remain isolated and durable.
4. **Memory before constant retraining.** Durable knowledge should usually enter explicit persistent state first. Parameter updates require evaluation and rollback.
5. **One grounded communication system.** Language connects current state, memory, relationships, planning, and action for human and AI interlocutors alike.
6. **Autonomy, not servitude.** External suggestions are social inputs, not the sole source of goals.
7. **Emergence over scripting.** Implement learning conditions and affordances, not predetermined personalities or societies.
8. **Partial observability is real.** Do not expose unseen chunks, omniscient entity state, recipes or facts not legitimately known, or future outcomes.
9. **Many-agent viability.** Every persistent structure and inference path must have an explicit scaling story.
10. **Evidence over demos.** Record baselines, negative results, uncertainty, and learned-versus-scripted contributions.
11. **Operator transparency and control.** An agent's native ontology never removes human disclosure, administration, privacy, deletion, or safety obligations.
12. **Technical neutrality until evidence.** Core platform and model choices remain research questions until evaluated.

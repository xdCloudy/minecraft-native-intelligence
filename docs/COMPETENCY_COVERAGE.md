# Minecraft gameplay coverage protocol

The [generated competency matrix](MINECRAFT_COMPETENCY_MATRIX.md) is a continuously
expandable catalogue of Minecraft-native capabilities. It is not a declaration
that every Minecraft mechanic is known, supported, or learned. The canonical
records live in [progress.json](progress/progress.json), not in generated Markdown.

## What each row must prove

1. **Native action:** the Java Edition mod proposes a player-equivalent action
   that Minecraft accepts or rejects through ordinary server mechanics.
2. **Legitimate knowledge:** observation fields are filtered through the access
   policy. Evaluator-only terrain, recipes, entities, gamerules and metadata
   cannot leak into the model or memory.
3. **Reproducible success:** predeclare scenario, baseline, game/loader version,
   survival rules, held-out world seeds, model/data revisions and success metric.
   Preserve every trial, timeout, retry and failure, not just a demonstration.
4. **Failure boundary:** measure inaccessible items, insufficient resources,
   unsafe terrain, missing permissions, invalid interactions, stale observations,
   interrupted actions and known version differences where relevant.
5. **Transfer:** for learned competence, evaluate on unseen seeds, structures and
   situations, and compare with matched scripted/no-learning/no-memory controls.
6. **Evidence:** link exact repository revisions, game test fixtures, results,
   raw traces and reproduction commands. A unit test, schema or synthetic world
   model is not evidence that a Minecraft gameplay capability was demonstrated.

## Coverage maintenance

- Add a new stable ID for a separately falsifiable mechanic or research question.
  Use a new record when completing the parent item could conceal an unimplemented
  operation, such as crafting versus enchanting or building versus redstone.
- Preserve retired IDs and record overlap instead of silently deleting scope.
  Distinct experiments may share prerequisites; do not double-count the same
  successful experiment as independent confirmation without justification.
- Assign workstream, category, priority, dependencies, milestone mapping,
  acceptance scenario, failure boundary, evidence and all five status dimensions.
- When a new Minecraft version or modpack changes mechanics, add cases or
  explicit compatibility/version entries and re-run appropriate prior tests.
- Update upstream goals, ADRs and interface contracts only when actual decisions
  change; listing an avenue is not an architecture decision.
- Run the progress validation, regeneration, deterministic freshness check,
  focused progress tests and documentation CI. Never hand-edit the generated
  competency matrix or README percentage.

The initial set covers Survival progression, combat/entities,
world dimensions and traversal, construction/automation, and multiplayer
world lifecycle. Other variants may arise from player testing, platform
changes, mod interactions and independent research. Such discoveries expand
the denominator honestly, even if the aggregate percentage falls.

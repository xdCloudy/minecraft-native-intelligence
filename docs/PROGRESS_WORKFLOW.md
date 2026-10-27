# Research and development progress workflow

## Canonical data and generated views

[`progress/progress.json`](progress/progress.json) is the sole manually maintained progress dataset. Its versioned structure is [`progress/progress.schema.json`](progress/progress.schema.json). [`tools/progress.py`](../tools/progress.py) validates local and cross-record invariants, calculates transparent indicators, and deterministically generates:

- [`PROGRESS.md`](PROGRESS.md), the project dashboard.
- [`FEATURE_MATRIX.md`](FEATURE_MATRIX.md), every feature and engineering item.
- [`MINECRAFT_COMPETENCY_MATRIX.md`](MINECRAFT_COMPETENCY_MATRIX.md), independently falsifiable legal-gameplay scenarios, mechanic groups and failure boundaries.
- [`RESEARCH_MATRIX.md`](RESEARCH_MATRIX.md), the research questions, alternative approaches, prior work and conclusions.
- [`MODEL_TRAINING_MATRIX.md`](MODEL_TRAINING_MATRIX.md), architecture candidates and training/learning methods.
- [`PRODUCTION_READINESS.md`](PRODUCTION_READINESS.md), experiment records, compatibility, readiness gates, rejected approaches, open questions and branch audit.
- Bounded dashboard and roadmap sections in [`README.md`](../README.md) and [`ROADMAP.md`](../ROADMAP.md).

Run the standard-library-only CLI from the repository root:

```sh
python tools/progress.py validate
python tools/progress.py generate
python tools/progress.py check
python -m unittest discover -s tests -p test_progress.py
```

`generate` writes deterministic Markdown and changes only the README/ROADMAP content inside their markers. `check` is read-only and fails if generated files are missing or stale. CI runs validation, freshness checking and tests; it never writes generated documentation. `scripts/generate_progress.py` remains a compatibility entry point.

## Independent status dimensions

The exact ordered vocabulary is recorded in `statusDefinitions`, with versioned score maps in `scoring`.

| Dimension | Ordered states | Meaning |
|---|---|---|
| Research | `not_investigated`, `prior_art_reviewed`, `hypothesis_established`, `feasibility_evaluated`, `experiment_designed`, `experiment_conducted`, `baselines_compared`, `reproducibility_validated`, `research_concluded` | A negative or infeasible result can conclude a bounded question when evidence and limitations are recorded. |
| Experimental outcome | `not_assessed`, `positive`, `negative`, `inconclusive`, `infeasible`, `superseded` | Project outcomes require a reproducible experiment record. Literature is not a project result. |
| Implementation | `not_implemented`, `experimental`, `prototype`, `functional`, `locally_tested`, `integrated`, `regression_tested`, `production_validated` | Open branches cannot receive integrated credit. Every item is assessed against the recorded main SHA. |
| Validation | `untested`, `unit_tested`, `integration_tested`, `in_game_tested`, `reproducibly_benchmarked`, `independently_verified` | A document, compile, or unit-test pass alone is not an in-game capability test. |
| Production readiness | `not_assessed`, `experimental`, `locally_validated`, `ci_validated`, `integrated_into_main`, `release_validated`, `production_validated` | Operational, security, privacy, compatibility, reliability and release criteria apply as relevant to each item. |

A failed hypothesis may close research but cannot establish an implemented capability. A prototype, schema, test pass or completed bounded research question cannot establish autonomous intelligence.

## Scoring and scope

Reported measures are research coverage, research completion, experimental effectiveness, implementation maturity, demonstrated capabilities, validation coverage, production readiness, model research, training research and overall scoped progress. Every scored item has the weight `workstream weight × item priority`; fixed score maps and overall weights live in the canonical JSON. Core intelligence and Minecraft capability workstreams receive mission-oriented weights. Scope coverage measures completeness of each record, not research completion. Empty dependency and related-reference lists are valid when none exist.

Overall scoped progress is explicitly weighted toward demonstrated capability (60%), then implementation maturity (20%), validation coverage (10%) and production readiness (10%). Demonstrated capability requires a positive outcome, functional-or-better implementation, in-game-or-stronger validation and main-revision provenance. Expanding scope or correcting inflated assessments may lower a percentage. Do not adjust weights to preserve a trend.

Roadmap gate percentages are calculated from evidence-backed criterion states (`open` 0%, `prototype` 25%, `partial` 50%, `met` 100%), equally weighted within each milestone. Milestone item maps include avenues, models and training methods. A completed documentation milestone is not evidence of Minecraft-native capability.

## Evidence and branch audit

- Give each workstream, item, evidence source, model, method, experiment, compatibility cell, milestone, criterion and PR snapshot a stable unique ID. Never reuse retired IDs.
- Link evidence to repository files or external primary sources. Distinguish prior work from project evidence; a design document does not prove implementation.
- Record exact revisions and the assessed main SHA. For experiments, record environment/hardware, Minecraft version or why not applicable, model and dataset versions, configuration, seeds, methodology, raw artifact/results, reproduction steps and limitations.
- Preserve negative, inconclusive and rejected approaches. Do not convert a missing experiment into a negative result or claim an unmeasured latency, throughput, memory, license or capability.
- Record open PR base/head revisions, affected items and latest checks separately. Stacked PR checks do not integrate their parents. Never credit unmerged work as shipped or present on main.
- Refresh PR state and checks when refreshing the assessment date or source SHA; do not silently carry stale branch snapshots forward.

## Updating the tracker in a feature or research PR

1. Inspect current repository instructions, the main revision, relevant code and tests, open PRs, roadmap dependencies, research notes and experiment artifacts.
2. Add stable item records when new requirements or independent research questions are discovered. Record alternatives and falsifiable completion criteria.
3. Change only status dimensions supported by evidence. Link exact revisions, record limitations and remaining work, and maintain historical changes and scope changes.
4. Update milestone maps and gates from their evidence; keep open-branch outcomes attributed to their source revision.
5. Run `validate`, `generate`, inspect the generated diff, then run `check` and the focused unit tests listed above.
6. Update authoritative subsystem/research documents when conclusions change; generated matrices summarize the canonical data and do not replace those documents.

## Minecraft gameplay coverage and scope changes

The [`gameplay coverage protocol`](COMPETENCY_COVERAGE.md) defines independent
success, failure, parity and held-out-world requirements. Every GP- item needs
its own scenario and failure boundary in the canonical JSON. A broad parent
mechanic or a passing synthetic unit test cannot complete individual cases.
Data/experiment workflow items (DP-) and training-method candidates (TM-)
remain research plans until evidence is reproduced. New Minecraft versions,
modded content and independently discovered methods must expand the scope when
needed, even when this lowers a percentage.

Do not interpret the catalog completeness percentage as proof that every
Minecraft mechanic, training method or research avenue has been identified.
The independent gameplay matrix measures declared, falsifiable cases, not a
closed universal checklist.

## Legacy research protocol specificity

The inherited research inventory contained **150** placeholder plans (an earlier
estimate of 141 omitted nine). Each now records an independently identifiable
Minecraft/server experiment fixture, an actual comparison/control, named metrics
and a failure or safety boundary, reflected in the generated feature and
research matrices. These are **proposed protocols**, not experiments performed
or proof that any architecture is effective.

When editing an existing avenue or adding a new one:

1. Name the exact game-state setup, player-equivalent actions or dataset trial.
2. Identify at least one legitimate comparator. A privileged oracle or scripted
   policy can be an explicitly invalid/negative control, never a claimed native
   agent achievement.
3. Record the primary observable outcome and its units/metric definition before
   the experiment; include all failures, seeds or deterministic fault schedules.
4. Specify an adverse case that could disprove the claim, violate privacy or
   game legality, or invalidate a performance comparison.
5. Link in-game outcomes to relevant GP-/DP- cases where a broad avenue spans
   multiple mechanics. Completing a parent study does not complete its children.
6. Preserve the existing five status dimensions until actual reproducible
   evidence on the assessed main revision warrants promotion.

The validator rejects previously used boilerplate patterns, and regression tests
guard all 150 audited rows against accidental reversion to generic templates.
This research-plan enrichment does not change the declared item count or any
progress percentage; the dashboard remains tied to the separately recorded
main-branch assessment revision.

## Current assessment limits

The expanded taxonomy contains 15 workstreams, 268 feature/research avenues (including 60 concrete gameplay mechanics and 12 data lifecycle items), 21 model candidates and 21 training methods: 310 tracked items. Naming an avenue does not mean it has been investigated. The assessed main snapshot has no integrated Minecraft agent mod or demonstrated intelligent Minecraft-native behavior. Model architecture remains undecided. Project-specific training compute, inference latency, throughput, generalization and grounding remain unmeasured. The terrain-encoding experiment is synthetic and branch-only; it does not establish in-game perception quality.

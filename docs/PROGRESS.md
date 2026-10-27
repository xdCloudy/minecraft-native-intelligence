# Research and development progress

Assessment: `2026-10-27` · assessed main `8622b139da2db7782525faec3ee4dac623acb1ba` · 15 workstreams · 330 tracked features, research candidates and methods.

> The percentages track evidence against this declared research scope. They do not measure intelligence, autonomy, consciousness or human-level ability. No Minecraft-native intelligent agent is demonstrated on the assessed main revision. Unmerged PRs and their historical checks are recorded separately and receive no integrated or shipped credit.

| Dimension | Progress | Percent | Interpretation |
|---|---|---:|---|
| Research coverage | ████████████████ | 100.0% | Catalog completeness, not amount of research conducted. |
| Research completion | ░░░░░░░░░░░░░░░░ | 0.0% | Investigation can conclude negatively or as infeasible. |
| Experimental effectiveness | ░░░░░░░░░░░░░░░░ | 0.0% | Positive outcomes only; a negative result can still conclude research. |
| Demonstrated capabilities | ░░░░░░░░░░░░░░░░ | 0.0% | Positive, functional and in-game or stronger evidence on main. |
| Implementation maturity | ░░░░░░░░░░░░░░░░ | 0.0% | Functional states on the assessed main revision. |
| Validation coverage | ░░░░░░░░░░░░░░░░ | 0.0% | Unit through independent verification; gameplay requires in-game evidence. |
| Production readiness | ░░░░░░░░░░░░░░░░ | 0.0% | Operational, security, privacy, compatibility and release gates. |
| Overall scoped progress | ░░░░░░░░░░░░░░░░ | 0.0% | 60% demonstrated capabilities, 20% implementation, 10% validation, 10% readiness. |

Research coverage and completion are distinct. Expanding scope can lower completion. Weights are `workstream weight × item priority`; neither is adjusted to preserve a trend. [Scoring and definitions](PROGRESS_WORKFLOW.md).

## Current milestone

**v0.2 — Minecraft Native Interface** · 20.0% of evidence-reviewed exit gates. This delivery milestone does not imply agent capability.

### Model and training research

- Model architecture research completion: **0.0%** across 21 candidates.
- Training and learning research completion: **0.0%** across 23 methods.

### Workstream view

| Workstream | Items | Research | Implementation | Validation | Readiness |
|---|---:|---:|---:|---:|---:|
| Minecraft integration and embodiment | 13 | 0.0% | 0.0% | 0.0% | 0.0% |
| Perception and information access | 14 | 0.0% | 0.0% | 0.0% | 0.0% |
| Action, control and legality | 14 | 0.0% | 0.0% | 0.0% | 0.0% |
| Model architectures and training | 42 | 0.0% | 0.0% | 0.0% | 0.0% |
| Learning and adaptation | 47 | 0.0% | 0.0% | 0.0% | 0.0% |
| Cognition and autonomy | 16 | 0.0% | 0.0% | 0.0% | 0.0% |
| Construction and spatial creativity | 18 | 0.0% | 0.0% | 0.0% | 0.0% |
| Memory and identity | 17 | 0.0% | 0.0% | 0.0% | 0.0% |
| Language, relationships and social behavior | 15 | 0.0% | 0.0% | 0.0% | 0.0% |
| Infrastructure, runtime and scaling | 11 | 0.0% | 0.0% | 0.0% | 0.0% |
| Evaluation and evidence | 19 | 0.0% | 0.0% | 0.0% | 0.0% |
| Safety, security and data governance | 15 | 0.0% | 0.0% | 0.0% | 0.0% |
| Multi-agent infrastructure and population scaling | 15 | 0.0% | 0.0% | 0.0% | 0.0% |
| Minecraft-specific gameplay competencies | 62 | 0.0% | 0.0% | 0.0% | 0.0% |
| Training data and experiment lifecycle | 12 | 0.0% | 0.0% | 0.0% | 0.0% |

## Main blockers

| Item | Workstream | Main status | Acceptance evidence still needed |
|---|---|---|---|
| [`AC-01` Legal action interface and outcome contract](FEATURE_MATRIX.md#ac-01) | Action, control and legality | not_implemented / untested | Each action has validated preconditions, bounded duration, stable outcome and no direct world mutation. |
| [`BU-016` Natural-language-to-voxel build specification and clarification](FEATURE_MATRIX.md#bu-016) | Construction and spatial creativity | not_implemented / untested | Reproduce the fixture: Translate ambiguous requests such as a two-storey mob-safe spruce house with a cellar into constraints, dimensions, materials and a preview before any block placement. |
| [`BU-018` Versioned blueprint execution state and design revision](FEATURE_MATRIX.md#bu-018) | Construction and spatial creativity | not_implemented / untested | Reproduce the fixture: Resume a partially placed bridge and house after world reload, block destruction and a player-requested room extension. |
| [`BU-02` Terrain-aware planning, materials and execution](FEATURE_MATRIX.md#bu-02) | Construction and spatial creativity | not_implemented / untested | All changes via legal actions; plan adapts to perturbations and incomplete resources; artifacts reproducible. |
| [`CO-03` Autonomous goal generation and arbitration](FEATURE_MATRIX.md#co-03) | Cognition and autonomy | not_implemented / untested | Goal persistence/revision is causally linked to experience; scripts and operator prompts are disclosed. |

## Roadmap progress

Gate percentage is calculated from each milestone’s evidence-reviewed criteria (open=0, prototype=25%, partial=50%, met=100%). Item mappings are shown in the feature matrix; a PR cannot satisfy an integrated gate.

| Milestone | Stage | Gate progress | Gates met / total |
|---|---|---:|---:|
| v0.1 — Project Foundation | complete_as_documented | 100.0% | 1/1 |
| v0.2 — Minecraft Native Interface | in_progress | 20.0% | 0/5 |
| v0.3 — Agent Runtime | future | 0.0% | 0/1 |
| v0.4 — Memory | future | 0.0% | 0/1 |
| v0.5 — Behaviour Baseline | future | 0.0% | 0/1 |
| v0.6 — Language Grounding | future | 0.0% | 0/1 |
| v0.7 — Autonomous Behaviour | future | 0.0% | 0/1 |
| v0.8 — Lifelong Learning | future | 0.0% | 0/1 |
| v0.9 — Multi-Agent Intelligence | future | 0.0% | 0/1 |
| v0.10 — Scaling & Simulation | future | 0.0% | 0/1 |
| v0.11 — Integrated Research Prototype | future | 0.0% | 0/1 |
| v1.0 — Native Intelligence Research Release | future | 0.0% | 0/1 |

## GitHub workflow audit

Checked: 2026-10-27T12:50:17Z · open issues: **0** · open PRs: **0** · issues closed administratively: **101**.

GitHub issues and PRs are tracked as workflow state, not capability evidence. The 101 issue closures and eight unmerged PR closures do not meet any acceptance criteria.

## Unmerged PR history (including closed PRs)

| PR / state | Branch | Base → head | Historical checks | Integrated credit |
|---|---|---|---|---|
| [#122](https://github.com/xdCloudy/minecraft-native-intelligence/pull/122) closed | `feat/sensed-entity-identity` | `main` → `b8ac08a8` | PowerShell syntax: skipped; Documentation: success; Python and JSON tooling: success; Detect changed stacks: success | excluded |
| [#123](https://github.com/xdCloudy/minecraft-native-intelligence/pull/123) closed | `research/terrain-encoding-prototype` | `main` → `59695fc6` | PowerShell syntax: skipped; Python and JSON tooling: success; Documentation: success; Detect changed stacks: success | excluded |
| [#124](https://github.com/xdCloudy/minecraft-native-intelligence/pull/124) closed | `feat/native-action-schema-v0` | `main` → `7886c4be` | PowerShell syntax: skipped; Python and JSON tooling: success; Documentation: success; Detect changed stacks: success | excluded |
| [#125](https://github.com/xdCloudy/minecraft-native-intelligence/pull/125) closed | `spike/server-player-embodiment` | `feat/sensed-entity-identity` → `d177480a` | Python and JSON tooling: success; PowerShell syntax: success; Minecraft mod compile: success; Documentation: success; Detect changed stacks: success | excluded |
| [#126](https://github.com/xdCloudy/minecraft-native-intelligence/pull/126) closed | `feat/persistent-agent-identity` | `main` → `28713c16` | PowerShell syntax: skipped; Python and JSON tooling: success; Documentation: success; Detect changed stacks: success | excluded |
| [#127](https://github.com/xdCloudy/minecraft-native-intelligence/pull/127) closed | `feat/environment-protocol-compatibility` | `feat/native-action-schema-v0` → `9d26898d` | PowerShell syntax: skipped; Documentation: success; Python and JSON tooling: success; Detect changed stacks: success | excluded |
| [#128](https://github.com/xdCloudy/minecraft-native-intelligence/pull/128) closed | `feat/legal-action-validator` | `spike/server-player-embodiment` → `2231a03b` | Python and JSON tooling: success; Documentation: success; PowerShell syntax: success; Minecraft mod compile: success; Detect changed stacks: success | excluded |
| [#129](https://github.com/xdCloudy/minecraft-native-intelligence/pull/129) closed | `feat/native-action-executor` | `feat/legal-action-validator` → `25272d72` | Python and JSON tooling: skipped; PowerShell syntax: skipped; Documentation: success; Minecraft mod compile: success; Detect changed stacks: success | excluded |

## Detailed matrices

- [Feature and engineering matrix](FEATURE_MATRIX.md) — every scoped subsystem item and its five independent status dimensions.
- [Minecraft gameplay competency matrix](MINECRAFT_COMPETENCY_MATRIX.md) — concrete legal Survival scenarios and negative tests.
- [Research inventory](RESEARCH_MATRIX.md) — full questions, alternatives, prior work, methods, evidence and open issues.
- [Model architectures and training methods](MODEL_TRAINING_MATRIX.md) — candidate-by-candidate research and measured unknowns.
- [Experiments, compatibility and production readiness](PRODUCTION_READINESS.md) — reproducible evidence, branch audit, readiness gates and rejected approaches.
- [Progress maintenance workflow](PROGRESS_WORKFLOW.md).

**Minecraft-specific competency scenarios inventoried: 62.** This is a declared, extensible scope, not proof all mechanics are known or tested. Each scenario requires separate legal-action, in-game and failure-boundary evidence.

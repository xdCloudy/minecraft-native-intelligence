# Documentation guide

Minecraft Native Intelligence is a research-stage project. These documents describe intended capabilities, candidate designs, evidence standards, and work that remains to be implemented. They are **not** a manual for a working AI-player mod.

Return to the [project README](../README.md) for the overview and current progress snapshot.

## Choose a reading path

| If you want to… | Start with | Then read |
| --- | --- | --- |
| Understand the project | [Goal](GOAL.md) | [Principles](PRINCIPLES.md), [architecture](../ARCHITECTURE.md) |
| Work on the Minecraft integration | [Integration](INTEGRATION.md) | [Platform comparison](MOD_PLATFORM.md), [observations](OBSERVATION_SCHEMA.md), [actions](ACTION_SPACE.md) |
| Investigate an AI/ML approach | [Research programme](../RESEARCH.md) | [Prior work](RESEARCH_REFERENCES.md), [experiments](EXPERIMENTS.md), [evaluation](EVALUATION.md) |
| Find a capability or blocker | [Progress dashboard](PROGRESS.md) | [Feature matrix](FEATURE_MATRIX.md), [roadmap](../ROADMAP.md) |
| Contribute a change | [Contributing](../CONTRIBUTING.md) | [Testing](TESTING.md), [CI](CI.md), [progress workflow](PROGRESS_WORKFLOW.md) |

## Vision and architecture

- [Goal](GOAL.md) — authoritative mission, near-term deliverable, and non-goals.
- [Vision](VISION.md), [principles](PRINCIPLES.md), and [glossary](GLOSSARY.md) — vocabulary and design constraints.
- [Architecture overview](../ARCHITECTURE.md) and [detailed architecture](ARCHITECTURE.md) — conceptual boundaries and interfaces; the proposed system is not yet implemented.
- [Decision log](DECISIONS.md) — accepted constraints, proposed platform choices, and unresolved decisions.
- [Minecraft integration](INTEGRATION.md), [mod platform](MOD_PLATFORM.md), and [embodiment spike](EMBODIMENT_SPIKE.md) — player embodiment, Survival parity, compatibility, installation target, and loader experiments.
- [Runtime boundary](RUNTIME_BOUNDARY.md) and [scaling](SCALING.md) — asynchronous scheduling, serving, state isolation, and multi-agent resource limits.
- [Observation schema](OBSERVATION_SCHEMA.md), [information access](INFORMATION_ACCESS.md), and [action space](ACTION_SPACE.md) — what an agent may sense and legally do.

### Focused intelligence design notes

These are research-oriented subsystem notes, not finished implementations:

- [Perception](PERCEPTION.md) and [world models](WORLD_MODEL.md)
- [Memory](MEMORY.md), [learning](LEARNING.md), and [training](TRAINING.md)
- [Language](LANGUAGE.md), [personality](PERSONALITY.md), and [multi-agent behaviour](MULTI_AGENT.md)
- [Safety](SAFETY.md) and [data systems](DATA.md)

## Research and evaluation

- [Research programme](../RESEARCH.md) — questions and scientific decision rules.
- [Prior research and external projects](RESEARCH_REFERENCES.md) — evidence, transfer limitations, and reuse considerations.
- [Experiment protocol](EXPERIMENTS.md) — manifests, reproducibility, run capture, and failure preservation.
- [Evaluation](EVALUATION.md) — scenario/result contracts, controls, uncertainty, and in-world success criteria.
- [Gameplay coverage protocol](COMPETENCY_COVERAGE.md) — independent mechanic-level acceptance and negative tests.
- [Data governance](DATA_GOVERNANCE.md) — consent, licences, privacy, retention, and dataset provenance.

## Matrices and progress

The [progress dashboard](PROGRESS.md) is the quickest way to inspect the current evidence assessment. Detailed, generated views serve different questions:

| View | What it answers |
| --- | --- |
| [Feature and engineering matrix](FEATURE_MATRIX.md) | What is scoped, what depends on what, and what implementation evidence exists? |
| [Minecraft gameplay competencies](MINECRAFT_COMPETENCY_MATRIX.md) | Which Survival mechanics have independently falsifiable scenarios? |
| [Research matrix](RESEARCH_MATRIX.md) | Which hypotheses, comparisons, limitations, and experiments are recorded? |
| [Model and training matrix](MODEL_TRAINING_MATRIX.md) | Which architectures and learning methods remain candidates? |
| [Production-readiness matrix](PRODUCTION_READINESS.md) | What compatibility, safety, operational, and release gates remain? |

The [roadmap](../ROADMAP.md) defines milestone order and exit gates. The [progress workflow](PROGRESS_WORKFLOW.md) defines status vocabularies, scoring denominators, evidence provenance, and regeneration commands.

**Important:** 100% catalog completeness means required fields are present for declared records. It is not 100% research completion, feature implementation, or exhaustive discovery of every possible requirement.

## Contributing and maintenance

- [Contributor guide](../CONTRIBUTING.md) — issue selection, PR expectations, and first changes.
- [Engineering backlog and critical path](BACKLOG.md) — issue coverage, blocker dependencies, ranked ready work, and the continuous contributor loop.
- [Documentation style](STYLE_GUIDE.md) — writing, links, generated-file rules, and evidence language.
- [Testing](TESTING.md) and [CI](CI.md) — verification tiers, supported tools, and local checks.
- [Security policy](../SECURITY.md) and [code of conduct](../CODE_OF_CONDUCT.md) — responsible disclosure and community conduct.
- [Contributor audit](CONTRIBUTOR_AUDIT.md) — historical audit context; use current policy and matrices for live requirements.

### Sources of truth

1. **Project intent:** [GOAL.md](GOAL.md) and accepted [ADRs](DECISIONS.md).
2. **Requirements and evidence status:** [`progress/progress.json`](progress/progress.json), not the generated Markdown matrices.
3. **Experiment outcomes:** versioned raw records and the [evaluation contract](EVALUATION.md), not descriptions or screenshots alone.
4. **Implementation:** code and tests on the audited main revision, not open PRs or conceptual interfaces.

For tracker changes, edit the canonical JSON and regenerate through `python tools/progress.py generate`. Never hand-edit the generated matrix tables or the marked README/roadmap dashboard sections.

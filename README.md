# Minecraft Native Intelligence

> **Research-stage project.** There is no installable AI-player mod or demonstrated Minecraft-native intelligence on `main` yet. The repository currently contains research plans, interface contracts, evaluation tooling, and an evidence-tracked engineering roadmap.

Minecraft Native Intelligence (MNI) investigates persistent, autonomous agents that experience Minecraft as their world. The long-term goal is for agents to learn through legal in-game actions, remember their own histories, communicate with players, and pursue goals beyond externally assigned tasks.

**Start here:** [Project goal](docs/GOAL.md) · [Documentation guide](docs/README.md) · [Architecture](ARCHITECTURE.md) · [Roadmap](ROADMAP.md) · [Contributing](CONTRIBUTING.md)

## What makes it different

MNI is not intended to be an LLM command wrapper, a screenshot-to-keyboard controller, a prompted Mineflayer bot, or a scripted NPC. Those approaches may serve as clearly labelled research baselines, but they do not define the project.

The guiding requirements are:

- **Native grounding:** agents receive bounded game-state observations and perform player-equivalent actions, without privileged world access or direct state manipulation.
- **Persistent individuals:** identity, memory, relationships, goals, and behaviour continue across sessions and world events.
- **Autonomy and learning:** research distinguishes acquired competence from scripts, prompts, preloaded knowledge, and short-lived demonstrations.
- **Shared intelligence, separate lives:** models may be shared, but personal state must remain isolated and scalable across agents.
- **Reproducible evidence:** claims require controlled Minecraft trials, failure cases, held-out worlds, and explicit limitations.

The intended integration is a server-authoritative **Minecraft: Java Edition mod** for single-player/LAN and dedicated servers. An authorized operator would create a persistent Survival-mode AI player with `/spawn ai-agent <username>`, including a stable profile and skin. **That command is a future requirement, not a working feature.** See [integration design](docs/INTEGRATION.md) and the [decision log](docs/DECISIONS.md).

## Current status

<!-- MNI_PROGRESS_START -->
### Live research and engineering progress

**15 workstreams · 330 tracked research/engineering items · current milestone: v0.2 Minecraft Native Interface.** The dashboard reflects evidence on the assessed main revision. No intelligent Minecraft-native agent has been demonstrated.

| Progress dimension | Current |
|---|---:|
| Research coverage | 100.0% |
| Research completion | 0.0% |
| Model architecture research | 0.0% |
| Training-method research | 0.0% |
| Experimental effectiveness | 0.0% |
| Demonstrated capabilities | 0.0% |
| Implementation maturity | 0.0% |
| Validation coverage | 0.0% |
| Production readiness | 0.0% |
| Overall scoped progress | 0.0% |

**Minecraft-specific competency scenarios inventoried: 62.** Each remains unproven until independently evaluated in-game. A full catalog is not a guarantee that every possible mechanic has been enumerated.

**Main gaps:** no integrated Minecraft agent mod, player embodiment, Survival-parity in-game validation, selected foundation architecture or demonstrated learning/autonomy. Historical unmerged PRs are displayed separately and do not count as integrated.

[Full progress dashboard](docs/PROGRESS.md) · [Feature matrix](docs/FEATURE_MATRIX.md) · [Minecraft competency matrix](docs/MINECRAFT_COMPETENCY_MATRIX.md) · [Research inventory](docs/RESEARCH_MATRIX.md) · [Model and training matrices](docs/MODEL_TRAINING_MATRIX.md) · [Experiment and production readiness](docs/PRODUCTION_READINESS.md) · [Scoring and maintenance workflow](docs/PROGRESS_WORKFLOW.md)
<!-- MNI_PROGRESS_END -->

The percentages describe evidence against the *declared* scope, not an estimate of human-level intelligence. In particular, 100% catalog metadata completeness does **not** mean the research or implementation is complete. See the [roadmap](ROADMAP.md) and [scoring rules](docs/PROGRESS_WORKFLOW.md).

## Explore the project

| Looking for… | Go to |
| --- | --- |
| A reading order and the full document map | [Documentation guide](docs/README.md) |
| Intended behaviour, constraints, and system boundaries | [Goal](docs/GOAL.md) · [Architecture](ARCHITECTURE.md) |
| Research directions and external comparisons | [Research programme](RESEARCH.md) · [References](docs/RESEARCH_REFERENCES.md) |
| Tracked requirements, results, and blockers | [Progress dashboard](docs/PROGRESS.md) · [Capability matrices](docs/README.md#matrices-and-progress) |
| How to propose, verify, or review changes | [Contributing](CONTRIBUTING.md) · [Testing](docs/TESTING.md) |

## Contributing

Research, engineering, documentation, and evaluation contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md); coding agents should also read [AGENTS.md](AGENTS.md). There is no end-user installation guide yet because the mod is not implemented.

## License

Repository code and documentation use [Apache License 2.0](LICENSE). Model weights, datasets, Minecraft assets, and other third-party material require separate rights and provenance review.

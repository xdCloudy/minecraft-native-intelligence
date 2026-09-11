# Minecraft Native Intelligence

> **Experimental, early-stage research project.** No intelligent agent has been implemented or demonstrated yet. This repository currently defines the research programme, interfaces, constraints, and staged engineering work needed to test feasibility.

Minecraft Native Intelligence investigates persistent, autonomous intelligence whose perceived world is Minecraft itself. The intended agent learns and acts through native game state and legal game actions, develops an individual history and behavioural tendencies, communicates with other players, and pursues activities without existing only as a command-following assistant.

This is **not** an LLM wrapper, a screenshot-to-keyboard agent, a prompted Mineflayer bot, a scripted NPC, or “ChatGPT inside Minecraft.” Language models may be studied as components, but they are neither the project definition nor a substitute for grounded perception, action, memory, learning, and evaluation.

## Native reality

The agent-facing ontology should be grounded in blocks, entities, items, terrain, motion, health, hunger, danger, time, places, communication, relationships, and remembered experience. It should not require concepts such as operating systems, model APIs, or a human “user.” Developers and server operators, however, must retain transparent oversight and must identify AI players where policy requires it.

## System direction

- A native Minecraft integration exposes bounded, observable state and validates ordinary in-game actions—without hidden information, teleportation, inventory editing, or other cheats.
- A shared foundation model provides reusable world and behavioural competence without loading a full independent model per agent.
- Each agent owns separate persistent identity, episodic/semantic/procedural/spatial memory, relationships, goals, preferences, and—only if evidence supports it—small personal learning modules.
- Learning begins with durable state and memory, not continuous retraining. Later work may test replay, consolidation, adapters, and other continual-learning techniques against catastrophic forgetting.
- Human and AI players use the same grounded communication pathway and appear to the agent as other intelligent beings in its world.
- Multi-agent behaviour should emerge from learned policies and interaction, not hardcoded friendships, rivalries, professions, or stories.

See [the authoritative goal](docs/GOAL.md) and [architecture](ARCHITECTURE.md) for scope and uncertainty.

## Status and roadmap

The project is at **v0.1 — Project Foundation**. The immediate objective is infrastructure, reproducible research baselines, and evidence needed to select interfaces and architectures. Later milestones progress through native integration, runtime and memory prototypes, behavioural and language grounding, autonomy, lifelong learning, multi-agent scaling, and an integrated research platform. They are research stages—not promises of human-level intelligence.

See [ROADMAP.md](ROADMAP.md) for dependencies and success gates.

## Documentation

| Start here | Purpose |
| --- | --- |
| [Goal](docs/GOAL.md) | Ultimate goal, near-term objective, and non-goals |
| [Vision](docs/VISION.md) and [Principles](docs/PRINCIPLES.md) | Product direction and invariants |
| [Architecture](ARCHITECTURE.md) | Proposed system boundaries and timescales |
| [Research programme](RESEARCH.md) | Questions, experimental method, and evidence standards |
| [Roadmap](ROADMAP.md) | Milestones, dependencies, and exit criteria |
| [Safety](docs/SAFETY.md) and [Security](SECURITY.md) | Minecraft-specific operational safeguards |
| [Decision log](docs/DECISIONS.md) | Accepted decisions and unresolved ADRs |
| [Glossary](docs/GLOSSARY.md) | Canonical terminology |

Focused design notes live under [`docs/`](docs/).

## Contributing

Contributions are welcome at the design, research, tooling, and documentation stages. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md) before substantial work. Claims of capability require reproducible evidence; experiments must remain distinguishable from proposed production architecture.

## License

Code and documentation are licensed under [Apache License 2.0](LICENSE). Datasets, Minecraft assets, model weights, and third-party artifacts require separate provenance and license review; inclusion in this repository does not automatically place them under Apache-2.0.

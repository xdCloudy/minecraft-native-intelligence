# Roadmap

Milestones are progressive research and engineering infrastructure. Dates are intentionally absent until evidence supports estimates; none promises human-level intelligence.

| Milestone | Outcome and exit gate | Depends on |
| --- | --- | --- |
| **v0.1 — Project Foundation** | Coherent documentation, contribution/security policy, issue taxonomy, reproducible experiment/test/CI plan, and research baseline | — |
| **v0.2 — Minecraft Native Interface** | Versioned observation/event/action prototypes; information-access and legality tests; platform decision recorded | v0.1 |
| **v0.3 — Agent Runtime** | Multiple identity-safe runtimes can save/load, schedule cognition, and execute through the interface | v0.2 |
| **v0.4 — Memory** | Auditable episodic, semantic, spatial, and procedural prototypes with provenance, contradiction, and consolidation experiments | v0.3 |
| **v0.5 — Behaviour Baseline** | Reproducible native behavioural/imitation baseline with navigation, gathering, survival, and building evaluation | v0.2–v0.4 |
| **v0.6 — Language Grounding** | Communication demonstrably conditions on world state, memory, relationships, and outcomes; human/agent pathways align | v0.4–v0.5 |
| **v0.7 — Autonomous Behaviour** | Agents generate and revise activities without constant instruction; scripted contribution is measured and bounded | v0.5–v0.6 |
| **v0.8 — Lifelong Learning** | Controlled memory/parameter adaptation improves selected capabilities while retention, rollback, and privacy tests pass | v0.4–v0.7 |
| **v0.9 — Multi-Agent Intelligence** | Persistent agents interact concurrently without identity leakage; social and communication evaluations report emergence and failure | v0.6–v0.8 |
| **v0.10 — Scaling & Simulation** | Batched shared inference, low-frequency cognition, profiling, and accelerated/replayable simulation support larger populations | v0.3–v0.9 |
| **v0.11 — Integrated Research Prototype** | Major subsystems run together in a persistent experimental world with end-to-end observability and reproducibility | v0.10 |
| **v1.0 — Native Intelligence Research Release** | Stable, documented research platform publishing the strongest validated results and limitations | v0.11 |

## Cross-cutting gates

Every milestone must preserve legal action constraints, partial observability, per-agent state isolation, operator controls, reproducibility metadata, and explicit learned-versus-scripted accounting. Failed or inconclusive experiments may satisfy a research task when methods and evidence are complete, but not a capability gate.

## Current focus

Complete v0.1, then prioritize platform selection, observation/action contracts, information-access rules, deterministic harness design, and telemetry. These determine whether later results are meaningful and should precede model architecture commitments.

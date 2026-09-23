# Instructions for coding and research agents

## Required orientation

Before substantial work, read:

1. [`docs/GOAL.md`](docs/GOAL.md) — authoritative purpose and non-goals.
2. [`ARCHITECTURE.md`](ARCHITECTURE.md) — proposed boundaries and known uncertainty.
3. [`ROADMAP.md`](ROADMAP.md) — milestone order and current scope.

Read the focused document for the subsystem you touch and check [`docs/DECISIONS.md`](docs/DECISIONS.md) for binding decisions.

## Vision invariants

- Preserve the goal of persistent, autonomous, Minecraft-native intelligence.
- Never silently reframe the project as an LLM wrapper, prompt-driven bot, scripted NPC, or screenshot/keyboard agent.
- Prefer native Minecraft state and event interfaces. Screenshot-based perception is allowed only as an explicitly scoped research experiment.
- Preserve the Java Edition mod delivery target and server-authoritative, player-compatible embodiment described in `docs/INTEGRATION.md`. Do not replace it with an authenticated bot account, custom NPC mob, or client-only desktop controller.
- Keep the agent-facing ontology within its world unless an explicit, reviewed design decision approves an external-world concept.
- Treat identity, memory, relationships, time, and per-agent state as first-class systems.
- Preserve shared-model, many-agent scalability. Do not assume a full independent foundation model per agent.
- Do not hardcode social outcomes, personality stereotypes, autonomous projects, or other behaviour intended to emerge through learning and experience.
- Do not claim consciousness. Do not claim a research goal is achieved without reproducible evidence.

## Engineering practice

- Maintain a clear boundary between Minecraft integration, environment schemas, agent runtime, model/research code, persistence, and evaluation.
- Validate all actions against ordinary Minecraft mechanics and the agent's permitted information. No hidden-state oracle, teleportation, direct inventory mutation, or equivalent shortcut belongs in a baseline.
- Keep `/spawn ai-agent <username>` and other lifecycle commands as authorized operator controls, separate from in-world chat and the agent action space. Preserve Survival parity and persistent identity/skin semantics.
- Write focused tests for behaviour and schemas; follow [`docs/TESTING.md`](docs/TESTING.md) and run relevant local checks before submitting changes.
- Keep changes scoped. Avoid unrelated refactors and premature shared abstractions.
- Document assumptions, nondeterminism, seeds, data versions, model/checkpoint versions, environment versions, hardware, and commands needed to reproduce experiments.
- Separate experimental code and conclusions from candidate production architecture.
- Update affected documentation when interfaces or architecture change. Add an ADR entry to `docs/DECISIONS.md` for material decisions.
- Reference GitHub issues in commits and pull requests when appropriate.
- Never commit credentials, private player data, unlicensed datasets, or generated artifacts without provenance.

## Coding standards before stack selection

The stack is intentionally open. Apply the native formatter, linter, static/type checker, and test runner of each introduced language. Pin tool versions or record a reproducible environment; use structured interfaces, explicit error handling, deterministic tests where possible, and small modules with documented ownership. A proposal introducing a core language, framework, database, mod loader, or inference runtime requires evidence and an ADR rather than preference alone.

## Research change checklist

- State the question or hypothesis and comparison baseline.
- Define metrics and falsification/stop criteria before running the experiment.
- Preserve raw observations and configuration where licensing and privacy permit.
- Report negative and inconclusive results.
- Distinguish learned behaviour from scripted scaffolding in every evaluation.
- Check data consent, licensing, privacy, leakage, and Minecraft/server policy.

## Pull request checklist

- Relevant tests and documentation pass.
- Links and Mermaid diagrams render.
- No unsupported capability claims or fake benchmark values were added.
- New persistent formats include versioning/migration considerations.
- Security, privacy, information-access, and multi-agent scaling consequences are described.

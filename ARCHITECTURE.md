# Proposed Architecture

This is a hypothesis to organize interfaces and experiments, **not a validated implementation**. Focused details live in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

```mermaid
flowchart TD
    OP[Authorized operator] -->|/spawn ai-agent username| MOD[Java Edition mod on logical server]
    MC[Minecraft world] --> MOD
    MOD --> PEID[Player embodiment and persistent profile]
    PEID --> IF[Versioned environment interface]
    IF -->|bounded observations and events| PE[State / perception encoder]
    PE --> FM[Shared foundation world / behaviour model]
    FM --> AR[Agent runtime]
    AR --> AS[Action system and legal-action validator]
    AS -->|player inputs / intentions| PEID
    PEID -->|ordinary Survival mechanics| MC
    AR --- ID[Identity and lifecycle]
    AR --- MEM[Episodic · semantic · procedural · spatial memory]
    AR --- PS[Personality · relationships · goals]
    AR --- PA[Optional personal adapters]
    MC -->|outcomes| IF
```

The foundation layer may eventually combine world understanding, planning/reasoning, behavioural policy, and language; whether these are one model, multiple models, or hybrid components is unresolved. The runtime binds shared competence to one persistent life. Personal adapters are optional research, not a v0.3 requirement.

The mod is server-authoritative and must work with both the integrated server used by single-player/LAN and a dedicated server. Its AI avatar should use the closest maintainable `ServerPlayer`-compatible representation so vanilla clients and other mods observe a player, not a custom humanoid mob. Exact compatibility hooks and whether clients also need the mod remain loader/version research questions. See [`docs/INTEGRATION.md`](docs/INTEGRATION.md).

## Decision timescales

| Timescale | Responsibility | Example | Initial implementation direction |
| --- | --- | --- | --- |
| Reactive | Immediate control and interruption | avoid fall, continue mining stroke | bounded policy loop; no remote prompt dependency |
| Behavioural | Select and execute short activities | approach tree, eat, answer nearby player | state + memory conditioned policy/skills |
| Deliberative | Plan and reconsider longer goals | establish shelter, prepare expedition | hierarchical planning research |
| Consolidation | Restructure durable state | summarize episodes, revise route confidence | asynchronous, auditable memory jobs |
| Learning | Update shared or personal parameters | offline skill refinement | gated experiments with replay, evaluation, and rollback |

These loops must exchange versioned messages without forcing one cadence. Sleeping or distant agents may reduce cognition frequency while world-critical simulation and identity persistence remain correct.

## Core boundaries

- **Integration boundary:** versioned observations, events, actions, capabilities, and outcomes; no model-specific types.
- **Embodiment boundary:** the mod owns player-compatible lifecycle, profile/skin synchronization, and translation of actions into ordinary Survival mechanics.
- **Runtime boundary:** per-agent state, scheduling, memory access, and lifecycle over an asynchronous boundary; no implicit singleton identity and no synchronous model wait on the Minecraft tick thread. See [`docs/RUNTIME_BOUNDARY.md`](docs/RUNTIME_BOUNDARY.md).
- **Model boundary:** batched inference over agent contexts with explicit state ownership and latency budgets.
- **Persistence boundary:** schema versions, atomic saves, migrations, export/deletion, and provenance.
- **Evaluation boundary:** deterministic/replayable scenarios where possible, plus long-running ecological evaluations that report variance.

## Open decisions

Fabric embodiment validation, exact player-entity hooks, observation encoding, model family, training framework, persistence store, inference runtime implementation, skin-catalog source, and personal adaptation technique remain unresolved. Each needs an issue, experiment, and ADR before commitment.

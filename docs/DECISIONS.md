# Architecture Decision Log

Use the template below for material decisions. Statuses are `proposed`, `accepted`, `superseded`, or `rejected`. An accepted decision records evidence and consequences; it is not proof the overall architecture works.

## ADR-0001 — Minecraft-native interfaces are the core boundary

- **Date:** 2026-09-11
- **Status:** accepted
- **Context:** The project seeks intelligence grounded directly in Minecraft rather than desktop automation.
- **Decision:** Core perception and action use versioned native game/mod interfaces with explicit information-access and legal-action enforcement.
- **Alternatives:** screenshots/OCR with mouse/keyboard; command APIs; direct server-state control.
- **Consequences:** Integration work is required and pixel-pretrained policies need an adaptation path. Screenshot control remains permissible only as a labelled comparison experiment.

## ADR-0002 — Shared foundation, isolated persistent lives

- **Date:** 2026-09-11
- **Status:** accepted
- **Context:** Many agents must be feasible without duplicating a huge model, while identities must remain distinct.
- **Decision:** Separate shared model weights/services from per-agent identity, memory, relationships, goals, personality, and optional personal modules.
- **Alternatives:** full model copy per agent; stateless sessions; shared mutable memory.
- **Consequences:** APIs require explicit ownership and isolation tests; batching is possible; personal adaptation needs lineage and rollback.

## ADR-0003 — Memory-first continual adaptation

- **Date:** 2026-09-11
- **Status:** accepted
- **Context:** Agents must learn continuously without unsafe full-model retraining after every event.
- **Decision:** Begin with explicit persistent memory. Treat personal adapters, skill modules, consolidation training, and shared updates as gated research.
- **Alternatives:** continuous end-to-end training; no persistent learning; prompt history alone.
- **Consequences:** Memory schemas and evaluation precede parameter-level lifelong learning; retention and provenance are mandatory.

## ADR-0004 — Emergence is not scripted

- **Date:** 2026-09-11
- **Status:** accepted
- **Context:** Hardcoded personalities and societies can imitate the desired appearance without intelligence.
- **Decision:** Provide learnable mechanisms, incentives, memories, and interaction affordances; measure and disclose all scripted scaffolding.
- **Alternatives:** personality prompts, role scripts, authored social storylines.
- **Consequences:** Early demos may look less polished; evaluation can distinguish learned behaviour.

## ADR-0005 — Technical stack remains open

- **Date:** 2026-09-11
- **Status:** accepted
- **Context:** Minecraft version/mod loader, language boundaries, model architecture, training framework, persistence, and inference requirements need evidence.
- **Decision:** Resolve each through a scoped comparison and follow-up ADR; do not infer a stack from repository tooling.
- **Alternatives:** select Fabric/NeoForge, Java/Python, PyTorch/JAX, a database, or an inference runtime immediately.
- **Consequences:** Interfaces and research questions can advance; implementation waits for evidence where choices are costly.

## Open decision queue

Platform/version support, process and language boundary, observation and action granularity, model family, training framework, persistence store, telemetry format, deterministic simulation approach, personal adaptation, and model serving remain unresolved.

## ADR template

```markdown
## ADR-NNNN — Title
- **Date:** YYYY-MM-DD
- **Status:** proposed
- **Context:**
- **Decision:**
- **Alternatives:**
- **Consequences:**
```

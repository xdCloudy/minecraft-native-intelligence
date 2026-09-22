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

## ADR-0006 — Java Edition mod with server-authoritative player embodiment

- **Date:** 2026-09-11
- **Status:** accepted
- **Context:** The intended user experience is easy installation and creation of an AI that appears and behaves through ordinary player systems, rather than a remote bot account or custom NPC mob.
- **Decision:** Ship the Minecraft integration as a Java Edition mod attached to the logical server. An authorized `/spawn ai-agent <username>` command creates or loads a project-owned, player-compatible entity with a persistent profile and skin. New agents default to Survival, and existing Minecraft server mechanics remain authoritative for health, hunger, inventory, crafting, armour/equipment, damage, movement, interaction, death, and respawn.
- **Alternatives:** external authenticated bot clients; a custom mob/NPC entity; desktop input automation; direct server-state simulation; a client-only mod.
- **Consequences:** The selected loader/version must expose maintainable player lifecycle and synchronization hooks. Vanilla and third-party player-system compatibility requires a test matrix. The design must not impersonate real authenticated accounts. The mod boundary is decided; Fabric versus NeoForge, exact version, client requirement, and process transport remain open.

## ADR-0007 — Skins are curated, assigned once, and persistent

- **Date:** 2026-09-11
- **Status:** accepted
- **Context:** Spawned agents need distinct, recognizable player appearances that survive restarts without appropriating real account identities or relying on fragile scraping.
- **Decision:** On first creation, choose randomly from an approved catalog of redistributable popular Minecraft-style skins; persist the catalog ID, content hash, geometry, and provenance with the agent identity. Do not reroll on spawn, reload, death, or respawn. Operator-requested changes are explicit and audited.
- **Alternatives:** default Steve/Alex only; random skin on every spawn; fetch an arbitrary popular player's live skin; generate a new skin at runtime.
- **Consequences:** A catalog licensing/provenance review and asset-integrity pipeline are required. Existing identities remain stable across catalog updates. Remote catalogs are optional rather than an installation dependency.

## ADR-0008 — Fabric 26.3 is the proposed first Minecraft platform

- **Date:** 2026-09-22
- **Status:** proposed
- **Context:** Issue #1 requires a loader, Minecraft/Java version policy, and client/server installation model before player embodiment and observation/action implementation can proceed. The platform must support the logical server in both integrated and dedicated environments, one distributable mod, operator commands, headless testing, vanilla-client compatibility where practical, and a maintainable player-compatible AI embodiment.
- **Decision:** Begin the v0.2 embodiment spike on Fabric, pinned to Minecraft 26.3 and Java 25. Load common code in both physical environments while keeping authoritative game logic on the logical server. Human clients are not required to install the project mod unless the embodiment/compatibility spike proves a client component unavoidable. Keep runtime, observation/action, persistence, and evaluation contracts loader-neutral.
- **Alternatives:** NeoForge on a stable 26.x baseline; Quilt Loader/Fabric-compatible stack; maintaining multiple loaders from the start.
- **Consequences:** Fabric currently offers a direct 26.3 path, one-JAR tooling, server commands, GameTests, and a small integration surface. The unresolved risk is synthetic-player lifecycle support: this decision is rejected if a vanilla-visible persistent ServerPlayer-compatible agent requires a fake authenticated connection, a required client mod, or broad brittle mixins, especially if a matched NeoForge spike satisfies the same tests more cleanly. Version upgrades are explicit, pinned migrations rather than floating to latest. See docs/MOD_PLATFORM.md for the comparison, spike plan, falsifiers, and sources.

## ADR-0009 — Data use is deny-by-default and artifact-specific

- **Date:** 2026-09-22
- **Status:** accepted
- **Context:** Gameplay telemetry, chat, skins, worlds, public videos, research datasets, derived labels, and trained artifacts can have different copyright, database, contractual, consent, privacy, and redistribution constraints. Public availability and a repository code license do not answer all of those layers.
- **Decision:** No data source enters collection, training, evaluation publication, or redistribution unless a versioned manifest records source/provenance, applicable rights or consent, permitted uses, privacy classes, retention/deletion policy, transformation lineage, and unresolved questions. Missing or contradictory evidence means the source is on hold. Prefer project-collected native telemetry under a purpose-specific consent protocol and synthetic/agent-only data where human data is unnecessary. Human chat is off by default. Never promise deletion from trained parameters without a validated mechanism that can actually provide it.
- **Alternatives:** Treat public/downloadable data as reusable by default; infer data rights from an open-source code license; defer provenance and deletion lineage until publication.
- **Consequences:** Dataset ingestion and training tooling require machine-readable use gates and lineage. Third-party datasets may remain unusable until artifact-specific terms are resolved. Human collection needs versioned consent, minimisation, retention, and withdrawal workflows. See [DATA_GOVERNANCE.md](DATA_GOVERNANCE.md) for the source matrix, consent requirements, risks, and review triggers.

## Open decision queue

Fabric versus NeoForge (or another loader), supported Minecraft/Java versions, whether clients also need the mod, exact player lifecycle hooks, process and language boundary, observation and action granularity, model family, training framework, persistence store, telemetry format, skin catalog source, deterministic simulation approach, personal adaptation, and model serving remain unresolved.

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

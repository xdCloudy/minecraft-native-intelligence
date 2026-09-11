# Architecture Detail

## Responsibilities

### Java Edition mod and player embodiment

The distributable mod attaches to the logical server: the integrated server in single-player/LAN or the dedicated server in multiplayer. It registers administrative lifecycle commands, creates and tracks player-compatible AI entities, owns their Minecraft profile/skin synchronization, and delegates all game consequences to normal server mechanics. Vanilla-compatible clients should require no special AI UI; a small client component is acceptable only when a loader or presentation requirement makes it necessary and must degrade cleanly. See [Integration](INTEGRATION.md).

### Native environment interface

Produces observations and events that an ordinary embodied player could legitimately access, and accepts semantic game actions. It owns Minecraft-version adaptation, capability negotiation, tick/time semantics, and enforcement of server/operator policy. See [Perception](PERCEPTION.md) and [Action space](ACTION_SPACE.md).

### State and perception encoder

Transforms variable local geometry, entities, inventory, events, and temporal context into model-ready representations while preserving masks, coordinate frames, uncertainty, and provenance. It must not smuggle in hidden world state.

### Shared foundation intelligence

A research boundary for reusable world and behavioural competence. Candidate designs may be model-based, policy-based, modular, or hybrid. “Foundation” does not imply an LLM or a fixed scale.

### Agent runtime

Owns one individual's lifecycle, identity pointer, active context, memory access, relationships, goals, personality state, action arbitration, persistent skin reference, and optional personal modules. Many runtimes may share model servers but must never share mutable personal state accidentally.

### Action system

Converts intentions/policy outputs into typed actions, checks schema and timing, rejects illegal or unavailable actions, and returns outcomes. The Minecraft integration remains authoritative.

## Data flow

Every observation and action should carry agent identity, world/session identity, schema version, monotonic sequence information, game time, validity masks, and trace correlation. Persistent facts link to evidence; model inputs are reconstructable subject to privacy retention policy.

## Failure isolation

- A failed model request should degrade to safe idle or a bounded fallback, not corrupt identity.
- A malformed action is rejected and observed as a failure.
- Persistence failures must be visible and recoverable; partial writes must not masquerade as valid saves.
- One agent's slow planning or consolidation must not stall every agent.
- Version incompatibility fails closed with actionable diagnostics.

## Research seams

Stable schemas should allow behavioural cloning, hierarchical RL, learned world models, language grounding, memory retrieval, and multi-agent experiments to change independently. Experiments may temporarily cross a seam but must document why and avoid turning that coupling into the default architecture without an ADR.

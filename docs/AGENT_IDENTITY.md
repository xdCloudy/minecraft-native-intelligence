# Persistent agent identity record

Status: store-neutral v0 contract for issue #9. This defines identity and
ownership semantics; it does not select or implement a persistence backend.

The machine-readable record is [`docs/agents/identity.schema.json`](agents/identity.schema.json)
and its example is [`docs/agents/identity.example.v0.json`](agents/identity.example.v0.json).

## Identity and ownership

- `agent_id` is a cryptographically random project identifier. It is immutable
  and independent of a model process, Minecraft entity ID, username, or
  Minecraft profile.
- `minecraft_profile_id` is a separate project-owned UUID for the player
  profile. It must not copy a real account UUID, authentication token, or
  session property.
- `world_binding_id` is an opaque project identifier for the world/save that
  owns this identity. It is not a filesystem path, host name, seed, or secret.
  The adapter resolves it from its local world registry.
- `personal_state_refs` are logical references, never paths or credentials.
  Every reference is scoped to its `agent_id`. A storage adapter must enforce
  that owner at read and write time; a schema-valid reference alone is not
  authorization.
- `revision` is a monotonically increasing record revision. A backend must
  update it atomically with the record and reject stale writes; backend
  transaction details remain a persistence-store decision.

`agent_id`, `minecraft_profile_id`, `world_binding_id`, and `created_at` are
immutable after creation. Username uniqueness is enforced on the case-folded
name within the bound world, while display names may repeat. Creation must
reserve the IDs, username, and initial state partitions atomically or leave no
record behind.

The UUIDs are identifiers, not secrets or access capabilities. Authorization
comes from the operator/runtime boundary and storage policy. Usernames and
display names are mutable presentation values, never primary keys. Skin choice
is pinned by catalog ID, content hash, and model so catalog changes cannot
silently change an existing identity.

## Lifecycle and import semantics

`despawned` means no live Minecraft player entity is currently present; all
identity and personal state remain. `paused` preserves identity and state
while operator policy prevents cognition/actions. `retired` is terminal for
normal spawning, but retention or deletion is governed by a separate audited
operator operation. A new spawn must not silently create a replacement identity
when an existing username or profile is found.

Allowed lifecycle transitions are `active -> paused|despawned|retired`,
`paused -> active|despawned|retired`, and
`despawned -> active|paused|retired`. `retired` is terminal. Each transition
increments the revision and is committed with its associated entity/state
changes by the selected backend.

- **Move/restore:** an authenticated export may preserve the same IDs only
  when the source is retired or made unavailable as part of one controlled
  transfer, and the destination does not already own those IDs. A world move
  updates `world_binding_id` in the same transaction as the associated world
  state migration and records `lineage.operation = "relocated"`.
- **Clone:** allocate new `agent_id`, `minecraft_profile_id`, and target-world
  binding. Copy only explicitly selected state. Rewrite every copied state
  reference into the new agent namespace, retain the source ID in lineage, and
  require explicit operator authorization. A clone is a new individual; it
  must not share mutable personal-state partitions with its source.
- **Conflict or merge:** reject duplicate IDs, username collisions, world
  mismatches, dangling references, and attempts to merge mutable lives. There
  is no implicit “last write wins” import behavior in v0.

The current schema provides structural validation. Import/export envelopes,
cryptographic signatures, atomic file/database transactions, migration
execution, and deletion propagation are out of scope until persistence-store
research selects those mechanisms.

## Threat model and controls

| Threat | Required control in v0 |
| --- | --- |
| Accidental identity collision or reuse | Generate UUIDv4 IDs; enforce uniqueness in the world registry; never derive identity from username or runtime session |
| Cross-agent state aliasing | Require owner-scoped references and enforce distinct mutable partitions at storage access; test clone remapping |
| Stale concurrent updates | Compare `revision` and commit record plus state-reference changes atomically in the chosen backend |
| Cross-world state loaded into the wrong save | Check `world_binding_id` against the active world's registry before spawn or state access; fail closed |
| Forged import or identity takeover | Treat files/records as untrusted input; authorize imports separately, reject collisions, and never interpret IDs as credentials |
| Path traversal or host disclosure | Keep references logical and resolve them through a backend-owned mapping; never accept paths, URLs, or tokens in this record |
| Real-player impersonation or skin-rights violation | Generate a project-owned profile UUID; record approved catalog assets and hashes; prohibit authentication material and arbitrary profile scraping |
| Display-name spoofing or command injection | Validate names against Minecraft constraints, escape presentation contexts, and keep display data out of command construction |

This contract reduces accidental cross-wiring but does not itself provide
confidentiality, authorization, crash consistency, or durable storage. Those
require backend and runtime boundary decisions plus integration tests.

## Verification

Run:

```powershell
python scripts/validate_agent_identity.py
```

The check validates the example's core ownership rules, performs a JSON
serialization round trip, checks that two records do not share mutable state
references, and checks that a clone remaps its owner-scoped references. It is
contract evidence only; it does not prove persistent writes, restart survival,
or a working Minecraft lifecycle.

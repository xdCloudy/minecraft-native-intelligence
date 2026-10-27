# Sensed entity identity

Issue #5 defines how observation v0 evidence may support continuity hypotheses
without leaking server-global identity. The machine-readable contract is
`docs/entities/identity.v0.json`, validated against
`docs/entities/identity.schema.json`.

## Boundary and representation

`observation_ref` remains local to the current observation/event window. It is
not persisted as identity. The proposed memory representation is an
agent-owned association graph: observation episodes are evidence nodes and
opaque track handles link episodes that may concern the same perceptual
continuity. Handles are scoped to an agent and world/memory epoch. They are not
Minecraft entity IDs, UUIDs, player profiles, or claims about actual individual
identity.

Observation facts and derived continuity remain separate. The adapter exposes
only current v0 policy fields and delivered events. A runtime may derive
candidate scores from those fields, but the heuristic score buckets are not
probabilities, calibrated confidence, or validated capability. The reference
prototype exists to make the scoring contract executable and test its edge
cases; it uses synthetic scores and does not consume Minecraft observations.

## Uncertainty and information limits

- Similar observations may support multiple candidates. Keep them as separate
  tracks and preserve the tie; do not force a one-to-one association.
- A display name is a weak cue because it may be absent, duplicated, changed,
  or spoofed.
- Partial or unavailable coverage cannot establish absence, death, or
  despawn. Complete coverage supports only “not sensed in this declared scope.”
- A complete-scope empty collection may put a memory track in
  `not_sensed_in_scope`; this is not a claim that it despawned or died.
- A first sighting means new-to-memory, not newly spawned in the world.
- Mounts, passengers, projectiles, and their owners remain distinct tracks.
  A visible relation contributes evidence about the relation and never
  transfers identity.
- Unknown fields add no negative evidence. Memory splits and retirement retain
  their provenance and remain agent-local.
- Evaluator labels, server UUIDs, entity IDs, hidden state, and policy-hidden
  metadata are not tracker inputs.

See the five conformance fixtures in `docs/entities/fixtures/`. The local check
is:

```powershell
python scripts/validate_entity_identity.py
```

Passing checks establish only that the proposed contract is internally
consistent and that the deterministic synthetic examples match the declared
heuristic. They do not establish reliable re-identification or learned
behaviour.

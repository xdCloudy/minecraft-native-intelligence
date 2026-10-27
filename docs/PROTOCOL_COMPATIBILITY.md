# Environment protocol compatibility

Status: proposed v0 policy and conformance contract for issue #61. It defines
deterministic peer negotiation; it does not implement the gRPC/Protobuf wire
transport or certify Minecraft runtime behavior.

Machine-readable producer and consumer manifests are in [`docs/protocol/`](protocol/).
The reference producer tuple uses the Minecraft 26.3 Fabric embodiment spike.
It is an example tuple, not a product support guarantee.

## Negotiation inputs

Before observations or actions flow, the peers exchange the implementation and
environment identity, protocol major/minor, exact observation/action request/
action outcome schema versions, and offered/required capabilities. The producer
manifest identifies Minecraft Java version, loader and loader version, mod ID,
mod version, Java major version, and whether the logical server is integrated,
dedicated, a replay, or an offline tool. These are compatibility metadata, not
policy inputs for the agent.

The consumer policy explicitly lists accepted game, Java, loader, mod,
server-mode, and schema versions. No wildcard or implicit “latest” match is
supported in v0.
This keeps a version upgrade visible and makes old/new peer outcomes
reproducible.

## Deterministic outcomes

| Condition | Outcome | Required behavior |
| --- | --- | --- |
| Same protocol major and peer minor is within the consumer's declared maximum; exact schemas and required capabilities are supported | `accept` | Begin the session with the negotiated common capability set |
| Same protocol major, peer minor is newer, and every required capability and exact schema is supported | `degraded` | Continue only with known fields/capabilities; report `newer_protocol_minor` and retain diagnostics |
| Optional capability is unknown or not allowed | `degraded` | Omit it; do not reinterpret another field or invent equivalent behavior |
| Experimental capability is explicitly allowlisted | `degraded` | Enable only that named capability and mark all resulting evidence experimental |
| Required capability is unknown, unsupported, or experimental without explicit allowlisting | `reject` | Do not start action acceptance; report the capability ID and reason |
| Protocol major, environment tuple, server mode, or exact observation/action schema is unsupported | `reject` | Fail closed before action acceptance; show an actionable compatibility diagnostic |
| Producer marks a capability required but does not offer it | `reject` | Treat the producer manifest as invalid |

Protocol minor increments are reserved for additive, ignorable transport
metadata. A minor increment cannot change the meaning or legality of an
observation/action field. Any semantic change requires a new exact schema
version. The schema transitions tested here (`observation.v0` to `v1`,
`action-request.v0` to `v1`, and `action-outcome.v0` to `v1`) reject under a v0
consumer; no automatic conversion is performed.

Capabilities are namespaced identifiers with explicit `stable` or
`experimental` maturity. Unknown optional capabilities are omitted. Stable
capability IDs do not authorize hidden information or illegal actions; the
information-access and action validators remain authoritative. Experimental
capabilities require an exact local allowlist entry and produce degraded
session status so they cannot be mistaken for baseline evidence.

## Version-support policy

- Keep protocol major/minor separate from Minecraft, mod, loader, observation,
  action request, action outcome, and persistent-store versions.
- Match Java, Minecraft, loader, and mod versions against exact consumer
  allowlists. Upgrade those tuples through an explicit compatibility change
  and rerun the relevant conformance suite.
- Keep schema versions exact. Unknown versions fail closed; migrations are
  explicit adapters with separate tests and provenance.
- Report integrated, dedicated, replay, and offline modes explicitly. A mode is
  supported only when its tuple appears in the consumer policy and the relevant
  mode-specific tests have passed. The sample policy is illustrative.
- Use `degraded` only when the peers can preserve the common semantics while
  omitting optional capabilities. Degraded operation never relaxes legal-action
  validation, player-equivalent information access, sequence/session checks,
  or the no-blocking-tick rule.
- Do not expose protocol, loader, schema, or capability metadata as Minecraft
  world perception. In particular, these values must not enter the policy view
  unless a separate reviewed observation field grants that information.
- JSON manifests and fixtures in this directory are descriptive/conformance
  artifacts. The selected runtime wire remains binary Protocol Buffers over
  local asynchronous gRPC as recorded in [RUNTIME_BOUNDARY.md](RUNTIME_BOUNDARY.md).

## Conformance evidence

`docs/protocol/compatibility.v0.json` covers compatible, degraded, and
incompatible peers, including major mismatch, additive minor versions, exact
schema transitions, unsupported Minecraft/loader/server-mode tuples,
unsupported optional/required capabilities, and experimental allowlisting.
Run:

```powershell
python scripts/validate_protocol_compatibility.py
```

These tests validate the declared negotiation algorithm and fixtures. They do
not prove generated Protobuf compatibility, network security, process recovery,
integrated/dedicated Minecraft execution, or client presentation. Those remain
runtime integration and platform-spike gates.

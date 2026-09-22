# Data

The canonical telemetry design should align observation, action request, action outcome, events, agent/world identity, game time, schema version, and trace identifiers. Derived labels, memory writes, model outputs, and experiment configuration should remain traceable to source records.

Before collection, define purpose, consent, retention, access, deletion, redaction, licensing, and whether human chat or identifiers are included. Server participation does not automatically grant permission to publish or train on every interaction. Secrets and host/private external information must never enter agent-visible observations or datasets.

Datasets need manifests, provenance, hashes, Minecraft/mod versions, collection policy, known biases, split logic, transformations, and licenses. Prefer data minimisation and pseudonymous identifiers. Provide deletion propagation for retained raw data and derived stores where feasible, and document limitations for trained artifacts.

The binding collection/use decision framework is [DATA_GOVERNANCE.md](DATA_GOVERNANCE.md). A source with missing provenance, unresolved rights/terms, or no affirmative permitted-use decision is on hold and must not silently enter training, publication, or redistribution.

## Player profiles and skins

An agent identity stores a stable skin catalog entry and content hash, not a transient random choice on every spawn. The default catalog may contain popular Minecraft-style skins only when their redistribution and use are permitted and provenance is recorded; the project must not scrape or impersonate arbitrary player profiles. Selection occurs once at identity creation, is deterministic from the persisted assignment thereafter, and can be changed only by an authorized lifecycle operation. Catalog updates must not silently alter existing agents whose stored skin content remains available.

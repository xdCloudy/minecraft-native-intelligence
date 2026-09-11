# Data

The canonical telemetry design should align observation, action request, action outcome, events, agent/world identity, game time, schema version, and trace identifiers. Derived labels, memory writes, model outputs, and experiment configuration should remain traceable to source records.

Before collection, define purpose, consent, retention, access, deletion, redaction, licensing, and whether human chat or identifiers are included. Server participation does not automatically grant permission to publish or train on every interaction. Secrets and host/private external information must never enter agent-visible observations or datasets.

Datasets need manifests, provenance, hashes, Minecraft/mod versions, collection policy, known biases, split logic, transformations, and licenses. Prefer data minimisation and pseudonymous identifiers. Provide deletion propagation for retained raw data and derived stores where feasible, and document limitations for trained artifacts.

# Memory

Memory is durable, per-agent state—not a transcript stuffed into a prompt. Every record should have an owning agent, world identity, time, provenance, confidence, access policy, schema version, and links to supporting or conflicting evidence.

| System | Stores | Key research questions |
| --- | --- | --- |
| Episodic | situated events and experiences | segmentation, salience, compression, temporal retrieval |
| Semantic | facts, beliefs, concepts, and generalisations | evidence aggregation, confidence, contradiction, revision |
| Procedural | skills and ways of acting | representation, practice, transfer, success conditions |
| Spatial | places, routes, structures, hazards | frames, change detection, topology, uncertainty |

Retrieval should combine relevance, recency, importance, causal/relational links, and current context without making forgotten information omniscient. Consolidation may summarize episodes into semantic or procedural structures, but must retain traceable evidence and support rollback. Decay lowers accessibility or confidence; it should not silently erase protected identity-defining or safety-critical memories.

Statements from chat are claims with a source, not truth. Experience can support or contradict them. Competing beliefs may coexist until evidence justifies revision. Evaluation should test delayed recall, false-memory resistance, provenance, changed-world detection, cross-agent isolation, and bounded storage/latency.

# Learning and Adaptation

Learning has layers with different risk:

1. **Working adaptation:** current context and active plans; cheap and transient.
2. **Persistent memory:** durable episodes, beliefs, routes, skills, and relationships; the default initial mechanism.
3. **Skill/personal modules:** optional compact policies or adapters trained from an individual's experience.
4. **Shared foundation updates:** infrequent, offline, versioned changes evaluated across a broad population.

Continuous living must not imply continuous full-model gradient updates. Any parameter-level adaptation needs replay or other retention controls, held-out old and new tasks, identity/privacy boundaries, checkpoint lineage, canary evaluation, and rollback. Consolidation jobs should be interruptible and auditable.

Key experiments compare memory-only adaptation, retrieval plus fixed policy, personal adapters, modular skills, and shared fine-tuning on learning speed, retention, interference, transfer, compute, and privacy. Catastrophic-forgetting tests must span old skills, factual beliefs, language grounding, and safety constraints—not only aggregate reward.

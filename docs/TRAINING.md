# Training

Training strategy remains open. Candidate stages include representation learning from native telemetry, behavioural cloning from aligned trajectories, offline RL, online fine-tuning in controlled worlds, model-based learning, hierarchical policies, language grounding, and multi-agent curricula.

Every training run should pin code, environment/mod version, schema, dataset manifest, checkpoint parent, configuration, seeds, hardware, and evaluation suite. Model artifacts need immutable identifiers, checksums, lineage, licenses, and promotion/rollback criteria. Train/test splits must control for world seeds, structures, players, and temporally adjacent trajectory leakage.

Human gameplay is not automatically licensed training data. Pixel/video-pretrained work can be a comparison or initialization source, but the project must measure transfer to native observations and actions rather than assume compatibility.

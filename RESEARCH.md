# Research Programme

The project asks whether broad, persistent, socially grounded Minecraft intelligence can be built from native state/action interfaces, shared learned competence, and durable individual lives. Architecture is provisional until comparative experiments support it.

This page explains the research programme. Use the [research matrix](docs/RESEARCH_MATRIX.md) for individual hypotheses, the [model/training matrix](docs/MODEL_TRAINING_MATRIX.md) for architecture candidates, and the [documentation guide](docs/README.md) to find the relevant subsystem design.

## Workstreams

1. **Embodiment and representation:** identify sufficient, non-omniscient observation structures and expressive legal actions.
2. **World and behaviour learning:** compare imitation, offline/online RL, model-based learning, hierarchical control, and hybrids.
3. **Persistent cognition:** test memory types, retrieval, provenance, contradiction, consolidation, and long-horizon goal management.
4. **Grounded language and social learning:** measure whether conversation refers to shared state and changes later belief/action appropriately.
5. **Individual adaptation:** separate memory-based learning from parameter updates; quantify retention, transfer, privacy, and rollback.
6. **Multi-agent systems:** measure scheduling, batching, identity isolation, social dynamics, and emergent communication without scripting outcomes.
7. **Evaluation:** build scenario suites and longitudinal studies that expose brittleness, privileged information, and scripted shortcuts using the versioned contract in [`docs/EVALUATION.md`](docs/EVALUATION.md).

## Evidence standard

Each experiment must predeclare a question/hypothesis, baseline, intervention, metrics, seeds, environment version, compute budget, stop/falsification conditions, and expected output. Execute and preserve runs through the reproducibility framework in [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md). Preserve configuration and raw results where policy permits. Report variance, negative results, failures, and the exact amount of scripted scaffolding. A compelling video is not sufficient evidence.

In particular, compare **plan quality** with **completed legal in-game actions** as different outcomes. A synthetic result, external paper, or generated task plan is not evidence of an autonomous Minecraft capability. The [evaluation protocol](docs/EVALUATION.md) defines scenario and result requirements.

## Prior work

[VPT](https://arxiv.org/abs/2206.11795), [MineDojo](https://arxiv.org/abs/2206.08853), [STEVE-1](https://arxiv.org/abs/2306.00937), and [Voyager](https://arxiv.org/abs/2305.16291) are important Minecraft research references. They inform imitation, evaluation, language conditioning, curriculum, and skill-library experiments. Their original results do not demonstrate MNI's intended persistent, native-state, many-agent architecture.

See [research references and gaps](docs/RESEARCH_REFERENCES.md) for what each project reports, what can be reproduced, and which ideas merit comparison rather than adoption.

## Decision discipline

Research outputs should end in one of: adopt, reject, continue investigation, or insufficient evidence. Architectural adoption requires an ADR. Benchmarks should test generalisation and long-term retention, not only task completion on known seeds.

Document conclusions, including negative results, in the canonical [progress system](docs/PROGRESS_WORKFLOW.md). Do not change implementation or capability status because a research protocol has been written.

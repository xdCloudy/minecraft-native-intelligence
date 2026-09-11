# Research Programme

The project asks whether broad, persistent, socially grounded Minecraft intelligence can be built from native state/action interfaces, shared learned competence, and durable individual lives. Architecture is provisional until comparative experiments support it.

## Workstreams

1. **Embodiment and representation:** identify sufficient, non-omniscient observation structures and expressive legal actions.
2. **World and behaviour learning:** compare imitation, offline/online RL, model-based learning, hierarchical control, and hybrids.
3. **Persistent cognition:** test memory types, retrieval, provenance, contradiction, consolidation, and long-horizon goal management.
4. **Grounded language and social learning:** measure whether conversation refers to shared state and changes later belief/action appropriately.
5. **Individual adaptation:** separate memory-based learning from parameter updates; quantify retention, transfer, privacy, and rollback.
6. **Multi-agent systems:** measure scheduling, batching, identity isolation, social dynamics, and emergent communication without scripting outcomes.
7. **Evaluation:** build scenario suites and longitudinal studies that expose brittleness, privileged information, and scripted shortcuts.

## Evidence standard

Each experiment must predeclare a question/hypothesis, baseline, intervention, metrics, seeds, environment version, compute budget, stop/falsification conditions, and expected output. Preserve configuration and raw results where policy permits. Report variance, negative results, failures, and the exact amount of scripted scaffolding. A compelling video is not sufficient evidence.

## Prior work

[VPT](https://arxiv.org/abs/2206.11795) demonstrates large-scale semi-supervised behavioural cloning from Minecraft video; [MineDojo](https://arxiv.org/abs/2206.08853) provides an open-ended environment and knowledge resources; [STEVE-1](https://arxiv.org/abs/2306.00937) demonstrates text-conditioned behaviour using VPT/MineCLIP; and [Voyager](https://arxiv.org/abs/2305.16291) demonstrates LLM-driven exploration with code skills. Each informs data, evaluation, or modular skill research, but none by itself establishes our native-state, persistent-identity, autonomous, many-agent goal. See [`docs/RESEARCH_REFERENCES.md`](docs/RESEARCH_REFERENCES.md) for comparisons and gaps.

## Decision discipline

Research outputs should end in one of: adopt, reject, continue investigation, or insufficient evidence. Architectural adoption requires an ADR. Benchmarks should test generalisation and long-term retention, not only task completion on known seeds.

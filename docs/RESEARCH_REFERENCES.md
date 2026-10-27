# Research References and Gaps

Primary papers and official project repositories are preferred. Inclusion means “relevant evidence,” not endorsement or architectural adoption.

## Java Edition mod integration

The official [Fabric developer guides](https://docs.fabricmc.net/develop/) describe a lightweight Java Edition mod toolchain, server/client entry points, and distributable mod JARs; the [Fabric networking guide](https://docs.fabricmc.net/develop/networking) documents logical client/server synchronization, including the integrated server used in single-player; and its [command guide](https://docs.fabricmc.net/develop/commands/basics) documents server command registration. Official [NeoForge getting-started documentation](https://docs.neoforged.net/docs/1.21.1/gettingstarted/) likewise documents Java/Gradle mod JARs and dedicated-server testing.

These sources support the feasibility of an installable Java mod and server-authoritative command/network boundary. They do not establish that either loader can cleanly instantiate a fully player-compatible AI entity across all vanilla and third-party systems. Loader/version selection, exact `ServerPlayer`-compatible hooks, and client requirements therefore remain empirical issues rather than assumed facts.

## Minecraft agents and datasets

### VPT — Video PreTraining

[Baker et al., 2022](https://arxiv.org/abs/2206.11795) learn an inverse-dynamics model from labelled Minecraft footage, use it to label large amounts of online video, and behaviourally clone a general prior over pixel observations and low-level controls.

- **Demonstrates:** internet-scale semi-supervised imitation can produce broad Minecraft control and support downstream fine-tuning.
- **Potential reuse:** data scaling hypotheses, behavioural-cloning baselines, inverse-dynamics methodology, long-horizon evaluation lessons.
- **Difference:** VPT uses pixels and human interface actions; this project targets structured native observations/actions, persistent individuals, autonomy, memory, language, and many-agent operation.
- **Gap:** determine whether native-state telemetry preserves broad human demonstrations and how to align/transfer pixel-trained priors.

### MineDojo and MineCLIP

[Fan et al., 2022](https://arxiv.org/abs/2206.08853) provide a Minecraft research framework, open-ended tasks, multimodal knowledge, and a video-language reward approach.

- **Demonstrates:** a broad environment/data/evaluation ecosystem and language-conditioned learned rewards.
- **Potential reuse:** task taxonomy, evaluation design, dataset governance lessons, language–behaviour representation baselines.
- **Difference:** thousands of externally specified tasks and internet knowledge do not themselves yield persistent autonomous lives or native ontology.
- **Gap:** evaluate version compatibility, licensing, native-interface suitability, and whether learned rewards encourage shortcuts.

### STEVE-1

[Lifshitz et al., 2023](https://arxiv.org/abs/2306.00937) instruction-tune a VPT-based behavioural model using MineCLIP latent goals and hindsight relabelling.

- **Demonstrates:** open-ended text conditioning can be learned with limited direct instruction-labelled trajectories.
- **Potential reuse:** relabelling, classifier-free guidance ablations, command-following comparison baseline.
- **Difference:** short-horizon instructions, pixels, and controls are narrower than grounded conversational memory and autonomous goal formation.
- **Gap:** connect language to persistent beliefs, social context, native state, and delayed behavioural consequences.

### Voyager

[Wang et al., 2023](https://arxiv.org/abs/2305.16291) use an LLM, automatic curriculum, iterative prompting, and an executable code skill library for open-ended Minecraft exploration.

- **Demonstrates:** curriculum and compositional skills can extend exploration and retain reusable procedures.
- **Potential reuse:** skill-library evaluation, curriculum questions, error-feedback loops.
- **Difference:** an external LLM generates code for a Mineflayer-style agent; that is explicitly not this project's core architecture.
- **Gap:** learn procedural competence and intrinsic goals within a grounded native policy without arbitrary code execution or prompt-defined identity.

### MineRL

[Guss et al., 2019](https://arxiv.org/abs/1904.10079) introduce large human-demonstration datasets and competition tasks for sample-efficient Minecraft learning.

- **Demonstrates:** human trajectories and competition protocols can support reproducible Minecraft imitation/RL research.
- **Potential reuse:** dataset format/evaluation lessons and behavioural-cloning baselines.
- **Difference:** benchmark task completion is only one slice of persistent general intelligence.
- **Gap:** native telemetry collection, current-version support, consent/licensing, and longitudinal evaluation.

## World and hierarchical models

[World Models](https://arxiv.org/abs/1803.10122) show policies using compact learned dynamics, while [DreamerV3](https://arxiv.org/abs/2301.04104) learns behaviours through imagined trajectories across diverse domains, including Minecraft diamond collection. They motivate predictive state and model-based planning, but neither result establishes persistent identity, grounded language, or social learning. Research must compare predictive accuracy with downstream behaviour while preventing hidden-state leakage.

[HIDIO](https://arxiv.org/abs/2101.06521) studies task-agnostic learned options for hierarchical RL. Temporally extended behaviours may bridge reactive control and long plans, but Minecraft options should be learned and evaluated for transfer rather than named scripts that conceal task logic.

## Memory and continual learning

[Generative Agents](https://arxiv.org/abs/2304.03442) demonstrate observation, retrieval, reflection, and planning patterns for believable simulated social agents. The natural-language/LLM architecture is useful as a memory ablation reference, not a template for Minecraft-native intelligence; believability is also weaker than grounded causal competence.

[Kaplanis et al., 2018](https://proceedings.mlr.press/v80/kaplanis18a.html) investigate multi-timescale synaptic mechanisms for continual RL. [Yoo et al., 2024](https://proceedings.mlr.press/v235/yoo24a.html) show that replay can still have unstable optimisation dynamics and propose layerwise proximal replay. These support treating replay and adapters as hypotheses, requiring retention and plasticity tests rather than assuming replay solves catastrophic forgetting.

## Intrinsic motivation and multi-agent learning

[Random Network Distillation](https://arxiv.org/abs/1810.12894) provides a simple prediction-error exploration bonus. It is a useful curiosity baseline, but novelty reward alone can produce noisy-TV behaviour, neglect, or endless exploration; Minecraft autonomy needs diverse needs, self-generated goals, memory, competence, and social context.

[Gupta et al., 2020](https://arxiv.org/abs/2004.02780) study learned discrete communication among networked cooperative agents and analyse grounding. The fixed cooperative objective differs from open-ended Minecraft societies, but its protocol-grounding evaluations can inform agent-to-agent studies.

## Research and comparative adoption candidates (2026-10-27 audit)

### Additional Minecraft implementations to evaluate

The following official repositories are **external references**, not implementations
inside MNI. The repository links and stated code availability were inspected on
2026-10-27; upstream performance results and version compatibility have **not**
been independently reproduced by this project.

| Reference | What upstream publishes | Useful comparison for MNI | Boundary and reuse recommendation |
| --- | --- | --- | --- |
| [JARVIS-1 paper](https://arxiv.org/abs/2311.05997) and [official code](https://github.com/CraftJarvis/JARVIS-1) | Authors report multimodal memory-assisted planning and goal-conditioned controllers across Minecraft tasks. The official repository states important multimodal descriptor/retrieval and learning components are not released. | Compare temporally scoped memory retrieval, hierarchical task planning and the difference between memory assistance and actual continual learning. | **Partial reproducibility.** Treat task metrics as author claims pending reproduction. Do not claim the released code reproduces the full reported system. Verify component-specific licenses before adaptation. |
| [MineStudio](https://github.com/CraftJarvis/MineStudio) and [paper](https://arxiv.org/abs/2412.18293) | A MineRL-derived environment/data/policy/training/inference/benchmark research toolkit; the repository is MIT-licensed and documents Python and older JDK simulator requirements. | Test data interchange, replay/trajectory protocols and reproducible baseline training on an isolated research harness. | **Evaluate or adapt selectively.** Its simulator/version and pixel-action assumptions cannot validate the proposed native Java-mod interface or current multiplayer lifecycle. Audit assets and dataset terms separately from repository code. |
| [Mineflayer](https://github.com/PrismarineJS/mineflayer) | Maintained MIT-licensed JavaScript bot library with world queries, physics, inventory, navigation and integration examples. | Use only for disclosed external-bot control baselines, reference task fixtures or protocol comparisons. | **Comparison, not integration target.** Authenticated network bot assumptions conflict with the accepted server-authoritative player embodiment ADR; license and Minecraft-version support still need revision pinning. |
| [Mindcraft](https://github.com/mindcraft-bots/mindcraft) | MIT-licensed LLM/Mineflayer bot framework with task fixtures and optional code generation; its own README warns that generated code execution can be vulnerable to injection. | Compare building task definitions, multi-agent coordination controls and high-level prompt planning against native learned behaviour. | **External reference only.** Do not make arbitrary LLM-authored JavaScript or a remote bot account part of the native action boundary. Audit prompt/tool privileges in any benchmark. |

### Additional methods with bounded hypotheses

| Research | Testable Minecraft application | Falsifier or limitation | Tracker |
| --- | --- | --- | --- |
| [Speculative decoding](https://proceedings.mlr.press/v202/leviathan23a.html) | Compare target-only serving to draft-and-verify serving with shared-model inference for one/four/sixteen agents; record draft acceptance and decision latency, not only token rate. | The paper's acceleration on its model/hardware does not predict MNI gains. VRAM, variable prompt lengths, cache isolation and scheduling may erase benefits. | `MO-019`, `IN-016`, `EV-019` |
| [Structured-output constrained decoding benchmark](https://arxiv.org/abs/2501.10868) | Compare action-schema-constrained generation with unconstrained proposals followed by the same server-side legal-action validator. | Syntactically valid actions can still be impossible, unauthorized, stale or semantically wrong. Grammar conformance is not gameplay success. | `MO-018` |
| [Inverse reinforcement learning](https://ai.stanford.edu/~ang/papers/icml04-apprentice.pdf) | Infer uncertain risk/resource preferences from consented native Survival demonstrations, comparing with direct cloning and explicitly shaped rewards. | Reward ambiguity, demonstrator bias, hidden information and out-of-distribution worlds can make inferred objectives unreliable. | `LR-023`, `TM-22` |
| Active preference learning | Collect opt-in pairwise judgments on feasible shelter designs to compare informative queries against passive labels and fixed building criteria. | Aesthetic preference must never override legality, operator protections or safety; annotator disagreement and reward hacking require explicit tests. | `LR-024`, `TM-23` |
| [Graph networks and relational inductive biases](https://arxiv.org/abs/1806.01261) | Compare typed dynamic relations among entities, regions, items and portals with flat symbolic and voxel-attention baselines. | Building, updating and permission-filtering the graph may cost more than its relational generalization provides; unseen edges must remain unknown. | `MO-021`, `ME-017` |

These are *hypotheses*, not benchmark outcomes. Original paper/code claims,
licensing, availability, build reproducibility, locally replicated outcomes and
native-game transfer are separate evidence fields. No third-party source code,
weights or datasets are imported by this audit.

### Architecture questions that remain deliberately open

1. **State representation:** Does a compact legal native observation outperform
   pixel/vision priors after matched data, modality availability and compute?
   Re-test when versions, unknown mechanics and occlusion change.
2. **Policy decomposition:** When are one generalist, dynamic specialists,
   recurrent policies, world models or neuro-symbolic planners preferable?
   Compare equal information access and memory/VRAM ceilings, not just equal
   parameter count.
3. **Inference:** Evaluate caching, constrained action proposals, routing and
   draft verification independently before combining them. Measure p99
   decisions and game MSPT/TPS, failover and identity isolation.
4. **Construction:** Maintain separate scores for specification correctness,
   geometry/blueprint quality, material acquisition, *legal world placement*,
   verification and recovery. A plausible image or plan is not a built house.
5. **Learning:** Compare parameter updates with retrieval, memory, simple
   scripted controls and offline training under held-out seeds, safety checks,
   consent, replay and rollback. Negative results are useful research outcomes.

See the generated [research matrix](RESEARCH_MATRIX.md),
[model/training matrix](MODEL_TRAINING_MATRIX.md) and
[evaluation protocol](EVALUATION.md) for the individual gates and metadata.

## Research gaps specific to this project

1. A native observation/action representation that is rich enough to learn from while preserving ordinary-player information limits.
2. Broad behavioural pretraining aligned to structured state rather than pixels alone.
3. Long-horizon autonomy not reducible to a prompted curriculum or fixed reward list.
4. Auditable memory with contradiction, provenance, forgetting, spatial change, and causal behavioural effects.
5. Personality represented through persistent decision tendencies rather than text descriptions.
6. One grounded language/action system that supports human and AI peers without becoming a detached chatbot.
7. Continual adaptation that retains competence and privacy over very long worlds.
8. Shared inference for many agents with strict personal-state isolation.
9. Evaluations that distinguish learned behaviour, scripts, privileged state, memorised seeds, and presentation effects.

## Reference hygiene

Before depending on code, weights, or data, verify the exact repository revision, license, Minecraft version, transitive assets, and collection terms. Record additions here with a primary paper or official repository and a concise statement of demonstrated evidence and limitations.

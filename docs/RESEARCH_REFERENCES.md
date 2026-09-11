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

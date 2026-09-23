# Evaluation framework and scenario contract

Status: binding v0.1 evaluation contract for issue #28.

## Purpose

The evaluation framework defines the minimum information required to make a
Minecraft intelligence experiment comparable, inspectable, and reproducible
without depending on one model, mod loader, programming language, or runner.

The contract is intentionally separate from the executable experiment runner.
Issue #46 owns the reproducible runner and artifact execution layer. This
document defines what that runner must consume and produce.

## Core rule

A result is not an evaluation result unless the scenario and result manifests
make it possible to determine:

- what question or hypothesis was tested;
- what baseline or comparison was used;
- which exact environment/configuration was run;
- which seeds and repetitions were executed;
- which observations/actions/capabilities were available;
- which privileged information, scripts, heuristics, or operator interventions
  were present;
- what metrics and stop criteria were declared before the run;
- what failures, timeouts, negative results, and inconclusive trials occurred;
- which raw artifacts support the summary; and
- which source/code/data/model revisions produced the result.

A successful-looking video, cherry-picked episode, or aggregate score without
these records is not sufficient evidence.

## Versioned artifacts

The v1 contract consists of:

- `docs/evaluation/scenario.schema.json` — scenario definition;
- `docs/evaluation/result.schema.json` — immutable run/result manifest;
- `docs/evaluation/example-scenario.json` — synthetic contract example; and
- `docs/evaluation/example-result.json` — synthetic failure-preservation
  example.

The schemas use JSON Schema Draft 2020-12 and are language-neutral.

A future runner may use YAML/TOML or generated language types as an authoring
surface, but the canonical persisted interchange artifact must validate against
the versioned schema or a formally migrated successor.

## Scenario contract

Every scenario declares the following before execution.

### Identity and purpose

- stable scenario ID and schema version;
- human-readable title/description;
- owner/maintainer;
- evaluation class;
- construct being measured;
- research question or hypothesis; and
- explicit falsification or stop criteria.

Evaluation classes are deliberately broad:

- `unit` — narrow deterministic component/contract behavior;
- `integration` — multiple system boundaries;
- `simulation` — controlled Minecraft scenario;
- `statistical` — repeated stochastic capability comparison;
- `security` — adversarial or isolation behavior; and
- `longitudinal` — persistent behavior across long horizons/restarts.

Issue #29 owns the later benchmark taxonomy and anti-shortcut governance. These
classes are execution/test tiers, not a claim that the benchmark construct is
already valid.

### Environment

The scenario identifies or constrains:

- Minecraft version;
- mod/runtime protocol/schema versions where applicable;
- world source and world/content hash when a fixed artifact is used;
- world-generation seed(s);
- game mode/difficulty and material server rules relevant to the result;
- required mods/plugins/datapacks/resource packs;
- hardware constraints when they are part of the construct;
- data/model/checkpoint/config references; and
- code revision policy.

The result manifest records the exact resolved values used for a run.

### Participants and identities

The scenario declares:

- number and role of AI agents;
- whether human participants are present;
- agent initialization/reset semantics;
- persistent-state reuse versus clean identity creation;
- permitted shared state;
- prohibited cross-agent state; and
- any operator role.

Persistent-life experiments must state exactly which state survives between
episodes/restarts.

### Capabilities and information access

The scenario declares all permitted input/output classes and any exceptional
capabilities.

Privileged information is any input not legitimately available to the tested
agent under the baseline information-access policy, including hidden server
state, unseen chunks/entities, direct ground-truth labels, future outcomes,
other agents' private state, or evaluator-only state.

Every privileged input must be listed with:

- name;
- reason;
- consumers;
- whether it is available to the tested policy or evaluator only; and
- whether the scenario remains valid as a baseline capability claim.

An undeclared privileged input invalidates the baseline claim.

### Scripted and heuristic scaffolding

Every script, hardcoded rule, oracle, authored plan, task-specific heuristic, or
external intervention that can influence behavior must be declared.

Each scaffolding record states:

- identifier and type;
- what behavior it controls or influences;
- when it is active;
- whether it is part of the policy, environment, evaluator, or recovery path;
- whether it directly encodes task solution information; and
- how its contribution is separated or ablated.

A deterministic harness used only to set up/reset a world is still declared,
but it is not counted as learned behavior.

### Trial plan

The scenario fixes:

- exact seed list or immutable seed-set reference;
- repetitions per seed;
- warm-up policy;
- reset/restart policy;
- timeout in game ticks and/or wall time;
- allowed retries;
- intervention policy; and
- order/randomization policy.

Retries never overwrite failed attempts. Every attempt receives a unique trial
record.

### Metrics

Every metric declares:

- stable metric ID;
- definition;
- unit;
- direction (`higher`, `lower`, or `neutral`);
- aggregation method;
- whether it is primary, secondary, diagnostic, or guardrail;
- required raw source/artifact;
- treatment of failures/timeouts; and
- any threshold used for a predeclared decision.

Metrics must not silently drop unsuccessful trials from denominators.

### Baselines

A comparative scenario declares one or more baseline/configuration references,
for example:

- random/no-op policy;
- fixed heuristic;
- previous checkpoint;
- ablation;
- current candidate;
- human reference where appropriately consented.

The scenario does not encode a preferred winner. It records comparable
configurations and metrics.

### Artifacts

The scenario predeclares required artifacts such as:

- resolved scenario/configuration;
- raw event/trace output;
- action/outcome logs;
- metric inputs;
- stdout/stderr or structured diagnostics;
- environment manifest;
- model/checkpoint manifest;
- data manifest;
- failure/crash information; and
- summary/result manifest.

Human/private data artifacts remain subject to `DATA_GOVERNANCE.md`.

## Result contract

A result manifest is immutable once published for a run. Corrections create a
new result manifest that references the superseded result.

Every result records:

- scenario ID and content hash;
- result/run ID;
- source-code revision;
- exact resolved environment/software/model/data versions;
- hardware identity sufficient to interpret performance results;
- start/end timestamps;
- all trial attempts;
- actual seeds/repetition indices;
- per-trial status;
- per-trial metric values;
- failures/timeouts/errors;
- interventions and deviations;
- actual privileged-input use;
- actual scripted/heuristic scaffolding use;
- raw artifact identifiers and hashes;
- aggregate summaries with sample count and variance information; and
- final interpretation state.

Allowed interpretation states are:

- `supports_hypothesis`;
- `does_not_support_hypothesis`;
- `inconclusive`; and
- `not_applicable`.

These states describe evidence relative to the declared hypothesis. They are not
automatic architecture decisions.

## Failure preservation

Failures are data.

The runner and result format must preserve:

- setup failures;
- crashes;
- protocol/schema errors;
- timeouts;
- invalid actions;
- corrupted or missing artifacts;
- operator aborts;
- policy/evaluator exceptions;
- world-reset failures;
- resource exhaustion; and
- statistical trials that complete with poor outcomes.

A failed trial must not disappear because a retry later succeeds.

The result manifest may summarize a run as `error`, `partial`,
`completed`, or `cancelled`, but the raw trial records remain.

## Variance and repeated trials

For stochastic evaluations:

- preserve every raw trial result;
- report `n` for every aggregate;
- report at least one dispersion measure when `n > 1`;
- declare the aggregation method before the run;
- do not substitute a best episode for the distribution;
- do not average away failures unless the metric definition explicitly assigns
  their outcome; and
- separate across-seed and within-seed repetition when meaningful.

The contract supports summary statistics, but raw trial-level values are the
evidence source.

## Reset and replay semantics

Each scenario declares one reset mode:

- `clean_world` — regenerate/reload the declared initial world;
- `snapshot_restore` — restore an immutable world snapshot;
- `persistent_world` — intentionally continue the same world; or
- `custom` — fully documented procedure.

For persistent-world scenarios, the scenario must declare which state is
allowed to carry over and how order effects are handled.

Replay may be:

- deterministic re-execution;
- event/trace replay without Minecraft simulation; or
- unsupported.

Unsupported replay is permitted only when raw artifacts and environment state
still permit result inspection.

## Scenario immutability

Once a scenario version has produced externally referenced results, changing
material semantics requires a new scenario version.

Material changes include:

- metric definition;
- information access;
- seeds/splits;
- reset semantics;
- timeout;
- task setup;
- participant roles;
- scaffolding;
- success criteria; or
- baseline configuration.

Editorial descriptions may change without changing semantics, but the persisted
scenario content hash always identifies the exact executed file.

## Artifact identifiers and hashes

Every persisted artifact referenced by a result uses:

- stable artifact ID;
- artifact kind;
- path/URI or approved storage locator;
- SHA-256 content hash when the artifact is immutable/file-like;
- size where available; and
- privacy/release classification.

Git commit IDs are used for source revisions where applicable. Mutable branch
names are not sufficient provenance.

## CI and execution strategy

Issue #52 owns the concrete GitHub Actions implementation. The evaluation
contract defines the intended tiers so CI does not become the research loop.

### Pull requests

Fast, deterministic checks only:

- JSON/schema syntax;
- example/fixture schema validation;
- contract compatibility tests;
- deterministic unit tests for metric/reset helpers once implemented; and
- very small synthetic smoke scenarios where runtime cost is bounded.

PR checks must not launch expensive model training or long Minecraft studies.

### Main/nightly

Run bounded deterministic integration scenarios and selected regression seeds
when implementation exists. Preserve failure artifacts.

### Scheduled/manual research runs

Statistical, multi-seed, GPU-heavy, long-horizon, social, or ecological studies
run through the reproducible experiment framework (#46), not as an automatic
reaction to ordinary commits.

GitHub Actions is a final validation/orchestration layer, not the iterative
experiment debugger.

## Contract tests required from the runner

The runner introduced by #46 must prove at least:

1. a valid scenario executes or is resolved without schema loss;
2. an invalid/missing required field fails before execution;
3. resolved seeds and versions are persisted;
4. failed trials remain in the result after retries;
5. timeouts are explicit;
6. raw artifact hashes are recorded;
7. privileged inputs and scaffolding are copied from declared configuration and
   actual usage is reportable;
8. one agent/trial cannot overwrite another's records;
9. interrupted runs can retain partial diagnostics; and
10. result summaries can be recomputed from trial-level data.

## Example fixtures

The example files are **synthetic fixtures**, not benchmark evidence.

`example-scenario.json` demonstrates a deterministic integration scenario with
a declared evaluator-only privileged input and a scripted world-reset harness.

`example-result.json` demonstrates how a failed/timeout trial remains visible
rather than being replaced by a successful retry. Its values are illustrative
schema fixtures only and must never be cited as project performance.

## Relationship to other issues

This framework intentionally does not absorb downstream work:

- #29 defines benchmark taxonomy, confounds, generalisation splits, and
  anti-shortcut governance.
- #46 implements the reproducible experiment runner and environment capture.
- #49 defines privacy-aware cross-system trace semantics.
- #50 builds performance profiling.
- #51 defines repository-wide test architecture and quality gates.
- #52 implements stack-aware CI.
- subsystem-specific evaluation issues define their actual constructs and
  scenario suites.

The shared contract prevents each later workstream from inventing incompatible
result formats.

## Adoption checklist

A new evaluation is ready to run only when:

- [ ] scenario validates against the current schema;
- [ ] question/hypothesis and falsification criteria are explicit;
- [ ] exact seeds/repetitions are fixed or immutably referenced;
- [ ] environment/model/data/code versions are resolvable;
- [ ] information-access and privileged inputs are declared;
- [ ] scripted/heuristic scaffolding is declared;
- [ ] baselines/configurations are explicit;
- [ ] metrics include failure/timeout treatment;
- [ ] reset and intervention policy are explicit;
- [ ] required raw artifacts are declared;
- [ ] data/privacy restrictions are satisfied; and
- [ ] runner output will preserve failed and inconclusive attempts.

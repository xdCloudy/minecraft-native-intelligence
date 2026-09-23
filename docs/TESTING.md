# Test architecture and quality gates

Status: repository-wide testing policy for issue #51.

## Purpose

This document defines how the mixed Minecraft/research stack is tested without
forcing one language, framework, model runtime, or deployment topology.

The policy separates cheap deterministic checks from expensive stochastic and
longitudinal evaluation. GitHub Actions is a verification layer, not the normal
debugging loop.

## Principles

1. Test the narrowest meaningful boundary first.
2. Reproduce deterministic failures locally before pushing.
3. Preserve failed attempts and diagnostics.
4. Keep schema/contract compatibility explicit.
5. Treat nondeterminism as part of the test design, not an excuse for flaky
   assertions.
6. Never use privileged Minecraft state in a baseline test unless the test
   explicitly verifies evaluator-only behavior.
7. Use synthetic fixtures by default for privacy/security-sensitive paths.
8. Do not weaken meaningful coverage to reduce CI usage.
9. Expensive statistical or longitudinal studies do not run on every PR.
10. A green build is not evidence of intelligence capability unless an
    evaluation scenario/result contract supports that claim.

## Test tiers

### T0 — Static and format checks

Purpose:

- formatting;
- linting;
- schema/JSON syntax;
- documentation links;
- import/compile checks;
- generated-file consistency; and
- secret/license hygiene where tooling exists.

Properties:

- deterministic;
- no Minecraft launch;
- no network dependency where practical;
- no model download;
- suitable for every relevant PR.

Examples:

- Markdown lint/link validation;
- Python byte-compilation;
- JSON fixture parsing;
- Java formatter/static checks once Java code exists.

### T1 — Unit tests

Purpose:

- pure functions;
- state transitions;
- validation rules;
- serialization helpers;
- metric calculations;
- queue/budget logic; and
- deterministic policy-independent behavior.

Properties:

- deterministic;
- isolated from network/GPU/Minecraft where possible;
- fast enough for local edit/test loops.

A T1 failure must be reproducible without rerunning CI.

### T2 — Contract and compatibility tests

Purpose:

- observation/action schemas;
- runtime protocol messages;
- persistence formats;
- dataset/evaluation/experiment manifests;
- version negotiation;
- backward/forward compatibility; and
- ownership/isolation contracts.

Properties:

- language-neutral fixtures where possible;
- golden fixtures are immutable/versioned;
- old/new compatibility expectations are explicit.

Contract tests are required whenever a persisted or cross-process format changes.

### T3 — Component integration tests

Purpose:

- Java mod ↔ runtime bridge;
- runtime ↔ memory/persistence;
- persistence migrations;
- process startup/shutdown;
- reconnect/backpressure;
- diagnostics/trace propagation; and
- multi-component failure handling.

Properties:

- may launch multiple local processes;
- no external service unless specifically scoped;
- fault injection is expected;
- bounded runtime.

### T4 — Minecraft simulation/conformance tests

Purpose:

- player-compatible embodiment;
- Survival parity;
- observation information limits;
- legal action execution;
- death/respawn;
- integrated vs dedicated server behavior;
- mod compatibility; and
- deterministic scenario mechanics.

Use the loader's accepted game-test/headless facilities once implementation
exists.

T4 tests may use evaluator-only ground truth for assertions, but that state must
never enter the tested policy input.

### T5 — Statistical capability/regression tests

Purpose:

- stochastic policies;
- learned behavior;
- model/checkpoint comparisons;
- seed generalisation;
- memory retrieval quality;
- performance distributions; and
- behavior regressions.

Requirements:

- versioned evaluation scenario;
- predeclared seed/repetition plan;
- trial-level result preservation;
- variance/dispersion reporting;
- explicit failure treatment; and
- no cherry-picked retries.

T5 is normally scheduled/manual, not required PR CI.

### T6 — Security, privacy, isolation, and adversarial tests

Purpose:

- path traversal;
- unsafe artifact loading;
- malformed protocol/schema input;
- cross-agent leakage;
- unauthorized operator actions;
- hostile chat/book/sign/world input;
- resource exhaustion;
- redaction/privacy controls; and
- consent/deletion enforcement.

T6 includes both deterministic PR tests and heavier scheduled adversarial suites.

A security-sensitive change must identify which T6 cases protect its boundary.

### T7 — Longitudinal and soak tests

Purpose:

- long-running worlds;
- restart/recovery;
- persistence drift;
- memory consolidation;
- resource leaks;
- many-agent fairness;
- checkpoint promotion/rollback; and
- social/ecological behavior over time.

T7 is scheduled/manual only unless a tiny deterministic reproduction is created.

Results use the evaluation and experiment artifact contracts.

## Subsystem-to-tier map

| Subsystem | Minimum routine tiers | Later/heavier tiers |
| --- | --- | --- |
| Documentation/policy | T0 | — |
| JSON/schema contracts | T0, T1, T2 | T6 where hostile input matters |
| Minecraft integration/embodiment | T1, T2, T3, T4 | T6, T7 |
| Observation/action interface | T1, T2, T4 | T5, T6 |
| Runtime transport/scheduler | T1, T2, T3 | T5, T6, T7 |
| Identity/persistence | T1, T2, T3 | T6, T7 |
| Memory systems | T1, T2, T3 | T5, T6, T7 |
| Model/inference adapters | T1, T2, T3 | T5, T6 |
| Training/continual learning | T0, T1, T2 | T5, T6, T7 |
| Language/social systems | T1, T2, T3 | T5, T6, T7 |
| Evaluation/experiment tooling | T0, T1, T2, T3 | T5 |
| Data/privacy tooling | T1, T2, T3, T6 | T7 |
| Packaging/service management | T1, T2, T3 | T4, T6, T7 |
| Performance/scaling | T1, T3 | T5, T7 |

The map defines minimum coverage categories, not specific test frameworks.

## Quality gates

### Pull request required gate

Every PR runs only checks relevant to its changed paths, but a code PR should
normally satisfy:

- T0 static/format/schema checks;
- targeted T1 tests;
- affected T2 contract fixtures;
- bounded T3/T4 smoke tests when the changed boundary cannot be validated below
  that level; and
- relevant deterministic T6 checks for security/privacy-sensitive code.

PR checks should be deterministic and designed to finish quickly enough for
normal review. The current target is an aggregate required-check budget of
approximately 10 minutes on normal hosted runners once implementation CI exists.

That is an engineering budget target, not a performance claim.

### Main/nightly gate

Nightly/scheduled verification may add:

- broader T3/T4 combinations;
- compatibility matrices;
- rotating deterministic seeds;
- selected T5 regression suites;
- heavier T6 fault/adversarial checks; and
- bounded soak subsets.

### Manual/research gate

Run manually or on dedicated scheduled infrastructure:

- full statistical studies;
- GPU/model-heavy benchmarks;
- large population scaling;
- long-horizon autonomy;
- social/ecological studies;
- extensive fuzzing; and
- multi-hour/day T7 soak tests.

These runs use `docs/EVALUATION.md` and `docs/EXPERIMENTS.md`.

## Local-first validation

Before the first push of a coherent change:

1. run formatter/linter for the touched stack;
2. run targeted unit tests;
3. run affected contract tests;
4. run the narrowest meaningful integration/simulation smoke;
5. inspect the diff;
6. run the repository's documented pre-PR command set; and
7. push once the branch is ready for remote verification.

Do not use GitHub Actions to discover trivial syntax/import/format failures.

## Nondeterminism policy

### Deterministic tests

T0–T4 tests are deterministic unless the test explicitly declares otherwise.

A deterministic test that intermittently fails is a bug.

Do not solve it by adding blind CI retries.

Investigate:

- timing/race conditions;
- leaked shared state;
- test order;
- filesystem/process cleanup;
- uncontrolled randomness;
- external dependency;
- resource exhaustion; or
- incorrect timeout.

A temporary quarantine requires an issue, owner, evidence, and removal
condition.

### Stochastic/statistical tests

T5/T7 evaluations do not become deterministic by fixing one seed.

They require:

- declared seed set;
- declared repetitions;
- exact raw trial preservation;
- predeclared metrics;
- failure/timeout treatment;
- variance/uncertainty reporting; and
- threshold/comparison rules defined before the run.

One rerun must not erase a poor trial.

## Seed policy

Use seeds according to test purpose.

### PR seeds

For a deterministic or bounded stochastic smoke:

- use a small fixed sentinel seed set;
- keep it versioned with the test;
- do not rotate seeds silently.

### Nightly seeds

Use:

- fixed sentinel seeds for regression continuity; plus
- a recorded rotating/expanded set for broader coverage.

A newly discovered failure seed becomes a regression fixture when it exposes a
deterministic bug.

### Research seeds

The evaluation scenario is authoritative. Never choose or remove seeds after
seeing outcomes without recording a new scenario/version and explaining why.

## Fixture policy

Fixtures must be:

- minimal;
- versioned;
- attributable/provenanced;
- deterministic where expected;
- free of secrets;
- synthetic unless real data is essential; and
- small enough for the tier using them.

Human/private fixtures require data-governance approval and must not be placed
in public Git history by default.

## Contract fixture conventions

Contract fixtures live near the owning contract or in an eventual common fixture
directory chosen by #52/#51 follow-up implementation.

Use pairs such as:

```text
valid/
  v1-minimal.json
  v1-full.json

invalid/
  missing-required-field.json
  wrong-owner.json

compat/
  v1-reader-v2-additive.json
```

Each fixture needs a short expectation:

- should parse/validate;
- should fail with a stable error class; or
- should preserve specific unknown/compatibility data.

Do not use generated random blobs as the only contract coverage.

## Naming conventions

Test names should identify:

```text
<component>__<behavior>__<condition>
```

Examples:

```text
runtime_bridge__rejects_action__old_session_epoch
identity_store__round_trips__restart
observation_adapter__hides_entity__occluded
experiment_runner__preserves_attempt__retry_after_failure
```

Scenario IDs remain lower-case stable identifiers, for example:

```text
embodiment.damage-parity.v1
runtime.reconnect-idempotency.v1
memory.contradiction-revision.v1
```

Avoid names like `test1`, `works`, or `happy_path` without the behavior
being protected.

## Test ownership

Every test belongs to the subsystem whose contract it protects.

Cross-boundary tests identify one primary owner and list dependencies.

When a contract changes, the contract owner is responsible for:

- updating valid/invalid fixtures;
- updating compatibility expectations;
- documenting migration;
- coordinating downstream test changes; and
- preventing silent breakage.

## Timeouts

Every test that waits on:

- process;
- network;
- Minecraft/server state;
- model runtime;
- queue;
- lock; or
- external service

must have an explicit timeout.

Timeouts should fail with diagnostics, not hang until the CI platform kills the
job.

Do not increase a timeout to hide a deterministic deadlock/race without root
cause evidence.

## Retry policy

Automatic retries are allowed only when the test semantics require attempts or a
credible transient infrastructure condition is identified.

Rules:

- deterministic test failure: no blind retry;
- research trial retry: preserve the failed attempt;
- transient service/download failure: one bounded retry may be reasonable when
  documented;
- rerunning an entire failed CI workflow is not the default debugging method.

## Artifact retention

### PR artifacts

Retain only what is needed to diagnose failure:

- failing logs;
- small traces;
- test reports;
- screenshots when relevant;
- contract mismatch details.

Do not upload model checkpoints, datasets, full worlds, or private player data
from routine PR checks.

### Scheduled/research artifacts

Use the experiment/data artifact policies and include:

- source/config/scenario versions;
- raw trial outputs;
- result manifest;
- failure diagnostics;
- hashes/provenance; and
- declared retention/release classification.

## Failure diagnostics

A useful failure reports:

- protected behavior;
- expected state;
- observed state;
- seed/trial ID when relevant;
- component/version;
- stable error code where appropriate; and
- artifact/trace reference.

Avoid assertions that produce only `false != true` when the underlying state
can be reported safely.

## Flake accounting

A flaky test is tracked as debt.

Required metadata:

- issue;
- affected test;
- observed failure mode;
- estimated frequency from evidence;
- owner;
- quarantine/mitigation;
- exit condition.

Do not permanently exclude a flaky test without replacing its coverage.

## Coverage philosophy

Line/branch coverage can identify untested code, but no universal percentage is
a project capability gate.

Prioritize:

- security boundaries;
- persistence/migration;
- identity isolation;
- legal actions;
- information access;
- protocol compatibility;
- error/recovery paths; and
- research-result integrity.

A high percentage with weak behavioral assertions is insufficient.

## Adoption checklist

A new subsystem is test-ready when:

- [ ] owner and public contracts are identified;
- [ ] deterministic unit boundaries are covered;
- [ ] versioned/persisted interfaces have contract fixtures;
- [ ] integration boundaries have success and failure-path tests;
- [ ] timeouts exist for waits;
- [ ] randomness/seeds are controlled and recorded;
- [ ] private data is absent or explicitly governed;
- [ ] fault/security cases are identified;
- [ ] expensive evaluations are separated from PR gates;
- [ ] failure artifacts are useful and bounded;
- [ ] local pre-PR commands are documented; and
- [ ] CI paths can target relevant checks without running unrelated expensive
      work.

## Current repository application

At the v0.1 state:

- documentation checks are T0;
- evaluation JSON fixtures are T2 contract fixtures;
- experiment runner smoke behavior is a T1/T3 tooling check;
- no Minecraft T4 suite exists yet;
- no capability T5 result is implied;
- later #52 should add only the cheap Python/schema smoke required for current
  code, leaving Minecraft/model-heavy work for later milestones.

This prevents CI architecture from getting ahead of implemented stacks.

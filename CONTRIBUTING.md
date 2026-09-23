# Contributing

This project welcomes research, design, documentation, evaluation, tooling, and—when milestones reach it—implementation contributions. It is early-stage: discuss large architectural work in an issue before investing heavily.

## Before starting

Read [`docs/GOAL.md`](docs/GOAL.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`ROADMAP.md`](ROADMAP.md), and [`AGENTS.md`](AGENTS.md). Select or open a scoped issue with a milestone, area, type, and priority. Research work should state its question, evidence plan, expected artifact, and decision it can unblock.

## Finding and choosing work

Use [ROADMAP.md](ROADMAP.md) to identify the current milestone, then prefer an
issue labelled `status:ready`.

Before starting:

- read the full issue and discussion;
- confirm listed dependencies/blockers are actually resolved;
- check for an existing pull request covering the same work;
- prefer `good first issue` for a small first contribution;
- use `help wanted` when maintainers have explicitly invited focused help; and
- do not convert a blocked later-milestone item into current work merely because
  it is easier or more interesting.

Choose the issue form that matches the work:

| Work | Issue form |
| --- | --- |
| Reproducible defect | Bug report |
| Material interface/technology/ADR decision | Architecture or design proposal |
| Hypothesis with an implementation/evaluation run | Experiment |
| Scoped engineering capability | Feature proposal |
| Decision-oriented investigation | Research task |
| Security vulnerability | Private security advisory, never a public issue |

Research/experiment work should follow
[RESEARCH.md](RESEARCH.md), [docs/EVALUATION.md](docs/EVALUATION.md), and
[docs/EXPERIMENTS.md](docs/EXPERIMENTS.md). Any human or third-party data also
uses [docs/DATA_GOVERNANCE.md](docs/DATA_GOVERNANCE.md).

## Changes

1. Keep a branch focused on one issue or cohesive decision.
2. Add tests for schemas and behaviour; make experiments reproducible.
3. Follow [`docs/TESTING.md`](docs/TESTING.md): run the narrowest relevant local checks first, preserve failed attempts, and keep expensive statistical/longitudinal work out of ordinary PR CI.
4. Use the ecosystem's standard formatter/linter once a stack exists.
5. Update docs and `docs/DECISIONS.md` when contracts or architecture change.
6. Submit the pull-request template completely, including learned-versus-scripted and data/privacy sections.

## Before opening a pull request

1. Run the relevant local checks from [docs/CI.md](docs/CI.md).
2. Follow the tier/seed/flake policy in [docs/TESTING.md](docs/TESTING.md).
3. Inspect the final diff for unrelated changes and generated noise.
4. Update documentation/ADRs when a contract or material decision changed.
5. State anything that could not be validated and why.
6. Complete every relevant section of the pull-request template.

Capability claims need rerunnable evidence and limitations. Negative results are valuable. Do not include player chat/telemetry without consent and provenance, or third-party assets without license review.

## Research artifacts

Record environment and game versions, seeds, configuration, code revision, dataset/checkpoint identity, hardware, metrics, evaluation episodes, variance, failures, and exact commands. Large datasets and weights should use approved artifact storage with checksums and licenses rather than ordinary Git history.

## Community conduct and security

Follow the [Code of Conduct](CODE_OF_CONDUCT.md). Report vulnerabilities through the private process in [SECURITY.md](SECURITY.md), not a public issue.

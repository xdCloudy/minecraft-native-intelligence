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

### Progress data is part of the change

For every meaningful feature or research PR, update the canonical dataset at
[`docs/progress/progress.json`](docs/progress/progress.json) with evidence-backed
status changes, stable IDs, acceptance criteria, limitations, remaining work,
history, dependencies and milestone mappings. Keep research, experimental
outcome, implementation, validation and production readiness independent.
Update affected architecture and training candidates when relevant. Do not
credit work on an open branch as integrated on main. Generate the dashboard and
matrices; do not edit their generated Markdown by hand.

Before submitting, run:

```sh
python tools/progress.py validate
python tools/progress.py generate
python tools/progress.py check
python tools/check_doc_links.py
python -m unittest discover -s tests -p 'test_*.py'
```

See [`docs/PROGRESS_WORKFLOW.md`](docs/PROGRESS_WORKFLOW.md) for scoring,
status definitions and evidence rules.

For game-mechanic changes, use the generated
[`Minecraft competency matrix`](docs/MINECRAFT_COMPETENCY_MATRIX.md) and
[`coverage protocol`](docs/COMPETENCY_COVERAGE.md). Add independent
scenario/failure-boundary gates when aggregated capabilities conceal missing
mechanics. Model/data hypotheses are not in-game capability evidence.

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

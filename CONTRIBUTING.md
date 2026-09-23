# Contributing

This project welcomes research, design, documentation, evaluation, tooling, and—when milestones reach it—implementation contributions. It is early-stage: discuss large architectural work in an issue before investing heavily.

## Before starting

Read [`docs/GOAL.md`](docs/GOAL.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`ROADMAP.md`](ROADMAP.md), and [`AGENTS.md`](AGENTS.md). Select or open a scoped issue with a milestone, area, type, and priority. Research work should state its question, evidence plan, expected artifact, and decision it can unblock.

## Changes

1. Keep a branch focused on one issue or cohesive decision.
2. Add tests for schemas and behaviour; make experiments reproducible.
3. Follow [`docs/TESTING.md`](docs/TESTING.md): run the narrowest relevant local checks first, preserve failed attempts, and keep expensive statistical/longitudinal work out of ordinary PR CI.
4. Use the ecosystem's standard formatter/linter once a stack exists.
5. Update docs and `docs/DECISIONS.md` when contracts or architecture change.
5. Submit the pull-request template completely, including learned-versus-scripted and data/privacy sections.

Capability claims need rerunnable evidence and limitations. Negative results are valuable. Do not include player chat/telemetry without consent and provenance, or third-party assets without license review.

## Research artifacts

Record environment and game versions, seeds, configuration, code revision, dataset/checkpoint identity, hardware, metrics, evaluation episodes, variance, failures, and exact commands. Large datasets and weights should use approved artifact storage with checksums and licenses rather than ordinary Git history.

## Community conduct and security

Follow the [Code of Conduct](CODE_OF_CONDUCT.md). Report vulnerabilities through the private process in [SECURITY.md](SECURITY.md), not a public issue.

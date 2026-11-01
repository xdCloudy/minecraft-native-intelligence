# GitHub engineering backlog and critical path

The [GitHub Issues backlog](https://github.com/xdCloudy/minecraft-native-intelligence/issues)
turns the canonical research/engineering inventory into executable packages.
It is an **execution plan**, not evidence that any Minecraft-native AI capability
has been implemented.

## Sources of truth

- [`progress/progress.json`](progress/progress.json) owns stable requirement IDs,
  research/implementation/validation statuses, evidence and roadmap membership.
- [GitHub Issues](https://github.com/xdCloudy/minecraft-native-intelligence/issues)
  owns execution state, discussion, PR links, reviewers and acceptance decisions.
- [`backlog/groups.tsv`](backlog/groups.tsv) assigns each canonical ID to exactly
  one issue-sized execution package. It is a *coverage plan*, not a competing
  progress tracker.
- [`backlog/prerequisites.tsv`](backlog/prerequisites.tsv) adds package-level
  engineering gates not expressed by individual canonical item dependencies.
- [`tools/backlog.py`](../tools/backlog.py) validates complete one-to-one item
  assignment, expands requirements into a package dependency DAG, detects
  cycles, reads live issues and computes an execution queue without writing.

Existing issue numbers #1–#111 retain historical discussions. Their earlier
administrative closure must not be interpreted as delivery of any matrix item.
The new backlog uses unique hidden `mni-backlog-group:` markers so repeated
audits can find and update issues rather than duplicate them.

## How to pick work

From a local checkout:

```sh
python tools/backlog.py
python tools/backlog.py --live
python tools/backlog.py --live --json
```

Without `--live`, the tool validates the planned matrix-to-group mapping and
dependency graph only. It does **not** imply issues have been published.
`--live` queries all current GitHub issues (read-only). A GitHub token in
`GITHUB_TOKEN` or `GH_TOKEN` is optional for public reads but recommended
to avoid anonymous API rate limits. Do not put tokens in repository files.

The output reports actual mapped-item coverage and a ranked **ready queue**.
Ranking combines declared P0–P3 priority and downstream weighted unlock impact.
This is a dependency-unblocking heuristic, not a mathematical critical-path
duration estimate: task durations, variance and team capacity have not been
measured. Reassess when estimates and evidence become available.

An issue is eligible for the ready queue only if it is open, its linked
prerequisite packages have **verified** acceptance, and declared milestone
gates have been satisfied. Ordinary issue closure does not release dependencies.
For an accepted completed package, reviewers must record linked test/artifact
evidence and the exact marker `<!-- mni-acceptance-verified:GROUP_KEY -->`
before its closed state can unblock successors. The marker does not change
canonical research or implementation status.

Issue labels are hints that may be stale. For the current execution frontier,
the calculated queue takes precedence over static `status:ready` labels.

## Development loop

1. Run the live audit and choose the highest-impact *actually ready* package.
2. Confirm no active PR/agent owns conflicting files or architectural decisions.
3. Read its linked canonical IDs, acceptance criteria, negatives and dependencies.
4. Implement or perform the bounded research; record test results and failures.
5. Link the PR, revision, experiment/data provenance and acceptance evidence.
6. Review acceptance independently. Close only when the scoped issue is truly
   complete; record the verified marker separately from capability evidence.
7. Update relevant canonical tracker statuses **only if evidence warrants it**,
   regenerate matrices, and rerun the live issue audit.
8. Pick newly unlocked work, or document an unresolved blocker with an
   actionable investigation and adjust prerequisites with a reviewable PR.

Do not turn a dependency into a hard blocker merely because it is conceptually
related: prerequisites should prevent technically invalid parallel work, not
serialize independent research. Cycles are an error and fail the validator.

## Automation and maintenance

The [read-only backlog audit workflow](../.github/workflows/backlog-audit.yml)
runs on relevant issue events, a periodic schedule and manual invocation.
It publishes a JSON queue/coverage report as an artifact; it does not silently
rewrite labels, close issues or promote implementation progress.

When adding a requirement, update the canonical tracker and place its stable ID
in the appropriate package or propose a new one. When splitting packages,
preserve their history and stable GitHub references. Run:

```sh
python tools/backlog.py
python tools/progress.py validate
python tools/progress.py check
python tools/check_doc_links.py
python -m unittest discover -s tests -p 'test_*.py'
```

The live audit must ultimately report 100% published package coverage,
accurate issue references, and no dependency cycles. This **issue coverage**
is separate from research completion, demonstrated gameplay capability,
implementation maturity, validation and production readiness.

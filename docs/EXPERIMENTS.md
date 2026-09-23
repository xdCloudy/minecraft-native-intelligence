# Reproducible experiment framework

Status: v0.1 reference experiment framework for issue #46.

## Purpose

This framework turns a versioned evaluation scenario into reproducible execution
artifacts without selecting the project's future model, training, or agent
runtime stack.

The canonical contracts are JSON. The Python runner in `scripts/` is a
replaceable reference implementation, not a core architecture dependency.

## Requirements

A clean-machine smoke run requires:

- Git;
- Python 3.11 or newer;
- a clean checkout of the repository; and
- no third-party Python packages.

The reference runner uses only the Python standard library.

## Files

- `scripts/run_experiment.py` — executes scenario seed/repetition matrices.
- `scripts/compare_experiment_runs.py` — compares immutable run provenance and
  final trial statuses without ranking experimental variants.
- `docs/experiments/experiment.schema.json` — experiment execution manifest.
- `docs/experiments/run.schema.json` — produced run manifest.
- `docs/experiments/artifacts.schema.json` — produced artifact inventory.
- `experiments/smoke/experiment.json` — deterministic synthetic smoke
  experiment.
- `experiments/smoke/trial_fixture.py` — deterministic synthetic trial command.

Evaluation semantics remain in [EVALUATION.md](EVALUATION.md) and
`docs/evaluation/`.

## Experiment manifest

An experiment manifest declares:

- stable experiment ID;
- evaluation scenario path;
- whether a dirty source tree may run;
- explicit environment variables safe to capture;
- one or more execution variants;
- executable and argument list for each variant;
- variant environment/configuration; and
- optional fallback wall timeout.

The manifest never stores secrets. If a command requires credentials, the
credential mechanism is outside the manifest and must comply with the security
and data-governance policies.

### Python executable token

A variant may use:

```json
"executable": "{python}"
```

The runner substitutes the interpreter that launched
`scripts/run_experiment.py`. The persisted run record keeps the portable token,
not the machine's absolute interpreter path.

## Scenario-driven trial matrix

The runner reads the referenced `eval.scenario.v1` scenario and executes:

```text
variant
  × seed
  × repetition
  × attempt (initial + allowed retries)
```

The scenario remains authoritative for:

- seed list;
- repetitions per seed;
- retry count; and
- wall timeout when one is declared.

A retry creates a new attempt record. It never overwrites the failed attempt.

## Trial environment

Each trial process receives:

- `MNI_VARIANT_ID`;
- `MNI_SEED`;
- `MNI_REPETITION_INDEX`;
- `MNI_ATTEMPT`;
- `MNI_TRIAL_ID`; and
- `MNI_TRIAL_DIR`.

Trial programs should write all generated files beneath `MNI_TRIAL_DIR`.
The runner hashes every file in that directory.

## Source immutability

By default the runner refuses to execute from a dirty Git working tree.

This prevents a run from claiming an immutable source revision while using
uncommitted code.

For local development only:

```bash
python scripts/run_experiment.py \
  --manifest experiments/smoke/experiment.json \
  --allow-dirty
```

A dirty run is marked `publishable: false`.

Published evidence must use a clean exact commit.

## Run directory

Default output goes under the ignored `.mni-runs/` directory:

```text
.mni-runs/<run-id>/
├── experiment.json
├── scenario.json
├── run.json
├── artifacts.json
└── trials/
    └── <trial-id>/
        ├── stdout.log
        ├── stderr.log
        └── ... trial-generated artifacts
```

`experiment.json` and `scenario.json` are copies of the exact executed
inputs.

`run.json` is updated atomically after every attempt so partial progress and
failures survive an interrupted later trial.

`artifacts.json` contains SHA-256 and size for immutable run files other than
the self-referential run/artifact manifests.

## Failure preservation

Attempt status is one of:

- `completed`;
- `failed` — process launched but returned a non-zero exit code;
- `timeout` — wall timeout expired; or
- `error` — process could not be launched.

The run summary keeps both:

- attempt-level counts; and
- the final status of each logical variant/seed/repetition trial.

If an attempt fails and a retry succeeds, both records remain in `run.json`.

A run is:

- `completed` when every logical trial finishes successfully;
- `partial` when some logical trials finish and others do not;
- `error` when none finish; or
- `cancelled` after an operator interruption.

## Logging and artifacts

Stdout and stderr are always captured separately for every attempt.

The runner records:

- exact Git commit and clean/dirty state;
- experiment/scenario hashes;
- Python version;
- OS/platform/machine metadata;
- explicitly allowlisted environment variables;
- command token/arguments;
- relative working directory;
- timestamps/duration;
- timeout;
- exit code or launch error; and
- per-trial artifact hashes.

It deliberately does not persist:

- absolute Python interpreter path;
- repository/host absolute paths;
- dirty-file names;
- arbitrary environment variables; or
- secret values not explicitly placed in an allowlist.

## Environment capture

The experiment manifest contains an explicit environment-variable allowlist.

Use it only for non-secret reproducibility metadata such as a CI indicator.
Do not add tokens, passwords, cloud credentials, home directories, or other
machine-private values.

Model/GPU/framework versions should later be recorded through explicit
experiment/model manifests rather than dumping the host environment wholesale.

## Comparison

Compare two run manifests with:

```bash
python scripts/compare_experiment_runs.py \
  .mni-runs/<left>/run.json \
  .mni-runs/<right>/run.json
```

The comparator reports:

- whether experiment manifests match;
- whether scenarios match;
- source-revision change;
- captured environment differences;
- run-summary differences; and
- logical trial final-status changes.

It intentionally does **not** rank variants or interpret capability metrics.
Metric interpretation belongs to the evaluation result contract and the
predeclared hypothesis.

## Smoke experiment

From a clean checkout:

```bash
python scripts/run_experiment.py \
  --manifest experiments/smoke/experiment.json
```

The smoke fixture is intentionally synthetic:

- seed `101` succeeds on its first attempt;
- seed `202` exits non-zero on attempt 0;
- seed `202` succeeds on its allowed retry.

The expected run status is `completed`, while `run.json` still contains all
three attempt records.

This verifies failure preservation without making a Minecraft intelligence
capability claim.

## Reproducing a research experiment

A publishable experiment should record or reference:

1. a committed experiment manifest;
2. a committed evaluation scenario;
3. exact data/model/checkpoint manifests;
4. exact source commit;
5. hardware/software configuration relevant to interpretation;
6. raw trial artifacts;
7. generated `run.json` and `artifacts.json`; and
8. an `eval.result.v1` result built from those raw trial artifacts.

The evaluation result is the scientific evidence surface. The experiment run
manifest is the execution/provenance surface.

## Interrupted runs

The runner writes `run.json` after each attempt.

On Ctrl+C it:

- marks the run `cancelled`;
- preserves completed attempt records;
- writes the artifact inventory available at that point; and
- exits with code 130.

A future resume feature must create an explicit continuation relationship rather
than silently editing prior trial history.

## Security boundary

Experiment manifests are trusted developer/research inputs and may execute
programs. Do not run an untrusted manifest.

The reference runner additionally:

- confines manifest/scenario/working-directory paths to the repository root;
- defaults outputs to a repository-local ignored directory;
- avoids broad environment capture;
- records portable command metadata rather than host paths; and
- does not weaken the runtime/Minecraft action security boundary.

Experiment commands themselves remain responsible for their own sandboxing and
resource limits.

## Data and privacy

Human/private artifacts remain governed by
[DATA_GOVERNANCE.md](DATA_GOVERNANCE.md).

Do not place sensitive raw data in the Git repository or in public CI artifacts.

Run directories are local evidence stores by default. Upload/retention policy is
a separate explicit decision.

## CI strategy

Issue #52 owns concrete stack-aware GitHub Actions changes.

When that work adopts this runner, the cheap PR smoke should be:

```bash
python -m py_compile \
  scripts/run_experiment.py \
  scripts/compare_experiment_runs.py \
  experiments/smoke/trial_fixture.py

python scripts/run_experiment.py \
  --manifest experiments/smoke/experiment.json
```

That smoke is deterministic and does not launch Minecraft, download models, or
train anything.

Long-running/statistical experiments remain scheduled/manual research work, not
ordinary PR CI.

## Extension rules

Do not add runner features merely because a particular model stack wants them.

Extend the framework when the capability is broadly required for reproducible
experiments and can remain independent of one model/runtime.

Material changes to the persisted schemas require a schema version change and
compatibility/migration consideration.

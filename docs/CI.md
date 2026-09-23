# Continuous integration

The repository uses one stack-aware GitHub Actions workflow:
`.github/workflows/ci.yml`.

## Goals

CI should:

- verify committed work rather than act as the edit/debug loop;
- run only checks relevant to changed stacks;
- use least-privilege permissions;
- pin third-party actions to reviewed commit SHAs;
- cancel superseded runs for the same PR/ref;
- keep ordinary PR checks deterministic and cheap; and
- retain only bounded diagnostics when a failure benefits from artifacts.

## Change routing

The workflow always starts a small change-detection job so required workflow
checks are not left pending by workflow-level path filters.

It then conditionally runs:

| Changed path | Job |
| --- | --- |
| `*.md`, `.markdownlint.yml` | Documentation |
| `*.py`, `*.json`, `pyproject.toml`, `requirements*.txt`, `.gitignore` | Python and JSON tooling |
| `*.ps1` | PowerShell syntax |
| `.github/workflows/ci.yml` | All current stack checks |

A skipped conditional job is expected for an unrelated stack.

## Documentation checks

Remote checks:

- markdownlint;
- link validation with lychee.

Equivalent local commands, when those tools are installed:

```bash
markdownlint-cli2 "**/*.md"
lychee --no-progress --exclude-path LICENSE --accept 200,429 "**/*.md"
```

The repository does not add Node/Rust package management solely to install these
documentation tools locally.

## Python and JSON checks

The local and CI entrypoint is:

```bash
python scripts/ci_smoke.py
```

It performs:

- byte-compilation of current Python tooling;
- JSON parsing under `docs/` and `experiments/`;
- information-access rule/reference/conformance integrity;
- observation schema/field-registry/compatibility validation;
- the deterministic experiment-runner smoke;
- failure/retry preservation assertions;
- artifact hash checks;
- experiment self-comparison; and
- the dirty-working-tree refusal test.

CI runs this on Python 3.11, the minimum supported reference-runner version.

No dependency cache is configured because the current Python tooling is
standard-library only and installs no packages. Add caching only when a real,
pinned dependency installation exists and measurements show it saves work.

## PowerShell checks

PowerShell changes are parsed with PowerShell's own AST parser on the hosted
runner.

A local equivalent is:

```powershell
$failed = $false
Get-ChildItem -Path . -Recurse -Filter *.ps1 | ForEach-Object {
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $_.FullName,
        [ref]$tokens,
        [ref]$errors
    ) | Out-Null

    foreach ($error in $errors) {
        Write-Error "$($_.FullName):$($error.Extent.StartLineNumber): $($error.Message)"
        $failed = $true
    }
}

if ($failed) { exit 1 }
```

No PowerShell modules are installed solely for CI at this stage.

## Action pinning

Third-party actions use full commit SHAs with the reviewed major tag recorded in
a comment.

When updating an action:

1. inspect the upstream release/tag;
2. resolve the tag to its commit SHA;
3. review material release changes;
4. update the SHA/comment together; and
5. let the workflow change trigger all current stack checks.

Do not use floating `@main` references.

## Concurrency

The workflow cancels an older in-progress run when a newer commit arrives for
the same PR/ref.

This prevents obsolete commits from consuming workflow capacity.

## Failure artifacts

The Python job uploads `.ci-artifacts/` only when the job fails.

Retention is three days.

The directory contains synthetic smoke-run diagnostics only; it must not become
a path for datasets, checkpoints, full worlds, or human/private data.

Documentation and PowerShell syntax failures are expected to be diagnosable
from job logs and do not upload artifacts.

## Permissions

Workflow permissions are:

```yaml
permissions:
  contents: read
```

No workflow job receives write permission.

Future publishing/release workflows must be separate and grant only the
permissions they require.

## What does not belong in PR CI

Ordinary PR CI must not automatically:

- download model weights;
- train/fine-tune models;
- run statistical capability studies;
- run large Minecraft populations;
- execute long soaks;
- upload research datasets;
- publish releases; or
- call external services merely to validate deterministic local behavior.

Those belong to scheduled/manual research or later release workflows.

## Adding a stack

When a new implementation stack is accepted:

1. define its local formatter/linter/type/test commands;
2. map it to `docs/TESTING.md` tiers;
3. add change detection for its files;
4. add only deterministic bounded PR checks;
5. pin tool/action versions;
6. cache only real repeatable dependency work;
7. define bounded failure artifacts; and
8. validate locally before opening the CI PR.

The workflow should grow from implemented needs, not hypothetical future stacks.

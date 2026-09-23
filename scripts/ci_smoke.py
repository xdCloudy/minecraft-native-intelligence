#!/usr/bin/env python3
"""Cheap deterministic CI smoke for the currently accepted Python tooling."""
from __future__ import annotations

import json
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / ".ci-artifacts"
PYTHON_FILES = [
    ROOT / "scripts" / "run_experiment.py",
    ROOT / "scripts" / "compare_experiment_runs.py",
    ROOT / "scripts" / "ci_smoke.py",
    ROOT / "scripts" / "validate_information_access.py",
    ROOT / "scripts" / "validate_observation_contract.py",
    ROOT / "experiments" / "smoke" / "trial_fixture.py",
]


def check_python() -> None:
    for path in PYTHON_FILES:
        py_compile.compile(str(path), doraise=True)


def check_json() -> int:
    count = 0
    for base in [ROOT / "docs", ROOT / "experiments"]:
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.json")):
            with path.open("r", encoding="utf-8") as f:
                json.load(f)
            count += 1
    return count


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def check_information_access() -> None:
    run([sys.executable, "scripts/validate_information_access.py"])


def check_observation_contract() -> None:
    run([sys.executable, "scripts/validate_observation_contract.py"])


def check_smoke() -> Path:
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    ARTIFACT_ROOT.mkdir(parents=True)
    cp = run([
        sys.executable,
        "scripts/run_experiment.py",
        "--manifest",
        "experiments/smoke/experiment.json",
        "--output-root",
        str(ARTIFACT_ROOT),
    ])
    run_dir = Path(cp.stdout.strip().splitlines()[-1])
    run_manifest = run_dir / "run.json"
    data = json.loads(run_manifest.read_text(encoding="utf-8"))
    expected = [(101, 0, "completed"), (202, 0, "failed"), (202, 1, "completed")]
    actual = [(t["seed"], t["attempt"], t["status"]) for t in data["trials"]]
    if data["status"] != "completed" or actual != expected:
        raise AssertionError(f"unexpected smoke result: status={data['status']!r}, trials={actual!r}")
    if data["source_revision"]["dirty"]:
        raise AssertionError("clean CI smoke unexpectedly recorded a dirty source tree")
    if "python_executable" in data["environment"] or "dirty_entries" in data["source_revision"]:
        raise AssertionError("run manifest leaked local path/file-name provenance")
    artifacts = json.loads((run_dir / "artifacts.json").read_text(encoding="utf-8"))
    if not artifacts.get("files"):
        raise AssertionError("artifact manifest is empty")
    for item in artifacts["files"]:
        if len(item.get("sha256", "")) != 64:
            raise AssertionError(f"invalid artifact hash entry: {item!r}")
    cmp = run([sys.executable, "scripts/compare_experiment_runs.py", str(run_manifest), str(run_manifest)])
    comparison = json.loads(cmp.stdout)
    if not comparison["same_experiment_manifest"] or comparison["logical_trial_status_changes"]:
        raise AssertionError(f"self-comparison failed: {comparison!r}")
    (ARTIFACT_ROOT / "self-comparison.json").write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return run_dir


def check_dirty_refusal() -> None:
    probe = ROOT / ".ci-dirty-probe.tmp"
    probe.write_text("dirty probe\n", encoding="utf-8")
    try:
        cp = run([
            sys.executable,
            "scripts/run_experiment.py",
            "--manifest",
            "experiments/smoke/experiment.json",
            "--output-root",
            str(ARTIFACT_ROOT / "dirty-probe"),
        ], check=False)
        if cp.returncode != 2 or "repository is dirty" not in cp.stderr:
            raise AssertionError(f"dirty-tree guard failed: code={cp.returncode}, stderr={cp.stderr!r}")
    finally:
        probe.unlink(missing_ok=True)


def main() -> int:
    check_python()
    json_count = check_json()
    check_information_access()
    check_observation_contract()
    run_dir = check_smoke()
    check_dirty_refusal()
    print(f"python compile: ok ({len(PYTHON_FILES)} files)")
    print(f"json parse: ok ({json_count} files)")
    print("information-access contract: ok")
    print("observation contract: ok")
    print(f"experiment smoke: ok ({run_dir.name})")
    print("dirty-tree refusal: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

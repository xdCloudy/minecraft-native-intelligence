#!/usr/bin/env python3
"""Minimal reproducible experiment runner for Minecraft Native Intelligence.

Standard-library only. The canonical experiment/evaluation contracts remain JSON,
not Python APIs. This runner is a replaceable reference implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUN_SCHEMA_VERSION = "experiment.run.v1"
MANIFEST_SCHEMA_VERSION = "experiment.v1"
SCENARIO_SCHEMA_VERSION = "eval.scenario.v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def resolve_inside(base: Path, candidate: str | Path, label: str) -> Path:
    path = (base / candidate).resolve() if not Path(candidate).is_absolute() else Path(candidate).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} must stay inside repository root: {candidate}") from exc
    return path


def git_capture(repo_root: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return cp.stdout.strip()


def git_info(repo_root: Path) -> dict[str, Any]:
    commit = git_capture(repo_root, "rev-parse", "HEAD")
    dirty_text = git_capture(repo_root, "status", "--porcelain=v1", "--untracked-files=normal")
    return {
        "vcs": "git",
        "commit": commit,
        "dirty": bool(dirty_text),
        "dirty_entry_count": len(dirty_text.splitlines()),
    }


def require_keys(obj: dict[str, Any], keys: list[str], label: str) -> None:
    missing = [key for key in keys if key not in obj]
    if missing:
        raise ValueError(f"{label} missing required keys: {', '.join(missing)}")


def validate_manifest(manifest: dict[str, Any]) -> None:
    require_keys(
        manifest,
        ["schema_version", "experiment_id", "scenario_path", "variants", "environment_capture"],
        "experiment manifest",
    )
    if manifest["schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise ValueError(f"unsupported experiment schema: {manifest['schema_version']!r}")
    if not isinstance(manifest["variants"], list) or not manifest["variants"]:
        raise ValueError("experiment manifest variants must be a non-empty list")
    ids: set[str] = set()
    for variant in manifest["variants"]:
        if not isinstance(variant, dict):
            raise ValueError("each variant must be an object")
        require_keys(variant, ["id", "executable", "arguments", "environment"], "variant")
        if variant["id"] in ids:
            raise ValueError(f"duplicate variant id: {variant['id']}")
        ids.add(variant["id"])
        if not isinstance(variant["arguments"], list) or not all(isinstance(x, str) for x in variant["arguments"]):
            raise ValueError(f"variant {variant['id']} arguments must be a list of strings")
        if not isinstance(variant["environment"], dict):
            raise ValueError(f"variant {variant['id']} environment must be an object")


def validate_scenario(scenario: dict[str, Any]) -> None:
    require_keys(scenario, ["schema_version", "scenario_id", "trial_plan"], "scenario")
    if scenario["schema_version"] != SCENARIO_SCHEMA_VERSION:
        raise ValueError(f"unsupported scenario schema: {scenario['schema_version']!r}")
    trial = scenario["trial_plan"]
    if not isinstance(trial, dict):
        raise ValueError("scenario trial_plan must be an object")
    require_keys(trial, ["seeds", "repetitions_per_seed", "allowed_retries", "timeout"], "scenario trial_plan")
    if not isinstance(trial["seeds"], list) or not trial["seeds"]:
        raise ValueError("scenario trial_plan.seeds must be a non-empty list")
    if not isinstance(trial["repetitions_per_seed"], int) or trial["repetitions_per_seed"] < 1:
        raise ValueError("scenario repetitions_per_seed must be >= 1")
    if not isinstance(trial["allowed_retries"], int) or trial["allowed_retries"] < 0:
        raise ValueError("scenario allowed_retries must be >= 0")


def resolve_executable(value: str) -> str:
    if value == "{python}":
        return sys.executable
    return value


def wall_timeout_seconds(manifest: dict[str, Any], scenario: dict[str, Any]) -> float:
    timeout = scenario.get("trial_plan", {}).get("timeout", {})
    wall = timeout.get("wall_seconds") if isinstance(timeout, dict) else None
    if isinstance(wall, (int, float)) and wall > 0:
        return float(wall)
    fallback = manifest.get("default_wall_timeout_seconds")
    if isinstance(fallback, (int, float)) and fallback > 0:
        return float(fallback)
    raise ValueError("scenario must declare wall_seconds or experiment must set default_wall_timeout_seconds")


def collect_files(root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not root.exists():
        return items
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        items.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return items


def run_attempt(
    *,
    repo_root: Path,
    run_dir: Path,
    variant: dict[str, Any],
    seed: int | str,
    repetition_index: int,
    attempt: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    variant_id = str(variant["id"])
    trial_id = f"{variant_id}--seed-{seed}--r{repetition_index}--a{attempt}"
    safe_trial = trial_id.replace("/", "_").replace("\\", "_").replace(":", "_")
    trial_dir = run_dir / "trials" / safe_trial
    trial_dir.mkdir(parents=True, exist_ok=False)

    cwd = resolve_inside(repo_root, variant.get("working_directory", "."), f"variant {variant_id} working_directory")
    executable = resolve_executable(str(variant["executable"]))
    arguments = [str(arg) for arg in variant["arguments"]]
    command = [executable, *arguments]

    env = os.environ.copy()
    env.update({str(k): str(v) for k, v in variant.get("environment", {}).items()})
    env.update(
        {
            "MNI_VARIANT_ID": variant_id,
            "MNI_SEED": str(seed),
            "MNI_REPETITION_INDEX": str(repetition_index),
            "MNI_ATTEMPT": str(attempt),
            "MNI_TRIAL_ID": trial_id,
            "MNI_TRIAL_DIR": str(trial_dir),
        }
    )

    stdout_path = trial_dir / "stdout.log"
    stderr_path = trial_dir / "stderr.log"
    started_at = utc_now()
    t0 = time.monotonic()
    timed_out = False
    exit_code: int | None = None
    launch_error: str | None = None

    try:
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=stdout_file, stderr=stderr_file)
            try:
                exit_code = proc.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.terminate()
                try:
                    exit_code = proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    exit_code = proc.wait()
    except OSError as exc:
        launch_error = f"{type(exc).__name__}: {exc}"

    duration = time.monotonic() - t0
    ended_at = utc_now()
    if launch_error is not None:
        status = "error"
    elif timed_out:
        status = "timeout"
    elif exit_code == 0:
        status = "completed"
    else:
        status = "failed"

    return {
        "trial_id": trial_id,
        "variant_id": variant_id,
        "seed": seed,
        "repetition_index": repetition_index,
        "attempt": attempt,
        "status": status,
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_seconds": round(duration, 6),
        "timeout_seconds": timeout_seconds,
        "command": {"executable": str(variant["executable"]), "arguments": arguments},
        "working_directory": cwd.relative_to(repo_root).as_posix() or ".",
        "exit_code": exit_code,
        "launch_error": launch_error,
        "artifacts": collect_files(trial_dir),
    }


def summarize_trials(trials: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    final: dict[tuple[str, str, int], str] = {}
    for trial in trials:
        status = str(trial["status"])
        counts[status] = counts.get(status, 0) + 1
        key = (str(trial["variant_id"]), str(trial["seed"]), int(trial["repetition_index"]))
        final[key] = status
    final_counts: dict[str, int] = {}
    for status in final.values():
        final_counts[status] = final_counts.get(status, 0) + 1
    return {"attempt_status_counts": counts, "final_trial_status_counts": final_counts, "logical_trial_count": len(final)}


def capture_environment(manifest: dict[str, Any]) -> dict[str, Any]:
    capture = manifest.get("environment_capture", {})
    env_names = capture.get("environment_variables", []) if isinstance(capture, dict) else []
    if not isinstance(env_names, list):
        raise ValueError("environment_capture.environment_variables must be a list")
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "environment_variables": {name: os.environ.get(name) for name in env_names},
    }


def build_artifact_manifest(run_dir: Path) -> dict[str, Any]:
    excluded = {"run.json", "artifacts.json"}
    files = []
    for path in sorted(p for p in run_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(run_dir).as_posix()
        if rel in excluded:
            continue
        files.append({"path": rel, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return {"schema_version": "experiment.artifacts.v1", "files": files}


def final_run_status(trials: list[dict[str, Any]], expected_logical_trials: int) -> str:
    summary = summarize_trials(trials)
    final_counts = summary["final_trial_status_counts"]
    completed = final_counts.get("completed", 0)
    if completed == expected_logical_trials:
        return "completed"
    if completed > 0:
        return "partial"
    return "error"


def run_experiment(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(git_capture(Path.cwd(), "rev-parse", "--show-toplevel")).resolve()
    manifest_path = resolve_inside(repo_root, args.manifest, "manifest")
    manifest = load_json(manifest_path)
    validate_manifest(manifest)

    scenario_path = resolve_inside(repo_root, manifest["scenario_path"], "scenario_path")
    scenario = load_json(scenario_path)
    validate_scenario(scenario)

    source = git_info(repo_root)
    allow_dirty = bool(manifest.get("allow_dirty", False) or args.allow_dirty)
    if source["dirty"] and not allow_dirty:
        raise RuntimeError("repository is dirty; commit/stash changes or pass --allow-dirty for a non-publishable development run")

    manifest_bytes = manifest_path.read_bytes()
    scenario_bytes = scenario_path.read_bytes()
    manifest_hash = sha256_bytes(manifest_bytes)
    scenario_hash = sha256_bytes(scenario_bytes)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{manifest['experiment_id']}:{timestamp}:{manifest_hash[:10]}"

    output_root = resolve_inside(repo_root, args.output_root, "output_root") if not Path(args.output_root).is_absolute() else Path(args.output_root).resolve()
    run_dir = output_root / run_id.replace(":", "_")
    if run_dir.exists():
        raise FileExistsError(f"run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True)

    shutil.copy2(manifest_path, run_dir / "experiment.json")
    shutil.copy2(scenario_path, run_dir / "scenario.json")

    trial_plan = scenario["trial_plan"]
    seeds = list(trial_plan["seeds"])
    repetitions = int(trial_plan["repetitions_per_seed"])
    retries = int(trial_plan["allowed_retries"])
    timeout_seconds = wall_timeout_seconds(manifest, scenario)
    expected = len(manifest["variants"]) * len(seeds) * repetitions

    run_record: dict[str, Any] = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "experiment_id": manifest["experiment_id"],
        "experiment_manifest_sha256": manifest_hash,
        "scenario": {"scenario_id": scenario["scenario_id"], "sha256": scenario_hash},
        "source_revision": source,
        "publishable": not source["dirty"],
        "environment": capture_environment(manifest),
        "started_at": utc_now(),
        "ended_at": None,
        "status": "running",
        "expected_logical_trials": expected,
        "variants": [variant["id"] for variant in manifest["variants"]],
        "trials": [],
        "summary": {"attempt_status_counts": {}, "final_trial_status_counts": {}, "logical_trial_count": 0},
        "artifact_manifest": "artifacts.json",
        "notes": manifest.get("notes", ""),
    }
    atomic_write_json(run_dir / "run.json", run_record)

    try:
        for variant in manifest["variants"]:
            for seed in seeds:
                for repetition_index in range(repetitions):
                    for attempt in range(retries + 1):
                        trial = run_attempt(
                            repo_root=repo_root,
                            run_dir=run_dir,
                            variant=variant,
                            seed=seed,
                            repetition_index=repetition_index,
                            attempt=attempt,
                            timeout_seconds=timeout_seconds,
                        )
                        run_record["trials"].append(trial)
                        run_record["summary"] = summarize_trials(run_record["trials"])
                        atomic_write_json(run_dir / "run.json", run_record)
                        if trial["status"] == "completed":
                            break
    except KeyboardInterrupt:
        run_record["status"] = "cancelled"
        run_record["ended_at"] = utc_now()
        run_record["summary"] = summarize_trials(run_record["trials"])
        atomic_write_json(run_dir / "run.json", run_record)
        atomic_write_json(run_dir / "artifacts.json", build_artifact_manifest(run_dir))
        print(run_dir)
        return 130

    run_record["status"] = final_run_status(run_record["trials"], expected)
    run_record["ended_at"] = utc_now()
    run_record["summary"] = summarize_trials(run_record["trials"])
    atomic_write_json(run_dir / "artifacts.json", build_artifact_manifest(run_dir))
    atomic_write_json(run_dir / "run.json", run_record)
    print(run_dir)
    return 0 if run_record["status"] == "completed" else 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Experiment manifest path relative to repository root")
    parser.add_argument("--repo-root", help="Repository root; defaults to git rev-parse --show-toplevel")
    parser.add_argument("--output-root", default=".mni-runs", help="Run output directory, relative to repository root by default")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow a dirty source tree; run is marked non-publishable")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        return run_experiment(parse_args(argv))
    except (ValueError, RuntimeError, FileNotFoundError, FileExistsError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

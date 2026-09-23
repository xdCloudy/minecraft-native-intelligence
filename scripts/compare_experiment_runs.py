#!/usr/bin/env python3
"""Compare two immutable experiment run manifests without ranking variants."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_SCHEMA = "experiment.run.v1"


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict) or value.get("schema_version") != EXPECTED_SCHEMA:
        raise ValueError(f"{path} is not an {EXPECTED_SCHEMA} manifest")
    return value


def final_trials(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for trial in run.get("trials", []):
        key = f"{trial['variant_id']}|{trial['seed']}|{trial['repetition_index']}"
        result[key] = trial
    return result


def dict_diff(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    keys = sorted(set(a) | set(b))
    changed: dict[str, Any] = {}
    for key in keys:
        av = a.get(key)
        bv = b.get(key)
        if av != bv:
            changed[key] = {"left": av, "right": bv}
    return changed


def compare(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    af = final_trials(a)
    bf = final_trials(b)
    keys = sorted(set(af) | set(bf))
    trial_changes = []
    for key in keys:
        left = af.get(key)
        right = bf.get(key)
        left_status = None if left is None else left.get("status")
        right_status = None if right is None else right.get("status")
        if left_status != right_status:
            trial_changes.append({"logical_trial": key, "left_status": left_status, "right_status": right_status})
    return {
        "schema_version": "experiment.comparison.v1",
        "left_run_id": a.get("run_id"),
        "right_run_id": b.get("run_id"),
        "same_experiment_id": a.get("experiment_id") == b.get("experiment_id"),
        "same_experiment_manifest": a.get("experiment_manifest_sha256") == b.get("experiment_manifest_sha256"),
        "same_scenario": a.get("scenario") == b.get("scenario"),
        "source_revision_changed": a.get("source_revision", {}).get("commit") != b.get("source_revision", {}).get("commit"),
        "environment_changes": dict_diff(a.get("environment", {}), b.get("environment", {})),
        "summary_changes": dict_diff(a.get("summary", {}), b.get("summary", {})),
        "logical_trial_status_changes": trial_changes,
        "note": "Provenance/status comparison only; this tool does not rank experimental variants or interpret capability metrics."
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("left")
    p.add_argument("right")
    p.add_argument("--output")
    args = p.parse_args(argv)
    try:
        result = compare(load(Path(args.left)), load(Path(args.right)))
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

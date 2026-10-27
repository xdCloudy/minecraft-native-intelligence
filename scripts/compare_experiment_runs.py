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


def trial_histories(run: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Index every attempt deterministically; never discard failed retries."""
    histories: dict[str, dict[int, dict[str, Any]]] = {}
    identities: dict[str, tuple[Any, Any, Any]] = {}
    trials = run.get("trials", [])
    if not isinstance(trials, list):
        raise ValueError("trials must be a list")
    for trial in trials:
        if not isinstance(trial, dict):
            raise ValueError("trial must be an object")
        key = f"{trial['variant_id']}|{trial['seed']}|{trial['repetition_index']}"
        identity = (trial["variant_id"], trial["seed"], trial["repetition_index"])
        if key in identities and identities[key] != identity:
            raise ValueError(f"ambiguous logical trial key: {key}")
        identities[key] = identity
        attempt = trial["attempt"]
        if type(attempt) is not int or attempt < 0:
            raise ValueError(f"{key}: attempt must be a nonnegative integer")
        attempts = histories.setdefault(key, {})
        if attempt in attempts:
            raise ValueError(f"{key}: duplicate attempt {attempt}")
        attempts[attempt] = trial

    ordered: dict[str, list[dict[str, Any]]] = {}
    for key, attempts in histories.items():
        indices = sorted(attempts)
        if indices != list(range(indices[-1] + 1)):
            raise ValueError(f"{key}: missing attempt in retry history {indices}")
        history = [attempts[index] for index in indices]
        if any(item.get("status") == "completed" for item in history[:-1]):
            raise ValueError(f"{key}: retry after a completed attempt")
        ordered[key] = history
    return ordered


def final_trials(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {key: history[-1] for key, history in trial_histories(run).items()}


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
    ah = trial_histories(a)
    bh = trial_histories(b)
    af = {key: history[-1] for key, history in ah.items()}
    bf = {key: history[-1] for key, history in bh.items()}
    keys = sorted(set(af) | set(bf))
    trial_changes = []
    for key in keys:
        left = af.get(key)
        right = bf.get(key)
        left_status = None if left is None else left.get("status")
        right_status = None if right is None else right.get("status")
        if left_status != right_status:
            trial_changes.append({"logical_trial": key, "left_status": left_status, "right_status": right_status})
    histories_changed = []
    for key in keys:
        left = [{"attempt": t["attempt"], "status": t.get("status")} for t in ah.get(key, [])]
        right = [{"attempt": t["attempt"], "status": t.get("status")} for t in bh.get(key, [])]
        if left != right:
            histories_changed.append({"logical_trial": key, "left_attempts": left, "right_attempts": right})
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
        "logical_trial_attempt_history_changes": histories_changed,
        "note": "Provenance/status/retry history comparison only; this tool does not rank experimental variants or interpret capability metrics."
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

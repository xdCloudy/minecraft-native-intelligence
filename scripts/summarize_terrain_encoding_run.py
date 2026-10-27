#!/usr/bin/env python3
"""Summarize raw terrain-encoding experiment artifacts without dropping trials."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path
from typing import Any


def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def quantiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"median": None, "p25": None, "p75": None}
    if len(values) == 1:
        return {"median": values[0], "p25": values[0], "p75": values[0]}
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return {"median": statistics.median(values), "p25": q1, "p75": q3}


def summarize(run_dir: Path) -> dict[str, Any]:
    run_path = run_dir / "run.json"
    run = load(run_path)
    if run.get("schema_version") != "experiment.run.v1" or run.get("status") != "completed":
        raise ValueError("run must be a completed experiment.run.v1")
    if run.get("source_revision", {}).get("dirty"):
        raise ValueError("run source revision is dirty")
    trials = run.get("trials", [])
    if len(trials) != run.get("expected_logical_trials"):
        raise ValueError("trial count does not match expected logical trial count")
    if any(trial.get("status") != "completed" or trial.get("exit_code") != 0 for trial in trials):
        raise ValueError("all trial attempts must complete successfully before comparison")

    by_variant: dict[str, list[dict[str, Any]]] = {}
    for trial in trials:
        artifact_record = next((item for item in trial.get("artifacts", []) if item.get("path") == "terrain-encoding.json"), None)
        if artifact_record is None:
            raise ValueError(f"{trial['trial_id']}: missing terrain-encoding.json artifact record")
        result_path = run_dir / "trials" / trial["trial_id"] / "terrain-encoding.json"
        content = result_path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != artifact_record.get("sha256") or len(content) != artifact_record.get("size_bytes"):
            raise ValueError(f"{trial['trial_id']}: artifact hash/size does not match run manifest")
        result = json.loads(content.decode("utf-8"))
        expected_encoder = trial["variant_id"].replace("-", "_")
        if result.get("encoder") != expected_encoder or result.get("seed") != trial["seed"]:
            raise ValueError(f"{trial['trial_id']}: artifact identity does not match trial manifest")
        by_variant.setdefault(trial["variant_id"], []).extend(result.get("cases", []))

    summaries = {}
    for variant, cases in sorted(by_variant.items()):
        applicable_errors = [case["nearest_gold_distance_error_blocks"] for case in cases
                             if case["nearest_gold_distance_error_blocks"] is not None]
        summaries[variant] = {
            "terrain_case_count": len(cases),
            "payload_bytes": quantiles([case["payload_bytes"] for case in cases]),
            "encode_median_ns": quantiles([case["encode_median_ns"] for case in cases]),
            "decode_median_ns": quantiles([case["decode_median_ns"] for case in cases]),
            "visible_sample_reconstruction_mean": statistics.mean(case["visible_sample_reconstruction"] for case in cases),
            "visible_material_count_exact_rate": statistics.mean(case["visible_material_counts_exact"] for case in cases),
            "nearest_gold_distance_error_blocks_mean": (statistics.mean(applicable_errors) if applicable_errors else None),
            "nearest_gold_applicable_cases": len(applicable_errors),
            "local_block_query_exact_rate": statistics.mean(case["local_block_query_exact"] for case in cases),
            "visible_adjacency_graph_exact_rate": statistics.mean(case["visible_adjacency_graph_exact"] for case in cases),
            "hidden_state_compliance_all": all(case["hidden_state_compliant"] for case in cases),
            "hidden_world_perturbation_independent_all": all(case["hidden_world_perturbation_independent"] for case in cases),
        }
    return {
        "format": "terrain-encoding-summary.v0",
        "run_id": run["run_id"],
        "source_commit": run["source_revision"]["commit"],
        "scenario_id": run["scenario"]["scenario_id"],
        "environment": run["environment"],
        "logical_trials": len(trials),
        "summaries": summaries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, help="write summary JSON to this path instead of stdout")
    args = parser.parse_args()
    result = summarize(args.run_dir.resolve())
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"terrain run summary failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

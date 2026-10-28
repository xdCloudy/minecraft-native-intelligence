#!/usr/bin/env python3
"""Exploratory paired binary metric audit; never infers Minecraft competence."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
from typing import Any

from scripts.validate_observation_contract import validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs" / "evaluation" / "result.schema.json"


class EvidenceError(ValueError):
    pass


def validate_run(run: Any) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = validate_json_schema(run, schema, schema)
    if errors:
        raise EvidenceError("invalid result manifest: " + "; ".join(errors[:5]))
    if run["run_status"] != "completed":
        raise EvidenceError("incomplete run is not eligible for paired analysis")
    if any(x["used_by_policy"] for x in run["actual_privileged_inputs"]):
        raise EvidenceError("privileged inputs reached the tested policy")
    if any(x["interventions"] or x["deviations"] for x in run["trials"]):
        raise EvidenceError("intervened or deviated trial cannot enter clean comparison")
    counts = Counter(x["status"] for x in run["trials"])
    if run["summary"]["trial_count"] != len(run["trials"]) or dict(counts) != run["summary"]["status_counts"]:
        raise EvidenceError("trial summary does not match raw trial history")


def paired_trials(run: dict[str, Any], metric: str) -> dict[tuple[str, int | str, int], bool]:
    result: dict[tuple[str, int | str, int], bool] = {}
    seen: dict[tuple[str, int | str, int], set[int]] = {}
    for trial in run["trials"]:
        seed = trial["seed"]
        key = (type(seed).__name__, seed, trial["repetition_index"])
        attempt = trial["attempt"]
        if attempt in seen.setdefault(key, set()):
            raise EvidenceError(f"duplicate attempt for {key!r}")
        seen[key].add(attempt)
        if attempt != 0:
            raise EvidenceError("retries require preregistered analysis and are not supported by this tool")
        if trial["status"] != "completed":
            raise EvidenceError("failed or missing trial must not be silently dropped")
        value = trial["metrics"].get(metric)
        if type(value) is not bool:
            raise EvidenceError(f"missing or non-boolean primary metric {metric!r} in {key!r}")
        result[key] = value
    if not result:
        raise EvidenceError("no trials")
    return result


def exact_mcnemar_p_value(left_only: int, right_only: int) -> float:
    """Two-sided exact binomial p-value for discordant pairs, no continuity fudge."""
    discordant = left_only + right_only
    if discordant == 0:
        return 1.0
    extreme = min(left_only, right_only)
    numerator = 2 * sum(math.comb(discordant, k) for k in range(extreme + 1))
    return min(1.0, numerator / (1 << discordant))


def compare(left: dict[str, Any], right: dict[str, Any], metric: str) -> dict[str, Any]:
    if not metric or not isinstance(metric, str):
        raise EvidenceError("metric identifier required")
    validate_run(left)
    validate_run(right)
    if left["scenario"] != right["scenario"]:
        raise EvidenceError("scenario revision/hash mismatch; not a paired comparison")
    if left["run_id"] == right["run_id"]:
        raise EvidenceError("comparison requires distinct run IDs")
    left_trials = paired_trials(left, metric)
    right_trials = paired_trials(right, metric)
    if left_trials.keys() != right_trials.keys():
        raise EvidenceError("seed/repetition coverage differs; refusing unpaired analysis")
    counts = Counter((left_trials[k], right_trials[k]) for k in left_trials)
    both = counts[(True, True)]
    left_only = counts[(True, False)]
    right_only = counts[(False, True)]
    neither = counts[(False, False)]
    n = len(left_trials)
    return {
        "schema_version": "evaluation.paired-binary.audit.v0",
        "metric_id": metric,
        "left_run_id": left["run_id"],
        "right_run_id": right["run_id"],
        "synthetic_only": left["synthetic_fixture"] or right["synthetic_fixture"],
        "paired_trial_count": n,
        "both_success": both,
        "left_only_success": left_only,
        "right_only_success": right_only,
        "neither_success": neither,
        "left_rate": (both + left_only) / n,
        "right_rate": (both + right_only) / n,
        "paired_rate_difference": (left_only - right_only) / n,
        "mcnemar_exact_two_sided_p": exact_mcnemar_p_value(left_only, right_only),
        "interpretation": "Exploratory audit only; no confidence interval, power analysis, preregistration verification or causal/competence claim.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--metric", required=True)
    args = parser.parse_args()
    try:
        result = compare(json.loads(args.left.read_text(encoding="utf-8")),
                         json.loads(args.right.read_text(encoding="utf-8")), args.metric)
    except (OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

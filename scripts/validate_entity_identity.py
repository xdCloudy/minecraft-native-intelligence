#!/usr/bin/env python3
"""Validate and run the deterministic heuristic prototype for issue #5."""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

from validate_observation_contract import ValidationError, load, validate_json_schema

ROOT = Path(__file__).resolve().parents[1]
ENTITY_ROOT = ROOT / "docs" / "entities"
SCHEMA_PATH = ENTITY_ROOT / "identity.schema.json"
CONTRACT_PATH = ENTITY_ROOT / "identity.v0.json"
INFO_RULES_PATH = ROOT / "docs" / "information_access" / "rules.v1.json"
FORBIDDEN_KEYS = {"uuid", "entity_uuid", "server_entity_id", "internal_entity_id", "evaluator_label"}


def validate_schema(value: Any, schema: dict[str, Any], label: str) -> None:
    errors = validate_json_schema(value, schema, schema)
    if errors:
        raise ValidationError(label + ":\n  - " + "\n  - ".join(errors[:25]))


def validate_fixture(value: Any, signal_ids: set[str], label: str) -> None:
    if not isinstance(value, dict) or value.get("format") != "entity-identity-fixture.v0":
        raise ValidationError(f"{label}: unsupported fixture format")
    root_keys = {"format", "case_id", "current_observation_sequence", "coverage", "previous_tracks", "current_observation_refs", "relations"}
    if set(value) - root_keys:
        raise ValidationError(f"{label}: unexpected fixture properties {sorted(set(value) - root_keys)!r}")
    if value.get("coverage") not in {"complete", "partial", "unavailable"}:
        raise ValidationError(f"{label}: invalid coverage")
    sequence = value.get("current_observation_sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        raise ValidationError(f"{label}: invalid current observation sequence")
    refs = value.get("current_observation_refs")
    if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref for ref in refs):
        raise ValidationError(f"{label}: current_observation_refs must be non-empty strings")
    if len(refs) != len(set(refs)):
        raise ValidationError(f"{label}: duplicate current observation reference")

    tracks = value.get("previous_tracks")
    if not isinstance(tracks, list):
        raise ValidationError(f"{label}: previous_tracks must be a list")
    handles: set[str] = set()
    for track in tracks:
        if not isinstance(track, dict):
            raise ValidationError(f"{label}: track entry must be an object")
        track_keys = {"handle", "observation_ref", "is_existing", "gap_windows", "signal_scores"}
        if set(track) - track_keys:
            raise ValidationError(f"{label}: unexpected track properties {sorted(set(track) - track_keys)!r}")
        handle = track.get("handle")
        if not isinstance(handle, str) or re.fullmatch(r"t[0-9]+", handle) is None:
            raise ValidationError(f"{label}: invalid opaque track handle")
        if handle in handles:
            raise ValidationError(f"{label}: duplicate track handle {handle!r}")
        handles.add(handle)
        if not isinstance(track.get("is_existing"), bool):
            raise ValidationError(f"{label}: is_existing must be boolean")
        gap = track.get("gap_windows")
        if not isinstance(gap, int) or isinstance(gap, bool) or gap < 0:
            raise ValidationError(f"{label}: gap_windows must be a non-negative integer")
        observation_ref = track.get("observation_ref")
        if observation_ref is not None and observation_ref not in refs:
            raise ValidationError(f"{label}: track refers to an unknown current observation")
        signal_scores = track.get("signal_scores")
        if not isinstance(signal_scores, dict):
            raise ValidationError(f"{label}: signal_scores must be an object")
        for signal, score in signal_scores.items():
            if signal not in signal_ids:
                raise ValidationError(f"{label}: undeclared signal {signal!r}")
            if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 1:
                raise ValidationError(f"{label}: signal score must be between 0 and 1")

    relations = value.get("relations", [])
    if not isinstance(relations, list):
        raise ValidationError(f"{label}: relations must be a list")
    for relation in relations:
        if not isinstance(relation, dict) or set(relation) != {"kind", "from", "to"}:
            raise ValidationError(f"{label}: relation must contain kind, from, and to only")
        if relation["from"] not in refs or relation["to"] not in refs:
            raise ValidationError(f"{label}: relation endpoint must reference a current observed entity")

    def reject_forbidden_keys(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key.lower() in FORBIDDEN_KEYS:
                    raise ValidationError(f"{label}: forbidden server/evaluator field {key!r}")
                reject_forbidden_keys(child)
        elif isinstance(node, list):
            for child in node:
                reject_forbidden_keys(child)

    reject_forbidden_keys(value)


def bucket_for(score: float, thresholds: dict[str, float]) -> str:
    if score >= thresholds["certain_min"]:
        return "certain"
    if score >= thresholds["strong_min"]:
        return "strong"
    if score >= thresholds["plausible_min"]:
        return "plausible"
    return "ambiguous"


def run_fixture(value: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, Any]]:
    signal_weights = {signal["id"]: signal["weight"] for signal in contract["signals"]}
    thresholds = contract["policy"]["thresholds"]
    decay = contract["policy"]["decay"]["parameter"]
    tracks = []
    seen_refs: set[str] = set()
    for candidate in value["previous_tracks"]:
        handle = candidate["handle"]
        observation_ref = candidate.get("observation_ref")
        existing = candidate["is_existing"]
        score = sum(signal_weights[name] * raw for name, raw in candidate["signal_scores"].items())
        score = max(0, round(score - (decay * candidate["gap_windows"] if existing else 0)))
        if not existing:
            state = "new"
            score = 0
        elif observation_ref is None:
            state = "not_sensed_in_scope" if value["coverage"] == "complete" else "occluded_hypothesis"
        elif observation_ref is not None and candidate["gap_windows"] > 0:
            state = "reassociated"
        else:
            state = "tracked"
        if observation_ref is not None:
            seen_refs.add(observation_ref)
        tracks.append({"handle": handle, "state": state, "bucket": bucket_for(score, thresholds), "aggregate": score})

    next_handle = 1
    for observation_ref in value["current_observation_refs"]:
        if observation_ref in seen_refs:
            continue
        while f"t{next_handle}" in {track["handle"] for track in tracks}:
            next_handle += 1
        tracks.append({"handle": f"t{next_handle}", "state": "new", "bucket": "ambiguous", "aggregate": 0})
        next_handle += 1
    return sorted(tracks, key=lambda track: track["handle"])


def assert_case(case: dict[str, Any], contract: dict[str, Any], schema: dict[str, Any], signal_ids: set[str]) -> None:
    fixture_path = (ENTITY_ROOT / contract["conformance"]["fixtures_root"] / case["fixture"]).resolve()
    fixtures_root = (ENTITY_ROOT / contract["conformance"]["fixtures_root"]).resolve()
    if fixtures_root not in fixture_path.parents:
        raise ValidationError(f"{case['id']}: fixture path escapes fixtures root")
    fixture = load(fixture_path)
    validate_fixture(fixture, signal_ids, case["fixture"])
    if fixture.get("case_id") != case["id"]:
        raise ValidationError(f"{case['id']}: fixture case_id mismatch")
    actual_tracks = run_fixture(fixture, contract)
    expected_tracks = case["expected"]["tracks"]
    if actual_tracks != expected_tracks:
        raise ValidationError(f"{case['id']}: expected tracks {expected_tracks!r}, got {actual_tracks!r}")
    if not case["expected"]["leakage_free"]:
        raise ValidationError(f"{case['id']}: conformance case must declare a leakage-free fixture")


def expect_invalid(fixture: dict[str, Any], signal_ids: set[str], label: str) -> None:
    try:
        validate_fixture(fixture, signal_ids, label)
    except ValidationError:
        return
    raise AssertionError(f"invalid identity fixture was accepted: {label}")


def main() -> int:
    schema = load(SCHEMA_PATH)
    contract = load(CONTRACT_PATH)
    validate_schema(contract, schema, "identity.v0.json")

    rules = load(INFO_RULES_PATH)
    valid_rule_ids = {rule["id"] for rule in rules["rules"]}
    signals = contract["signals"]
    signal_ids = {signal["id"] for signal in signals}
    if len(signal_ids) != len(signals):
        raise ValidationError("signal IDs must be unique")
    if sum(signal["weight"] for signal in signals) != 100:
        raise ValidationError("prototype signal weights must sum to 100")
    for signal in signals:
        unknown_rules = set(signal["access_rule_ids"]) - valid_rule_ids
        if unknown_rules:
            raise ValidationError(f"signal {signal['id']}: unknown access rules {sorted(unknown_rules)!r}")
    thresholds = contract["policy"]["thresholds"]
    ordered_thresholds = [thresholds[name] for name in ("ambiguous_min", "plausible_min", "strong_min", "certain_min")]
    if ordered_thresholds != sorted(ordered_thresholds):
        raise ValidationError("identity score thresholds must be ordered")

    edge_cases = contract["edge_cases"]
    edge_ids = [edge["id"] for edge in edge_cases]
    if len(edge_ids) != len(set(edge_ids)):
        raise ValidationError("edge-case IDs must be unique")
    required_categories = {"spawn_despawn", "occlusion", "similar_entities", "mounts_projectiles", "information_loss"}
    categories = {edge["category"] for edge in edge_cases}
    if not required_categories <= categories:
        raise ValidationError(f"missing required edge-case categories: {sorted(required_categories - categories)!r}")
    for edge in edge_cases:
        if not set(edge["signals_used"]) <= signal_ids:
            raise ValidationError(f"edge case {edge['id']}: references undeclared signals")
        for relative_path in edge["fixtures"]:
            fixture_path = (ENTITY_ROOT / contract["conformance"]["fixtures_root"] / relative_path).resolve()
            fixtures_root = (ENTITY_ROOT / contract["conformance"]["fixtures_root"]).resolve()
            if fixtures_root not in fixture_path.parents or not fixture_path.is_file():
                raise ValidationError(f"edge case {edge['id']}: missing or out-of-root fixture {relative_path!r}")

    case_ids = [case["id"] for case in contract["conformance"]["cases"]]
    if len(case_ids) != len(set(case_ids)):
        raise ValidationError("conformance case IDs must be unique")
    if any(not any(case_id.startswith(edge_id + ".case-") for edge_id in edge_ids) for case_id in case_ids):
        raise ValidationError("conformance case IDs must refer to a declared edge case")
    for case in contract["conformance"]["cases"]:
        assert_case(case, contract, schema, signal_ids)

    sample = load(ENTITY_ROOT / contract["conformance"]["fixtures_root"] / contract["conformance"]["cases"][0]["fixture"])
    invalid = copy.deepcopy(sample)
    invalid["previous_tracks"] = [{"handle": "t1", "is_existing": True, "gap_windows": 0, "signal_scores": {"server_uuid": 1}}]
    expect_invalid(invalid, signal_ids, "server UUID used as evidence")
    invalid = copy.deepcopy(sample)
    invalid["coverage"] = "unavailable"
    invalid["previous_tracks"] = [{"handle": "t1", "is_existing": True, "gap_windows": -1, "signal_scores": {}}]
    expect_invalid(invalid, signal_ids, "negative observation gap")
    invalid = copy.deepcopy(sample)
    invalid["meta"] = {"agent_id": "hidden-routing-value"}
    expect_invalid(invalid, signal_ids, "policy-hidden metadata")

    print(f"entity identity contract: ok ({len(case_ids)} conformance cases, 3 invalid fixtures rejected; heuristic prototype only)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"entity identity validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
"""Run deterministic producer/consumer protocol compatibility conformance cases."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

from validate_observation_contract import ValidationError, assert_valid, load

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_DIR = ROOT / "docs" / "protocol"
PRODUCER_SCHEMA_PATH = PROTOCOL_DIR / "producer-manifest.schema.json"
CONSUMER_SCHEMA_PATH = PROTOCOL_DIR / "consumer-policy.schema.json"
CASES_SCHEMA_PATH = PROTOCOL_DIR / "compatibility.schema.json"
PRODUCER_PATH = PROTOCOL_DIR / "producer.example.v0.json"
CONSUMER_PATH = PROTOCOL_DIR / "consumer.example.v0.json"
CASES_PATH = PROTOCOL_DIR / "compatibility.v0.json"

REQUIRED_CASES = {
    "baseline_exact_v0",
    "newer_supported_minor",
    "newer_additive_minor_degrades",
    "multiple_degradations_keep_diagnostics",
    "major_mismatch_fails_closed",
    "observation_v0_to_v1_rejected",
    "action_request_v0_to_v1_rejected",
    "action_outcome_v0_to_v1_rejected",
    "unknown_optional_capability_degrades",
    "unknown_required_capability_rejected",
    "experimental_optional_capability_degrades",
    "allowlisted_experimental_capability_degrades",
    "required_experimental_capability_rejected",
    "required_experimental_allowlisted_degrades",
    "experimental_allowlist_does_not_enable_unknown_stable",
    "unsupported_minecraft_version_rejected",
    "unsupported_java_version_rejected",
    "unsupported_loader_version_rejected",
    "unsupported_mod_version_rejected",
    "unsupported_server_mode_rejected",
}


def set_path(obj: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    node: Any = obj
    for part in parts[:-1]:
        if not isinstance(node, dict) or part not in node:
            raise ValidationError(f"compatibility mutation path does not exist: {dotted}")
        node = node[part]
    if not isinstance(node, dict) or parts[-1] not in node:
        raise ValidationError(f"compatibility mutation target does not exist: {dotted}")
    node[parts[-1]] = value


def apply_mutations(source: dict[str, Any], mutations: list[dict[str, Any]]) -> dict[str, Any]:
    result = copy.deepcopy(source)
    for mutation in mutations:
        op = mutation["op"]
        path = mutation["path"]
        if op == "set":
            set_path(result, path, mutation["value"])
            continue
        if op != "append":
            raise ValidationError(f"unsupported mutation operation: {op}")
        parts = path.split(".")
        node: Any = result
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                raise ValidationError(f"compatibility mutation path does not exist: {path}")
            node = node[part]
        if not isinstance(node, list):
            raise ValidationError(f"compatibility mutation target is not an array: {path}")
        node.append(mutation["value"])
    return result


def negotiate(producer: dict[str, Any], consumer: dict[str, Any]) -> tuple[str, str, list[str], list[str]]:
    """Return outcome, primary diagnostic, enabled capabilities, and all diagnostics."""
    p_protocol = producer["protocol"]
    if p_protocol["major"] != consumer["protocol_major"]:
        return "reject", "protocol_major_mismatch", [], ["protocol_major_mismatch"]

    env = producer["environment"]
    support = consumer["environment_support"]
    if env["minecraft_version"] not in support["minecraft_versions"]:
        return "reject", "unsupported_minecraft_version", [], ["unsupported_minecraft_version"]
    if env["java_major"] not in support["java_majors"]:
        return "reject", "unsupported_java_version", [], ["unsupported_java_version"]
    loader = next((item for item in support["loaders"] if item["id"] == env["loader_id"]), None)
    if loader is None or env["loader_version"] not in loader["versions"]:
        return "reject", "unsupported_loader_version", [], ["unsupported_loader_version"]
    mod = next((item for item in support["mods"] if item["id"] == env["mod_id"]), None)
    if mod is None or env["mod_version"] not in mod["versions"]:
        return "reject", "unsupported_mod_version", [], ["unsupported_mod_version"]
    if env["server_mode"] not in support["server_modes"]:
        return "reject", "unsupported_server_mode", [], ["unsupported_server_mode"]

    for name in ("observation", "action_request", "action_outcome"):
        if producer["schemas"][name] not in consumer["schemas"][name]:
            code = f"unsupported_{name}_schema"
            return "reject", code, [], [code]

    offered_items = producer["capabilities"]
    offered = {item["id"]: item["maturity"] for item in offered_items}
    if len(offered) != len(offered_items):
        return "reject", "duplicate_capability", [], ["duplicate_capability"]
    required = set(producer["required_capabilities"])
    if not required <= set(offered):
        return "reject", "invalid_required_capability", [], ["invalid_required_capability"]

    supported = set(consumer["capabilities"])
    experimental_allowlist = set(consumer["allowed_experimental_capabilities"])
    enabled: list[str] = []
    warnings: list[str] = []
    for capability in sorted(required):
        maturity = offered[capability]
        if maturity == "experimental" and capability not in experimental_allowlist:
            return "reject", "required_experimental_capability_not_allowed", [], ["required_experimental_capability_not_allowed"]
        if maturity == "stable" and capability not in supported:
            return "reject", "required_capability_unsupported", [], ["required_capability_unsupported"]
        if maturity == "experimental" and capability not in experimental_allowlist:
            return "reject", "required_experimental_capability_not_allowed", [], ["required_experimental_capability_not_allowed"]
        enabled.append(capability)
        if maturity == "experimental":
            warnings.append("experimental_capability_enabled")

    for capability, maturity in sorted(offered.items()):
        if capability in required:
            continue
        if maturity == "experimental":
            if capability in experimental_allowlist:
                enabled.append(capability)
                warnings.append("experimental_capability_enabled")
            else:
                warnings.append("experimental_capability_omitted")
        elif capability in supported:
            enabled.append(capability)
        else:
            warnings.append("optional_capability_unavailable")

    if p_protocol["minor"] > consumer["max_protocol_minor"]:
        warnings.append("newer_protocol_minor")
    if warnings:
        warnings = list(dict.fromkeys(warnings))
        return "degraded", warnings[0], sorted(enabled), warnings
    return "accept", "compatible", sorted(enabled), ["compatible"]


def main() -> int:
    try:
        producer_schema = load(PRODUCER_SCHEMA_PATH)
        consumer_schema = load(CONSUMER_SCHEMA_PATH)
        cases_schema = load(CASES_SCHEMA_PATH)
        producer = load(PRODUCER_PATH)
        consumer = load(CONSUMER_PATH)
        cases = load(CASES_PATH)

        assert_valid(producer, producer_schema, "producer manifest")
        assert_valid(consumer, consumer_schema, "consumer policy")
        assert_valid(cases, cases_schema, "compatibility cases")
        if cases["producer_fixture"] != PRODUCER_PATH.name or cases["consumer_fixture"] != CONSUMER_PATH.name:
            raise ValidationError("compatibility catalog references unexpected base fixtures")

        case_ids = [case["id"] for case in cases["cases"]]
        if len(case_ids) != len(set(case_ids)):
            raise ValidationError("duplicate compatibility case IDs")
        missing = sorted(REQUIRED_CASES - set(case_ids))
        if missing:
            raise ValidationError("missing required conformance cases: " + ", ".join(missing))

        for case in cases["cases"]:
            candidate_producer = apply_mutations(producer, case["producer"])
            candidate_consumer = apply_mutations(consumer, case["consumer"])
            assert_valid(candidate_producer, producer_schema, case["id"] + " producer")
            assert_valid(candidate_consumer, consumer_schema, case["id"] + " consumer")
            outcome, diagnostic, _enabled, diagnostics = negotiate(candidate_producer, candidate_consumer)
            if outcome != case["expected"] or diagnostic != case["diagnostic"]:
                raise ValidationError(
                    f"{case['id']}: expected {case['expected']}/{case['diagnostic']}, "
                    f"got {outcome}/{diagnostic}"
                )
            if "diagnostics" in case and diagnostics != case["diagnostics"]:
                raise ValidationError(f"{case['id']}: expected diagnostics {case['diagnostics']}, got {diagnostics}")
            if "enabled_capabilities" in case and _enabled != case["enabled_capabilities"]:
                raise ValidationError(
                    f"{case['id']}: expected enabled capabilities {case['enabled_capabilities']}, got {_enabled}"
                )

        print(f"protocol compatibility: ok ({len(cases['cases'])} accept/degrade/reject cases)")
        print("schema transitions: ok (observation v0→v1, action request v0→v1, action outcome v0→v1)")
        return 0
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

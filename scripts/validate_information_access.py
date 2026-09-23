#!/usr/bin/env python3
"""Validate information-access rule/catalog referential integrity."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "docs" / "information_access" / "rules.v1.json"
CONFORMANCE_PATH = ROOT / "docs" / "information_access" / "conformance.v1.json"

EXPECTED_RULE_SCHEMA = "information-access.v1"
EXPECTED_CONFORMANCE_SCHEMA = "information-access-conformance.v1"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def unique(values: list[str], label: str) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        raise ValueError(f"duplicate {label}: {', '.join(sorted(duplicates))}")
    return seen


def validate() -> None:
    rules_doc = load(RULES_PATH)
    conformance = load(CONFORMANCE_PATH)

    if rules_doc.get("schema_version") != EXPECTED_RULE_SCHEMA:
        raise ValueError(f"unexpected rule schema: {rules_doc.get('schema_version')!r}")
    if conformance.get("schema_version") != EXPECTED_CONFORMANCE_SCHEMA:
        raise ValueError(f"unexpected conformance schema: {conformance.get('schema_version')!r}")
    if rules_doc.get("profile_id") != conformance.get("profile_id"):
        raise ValueError("rule and conformance profile_id values differ")

    rules = rules_doc.get("rules")
    field_classes = rules_doc.get("field_classes")
    scenarios = conformance.get("scenarios")
    if not isinstance(rules, list) or not rules:
        raise ValueError("rules must be a non-empty list")
    if not isinstance(field_classes, list) or not field_classes:
        raise ValueError("field_classes must be a non-empty list")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("scenarios must be a non-empty list")

    rule_ids = unique([str(rule["id"]) for rule in rules], "rule IDs")
    unique([str(field["field_class"]) for field in field_classes], "field classes")
    scenario_ids = unique([str(scenario["id"]) for scenario in scenarios], "conformance scenario IDs")

    missing_refs: list[str] = []
    for field in field_classes:
        for rule_id in field.get("access_rule_ids", []):
            if rule_id not in rule_ids:
                missing_refs.append(f"field {field['field_class']} -> {rule_id}")

    for scenario in scenarios:
        for rule_id in scenario.get("rules", []):
            if rule_id not in rule_ids:
                missing_refs.append(f"scenario {scenario['id']} -> {rule_id}")

    if missing_refs:
        raise ValueError("unknown rule references: " + "; ".join(sorted(missing_refs)))

    required_scenarios = {f"IA-{n:02d}" for n in range(1, 18)}
    if scenario_ids != required_scenarios:
        missing = sorted(required_scenarios - scenario_ids)
        extra = sorted(scenario_ids - required_scenarios)
        raise ValueError(f"conformance catalog mismatch; missing={missing}, extra={extra}")

    camera = rules_doc.get("camera", {})
    if camera.get("base_horizontal_fov_degrees") != 70:
        raise ValueError("player-equivalent.v1 base horizontal FOV must remain 70 unless the profile/version changes")
    if camera.get("debug_overlay") is not False:
        raise ValueError("player-equivalent.v1 debug overlay must remain disabled")

    print(f"information-access rules: ok ({len(rule_ids)} rules)")
    print(f"information-access field classes: ok ({len(field_classes)} classes)")
    print(f"information-access conformance: ok ({len(scenario_ids)} scenarios)")


def main() -> int:
    try:
        validate()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

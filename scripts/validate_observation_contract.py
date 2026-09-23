#!/usr/bin/env python3
"""Validate observation v0 schemas, fixtures, field registry, and compatibility cases.

Uses only the Python standard library and implements the small JSON Schema
Draft 2020-12 subset used by this repository's observation contract.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OBS_DIR = ROOT / "docs" / "observations"
INFO_RULES = ROOT / "docs" / "information_access" / "rules.v1.json"

OBS_SCHEMA_PATH = OBS_DIR / "observation.schema.json"
FIELDS_SCHEMA_PATH = OBS_DIR / "fields.schema.json"
FIELDS_PATH = OBS_DIR / "fields.v0.json"
COMPAT_SCHEMA_PATH = OBS_DIR / "compatibility.schema.json"
COMPAT_PATH = OBS_DIR / "compatibility.v0.json"

FIXTURES = {
    "example-observation.v0.json": OBS_DIR / "example-observation.v0.json",
    "example-unknowns.v0.json": OBS_DIR / "example-unknowns.v0.json",
    "example-extension.v0.json": OBS_DIR / "example-extension.v0.json",
}


class ValidationError(ValueError):
    pass


def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValidationError(f"unsupported external $ref: {ref}")
    node: Any = root_schema
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        node = node[token]
    if not isinstance(node, dict):
        raise ValidationError(f"$ref does not resolve to an object: {ref}")
    return node


def type_matches(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    raise ValidationError(f"unsupported schema type: {expected}")


def validate_json_schema(value: Any, schema: dict[str, Any], root_schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []

    if "$ref" in schema:
        return validate_json_schema(value, resolve_ref(root_schema, schema["$ref"]), root_schema, path)

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {value!r}")
        return errors

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} not in enum")
        return errors

    if "type" in schema:
        expected = schema["type"]
        allowed = expected if isinstance(expected, list) else [expected]
        if not any(type_matches(value, t) for t in allowed):
            errors.append(f"{path}: expected type {allowed!r}, got {type(value).__name__}")
            return errors

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: string shorter than minLength")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            errors.append(f"{path}: string does not match {schema['pattern']!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} below minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} above maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"{path}: {value} not above exclusiveMinimum {schema['exclusiveMinimum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: more than maxItems")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in value]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{path}: duplicate array items")
        if "items" in schema:
            for i, item in enumerate(value):
                errors.extend(validate_json_schema(item, schema["items"], root_schema, f"{path}[{i}]"))

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")

        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                errors.extend(validate_json_schema(item, properties[key], root_schema, f"{path}.{key}"))
            elif "additionalProperties" in schema:
                additional = schema["additionalProperties"]
                if additional is False:
                    errors.append(f"{path}: unexpected property {key!r}")
                elif isinstance(additional, dict):
                    errors.extend(validate_json_schema(item, additional, root_schema, f"{path}.{key}"))

        if "propertyNames" in schema:
            name_schema = schema["propertyNames"]
            for key in value:
                errors.extend(validate_json_schema(key, name_schema, root_schema, f"{path}.<propertyName:{key}>"))

    if "oneOf" in schema:
        matches = 0
        candidate_errors: list[list[str]] = []
        for candidate in schema["oneOf"]:
            candidate_result = validate_json_schema(value, candidate, root_schema, path)
            candidate_errors.append(candidate_result)
            if not candidate_result:
                matches += 1
        if matches != 1:
            errors.append(f"{path}: oneOf matched {matches} alternatives")

    if "allOf" in schema:
        for sub in schema["allOf"]:
            errors.extend(validate_json_schema(value, sub, root_schema, path))

    if "if" in schema:
        condition_errors = validate_json_schema(value, schema["if"], root_schema, path)
        if not condition_errors and "then" in schema:
            errors.extend(validate_json_schema(value, schema["then"], root_schema, path))
        elif condition_errors and "else" in schema:
            errors.extend(validate_json_schema(value, schema["else"], root_schema, path))

    return errors


def assert_valid(value: Any, schema: dict[str, Any], label: str) -> None:
    errors = validate_json_schema(value, schema, schema)
    if errors:
        raise ValidationError(label + ":\n  - " + "\n  - ".join(errors[:25]))


def set_path(obj: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    node: Any = obj
    for part in parts[:-1]:
        if not isinstance(node, dict) or part not in node:
            raise ValidationError(f"mutation path does not exist: {dotted}")
        node = node[part]
    if not isinstance(node, dict):
        raise ValidationError(f"mutation parent is not object: {dotted}")
    node[parts[-1]] = value


def apply_mutation(obj: dict[str, Any], mutation: dict[str, Any] | None) -> dict[str, Any]:
    result = copy.deepcopy(obj)
    if mutation is None:
        return result

    op = mutation["op"]
    if op == "set_schema_version":
        result["schema_version"] = mutation["value"]
    elif op == "add_required_capability":
        result["meta"]["required_capabilities"].append(mutation["capability"])
    elif op == "add_core_property":
        set_path(result, mutation["path"], mutation["value"])
    elif op == "set_path":
        set_path(result, mutation["path"], mutation["value"])
    elif op == "set_collection_coverage":
        collection = mutation["collection"]
        result["policy"][collection]["coverage"]["status"] = mutation["status"]
        result["policy"][collection]["coverage"]["negative_evidence"] = mutation["negative_evidence"]
        result["policy"][collection]["coverage"]["reason_codes"] = []
    else:
        raise ValidationError(f"unsupported compatibility mutation: {op}")
    return result


def consumer_accepts(observation: dict[str, Any], supported_capabilities: set[str], schema: dict[str, Any]) -> tuple[bool, str]:
    errors = validate_json_schema(observation, schema, schema)
    if errors:
        return False, errors[0]
    required = set(observation["meta"]["required_capabilities"])
    missing = sorted(required - supported_capabilities)
    if missing:
        return False, "unsupported_required_capability:" + ",".join(missing)
    return True, "accepted"


def absence_claim_allowed(observation: dict[str, Any], collection: str) -> bool:
    block = observation["policy"][collection]
    coverage = block["coverage"]
    return (
        len(block["items"]) == 0
        and coverage["status"] == "complete"
        and coverage["negative_evidence"] == "scope_complete"
    )


def validate_registry(fields_doc: dict[str, Any], access_rule_ids: set[str]) -> None:
    if fields_doc.get("registry_version") != "observation-fields.v0":
        raise ValidationError("unexpected field registry version")
    if fields_doc.get("observation_schema_version") != "observation.v0":
        raise ValidationError("field registry points at unexpected observation schema")

    fields = fields_doc.get("fields")
    if not isinstance(fields, list) or not fields:
        raise ValidationError("field registry must contain fields")

    paths = [field["path"] for field in fields]
    duplicates = sorted({path for path in paths if paths.count(path) > 1})
    if duplicates:
        raise ValidationError("duplicate field-registry paths: " + ", ".join(duplicates))

    for field in fields:
        for key in (
            "path", "channel", "source", "access_rule_ids", "policy_visible",
            "units", "frame", "precision", "unknown_semantics",
            "absence_semantics", "stability"
        ):
            if key not in field:
                raise ValidationError(f"field {field.get('path', '<unknown>')} missing {key}")
        unknown_rules = sorted(set(field["access_rule_ids"]) - access_rule_ids)
        if unknown_rules:
            raise ValidationError(f"field {field['path']} references unknown rules: {unknown_rules}")
        if field["path"].startswith("meta.") and field["policy_visible"] is not False:
            raise ValidationError(f"meta field unexpectedly policy-visible: {field['path']}")
        if field["path"].startswith("policy.") and field["path"] != "policy.extensions.*":
            if field["policy_visible"] is not True:
                raise ValidationError(f"core policy field unexpectedly hidden: {field['path']}")

    forbidden_paths = {
        "policy.world_cues.visual_profile_id",
        "policy.geometry.representation",
        "policy.geometry.frame",
        "policy.entities.representation",
        "policy.entities.frame",
    }
    present_forbidden = sorted(forbidden_paths & set(paths))
    if present_forbidden:
        raise ValidationError("protocol/representation metadata leaked into policy registry: " + ", ".join(present_forbidden))

    entity_equipment = next(f for f in fields if f["path"] == "policy.entities.items[*].equipment")
    if "item identity only" not in entity_equipment["precision"]:
        raise ValidationError("visible entity equipment must be identity-only")

    expected_minimum_paths = {
        "meta.game_tick",
        "meta.information_access_profile_id",
        "policy.self.position",
        "policy.self.inventory.slots[*].item",
        "policy.geometry.coverage.status",
        "policy.geometry.items[*].block_id",
        "policy.entities.coverage.status",
        "policy.entities.items[*].observation_ref",
        "policy.entities.items[*].equipment",
        "policy.events.coverage.status",
        "policy.events.items[*].kind",
        "policy.events.items[*].sound_id",
        "policy.events.items[*].text",
        "policy.events.items[*].request_id",
        "policy.events.items[*].event_type",
        "policy.extensions.*",
    }
    missing = sorted(expected_minimum_paths - set(paths))
    if missing:
        raise ValidationError("field registry missing required semantic paths: " + ", ".join(missing))


def validate_semantic_fixture(observation: dict[str, Any], label: str) -> None:
    if observation["meta"]["information_access_profile_id"] != "player-equivalent.v1":
        raise ValidationError(f"{label}: unexpected information access profile")

    for name in ("geometry", "entities", "events"):
        collection = observation["policy"][name]
        coverage = collection["coverage"]
        if coverage["status"] == "partial" and coverage["negative_evidence"] == "scope_complete":
            raise ValidationError(f"{label}: {name} partial coverage cannot claim complete negative evidence")
        if coverage["status"] == "unavailable" and collection["items"]:
            raise ValidationError(f"{label}: {name} unavailable coverage must not carry positive items")

    for entity in observation["policy"]["entities"]["items"]:
        for equipment in entity["equipment"]:
            item = equipment["item"]
            if item is not None and set(item) != {"item_id"}:
                raise ValidationError(f"{label}: other-entity visible equipment leaked non-identity metadata")

    if "game_tick" in observation["policy"]:
        raise ValidationError(f"{label}: exact game tick leaked into policy")
    if any(key in observation["policy"]["world_cues"] for key in ("visual_profile_id", "information_access_profile_id")):
        raise ValidationError(f"{label}: access profile leaked into world_cues policy payload")


def validate_compatibility(
    compat: dict[str, Any],
    fixtures: dict[str, dict[str, Any]],
    obs_schema: dict[str, Any],
) -> None:
    ids = [case["id"] for case in compat["cases"]]
    if len(ids) != len(set(ids)):
        raise ValidationError("duplicate compatibility case IDs")

    required_cases = {
        "canonical_v0",
        "unknown_optional_extension",
        "unknown_required_capability",
        "future_schema_version",
        "wrong_position_shape",
        "unknown_core_property",
        "partial_empty_is_not_absence",
        "complete_empty_can_support_absence",
        "partial_cannot_claim_scope_complete",
    }
    missing = sorted(required_cases - set(ids))
    if missing:
        raise ValidationError("missing required compatibility cases: " + ", ".join(missing))

    for case in compat["cases"]:
        fixture_name = case["fixture"]
        if fixture_name not in fixtures:
            raise ValidationError(f"case {case['id']} references unknown fixture {fixture_name}")
        candidate = apply_mutation(fixtures[fixture_name], case["mutation"])
        accepted, reason = consumer_accepts(candidate, set(case["supported_capabilities"]), obs_schema)
        expected_accept = case["expected"] == "accept"
        if accepted != expected_accept:
            raise ValidationError(
                f"compatibility case {case['id']} expected {case['expected']} but got "
                f"{'accept' if accepted else 'reject'} ({reason})"
            )
        expected_absence = case.get("absence_claim_allowed")
        if expected_absence is not None:
            actual_absence = absence_claim_allowed(candidate, "entities")
            if actual_absence is not expected_absence:
                raise ValidationError(
                    f"compatibility case {case['id']} expected absence_claim_allowed="
                    f"{expected_absence}, got {actual_absence}"
                )


def main() -> int:
    try:
        obs_schema = load(OBS_SCHEMA_PATH)
        fields_schema = load(FIELDS_SCHEMA_PATH)
        fields = load(FIELDS_PATH)
        compat_schema = load(COMPAT_SCHEMA_PATH)
        compat = load(COMPAT_PATH)
        access = load(INFO_RULES)

        assert_valid(fields, fields_schema, "field registry")
        assert_valid(compat, compat_schema, "compatibility catalog")

        fixtures = {name: load(path) for name, path in FIXTURES.items()}
        for name, fixture in fixtures.items():
            assert_valid(fixture, obs_schema, name)
            validate_semantic_fixture(fixture, name)

        rule_ids = {rule["id"] for rule in access["rules"]}
        validate_registry(fields, rule_ids)
        validate_compatibility(compat, fixtures, obs_schema)

        canonical = fixtures["example-observation.v0.json"]
        if canonical["policy"]["entities"]["coverage"]["status"] != "partial":
            raise ValidationError("canonical fixture must exercise partial entity coverage")
        unknowns = fixtures["example-unknowns.v0.json"]
        if absence_claim_allowed(unknowns, "entities"):
            raise ValidationError("unknown fixture accidentally permits entity absence claim")

        print(f"observation schema: ok ({len(fixtures)} fixtures)")
        print(f"observation field registry: ok ({len(fields['fields'])} fields)")
        print(f"observation compatibility: ok ({len(compat['cases'])} cases)")
        return 0
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

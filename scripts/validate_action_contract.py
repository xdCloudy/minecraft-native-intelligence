#!/usr/bin/env python3
"""Validate action request/outcome schemas and representative contract cases."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_observation_contract import ValidationError, assert_valid, load  # noqa: E402

ACTION_DIR = ROOT / "docs" / "actions"
REQUEST_SCHEMA = load(ACTION_DIR / "action-request.schema.json")
OUTCOME_SCHEMA = load(ACTION_DIR / "action-outcome.schema.json")
REQUEST_EXAMPLE = load(ACTION_DIR / "example-action-request.v0.json")
OUTCOME_EXAMPLE = load(ACTION_DIR / "example-action-outcome.v0.json")


def must_reject(value: dict[str, Any], schema: dict[str, Any], label: str) -> None:
    try:
        assert_valid(value, schema, label)
    except ValidationError:
        return
    raise AssertionError(f"{label} unexpectedly passed validation")


def check_requests() -> None:
    assert_valid(REQUEST_EXAMPLE, REQUEST_SCHEMA, "example request")
    round_trip = json.loads(json.dumps(REQUEST_EXAMPLE, sort_keys=True))
    assert_valid(round_trip, REQUEST_SCHEMA, "serialized request")

    invalid = copy.deepcopy(REQUEST_EXAMPLE)
    invalid["action"]["target"]["x"] = 1.5
    must_reject(invalid, REQUEST_SCHEMA, "fractional block coordinate")

    invalid = copy.deepcopy(REQUEST_EXAMPLE)
    invalid["action"]["bypass_reach"] = True
    must_reject(invalid, REQUEST_SCHEMA, "unknown privileged property")

    invalid = copy.deepcopy(REQUEST_EXAMPLE)
    invalid["action"] = {"type": "set_position", "x": 100, "y": 80, "z": 100}
    must_reject(invalid, REQUEST_SCHEMA, "unknown teleport action")

    invalid = copy.deepcopy(REQUEST_EXAMPLE)
    invalid["action"] = {"type": "move", "forward": 2, "strafe": 0}
    must_reject(invalid, REQUEST_SCHEMA, "out-of-range movement input")

    invalid = copy.deepcopy(REQUEST_EXAMPLE)
    invalid["session_epoch"] = True
    must_reject(invalid, REQUEST_SCHEMA, "boolean session epoch")


def check_outcomes() -> None:
    assert_valid(OUTCOME_EXAMPLE, OUTCOME_SCHEMA, "example outcome")
    round_trip = json.loads(json.dumps(OUTCOME_EXAMPLE, sort_keys=True))
    assert_valid(round_trip, OUTCOME_SCHEMA, "serialized outcome")

    invalid = copy.deepcopy(OUTCOME_EXAMPLE)
    invalid["status"] = "rejected"
    must_reject(invalid, OUTCOME_SCHEMA, "rejection without reason")

    invalid = copy.deepcopy(OUTCOME_EXAMPLE)
    invalid["status"] = "success"
    must_reject(invalid, OUTCOME_SCHEMA, "unknown outcome status")

    invalid = copy.deepcopy(OUTCOME_EXAMPLE)
    invalid["extra"] = "ignored?"
    must_reject(invalid, OUTCOME_SCHEMA, "unknown outcome property")


def check_interaction_target_pairing() -> None:
    """Validate the schema's documented cross-field target invariant."""
    action = {"type": "interact", "target_kind": "block", "target_block": {"x": 1, "y": 2, "z": 3}}
    envelope = copy.deepcopy(REQUEST_EXAMPLE)
    envelope["action"] = action
    assert_valid(envelope, REQUEST_SCHEMA, "block interaction")

    envelope["action"] = {"type": "interact", "target_kind": "block", "target_entity_id": "entity:1"}
    must_reject(envelope, REQUEST_SCHEMA, "block interaction with entity target")

    envelope["action"] = {"type": "interact", "target_kind": "entity", "target_entity_id": "entity:1"}
    assert_valid(envelope, REQUEST_SCHEMA, "entity interaction")


def main() -> int:
    check_requests()
    check_outcomes()
    check_interaction_target_pairing()
    print("action request/outcome contract: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

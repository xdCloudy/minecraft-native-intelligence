"""T1/T2/T6 action protocol regressions; no Minecraft capability claims."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from scripts.validate_action_contract import (
    ACTION_SCHEMA,
    validate_outcome,
    validate_request,
    schema_errors,
)


def example_action() -> dict:
    return {
        "schema_version": "action.v0",
        "agent_id": "agent-1",
        "session_epoch": 3,
        "action_id": "action-001",
        "observation_seq": 42,
        "submitted_tick": 100,
        "expires_tick": 105,
        "trace_id": "trace-001",
        "intent": {"type": "move", "forward": 0.5, "strafe": 0, "duration_ticks": 5},
    }


def preflight(action: dict, supported: set[str] | None = None) -> str | None:
    return validate_request(
        action, supported_actions=supported if supported is not None else {"move", "chat", "stop", "attack"},
        agent_id="agent-1", session_epoch=3,
        latest_observation_seq=42, current_tick=101,
    )


class ActionContractTests(unittest.TestCase):
    def test_valid_move(self):
        self.assertEqual([], schema_errors(example_action(), ACTION_SCHEMA))
        self.assertIsNone(preflight(example_action()))

    def test_each_declared_intent_has_a_typed_valid_shape(self):
        intents = [
            {"type": "look", "yaw_delta_degrees": 10, "pitch_delta_degrees": -5},
            {"type": "jump", "pressed": True, "duration_ticks": 1},
            {"type": "attack", "target_ref": "visible:entity:12"},
            {"type": "mine", "target_ref": "visible:block:13"},
            {"type": "place", "target_ref": "visible:block:13", "face": "up", "hand": "main"},
            {"type": "interact", "target_ref": "visible:block:13", "hand": "off"},
            {"type": "select_hotbar", "slot": 8},
            {"type": "craft", "recipe_id": "minecraft:oak_planks", "count": 2},
            {"type": "chat", "message": "hello"},
            {"type": "stop", "scope": "active_intent"},
        ]
        for intent in intents:
            with self.subTest(intent=intent["type"]):
                action = example_action()
                action["intent"] = intent
                self.assertEqual([], schema_errors(action, ACTION_SCHEMA))

    def test_old_or_future_versions_fail_closed(self):
        for version in ("action.v-1", "action.v1", "observation.v0"):
            with self.subTest(version=version):
                action = example_action()
                action["schema_version"] = version
                self.assertEqual("unsupported_version", preflight(action))

    def test_unknown_action_or_privileged_field_rejected(self):
        for intent in ({"type": "teleport", "coordinates": [1, 2, 3]},
                       {"type": "move", "forward": 1, "strafe": 0, "duration_ticks": 1, "set_health": 20}):
            action = example_action()
            action["intent"] = intent
            self.assertEqual("invalid_schema", preflight(action))

    def test_wrong_agent_session_or_observation_rejected(self):
        cases = [("agent_id", "other", "unknown_agent"),
                 ("session_epoch", 2, "wrong_session"),
                 ("observation_seq", 41, "stale_observation"),
                 ("observation_seq", 43, "stale_observation")]
        for field, value, expected in cases:
            with self.subTest(field=field, value=value):
                action = example_action()
                action[field] = value
                self.assertEqual(expected, preflight(action))

    def test_expiry_and_future_ticks_rejected(self):
        for field, value, expected in (
            ("expires_tick", 100, "expired"),
            ("submitted_tick", 102, "expired"),
            ("expires_tick", 99, "invalid_schema"),
        ):
            action = example_action()
            action[field] = value
            self.assertEqual(expected, preflight(action))

    def test_inverted_deadline_rejected_even_before_expiry(self):
        action = example_action()
        action["submitted_tick"] = 100
        action["expires_tick"] = 99
        self.assertEqual("invalid_schema", preflight(action))

    def test_negotiation_fails_closed(self):
        action = example_action()
        self.assertEqual("unsupported_action", preflight(action, {"look"}))

    def test_no_command_injection_over_chat(self):
        for message in ("/op Cloudy", "hello\x00world", "x" * 257):
            action = example_action()
            action["intent"] = {"type": "chat", "message": message}
            self.assertEqual("illegal_action", preflight(action))

    def test_bounded_continuous_controls_and_hotbar(self):
        for intent in (
            {"type": "move", "forward": 1.1, "strafe": 0, "duration_ticks": 1},
            {"type": "move", "forward": 0, "strafe": 0, "duration_ticks": 1000},
            {"type": "select_hotbar", "slot": 9},
        ):
            action = example_action()
            action["intent"] = intent
            self.assertEqual("invalid_schema", preflight(action))

    def test_unexpected_top_level_privileges_rejected(self):
        action = example_action()
        action["server_command"] = "give"
        self.assertEqual("invalid_schema", preflight(action))

    def test_outcome_lifecycle_and_reason_constraints(self):
        outcome = {
            "schema_version": "action-outcome.v0",
            "agent_id": "agent-1", "session_epoch": 3,
            "action_id": "action-001", "trace_id": "trace-001",
            "server_tick": 102, "phase": "accepted",
        }
        self.assertEqual([], validate_outcome(outcome))
        for phase in ("started", "completed"):
            outcome["phase"] = phase
            self.assertEqual([], validate_outcome(outcome))
        outcome["phase"] = "rejected"
        self.assertTrue(validate_outcome(outcome))
        outcome["reason"] = "permission_denied"
        self.assertEqual([], validate_outcome(outcome))
        outcome["phase"] = "completed"
        self.assertTrue(validate_outcome(outcome))

    def test_direct_cli_accepts_golden_fixture(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "scripts/validate_action_contract.py", "docs/actions/example-action.v0.json"],
            cwd=root, capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_bool_is_not_integer_tick(self):
        action = example_action()
        action["submitted_tick"] = True
        self.assertEqual("invalid_schema", preflight(action))


if __name__ == "__main__":
    unittest.main()

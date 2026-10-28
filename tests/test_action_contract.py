"""T1/T2/T6 action protocol regressions; no Minecraft capability claims."""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from scripts.validate_action_contract import (
    ACTION_SCHEMA,
    OutcomeSequenceError,
    audit_outcome_sequence,
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


def outcome(phase: str, tick: int = 101, reason: str | None = None) -> dict:
    event = {
        "schema_version": "action-outcome.v0", "agent_id": "agent-1",
        "session_epoch": 3, "action_id": "action-001",
        "trace_id": "trace-001", "server_tick": tick, "phase": phase,
    }
    if reason is not None:
        event["reason"] = reason
    return event


class ActionContractTests(unittest.TestCase):
    def test_audit_completed_lifecycle_and_exact_idempotent_replays(self):
        accepted = outcome("accepted", 101)
        started = outcome("started", 102)
        completed = outcome("completed", 103)
        history = [accepted, started, accepted.copy(), completed, completed.copy()]
        result = audit_outcome_sequence(example_action(), history)
        self.assertEqual("completed", result.phase)
        self.assertEqual(103, result.last_server_tick)
        self.assertEqual(2, result.replayed_messages)
        self.assertTrue(result.terminal)

    def test_audit_pending_partial_and_terminal_rejection(self):
        self.assertFalse(audit_outcome_sequence(example_action(), []).terminal)
        self.assertFalse(audit_outcome_sequence(example_action(), [outcome("accepted")]).terminal)
        self.assertTrue(audit_outcome_sequence(
            example_action(), [outcome("rejected", 101, "permission_denied")]
        ).terminal)
        self.assertTrue(audit_outcome_sequence(
            example_action(), [outcome("accepted"), outcome("cancelled", 102, "operator_stop")]
        ).terminal)

    def test_audit_rejects_identity_mismatch_and_changed_replay(self):
        for field, replacement in (
            ("agent_id", "other"), ("session_epoch", 4),
            ("action_id", "other"), ("trace_id", "other"),
        ):
            with self.subTest(field=field):
                changed = outcome("accepted")
                changed[field] = replacement
                with self.assertRaisesRegex(OutcomeSequenceError, "unrelated"):
                    audit_outcome_sequence(example_action(), [changed])
        with self.assertRaisesRegex(OutcomeSequenceError, "conflicting"):
            audit_outcome_sequence(example_action(), [outcome("accepted", 101), outcome("accepted", 102)])

    def test_audit_rejects_illegal_phase_transitions(self):
        invalid = [
            [outcome("completed")],
            [outcome("started")],
            [outcome("accepted"), outcome("rejected", 102, "illegal_action")],
            [outcome("accepted"), outcome("completed", 102), outcome("cancelled", 103, "operator_stop")],
            [outcome("accepted"), outcome("started", 102), outcome("accepted", 103)],
        ]
        for events in invalid:
            with self.subTest(events=events), self.assertRaises(OutcomeSequenceError):
                audit_outcome_sequence(example_action(), events)

    def test_audit_rejects_bad_ticks_schemas_and_deadlines(self):
        for events in (
            [outcome("accepted", 99)],
            [outcome("accepted", 102), outcome("completed", 101)],
            [outcome("rejected")],
        ):
            with self.subTest(events=events), self.assertRaises(OutcomeSequenceError):
                audit_outcome_sequence(example_action(), events)
        action = example_action()
        action["expires_tick"] = 99
        with self.assertRaisesRegex(OutcomeSequenceError, "inverted"):
            audit_outcome_sequence(action, [])
        with self.assertRaisesRegex(OutcomeSequenceError, "ordered list"):
            audit_outcome_sequence(example_action(), None)

    def test_audit_cli_on_golden_fixture(self):
        root = Path(__file__).resolve().parents[1]
        run = subprocess.run(
            [sys.executable, "scripts/validate_action_contract.py",
             "docs/actions/example-outcomes.v0.json", "--request", "docs/actions/example-action.v0.json"],
            cwd=root, text=True, capture_output=True, check=False,
        )
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertIn("terminal=True", run.stdout)

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

    def test_nonfinite_numeric_input_rejected(self):
        for value in (float("nan"), float("inf"), -float("inf")):
            action = example_action()
            action["intent"]["forward"] = value
            self.assertEqual("invalid_schema", preflight(action))

    def test_bool_is_not_integer_tick(self):
        action = example_action()
        action["submitted_tick"] = True
        self.assertEqual("invalid_schema", preflight(action))


if __name__ == "__main__":
    unittest.main()

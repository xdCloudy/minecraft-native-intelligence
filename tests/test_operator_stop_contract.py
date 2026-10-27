"""T1/T6 model of operator authority and immediate action fencing."""
from __future__ import annotations

import unittest

from scripts.operator_stop_contract import ControlState, action_admissible, apply_operator_command


class OperatorStopContractTests(unittest.TestCase):
    def setUp(self):
        self.initial = ControlState("agent-001")

    def send(self, state, command, seq, role="server_owner"):
        return apply_operator_command(state, command, seq, verified_role=role)

    def test_emergency_stop_fences_queued_and_inflight_actions(self):
        state = self.initial
        self.assertTrue(action_admissible(state, agent_id="agent-001", action_epoch=0))
        state, reason = self.send(state, "emergency_stop", 1)
        self.assertEqual("stopped", reason)
        self.assertFalse(action_admissible(state, agent_id="agent-001", action_epoch=0))
        self.assertFalse(action_admissible(state, agent_id="agent-001", action_epoch=1))

    def test_paused_agent_cannot_act_even_with_fresh_epoch(self):
        paused, _ = self.send(self.initial, "pause", 1)
        self.assertFalse(action_admissible(paused, agent_id="agent-001", action_epoch=paused.epoch))
        resumed, result = self.send(paused, "resume", 2)
        self.assertEqual("running", result)
        self.assertTrue(action_admissible(resumed, agent_id="agent-001", action_epoch=resumed.epoch))
        self.assertFalse(action_admissible(resumed, agent_id="agent-001", action_epoch=0))

    def test_no_chat_or_model_authority(self):
        for role in (None, "agent", "player", "minecraft_chat", "runtime"):
            with self.subTest(role=role):
                state, reason = self.send(self.initial, "emergency_stop", 1, role)
                self.assertEqual(self.initial, state)
                self.assertEqual("permission_denied", reason)

    def test_unknown_or_bogus_commands_fail_closed(self):
        for command in ("give", "teleport", "shutdown_host", "resume", "reset_stop"):
            state, reason = self.send(self.initial, command, 1)
            self.assertEqual(self.initial, state)
            self.assertEqual("invalid_transition", reason)

    def test_stop_requires_explicit_owner_reset_then_resume(self):
        stopped, _ = self.send(self.initial, "emergency_stop", 1)
        same, reason = self.send(stopped, "resume", 2)
        self.assertEqual("invalid_transition", reason)
        self.assertEqual(stopped, same)
        same, reason = self.send(stopped, "reset_stop", 2, "operator_admin")
        self.assertEqual("invalid_transition", reason)
        self.assertEqual(stopped, same)
        paused, reason = self.send(stopped, "reset_stop", 2)
        self.assertEqual("reset_to_paused", reason)
        self.assertFalse(action_admissible(paused, agent_id="agent-001", action_epoch=paused.epoch))
        running, reason = self.send(paused, "resume", 3)
        self.assertEqual("running", reason)
        self.assertTrue(action_admissible(running, agent_id="agent-001", action_epoch=running.epoch))

    def test_replayed_or_invalid_operator_sequence_rejected(self):
        paused, _ = self.send(self.initial, "pause", 2)
        for sequence in (2, 1, True, "3"):
            state, reason = self.send(paused, "resume", sequence)
            self.assertEqual(paused, state)
            self.assertEqual("stale_or_invalid_sequence", reason)

    def test_per_agent_identity_boundary(self):
        self.assertFalse(action_admissible(self.initial, agent_id="agent-002", action_epoch=0))
        self.assertFalse(action_admissible(self.initial, agent_id="agent-001", action_epoch=True))

    def test_state_is_immutable(self):
        first = self.initial
        second, _ = self.send(first, "pause", 1)
        self.assertEqual("running", first.mode)
        self.assertEqual(0, first.epoch)
        self.assertEqual("paused", second.mode)


if __name__ == "__main__":
    unittest.main()

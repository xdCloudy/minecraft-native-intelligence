"""Deterministic semantic tests for offline runtime handshake negotiation."""
from __future__ import annotations

import copy
import unittest

from scripts.validate_runtime_handshake import HandshakeError, negotiate


SHA = "a" * 64


def peer(role: str) -> dict:
    return {
        "schema_version": "runtime-handshake.v0",
        "role": role,
        "instance_id": "mod-1" if role == "minecraft_mod" else "worker-1",
        "session_epoch": 4,
        "protocol": {"major": 0, "minor": 2 if role == "minecraft_mod" else 1},
        "transport": "loopback",
        "ready": True,
        "schemas": {"observation": "observation.v0", "action": "action.v0"},
        "supported_capabilities": ["observations", "actions"] if role == "minecraft_mod" else ["inference", "batch"],
        "required_capabilities": ["inference"] if role == "minecraft_mod" else ["observations"],
        "limits": {"max_message_bytes": 65536 if role == "minecraft_mod" else 32768, "max_batch": 64 if role == "minecraft_mod" else 8},
        "model": None if role == "minecraft_mod" else {"model_id": "test-synthetic", "checkpoint_sha256": SHA, "revision": "fixture-1"},
    }


class RuntimeNegotiationTests(unittest.TestCase):
    def setUp(self):
        self.mod = peer("minecraft_mod")
        self.worker = peer("inference_runtime")

    def negotiate(self):
        return negotiate(self.mod, self.worker, approved_checkpoint_sha256=SHA)

    def test_success_limits_minimum_and_protocol(self):
        result = self.negotiate()
        self.assertEqual(result.session_epoch, 4)
        self.assertEqual(result.minor_version, 1)
        self.assertEqual(result.max_batch, 8)
        self.assertEqual(result.max_message_bytes, 32768)
        self.assertEqual(result.checkpoint_sha256, SHA)
        self.assertEqual(result.capabilities, ())

    def test_common_capability_intersection_is_stable(self):
        self.mod["supported_capabilities"].append("tracing")
        self.worker["supported_capabilities"].append("tracing")
        self.assertEqual(self.negotiate().capabilities, ("tracing",))

    def test_reject_old_epoch(self):
        self.worker["session_epoch"] = 3
        with self.assertRaisesRegex(HandshakeError, "epoch"):
            self.negotiate()

    def test_reject_major_mismatch(self):
        self.worker["protocol"]["major"] = 1
        with self.assertRaises(HandshakeError):
            self.negotiate()

    def test_reject_boolean_major(self):
        self.worker["protocol"]["major"] = False
        with self.assertRaises(HandshakeError):
            self.negotiate()

    def test_reject_incompatible_minor(self):
        with self.assertRaisesRegex(HandshakeError, "minor"):
            negotiate(self.mod, self.worker, approved_checkpoint_sha256=SHA, minimum_minor=2)

    def test_reject_unready(self):
        self.worker["ready"] = False
        with self.assertRaisesRegex(HandshakeError, "not ready"):
            self.negotiate()

    def test_reject_remote_transport(self):
        self.worker["transport"] = "remote"
        with self.assertRaises(HandshakeError):
            self.negotiate()

    def test_reject_bad_observation_version(self):
        self.mod["schemas"]["observation"] = "observation.v1"
        with self.assertRaises(HandshakeError):
            self.negotiate()

    def test_reject_no_model(self):
        self.worker["model"] = None
        with self.assertRaisesRegex(HandshakeError, "no loaded"):
            self.negotiate()

    def test_reject_unapproved_model(self):
        self.worker["model"]["checkpoint_sha256"] = "b" * 64
        with self.assertRaisesRegex(HandshakeError, "not approved"):
            self.negotiate()

    def test_reject_peer_model_disagreement(self):
        self.mod["model"] = copy.deepcopy(self.worker["model"])
        self.mod["model"]["checkpoint_sha256"] = "b" * 64
        with self.assertRaisesRegex(HandshakeError, "disagree"):
            self.negotiate()

    def test_reject_capability_absent_on_other_peer(self):
        self.worker["supported_capabilities"].append("action-authority")
        self.worker["required_capabilities"] = ["action-authority"]
        with self.assertRaisesRegex(HandshakeError, "Minecraft missing"):
            self.negotiate()

    def test_reject_self_inconsistent_requirements(self):
        self.worker["required_capabilities"] = ["fictional"]
        with self.assertRaises(HandshakeError):
            self.negotiate()

    def test_reject_oversized_batch(self):
        self.worker["limits"]["max_batch"] = 10001
        with self.assertRaises(HandshakeError):
            self.negotiate()

    def test_reject_duplicate_capability(self):
        self.mod["supported_capabilities"].append("observations")
        with self.assertRaises(HandshakeError):
            self.negotiate()

    def test_reject_unknown_field(self):
        self.mod["authentication_token"] = "secret"
        with self.assertRaises(HandshakeError):
            self.negotiate()

    def test_reject_null_and_bool_minor(self):
        for invalid in (None, True, -1):
            with self.subTest(invalid=invalid):
                mod = copy.deepcopy(self.mod)
                mod["protocol"]["minor"] = invalid
                with self.assertRaises(HandshakeError):
                    negotiate(mod, self.worker, approved_checkpoint_sha256=SHA)

    def test_reject_bad_approved_digest(self):
        with self.assertRaises(HandshakeError):
            negotiate(self.mod, self.worker, approved_checkpoint_sha256="not-a-hash")

    def test_reject_identical_peer_identity(self):
        self.worker["instance_id"] = self.mod["instance_id"]
        with self.assertRaisesRegex(HandshakeError, "distinct"):
            self.negotiate()


if __name__ == "__main__":
    unittest.main()

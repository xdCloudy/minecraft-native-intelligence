#!/usr/bin/env python3
"""Offline, fail-closed semantic handshake check; not a network authentication layer.

The JSON representation is an executable test fixture for the logical protocol.
Production wire messages remain Protobuf under the runtime boundary design.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.validate_observation_contract import validate_json_schema

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "docs" / "runtime" / "handshake.schema.json"


class HandshakeError(ValueError):
    """Two peers cannot establish a compatible, authorized-to-start session."""


@dataclass(frozen=True)
class NegotiatedSession:
    session_epoch: int
    minor_version: int
    capabilities: tuple[str, ...]
    max_message_bytes: int
    max_batch: int
    model_id: str
    checkpoint_sha256: str


def _validate(peer: Any, role: str, schema: dict[str, Any]) -> None:
    problems = validate_json_schema(peer, schema, schema)
    if problems:
        raise HandshakeError(f"{role}: invalid handshake: {'; '.join(problems[:5])}")
    if peer["role"] != role:
        raise HandshakeError(f"expected role {role}")
    if not peer["ready"]:
        raise HandshakeError(f"{role} not ready")


def negotiate(
    mod: dict[str, Any],
    runtime: dict[str, Any],
    *,
    approved_checkpoint_sha256: str,
    minimum_minor: int = 0,
) -> NegotiatedSession:
    """Negotiate one exact-epoch local session with a pre-approved model digest.

    Caller must authenticate the process/channel independently and fence older
    sessions. Capability advertisement is never Minecraft action authorization.
    """
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    _validate(mod, "minecraft_mod", schema)
    _validate(runtime, "inference_runtime", schema)

    if type(minimum_minor) is not int or minimum_minor < 0:
        raise HandshakeError("minimum_minor must be a nonnegative integer")
    if not isinstance(approved_checkpoint_sha256, str) or len(approved_checkpoint_sha256) != 64 or any(
        ch not in "0123456789abcdef" for ch in approved_checkpoint_sha256
    ):
        raise HandshakeError("approved checkpoint must be a lowercase SHA-256 digest")
    if mod["session_epoch"] != runtime["session_epoch"]:
        raise HandshakeError("mismatched session epoch")
    if mod["instance_id"] == runtime["instance_id"]:
        raise HandshakeError("peers must have distinct instance IDs")
    minor = min(mod["protocol"]["minor"], runtime["protocol"]["minor"])
    if minor < minimum_minor:
        raise HandshakeError("no compatible protocol minor version")

    mod_caps = set(mod["supported_capabilities"])
    runtime_caps = set(runtime["supported_capabilities"])
    if not set(mod["required_capabilities"]).issubset(runtime_caps):
        raise HandshakeError("runtime missing mandatory Minecraft capabilities")
    if not set(runtime["required_capabilities"]).issubset(mod_caps):
        raise HandshakeError("Minecraft missing mandatory runtime capabilities")

    model = runtime["model"]
    if not isinstance(model, dict):
        raise HandshakeError("no loaded runtime model")
    if model["checkpoint_sha256"] != approved_checkpoint_sha256:
        raise HandshakeError("runtime checkpoint is not approved")
    if mod["model"] is not None and mod["model"]["checkpoint_sha256"] != model["checkpoint_sha256"]:
        raise HandshakeError("peers disagree on model checkpoint")

    return NegotiatedSession(
        session_epoch=mod["session_epoch"],
        minor_version=minor,
        capabilities=tuple(sorted(mod_caps & runtime_caps)),
        max_message_bytes=min(mod["limits"]["max_message_bytes"], runtime["limits"]["max_message_bytes"]),
        max_batch=min(mod["limits"]["max_batch"], runtime["limits"]["max_batch"]),
        model_id=model["model_id"],
        checkpoint_sha256=model["checkpoint_sha256"],
    )

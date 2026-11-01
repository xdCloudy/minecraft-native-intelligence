#!/usr/bin/env python3
"""Reference operator-stop state transitions, not a connected Minecraft controller."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

Mode = Literal["running", "paused", "stopped"]
Command = Literal["pause", "resume", "emergency_stop", "reset_stop"]
TRUSTED_ROLES = frozenset({"server_owner", "operator_admin"})


@dataclass(frozen=True)
class ControlState:
    """Per-agent control fence. Epoch increments invalidate queued actions."""

    agent_id: str
    mode: Mode = "paused"
    epoch: int = 0
    last_operator_sequence: int = -1


def apply_operator_command(
    state: ControlState, command: str, sequence: int, *, verified_role: str | None
) -> tuple[ControlState, str]:
    """Caller MUST pass a role verified out-of-band by the server control plane.

    Do not populate verified_role from chat, books, signs, model output or
    unauthenticated runtime messages.
    """
    if verified_role not in TRUSTED_ROLES:
        return state, "permission_denied"
    if type(sequence) is not int or sequence <= state.last_operator_sequence:
        return state, "stale_or_invalid_sequence"
    if command == "emergency_stop":
        return replace(state, mode="stopped", epoch=state.epoch + 1,
                       last_operator_sequence=sequence), "stopped"
    if command == "pause" and state.mode == "running":
        return replace(state, mode="paused", epoch=state.epoch + 1,
                       last_operator_sequence=sequence), "paused"
    if command == "resume" and state.mode == "paused":
        return replace(state, mode="running", epoch=state.epoch + 1,
                       last_operator_sequence=sequence), "running"
    if command == "reset_stop" and state.mode == "stopped" and verified_role == "server_owner":
        return replace(state, mode="paused", epoch=state.epoch + 1,
                       last_operator_sequence=sequence), "reset_to_paused"
    return state, "invalid_transition"


def action_admissible(state: ControlState, *, agent_id: str, action_epoch: int) -> bool:
    """Check again on the logical server thread immediately before side effects."""
    return (
        state.mode == "running"
        and state.agent_id == agent_id
        and type(action_epoch) is int
        and action_epoch == state.epoch
    )

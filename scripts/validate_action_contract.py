#!/usr/bin/env python3
"""Offline conformance checks for action.v0; never executes Minecraft actions."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.validate_observation_contract import validate_json_schema
ACTION_SCHEMA = ROOT / "docs" / "actions" / "action.schema.json"
OUTCOME_SCHEMA = ROOT / "docs" / "actions" / "outcome.schema.json"


def load(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def contains_nonfinite(value: Any) -> bool:
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, list):
        return any(contains_nonfinite(item) for item in value)
    if isinstance(value, dict):
        return any(contains_nonfinite(item) for item in value.values())
    return False


def schema_errors(value: Any, schema_path: Path) -> list[str]:
    schema = load(schema_path)
    return (["non-finite numeric value"] if contains_nonfinite(value)
            else validate_json_schema(value, schema, schema))


def validate_request(
    request: dict[str, Any],
    *,
    supported_actions: set[str],
    agent_id: str,
    session_epoch: int,
    latest_observation_seq: int,
    current_tick: int,
) -> str | None:
    """Return a stable reject reason, or None when the envelope is admissible.

    This is a boundary preflight, NOT a Minecraft legality or permission check.
    The authoritative server must still evaluate the action against live state.
    """
    if not isinstance(request, dict):
        return "invalid_schema"
    if request.get("schema_version") != "action.v0":
        return "unsupported_version"
    if schema_errors(request, ACTION_SCHEMA):
        return "invalid_schema"
    if request["agent_id"] != agent_id:
        return "unknown_agent"
    if request["session_epoch"] != session_epoch:
        return "wrong_session"
    if request["observation_seq"] != latest_observation_seq:
        return "stale_observation"
    if request["expires_tick"] < request["submitted_tick"]:
        return "invalid_schema"
    if request["submitted_tick"] > current_tick or request["expires_tick"] < current_tick:
        return "expired"
    kind = request["intent"]["type"]
    if kind not in supported_actions:
        return "unsupported_action"
    if kind == "chat":
        message = request["intent"]["message"]
        if len(message) > 256 or message.startswith("/") or "\x00" in message:
            return "illegal_action"
    return None


def validate_outcome(outcome: dict[str, Any]) -> list[str]:
    return schema_errors(outcome, OUTCOME_SCHEMA)


class OutcomeSequenceError(ValueError):
    """An outcome stream cannot be safely associated with one action."""


@dataclass(frozen=True)
class OutcomeAudit:
    phase: str | None
    last_server_tick: int | None
    terminal: bool
    replayed_messages: int


def audit_outcome_sequence(request: dict[str, Any], events: list[Any]) -> OutcomeAudit:
    """Audit an ordered, server-origin outcome stream without executing actions.

    Authentication and gameplay legality MUST be enforced by the live server.
    Exact replays are idempotent; changed replays, unrelated identities, phase
    regressions and out-of-order *new* state changes fail closed.
    """
    if schema_errors(request, ACTION_SCHEMA):
        raise OutcomeSequenceError("invalid request schema")
    if request["expires_tick"] < request["submitted_tick"]:
        raise OutcomeSequenceError("inverted action deadline")
    if not isinstance(events, list):
        raise OutcomeSequenceError("outcomes must be an ordered list")

    identity = ("agent_id", "session_epoch", "action_id", "trace_id")
    transitions: dict[str | None, frozenset[str]] = {
        None: frozenset({"accepted", "rejected"}),
        "accepted": frozenset({"started", "completed", "cancelled"}),
        "started": frozenset({"completed", "cancelled"}),
    }
    seen: dict[str, dict[str, Any]] = {}
    phase: str | None = None
    last_tick: int | None = None
    replays = 0
    for index, event in enumerate(events):
        if validate_outcome(event):
            raise OutcomeSequenceError(f"event {index}: invalid outcome schema")
        if any(event[field] != request[field] for field in identity):
            raise OutcomeSequenceError(f"event {index}: unrelated action identity")
        new_phase = event["phase"]
        if new_phase in seen:
            if event != seen[new_phase]:
                raise OutcomeSequenceError(f"event {index}: conflicting phase replay")
            replays += 1
            continue
        if new_phase not in transitions.get(phase, frozenset()):
            raise OutcomeSequenceError(f"event {index}: invalid phase transition")
        tick = event["server_tick"]
        if tick < request["submitted_tick"] or (last_tick is not None and tick < last_tick):
            raise OutcomeSequenceError(f"event {index}: nonmonotonic server tick")
        seen[new_phase] = event
        phase, last_tick = new_phase, tick

    return OutcomeAudit(phase=phase, last_server_tick=last_tick,
                        terminal=phase in {"completed", "cancelled", "rejected"},
                        replayed_messages=replays)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="JSON request or outcome")
    parser.add_argument("--outcome", action="store_true", help="Validate outcome rather than request")
    parser.add_argument("--request", type=Path,
                        help="Treat file as an outcome array and audit it against this request")
    args = parser.parse_args()
    if args.outcome and args.request:
        parser.error("--outcome and --request are mutually exclusive")
    value = load(args.file)
    if args.request:
        try:
            audit = audit_outcome_sequence(load(args.request), value)
        except OutcomeSequenceError as error:
            parser.exit(1, f"outcome sequence rejected: {error}\n")
        print(f"offline outcome audit valid: phase={audit.phase}, "
              f"terminal={audit.terminal}, exact_replays={audit.replayed_messages}")
        return 0
    errors = validate_outcome(value) if args.outcome else schema_errors(value, ACTION_SCHEMA)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("schema valid (offline only; no server legality claimed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

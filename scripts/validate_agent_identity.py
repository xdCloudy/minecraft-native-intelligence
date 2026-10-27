#!/usr/bin/env python3
"""Validate v0 persistent-agent identity ownership and serialization fixtures."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "agents" / "identity.schema.json"
EXAMPLE_PATH = ROOT / "docs" / "agents" / "identity.example.v0.json"
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
STATE_REF_RE = re.compile(r"^mni-state://agent/(?P<owner>[0-9a-f-]{36})/(?P<kind>[a-z][a-z0-9-]*)$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")
SKIN_HASH_RE = re.compile(r"^[a-f0-9]{64}$")


def validate_record(record: dict[str, Any]) -> None:
    required = {
        "schema_version", "agent_id", "minecraft_profile_id", "world_binding_id",
        "revision", "created_at", "created_by", "lifecycle_state", "display",
        "personal_state_refs",
    }
    if record.keys() - (required | {"lineage"}) or not required <= record.keys():
        raise ValueError("identity record has missing or unknown top-level fields")
    if record["schema_version"] != "agent-identity.v0":
        raise ValueError("unsupported identity schema version")
    for field in ("agent_id", "minecraft_profile_id", "world_binding_id"):
        if not UUID_RE.fullmatch(record[field]):
            raise ValueError(f"{field} must be a lowercase UUIDv4")
    if type(record["revision"]) is not int or record["revision"] < 0:
        raise ValueError("revision must be a nonnegative integer")
    try:
        created_at = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError("created_at must be an RFC 3339 UTC timestamp") from exc
    if not record["created_at"].endswith("Z") or created_at.utcoffset() is None:
        raise ValueError("created_at must be an RFC 3339 UTC timestamp")
    if record["created_by"].get("kind") not in {"operator", "import"}:
        raise ValueError("created_by.kind must be operator or import")
    if record["lifecycle_state"] not in {"active", "paused", "despawned", "retired"}:
        raise ValueError("unknown lifecycle state")
    display = record["display"]
    if not USERNAME_RE.fullmatch(display.get("username", "")):
        raise ValueError("display.username does not satisfy Minecraft username rules")
    skin = display.get("skin", {})
    if not SKIN_HASH_RE.fullmatch(skin.get("content_sha256", "")):
        raise ValueError("skin content hash must be lowercase SHA-256")
    if skin.get("model") not in {"classic", "slim"} or not skin.get("catalog_id"):
        raise ValueError("skin must name a catalog entry and supported model")
    refs = record["personal_state_refs"]
    expected_refs = {"minecraft_state", "memory", "relationships", "goals", "personality", "skills"}
    if set(refs) != expected_refs:
        raise ValueError("personal state reference set does not match v0")
    owners: set[str] = set()
    kinds: set[str] = set()
    for ref in refs.values():
        match = STATE_REF_RE.fullmatch(ref)
        if not match or match.group("owner") != record["agent_id"]:
            raise ValueError("personal state reference escapes its owning agent namespace")
        owners.add(match.group("owner"))
        kinds.add(match.group("kind"))
    if owners != {record["agent_id"]} or len(kinds) != len(expected_refs):
        raise ValueError("personal state references must be distinct and agent-scoped")


def clone_record(source: dict[str, Any], agent_id: str, profile_id: str, world_id: str) -> dict[str, Any]:
    clone = json.loads(json.dumps(source))
    old_id = source["agent_id"]
    clone["agent_id"] = agent_id
    clone["minecraft_profile_id"] = profile_id
    clone["world_binding_id"] = world_id
    clone["revision"] = 0
    clone["created_by"] = {"kind": "import"}
    clone["lineage"] = {"operation": "clone", "source_agent_id": old_id}
    clone["personal_state_refs"] = {
        key: value.replace(f"/agent/{old_id}/", f"/agent/{agent_id}/")
        for key, value in source["personal_state_refs"].items()
    }
    validate_record(clone)
    return clone


def transition_allowed(old: str, new: str) -> bool:
    allowed = {
        "active": {"paused", "despawned", "retired"},
        "paused": {"active", "despawned", "retired"},
        "despawned": {"active", "paused", "retired"},
        "retired": set(),
    }
    return new in allowed.get(old, set())


def main() -> int:
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    if schema.get("$id") != "urn:mni:agent-identity:v0":
        raise ValueError("identity schema identifier changed unexpectedly")
    with EXAMPLE_PATH.open("r", encoding="utf-8") as f:
        record = json.load(f)
    validate_record(record)

    round_trip = json.loads(json.dumps(record, sort_keys=True))
    if round_trip != record:
        raise AssertionError("identity JSON serialization round trip changed the record")

    second = clone_record(
        record,
        "380260e6-3b4f-4651-8c93-130742e7e952",
        "02c20892-a7ee-4e52-84bc-eb363099acdb",
        "104a01f8-0ad2-4e69-9bef-d7ca35c23cb1",
    )
    if set(record["personal_state_refs"].values()) & set(second["personal_state_refs"].values()):
        raise AssertionError("clone shares mutable state references with its source")
    invalid = json.loads(json.dumps(record))
    invalid["personal_state_refs"]["memory"] = second["personal_state_refs"]["memory"]
    try:
        validate_record(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("cross-agent state reference was accepted")
    if not transition_allowed("despawned", "active") or transition_allowed("retired", "active"):
        raise AssertionError("lifecycle transition rules do not preserve retired identity")
    print("agent identity contract: ok (schema metadata, ownership, clone remap, JSON round trip)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

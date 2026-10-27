#!/usr/bin/env python3
"""Fail-closed, offline data-use preflight. Never deletes files or trains models."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.validate_observation_contract import validate_json_schema

SCHEMA_PATH = ROOT / "docs" / "data" / "dataset-manifest.schema.json"
USES = {
    "collect", "store", "inspect", "train", "evaluate", "derive", "publish",
    "redistribute_raw", "redistribute_derived", "release_weights",
}


def manifest_errors(manifest: Any) -> list[str]:
    with SCHEMA_PATH.open(encoding="utf-8") as stream:
        schema = json.load(stream)
    return validate_json_schema(manifest, schema, schema)


def expiry_valid(expires_at: str | None, now: datetime) -> bool:
    if expires_at is None:
        return True
    try:
        parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        return parsed.tzinfo is not None and parsed > now
    except (ValueError, TypeError, OverflowError):
        return False


def authorize_use(
    manifests: dict[str, dict[str, Any]],
    artifact_id: str,
    purpose: str,
    *,
    now: datetime | None = None,
) -> tuple[bool, str]:
    """Validate requested use across the entire source lineage.

    A positive result only validates *declared* permission metadata. It is not
    proof that source rights or recorded consent were independently verified.
    """
    if purpose not in USES:
        return False, "unsupported_use"
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    visited: set[str] = set()
    active: set[str] = set()

    def visit(identifier: str) -> str | None:
        if identifier in active:
            return "lineage_cycle"
        if identifier in visited:
            return None
        manifest = manifests.get(identifier)
        if manifest is None:
            return "missing_lineage"
        if manifest_errors(manifest) or manifest["artifact_id"] != identifier:
            return "invalid_manifest"
        active.add(identifier)
        if manifest["review"]["status"] != "approved":
            return "review_not_approved"
        if purpose not in manifest["review"]["approved_uses"]:
            return "use_not_approved"
        retention = manifest["retention"]
        if retention["deleted_at"] is not None:
            return "deleted_artifact"
        if retention["deletion_requested"]:
            return "deletion_requested"
        if not expiry_valid(retention["expires_at"], current):
            return "retention_expired_or_invalid"
        consent = manifest["consent"]
        if consent["status"] in ("withdrawn", "unknown"):
            return "consent_unavailable"
        human = (manifest["origin"] == "human_gameplay"
                 or manifest["personal_data"]["contains_identifiers"]
                 or manifest["personal_data"]["contains_chat"])
        if human and (consent["status"] != "granted" or not consent["record_id"]):
            return "consent_unavailable"
        if consent["status"] == "granted" and purpose not in consent["permitted_uses"]:
            return "consent_does_not_cover_use"
        if manifest["personal_data"]["contains_chat"] and not manifest["personal_data"]["chat_opt_in"]:
            return "chat_opt_in_missing"
        sources = manifest["lineage"]["source_ids"]
        if manifest["origin"] == "derived" and not sources:
            return "missing_lineage"
        for parent in sources:
            reason = visit(parent)
            if reason is not None:
                return reason
        active.remove(identifier)
        visited.add(identifier)
        return None

    reason = visit(artifact_id)
    return (reason is None, reason or "approved_declared_metadata_only")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("collection", type=Path, help="JSON object mapping artifact IDs to manifests")
    p.add_argument("--artifact", required=True)
    p.add_argument("--use", required=True, choices=sorted(USES))
    args = p.parse_args()
    with args.collection.open(encoding="utf-8") as stream:
        manifests = json.load(stream)
    if not isinstance(manifests, dict):
        print("invalid manifest collection", file=sys.stderr)
        return 2
    allowed, reason = authorize_use(manifests, args.artifact, args.use)
    print(reason)
    return 0 if allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())

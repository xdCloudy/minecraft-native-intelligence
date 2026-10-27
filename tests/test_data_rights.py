"""Purpose-specific consent and lineage preflight using synthetic metadata only."""
from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone

from scripts.validate_data_rights import authorize_use, manifest_errors

NOW = datetime(2026, 10, 27, tzinfo=timezone.utc)


def manifest(identifier: str = "synthetic-001") -> dict:
    return {
        "schema_version": "dataset-manifest.v0",
        "artifact_id": identifier, "origin": "synthetic",
        "source": {
            "reference": "project-fixture", "version": "v1",
            "sha256": "a" * 64, "rights_holder": "project",
            "license_or_permission_ref": "project-reviewed",
        },
        "consent": {"status": "not_required", "record_id": None, "permitted_uses": []},
        "review": {
            "status": "approved", "reviewer": "fixture-reviewer",
            "reviewed_at": "2026-10-26T00:00:00Z",
            "approved_uses": ["train", "evaluate", "derive", "store"],
        },
        "personal_data": {
            "contains_identifiers": False, "contains_chat": False, "chat_opt_in": False,
        },
        "retention": {
            "expires_at": "2027-10-27T00:00:00Z",
            "deletion_requested": False, "deleted_at": None,
        },
        "lineage": {"source_ids": [], "transformation_ref": None},
    }


def allowed(items: dict, identifier: str = "synthetic-001", purpose: str = "train") -> tuple[bool, str]:
    return authorize_use(items, identifier, purpose, now=NOW)


class DataRightsTests(unittest.TestCase):
    def test_synthetic_approved_training(self):
        item = manifest()
        self.assertEqual([], manifest_errors(item))
        self.assertEqual((True, "approved_declared_metadata_only"), allowed({"synthetic-001": item}))

    def test_no_implicit_redistribution_from_training_rights(self):
        item = manifest()
        self.assertEqual("use_not_approved", allowed({item["artifact_id"]: item}, purpose="redistribute_raw")[1])

    def test_denies_unreviewed_or_rejected_source(self):
        for status in ("rejected", "pending"):
            item = manifest()
            item["review"]["status"] = status
            self.assertEqual("review_not_approved", allowed({item["artifact_id"]: item})[1])

    def test_deletion_request_or_deleted_artifact_blocks_reuse(self):
        item = manifest()
        item["retention"]["deletion_requested"] = True
        self.assertEqual("deletion_requested", allowed({item["artifact_id"]: item})[1])
        item["retention"]["deletion_requested"] = False
        item["retention"]["deleted_at"] = "2026-10-26T00:00:00Z"
        self.assertEqual("deleted_artifact", allowed({item["artifact_id"]: item})[1])

    def test_withdrawal_reaches_derived_children(self):
        parent = manifest()
        parent["origin"] = "human_gameplay"
        parent["consent"] = {
            "status": "granted", "record_id": "consent-v1",
            "permitted_uses": ["train", "derive"],
        }
        child = manifest("derived-001")
        child["origin"] = "derived"
        child["lineage"] = {
            "source_ids": ["synthetic-001"], "transformation_ref": "transform-v1",
        }
        items = {"synthetic-001": parent, "derived-001": child}
        self.assertTrue(allowed(items, "derived-001")[0])
        parent["consent"]["status"] = "withdrawn"
        self.assertEqual("consent_unavailable", allowed(items, "derived-001")[1])

    def test_chat_requires_separate_opt_in(self):
        item = manifest()
        item["origin"] = "human_gameplay"
        item["personal_data"]["contains_chat"] = True
        item["consent"] = {"status": "granted", "record_id": "v1", "permitted_uses": ["train"]}
        self.assertEqual("chat_opt_in_missing", allowed({item["artifact_id"]: item})[1])
        item["personal_data"]["chat_opt_in"] = True
        self.assertTrue(allowed({item["artifact_id"]: item})[0])

    def test_human_data_requires_specific_consent_and_use(self):
        item = manifest()
        item["origin"] = "human_gameplay"
        self.assertEqual("consent_unavailable", allowed({item["artifact_id"]: item})[1])
        item["consent"] = {"status": "granted", "record_id": "v1", "permitted_uses": ["evaluate"]}
        self.assertEqual("consent_does_not_cover_use", allowed({item["artifact_id"]: item})[1])

    def test_retention_expiry_and_invalid_timestamp_deny(self):
        item = manifest()
        for date in ("2026-10-26T00:00:00Z", "not-a-time", "2027-01-01"):
            item["retention"]["expires_at"] = date
            self.assertEqual("retention_expired_or_invalid", allowed({item["artifact_id"]: item})[1])

    def test_missing_lineage_and_cycles_fail(self):
        child = manifest("derived-001")
        child["origin"] = "derived"
        child["lineage"]["source_ids"] = ["missing-001"]
        self.assertEqual("missing_lineage", allowed({"derived-001": child}, "derived-001")[1])
        child["lineage"]["source_ids"] = ["derived-001"]
        self.assertEqual("lineage_cycle", allowed({"derived-001": child}, "derived-001")[1])

    def test_invalid_schema_or_mismatched_id_denied(self):
        item = manifest()
        invalid = copy.deepcopy(item)
        invalid["source"]["sha256"] = "invalid-hash"
        self.assertEqual("invalid_manifest", allowed({"synthetic-001": invalid})[1])
        self.assertEqual("invalid_manifest", allowed({"other-001": item}, "other-001")[1])

    def test_no_unknown_permissions(self):
        item = manifest()
        self.assertEqual("unsupported_use", allowed({item["artifact_id"]: item}, purpose="execute_code")[1])


if __name__ == "__main__":
    unittest.main()

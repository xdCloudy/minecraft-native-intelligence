"""Offline, deterministic checks for issue mapping and execution prioritisation."""
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("backlog", ROOT / "tools/backlog.py")
assert spec and spec.loader
backlog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backlog)


class BacklogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.rows, cls.groups, cls.overrides = backlog.load()
        cls.by_key, cls.member, cls.deps, cls.gates = backlog.graph(
            cls.data, cls.rows, cls.groups, cls.overrides
        )

    def test_every_canonical_requirement_maps_once(self):
        self.assertEqual(len(self.rows), 330)
        self.assertEqual(len(self.member), 330)
        self.assertEqual(set(self.member), set(self.rows))
        self.assertGreater(len(self.groups), 15)

    def test_duplicate_and_missing_coverage_are_rejected(self):
        duplicate = copy.deepcopy(self.groups)
        duplicate[0]["matrix_ids"] += " " + duplicate[1]["matrix_ids"].split()[0]
        with self.assertRaisesRegex(backlog.BacklogError, "Duplicate matrix coverage"):
            backlog.graph(self.data, self.rows, duplicate, self.overrides)
        missing = copy.deepcopy(self.groups)
        missing[0]["matrix_ids"] = " ".join(missing[0]["matrix_ids"].split()[1:])
        with self.assertRaisesRegex(backlog.BacklogError, "Missing matrix coverage"):
            backlog.graph(self.data, self.rows, missing, self.overrides)

    def test_cyclic_dependencies_are_rejected(self):
        circular = self.overrides + [
            {"group": "mi-platform", "blocked_by": "mi-lifecycle"}
        ]
        with self.assertRaisesRegex(backlog.BacklogError, "Cycle in issue group graph"):
            backlog.graph(self.data, self.rows, self.groups, circular)

    def test_issue_markers_must_be_unique_and_known(self):
        issue = {"number": 200, "state": "open", "body": "<!-- mni-backlog-group:mi-platform -->"}
        mapped, epics = backlog.issue_index([issue], self.groups)
        self.assertEqual(mapped["mi-platform"]["number"], 200)
        self.assertEqual(epics, {})
        with self.assertRaisesRegex(backlog.BacklogError, "duplicate GitHub group marker"):
            backlog.issue_index([issue, issue], self.groups)

    def test_missing_blocker_never_becomes_ready(self):
        mapped = {
            "mi-platform": {"number": 200, "state": "open"},
            "mi-lifecycle": {"number": 201, "state": "open"},
        }
        scores = {row["key"]: row for row in backlog.rankings(
            self.data, self.by_key, self.deps, self.gates, mapped
        )}
        self.assertEqual(scores["mi-platform"]["readiness"], "ready")
        self.assertEqual(scores["mi-lifecycle"]["readiness"], "blocked")
        self.assertIn("mi-platform", scores["mi-lifecycle"]["blockedBy"])

    def test_closure_is_not_claimed_capability_evidence(self):
        mapped = {"mi-platform": {"number": 200, "state": "closed"}}
        scores = {row["key"]: row for row in backlog.rankings(
            self.data, self.by_key, self.deps, self.gates, mapped
        )}
        self.assertEqual(scores["mi-platform"]["readiness"], "closed_needs_evidence_review")
        self.assertEqual(self.rows["MI-01"][1]["status"]["implementation"], "not_implemented")

    def test_issue_body_keeps_matrix_links_and_acceptance(self):
        issue = backlog.render_issue(
            self.by_key["mi-platform"], self.rows, self.deps, self.gates,
            self.by_key, {}, {}
        )
        self.assertIn("<!-- mni-backlog-group:mi-platform -->", issue)
        self.assertIn("MI-01", issue)
        self.assertIn("acceptance criteria", issue)
        self.assertIn("Blocked by", issue)


if __name__ == "__main__":
    unittest.main()

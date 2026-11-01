"""Synthetic-only paired binary audit regressions; not benchmark results."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.paired_binary_evaluation import EvidenceError, compare, exact_mcnemar_p_value

FIXTURE = Path(__file__).resolve().parents[1] / "docs" / "evaluation" / "example-result.json"


def make_run(run_id: str, values: list[bool]) -> dict:
    run = json.loads(FIXTURE.read_text(encoding="utf-8"))
    prototype = run["trials"][0]
    run["run_id"] = run_id
    run["run_status"] = "completed"
    run["trials"] = []
    for index, value in enumerate(values):
        trial = copy.deepcopy(prototype)
        trial["trial_id"] = f"{run_id}-seed-{index}"
        trial["seed"] = 1000 + index
        trial["repetition_index"] = 0
        trial["attempt"] = 0
        trial["metrics"] = {"primary_success": value}
        trial["artifact_ids"] = []
        run["trials"].append(trial)
    run["summary"] = {
        "trial_count": len(values),
        "status_counts": {"completed": len(values)},
        "metrics": [{"id": "primary_success", "n": len(values), "aggregation": "count", "value": sum(values)}],
    }
    return run


class PairedBinaryEvaluationTests(unittest.TestCase):
    def test_exact_p_for_six_discordant_pairs(self):
        self.assertEqual(0.03125, exact_mcnemar_p_value(6, 0))
        self.assertEqual(1.0, exact_mcnemar_p_value(0, 0))
        self.assertEqual(1.0, exact_mcnemar_p_value(1, 1))

    def test_valid_paired_exploratory_audit(self):
        result = compare(make_run("run-left", [True, False, True, False]),
                         make_run("run-right", [False, False, True, True]), "primary_success")
        self.assertEqual(4, result["paired_trial_count"])
        self.assertEqual(1, result["both_success"])
        self.assertEqual(1, result["left_only_success"])
        self.assertEqual(1, result["right_only_success"])
        self.assertEqual(1, result["neither_success"])
        self.assertEqual(1.0, result["mcnemar_exact_two_sided_p"])
        self.assertEqual(0, result["paired_rate_difference"])
        self.assertTrue(result["synthetic_only"])
        self.assertIn("Exploratory", result["interpretation"])

    def test_same_seed_different_order_is_paired(self):
        left = make_run("run-left", [True, False, True])
        right = make_run("run-right", [True, False, True])
        right["trials"].reverse()
        self.assertEqual(3, compare(left, right, "primary_success")["paired_trial_count"])

    def test_reject_missing_trial_no_survivorship_bias(self):
        left = make_run("run-left", [True, False])
        right = make_run("run-right", [True, False])
        right["trials"][1]["seed"] = 2000
        with self.assertRaisesRegex(EvidenceError, "coverage"):
            compare(left, right, "primary_success")

    def test_reject_non_boolean_metric(self):
        left = make_run("run-left", [True, False])
        right = make_run("run-right", [True, False])
        right["trials"][0]["metrics"]["primary_success"] = 1
        with self.assertRaisesRegex(EvidenceError, "non-boolean"):
            compare(left, right, "primary_success")

    def test_reject_missing_metric(self):
        left = make_run("run-left", [True])
        right = make_run("run-right", [False])
        del right["trials"][0]["metrics"]["primary_success"]
        with self.assertRaisesRegex(EvidenceError, "missing"):
            compare(left, right, "primary_success")

    def test_reject_attempted_retry(self):
        left = make_run("run-left", [True])
        right = make_run("run-right", [False])
        right["trials"][0]["attempt"] = 1
        with self.assertRaisesRegex(EvidenceError, "retries"):
            compare(left, right, "primary_success")

    def test_reject_failed_trial_even_if_metric_present(self):
        left = make_run("run-left", [True])
        right = make_run("run-right", [False])
        right["trials"][0]["status"] = "timeout"
        right["summary"]["status_counts"] = {"timeout": 1}
        with self.assertRaisesRegex(EvidenceError, "failed"):
            compare(left, right, "primary_success")

    def test_reject_partial_run(self):
        left = make_run("run-left", [True])
        right = make_run("run-right", [False])
        right["run_status"] = "partial"
        with self.assertRaisesRegex(EvidenceError, "incomplete"):
            compare(left, right, "primary_success")

    def test_reject_privileged_policy_leak(self):
        left = make_run("run-left", [True])
        right = make_run("run-right", [True])
        right["actual_privileged_inputs"][0]["used_by_policy"] = True
        with self.assertRaisesRegex(EvidenceError, "privileged"):
            compare(left, right, "primary_success")

    def test_reject_unacknowledged_intervention(self):
        left = make_run("run-left", [True])
        right = make_run("run-right", [True])
        right["trials"][0]["interventions"] = ["operator nudge"]
        with self.assertRaisesRegex(EvidenceError, "intervened"):
            compare(left, right, "primary_success")

    def test_reject_scenario_mismatch(self):
        left = make_run("run-left", [True])
        right = make_run("run-right", [True])
        right["scenario"]["sha256"] = "b" * 64
        with self.assertRaisesRegex(EvidenceError, "scenario"):
            compare(left, right, "primary_success")

    def test_reject_forged_summary(self):
        left = make_run("run-left", [True])
        right = make_run("run-right", [False])
        right["summary"]["status_counts"] = {"completed": 9}
        with self.assertRaisesRegex(EvidenceError, "summary"):
            compare(left, right, "primary_success")

    def test_reject_cross_type_seed_equivalence(self):
        left = make_run("run-left", [True])
        right = make_run("run-right", [True])
        right["trials"][0]["seed"] = str(left["trials"][0]["seed"])
        with self.assertRaisesRegex(EvidenceError, "coverage"):
            compare(left, right, "primary_success")

    def test_reject_duplicate_attempt(self):
        left = make_run("run-left", [True])
        right = make_run("run-right", [True])
        right["trials"].append(copy.deepcopy(right["trials"][0]))
        right["summary"]["trial_count"] = 2
        right["summary"]["status_counts"] = {"completed": 2}
        with self.assertRaisesRegex(EvidenceError, "duplicate"):
            compare(left, right, "primary_success")


if __name__ == "__main__":
    unittest.main()

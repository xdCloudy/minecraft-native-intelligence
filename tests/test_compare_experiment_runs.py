"""Prevent experiment comparison from hiding failed, reordered or duplicate retries."""
from __future__ import annotations

import copy
import unittest

from scripts.compare_experiment_runs import compare, final_trials, trial_histories


def trial(attempt: int, status: str, seed: int = 8) -> dict:
    return {
        "variant_id": "candidate", "seed": seed, "repetition_index": 0,
        "attempt": attempt, "status": status,
    }


def run(trials: list[dict], run_id: str = "r1") -> dict:
    return {
        "schema_version": "experiment.run.v1",
        "run_id": run_id, "experiment_id": "retries",
        "experiment_manifest_sha256": "sha",
        "scenario": {"scenario_id": "s"},
        "trials": trials,
        "summary": {},
    }


class ComparisonRetryIntegrityTests(unittest.TestCase):
    def test_out_of_order_retries_choose_highest_attempt(self):
        record = run([trial(1, "completed"), trial(0, "failed")])
        self.assertEqual("completed", final_trials(record)["candidate|8|0"]["status"])

    def test_retains_failed_attempt_even_if_final_status_matches(self):
        left = run([trial(0, "failed"), trial(1, "completed")])
        right = run([trial(0, "completed")], "r2")
        result = compare(left, right)
        self.assertEqual([], result["logical_trial_status_changes"])
        changes = result["logical_trial_attempt_history_changes"]
        self.assertEqual(1, len(changes))
        self.assertEqual(["failed", "completed"], [x["status"] for x in changes[0]["left_attempts"]])
        self.assertEqual(["completed"], [x["status"] for x in changes[0]["right_attempts"]])

    def test_missing_trial_is_not_interpreted_as_success(self):
        result = compare(run([trial(0, "failed")]), run([], "r2"))
        self.assertEqual(None, result["logical_trial_status_changes"][0]["right_status"])
        self.assertEqual([], result["logical_trial_attempt_history_changes"][0]["right_attempts"])

    def test_duplicate_retry_index_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicate attempt"):
            trial_histories(run([trial(0, "failed"), trial(0, "completed")]))

    def test_missing_retry_record_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "missing attempt"):
            trial_histories(run([trial(0, "failed"), trial(2, "completed")]))

    def test_retry_after_success_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "retry after"):
            trial_histories(run([trial(0, "completed"), trial(1, "failed")]))

    def test_bad_attempt_type_fails_closed(self):
        for attempt in (True, -1, "1"):
            with self.subTest(attempt=attempt):
                with self.assertRaisesRegex(ValueError, "nonnegative integer"):
                    trial_histories(run([trial(attempt, "failed")]))

    def test_compare_does_not_mutate_source_trials(self):
        a = run([trial(1, "completed"), trial(0, "failed")])
        saved = copy.deepcopy(a)
        compare(a, run([trial(0, "failed"), trial(1, "completed")], "r2"))
        self.assertEqual(saved, a)


if __name__ == "__main__":
    unittest.main()

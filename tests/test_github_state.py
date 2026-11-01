"""Offline tests for live GitHub issue and PR reconciliation."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_github_state", ROOT / "tools/check_github_state.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class GitHubStateTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "githubState": {
                "openIssueNumbers": [],
                "openPullRequestNumbers": [],
            },
            "unmergedWork": [{"id": "PR-122", "state": "closed"}],
        }

    def test_empty_state_matches(self):
        self.assertEqual(checker.mismatches(self.data, [], []), [])

    def test_equal_count_but_different_issue_is_detected(self):
        self.data["githubState"]["openIssueNumbers"] = [1]
        self.assertTrue(checker.mismatches(self.data, [2], []))

    def test_pr_reopen_is_detected_even_when_snapshot_unchanged(self):
        self.assertTrue(checker.mismatches(self.data, [], [122]))

    def test_issue_endpoint_filters_pull_requests_and_paginates(self):
        first = [{"number": n} for n in range(1, 100)] + [
            {"number": 100, "pull_request": {"url": "https://example.org"}}
        ]
        second = [{"number": 101}]
        with patch.object(checker, "api_page", side_effect=[first, second]) as api:
            self.assertEqual(checker.open_numbers("xdCloudy/minecraft-native-intelligence", "issues", None),
                             list(range(1, 100)) + [101])
            self.assertEqual(api.call_count, 2)


if __name__ == "__main__":
    unittest.main()

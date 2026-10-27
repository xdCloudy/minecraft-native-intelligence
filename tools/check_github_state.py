#!/usr/bin/env python3
"""Check the canonical GitHub issue/PR snapshot against live repository state.

This check is intentionally separate from deterministic progress generation.
It only reads GitHub metadata; closing an issue or passing CI never advances
an agent capability or marks a research question complete.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/progress/progress.json"


def api_page(url: str, token: str | None) -> list[dict]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "minecraft-native-intelligence-tracker",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=20) as response:
        result = json.load(response)
    if not isinstance(result, list):
        raise ValueError(f"Unexpected GitHub API response for {url}")
    return result


def open_numbers(repo: str, endpoint: str, token: str | None) -> list[int]:
    """Paginate to avoid treating the first 100 results as complete."""
    results: list[int] = []
    page = 1
    encoded = "/".join(quote(part, safe="") for part in repo.split("/"))
    while True:
        url = f"https://api.github.com/repos/{encoded}/{endpoint}?state=open&per_page=100&page={page}"
        batch = api_page(url, token)
        for record in batch:
            # GitHub's /issues endpoint includes pull requests.
            if endpoint == "issues" and "pull_request" in record:
                continue
            number = record.get("number")
            if not isinstance(number, int) or number < 1:
                raise ValueError(f"Malformed GitHub {endpoint} record")
            results.append(number)
        if len(batch) < 100:
            return sorted(results)
        page += 1


def mismatches(data: dict, issues: list[int], prs: list[int]) -> list[str]:
    audit = data["githubState"]
    problems = []
    for name, observed in (("Issue", issues), ("Pull request", prs)):
        kind = "Issue" if name == "Issue" else "PullRequest"
        expected = audit[f"open{kind}Numbers"]
        if sorted(expected) != sorted(observed):
            problems.append(f"{name} set changed: recorded {sorted(expected)}; live {sorted(observed)}")
    historical_open = sorted(int(record["id"][3:]) for record in data["unmergedWork"] if record["state"] == "open")
    if historical_open != sorted(prs):
        problems.append(f"Tracked PR states disagree with live open PRs: {historical_open} vs {sorted(prs)}")
    return problems


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    repo = data["githubState"]["repository"]
    token = os.getenv("GITHUB_TOKEN")
    try:
        issues = open_numbers(repo, "issues", token)
        prs = open_numbers(repo, "pulls", token)
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        print(f"Could not verify GitHub state: {error}", file=sys.stderr)
        return 2
    problems = mismatches(data, issues, prs)
    if problems:
        for problem in problems:
            print(f"TRACKER DRIFT: {problem}", file=sys.stderr)
        print("Refresh canonical GitHub state and regenerate the progress matrices.", file=sys.stderr)
        return 1
    print(f"GitHub tracker matches live state: {len(issues)} open issues; {len(prs)} open PRs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

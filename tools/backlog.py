#!/usr/bin/env python3
"""Validate MNI issue coverage and rank executable work from GitHub issue state.

The canonical progress tracker owns requirement evidence/status; GitHub issues
own execution state. The TSV defines issue-sized coverage packages, never
implementation credit. No command in this module mutates GitHub.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/progress/progress.json"
GROUPS = ROOT / "docs/backlog/groups.tsv"
OVERRIDES = ROOT / "docs/backlog/prerequisites.tsv"
REPO = "xdCloudy/minecraft-native-intelligence"
GROUP_MARKER = re.compile(r"<!-- mni-backlog-group:([a-z0-9-]+) -->")
EPIC_MARKER = re.compile(r"<!-- mni-backlog-epic:([a-z0-9-]+) -->")
VERIFIED_MARKER = re.compile(r"<!-- mni-acceptance-verified:([a-z0-9-]+) -->")
PRIORITY_WEIGHT = {"P0": 100, "P1": 60, "P2": 30, "P3": 10}


class BacklogError(ValueError):
    """Invalid mapping, graph, or GitHub snapshot."""


def load():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    rows = {}
    for domain in data["domains"]:
        rows.update((item["id"], (domain, item)) for item in domain["avenues"])
    domains = {domain["id"]: domain for domain in data["domains"]}
    for kind in ("modelCandidates", "trainingMethods"):
        for item in data[kind]:
            rows[item["id"]] = (domains[item["workstream"]], item)
    with GROUPS.open(encoding="utf-8", newline="") as stream:
        groups = list(csv.DictReader(stream, delimiter="\t"))
    with OVERRIDES.open(encoding="utf-8", newline="") as stream:
        override_rows = list(csv.DictReader(stream, delimiter="\t"))
    return data, rows, groups, override_rows


def graph(data, rows, groups, overrides):
    by_key = {g["key"]: g for g in groups}
    if len(by_key) != len(groups):
        raise BacklogError("Duplicate issue group key")
    member = {}
    for group in groups:
        if group["domain"] not in {d["id"] for d in data["domains"]}:
            raise BacklogError(f"Unknown domain in {group['key']}")
        if group["priority"] not in PRIORITY_WEIGHT:
            raise BacklogError(f"Invalid priority in {group['key']}")
        ids = group["matrix_ids"].split()
        if not ids:
            raise BacklogError(f"Empty group: {group['key']}")
        for ident in ids:
            if ident in member:
                raise BacklogError(f"Duplicate matrix coverage: {ident}")
            if ident not in rows:
                raise BacklogError(f"Unknown matrix ID: {ident}")
            if rows[ident][0]["id"] != group["domain"]:
                raise BacklogError(f"Wrong workstream: {ident}")
            member[ident] = group["key"]
    if set(member) != set(rows):
        raise BacklogError(f"Missing matrix coverage: {sorted(set(rows) - set(member))}")

    deps = {key: set() for key in by_key}
    milestone_gates = defaultdict(set)
    for ident, (_, item) in rows.items():
        key = member[ident]
        for required in item["dependencies"]:
            if required in member:
                other = member[required]
                if other != key:
                    deps[key].add(other)
            elif re.fullmatch(r"v\d+\.\d+", required):
                milestone_gates[key].add(required)
            else:
                raise BacklogError(f"{ident} references unrecognised dependency {required}")
    for override in overrides:
        key, required = override["group"], override["blocked_by"]
        if key not in by_key or required not in by_key or key == required:
            raise BacklogError(f"Invalid declared dependency {key} -> {required}")
        deps[key].add(required)

    done = set()
    visiting = []

    def walk(node):
        if node in visiting:
            raise BacklogError("Cycle in issue group graph: " + " -> ".join(visiting[visiting.index(node):] + [node]))
        if node in done:
            return
        visiting.append(node)
        for previous in sorted(deps[node]):
            walk(previous)
        visiting.pop()
        done.add(node)

    for key in by_key:
        walk(key)
    return by_key, member, deps, milestone_gates


def load_github_issues():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "mni-backlog-audit"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    collected = []
    for page in range(1, 25):
        url = f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=100&page={page}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as resp:
                batch = json.load(resp)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise BacklogError(f"GitHub fetch failed on page {page}: {exc}") from exc
        collected.extend(x for x in batch if "pull_request" not in x)
        if len(batch) < 100:
            return collected
    raise BacklogError("Issue audit exceeded 24 API pages; pagination must be extended")


def issue_index(issues, groups):
    keys = {g["key"] for g in groups}
    mapped = {}
    epics = {}
    for issue in issues:
        body = issue.get("body") or ""
        match = GROUP_MARKER.search(body)
        epic = EPIC_MARKER.search(body)
        if match:
            key = match.group(1)
            if key not in keys or key in mapped:
                raise BacklogError(f"Unknown or duplicate GitHub group marker: {key}")
            mapped[key] = issue
        if epic:
            domain = epic.group(1)
            if domain in epics:
                raise BacklogError(f"Duplicate workstream epic: {domain}")
            epics[domain] = issue
    return mapped, epics


def issue_number(issue):
    return issue.get("number", issue.get("issue_number"))


def issue_state(issue):
    return issue.get("state") or "unknown"


def rankings(data, by_key, deps, milestone_gates, mapped):
    reverse = {key: set() for key in by_key}
    for key, prerequisites in deps.items():
        for prerequisite in prerequisites:
            reverse[prerequisite].add(key)

    def downstream(key):
        seen = set()
        todo = list(reverse[key])
        while todo:
            node = todo.pop()
            if node in seen:
                continue
            seen.add(node)
            todo.extend(reverse[node])
        return seen

    # Administrative issue closure never clears a dependency. Require a
    # separately reviewed acceptance marker with provenance in the issue.
    completed = {
        key for key, issue in mapped.items()
        if issue_state(issue) == "closed"
        and VERIFIED_MARKER.search(issue.get("body") or "")
        and VERIFIED_MARKER.search(issue["body"]).group(1) == key
    }
    milestones = {m["id"]: m["status"] for m in data["milestones"]}
    output = []
    for key, group in by_key.items():
        depend = sorted(deps[key])
        missing = [p for p in depend if p not in completed]
        pending_gates = sorted(g for g in milestone_gates[key] if milestones.get(g) != "complete_as_documented")
        issue = mapped.get(key)
        state = issue_state(issue) if issue else "unpublished"
        # Closed alone is an administrative state, not proof of acceptance.
        # Keep it out of the work queue, but flag it for evidence review.
        ready = state == "open" and not missing and not pending_gates
        descendants = downstream(key)
        impact = sum(PRIORITY_WEIGHT[by_key[child]["priority"]] for child in descendants)
        score = PRIORITY_WEIGHT[group["priority"]] * 10 + impact
        output.append({
            "key": key,
            "number": issue_number(issue) if issue else None,
            "state": state,
            "readiness": "ready" if ready else (
                ("closed_verified" if key in completed else "closed_needs_evidence_review")
                if state == "closed" else "blocked"
            ),
            "priority": group["priority"],
            "score": score,
            "directUnlocks": len(reverse[key]),
            "transitiveUnlocks": len(descendants),
            "blockedBy": missing,
            "milestoneGates": pending_gates,
        })
    return sorted(output, key=lambda row: (-int(row["readiness"] == "ready"), -row["score"], row["key"]))


def render_issue(group, rows, deps, milestone_gates, by_key, mapped, epics):
    key = group["key"]
    items = [(ident, rows[ident][1]) for ident in group["matrix_ids"].split()]
    def ref(other):
        issue = mapped.get(other)
        return f"#{issue_number(issue)}" if issue else f"`{other}` (publication pending)"
    dependency_lines = [f"- {ref(other)} — {by_key[other]['title']}" for other in sorted(deps[key])]
    if not dependency_lines:
        dependency_lines = ["- None identified; verify current roadmap and technical prerequisites before implementation."]
    downstream_lines = [
        f"- {ref(child)} — {by_key[child]['title']}"
        for child in sorted(deps) if key in deps[child]
    ] or ["- No direct downstream issue packages have been identified."]
    gates = sorted(milestone_gates[key])
    if gates:
        dependency_lines += [f"- Milestone gate `{gate}` must have evidence-backed completion." for gate in gates]
    domain = rows[items[0][0]][0]
    milestones = sorted({m for _, item in items for m in item.get("milestones", [])})
    epic = epics.get(group["domain"])
    parent = f"#{issue_number(epic)}" if epic else "Pending workstream epic"
    lines = [
        f"<!-- mni-backlog-group:{key} -->",
        "## Objective",
        "",
        group["title"] + ".",
        "",
        f"**Workstream:** {domain['name']}  ",
        f"**Parent:** {parent}  ",
        f"**Priority:** {group['priority']}  ",
        f"**Roadmap milestones:** {', '.join(milestones) or 'unassigned'}  ",
        "**Execution readiness:** determined by the live dependency audit, not static labels. An open issue is ready only when its prerequisites have independently verified acceptance.",
        "",
        "## Independently tracked requirements",
        "",
        "| Matrix ID | Scope | Evidence gate |",
        "|---|---|---|",
    ]
    for ident, item in items:
        criteria = item["acceptanceCriteria"]
        first = criteria[0] if criteria else "Acceptance criteria must be specified in the canonical tracker"
        anchor = ident.lower()
        lines.append(f"| [`{ident}`](https://github.com/{REPO}/blob/main/docs/FEATURE_MATRIX.md#{anchor}) | {item['title']} | {first} |")
    lines += [
        "",
        "Each matrix ID retains its **own** complete acceptance criteria, dependencies, research protocol and evidence obligations. The issue is not complete until those obligations are met or a separately reviewed scope change is recorded.",
        "",
        "## Blocked by",
        "",
        *dependency_lines,
        "",
        "## Directly unlocks",
        "",
        *downstream_lines,
        "",
        "## Deliverables",
        "",
        "- [ ] Produce the bounded design, implementation or research artifacts for each listed ID.",
        "- [ ] Preserve failing and negative cases, competing approaches and explicit limitations.",
        "- [ ] Link tests, experiments, exact revisions and source evidence to the relevant canonical entries.",
        "- [ ] Verify every included acceptance criterion independently (including legal Survival gameplay when applicable).",
        "- [ ] Update canonical progress status **only** for actually evidenced work; regenerate the matrices.",
        "- [ ] Recheck downstream issue readiness and critical-path order.",
        "",
        "## Verification",
        "",
        f"Follow [testing](https://github.com/{REPO}/blob/main/docs/TESTING.md), [evaluation](https://github.com/{REPO}/blob/main/docs/EVALUATION.md), and [progress evidence rules](https://github.com/{REPO}/blob/main/docs/PROGRESS_WORKFLOW.md). Documentation, closed issues, design contracts and unmerged PRs are **not** implemented agent capabilities.",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="query the live GitHub issue API (read-only)")
    parser.add_argument("--issues", type=Path, help="JSON snapshot of REST GitHub issue objects (offline)")
    parser.add_argument("--issue-body", metavar="GROUP_KEY", help="render an issue body for a group")
    parser.add_argument("--refs-json", help="JSON of {groups:{key:number},epics:{domain:number}} for offline issue-body rendering")
    parser.add_argument("--json", action="store_true", help="emit machine-readable audit")
    parser.add_argument("--require-complete", action="store_true", help="fail if published GitHub package, epic, or dependency coverage is incomplete")
    args = parser.parse_args()
    if args.live and args.issues:
        parser.error("choose one of --live and --issues")
    try:
        data, rows, groups, overrides = load()
        by_key, member, deps, gates = graph(data, rows, groups, overrides)
        raw = load_github_issues() if args.live else (json.loads(args.issues.read_text(encoding="utf-8")) if args.issues else [])
        if isinstance(raw, dict):
            raw = raw.get("issues", [])
        mapped, epics = issue_index(raw, groups)
        if args.refs_json:
            refs = json.loads(args.refs_json)
            mapped = {key: {"number": number, "state": "open"} for key, number in refs.get("groups", {}).items()}
            epics = {domain: {"number": number, "state": "open"} for domain, number in refs.get("epics", {}).items()}
        if args.issue_body:
            if args.issue_body not in by_key:
                raise BacklogError(f"Unknown issue group: {args.issue_body}")
            print(render_issue(by_key[args.issue_body], rows, deps, gates, by_key, mapped, epics))
            return 0
        if not args.live and not args.issues:
            if args.require_complete:
                raise BacklogError("--require-complete needs --live or --issues")
            plan = {
                "canonicalItems": len(rows),
                "plannedItems": len(member),
                "packages": len(groups),
                "liveIssueCoverage": "not_queried",
            }
            print(json.dumps(plan, indent=2) if args.json else
                  f"Valid dependency plan: {len(member)}/{len(rows)} IDs in {len(groups)} packages; live issue state not queried.")
            return 0
        queue = rankings(data, by_key, deps, gates, mapped)
        missing_links = []
        for key, issue in mapped.items():
            body = issue.get("body") or ""
            for other in deps[key]:
                if other in mapped and f"#{issue_number(mapped[other])}" not in body:
                    missing_links.append(f"{key}: missing dependency link to {other}")
            parent = epics.get(by_key[key]["domain"])
            if parent and f"#{issue_number(parent)}" not in body:
                missing_links.append(f"{key}: missing parent epic link")
        for domain, epic in epics.items():
            body = epic.get("body") or ""
            for key, group in by_key.items():
                if group["domain"] == domain and key in mapped and f"#{issue_number(mapped[key])}" not in body:
                    missing_links.append(f"{domain}: epic missing child {key}")
        result = {
            "canonicalItems": len(rows),
            "mappedItems": sum(len(by_key[key]["matrix_ids"].split()) for key in mapped),
            "packages": len(groups),
            "publishedPackages": len(mapped),
            "epics": len(epics),
            "coveragePercent": round(100 * sum(len(by_key[key]["matrix_ids"].split()) for key in mapped) / len(rows), 2),
            "missingLinks": missing_links,
            "ready": [entry for entry in queue if entry["readiness"] == "ready"],
            "queue": queue,
        }
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"{len(rows)} canonical IDs / {len(groups)} packages / {len(mapped)} published / {result['coveragePercent']}% issue coverage")
            print(f"Workstream epics: {len(epics)}; verified-ready issue packages: {len(result['ready'])}")
            for entry in result["ready"][:20]:
                print(f"  #{entry['number']} {entry['key']}: priority {entry['priority']}, unlocks {entry['transitiveUnlocks']}")
            for problem in missing_links[:20]:
                print(f"  Broken relation: {problem}")
        if args.require_complete and (
            len(mapped) != len(groups)
            or len(epics) != len(data["domains"])
            or missing_links
        ):
            raise BacklogError(
                f"incomplete live coverage: packages {len(mapped)}/{len(groups)}, "
                f"epics {len(epics)}/{len(data['domains'])}, broken links {len(missing_links)}"
            )
        return 0
    except (BacklogError, OSError, KeyError, ValueError) as exc:
        print(f"backlog audit failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

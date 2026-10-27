#!/usr/bin/env python3
"""Validate local Markdown links and anchors without network access or dependencies.

This complements (but does not replace) lychee's remote-link checks in CI.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'(?<!!)\[[^\]]+\]\(([^\s)]+)(?:\s+"[^"]*")?\)')
HEADING = re.compile(r'^#{1,6}\s+(.+?)\s*#*\s*$')
EXPLICIT = re.compile(r'<a\s+[^>]*id=["\']([^"\']+)["\']', re.I)


def visible_lines(source: str):
    """Ignore Markdown code fences so command examples do not become links."""
    fence = None
    for line in source.splitlines():
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker[0], len(marker)
            elif marker[0] == fence[0] and len(marker) >= fence[1]:
                fence = None
            continue
        if fence is None:
            yield line


def anchors(source: str) -> set[str]:
    names = set()
    used = {}
    for line in visible_lines(source):
        names.update(EXPLICIT.findall(line))
        match = HEADING.match(line)
        if not match:
            continue
        title = re.sub(r'<[^>]+>', '', match.group(1))
        title = re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', title)
        title = re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')
        count = used.get(title, 0)
        used[title] = count + 1
        names.add(title if count == 0 else f'{title}-{count}')
    return names


def check(root: Path = ROOT) -> list[str]:
    files = sorted(root.rglob('*.md'))
    texts = {path: path.read_text(encoding='utf-8') for path in files}
    known = {path: anchors(source) for path, source in texts.items()}
    errors = []
    for path, source in texts.items():
        for number, line in enumerate(visible_lines(source), 1):
            for match in LINK.finditer(line):
                raw = match.group(1)
                parsed = urlsplit(raw)
                if parsed.scheme or parsed.netloc or raw.startswith('//'):
                    continue
                destination = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
                location = f'{path.relative_to(root)}: link {raw}'
                if not destination.is_relative_to(root.resolve()):
                    errors.append(f'{location}: escapes repository')
                elif not destination.exists():
                    errors.append(f'{location}: missing path')
                elif parsed.fragment and destination.suffix.lower() == '.md':
                    if unquote(parsed.fragment) not in known.get(destination, set()):
                        errors.append(f'{location}: missing anchor')
    return errors


if __name__ == '__main__':
    issues = check()
    for issue in issues:
        print(issue, file=sys.stderr)
    print(f'Local Markdown link check: {"failed" if issues else "passed"} ({len(issues)} issues).')
    raise SystemExit(bool(issues))

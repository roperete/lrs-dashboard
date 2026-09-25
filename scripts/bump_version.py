#!/usr/bin/env python3
"""Bump the version the page shows (sidebar and loading screen), and open its CHANGELOG section.

The number in the sidebar is how a reader tells whether the page in front of them already
contains a given change, so every push carries a new one. This does both edits together —
`v2.9.x` in src/version.ts (read by the sidebar and the loading screen) and a dated section at the top of
CHANGELOG.md — so the bump lands in the same commit as the work it describes.

    python3 scripts/bump_version.py --body "One line on what changed."
    python3 scripts/bump_version.py --version 2.10.0 --body-file notes.md
    python3 scripts/bump_version.py --show           # print the current version and stop

A version already present in the CHANGELOG is refused: two pushes must not share a number.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# The one place the version is written; the sidebar and the loading screen import it.
SIDEBAR = ROOT / "src" / "version.ts"
CHANGELOG = ROOT / "CHANGELOG.md"

VERSION_RE = re.compile(r"\bv(\d+\.\d+\.\d+)\b")
PLACEHOLDER = "_No summary written._"


def current_version(sidebar: Path = SIDEBAR) -> str:
    m = VERSION_RE.search(sidebar.read_text())
    if not m:
        raise ValueError(f"no vX.Y.Z in {sidebar}")
    return m.group(1)


def next_patch(version: str) -> str:
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def bump(sidebar: Path = SIDEBAR, changelog: Path = CHANGELOG, today: str | None = None,
         body: str | None = None, version: str | None = None) -> str:
    """Write the new version into both files and return it."""
    today = today or date.today().isoformat()
    new = version or next_patch(current_version(sidebar))
    text = changelog.read_text()
    if re.search(rf"^## v{re.escape(new)}\b", text, re.M):
        raise ValueError(f"v{new} already has a CHANGELOG section; pick a later version")

    sidebar.write_text(VERSION_RE.sub(f"v{new}", sidebar.read_text(), count=1))

    section = f"## v{new} — {today} (staging)\n\n{(body or PLACEHOLDER).strip()}\n\n"
    first = re.search(r"^## ", text, re.M)
    at = first.start() if first else len(text.rstrip()) + 1
    changelog.write_text(text[:at] + section + text[at:])
    return new


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", help="explicit version instead of the next patch")
    ap.add_argument("--body", help="the section body")
    ap.add_argument("--body-file", type=Path, help="read the section body from this file")
    ap.add_argument("--show", action="store_true", help="print the current version and exit")
    args = ap.parse_args()
    if args.show:
        print(current_version())
        return
    body = args.body
    if args.body_file:
        body = args.body_file.read_text()
    if not body:
        print("warning: no --body; the section will be a placeholder", file=sys.stderr)
    new = bump(body=body, version=args.version)
    print(f"v{new}  ({SIDEBAR.name} and {CHANGELOG.name} updated)")


if __name__ == "__main__":
    main()

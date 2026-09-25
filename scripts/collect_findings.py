#!/usr/bin/env python3
"""Assemble apply-ready findings from a provenance workflow's journal.

The workflow's own return value only contains groups where BOTH stages finished. When a
run dies on the session limit, the journal still holds every completed agent's result.
This reads `journal.jsonl`, pairs extractions with verifications by group_key, and writes
a findings file in the shape scripts/apply_provenance.py consumes:

    {"groups": [{"group_key": ..., "extraction": {...}, "verification": {...} | null}]}

Usage:
    python3 scripts/collect_findings.py <transcript dir or journal.jsonl> [--out documentation/provenance-findings-<label>.json]
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def pair_results(events: list[dict]) -> list[dict]:
    """Pair extraction and verification results by group_key. Later results for the same
    group replace earlier ones. Extractions without a verification are kept with
    verification=None; verifications without an extraction are dropped."""
    extractions: dict[str, dict] = {}
    verifications: dict[str, dict] = {}
    order: list[str] = []
    for e in events:
        if e.get("type") != "result":
            continue
        r = e.get("result")
        if not isinstance(r, dict) or not r.get("group_key"):
            continue
        key = r["group_key"]
        if "results" in r:
            if key not in extractions:
                order.append(key)
            extractions[key] = r
        elif "checks" in r:
            verifications[key] = r
    return [{"group_key": k, "extraction": extractions[k], "verification": verifications.get(k)} for k in order]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("journal", type=Path, help="workflow transcript directory or its journal.jsonl")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--label", default=date.today().isoformat())
    args = ap.parse_args()
    path = args.journal / "journal.jsonl" if args.journal.is_dir() else args.journal
    events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    groups = pair_results(events)
    out = args.out or (ROOT / "documentation" / f"provenance-findings-{args.label}.json")
    out.write_text(json.dumps({"groups": groups}, indent=1))
    n_ver = sum(1 for g in groups if g["verification"])
    n_sim = sum(len(g["extraction"].get("results", [])) for g in groups)
    print(f"{len(groups)} groups with an extraction ({n_ver} also verified), {n_sim} simulant results -> {out}")


if __name__ == "__main__":
    main()

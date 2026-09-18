#!/usr/bin/env python3
"""Per-simulant data-quality scorecard for lrs.sqlite.

Grades every simulant on (1) how well its numbers are sourced and
(2) whether the numbers are internally consistent, then assigns a
review priority.

Source tiers (best available reference for the simulant):
    A  manufacturer spec sheet / technical data sheet, or datasheet_url set
    B  primary characterisation paper (reference_type contains "composition")
    C  some other non-review paper
    D  only review / assessment / database-type sources
    E  no references at all

Priorities:
    P1  has composition numbers but only tier D/E sources  -> likely unsourced
    P2  integrity problem: sums out of range or NULL values
    P3  has composition numbers backed by tier A/B/C       -> verify vs source
    P4  no composition numbers                             -> nothing to verify

Usage:
    python3 scripts/scorecard.py                       # writes documentation/data-quality-scorecard.{md,csv}
    python3 scripts/scorecard.py --db other.sqlite --out-dir /tmp
"""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "lrs.sqlite"
DEFAULT_OUT = ROOT / "documentation"

SPEC_SHEET = re.compile(
    r"spec ?sheet|fact sheet|technical data sheet|safety data sheet|\bTDS\b|\bSDS\b|datasheet|"
    r"exolithsimulants\.com|spaceresourcetech|offplanetresearch|hispansion",
    re.I,
)
REVIEW_LIKE = re.compile(
    r"overview|review|assessment|user.?s guide|registry|database|dataset|wikipedia|catalog",
    re.I,
)
# Rows that are totals or aggregates, never summed.
NON_ADDITIVE_OXIDES = {"Sum", "Total", "LOI"}

CHEM_RANGE = (95.0, 102.0)
MIN_RANGE = (90.0, 101.0)


def _blob(ref: dict) -> str:
    return " ".join(str(ref.get(k) or "") for k in ("reference_text", "title", "url"))


def _source_tier(refs: list[dict], has_datasheet_url: bool) -> str:
    if has_datasheet_url or any(SPEC_SHEET.search(_blob(r)) for r in refs):
        return "A"
    if any("composition" in (r.get("reference_type") or "") and not REVIEW_LIKE.search(_blob(r)) for r in refs):
        return "B"
    if any(not REVIEW_LIKE.search(_blob(r)) for r in refs):
        return "C"
    if refs:
        return "D"
    return "E"


def _chem_sum(rows: list[dict]) -> tuple[float, int]:
    """Sum oxide wt% excluding totals and double-counted iron/alkali aggregates."""
    names = {r["component_name"] for r in rows}
    skip = set(NON_ADDITIVE_OXIDES)
    if "FeOT" in names and ("FeO" in names or "Fe2O3" in names):
        skip.add("FeOT")
    if "Fe2O3T" in names and ("FeO" in names or "Fe2O3" in names):
        skip.add("Fe2O3T")
    if "Na2O+K2O" in names and ("Na2O" in names or "K2O" in names):
        skip.add("Na2O+K2O")
    total = 0.0
    n = 0
    for r in rows:
        if r["component_name"] in NON_ADDITIVE_OXIDES:
            continue
        n += 1
        if r["component_name"] in skip or r["value_wt_pct"] is None:
            continue
        total += float(r["value_wt_pct"])
    return round(total, 2), n


def build_scorecard(db_path: Path | str) -> list[dict]:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row

    sims = [dict(r) for r in con.execute("SELECT * FROM simulants ORDER BY simulant_id")]
    refs_by = defaultdict(list)
    for r in con.execute("SELECT * FROM references_"):
        refs_by[r["simulant_id"]].append(dict(r))
    chem_by = defaultdict(list)
    for r in con.execute("SELECT * FROM chemical_compositions"):
        chem_by[r["simulant_id"]].append(dict(r))
    min_by = defaultdict(list)
    for r in con.execute("SELECT * FROM mineral_compositions"):
        min_by[r["simulant_id"]].append(dict(r))
    con.close()

    out = []
    for s in sims:
        sid = s["simulant_id"]
        refs = refs_by.get(sid, [])
        chem = chem_by.get(sid, [])
        mins = min_by.get(sid, [])
        issues: list[str] = []

        has_datasheet_url = bool(s.get("datasheet_url"))
        tier = _source_tier(refs, has_datasheet_url)

        chem_sum, n_oxides = _chem_sum(chem)
        chem_sum_ok = n_oxides == 0 or CHEM_RANGE[0] <= chem_sum <= CHEM_RANGE[1]
        if not chem_sum_ok:
            issues.append(f"oxide sum {chem_sum}% outside {CHEM_RANGE[0]:g}-{CHEM_RANGE[1]:g}%")

        min_sum = round(sum(float(m["value_pct"]) for m in mins if m["value_pct"] is not None), 2)
        n_minerals = len(mins)
        min_sum_ok = n_minerals == 0 or MIN_RANGE[0] <= min_sum <= MIN_RANGE[1]
        if not min_sum_ok:
            issues.append(f"mineral sum {min_sum}% outside {MIN_RANGE[0]:g}-{MIN_RANGE[1]:g}%")

        n_null = sum(1 for c in chem if c["value_wt_pct"] is None) + sum(1 for m in mins if m["value_pct"] is None)
        if n_null:
            issues.append(f"{n_null} composition rows with null value")

        has_composition = n_oxides > 0 or n_minerals > 0
        n_comp_refs = sum(1 for r in refs if "composition" in (r.get("reference_type") or ""))

        if has_composition and tier in ("D", "E"):
            priority = "P1"
            issues.append("composition numbers without a primary source")
        elif not chem_sum_ok or not min_sum_ok or n_null:
            priority = "P2"
        elif has_composition:
            priority = "P3"
        else:
            priority = "P4"

        out.append(
            {
                "simulant_id": sid,
                "name": s["name"],
                "institution": s.get("institution"),
                "availability": s.get("availability"),
                "n_oxides": n_oxides,
                "chem_sum": chem_sum,
                "chem_sum_ok": chem_sum_ok,
                "n_minerals": n_minerals,
                "min_sum": min_sum,
                "min_sum_ok": min_sum_ok,
                "n_null_values": n_null,
                "n_refs": len(refs),
                "n_comp_refs": n_comp_refs,
                "source_tier": tier,
                "has_datasheet_url": has_datasheet_url,
                "priority": priority,
                "issues": issues,
            }
        )
    return out


def write_csv(rows: list[dict], path: Path) -> None:
    fields = [k for k in rows[0].keys()] if rows else []
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({**r, "issues": "; ".join(r["issues"])})


def render_markdown(rows: list[dict]) -> str:
    n = len(rows)
    by_pri = defaultdict(int)
    by_tier = defaultdict(int)
    for r in rows:
        by_pri[r["priority"]] += 1
        by_tier[r["source_tier"]] += 1

    lines = ["# Data-quality scorecard", ""]
    lines.append(f"Generated from `lrs.sqlite` — {n} simulants.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Priority | Meaning | Simulants |")
    lines.append("|---|---|---|")
    meaning = {
        "P1": "composition numbers with only review/no sources (likely unsourced)",
        "P2": "integrity problem (sums out of range or null values)",
        "P3": "composition numbers with a spec sheet or primary paper — verify against it",
        "P4": "no composition numbers — nothing to verify",
    }
    for p in ("P1", "P2", "P3", "P4"):
        lines.append(f"| {p} | {meaning[p]} | {by_pri.get(p, 0)} |")
    lines.append("")
    lines.append("| Source tier | Simulants |")
    lines.append("|---|---|")
    tier_name = {"A": "spec sheet / datasheet", "B": "primary paper", "C": "other paper", "D": "review-type only", "E": "none"}
    for t in "ABCDE":
        lines.append(f"| {t} — {tier_name[t]} | {by_tier.get(t, 0)} |")
    lines.append("")
    lines.append("## Per simulant")
    lines.append("")
    lines.append("| Pri | ID | Name | Institution | Tier | Oxides (sum) | Minerals (sum) | Refs (comp) | Issues |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda r: (r["priority"], r["simulant_id"])):
        ox = f"{r['n_oxides']} ({r['chem_sum']:g})" if r["n_oxides"] else "—"
        mn = f"{r['n_minerals']} ({r['min_sum']:g})" if r["n_minerals"] else "—"
        lines.append(
            f"| {r['priority']} | {r['simulant_id']} | {r['name']} | {r['institution'] or ''} | {r['source_tier']} | "
            f"{ox} | {mn} | {r['n_refs']} ({r['n_comp_refs']}) | {'; '.join(r['issues'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    rows = build_scorecard(args.db)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(rows, args.out_dir / "data-quality-scorecard.csv")
    (args.out_dir / "data-quality-scorecard.md").write_text(render_markdown(rows))

    by_pri = defaultdict(int)
    for r in rows:
        by_pri[r["priority"]] += 1
    print(f"{len(rows)} simulants -> " + ", ".join(f"{p}: {by_pri[p]}" for p in ("P1", "P2", "P3", "P4")))
    print(f"wrote {args.out_dir / 'data-quality-scorecard.md'} and .csv")


if __name__ == "__main__":
    main()

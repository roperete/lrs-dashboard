#!/usr/bin/env python3
"""Set composition_status from the composition rows' own citations.

scripts/apply_provenance.py inserts oxide and mineral rows that two independent readers
agreed on, each with the reference_id of the document it was read from. This step makes
the simulant's status line agree with those rows: a composition whose every row cites a
document is `verified`, and the "Composition data source" line points at the document
most of the rows cite. The kind of that document sets the label and the review flag:

    datasheet                               -> manufacturer_datasheet
    report                                  -> agency_report
    composition | geotechnical | untyped    -> primary_paper
    review | general | usage                -> secondary_reproduction, needs_review = 1

A composition with any row lacking reference_id is left as it is, and a simulant already
`verified` (the 2026-09-21 sheet audit) is never touched.

Run:  python3 scripts/refresh_composition_status.py [--db lrs.sqlite]
"""

from __future__ import annotations

import argparse
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"

SECONDARY_TYPES = {"review", "general", "usage"}


def kind_for(reference_type: str | None) -> str:
    t = (reference_type or "").strip().lower()
    if t == "datasheet":
        return "manufacturer_datasheet"
    if t == "report":
        return "agency_report"
    if t in SECONDARY_TYPES:
        return "secondary_reproduction"
    return "primary_paper"


def _source_url(ref: sqlite3.Row) -> str | None:
    if ref["url"]:
        return ref["url"]
    if ref["doi"]:
        return "https://doi.org/" + ref["doi"].strip()
    return None


def refresh(db_path: Path | str) -> list[dict]:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    log: list[dict] = []
    sids = [r[0] for r in con.execute(
        "SELECT simulant_id FROM chemical_compositions UNION SELECT simulant_id FROM mineral_compositions ORDER BY 1")]
    for sid in sids:
        sim = con.execute("SELECT composition_status FROM simulants WHERE simulant_id=?", (sid,)).fetchone()
        if sim is None or sim["composition_status"] == "verified":
            continue
        cited = [r[0] for r in con.execute(
            "SELECT reference_id FROM chemical_compositions WHERE simulant_id=? "
            "UNION ALL SELECT reference_id FROM mineral_compositions WHERE simulant_id=?", (sid, sid))]
        if any(not c for c in cited):
            log.append({"simulant_id": sid, "outcome": "skipped: composition row without reference"})
            continue
        counts = Counter(cited)
        top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        ref = con.execute("SELECT * FROM references_ WHERE reference_id=?", (top,)).fetchone()
        if ref is None:
            log.append({"simulant_id": sid, "outcome": f"skipped: cited reference {top} not in references_"})
            continue
        kind = kind_for(ref["reference_type"])
        title = (ref["title"] or ref["reference_text"] or top).strip()[:200]
        needs_review = 1 if kind == "secondary_reproduction" else 0
        con.execute(
            "UPDATE simulants SET composition_status='verified', composition_source_title=?, composition_source_url=?, "
            "composition_source_kind=?, composition_needs_review=? WHERE simulant_id=?",
            (title, _source_url(ref), kind, needs_review, sid))
        log.append({"simulant_id": sid, "outcome": f"verified: {kind}", "reference_id": top, "rows": len(cited)})
    con.commit()
    con.close()
    return log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DB)
    args = ap.parse_args()
    for e in refresh(args.db):
        print(f"{e['simulant_id']}: {e['outcome']}" + (f" ({e['reference_id']}, {e['rows']} rows)" if "rows" in e else ""))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Repair identifiers in references_ that were stored truncated or dead.

* DOIs: six ASCE DOIs were cut at the first parenthesis ("10.1061/(ASCE") and one MDPI
  proceedings DOI no longer resolves. `doi_from_text` recovers the full DOI from the
  citation text; each recovered DOI is re-resolved at Crossref before it is written.
* URLs: replacements in URL_FIXES, each HEAD-checked before writing.

Every change is logged to documentation/reference-repair-log-<date>.json.

Usage:  python3 scripts/repair_references.py [--write]
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from check_references import crossref, head, title_similarity  # noqa: E402

DB = ROOT / "lrs.sqlite"

_DOI_START = re.compile(r"10\.\d{4,9}/")

# old (dead) URL -> live URL, each found by hand and HEAD-checked on 2026-09-22.
URL_FIXES: dict[str, str] = {
    # ISECG ISRU Technology Gap Assessment Report (April 2021): the stored filename never existed
    "https://www.globalspaceexploration.org/wordpress/wp-content/uploads/2021/04/ISRU-Gap-Assessment-Report-2021.pdf":
        "https://www.globalspaceexploration.org/wordpress/wp-content/uploads/2021/04/ISECG-ISRU-Technology-Gap-Assessment-Report-Apr-2021.pdf",
    # LEAG Simulant Working Group 2010: the presentation link is dead, the report it presented is live
    "https://www.lpi.usra.edu/meetings/leagilewg2010/presentations/stoeser.pdf":
        "https://www.lpi.usra.edu/leag/reports/SIM_SATReport2010.pdf",
}

# Explicit per-reference corrections that the citation text alone cannot yield.
# reference_id -> {field: (new value, reason)}; each DOI here was resolved at Crossref by hand.
EXPLICIT_FIXES: dict[str, dict[str, tuple[str, str]]] = {
    "R001": {"doi": ("10.1061/(ASCE)AS.1943-5525.0000428",
                     "citation text carries the DOI one digit short; Crossref bibliographic search for Bonanno & Bernold 2015 returns this DOI with the matching title")},
    "R081": {"doi": ("10.1061/(ASCE)AS.1943-5525.0000798",
                     "recovered from citation text; resolves to Ryu, Wang & Chang 2018 in J. Aerospace Eng."),
             "title": ("Development and Geotechnical Engineering Properties of KLS-1 Lunar Simulant",
                       "stored title did not match the paper the DOI and authors identify; replaced with the Crossref title")},
    "R112": {"title": ("Status of Lunar Regolith Simulants and Demand for Apollo Lunar Samples (Report of the LEAG Simulant Working Group, 2010)",
                       "the dead link was a presentation of this report; the report is the citable document"),
             "local_path": ("papers/LRS/LEAG-SIM-SAT2010_LunarRegolithSimulants.pdf",
                            "copy in DIRT/Sources, first page title confirmed")},
}


def doi_from_text(text: str | None) -> str | None:
    """Recover a full DOI from citation text. Handles the ASCE form with parentheses, a DOI
    wrapped across a line break after a period, and trailing punctuation."""
    if not text:
        return None
    m = _DOI_START.search(text)
    if not m:
        return None
    i = m.start()
    out = []
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            # a wrapped DOI continues after a period: "j. asr.2008" -> "j.asr.2008"
            if out and out[-1] == "." and i + 1 < n and text[i + 1].isalnum():
                i += 1
                continue
            break
        if ch in '"<>':
            break
        out.append(ch)
        i += 1
    doi = "".join(out)
    doi = doi.rstrip(".,;:")
    while doi.endswith(")") and doi.count(")") > doi.count("("):
        doi = doi[:-1].rstrip(".,;:")
    return doi or None


def looks_truncated(doi: str | None) -> bool:
    if not doi:
        return False
    d = doi.strip()
    return d.endswith("(") or d.count("(") != d.count(")") or d.endswith("/") or len(d) < 12


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    refs = [dict(r) for r in con.execute("SELECT * FROM references_ ORDER BY reference_id")]
    log = []

    for r in refs:
        stored = (r.get("doi") or "").strip()
        if not looks_truncated(stored):
            continue
        cand = doi_from_text(r.get("reference_text") or r.get("title") or "")
        if not cand or cand == stored:
            log.append({"reference_id": r["reference_id"], "field": "doi", "old": stored, "new": None,
                        "outcome": "no fuller DOI in citation text"})
            continue
        cr = crossref(cand)
        if not cr or "error" in cr:
            log.append({"reference_id": r["reference_id"], "field": "doi", "old": stored, "new": cand,
                        "outcome": f"candidate does not resolve: {cr.get('error') if cr else 'no response'}"})
            continue
        sim = title_similarity((r.get("title") or "") + " " + (r.get("reference_text") or ""), cr.get("title", ""))
        ok = sim >= 0.6
        log.append({"reference_id": r["reference_id"], "field": "doi", "old": stored, "new": cand,
                    "outcome": "resolves, title matches" if ok else f"resolves but title similarity {sim:.2f}",
                    "crossref_title": cr.get("title", "")})
        if ok and args.write:
            con.execute("UPDATE references_ SET doi=? WHERE reference_id=?", (cand, r["reference_id"]))

    for r in refs:
        url = (r.get("url") or "").strip()
        for old, new in URL_FIXES.items():
            if url.startswith(old) and url != new:
                status = head(new)
                ok = status.startswith("2") or status.startswith("3")
                log.append({"reference_id": r["reference_id"], "field": "url", "old": url, "new": new,
                            "outcome": f"replacement answers {status}" if ok else f"replacement NOT live: {status}"})
                if ok and args.write:
                    con.execute("UPDATE references_ SET url=? WHERE reference_id=?", (new, r["reference_id"]))

    # A url that is just the DOI in link form must follow the DOI once the DOI is repaired.
    for r in con.execute("SELECT reference_id, doi, url FROM references_ WHERE url LIKE 'https://doi.org/%' AND doi IS NOT NULL AND doi != ''").fetchall():
        rid, doi, url = r["reference_id"], r["doi"].strip(), r["url"].strip()
        want = "https://doi.org/" + doi
        if url != want and not looks_truncated(doi):
            log.append({"reference_id": rid, "field": "url", "old": url, "new": want, "outcome": "doi.org link re-derived from the repaired DOI"})
            if args.write:
                con.execute("UPDATE references_ SET url=? WHERE reference_id=?", (want, rid))

    have_cols = {r[1] for r in con.execute("PRAGMA table_info(references_)")}
    for rid, fixes in EXPLICIT_FIXES.items():
        row = con.execute("SELECT * FROM references_ WHERE reference_id=?", (rid,)).fetchone()
        if row is None:
            continue
        for field, (new, reason) in fixes.items():
            if field not in have_cols:
                continue
            old = row[field]
            if old == new:
                continue
            if field == "doi":
                cr = crossref(new)
                if not cr or "error" in cr:
                    log.append({"reference_id": rid, "field": field, "old": old, "new": new,
                                "outcome": f"explicit fix REJECTED, does not resolve: {cr.get('error') if cr else 'no response'}"})
                    continue
            log.append({"reference_id": rid, "field": field, "old": old, "new": new, "outcome": "explicit fix: " + reason})
            if args.write:
                con.execute(f"UPDATE references_ SET {field}=? WHERE reference_id=?", (new, rid))

    if args.write:
        con.commit()
    con.close()
    out = ROOT / "documentation" / f"reference-repair-log-{date.today().isoformat()}.json"
    out.write_text(json.dumps(log, indent=1))
    for e in log:
        print(f"  {e['reference_id']} {e['field']}: {str(e['old'])[:40]!r} -> {str(e['new'])[:60]!r}  [{e['outcome']}]")
    print(f"{len(log)} entries{' written' if args.write else ' (dry run)'} -> {out.name}")


if __name__ == "__main__":
    main()

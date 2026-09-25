#!/usr/bin/env python3
"""Does every reference in references_ exist, and is it what we say it is?

For each reference row:
  * DOI present  -> resolve at Crossref; compare the returned title with our stored
                    title / citation text; record the match score.
  * URL present  -> request it; record the HTTP status.
  * neither      -> flagged: nothing to check against.

Writes documentation/reference-check-<date>.json and prints a summary. Read-only.

Usage:  python3 scripts/check_references.py [--limit N]
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"
UA = "lrs-dashboard-reference-check/1.0 (mailto:contact@thespringinstitute.com)"


def norm_title(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def title_similarity(ours: str, theirs: str) -> float:
    """0..1. Our field may be a whole citation string, so also test whether their title
    is contained in ours; take the better of the two views."""
    a, b = norm_title(ours), norm_title(theirs)
    if not a or not b:
        return 0.0
    if b in a or a in b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def crossref(doi: str) -> dict | None:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi.strip(), safe="/:()")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            m = json.load(r)["message"]
            return {"title": (m.get("title") or [""])[0], "year": (m.get("issued", {}).get("date-parts") or [[None]])[0][0],
                    "container": (m.get("container-title") or [""])[0],
                    "authors": [a.get("family", "") for a in m.get("author", [])][:4]}
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}"}
    except Exception as e:  # noqa: BLE001
        return {"error": type(e).__name__}


def head(url: str) -> str:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return str(r.status)
    except urllib.error.HTTPError as e:
        if e.code in (403, 405):  # some hosts refuse HEAD; try GET
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=25) as r:
                    return str(r.status)
            except urllib.error.HTTPError as e2:
                return f"HTTP {e2.code}"
            except Exception as e2:  # noqa: BLE001
                return type(e2).__name__
        return f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return type(e).__name__


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    refs = [dict(r) for r in con.execute(
        "SELECT r.*, s.name AS simulant_name FROM references_ r JOIN simulants s USING(simulant_id) ORDER BY r.reference_id")]
    con.close()
    if args.limit:
        refs = refs[: args.limit]

    out = []
    doi_cache: dict[str, dict] = {}
    url_cache: dict[str, str] = {}
    for i, r in enumerate(refs, 1):
        rec = {"reference_id": r["reference_id"], "simulant_id": r["simulant_id"], "simulant": r["simulant_name"],
               "type": r.get("reference_type"), "doi": (r.get("doi") or "").strip(), "url": (r.get("url") or "").strip(),
               "stored": (r.get("title") or r.get("reference_text") or "")[:160]}
        ours = (r.get("title") or "") + " " + (r.get("reference_text") or "")
        if rec["doi"]:
            if rec["doi"] not in doi_cache:
                doi_cache[rec["doi"]] = crossref(rec["doi"]) or {"error": "no response"}
                time.sleep(0.15)
            cr = doi_cache[rec["doi"]]
            rec["crossref"] = cr
            if "error" in cr:
                rec["doi_status"] = "unresolved: " + cr["error"]
            else:
                sim = title_similarity(ours, cr.get("title", ""))
                rec["title_similarity"] = round(sim, 2)
                rec["doi_status"] = "matches" if sim >= 0.6 else "TITLE MISMATCH"
        if rec["url"] and not rec["url"].startswith("https://doi.org/" + rec["doi"]) if rec["doi"] else rec["url"]:
            if rec["url"] not in url_cache:
                url_cache[rec["url"]] = head(rec["url"])
                time.sleep(0.1)
            rec["url_status"] = url_cache[rec["url"]]
        if not rec["doi"] and not rec["url"]:
            rec["check"] = "nothing to check: no DOI, no URL"
        out.append(rec)
        if i % 20 == 0:
            print(f"  {i}/{len(refs)}")

    report = ROOT / "documentation" / f"reference-check-{date.today().isoformat()}.json"
    report.write_text(json.dumps(out, indent=1))

    n = len(out)
    with_doi = [r for r in out if r["doi"]]
    mism = [r for r in with_doi if r.get("doi_status") == "TITLE MISMATCH"]
    unres = [r for r in with_doi if str(r.get("doi_status", "")).startswith("unresolved")]
    with_url = [r for r in out if r.get("url_status")]
    dead = [r for r in with_url if not str(r["url_status"]).startswith("2") and not str(r["url_status"]).startswith("3")]
    none = [r for r in out if r.get("check")]
    print(f"\nreferences: {n}")
    print(f"  with DOI: {len(with_doi)}  -> resolve & title matches: {len(with_doi)-len(mism)-len(unres)}, TITLE MISMATCH: {len(mism)}, unresolved: {len(unres)}")
    print(f"  with URL checked: {len(with_url)} -> not OK: {len(dead)}")
    print(f"  nothing to check (no DOI, no URL): {len(none)}")
    for r in mism:
        print(f"  MISMATCH {r['reference_id']} {r['simulant']}: stored '{r['stored'][:70]}' | crossref '{r['crossref'].get('title','')[:70]}' ({r['title_similarity']})")
    for r in unres:
        print(f"  UNRESOLVED {r['reference_id']} {r['simulant']}: {r['doi']} -> {r['doi_status']}")
    for r in dead:
        print(f"  URL {r['url_status']:>10} {r['reference_id']} {r['simulant']}: {r['url'][:80]}")
    print(f"\nreport: {report}")


if __name__ == "__main__":
    main()

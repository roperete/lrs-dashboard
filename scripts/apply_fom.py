#!/usr/bin/env python3
"""Store Figures of Merit read from the documents that score simulants.

One reader per document extracted every FoM row — simulant, property, the lunar reference it
is scored against, the score as printed — and an independent checker confirmed or refuted
each. This stores the confirmed rows, one score per (simulant, property, reference), cited to
the document: the simulant's own reference row for it if one exists, else a new one. A score is
attached only to a simulant of exactly the printed name; derivatives ("processed for glass")
and names the database lacks are logged for a human, never guessed.

    python3 scripts/apply_fom.py --findings <workflow result json> [--write]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_value import parse_number  # noqa: E402
from provenance import ensure_provenance_schema  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"

KINDS = [("overall", r"overall|mean|average|total|combined"), ("mineralogy", r"miner|modal|phase"),
         ("composition", r"compos|chemi|oxide|bulk chem"), ("particle_size", r"size|psd|grain|granulo"),
         ("shape", r"shape|morpho|aspect|circular|roundness|angular"), ("density", r"densit")]


def property_kind(label: str) -> str:
    l = (label or "").lower()
    for kind, pat in KINDS:
        if re.search(pat, l):
            return kind
    return "other"


def _key(name: str) -> str:
    return re.sub(r"[\s_\-]", "", (name or "").lower())


def match_simulant(printed: str, names: dict) -> str | None:
    """The simulant of exactly this name (ignoring case, spaces and hyphens), or None.
    Anything extra in the printed name — a processing note, a sieve fraction — means a
    different product, so it does not match."""
    k = _key(printed)
    for name, sid in names.items():
        if _key(name) == k:
            return sid
    return None


def _norm(t):
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\[.*?\]", "", (t or "").lower()))


def reference_for(con, sid, reading, checked_on, quote) -> str:
    """The simulant's own reference row for this document, or a new one."""
    path = reading.get("document_path") or ""
    title = reading.get("document_title") or ""
    t = _norm(title)[:60]
    for rid, rtitle, rtext, lp in con.execute("SELECT reference_id, title, reference_text, local_path FROM references_ WHERE simulant_id=?", (sid,)):
        if path and lp and Path(lp).name == Path(path).name:
            return rid
        c = _norm(f"{rtitle or ''} {rtext or ''}")
        for probe in (_norm(rtitle)[:40], ):
            if len(probe) >= 25 and probe in _norm(title):
                return rid
        if len(t) >= 25 and t[:40] in c:
            return rid
    n = con.execute("SELECT count(*) FROM references_ WHERE reference_id LIKE ?", (f"RN-{sid}-%",)).fetchone()[0]
    rid = f"RN-{sid}-{n + 1}"
    while con.execute("SELECT 1 FROM references_ WHERE reference_id=?", (rid,)).fetchone():
        n += 1; rid = f"RN-{sid}-{n + 1}"
    con.execute("INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type, title, names_simulant, mention_quote, "
                "local_path, checked_on) VALUES (?,?,?,?,?,1,?,?,?)", (rid, sid, title, "report", title, quote, path or None, checked_on))
    return rid


def apply_document(con: sqlite3.Connection, res: dict, checked_on: str | None = None) -> list[dict]:
    ensure_provenance_schema(con)
    checked_on = checked_on or date.today().isoformat()
    reading, check = res["reading"], res.get("check") or {}
    names = {n: sid for sid, n in con.execute("SELECT simulant_id, name FROM simulants")}
    verdicts = {c["row"]: c["verdict"] for c in check.get("checks", [])}
    log: list[dict] = []
    doc = reading.get("document_key") or res.get("doc", {}).get("key")
    for i, r in enumerate(reading.get("rows", [])):
        base = {"document": doc, "simulant": r["simulant"], "property": r["property"], "score": r["score"]}
        if verdicts.get(i) != "CONFIRMED":
            log.append({**base, "outcome": "not stored: refuted by the checker" if verdicts.get(i) == "REFUTED" else "not stored: the checker could not confirm"})
            continue
        sid = match_simulant(r["simulant"], names)
        if not sid:
            log.append({**base, "outcome": "not stored: no simulant of exactly this name"})
            continue
        p = parse_number(r["score"])
        if p is None:
            log.append({**base, "outcome": "not stored: the score is not a single number"})
            continue
        rid = reference_for(con, sid, reading, checked_on, r["quote"])
        ref_sample = (r.get("reference") or "").strip() or None
        fid = f"FOM-{sid}-{doc}-{_key(r['property'])[:20]}-{_key(ref_sample or 'na')[:20]}"
        have = con.execute("SELECT score FROM figures_of_merit WHERE fom_id=?", (fid,)).fetchone()
        if have and abs(have[0] - p.value) < 1e-9:
            continue
        con.execute("INSERT OR REPLACE INTO figures_of_merit (fom_id, simulant_id, property, property_label, reference_sample, score, scale, "
                    "score_text, reference_id, location, quote) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (fid, sid, property_kind(r["property"]), r["property"].strip(), ref_sample, p.value, (r.get("scale") or "").strip() or None,
                     r["score"], rid, f"{r.get('table', '')}, p.{r.get('page', '')}".strip(", "), r["quote"]))
        log.append({**base, "simulant_id": sid, "reference_id": rid, "outcome": "stored"})
    con.commit()
    return log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--findings", type=Path, required=True)
    ap.add_argument("--db", type=Path, default=DB)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    data = json.loads(args.findings.read_text())
    target = args.db
    if not args.write:
        target = Path("/tmp") / "apply_fom_dryrun.sqlite"
        shutil.copy(args.db, target)
    con = sqlite3.connect(target)
    log = []
    for res in data.get("fom", []):
        log += apply_document(con, res)
    con.close()
    from collections import Counter
    for k, v in Counter(e["outcome"] for e in log).most_common():
        print(f"  {v:4}  {k}")
    unmatched = sorted({e["simulant"] for e in log if e["outcome"] == "not stored: no simulant of exactly this name"})
    if unmatched:
        print("  names the database does not hold:", ", ".join(unmatched))
    if args.write:
        out = ROOT / "documentation" / f"fom-apply-log-{date.today().isoformat()}.json"
        out.write_text(json.dumps(log, indent=1, ensure_ascii=False))
        print(f"log -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

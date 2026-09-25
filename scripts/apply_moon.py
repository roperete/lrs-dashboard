#!/usr/bin/env python3
"""Apply the Moon provenance run (workflow moon-provenance) to lrs.sqlite.

For each landing site and lunar reference sample the reader traced every displayed value to a
document, and the checker tried to refute each claim. Rules, as for the simulants:

  * a document becomes a lunar_documents row only if the checker confirmed it names the site or
    sample (lunar_mentions keeps that quote);
  * a value gets a lunar_sources row only when the reader traced it (supported, or differs) and
    the checker CONFIRMED that, citing a confirmed document;
  * a "differs" value is corrected to what the document states, converted to the column's unit;
  * a range, a value not found, an uncertain or refuted claim writes nothing: the value stays in
    the database without a source, and the export hides it. A checker's own correction is
    listed for review, never applied;
  * a description is sourced only when every one of its claims is.

Idempotent. Usage:  python3 scripts/apply_moon.py --findings <result.json> [--write]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
from datetime import date
from pathlib import Path

from parse_value import parse_number
from provenance import ensure_provenance_schema

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"

SITE_TEXT = ("date", "samples_returned")
SITE_NUMBER = ("lat", "lng", "bulk_density", "friction_angle", "cohesion", "bearing_capacity")
SAMPLE_TEXT = ("landing_site", "type", "sample_description")

# The unit each site column is shown in, and the factors that convert a stated unit into it.
MOON_UNITS = {
    "bulk_density": {"": 1.0, "g/cm3": 1.0, "g/cc": 1.0, "gcm-3": 1.0, "g·cm-3": 1.0, "kg/m3": 0.001, "kgm-3": 0.001, "t/m3": 1.0},
    "friction_angle": {"": 1.0, "°": 1.0, "º": 1.0, "deg": 1.0, "degree": 1.0, "degrees": 1.0},
    "cohesion": {"": 1.0, "kpa": 1.0, "pa": 0.001, "mpa": 1000.0, "n/cm2": 10.0, "psi": 6.894757, "kn/m2": 1.0, "knm-2": 1.0},
    "bearing_capacity": {"": 1.0, "kpa": 1.0, "pa": 0.001, "mpa": 1000.0, "n/cm2": 10.0, "psi": 6.894757, "kn/m2": 1.0, "knm-2": 1.0},
}


def _plain(text: str) -> str:
    """Superscripts as documents print them (m⁻³, cm²) in plain form."""
    return str(text or "").replace("²", "2").replace("³", "3").replace("⁻", "-").replace("−", "-")


def _unit(text: str) -> str:
    m = re.match(r"^\s*[~≈]?\s*-?\d+(?:\.\d+)?(?:\s*±\s*\d+(?:\.\d+)?)?\s*([^(;,]*)", _plain(text))
    return re.sub(r"\s+", "", (m.group(1) if m else "")).lower().rstrip(".")


def to_moon_unit(field: str, raw: str) -> float | None:
    """A stated single value converted to the column's unit; None for ranges or unknown units."""
    text = _plain(raw).strip()
    if field in ("lat", "lng"):
        # one coordinate, possibly followed by words ("26.13239 N latitude (Lunar Module; ...)");
        # a text giving two values ("3.01612°S (Wikipedia); -3.0162 (LROC)") is not one value
        claim = re.sub(r"\([^)]*\)", " ", text.split(";")[0])     # the reader's own claim, restatements dropped
        if len(re.findall(r"-?\d+\.\d+", claim)) != 1:
            return None
        m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*°?\s*([NSEW])?(?![A-Za-z])", claim)
        if not m:
            return None
        v = float(m.group(1))
        return -abs(v) if (m.group(2) or "").upper() in ("S", "W") else v
    head = re.split(r"[(;,]", text, maxsplit=1)[0].strip()
    m = re.match(r"^\s*[~≈]?\s*(-?\d+(?:\.\d+)?)(?:\s*±\s*\d+(?:\.\d+)?)?\s*(.*)$", head)
    if not m:
        return None
    rest = m.group(2)
    # a second number that is not an exponent (m-3, cm2) makes it a range or a list, not a value
    if re.search(r"(?:^|[\s–])[~≈]?\d", rest):
        return None
    factor = MOON_UNITS[field].get(re.sub(r"\s+", "", rest).lower().rstrip("."))
    return None if factor is None else round(float(m.group(1)) * factor, 6)


def _percent(raw: str) -> float | None:
    p = parse_number(str(raw or "").replace("wt.%", "wt%"))
    return p.value if p else None


def _document(con: sqlite3.Connection, r: dict, checked_on: str) -> str:
    path = (r.get("local_path") or "").strip() or None
    doi = (r.get("doi") or "").strip() or None
    title = (r.get("title") or "").strip()
    for col, v in (("local_path", path), ("doi", doi), ("title", title)):
        if v:
            row = con.execute(f"SELECT document_id FROM lunar_documents WHERE {col}=?", (v,)).fetchone()
            if row:
                return row[0]
    n = con.execute("SELECT count(*) FROM lunar_documents").fetchone()[0] + 1
    did = f"LD-{n:03d}"
    while con.execute("SELECT 1 FROM lunar_documents WHERE document_id=?", (did,)).fetchone():
        n += 1; did = f"LD-{n:03d}"
    con.execute("INSERT INTO lunar_documents (document_id, title, authors, year, doi, url, local_path, kind, checked_on) VALUES (?,?,?,?,?,?,?,?,?)",
                (did, title, r.get("authors") or None, r.get("year") or None, doi, (r.get("url") or "").strip() or None, path, r.get("kind"), checked_on))
    return did


def apply_entity(con: sqlite3.Connection, reading: dict, check: dict, checked_on: str) -> list[dict]:
    eid = reading["id"]
    log: list[dict] = []
    note = lambda **k: log.append({"entity_id": eid, **k})
    is_site = con.execute("SELECT 1 FROM lunar_sites WHERE site_id=?", (eid,)).fetchone() is not None
    is_sample = con.execute("SELECT 1 FROM lunar_references WHERE sample_id=?", (eid,)).fetchone() is not None
    if not (is_site or is_sample):
        note(field=None, outcome="skipped: no site or sample with this id")
        return log

    ref_ok = {c["temp_id"] for c in check.get("reference_checks", []) if c.get("verdict") == "CONFIRMED"}
    docs: dict[str, str] = {}
    for r in reading.get("references", []):
        if r["temp_id"] not in ref_ok:
            note(field=None, reference=r.get("title"), outcome="document not confirmed to name this site or sample")
            continue
        did = _document(con, r, checked_on)
        docs[r["temp_id"]] = did
        con.execute("INSERT OR IGNORE INTO lunar_mentions (entity_id, document_id, mention_quote, location) VALUES (?,?,?,?)",
                    (eid, did, r.get("mention_quote") or "", r.get("location")))

    verdict = {c["field"]: c for c in check.get("value_checks", [])}

    def source(field: str, v: dict):
        con.execute("INSERT OR REPLACE INTO lunar_sources (entity_id, field, document_id, location, quote, value_text) VALUES (?,?,?,?,?,?)",
                    (eid, field, docs[v["reference_id"]], v.get("location"), v.get("quote") or "", v.get("value_in_source")))

    claims = []
    for v in reading.get("values", []):
        field, status = v["field"], v.get("status")
        chk = verdict.get(field, {})
        agreed = chk.get("verdict") == "CONFIRMED" and status in ("supported", "differs") and v.get("reference_id") in docs
        if field.startswith("description:"):
            claims.append((v, agreed))
            continue
        if not agreed:
            entry = {"field": field, "outcome": f"no source: {status}, checker {chk.get('verdict', 'silent')}"}
            if chk.get("verdict") == "REFUTED" and chk.get("correct_value"):
                entry.update(needs_review=True, correct_value=chk["correct_value"], correct_reference=chk.get("correct_reference"),
                             problems=chk.get("problems", []))
            note(**entry)
            continue
        if status == "supported":
            source(field, v)
            note(field=field, outcome="source written")
            continue
        # differs: correct the stored value to the document's
        stated = v.get("value_in_source") or ""
        if is_site and field == "samples_returned":
            q = re.search(r"\d+(?:\.\d+)?\s*(?:kg|g)\b", stated)      # the quantity, not the sentence around it
            if not q:
                note(field=field, outcome="no source: the stated value is not a mass", stated=stated, needs_review=True)
                continue
            con.execute("UPDATE lunar_sites SET samples_returned=? WHERE site_id=?", (q.group(0), eid))
        elif is_site and field in SITE_TEXT:
            con.execute(f"UPDATE lunar_sites SET {field}=? WHERE site_id=?", (stated.strip(), eid))
        elif is_site and field in SITE_NUMBER:
            x = to_moon_unit(field, stated)
            if x is None:
                note(field=field, outcome="no source: the stated value is not a single number in a known unit", stated=stated, needs_review=True)
                continue
            con.execute(f"UPDATE lunar_sites SET {field}=? WHERE site_id=?", (x, eid))
        elif is_sample and field in SAMPLE_TEXT:
            con.execute(f"UPDATE lunar_references SET {field}=? WHERE sample_id=?", (stated.strip(), eid))
        elif is_sample and field.split(":")[0] in ("oxide", "mineral"):
            kind, name = field.split(":", 1)
            col = "chemical_composition" if kind == "oxide" else "mineral_composition"
            x = _percent(stated)
            if x is None:
                note(field=field, outcome="no source: the stated value is not a single number", stated=stated, needs_review=True)
                continue
            comp = json.loads(con.execute(f"SELECT {col} FROM lunar_references WHERE sample_id=?", (eid,)).fetchone()[0] or "{}")
            comp[name] = x
            con.execute(f"UPDATE lunar_references SET {col}=? WHERE sample_id=?", (json.dumps(comp), eid))
        else:
            note(field=field, outcome="no source: not a field the page shows", needs_review=True)
            continue
        source(field, v)
        note(field=field, outcome="corrected to the source", was=v.get("stored"), now=stated)

    if claims:
        if all(ok for _, ok in claims):
            for v, _ in claims:
                con.execute("INSERT OR REPLACE INTO lunar_sources (entity_id, field, document_id, location, quote, value_text) VALUES (?,?,?,?,?,?)",
                            (eid, "description", docs[v["reference_id"]], v.get("location"), v.get("quote") or "", None))
            note(field="description", outcome=f"source written ({len(claims)} claims)")
        else:
            note(field="description", outcome="no source: not every claim is confirmed", needs_review=True,
                 unsupported=[v["field"].split(":", 1)[1] for v, ok in claims if not ok])

    if is_sample:
        for kind in ("oxide", "mineral"):
            used = {r[0] for r in con.execute("SELECT DISTINCT document_id FROM lunar_sources WHERE entity_id=? AND field LIKE ?", (eid, f"{kind}:%"))}
            if len(used) > 1:
                note(field=kind, outcome="the table cites more than one document: one analysis per table", needs_review=True, documents=sorted(used))
    return log


def apply_results(con: sqlite3.Connection, results: dict, checked_on: str | None = None) -> list[dict]:
    ensure_provenance_schema(con)
    checked_on = checked_on or date.today().isoformat()
    log: list[dict] = []
    for g in results.get("results", []):
        checks = {c["id"]: c for c in ((g.get("check") or {}).get("entities") or [])}
        for reading in (g.get("reading") or {}).get("entities", []):
            log += apply_entity(con, reading, checks.get(reading["id"], {}), checked_on)
    con.commit()
    return log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--findings", type=Path, required=True)
    ap.add_argument("--db", type=Path, default=DB)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    target = args.db
    if not args.write:
        target = Path("/tmp") / "apply_moon_dryrun.sqlite"
        shutil.copy(args.db, target)
    con = sqlite3.connect(target)
    log = apply_results(con, json.loads(args.findings.read_text()))
    from collections import Counter
    for k, v in Counter(e["outcome"].split(":")[0] for e in log).most_common():
        print(f"  {v:4}  {k}")
    print(f"  {sum(1 for e in log if e.get('needs_review'))} for review")
    if args.write:
        out = ROOT / "documentation" / f"moon-apply-log-{date.today().isoformat()}.json"
        out.write_text(json.dumps(log, indent=1, ensure_ascii=False) + "\n")
        print(f"log -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

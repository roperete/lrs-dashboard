#!/usr/bin/env python3
"""Move a simulant to a newer version of its manufacturer data sheet.

Hispansion published TLH-0 v1.4 and TLM-0 v2.2 after the database was built from v1.1; the
new sheets report iron as FeO rather than Fe2O3 and measure sodium v1.1 reported as below
detection. A reader and an independent checker read the new sheet value by value
(workflow hispansion-sheet-update); this applies what they both confirmed:

  * the new sheet becomes a reference row of its own (DS-<id>-<version>); the link and the
    "Composition data source" line point at it; the previous version stays, marked superseded;
  * a composition table the new sheet restates is replaced whole — one analysis, never
    merged row by row, or Fe2O3 from one version and FeO from the other count iron twice;
  * a value both agents confirmed replaces the stored one and takes a source row citing the
    new sheet; a value the new sheet does not restate keeps its previous citation;
  * a refuted value, or one only the checker found, is logged and not applied.

Idempotent.

    python3 scripts/supersede_sheet.py --findings <workflow result json> [--write]
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
from apply_provenance import SCALAR_FIELDS, _statement  # noqa: E402
from parse_value import COLUMN_UNITS, parse_number, to_column_unit  # noqa: E402
from provenance import ensure_provenance_schema  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"
SOURCES = Path("/Volumes/Extreme SSD/Spring - Forest on the moon/DIRT/Sources")
# Facts about the document itself rather than the product; set from the sheet, no source row.
DOCUMENT_FIELDS = {"datasheet_document_id", "datasheet_date", "product_grade"}


# Spelling slips on manufacturer sheets, corrected to the mineral's name.
MINERAL_NAME_FIXES = {"Fosterite": "Forsterite"}


def mineral_name(printed: str) -> tuple[str, str | None]:
    """(name to store, the correction made or None)."""
    name = re.sub(r"\s*/\s*", "/", printed.strip())
    fixed = MINERAL_NAME_FIXES.get(name, name)
    return fixed, (f"{name} -> {fixed}" if fixed != name else None)


def availability_category(printed: str) -> str | None:
    """The category a sheet's availability wording states, or None if it states none plainly."""
    t = printed.strip().lower()
    if t.startswith(("available", "in stock", "currently available")):
        return "Available"
    return None


def version_of(document_id: str) -> str:
    m = re.search(r"v\d+(?:\.\d+)*", document_id or "")
    return m.group(0) if m else "new"


def supersede(con: sqlite3.Connection, f: dict, sources_root=SOURCES, checked_on: str | None = None) -> list[dict]:
    ensure_provenance_schema(con)
    checked_on = checked_on or date.today().isoformat()
    sid, reading, check = f["simulant_id"], f["reading"], f.get("check") or {}
    log: list[dict] = []
    note = lambda **e: log.append({"simulant_id": sid, **e})

    verdicts = {c["field"]: c["verdict"] for c in check.get("checks", [])}
    confirmed = []
    for v in reading.get("values", []):
        verdict = verdicts.get(v["field"])
        if verdict == "CONFIRMED":
            confirmed.append(v)
        else:
            note(field=v["field"], value=v["value"], outcome="not applied: refuted by the checker" if verdict == "REFUTED"
                 else "not applied: the checker could not confirm")
    for v in check.get("missed", []):
        note(field=v["field"], value=v["value"], outcome="not applied: found only by the checker", quote=v.get("quote"))

    doc_id = reading.get("document_id") or ""
    ver = version_of(doc_id)
    old_rid, new_rid = f"DS-{sid}", f"DS-{sid}-{ver}"
    try:
        local = str(Path(f["path"]).relative_to(Path(sources_root)))
    except ValueError:
        local = f["path"]
    title = f"Hispansion Technical Data Sheet {doc_id} (public, {checked_on[:7]})"
    first = next((v["quote"] for v in confirmed if v["field"] == "datasheet_document_id"), doc_id)
    have = con.execute("SELECT 1 FROM references_ WHERE reference_id=?", (new_rid,)).fetchone()
    if not have:
        con.execute("INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type, title, url, names_simulant, "
                    "mention_quote, local_path, checked_on) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (new_rid, sid, title, "datasheet", title, f["url"], 1, first, local, checked_on))
        note(reference_id=new_rid, outcome="reference created for the new sheet")

    old = con.execute("SELECT title FROM references_ WHERE reference_id=?", (old_rid,)).fetchone()
    if old and f"superseded by {ver}" not in (old[0] or ""):
        con.execute("UPDATE references_ SET title=? WHERE reference_id=?", (f"{old[0]} — superseded by {ver}", old_rid))
        note(reference_id=old_rid, outcome=f"previous version marked superseded by {ver}")

    for kind, table, col, prefix in (("oxide", "chemical_compositions", "value_wt_pct", "CH"),
                                     ("mineral", "mineral_compositions", "value_pct", "C")):
        rows = [v for v in confirmed if v["field"].startswith(kind + ":")]
        parsed = [(v, parse_number(v["value"])) for v in rows]
        for v, p in parsed:
            if p is None:
                note(field=v["field"], value=v["value"], outcome="not applied: not a single number")
        parsed = [(v, p) for v, p in parsed if p is not None]
        if not parsed:
            continue
        named = []
        for v, p in parsed:
            printed = v["field"].split(":", 1)[1]
            name, fix = mineral_name(printed) if kind == "mineral" else (printed.strip(), None)
            if fix:
                note(field=v["field"], outcome=f"renamed: {fix}")
            named.append((v, p, name))
        want = sorted((name, p.value) for _, p, name in named)
        now = sorted((r[0], r[1]) for r in con.execute(
            f"SELECT component_name, {col} FROM {table} WHERE simulant_id=? AND reference_id=?", (sid, new_rid)))
        total = con.execute(f"SELECT count(*) FROM {table} WHERE simulant_id=?", (sid,)).fetchone()[0]
        if now == want and total == len(want):
            continue                                    # already on the new sheet
        for r in con.execute(f"SELECT component_name, {col}, reference_id FROM {table} WHERE simulant_id=?", (sid,)).fetchall():
            note(field=f"{kind}:{r[0]}", value=r[1], reference_id=r[2], outcome="replaced: previous version's row")
        con.execute(f"DELETE FROM {table} WHERE simulant_id=?", (sid,))
        for i, (v, p, name) in enumerate(named, 1):
            con.execute(f"INSERT INTO {table} (composition_id, simulant_id, component_type, component_name, {col}, reference_id, value_text) "
                        "VALUES (?,?,?,?,?,?,?)", (f"{prefix}-{sid}-{ver}-{i:02d}", sid, kind, name,
                                                   p.value, new_rid, _statement(v["value"])))
        note(outcome=f"{kind} table replaced from the new sheet", rows=len(named))

    numeric = {r[1] for r in con.execute("PRAGMA table_info(simulants)") if (r[2] or "").upper() == "REAL"}
    for v in confirmed:
        field = v["field"]
        if ":" in field:
            continue
        if field in DOCUMENT_FIELDS:
            con.execute(f"UPDATE simulants SET {field}=? WHERE simulant_id=?", (v["value"], sid))
            continue
        if field not in SCALAR_FIELDS:
            note(field=field, value=v["value"], outcome="not applied: not a field the database holds")
            continue
        value = v["value"]
        if field == "availability":
            value = availability_category(value)
            if value is None:
                note(field=field, value=v["value"], outcome="not applied: availability wording needs a human")
                continue
        if field in COLUMN_UNITS:
            value = to_column_unit(field, value)
            if value is None:
                note(field=field, value=v["value"], outcome="not applied: not a single number")
                continue
        elif field in numeric:
            p = parse_number(value)
            if p is None:
                note(field=field, value=value, outcome="not applied: not a single number")
                continue
            value = p.value
        prev = con.execute(f"SELECT {field} FROM simulants WHERE simulant_id=?", (sid,)).fetchone()[0]
        src = con.execute("SELECT reference_id, location, quote FROM property_sources WHERE simulant_id=? AND field=?", (sid, field)).fetchone()
        location = f"{v.get('table', '')}, p.{v.get('page', '')}".strip(", ")
        if prev == value and src and tuple(src) == (new_rid, location, v["quote"]):
            continue
        con.execute(f"UPDATE simulants SET {field}=? WHERE simulant_id=?", (value, sid))
        con.execute("INSERT OR REPLACE INTO property_sources (simulant_id, field, reference_id, location, quote) VALUES (?,?,?,?,?)",
                    (sid, field, new_rid, location, v["quote"]))
        note(field=field, value=value, previous=prev, previous_source=src[0] if src else None, outcome="value taken from the new sheet")

    kept = [r[0] for r in con.execute("SELECT field FROM property_sources WHERE simulant_id=? AND reference_id=?", (sid, old_rid))]
    for fld in kept:
        note(field=fld, outcome="kept: stated only by the previous version, still cited to it")

    con.execute("UPDATE simulants SET datasheet_url=?, composition_source_url=?, composition_source_title=?, "
                "composition_source_kind='manufacturer_datasheet', composition_needs_review=0 WHERE simulant_id=?",
                (f["url"], f["url"], title, sid))
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
        target = Path("/tmp") / "supersede_dryrun.sqlite"
        shutil.copy(args.db, target)
    con = sqlite3.connect(target)
    log = []
    for f in data["sheets"]:
        log += supersede(con, f)
    con.close()
    counts: dict[str, int] = {}
    for e in log:
        counts[e["outcome"]] = counts.get(e["outcome"], 0) + 1
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {v:4}  {k}")
    if args.write:
        out = ROOT / "documentation" / f"sheet-supersede-log-{date.today().isoformat()}.json"
        out.write_text(json.dumps(log, indent=1, ensure_ascii=False, default=str))
        print(f"log -> {out.relative_to(ROOT)}")
    else:
        print("dry run on a copy; pass --write to apply")


if __name__ == "__main__":
    main()

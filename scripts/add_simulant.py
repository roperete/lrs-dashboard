#!/usr/bin/env python3
"""Add a simulant the database lacks, from a paper that characterises it.

A reader and an independent checker read the paper product by product. A product becomes a
record only when the checker confirms the paper names it; every value it carries is one both
agents confirmed, cited to the paper as a reference of its own. Composition rows and
physical values are stored exactly as the rest of the pipeline stores them (numbers in the
column's unit, the statement kept beside a composition value).

    python3 scripts/add_simulant.py --findings <workflow result json> --paper <paper json> [--write]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_provenance import SCALAR_FIELDS, _statement  # noqa: E402
from parse_value import COLUMN_UNITS, parse_number, to_column_unit  # noqa: E402
from provenance import ensure_provenance_schema  # noqa: E402
from supersede_sheet import DOCUMENT_FIELDS, availability_category, mineral_name  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"
SOURCES = Path("/Volumes/Extreme SSD/Spring - Forest on the moon/DIRT/Sources")


def next_simulant_id(con: sqlite3.Connection) -> str:
    ids = [int(r[0][1:]) for r in con.execute("SELECT simulant_id FROM simulants") if r[0][1:].isdigit()]
    retired = ROOT / "documentation" / "retired-simulants.md"        # a retired id is never reused
    if retired.exists():
        import re
        ids += [int(m) for m in re.findall(r"\| S(\d+) \|", retired.read_text())]
    return f"S{max(ids, default=0) + 1:03d}"


def add_from_paper(con: sqlite3.Connection, f: dict, paper: dict, sources_root=SOURCES, checked_on: str | None = None) -> list[dict]:
    ensure_provenance_schema(con)
    checked_on = checked_on or date.today().isoformat()
    name, reading, check = f["name"], f["reading"], f.get("check") or {}
    log: list[dict] = []
    if check.get("names_verdict") != "CONFIRMED":
        return [{"name": name, "outcome": "not added: the checker did not confirm the paper names it"}]

    row = con.execute("SELECT simulant_id FROM simulants WHERE name=?", (name,)).fetchone()
    sid = row[0] if row else next_simulant_id(con)
    if not row:
        con.execute("INSERT INTO simulants (simulant_id, name, composition_status) VALUES (?,?,'not_extracted')", (sid, name))
        log.append({"simulant_id": sid, "name": name, "outcome": "record created"})

    try:
        local = str(Path(paper["path"]).relative_to(Path(sources_root)))
    except ValueError:
        local = paper["path"]
    have = con.execute("SELECT reference_id FROM references_ WHERE simulant_id=? AND lower(coalesce(doi,''))=lower(?)",
                       (sid, paper["doi"])).fetchone()
    if have:
        rid = have[0]
    else:
        n = con.execute("SELECT count(*) FROM references_ WHERE reference_id LIKE ?", (f"RN-{sid}-%",)).fetchone()[0]
        rid = f"RN-{sid}-{n + 1}"
        con.execute("INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type, title, authors, year, doi, url, "
                    "names_simulant, mention_quote, local_path, checked_on) VALUES (?,?,?,?,?,?,?,?,?,1,?,?,?)",
                    (rid, sid, f"{paper['authors']} ({paper['year']}). {paper['title']}.", "composition", paper["title"],
                     paper["authors"], paper["year"], paper["doi"], paper.get("url"), reading.get("names_quote"), local, checked_on))
        log.append({"simulant_id": sid, "reference_id": rid, "outcome": "reference created"})

    verdicts = {c["field"]: c["verdict"] for c in check.get("checks", [])}
    numeric = {r[1] for r in con.execute("PRAGMA table_info(simulants)") if (r[2] or "").upper() == "REAL"}
    rows = {"oxide": [], "mineral": []}
    for v in reading.get("values", []):
        field = v["field"]
        if verdicts.get(field) != "CONFIRMED":
            log.append({"simulant_id": sid, "field": field, "outcome": "not applied: not confirmed by the checker"})
            continue
        location = f"{v.get('table', '')}, p.{v.get('page', '')}".strip(", ")
        if ":" in field:
            kind, printed = field.split(":", 1)
            p = parse_number(v["value"])
            if kind in rows and p is not None:
                rows[kind].append((mineral_name(printed)[0] if kind == "mineral" else printed.strip(), p.value, _statement(v["value"])))
            else:
                log.append({"simulant_id": sid, "field": field, "value": v["value"], "outcome": "not applied: not a single number"})
            continue
        if field in DOCUMENT_FIELDS:
            con.execute(f"UPDATE simulants SET {field}=? WHERE simulant_id=?", (v["value"], sid))
            continue
        if field not in SCALAR_FIELDS:
            log.append({"simulant_id": sid, "field": field, "outcome": "not applied: not a field the database holds"})
            continue
        value = v["value"]
        if field == "availability":
            value = availability_category(value)
        elif field in COLUMN_UNITS:
            value = to_column_unit(field, value)
        elif field in numeric:
            p = parse_number(value)
            value = p.value if p else None
        if value is None:
            log.append({"simulant_id": sid, "field": field, "value": v["value"], "outcome": "not applied: not a single number"})
            continue
        con.execute(f"UPDATE simulants SET {field}=? WHERE simulant_id=?", (value, sid))
        con.execute("INSERT OR REPLACE INTO property_sources (simulant_id, field, reference_id, location, quote) VALUES (?,?,?,?,?)",
                    (sid, field, rid, location, v["quote"]))
        log.append({"simulant_id": sid, "field": field, "value": value, "outcome": "value added with source"})

    for kind, table, col, prefix in (("oxide", "chemical_compositions", "value_wt_pct", "CH"), ("mineral", "mineral_compositions", "value_pct", "C")):
        if not rows[kind]:
            continue
        if con.execute(f"SELECT count(*) FROM {table} WHERE simulant_id=? AND reference_id!=?", (sid, rid)).fetchone()[0]:
            log.append({"simulant_id": sid, "outcome": f"not merged: the {kind} table already holds another document's analysis"})
            continue
        con.execute(f"DELETE FROM {table} WHERE simulant_id=? AND reference_id=?", (sid, rid))
        for i, (comp, value, stated) in enumerate(rows[kind], 1):
            con.execute(f"INSERT INTO {table} (composition_id, simulant_id, component_type, component_name, {col}, reference_id, value_text) "
                        "VALUES (?,?,?,?,?,?,?)", (f"{prefix}-{sid}-{i:02d}", sid, kind, comp, value, rid, stated))
        log.append({"simulant_id": sid, "outcome": f"{kind} table added", "rows": len(rows[kind])})
    if rows["oxide"] or rows["mineral"]:
        con.execute("UPDATE simulants SET composition_status='verified', composition_source_title=?, composition_source_url=?, "
                    "composition_source_kind='primary_paper', composition_needs_review=0 WHERE simulant_id=?",
                    (paper["title"], paper.get("url"), sid))
    con.commit()
    return log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--findings", type=Path, required=True)
    ap.add_argument("--paper", type=Path, required=True)
    ap.add_argument("--db", type=Path, default=DB)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    data, paper = json.loads(args.findings.read_text()), json.loads(args.paper.read_text())
    target = args.db
    if not args.write:
        target = Path("/tmp") / "add_simulant_dryrun.sqlite"
        shutil.copy(args.db, target)
    con = sqlite3.connect(target)
    log = []
    for f in data["products"]:
        log += add_from_paper(con, f, paper)
    con.close()
    for e in log:
        print(f"  {e.get('simulant_id', e.get('name'))} {e.get('field') or ''}: {e['outcome']}")
    if args.write:
        out = ROOT / "documentation" / f"add-simulant-log-{date.today().isoformat()}.json"
        out.write_text(json.dumps(log, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()

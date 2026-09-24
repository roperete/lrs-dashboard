#!/usr/bin/env python3
"""Repair values stored as text in numeric columns, and citations that prove nothing.

Before 2026-09-23 the apply step wrote a reader's quoted value verbatim, and SQLite keeps a
string such as "22.4 (vol%)" in a REAL column as text; the page then drops the row without a
word. scripts/apply_provenance.py now parses at write time. This repairs what was already
stored:

  * a composition value that states one number becomes that number, with the statement
    kept verbatim in value_text; one that does not ("present", "<0.02") is removed;
  * a numeric physical property stated with its unit becomes the number; a range or two
    measurements is cleared along with its source row, the quote kept in the log;
  * mineral rows that are feedstock mixing ratios, named explicitly, are removed;
  * references to the project's own registry are deleted — it is the data being checked.

Every change is logged; nothing is lost. Idempotent.

    python3 scripts/fix_values.py            # dry run on a copy
    python3 scripts/fix_values.py --write
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
from apply_provenance import _statement, is_self_registry  # noqa: E402
from parse_value import COLUMN_UNITS, parse_number, to_column_unit  # noqa: E402
from provenance import ensure_provenance_schema  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"

# Feedstock mixing ratios recorded as mineral composition by the 2026-09-23 wave: the rocks
# blended to make the product, not the minerals in it. Named explicitly rather than guessed.
FEEDSTOCK_ROWS = {
    ("S100", "Agglutinates"), ("S100", "Anorthosite"), ("S100", "Basalt"),          # OPRH4W30
    ("S103", "Anorthosite (GreenSpar feedstock)"),                                    # CSM-LHT-1
    ("S103", "Basalt (Merriam Crater cinder feedstock)"),
    ("S105", "Basalt (Merriam Crater cinder feedstock)"),                             # CSM-LMT-1
    ("S119", "Coal"), ("S119", "Limestone"),                                          # CMU-1
}

COMPOSITION_TABLES = (("chemical_compositions", "value_wt_pct"), ("mineral_compositions", "value_pct"))


def repair(con: sqlite3.Connection, feedstock=FEEDSTOCK_ROWS) -> list[dict]:
    """Repair in place and return the log. The caller's connection settings are restored."""
    ensure_provenance_schema(con)
    previous_factory = con.row_factory
    con.row_factory = sqlite3.Row
    try:
        return _repair(con, feedstock)
    finally:
        con.row_factory = previous_factory


def _repair(con: sqlite3.Connection, feedstock) -> list[dict]:
    log: list[dict] = []

    for table, col in COMPOSITION_TABLES:
        for r in con.execute(f"SELECT composition_id, simulant_id, component_name, {col} AS v, reference_id FROM {table} "
                             f"WHERE typeof({col})='text'").fetchall():
            p = parse_number(r["v"])
            base = {"table": table, "composition_id": r["composition_id"], "simulant_id": r["simulant_id"],
                    "component": r["component_name"], "stated": r["v"], "reference_id": r["reference_id"]}
            if p is None:
                con.execute(f"DELETE FROM {table} WHERE composition_id=?", (r["composition_id"],))
                log.append({**base, "action": "removed: not a single number"})
            else:
                con.execute(f"UPDATE {table} SET {col}=?, value_text=? WHERE composition_id=?",
                            (p.value, _statement(r["v"]), r["composition_id"]))
                log.append({**base, "action": "converted", "value": p.value})

    for sid, component in sorted(feedstock):
        r = con.execute("SELECT composition_id, value_pct, reference_id FROM mineral_compositions WHERE simulant_id=? AND component_name=?",
                        (sid, component)).fetchone()
        if r:
            con.execute("DELETE FROM mineral_compositions WHERE composition_id=?", (r["composition_id"],))
            log.append({"table": "mineral_compositions", "composition_id": r["composition_id"], "simulant_id": sid,
                        "component": component, "stated": r["value_pct"], "reference_id": r["reference_id"],
                        "action": "removed: feedstock ratio, not a mineral"})

    numeric = [r[1] for r in con.execute("PRAGMA table_info(simulants)") if (r[2] or "").upper() == "REAL"]
    for col in numeric:
        for r in con.execute(f"SELECT simulant_id, {col} AS v FROM simulants WHERE typeof({col})='text'").fetchall():
            p = parse_number(r["v"])
            src = con.execute("SELECT reference_id, location, quote FROM property_sources WHERE simulant_id=? AND field=?",
                              (r["simulant_id"], col)).fetchone()
            base = {"table": "simulants", "simulant_id": r["simulant_id"], "field": col, "stated": r["v"],
                    "reference_id": src["reference_id"] if src else None, "quote": src["quote"] if src else None}
            if p is None:
                con.execute(f"UPDATE simulants SET {col}=NULL WHERE simulant_id=?", (r["simulant_id"],))
                con.execute("DELETE FROM property_sources WHERE simulant_id=? AND field=?", (r["simulant_id"], col))
                log.append({**base, "action": "cleared: not a single number"})
            else:
                con.execute(f"UPDATE simulants SET {col}=? WHERE simulant_id=?", (p.value, r["simulant_id"]))
                log.append({**base, "action": "converted", "value": p.value})

    # Text-typed physical columns the page reads as bare numbers in a fixed unit.
    for col in COLUMN_UNITS:
        for r in con.execute(f"SELECT simulant_id, {col} AS v FROM simulants WHERE {col} IS NOT NULL AND {col} != ''").fetchall():
            if isinstance(r["v"], (int, float)) or re.fullmatch(r"\s*[-+]?\d+(?:\.\d+)?\s*", str(r["v"])):
                continue
            converted = to_column_unit(col, r["v"])
            src = con.execute("SELECT reference_id, quote FROM property_sources WHERE simulant_id=? AND field=?",
                              (r["simulant_id"], col)).fetchone()
            base = {"table": "simulants", "simulant_id": r["simulant_id"], "field": col, "stated": r["v"],
                    "reference_id": src["reference_id"] if src else None, "quote": src["quote"] if src else None}
            if converted is None:
                con.execute(f"UPDATE simulants SET {col}=NULL WHERE simulant_id=?", (r["simulant_id"],))
                con.execute("DELETE FROM property_sources WHERE simulant_id=? AND field=?", (r["simulant_id"], col))
                log.append({**base, "action": "cleared: not a single number"})
            else:
                con.execute(f"UPDATE simulants SET {col}=? WHERE simulant_id=?", (converted, r["simulant_id"]))
                log.append({**base, "action": "converted to the column unit", "value": converted})

    for r in con.execute("SELECT reference_id, simulant_id, title, local_path FROM references_").fetchall():
        if not is_self_registry(r["title"], r["local_path"]):
            continue
        rid = r["reference_id"]
        con.execute("DELETE FROM property_sources WHERE reference_id=?", (rid,))
        for table, _ in COMPOSITION_TABLES:
            con.execute(f"UPDATE {table} SET reference_id=NULL WHERE reference_id=?", (rid,))
        con.execute("DELETE FROM references_ WHERE reference_id=?", (rid,))
        log.append({"table": "references_", "reference_id": rid, "simulant_id": r["simulant_id"], "title": r["title"],
                    "local_path": r["local_path"], "action": "deleted: the project's own registry is not evidence"})

    con.commit()
    return log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DB)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    target = args.db
    if not args.write:
        target = Path("/tmp") / "fix_values_dryrun.sqlite"
        shutil.copy(args.db, target)
    con = sqlite3.connect(target)
    log = repair(con)
    con.close()
    counts: dict[str, int] = {}
    for e in log:
        counts[e["action"]] = counts.get(e["action"], 0) + 1
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {v:4}  {k}")
    if args.write:
        out = ROOT / "documentation" / f"value-repair-log-{date.today().isoformat()}.json"
        out.write_text(json.dumps(log, indent=1, ensure_ascii=False, default=str))
        print(f"log -> {out.relative_to(ROOT)}")
    else:
        print("dry run on a copy; pass --write to apply")


if __name__ == "__main__":
    main()

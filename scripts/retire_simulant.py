#!/usr/bin/env python3
"""Retire a simulant record that turned out not to be a real product.

A retired record is deleted from every table that carries a simulant_id, so it leaves
the export entirely; a full copy of the deleted rows is written under
documentation/retired/, and a line is appended to documentation/retired-simulants.md
with the reason and, where the name was a misreading of other products, which ones.

Usage:
    python3 scripts/retire_simulant.py S068 --reason "..." [--alias-of S069,S070] [--write]

Without --write the deletion runs against a copy and only the row counts are printed.
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

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"
DOCS = ROOT / "documentation"


def tables_with_simulant_id(con: sqlite3.Connection) -> list[str]:
    """Every user table with a simulant_id column, simulants last so foreign rows go first."""
    names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    out = [t for t in names if any(c[1] == "simulant_id" for c in con.execute(f"PRAGMA table_info({t})"))]
    out.sort(key=lambda t: (t == "simulants", t))
    return out


def retire(con: sqlite3.Connection, simulant_id: str, reason: str, alias_of: list[str], today: str) -> dict:
    """Delete the record from every table and return an archive of what was deleted."""
    con.row_factory = sqlite3.Row
    sim = con.execute("SELECT * FROM simulants WHERE simulant_id=?", (simulant_id,)).fetchone()
    if sim is None:
        raise ValueError(f"{simulant_id} is not in simulants")
    rows: dict[str, list[dict]] = {}
    for table in tables_with_simulant_id(con):
        got = [dict(r) for r in con.execute(f"SELECT * FROM {table} WHERE simulant_id=?", (simulant_id,))]
        if got:
            rows[table] = got
            con.execute(f"DELETE FROM {table} WHERE simulant_id=?", (simulant_id,))
    con.commit()
    return {
        "simulant_id": simulant_id,
        "name": sim["name"],
        "retired_on": today,
        "reason": reason,
        "alias_of": list(alias_of),
        "rows": rows,
    }


def write_archive(archive: dict, docs_dir: Path) -> Path:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", archive["name"]).strip("-")
    path = docs_dir / "retired" / f"{archive['simulant_id']}-{slug}-{archive['retired_on']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(archive, indent=1, ensure_ascii=False))
    return path


REGISTER_HEADER = (
    "# Retired simulants\n\n"
    "Records removed from the database because the product does not exist under that name.\n"
    "The deleted rows are kept in full under `documentation/retired/`. A retired id is never reused.\n\n"
    "| Id | Name | Retired | Actually | Reason |\n"
    "|---|---|---|---|---|\n"
)


def append_register(archive: dict, register: Path) -> None:
    register.parent.mkdir(parents=True, exist_ok=True)
    text = register.read_text() if register.exists() else ""
    if "# Retired simulants" not in text:
        text = REGISTER_HEADER
    if not text.endswith("\n"):
        text += "\n"
    alias = ", ".join(archive["alias_of"]) or "—"
    text += f"| {archive['simulant_id']} | {archive['name']} | {archive['retired_on']} | {alias} | {archive['reason']} |\n"
    register.write_text(text)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("simulant_id")
    ap.add_argument("--reason", required=True)
    ap.add_argument("--alias-of", default="", help="comma-separated ids of the products this name actually referred to")
    ap.add_argument("--db", type=Path, default=DB)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    alias_of = [a.strip() for a in args.alias_of.split(",") if a.strip()]
    today = date.today().isoformat()

    db = args.db
    if not args.write:
        db = Path("/tmp") / f"retire-dryrun-{args.simulant_id}.sqlite"
        shutil.copy(args.db, db)
    con = sqlite3.connect(db)
    archive = retire(con, args.simulant_id, args.reason, alias_of, today)
    con.close()
    for table, rows in archive["rows"].items():
        print(f"{table}: {len(rows)} row(s)")
    if args.write:
        path = write_archive(archive, DOCS)
        append_register(archive, DOCS / "retired-simulants.md")
        print(f"retired {archive['name']} ({args.simulant_id}); archive {path.relative_to(ROOT)}")
    else:
        print("dry run only; pass --write to apply", file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Per-value provenance schema (spec: docs/superpowers/specs/2026-09-22-per-value-provenance-design.md).

    references_          + names_simulant, mention_quote, local_path, checked_on
    chemical_compositions + reference_id
    mineral_compositions  + reference_id
    property_sources     new: one row per (simulant, field) naming the reference a scalar came from

`ensure_provenance_schema(con)` is idempotent and returns what it added.

Usage:  python3 scripts/provenance.py          # migrate lrs.sqlite in place
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from datasheet_fill import ensure_columns  # noqa: E402

DB = ROOT / "lrs.sqlite"

REFERENCE_COLUMNS = [
    ("names_simulant", "INTEGER"),   # 1 confirmed, 0 checked and absent, NULL unchecked
    ("mention_quote", "TEXT"),       # the sentence naming the simulant
    ("local_path", "TEXT"),          # copy under DIRT/Sources used for verification; never displayed
    ("checked_on", "TEXT"),          # ISO date of last verification
]
COMPOSITION_COLUMNS = [("reference_id", "TEXT")]

PROPERTY_SOURCES_DDL = """
CREATE TABLE IF NOT EXISTS property_sources (
  simulant_id   TEXT NOT NULL REFERENCES simulants(simulant_id),
  field         TEXT NOT NULL,   -- column name on simulants, e.g. cohesion, ph, bulk_density
  reference_id  TEXT NOT NULL REFERENCES references_(reference_id),
  location      TEXT,            -- page, table or figure as the reader found it
  quote         TEXT,            -- the line stating the value
  PRIMARY KEY (simulant_id, field)
)
"""


def ensure_provenance_schema(con: sqlite3.Connection) -> list[str]:
    added: list[str] = []
    added += [f"references_.{c}" for c in ensure_columns(con, "references_", REFERENCE_COLUMNS)]
    added += [f"chemical_compositions.{c}" for c in ensure_columns(con, "chemical_compositions", COMPOSITION_COLUMNS)]
    added += [f"mineral_compositions.{c}" for c in ensure_columns(con, "mineral_compositions", COMPOSITION_COLUMNS)]
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "property_sources" not in have:
        con.execute(PROPERTY_SOURCES_DDL)
        added.append("property_sources")
    con.commit()
    return added


def main() -> None:
    con = sqlite3.connect(DB)
    added = ensure_provenance_schema(con)
    con.close()
    print("added:", added or "nothing (schema already current)")


if __name__ == "__main__":
    main()

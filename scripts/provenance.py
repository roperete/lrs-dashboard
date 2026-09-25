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
# value_text: the value as the document states it ("22.4 (vol%)", "2.33 ± 0.03 wt.-%"), kept
# when it says more than the bare number — the basis, the uncertainty, "ca." — so the page can show it.
COMPOSITION_COLUMNS = [("reference_id", "TEXT"), ("value_text", "TEXT")]

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


FOM_TABLE = """CREATE TABLE IF NOT EXISTS figures_of_merit (
  fom_id TEXT PRIMARY KEY, simulant_id TEXT NOT NULL REFERENCES simulants(simulant_id),
  property TEXT NOT NULL, property_label TEXT NOT NULL, reference_sample TEXT, score REAL NOT NULL,
  scale TEXT, score_text TEXT, reference_id TEXT NOT NULL REFERENCES references_(reference_id),
  location TEXT, quote TEXT)"""


# The Moon section (2026-09-25): landing sites moved out of src/lunarData.ts, and sources for
# every value of a site or a lunar reference sample. A document is shared by many sites (the
# Lunar Sourcebook serves all of them), so documents have their own table; lunar_mentions
# records that a document names a site or sample, lunar_sources that it states a value.
LUNAR_DDL = """
CREATE TABLE IF NOT EXISTS lunar_sites (
  site_id          TEXT PRIMARY KEY,
  name             TEXT NOT NULL,
  mission          TEXT NOT NULL,
  programme        TEXT NOT NULL,   -- Apollo | Luna | Chang-e | Other
  date             TEXT,
  lat              REAL,
  lng              REAL,
  samples_returned TEXT,
  description      TEXT,
  bulk_density     REAL,            -- g/cm3
  friction_angle   REAL,            -- degrees
  cohesion         REAL,            -- kPa
  bearing_capacity REAL             -- kPa
);
CREATE TABLE IF NOT EXISTS lunar_documents (
  document_id TEXT PRIMARY KEY,     -- LD-001 ...
  title       TEXT NOT NULL,
  authors     TEXT,
  year        TEXT,
  doi         TEXT,
  url         TEXT,
  local_path  TEXT,                 -- relative to DIRT/Sources
  kind        TEXT,
  checked_on  TEXT
);
CREATE TABLE IF NOT EXISTS lunar_mentions (
  entity_id     TEXT NOT NULL,      -- site_id or sample_id
  document_id   TEXT NOT NULL REFERENCES lunar_documents(document_id),
  mention_quote TEXT NOT NULL,
  location      TEXT,
  PRIMARY KEY (entity_id, document_id)
);
CREATE TABLE IF NOT EXISTS lunar_sources (
  entity_id   TEXT NOT NULL,
  field       TEXT NOT NULL,        -- column, "oxide:SiO2", "mineral:Plagioclase", "description"
  document_id TEXT NOT NULL REFERENCES lunar_documents(document_id),
  location    TEXT,
  quote       TEXT NOT NULL,
  value_text  TEXT,                 -- the value as the document states it
  PRIMARY KEY (entity_id, field, document_id)
);
"""


def ensure_provenance_schema(con: sqlite3.Connection) -> list[str]:
    added: list[str] = []
    added += [f"references_.{c}" for c in ensure_columns(con, "references_", REFERENCE_COLUMNS)]
    added += [f"chemical_compositions.{c}" for c in ensure_columns(con, "chemical_compositions", COMPOSITION_COLUMNS)]
    added += [f"mineral_compositions.{c}" for c in ensure_columns(con, "mineral_compositions", COMPOSITION_COLUMNS)]
    if not con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='figures_of_merit'").fetchone():
        con.execute(FOM_TABLE)
        added.append("figures_of_merit")
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "property_sources" not in have:
        con.execute(PROPERTY_SOURCES_DDL)
        added.append("property_sources")
    for t in ("lunar_sites", "lunar_documents", "lunar_mentions", "lunar_sources"):
        if t not in have:
            added.append(t)
    con.executescript(LUNAR_DDL)
    con.commit()
    return added


def main() -> None:
    con = sqlite3.connect(DB)
    added = ensure_provenance_schema(con)
    con.close()
    print("added:", added or "nothing (schema already current)")


if __name__ == "__main__":
    main()

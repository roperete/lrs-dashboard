#!/usr/bin/env python3
"""
Export lrs.sqlite → public/data/data.json
Run this after editing the database to regenerate the frontend data file.

Usage:
    python3 scripts/export_json.py
    python3 scripts/export_json.py --db path/to/custom.sqlite
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DEFAULT_DB = ROOT / "lrs.sqlite"
OUTPUT = ROOT / "public" / "data" / "data.json"


def row_to_dict(cursor, row):
    return {col[0]: val for col, val in zip(cursor.description, row)}


def run(db_path: Path):
    if not db_path.exists():
        print(f"ERROR: {db_path} not found. Run import_json_to_sqlite.py first.", file=sys.stderr)
        sys.exit(1)

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    def fetch(query):
        cur = con.execute(query)
        return [dict(row) for row in cur.fetchall()]

    # --- simulants: restore original types ---
    simulants = fetch("SELECT * FROM simulants ORDER BY simulant_id")
    for s in simulants:
        # release_date: restore to int if numeric, else keep string
        if s["release_date"] is not None:
            try:
                s["release_date"] = int(s["release_date"])
            except (ValueError, TypeError):
                pass
        # bulk_density / cohesion / friction_angle: restore to number if possible
        for field in ("bulk_density", "cohesion", "friction_angle"):
            if s[field] is not None:
                try:
                    s[field] = float(s[field])
                except (ValueError, TypeError):
                    pass

    # --- simulant_extra: restore booleans ---
    simulant_extra = fetch("SELECT * FROM simulant_extra ORDER BY simulant_id")
    for e in simulant_extra:
        e["publicly_available_composition"] = bool(e["publicly_available_composition"])

    # --- sites: filter nulls (matches original useData.ts behavior) ---
    sites = fetch("SELECT * FROM sites WHERE lat IS NOT NULL AND lon IS NOT NULL ORDER BY site_id")

    # --- chemical_compositions ---
    chemical_compositions = fetch("SELECT * FROM chemical_compositions ORDER BY composition_id")

    # --- mineral_compositions ---
    compositions = fetch("SELECT * FROM mineral_compositions ORDER BY composition_id")

    # --- mineral_groups ---
    mineral_groups = fetch("SELECT * FROM mineral_groups ORDER BY group_id")

    # --- references ---
    references = fetch("SELECT * FROM references_ ORDER BY reference_id")

    # --- purchase_info ---
    purchase_info = fetch("SELECT * FROM purchase_info ORDER BY simulant_id")

    # --- lunar_references: deserialize JSON fields ---
    lunar_raw = fetch("SELECT * FROM lunar_references ORDER BY sample_id")
    lunar_reference = []
    for lr in lunar_raw:
        lr["coordinates"] = json.loads(lr["coordinates"]) if lr["coordinates"] else {}
        lr["chemical_composition"] = json.loads(lr["chemical_composition"]) if lr["chemical_composition"] else {}
        lr["mineral_composition"] = json.loads(lr["mineral_composition"]) if lr["mineral_composition"] else None
        lr["sources"] = json.loads(lr["sources"]) if lr["sources"] else []
        lunar_reference.append(lr)

    # --- mineral_sourcing: restore booleans ---
    mineral_sourcing = fetch("SELECT * FROM mineral_sourcing ORDER BY mineral_name")
    for ms in mineral_sourcing:
        for field in ("mine_active", "available_france", "available_europe", "available_schengen"):
            if ms[field] is not None:
                ms[field] = bool(ms[field])

    con.close()

    data = {
        "simulants": simulants,
        "sites": sites,
        "compositions": compositions,
        "chemical_compositions": chemical_compositions,
        "references": references,
        "mineral_groups": mineral_groups,
        "simulant_extra": simulant_extra,
        "lunar_reference": lunar_reference,
        "mineral_sourcing": mineral_sourcing,
        "purchase_info": purchase_info,
    }

    with open(OUTPUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))

    size_kb = OUTPUT.stat().st_size // 1024
    print(f"Exported to {OUTPUT} ({size_kb}KB)")
    for key, val in data.items():
        print(f"  {key:<30} {len(val)} records")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DEFAULT_DB), type=Path)
    args = parser.parse_args()
    run(args.db)

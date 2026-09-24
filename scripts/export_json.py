#!/usr/bin/env python3
"""
Export lrs.sqlite → public/data/data.json
Run this after editing the database to regenerate the frontend data file.

Usage:
    python3 scripts/export_json.py
    python3 scripts/export_json.py --db path/to/custom.sqlite

Provenance rule (documentation/data-policy.md, applied per value since 2026-09-22):
a scalar on `simulants` is exported only when property_sources holds a row for
(simulant_id, field). The database keeps the value; the export writes null and logs
every hidden value to documentation/export-suppression-<date>.json so the owner can
see what left the page. Composition rows are exported regardless; the simulant's
composition_status already governs them.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent.parent
DEFAULT_DB = ROOT / "lrs.sqlite"
OUTPUT = ROOT / "public" / "data" / "data.json"
DOC_DIR = ROOT / "documentation"

# Scalar fields on `simulants` that need a property_sources row to be exported.
# Identity fields (name, type, institution, availability, release date) and the
# composition-status bookkeeping columns are not measurements and are not gated.
SUPPRESSED_SCALAR_FIELDS = (
    "bulk_density",
    "cohesion",
    "friction_angle",
    "specific_gravity",
    "density_g_cm3",
    "particle_size_d50",
    "particle_size_distribution",
    "particle_morphology",
    "particle_ruggedness",
    "glass_content_percent",
    "nasa_fom_score",
    "ti_content_percent",
    "ph",
    "angle_of_repose",
    "particle_size_mean_um",
    "bulk_density_range",
    "magnetic_susceptibility",
)

# Physical values from simulant_extra (the Gasteiner compilation) shown in the Physical
# Properties grid: exported only with a source row, like everything else there.
SUPPRESSED_EXTRA_FIELDS = ("grain_size_mm",)


def suppress_unsourced_extra(extra: list[dict], property_sources: list[dict]) -> tuple[list[dict], int]:
    sourced = {(p["simulant_id"], p["field"]) for p in property_sources}
    n, out = 0, []
    for e in extra:
        e = dict(e)
        for f in SUPPRESSED_EXTRA_FIELDS:
            if e.get(f) not in (None, "") and (e["simulant_id"], f) not in sourced:
                e[f] = None
                n += 1
        out.append(e)
    return out, n


def shown_references(references: list[dict]) -> list[dict]:
    """A reference a reader confirmed does not name the product is kept in the database, as the
    record of that check, but not listed under the product (test 2: a reference must concern it)."""
    return [r for r in references if r.get("names_simulant") != 0]


# Reference columns that exist for verification only and never leave the machine.
# local_path is where the checked copy sits on the maintainer's disk; publishing it
# would put a private filesystem path into a public bundle.
PRIVATE_REFERENCE_COLUMNS = ("local_path",)


def row_to_dict(cursor, row):
    return {col[0]: val for col, val in zip(cursor.description, row)}


def suppress_unsourced_scalars(simulants: list, property_sources: list) -> list:
    """Null every gated scalar with no property_sources row. Mutates `simulants`.

    Returns one entry per hidden value: simulant_id, name, field and the value as the
    database holds it, so the suppression report shows exactly what left the page.
    """
    sourced = {(p["simulant_id"], p["field"]) for p in property_sources}
    hidden = []
    for s in simulants:
        for field in SUPPRESSED_SCALAR_FIELDS:
            value = s.get(field)
            if value is None or (s["simulant_id"], field) in sourced:
                continue
            hidden.append({"simulant_id": s["simulant_id"], "name": s.get("name"), "field": field, "value": value})
            s[field] = None
    return hidden


def write_suppression_report(hidden: list, report_dir: Path, today: str) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"export-suppression-{today}.json"
    report = {
        "generated": today,
        "rule": "A scalar on simulants is exported only when property_sources has a row for (simulant_id, field). "
                "These values remain in lrs.sqlite and are written as null in public/data/data.json.",
        "count": len(hidden),
        "by_field": dict(Counter(h["field"] for h in hidden).most_common()),
        "by_simulant": dict(Counter(h["simulant_id"] for h in hidden).most_common()),
        "suppressed": hidden,
    }
    with open(path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return path


def run(db_path: Path, output: Path = OUTPUT, report_dir: Path = DOC_DIR, today: str | None = None):
    if not db_path.exists():
        print(f"ERROR: {db_path} not found. Run import_json_to_sqlite.py first.", file=sys.stderr)
        sys.exit(1)

    today = today or dt.date.today().isoformat()
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    def fetch(query):
        cur = con.execute(query)
        return [dict(row) for row in cur.fetchall()]

    # --- property_sources: which scalar came from which document ---
    property_sources = fetch("SELECT * FROM property_sources ORDER BY simulant_id, field")
    # Figures of Merit: one cited score per (simulant, property, lunar reference).
    try:
        figures_of_merit = fetch("SELECT * FROM figures_of_merit WHERE reference_id IS NOT NULL ORDER BY simulant_id, property, reference_sample")
    except sqlite3.OperationalError:
        figures_of_merit = []

    # --- simulants: suppress unsourced scalars, then restore original types ---
    simulants = fetch("SELECT * FROM simulants ORDER BY simulant_id")
    hidden = suppress_unsourced_scalars(simulants, property_sources)
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
    simulant_extra, hidden_extra = suppress_unsourced_extra(simulant_extra, property_sources)
    if hidden_extra:
        print(f"Suppressed {hidden_extra} unsourced grain size value(s) from the Gasteiner compilation")

    # --- sites: filter nulls (matches original useData.ts behavior) ---
    sites = fetch("SELECT * FROM sites WHERE lat IS NOT NULL AND lon IS NOT NULL ORDER BY site_id")

    # --- chemical_compositions (reference_id rides along via SELECT *) ---
    chemical_compositions = fetch("SELECT * FROM chemical_compositions ORDER BY composition_id")

    # --- mineral_compositions (reference_id rides along via SELECT *) ---
    compositions = fetch("SELECT * FROM mineral_compositions ORDER BY composition_id")

    # --- mineral_groups ---
    mineral_groups = fetch("SELECT * FROM mineral_groups ORDER BY group_id")

    # --- references: the registry of documents; drop verification-only columns ---
    references = shown_references(fetch("SELECT * FROM references_ ORDER BY reference_id"))
    for r in references:
        for col in PRIVATE_REFERENCE_COLUMNS:
            r.pop(col, None)

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
        "property_sources": property_sources,
        "figures_of_merit": figures_of_merit,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(data, f, separators=(",", ":"))

    report_path = write_suppression_report(hidden, report_dir, today)

    size_kb = output.stat().st_size // 1024
    print(f"Exported to {output} ({size_kb}KB)")
    for key, val in data.items():
        print(f"  {key:<30} {len(val)} records")
    print(f"Suppressed {len(hidden)} unsourced scalar values (kept in the database); see {report_path}")
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DEFAULT_DB), type=Path)
    args = parser.parse_args()
    run(args.db)

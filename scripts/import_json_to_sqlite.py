#!/usr/bin/env python3
"""
One-time migration: public/data/*.json → lrs.sqlite
After this runs, lrs.sqlite is the source of truth.
Edit data in the DB, then run export_json.py to regenerate public/data/data.json.

Usage:
    python3 scripts/import_json_to_sqlite.py
    python3 scripts/import_json_to_sqlite.py --db path/to/custom.sqlite
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "public" / "data"
SCHEMA = Path(__file__).parent / "schema.sql"


def load(filename: str):
    path = DATA_DIR / filename
    with open(path) as f:
        return json.load(f)


def run(db_path: Path):
    if db_path.exists():
        print(f"Removing existing {db_path}")
        db_path.unlink()

    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA.read_text())

    # --- simulants ---
    simulants = load("simulant.json")
    con.executemany("""
        INSERT OR REPLACE INTO simulants VALUES (
            :simulant_id, :name, :type, :country_code, :institution,
            :availability, :release_date, :tons_produced_mt, :notes,
            :specific_gravity, :lunar_sample_reference,
            :bulk_density, :cohesion, :friction_angle,
            :density_g_cm3, :particle_size_d50, :particle_size_distribution,
            :particle_morphology, :particle_ruggedness, :glass_content_percent,
            :nasa_fom_score, :ti_content_percent
        )
    """, [{
        "simulant_id": s["simulant_id"],
        "name": s.get("name"),
        "type": s.get("type"),
        "country_code": s.get("country_code"),
        "institution": s.get("institution"),
        "availability": s.get("availability"),
        "release_date": str(s["release_date"]) if s.get("release_date") is not None else None,
        "tons_produced_mt": s.get("tons_produced_mt"),
        "notes": s.get("notes"),
        "specific_gravity": s.get("specific_gravity"),
        "lunar_sample_reference": s.get("lunar_sample_reference"),
        "bulk_density": str(s["bulk_density"]) if s.get("bulk_density") is not None else None,
        "cohesion": str(s["cohesion"]) if s.get("cohesion") is not None else None,
        "friction_angle": str(s["friction_angle"]) if s.get("friction_angle") is not None else None,
        "density_g_cm3": s.get("density_g_cm3"),
        "particle_size_d50": s.get("particle_size_d50"),
        "particle_size_distribution": s.get("particle_size_distribution"),
        "particle_morphology": s.get("particle_morphology"),
        "particle_ruggedness": s.get("particle_ruggedness"),
        "glass_content_percent": s.get("glass_content_percent"),
        "nasa_fom_score": s.get("nasa_fom_score"),
        "ti_content_percent": s.get("ti_content_percent"),
    } for s in simulants])
    print(f"  simulants:             {len(simulants)}")

    # --- simulant_extra ---
    extras = load("simulant_extra.json")
    con.executemany("""
        INSERT OR REPLACE INTO simulant_extra VALUES (
            :simulant_id, :name, :classification, :application, :replica_of,
            :feedstock, :petrographic_class, :grain_size_mm, :specific_gravity,
            :publicly_available_composition, :reference
        )
    """, [{
        **e,
        "publicly_available_composition": 1 if e.get("publicly_available_composition") else 0,
    } for e in extras])
    print(f"  simulant_extra:        {len(extras)}")

    # --- sites ---
    sites = load("site.json")
    con.executemany("""
        INSERT OR REPLACE INTO sites VALUES (
            :site_id, :simulant_id, :site_name, :site_type, :country_code, :lat, :lon
        )
    """, sites)
    print(f"  sites:                 {len(sites)}")

    # --- chemical_compositions ---
    chem = load("chemical_composition.json")
    con.executemany("""
        INSERT OR REPLACE INTO chemical_compositions VALUES (
            :composition_id, :simulant_id, :component_type, :component_name, :value_wt_pct
        )
    """, [{"composition_id": c["composition_id"], "simulant_id": c["simulant_id"],
           "component_type": c.get("component_type"), "component_name": c.get("component_name"),
           "value_wt_pct": c.get("value_wt_pct")} for c in chem])
    print(f"  chemical_compositions: {len(chem)}")

    # --- mineral_compositions ---
    comp = load("composition.json")
    con.executemany("""
        INSERT OR REPLACE INTO mineral_compositions VALUES (
            :composition_id, :simulant_id, :component_type, :component_name, :value_pct
        )
    """, [{"composition_id": c["composition_id"], "simulant_id": c["simulant_id"],
           "component_type": c.get("component_type"), "component_name": c.get("component_name"),
           "value_pct": c.get("value_pct")} for c in comp])
    print(f"  mineral_compositions:  {len(comp)}")

    # --- mineral_groups ---
    groups = load("mineral_groups.json")
    con.executemany("""
        INSERT OR REPLACE INTO mineral_groups VALUES (
            :group_id, :simulant_id, :group_name, :value_pct
        )
    """, groups)
    print(f"  mineral_groups:        {len(groups)}")

    # --- references ---
    refs = load("references.json")
    con.executemany("""
        INSERT OR REPLACE INTO references_ VALUES (
            :reference_id, :simulant_id, :reference_text, :reference_type,
            :title, :authors, :year, :doi, :url
        )
    """, [{
        "reference_id": r["reference_id"],
        "simulant_id": r.get("simulant_id"),
        "reference_text": r.get("reference_text"),
        "reference_type": r.get("reference_type"),
        "title": r.get("title"),
        "authors": r.get("authors"),
        "year": r.get("year"),
        "doi": r.get("doi"),
        "url": r.get("url"),
    } for r in refs])
    print(f"  references:            {len(refs)}")

    # --- purchase_info ---
    purchase = load("purchase_info.json")
    con.executemany("""
        INSERT OR REPLACE INTO purchase_info VALUES (
            :simulant_id, :vendor, :url, :price_note
        )
    """, purchase)
    print(f"  purchase_info:         {len(purchase)}")

    # --- lunar_references ---
    lunar = load("lunar_reference.json")
    con.executemany("""
        INSERT OR REPLACE INTO lunar_references VALUES (
            :sample_id, :mission, :landing_site, :coordinates, :type,
            :sample_description, :chemical_composition, :mineral_composition, :sources
        )
    """, [{
        "sample_id": lr["sample_id"],
        "mission": lr.get("mission"),
        "landing_site": lr.get("landing_site"),
        "coordinates": json.dumps(lr.get("coordinates")),
        "type": lr.get("type"),
        "sample_description": lr.get("sample_description"),
        "chemical_composition": json.dumps(lr.get("chemical_composition")),
        "mineral_composition": json.dumps(lr.get("mineral_composition")) if lr.get("mineral_composition") else None,
        "sources": json.dumps(lr.get("sources", [])),
    } for lr in lunar])
    print(f"  lunar_references:      {len(lunar)}")

    # --- mineral_sourcing ---
    sourcing = load("mineral_sourcing.json")
    con.executemany("""
        INSERT OR REPLACE INTO mineral_sourcing VALUES (
            :mineral_name, :chemistry, :source_mineral, :description,
            :description_simple, :comments, :mineral_locations, :mining_locations,
            :mining_company, :mine_active, :ethical_compliance,
            :available_france, :available_europe, :available_schengen,
            :supplier, :further_reading, :european_sources, :european_locations_detail
        )
    """, [{
        **ms,
        "mine_active": 1 if ms.get("mine_active") else 0,
        "available_france": 1 if ms.get("available_france") else 0,
        "available_europe": 1 if ms.get("available_europe") else 0,
        "available_schengen": 1 if ms.get("available_schengen") else 0,
        "comments": ms.get("comments"),
        "european_locations_detail": ms.get("european_locations_detail"),
    } for ms in sourcing])
    print(f"  mineral_sourcing:      {len(sourcing)}")

    con.commit()
    con.close()

    size_kb = db_path.stat().st_size // 1024
    print(f"\nDatabase written to {db_path} ({size_kb}KB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(ROOT / "lrs.sqlite"), type=Path)
    args = parser.parse_args()
    print(f"Importing JSON → {args.db}")
    run(args.db)

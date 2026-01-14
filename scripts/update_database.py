#!/usr/bin/env python3
"""
Database updater with options:
  --auto-only    : Only auto-fill empty fields (no conflicts)
  --show-conflicts: Show all conflicts for review
  --interactive  : Run interactively (prompts for each conflict)
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_FILE = SCRIPT_DIR.parent / "data" / "simulant.json"
RESULTS_FILE = SCRIPT_DIR / "extraction_results" / "all_results.json"
BACKUP_FILE = SCRIPT_DIR.parent / "data" / f"simulant_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# Fields to update
FIELDS_TO_UPDATE = [
    "institution",
    "availability",
    "release_date",
    "tons_produced_mt",
    "notes",
    "type",
    "lunar_sample_reference",
    "density_g_cm3",
    "specific_gravity",
    "particle_size_distribution",
    "particle_morphology",
    "particle_ruggedness",
    "glass_content_percent",
    "ti_content_percent",
    "nanophase_iron_content",
    "nasa_fom_score",
]


def load_database():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def load_extractions():
    with open(RESULTS_FILE, 'r') as f:
        return json.load(f)


def is_empty(value):
    return value is None or value == "" or value == "null"


def analyze_changes(database, extractions):
    """Analyze all potential changes"""
    extraction_map = {r['simulant_id']: r for r in extractions['results']}

    auto_fills = []
    conflicts = []

    for simulant in database:
        sim_id = simulant.get('simulant_id', '')
        name = simulant.get('name', '')

        extraction = extraction_map.get(sim_id, {})
        aggregated = extraction.get('aggregated', {})

        if not aggregated:
            continue

        for field in FIELDS_TO_UPDATE:
            existing = simulant.get(field)
            extracted = aggregated.get(field)

            if not extracted:
                continue

            if is_empty(existing):
                auto_fills.append({
                    'sim_id': sim_id,
                    'name': name,
                    'field': field,
                    'value': extracted
                })
            elif str(existing).lower().strip() != str(extracted).lower().strip():
                conflicts.append({
                    'sim_id': sim_id,
                    'name': name,
                    'field': field,
                    'existing': existing,
                    'extracted': extracted
                })

    return auto_fills, conflicts


def apply_auto_fills(database, auto_fills):
    """Apply auto-fills to database"""
    updates_by_id = {}
    for af in auto_fills:
        sim_id = af['sim_id']
        if sim_id not in updates_by_id:
            updates_by_id[sim_id] = {}
        updates_by_id[sim_id][af['field']] = af['value']

    for simulant in database:
        sim_id = simulant.get('simulant_id', '')
        if sim_id in updates_by_id:
            for field, value in updates_by_id[sim_id].items():
                simulant[field] = value

    return database


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--auto-only'

    print("="*70)
    print("DATABASE UPDATE")
    print("="*70)

    database = load_database()
    extractions = load_extractions()

    print(f"Database: {len(database)} simulants")
    print(f"Extractions: {len(extractions['results'])} results")

    auto_fills, conflicts = analyze_changes(database, extractions)

    print(f"\nAnalysis:")
    print(f"  Auto-fills (empty fields): {len(auto_fills)}")
    print(f"  Conflicts (needs review):  {len(conflicts)}")

    if mode == '--show-conflicts':
        print("\n" + "="*70)
        print("ALL CONFLICTS")
        print("="*70)
        for c in conflicts:
            print(f"\n{c['name']} - {c['field']}:")
            print(f"  EXISTING (manual): {c['existing']}")
            print(f"  EXTRACTED (AI):    {c['extracted']}")
        return

    if mode == '--auto-only':
        if not auto_fills:
            print("\nNo empty fields to auto-fill.")
            return

        print("\n" + "="*70)
        print(f"AUTO-FILLING {len(auto_fills)} EMPTY FIELDS")
        print("="*70)

        # Show what will be filled
        print("\nChanges to apply:")
        for af in auto_fills:
            val_str = str(af['value'])[:50]
            print(f"  {af['name']}.{af['field']} = {val_str}")

        # Create backup
        print(f"\nCreating backup: {BACKUP_FILE}")
        with open(BACKUP_FILE, 'w') as f:
            json.dump(database, f, indent=2)

        # Apply changes
        database = apply_auto_fills(database, auto_fills)

        # Save
        with open(DATA_FILE, 'w') as f:
            json.dump(database, f, indent=2)

        print(f"\n✅ Done! {len(auto_fills)} fields updated.")
        print(f"   Backup: {BACKUP_FILE}")

        if conflicts:
            print(f"\n⚠️  {len(conflicts)} conflicts NOT updated (existing data preserved).")
            print("   Run with --show-conflicts to review them.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Usage: python update_database.py [option]")
        print("  --auto-only      Auto-fill empty fields only (default)")
        print("  --show-conflicts Show all conflicts for manual review")
    else:
        main()

#!/usr/bin/env python3
"""
Import curated composition data from specsheet_data.json into the database.

Rules:
1. Manual data prevails - never overwrite existing entries
2. Validate totals sum to ~100% before adding
3. Show detailed preview before committing
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'
SCRIPT_DIR = Path(__file__).parent


def get_simulant_id(simulant_name: str, simulants: list) -> str:
    """Find simulant ID by name."""
    for s in simulants:
        if s['name'] == simulant_name:
            return s['simulant_id']
    return None


def get_existing_data(simulant_id: str, compositions: list, chemicals: list) -> tuple:
    """Get existing mineral and chemical names for a simulant."""
    existing_minerals = {
        c['component_name']
        for c in compositions
        if c['simulant_id'] == simulant_id and c.get('component_type') == 'mineral'
    }
    existing_chemicals = {
        c['component_name']
        for c in chemicals
        if c['simulant_id'] == simulant_id
    }
    return existing_minerals, existing_chemicals


def main():
    # Load curated data
    with open(SCRIPT_DIR / 'specsheet_data.json') as f:
        curated = json.load(f)

    # Load database
    with open(DATA_DIR / 'simulant.json') as f:
        simulants = json.load(f)

    with open(DATA_DIR / 'composition.json') as f:
        compositions = json.load(f)

    with open(DATA_DIR / 'chemical_composition.json') as f:
        chemicals = json.load(f)

    # Get next IDs
    max_comp_id = max(int(c['composition_id'][1:]) for c in compositions) if compositions else 0
    max_chem_id = max(int(c['composition_id'][2:]) for c in chemicals) if chemicals else 0

    new_minerals = []
    new_chemicals = []
    skipped = []

    print("=" * 60)
    print("Importing curated composition data")
    print("=" * 60)

    for sim_name, data in curated['simulants'].items():
        print(f"\n→ {sim_name} (source: {data['source']})")

        # Find simulant ID
        sim_id = get_simulant_id(sim_name, simulants)
        if not sim_id:
            print(f"  ✗ Not found in database")
            skipped.append((sim_name, "Not in database"))
            continue

        print(f"  Simulant ID: {sim_id}")

        # Check existing data
        existing_mins, existing_chems = get_existing_data(sim_id, compositions, chemicals)

        # Validate mineral totals
        mineral_total = sum(data.get('minerals', {}).values())
        chemical_total = sum(data.get('chemicals', {}).values())

        print(f"  Mineral total: {mineral_total:.1f}%")
        print(f"  Chemical total: {chemical_total:.1f}%")

        if mineral_total > 105:
            print(f"  ✗ Mineral total too high - SKIPPED")
            skipped.append((sim_name, f"Mineral total {mineral_total:.1f}% > 105%"))
            continue

        if chemical_total > 105:
            print(f"  ✗ Chemical total too high - SKIPPED")
            skipped.append((sim_name, f"Chemical total {chemical_total:.1f}% > 105%"))
            continue

        # Process minerals
        if existing_mins:
            print(f"  ⚠ Already has {len(existing_mins)} minerals - preserving manual data")
        elif data.get('minerals'):
            print(f"  + Adding {len(data['minerals'])} minerals:")
            for mineral, value in data['minerals'].items():
                max_comp_id += 1
                entry = {
                    "composition_id": f"C{max_comp_id:03d}",
                    "simulant_id": sim_id,
                    "component_type": "mineral",
                    "component_name": mineral,
                    "value_pct": value
                }
                new_minerals.append(entry)
                print(f"      {mineral}: {value}%")

        # Process chemicals
        if existing_chems:
            print(f"  ⚠ Already has {len(existing_chems)} chemicals - preserving manual data")
        elif data.get('chemicals'):
            print(f"  + Adding {len(data['chemicals'])} chemicals:")
            for chemical, value in data['chemicals'].items():
                max_chem_id += 1
                entry = {
                    "composition_id": f"CH{max_chem_id:03d}",
                    "simulant_id": sim_id,
                    "component_type": "oxide",
                    "component_name": chemical,
                    "value_wt_pct": value
                }
                new_chemicals.append(entry)
                print(f"      {chemical}: {value}%")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  New mineral entries: {len(new_minerals)}")
    print(f"  New chemical entries: {len(new_chemicals)}")

    if skipped:
        print(f"\n  Skipped ({len(skipped)}):")
        for name, reason in skipped:
            print(f"    - {name}: {reason}")

    # Save
    if new_minerals or new_chemicals:
        response = input("\nSave changes? [y/N]: ")
        if response.lower() == 'y':
            if new_minerals:
                compositions.extend(new_minerals)
                with open(DATA_DIR / 'composition.json', 'w') as f:
                    json.dump(compositions, f, indent=2)
                print(f"  ✓ Saved {len(new_minerals)} minerals")

            if new_chemicals:
                chemicals.extend(new_chemicals)
                with open(DATA_DIR / 'chemical_composition.json', 'w') as f:
                    json.dump(chemicals, f, indent=2)
                print(f"  ✓ Saved {len(new_chemicals)} chemicals")

            print("\n  Don't forget to regenerate mineral_groups.json!")
        else:
            print("  Not saved.")


if __name__ == '__main__':
    main()

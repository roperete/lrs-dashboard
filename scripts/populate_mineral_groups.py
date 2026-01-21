#!/usr/bin/env python3
"""
Populate mineral_groups.json by mapping detailed minerals to NASA mineral groups.

NASA Mineral Groups (used in Figures of Merit methodology):
1. Plagioclase Feldspar - calcium-sodium feldspars
2. Pyroxene - single-chain inosilicates
3. Olivine - nesosilicates (Mg,Fe)2SiO4
4. Ilmenite - iron-titanium oxide FeTiO3
5. Glass/Agglutinate - volcanic/impact glass
"""

import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / 'data'

# Mapping from detailed mineral names to NASA groups
# Based on mineralogical classification
MINERAL_TO_GROUP = {
    # Plagioclase Feldspar group (Ca-Na feldspars)
    'Plagioclase': 'Plagioclase Feldspar',
    'Anorthite': 'Plagioclase Feldspar',      # Ca-rich plagioclase
    'Labradorite': 'Plagioclase Feldspar',    # Intermediate plagioclase
    'Bytownite': 'Plagioclase Feldspar',      # Ca-rich plagioclase
    'Albite': 'Plagioclase Feldspar',         # Na-rich plagioclase
    'Anorthosite': 'Plagioclase Feldspar',    # Plagioclase-rich rock (treat as mineral)
    'Feldspar': 'Plagioclase Feldspar',       # Generic feldspar, assume plagioclase for lunar

    # Pyroxene group (single-chain silicates)
    'Pyroxene': 'Pyroxene',
    'Augite': 'Pyroxene',                     # Clinopyroxene
    'Clinopyroxene': 'Pyroxene',
    'Orthopyroxene': 'Pyroxene',
    'Bronzite': 'Pyroxene',                   # Mg-rich orthopyroxene
    'Pigeonite': 'Pyroxene',                  # Ca-poor clinopyroxene
    'Diopside': 'Pyroxene',                   # Ca-Mg clinopyroxene
    'Enstatite': 'Pyroxene',                  # Mg orthopyroxene
    'Hypersthene': 'Pyroxene',                # Fe-Mg orthopyroxene

    # Olivine group (nesosilicates)
    'Olivine': 'Olivine',
    'Forsterite': 'Olivine',                  # Mg-rich olivine
    'Fayalite': 'Olivine',                    # Fe-rich olivine

    # Ilmenite (Fe-Ti oxide)
    'Ilmenite': 'Ilmenite',

    # Glass/Agglutinate (volcanic and impact glass)
    'Glass': 'Glass',
    'Volcanic Glass': 'Glass',
    'Agglutinate': 'Glass',
    'Basaltic Ash': 'Glass',                  # Treat as glassy material

    # Other minerals that don't fit NASA groups (will be tracked separately)
    # These are excluded from the standard 5 NASA groups
    # K-feldspar, Quartz, Magnetite, Ti-magnetite, Cr-spinel, Hematite,
    # Biotite, Clinochlore, Illite, Smectite, Apatite, Sulfide, Basalt, Norite
}

# Standard NASA groups
NASA_GROUPS = ['Plagioclase Feldspar', 'Pyroxene', 'Olivine', 'Ilmenite', 'Glass']


def parse_composite_mineral(name: str, value: float) -> dict:
    """
    Handle composite mineral entries like 'Olivine + pyroxene + ilmenite'.
    Returns a dict of {group: value} with the value split among components.
    """
    name_lower = name.lower()

    if '+' in name_lower:
        # Split composite minerals
        parts = [p.strip() for p in name_lower.split('+')]
        result = {}

        for part in parts:
            # Find matching group
            for mineral, group in MINERAL_TO_GROUP.items():
                if mineral.lower() in part or part in mineral.lower():
                    if group not in result:
                        result[group] = 0
                    result[group] += value / len(parts)
                    break

        return result

    return {}


def main():
    # Load data
    composition_path = DATA_DIR / 'composition.json'
    simulants_path = DATA_DIR / 'simulant.json'
    groups_path = DATA_DIR / 'mineral_groups.json'

    with open(composition_path) as f:
        compositions = json.load(f)

    with open(simulants_path) as f:
        simulants = json.load(f)

    # Load existing mineral groups (to preserve manually entered data like TDS sheets)
    existing_groups = []
    if groups_path.exists():
        with open(groups_path) as f:
            existing_groups = json.load(f)

    # Track which simulants already have group data
    existing_simulant_ids = set(g['simulant_id'] for g in existing_groups)

    # Create simulant lookup
    sim_lookup = {s['simulant_id']: s['name'] for s in simulants}

    # Aggregate minerals by simulant
    simulant_minerals = defaultdict(lambda: defaultdict(float))

    for comp in compositions:
        if comp.get('component_type') != 'mineral':
            continue

        sim_id = comp.get('simulant_id')
        mineral_name = comp.get('component_name', '')
        value = comp.get('value_pct', 0) or 0

        if not sim_id or not mineral_name:
            continue

        # Check if it's a composite mineral
        if '+' in mineral_name:
            composite_values = parse_composite_mineral(mineral_name, value)
            for group, group_value in composite_values.items():
                simulant_minerals[sim_id][group] += group_value
        # Check if mineral maps to a NASA group
        elif mineral_name in MINERAL_TO_GROUP:
            group = MINERAL_TO_GROUP[mineral_name]
            simulant_minerals[sim_id][group] += value

    # Generate new mineral group entries
    new_groups = []
    group_id_counter = len(existing_groups) + 1

    stats = {
        'simulants_processed': 0,
        'simulants_with_data': 0,
        'groups_added': 0,
        'simulants_skipped': 0
    }

    for sim_id, group_totals in simulant_minerals.items():
        # Skip if simulant already has group data (from TDS sheets)
        if sim_id in existing_simulant_ids:
            stats['simulants_skipped'] += 1
            continue

        stats['simulants_processed'] += 1

        if not group_totals:
            continue

        stats['simulants_with_data'] += 1
        sim_name = sim_lookup.get(sim_id, sim_id)

        # Create entries for all 5 NASA groups (even if 0%)
        for group_name in NASA_GROUPS:
            value = round(group_totals.get(group_name, 0), 2)

            new_groups.append({
                'group_id': f'MG{group_id_counter:03d}',
                'simulant_id': sim_id,
                'group_name': group_name,
                'value_pct': value
            })
            group_id_counter += 1
            stats['groups_added'] += 1

    # Combine existing and new groups
    all_groups = existing_groups + new_groups

    # Save updated mineral groups
    with open(groups_path, 'w') as f:
        json.dump(all_groups, f, indent=2)

    print("=" * 60)
    print("Mineral Groups Population Complete")
    print("=" * 60)
    print(f"  Simulants processed: {stats['simulants_processed']}")
    print(f"  Simulants with mineral data: {stats['simulants_with_data']}")
    print(f"  Simulants skipped (existing data): {stats['simulants_skipped']}")
    print(f"  New group entries added: {stats['groups_added']}")
    print(f"  Total entries in mineral_groups.json: {len(all_groups)}")
    print()

    # Show sample of new data
    print("Sample of newly populated data:")
    seen_sims = set()
    for g in new_groups[:25]:
        sim_name = sim_lookup.get(g['simulant_id'], g['simulant_id'])
        if sim_name not in seen_sims:
            print(f"\n  {sim_name}:")
            seen_sims.add(sim_name)
        if g['value_pct'] > 0:
            print(f"    - {g['group_name']}: {g['value_pct']}%")

    # Show unmapped minerals
    unmapped = set()
    for comp in compositions:
        if comp.get('component_type') == 'mineral':
            name = comp.get('component_name', '')
            if name and name not in MINERAL_TO_GROUP and '+' not in name:
                unmapped.add(name)

    if unmapped:
        print(f"\n\nUnmapped minerals (not in NASA groups):")
        for m in sorted(unmapped):
            print(f"    - {m}")


if __name__ == '__main__':
    main()

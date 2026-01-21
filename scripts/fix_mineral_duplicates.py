#!/usr/bin/env python3
"""
Fix mineral composition data where multiple sources caused duplicates/overlaps.

Strategy:
1. Identify simulants with totals significantly over 100%
2. For those cases, identify the most coherent dataset
3. Keep entries that form a complete picture (~100%)
"""

import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / 'data'

# Direct name mappings (these ARE the same thing)
SAME_AS = {
    'Anorthosite': 'Plagioclase',     # Anorthosite rock = plagioclase mineral
    'Volcanic Glass': 'Glass',
    'Feldspar': 'Plagioclase',        # Generic feldspar → plagioclase (lunar context)
}

# Rock types to exclude if we have actual minerals
ROCK_TYPES = {'Basalt', 'Norite'}

# Known sub-types that should NOT overlap with parent
# If we see both, it's duplicate data
PARENT_CHILD = {
    'Plagioclase': {'Anorthite', 'Labradorite', 'Bytownite', 'Albite'},
    'Pyroxene': {'Augite', 'Clinopyroxene', 'Orthopyroxene', 'Bronzite', 'Pigeonite'},
    'Olivine': {'Forsterite', 'Fayalite'},
    'Feldspar': {'Plagioclase', 'K-feldspar'},
}


def get_best_value(entries):
    """Get the best value from multiple entries for same mineral."""
    if not entries:
        return None
    # Prefer the highest value (usually more complete analysis)
    return max(entries, key=lambda e: e.get('value_pct', 0) or 0)


def fix_minerals(minerals_list, simulant_name):
    """Fix mineral list by removing duplicate sources."""
    if not minerals_list:
        return minerals_list

    total = sum(m.get('value_pct', 0) or 0 for m in minerals_list)

    # Group by mineral name
    by_name = defaultdict(list)
    for m in minerals_list:
        name = m.get('component_name', '')
        # Normalize names
        if name in SAME_AS:
            name = SAME_AS[name]
            m = dict(m)  # Copy to avoid modifying original
            m['component_name'] = name
        by_name[name].append(m)

    mineral_names = set(by_name.keys())
    to_remove = set()

    # Remove rock types if we have real mineral data
    real_total = sum(
        m.get('value_pct', 0) or 0
        for m in minerals_list
        if m.get('component_name') not in ROCK_TYPES
    )
    if real_total > 30:
        to_remove.update(ROCK_TYPES)

    # If total is reasonable (<= 110%), just clean up duplicates
    if total <= 110:
        cleaned = []
        for name, entries in by_name.items():
            if name in to_remove:
                continue
            best = get_best_value(entries)
            if best:
                cleaned.append(best)
        return cleaned

    # Total is too high - we have overlapping data sources
    # Strategy: Check for parent/child overlaps which indicate duplicate sources

    for parent, children in PARENT_CHILD.items():
        if parent in mineral_names:
            children_present = mineral_names & children
            if children_present:
                parent_value = sum(e.get('value_pct', 0) or 0 for e in by_name[parent])
                children_value = sum(
                    sum(e.get('value_pct', 0) or 0 for e in by_name[child])
                    for child in children_present
                )
                # If parent value is much larger, it's probably the total - remove children
                # If children values are larger or similar, they're the detailed breakdown - remove parent
                if parent_value > children_value * 1.5:
                    # Keep parent (it's the total), remove children
                    to_remove.update(children_present)
                else:
                    # Keep children (detailed), remove parent
                    to_remove.add(parent)

    # Build cleaned list
    cleaned = []
    for name, entries in by_name.items():
        if name in to_remove:
            continue
        best = get_best_value(entries)
        if best:
            cleaned.append(best)

    # Check if still over 100% after cleaning
    new_total = sum(m.get('value_pct', 0) or 0 for m in cleaned)

    if new_total > 115:
        # Still too high - might have completely duplicate datasets
        # Sort by value and take entries until we hit ~100%
        cleaned.sort(key=lambda m: -(m.get('value_pct', 0) or 0))
        final = []
        running_total = 0
        for m in cleaned:
            val = m.get('value_pct', 0) or 0
            if running_total + val <= 105 or running_total < 50:
                final.append(m)
                running_total += val
            # else: skip this entry as it would push us too far over
        return final

    return cleaned


def analyze_simulant_minerals(minerals_list):
    """Analyze a list of minerals for a single simulant."""
    total = sum(m.get('value_pct', 0) or 0 for m in minerals_list)
    return {
        'total': total,
        'count': len(minerals_list),
        'has_overlap': total > 110,
        'names': [m.get('component_name') for m in minerals_list]
    }


def main():
    # Load data
    composition_path = DATA_DIR / 'composition.json'
    simulants_path = DATA_DIR / 'simulant.json'

    with open(composition_path) as f:
        compositions = json.load(f)

    with open(simulants_path) as f:
        simulants = json.load(f)

    sim_lookup = {s['simulant_id']: s['name'] for s in simulants}

    # Separate minerals from other compositions
    minerals = [c for c in compositions if c.get('component_type') == 'mineral']
    other = [c for c in compositions if c.get('component_type') != 'mineral']

    # Group minerals by simulant
    by_simulant = defaultdict(list)
    for m in minerals:
        by_simulant[m.get('simulant_id')].append(m)

    # Analyze and fix each simulant
    fixed_minerals = []
    stats = {
        'simulants_checked': 0,
        'simulants_fixed': 0,
        'entries_removed': 0,
        'original_entries': len(minerals)
    }

    print("Analyzing mineral data...")
    print("=" * 60)

    for sim_id, sim_minerals in by_simulant.items():
        sim_name = sim_lookup.get(sim_id, sim_id)
        stats['simulants_checked'] += 1

        analysis = analyze_simulant_minerals(sim_minerals)

        if analysis['total'] > 105:
            print(f"\n{sim_name} ({sim_id}):")
            print(f"  Before: {analysis['count']} minerals, total={analysis['total']:.1f}%")

            cleaned = fix_minerals(sim_minerals, sim_name)
            new_analysis = analyze_simulant_minerals(cleaned)

            print(f"  After:  {new_analysis['count']} minerals, total={new_analysis['total']:.1f}%")

            removed = analysis['count'] - new_analysis['count']
            if removed > 0:
                stats['simulants_fixed'] += 1
                stats['entries_removed'] += removed

            fixed_minerals.extend(cleaned)
        else:
            # Keep as-is but still dedupe same-name entries
            cleaned = fix_minerals(sim_minerals, sim_name)
            fixed_minerals.extend(cleaned)

    # Recombine with other compositions
    new_compositions = other + fixed_minerals

    # Sort by composition_id
    new_compositions.sort(key=lambda x: x.get('composition_id', 'Z999'))

    # Save
    with open(composition_path, 'w') as f:
        json.dump(new_compositions, f, indent=2)

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Simulants checked: {stats['simulants_checked']}")
    print(f"  Simulants fixed: {stats['simulants_fixed']}")
    print(f"  Entries removed: {stats['entries_removed']}")
    print(f"  Original mineral entries: {stats['original_entries']}")
    print(f"  New mineral entries: {len(fixed_minerals)}")

    # Verify results
    print("\n" + "=" * 60)
    print("Verification - remaining totals over 100%:")
    any_over = False
    for sim_id, sim_minerals in by_simulant.items():
        cleaned = [m for m in fixed_minerals if m.get('simulant_id') == sim_id]
        total = sum(m.get('value_pct', 0) or 0 for m in cleaned)
        if total > 105:
            sim_name = sim_lookup.get(sim_id, sim_id)
            print(f"  {sim_name}: {total:.1f}%")
            any_over = True
    if not any_over:
        print("  None! All simulants now have totals <= 105%")


if __name__ == '__main__':
    main()

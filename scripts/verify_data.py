#!/usr/bin/env python3
"""Verify referential integrity across all JSON data files.

Usage:
    python scripts/verify_data.py
"""

import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).resolve().parent.parent / "public" / "data"


def load(name):
    with open(DATA_DIR / name) as f:
        return json.load(f)


def main():
    print("=== LRS Data Verification ===\n")

    simulants = load("simulant.json")
    extras = load("simulant_extra.json")
    sites = load("site.json")
    compositions = load("composition.json")
    chemicals = load("chemical_composition.json")
    references = load("references.json")
    mineral_groups = load("mineral_groups.json")
    mineral_sourcing = load("mineral_sourcing.json")
    lunar_ref = load("lunar_reference.json")

    sim_ids = {s["simulant_id"] for s in simulants}
    errors = []
    warnings = []

    # 1. Duplicate simulant IDs
    id_counts = Counter(s["simulant_id"] for s in simulants)
    for sid, count in id_counts.items():
        if count > 1:
            errors.append(f"Duplicate simulant_id: {sid} ({count} times)")

    # 2. Every extra has a matching simulant
    for e in extras:
        if e["simulant_id"] not in sim_ids:
            errors.append(f"simulant_extra orphan: {e['simulant_id']} ({e.get('name')})")

    # 3. Every site has a matching simulant
    for s in sites:
        if s["simulant_id"] not in sim_ids:
            errors.append(f"site orphan: {s['simulant_id']} ({s.get('site_name')})")

    # 4. Every composition has a matching simulant
    for c in compositions:
        if c["simulant_id"] not in sim_ids:
            errors.append(f"composition orphan: {c['simulant_id']} ({c.get('mineral_name')})")

    # 5. Every chemical has a matching simulant
    for c in chemicals:
        if c["simulant_id"] not in sim_ids:
            errors.append(f"chemical orphan: {c['simulant_id']} ({c.get('oxide')})")

    # 6. Every reference has a matching simulant
    for r in references:
        if r["simulant_id"] not in sim_ids:
            errors.append(f"reference orphan: {r['simulant_id']}")

    # 7. Every mineral group has a matching simulant
    for mg in mineral_groups:
        if mg["simulant_id"] not in sim_ids:
            errors.append(f"mineral_group orphan: {mg['simulant_id']}")

    # 8. Required fields check
    for s in simulants:
        if not s.get("name"):
            errors.append(f"Simulant {s['simulant_id']} missing name")
        if not s.get("simulant_id"):
            errors.append(f"Simulant missing simulant_id")

    # 9. Coverage stats
    sids_with_comp = set(c["simulant_id"] for c in compositions)
    sids_with_chem = set(c["simulant_id"] for c in chemicals)
    sids_with_ref = set(r["simulant_id"] for r in references)
    sids_with_site = set(s["simulant_id"] for s in sites)
    sids_with_extra = set(e["simulant_id"] for e in extras)

    no_comp = sim_ids - sids_with_comp
    no_chem = sim_ids - sids_with_chem
    no_ref = sim_ids - sids_with_ref
    no_site = sim_ids - sids_with_site

    if no_comp:
        warnings.append(f"{len(no_comp)} simulants without mineral composition")
    if no_chem:
        warnings.append(f"{len(no_chem)} simulants without chemical composition")
    if no_ref:
        warnings.append(f"{len(no_ref)} simulants without references")
    if no_site:
        warnings.append(f"{len(no_site)} simulants without site/location")

    # 10. Availability normalization check
    avail_values = Counter(s.get("availability") for s in simulants)
    for val, count in avail_values.most_common():
        if val and val not in ("Available", "Unknown", "Production stopped", "Limited Stock"):
            warnings.append(f"Non-standard availability: '{val}' ({count} records)")

    # Report
    print(f"Files loaded:")
    print(f"  simulants: {len(simulants)}")
    print(f"  extras: {len(extras)}")
    print(f"  sites: {len(sites)}")
    print(f"  compositions: {len(compositions)}")
    print(f"  chemicals: {len(chemicals)}")
    print(f"  references: {len(references)}")
    print(f"  mineral_groups: {len(mineral_groups)}")
    print(f"  mineral_sourcing: {len(mineral_sourcing)}")
    print(f"  lunar_reference: {len(lunar_ref)}")
    print()

    print(f"Coverage:")
    print(f"  With mineral composition: {len(sids_with_comp)}/{len(sim_ids)}")
    print(f"  With chemical composition: {len(sids_with_chem)}/{len(sim_ids)}")
    print(f"  With references: {len(sids_with_ref)}/{len(sim_ids)}")
    print(f"  With site/location: {len(sids_with_site)}/{len(sim_ids)}")
    print(f"  With extra data: {len(sids_with_extra)}/{len(sim_ids)}")
    print()

    print(f"Availability distribution:")
    for val, count in avail_values.most_common():
        print(f"  {val or 'null'}: {count}")
    print()

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  [ERROR] {e}")
    else:
        print("No errors found.")
    print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  [WARN] {w}")
    else:
        print("No warnings.")

    print()
    print("PASS" if not errors else "FAIL")
    return len(errors) == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)

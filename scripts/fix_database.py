#!/usr/bin/env python3
"""
Database Fix Script - Addresses several issues:
1. Add unmatched simulants
2. Fix country codes
3. Consolidate institution names
4. Fix site coordinates
"""

import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("/home/alvaro/lrs-dashboard/data")

# New simulants to add
NEW_SIMULANTS = [
    {
        "name": "LMS-2",
        "type": "Mare",
        "country_code": "USA",
        "institution": "Space Resource Technologies",
        "availability": "Available",
        "notes": "Lunar Mare Simulant variant"
    },
    {
        "name": "LHS-2",
        "type": "Highland",
        "country_code": "USA",
        "institution": "Space Resource Technologies",
        "availability": "Available",
        "notes": "Lunar Highland Simulant variant"
    },
    {
        "name": "LHS-2E",
        "type": "Highland",
        "country_code": "USA",
        "institution": "Space Resource Technologies",
        "availability": "Available",
        "notes": "Lunar Highland Simulant - Enhanced"
    },
    {
        "name": "LSP-2",
        "type": "Polar",
        "country_code": "USA",
        "institution": "Space Resource Technologies",
        "availability": "Available",
        "notes": "Lunar South Pole Simulant"
    },
    {
        "name": "IGG-01",
        "type": "Mare",
        "country_code": "China",
        "institution": "Chinese Academy of Sciences",
        "availability": "Research",
        "notes": "Moderate-Ti lunar mare simulant"
    },
    {
        "name": "JSC-2A",
        "type": "Mare",
        "country_code": "USA",
        "institution": "NASA",
        "availability": "Limited",
        "notes": "JSC series variant"
    },
    {
        "name": "GRC-3",
        "type": "Geotechnical",
        "country_code": "USA",
        "institution": "NASA",
        "availability": "Research",
        "notes": "Glenn Research Center simulant"
    },
    {
        "name": "NAO-2",
        "type": "Highland",
        "country_code": "China",
        "institution": "Chinese Academy of Sciences",
        "availability": "Research",
        "notes": "National Astronomical Observatories simulant"
    },
    {
        "name": "CLRS-2",
        "type": "Mare",
        "country_code": "China",
        "institution": "Chinese Academy of Sciences",
        "availability": "Research",
        "notes": "Chinese Lunar Regolith Simulant variant"
    },
]

# Country code fixes
COUNTRY_FIXES = {
    # Format: simulant_name: new_country_code
    "AGK-2010": "Poland",
}

# Institution consolidation mapping
# Maps various institution names to standardized names
INSTITUTION_CONSOLIDATION = {
    # ESA-related
    "ESA / Technical University of Bari": "ESA",
    "ESA/Technical University Braunschweig": "ESA",
    "European Astronaut Centre (EAC": "ESA",

    # NASA-related
    "NASA and USGS": "NASA",
    "NASA-MSFC and USGS": "NASA",
    "NASA/USGS": "NASA",
    "NASA/Washington Mills": "NASA",
    "Goddard Space Center": "NASA",
    "MSFC": "NASA",

    # Chinese Academy consolidation
    "Institute of\nGeochemistry,\nChinese Academy of Sciences": "Chinese Academy of Sciences",
    "National\nAstronomical\nObservatories,\nChinese Academy of\nSciences ": "Chinese Academy of Sciences",

    # Other fixes
    "Australia": "Australian Space Agency",
    "Germany": "German Aerospace Center (DLR)",
    "China": "Chinese Academy of Sciences",
    "Republic of Korea": "KIGAM",
    "Turkey": "Turkish Space Agency",
    "Türkiye": "Turkish Space Agency",
}

# Site coordinate fixes (for Polish Academy of Sciences - Warsaw)
SITE_FIXES = {
    "S001": {  # AGK-2010
        "site_name": "Polish Academy of Sciences, Warsaw",
        "country_code": "Poland",
        "lat": 52.2297,
        "lon": 21.0122
    }
}

# New sites for new simulants (Space Resource Technologies is in Orlando, FL)
NEW_SITES = {
    "Space Resource Technologies": {
        "site_name": "Space Resource Technologies, Orlando",
        "lat": 28.5383,
        "lon": -81.3792,
        "country_code": "USA"
    },
    "Chinese Academy of Sciences": {
        "site_name": "Chinese Academy of Sciences, Beijing",
        "lat": 39.9042,
        "lon": 116.4074,
        "country_code": "China"
    }
}


def load_json(filename):
    filepath = DATA_DIR / filename
    with open(filepath) as f:
        return json.load(f)


def save_json(filename, data):
    filepath = DATA_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"  Saved {filename}: {len(data)} entries")


def backup_file(filename):
    filepath = DATA_DIR / filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = DATA_DIR / f"{filepath.stem}_backup_{timestamp}.json"
    data = load_json(filename)
    with open(backup_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"  Backup: {backup_path.name}")


def get_next_simulant_id(simulants):
    existing = [int(s['simulant_id'][1:]) for s in simulants if s['simulant_id'].startswith('S')]
    return f"S{max(existing) + 1:03d}"


def get_next_site_id(sites):
    existing = [int(s['site_id'][1:]) for s in sites if s['site_id'].startswith('X')]
    return f"X{max(existing) + 1:03d}"


def main():
    print("=" * 70)
    print("Database Fix Script")
    print("=" * 70)

    # Create backups
    print("\nCreating backups...")
    backup_file('simulant.json')
    backup_file('site.json')

    # Load data
    simulants = load_json('simulant.json')
    sites = load_json('site.json')

    existing_names = {s['name'].upper() for s in simulants}

    # 1. Add new simulants
    print("\n--- Adding New Simulants ---")
    added_simulants = []
    for new_sim in NEW_SIMULANTS:
        if new_sim['name'].upper() not in existing_names:
            sim_id = get_next_simulant_id(simulants)
            simulant_entry = {
                "simulant_id": sim_id,
                "name": new_sim['name'],
                "type": new_sim.get('type'),
                "country_code": new_sim.get('country_code'),
                "institution": new_sim.get('institution'),
                "availability": new_sim.get('availability'),
                "release_date": None,
                "tons_produced_mt": None,
                "notes": new_sim.get('notes')
            }
            simulants.append(simulant_entry)
            added_simulants.append((sim_id, new_sim['name']))
            print(f"  Added: {sim_id} - {new_sim['name']}")

            # Add site for new simulant
            institution = new_sim.get('institution', '')
            if institution in NEW_SITES:
                site_info = NEW_SITES[institution]
                site_entry = {
                    "site_id": get_next_site_id(sites),
                    "simulant_id": sim_id,
                    "site_name": site_info['site_name'],
                    "site_type": "Lab",
                    "country_code": site_info['country_code'],
                    "lat": site_info['lat'],
                    "lon": site_info['lon']
                }
                sites.append(site_entry)
        else:
            print(f"  Skipped (exists): {new_sim['name']}")

    # 2. Fix country codes
    print("\n--- Fixing Country Codes ---")
    for sim in simulants:
        if sim['name'] in COUNTRY_FIXES:
            old_code = sim['country_code']
            new_code = COUNTRY_FIXES[sim['name']]
            sim['country_code'] = new_code
            print(f"  {sim['name']}: {old_code} -> {new_code}")

    # 3. Consolidate institutions
    print("\n--- Consolidating Institutions ---")
    for sim in simulants:
        old_inst = sim.get('institution', '')
        if old_inst in INSTITUTION_CONSOLIDATION:
            new_inst = INSTITUTION_CONSOLIDATION[old_inst]
            sim['institution'] = new_inst
            print(f"  {sim['name']}: '{old_inst[:30]}...' -> '{new_inst}'")

    # 4. Fix site coordinates
    print("\n--- Fixing Site Coordinates ---")
    for site in sites:
        sim_id = site['simulant_id']
        if sim_id in SITE_FIXES:
            fixes = SITE_FIXES[sim_id]
            for key, value in fixes.items():
                old_value = site.get(key)
                site[key] = value
                print(f"  {sim_id}: {key} = {old_value} -> {value}")

    # Save updated data
    print("\n--- Saving Updated Data ---")
    save_json('simulant.json', simulants)
    save_json('site.json', sites)

    # Summary
    print("\n" + "=" * 70)
    print("Summary:")
    print(f"  New simulants added: {len(added_simulants)}")
    print(f"  Total simulants: {len(simulants)}")
    print(f"  Total sites: {len(sites)}")
    print("=" * 70)


if __name__ == "__main__":
    main()

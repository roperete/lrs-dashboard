"""
Add chemical composition entries for 6 simulants to chemical_composition.json.
Source: NASA User's Guide Rev A 2024, Table 7 (bulk chemistry, wt%)

Simulants added:
  CSM-LMT-1  S105
  GreenSpar   S025
  NU-LHT-4M  S089
  OPRH3N      S058
  OPRH4W30    S100
  OPRL2N      S060
"""

import json
import sys

DATA_FILE = "/home/alvaro/lrs-dashboard-v2/lunar-regolith-simulant-globe/public/data/chemical_composition.json"

# New data: list of (simulant_id, oxide_name, value)
# Values of 0.0 from the table are stored as 0.0 (numeric, not null — source explicitly states 0)
NEW_ENTRIES_RAW = [
    # CSM-LMT-1 (S105)
    ("S105", "SiO2",  46.9),
    ("S105", "TiO2",   5.1),
    ("S105", "Al2O3", 15.1),
    ("S105", "FeO",   14.0),
    ("S105", "MgO",    4.1),
    ("S105", "CaO",   12.2),
    ("S105", "Na2O",   2.7),
    ("S105", "K2O",    0.0),
    # GreenSpar (S025)
    ("S025", "SiO2",  51.0),
    ("S025", "TiO2",   0.0),
    ("S025", "Al2O3", 30.6),
    ("S025", "FeO",    0.4),
    ("S025", "MgO",    0.2),
    ("S025", "CaO",   14.7),
    ("S025", "Na2O",   2.5),
    ("S025", "K2O",    0.2),
    # NU-LHT-4M (S089)
    ("S089", "SiO2",  47.2),
    ("S089", "TiO2",   0.4),
    ("S089", "Al2O3", 23.5),
    ("S089", "FeO",    4.3),
    ("S089", "MgO",    8.7),
    ("S089", "CaO",   12.8),
    ("S089", "Na2O",   1.5),
    ("S089", "K2O",    0.2),
    # OPRH3N (S058)
    ("S058", "SiO2",  46.0),
    ("S058", "TiO2",   2.5),
    ("S058", "Al2O3", 25.4),
    ("S058", "FeO",    4.7),
    ("S058", "MgO",    2.2),
    ("S058", "CaO",   16.9),
    ("S058", "Na2O",   2.3),
    ("S058", "K2O",    0.0),
    # OPRH4W30 (S100)
    ("S100", "SiO2",  48.1),
    ("S100", "TiO2",   0.2),
    ("S100", "Al2O3", 30.3),
    ("S100", "FeO",    1.7),
    ("S100", "MgO",    1.1),
    ("S100", "CaO",   15.2),
    ("S100", "Na2O",   2.3),
    ("S100", "K2O",    0.1),
    # OPRL2N (S060)
    ("S060", "SiO2",  46.2),
    ("S060", "TiO2",   5.5),
    ("S060", "Al2O3", 16.6),
    ("S060", "FeO",   12.9),
    ("S060", "MgO",    2.7),
    ("S060", "CaO",   12.9),
    ("S060", "Na2O",   3.2),
    ("S060", "K2O",    0.0),
]

TARGET_IDS = {"S105", "S025", "S089", "S058", "S100", "S060"}


def main():
    # Load existing data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("FATAL: expected a JSON array at top level", file=sys.stderr)
        sys.exit(1)

    # Guard: none of the target IDs should already exist
    existing_ids = set(e["simulant_id"] for e in data)
    already_present = TARGET_IDS & existing_ids
    if already_present:
        print(
            f"FATAL: simulant_id(s) already present in file — aborting to avoid duplicates: {sorted(already_present)}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Determine next composition_id number
    max_ch = 0
    for entry in data:
        cid = entry.get("composition_id", "")
        if cid.startswith("CH") and cid[2:].isdigit():
            max_ch = max(max_ch, int(cid[2:]))

    print(f"Last existing composition_id: CH{max_ch:03d}")
    print(f"Total existing entries: {len(data)}")

    # Build new entries
    new_entries = []
    counter = max_ch + 1
    for sim_id, oxide, value in NEW_ENTRIES_RAW:
        # Validate value is a plain Python float/int — never a string
        assert isinstance(value, (int, float)), f"Non-numeric value for {sim_id}/{oxide}: {value!r}"
        new_entries.append({
            "composition_id": f"CH{counter:03d}",
            "simulant_id": sim_id,
            "component_type": "oxide",
            "component_name": oxide,
            "value_wt_pct": value,
        })
        counter += 1

    # Verify schema matches existing entries exactly (same keys, same order)
    if data:
        expected_keys = list(data[0].keys())
        for entry in new_entries:
            assert list(entry.keys()) == expected_keys, (
                f"Key mismatch for {entry['composition_id']}: "
                f"got {list(entry.keys())}, expected {expected_keys}"
            )

    # Append
    data.extend(new_entries)

    # Write — use write mode (never append mode) so the file is deterministic on re-run
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Added {len(new_entries)} entries (CH{max_ch+1:03d} – CH{counter-1:03d})")
    print(f"Total entries now: {len(data)}")

    # Spot-check: verify all 6 simulants are now present with correct entry counts
    from collections import Counter
    id_counts = Counter(e["simulant_id"] for e in data)
    for sim_id in sorted(TARGET_IDS):
        print(f"  {sim_id}: {id_counts[sim_id]} entries")


if __name__ == "__main__":
    main()

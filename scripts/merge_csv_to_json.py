#!/usr/bin/env python3
"""Merge LMNotebook_list.csv into the JSON database files.

CSV is treated as source of truth. Existing JSON-only entries are preserved.
Handles combined entry splitting, name normalization, and composition parsing.
"""

import csv
import json
import os
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "LMNotebook_list.csv"

# Output files
SIMULANT_JSON = DATA_DIR / "simulant.json"
EXTRA_JSON = DATA_DIR / "simulant_extra.json"
CHEMICAL_JSON = DATA_DIR / "chemical_composition.json"
MINERAL_JSON = DATA_DIR / "composition.json"

# Name mapping: JSON name -> CSV name (for matching)
NAME_MAP = {
    "Chenobi": "CHENOBI",
    "CLDS-1": "CLDS-i",
    "Kohyama": "Kohyama Simulant",
    "Oshima": "Oshima Simulant",
    "UOM-Black": "UoM-B",
    "UOM-White": "UoM-W",
}

# Combined entries: JSON name -> (new name for existing ID, already-existing separate IDs)
COMBINED_ENTRIES = {
    "BH-1/2": {"rename_to": "BH-1", "split_names": ["BH-2"]},
    "CLRS-1/2": {"rename_to": "CLRS-1", "split_names": ["CLRS-2"]},  # S084 exists
    "TJ-1/TJ-2": {"rename_to": "TJ-1", "split_names": ["TJ-2"]},
    "NEU-1/3": {"rename_to": "NEU-1", "split_names": ["NEU-1A", "NEU-1B"]},
    "GRC-1, -3": {"rename_to": "GRC-1", "split_names": ["GRC-3"]},  # S082 exists
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def parse_json_field(s):
    """Parse a JSON-like string field from CSV (e.g. chemical/mineral composition)."""
    s = s.strip()
    if not s:
        return {}
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        # Try fixing common issues: single quotes, trailing commas
        s = s.replace("'", '"')
        s = re.sub(r",\s*}", "}", s)
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            print(f"  WARNING: Could not parse JSON field: {s[:80]}")
            return {}


def parse_release_date(s):
    """Convert release date string to numeric or None."""
    s = s.strip()
    if not s:
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def parse_tons(s):
    """Parse tons produced field."""
    s = s.strip()
    if not s:
        return None
    # Handle "14+", "<15", etc.
    cleaned = re.sub(r"[^\d.]", "", s)
    if not cleaned:
        return s  # Keep as string if it has qualifiers
    try:
        val = float(cleaned)
        return int(val) if val == int(val) else val
    except (ValueError, TypeError):
        return s


def parse_grain_size(s):
    """Parse grain size, keep as string since it may have ranges."""
    s = s.strip()
    if not s:
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return s


def parse_specific_gravity(s):
    """Parse specific gravity to float."""
    s = s.strip()
    if not s:
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def clean_string(s):
    """Clean up a string field — strip whitespace, normalize newlines."""
    if not s:
        return None
    s = s.strip().replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s)
    return s if s else None


def main():
    print("Loading files...")
    csv_rows = load_csv(CSV_PATH)
    simulants = load_json(SIMULANT_JSON)
    extras = load_json(EXTRA_JSON)
    chemicals = load_json(CHEMICAL_JSON)
    minerals = load_json(MINERAL_JSON)

    print(f"  CSV: {len(csv_rows)} rows")
    print(f"  simulant.json: {len(simulants)} entries")
    print(f"  simulant_extra.json: {len(extras)} entries")
    print(f"  chemical_composition.json: {len(chemicals)} entries")
    print(f"  composition.json: {len(minerals)} entries")

    # Build lookup dicts
    sim_by_name = {}  # name -> simulant entry
    sim_by_id = {}    # id -> simulant entry
    extra_by_id = {}  # id -> extra entry

    for s in simulants:
        sim_by_name[s["name"]] = s
        sim_by_id[s["simulant_id"]] = s
    for e in extras:
        extra_by_id[e["simulant_id"]] = e

    # Step 1: Handle combined entries — rename the existing entry
    print("\nResolving combined entries...")
    for old_name, info in COMBINED_ENTRIES.items():
        if old_name in sim_by_name:
            entry = sim_by_name.pop(old_name)
            new_name = info["rename_to"]
            print(f"  {old_name} ({entry['simulant_id']}) -> {new_name}")
            entry["name"] = new_name
            sim_by_name[new_name] = entry
            # Also update extras
            sid = entry["simulant_id"]
            if sid in extra_by_id:
                extra_by_id[sid]["name"] = new_name

    # Step 2: Apply name normalizations
    print("\nApplying name normalizations...")
    for old_name, new_name in NAME_MAP.items():
        if old_name in sim_by_name:
            entry = sim_by_name.pop(old_name)
            print(f"  {old_name} ({entry['simulant_id']}) -> {new_name}")
            entry["name"] = new_name
            sim_by_name[new_name] = entry
            sid = entry["simulant_id"]
            if sid in extra_by_id:
                extra_by_id[sid]["name"] = new_name

    # Step 3: Build reverse lookup for CSV name -> existing simulant
    # Also include the generic parent entries that match variants
    csv_name_to_sim = {}
    for name, entry in sim_by_name.items():
        csv_name_to_sim[name] = entry

    # Find next available simulant ID
    max_id = max(int(s["simulant_id"][1:]) for s in simulants)
    next_id = max_id + 1
    print(f"\nNext available ID: S{next_id:03d}")

    # Track which existing simulant_ids have been matched
    matched_ids = set()

    # Step 4: Process each CSV row
    print(f"\nProcessing {len(csv_rows)} CSV rows...")
    new_simulants = []
    new_extras = []
    new_chemicals = []
    new_minerals = []

    # Track which simulant_ids already have composition data
    existing_chem_sids = {c["simulant_id"] for c in chemicals}
    existing_min_sids = {m["simulant_id"] for m in minerals}

    # Track max composition IDs
    max_ch_id = max((int(c["composition_id"][2:]) for c in chemicals), default=0)
    max_min_id = max((int(m["composition_id"][1:]) for m in minerals), default=0)
    ch_counter = max_ch_id + 1
    min_counter = max_min_id + 1

    for row in csv_rows:
        csv_name = row["Simulant name"].strip()
        if not csv_name:
            continue

        # Find existing entry
        existing = csv_name_to_sim.get(csv_name)
        if existing:
            sid = existing["simulant_id"]
            matched_ids.add(sid)
        else:
            # Create new entry
            sid = f"S{next_id:03d}"
            next_id += 1
            existing = {"simulant_id": sid, "name": csv_name}
            print(f"  NEW: {csv_name} -> {sid}")

        # Update core simulant fields from CSV (source of truth)
        existing["name"] = csv_name
        existing["type"] = clean_string(row.get("Type")) or existing.get("type")
        existing["country_code"] = clean_string(row.get("Country")) or existing.get("country_code")
        existing["institution"] = clean_string(row.get("Institution")) or existing.get("institution")
        existing["availability"] = clean_string(row.get("Stage")) or existing.get("availability")
        existing["release_date"] = parse_release_date(row.get("Release Date", "")) or existing.get("release_date")
        existing["tons_produced_mt"] = parse_tons(row.get("Tons produced", "")) or existing.get("tons_produced_mt")
        existing["specific_gravity"] = parse_specific_gravity(row.get("Specific Gravity", "")) or existing.get("specific_gravity")
        existing["notes"] = clean_string(row.get("Notes")) or existing.get("notes")
        existing["lunar_sample_reference"] = clean_string(row.get("Replica of")) or existing.get("lunar_sample_reference")

        new_simulants.append(existing)

        # Build extra entry
        ex = extra_by_id.get(sid, {"simulant_id": sid, "name": csv_name})
        ex["name"] = csv_name
        ex["classification"] = clean_string(row.get("Classification")) or ex.get("classification")
        ex["application"] = clean_string(row.get("Application Column 1")) or ex.get("application")
        ex["feedstock"] = clean_string(row.get("Feedstock")) or ex.get("feedstock")
        ex["petrographic_class"] = clean_string(row.get("Petrographic Class (Composition:Percentage)")) or ex.get("petrographic_class")
        ex["grain_size_mm"] = parse_grain_size(row.get("Grain Size (mm)", "")) or ex.get("grain_size_mm")
        ex["publicly_available_composition"] = bool(clean_string(row.get("Publicly available composition")))
        ex["reference"] = clean_string(row.get("Reference")) or ex.get("reference")

        # Preserve specific_gravity in extra if it was there
        sg = parse_specific_gravity(row.get("Specific Gravity", ""))
        if sg:
            ex["specific_gravity"] = sg
        elif "specific_gravity" not in ex:
            ex["specific_gravity"] = None

        new_extras.append(ex)

        # Parse chemical composition — only add if simulant has NO existing data
        chem_str = row.get("Chemical Composition", "").strip()
        if chem_str and sid not in existing_chem_sids:
            chem_data = parse_json_field(chem_str)
            if chem_data:
                for component, value in chem_data.items():
                    new_chemicals.append({
                        "composition_id": f"CH{ch_counter:03d}",
                        "simulant_id": sid,
                        "component_type": "oxide",
                        "component_name": component,
                        "value_wt_pct": value
                    })
                    ch_counter += 1

        # Parse mineral composition — only add if simulant has NO existing data
        min_str = row.get("Mineral Composition (Composition; Percentage)", "").strip()
        if min_str and sid not in existing_min_sids:
            min_data = parse_json_field(min_str)
            if min_data:
                for component, value in min_data.items():
                    new_minerals.append({
                        "composition_id": f"C{min_counter:03d}",
                        "simulant_id": sid,
                        "component_type": "mineral",
                        "component_name": component,
                        "value_pct": value
                    })
                    min_counter += 1

    # Step 5: Preserve JSON-only entries (not in CSV)
    matched_names = {s["name"] for s in new_simulants}
    for s in simulants:
        if s["name"] not in matched_names and s["simulant_id"] not in matched_ids:
            print(f"  PRESERVED (JSON-only): {s['name']} ({s['simulant_id']})")
            new_simulants.append(s)
            # Also preserve their extras
            sid = s["simulant_id"]
            if sid in extra_by_id and not any(e["simulant_id"] == sid for e in new_extras):
                new_extras.append(extra_by_id[sid])

    # Step 6: Keep ALL existing composition data, new_chemicals/new_minerals
    # only contain entries for simulants that had NO existing data
    all_chemicals = list(chemicals) + new_chemicals
    all_minerals = list(minerals) + new_minerals
    new_chemicals = all_chemicals
    new_minerals = all_minerals

    # Step 7: Sort everything by simulant_id
    new_simulants.sort(key=lambda x: int(x["simulant_id"][1:]))
    new_extras.sort(key=lambda x: int(x["simulant_id"][1:]))
    new_chemicals.sort(key=lambda x: x["simulant_id"])
    new_minerals.sort(key=lambda x: x["simulant_id"])

    # Re-number chemical and mineral composition IDs sequentially
    for i, c in enumerate(new_chemicals, 1):
        c["composition_id"] = f"CH{i:03d}"
    for i, m in enumerate(new_minerals, 1):
        m["composition_id"] = f"C{i:03d}"

    # Step 8: Ensure every simulant has an extra entry
    extra_sids = {e["simulant_id"] for e in new_extras}
    for s in new_simulants:
        if s["simulant_id"] not in extra_sids:
            new_extras.append({
                "simulant_id": s["simulant_id"],
                "name": s["name"],
            })

    # Ensure all extras have consistent schema
    extra_keys = ["simulant_id", "name", "classification", "application",
                  "replica_of", "feedstock", "petrographic_class",
                  "grain_size_mm", "specific_gravity",
                  "publicly_available_composition", "reference"]
    for ex in new_extras:
        # Populate replica_of from simulant's lunar_sample_reference if not set
        sid = ex["simulant_id"]
        sim = next((s for s in new_simulants if s["simulant_id"] == sid), None)
        if sim and not ex.get("replica_of"):
            ex["replica_of"] = sim.get("lunar_sample_reference")
        for key in extra_keys:
            if key not in ex:
                ex[key] = None

    # Step 9: Write output
    print(f"\nWriting output...")
    print(f"  simulant.json: {len(new_simulants)} entries")
    print(f"  simulant_extra.json: {len(new_extras)} entries")
    print(f"  chemical_composition.json: {len(new_chemicals)} entries")
    print(f"  composition.json: {len(new_minerals)} entries")

    save_json(SIMULANT_JSON, new_simulants)
    save_json(EXTRA_JSON, new_extras)
    save_json(CHEMICAL_JSON, new_chemicals)
    save_json(MINERAL_JSON, new_minerals)

    print("\nDone!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Merge spreadsheet CSV data into existing JSON data files.

Reads the LRS types CSV (with embedded JSON mineral compositions),
matches rows to existing simulant.json entries by name,
and gap-fills missing fields.

Usage:
    python scripts/merge_spreadsheet.py
"""

import csv
import json
import re
import shutil
from pathlib import Path
from difflib import SequenceMatcher

DATA_DIR = Path(__file__).resolve().parent.parent / "public" / "data"
CSV_DIR = Path(__file__).resolve().parent.parent.parent / "Minerals"
LRS_CSV = CSV_DIR / "Database - LRS Constituents - LRS types (2).csv"
MINERAL_CSV = CSV_DIR / "Database - LRS Constituents - Mineral Constituents (1).csv"
MINERAL_PRELIM_CSV = CSV_DIR / "Database - LRS Constituents - Mineral Constituents, Preliminary (Nabila) (1).csv"


# --- Name normalization for matching ---

NAME_MAP = {
    "BH-1/2": ["BH-1", "BH-2"],
    "CLRS-1/2": ["CLRS-1", "CLRS-2"],
    "GRC-1, -3": ["GRC-1", "GRC-3"],
    "Kohyama": ["Kohyama Simulant"],
    "NEU-1/3": ["NEU-1", "NEU-1A", "NEU-1B"],
    "Oshima": ["Oshima Simulant"],
    "TJ-1/TJ-2": ["TJ-1", "TJ-2"],
    "UOM-Black": ["UoM-B"],
    "UOM-White": ["UoM-W"],
    "Chenobi": ["CHENOBI"],
    "CLDS-1": ["CLDS-i"],
}


def parse_lrs_csv(path: Path) -> list[dict]:
    """Parse the LRS types CSV, handling embedded JSON in cells."""
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    # The CSV has multiline JSON embedded in cells. Python's csv module
    # handles quoted multiline fields correctly.
    reader = csv.DictReader(raw.splitlines().__iter__())
    # But we need to re-parse because splitlines breaks multiline quoted fields.
    # Use the file directly instead.

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    parsed = []
    for row in rows:
        name = (row.get("Simulant name") or "").strip()
        if not name:
            continue

        entry = {
            "name": name,
            "type": (row.get("Type") or "").strip() or None,
            "country": (row.get("Country") or "").strip() or None,
            "classification": (row.get("Classification (https://ntrs.nasa.gov/citations/20240011783)") or "").strip() or None,
            "application": (row.get("Application") or "").strip() or None,
            "city": (row.get("Column 1") or "").strip() or None,
            "institution": (row.get("Institution") or "").strip() or None,
            "stage": (row.get("Stage") or "").strip() or None,
            "release_date": (row.get("Release Date") or "").strip() or None,
            "replica_of": (row.get("Replica of") or "").strip() or None,
            "notes": (row.get("Notes") or "").strip() or None,
            "reference": (row.get("Reference") or "").strip() or None,
            "publicly_available": (row.get("Publicly available composition") or "").strip(),
            "feedstock": (row.get("Feedstock") or "").strip() or None,
            "petrographic_class": (row.get("Petrographic Class (Composition:Percentage)") or "").strip() or None,
            "mineral_composition_raw": (row.get("Mineral Composition (Composition;Percentage)") or "").strip() or None,
            "chemical_composition_raw": (row.get("Chemical Composition") or "").strip() or None,
            "tons_produced": (row.get("Tons produced") or "").strip() or None,
            "grain_size_mm": (row.get("Grain Size (mm)") or "").strip() or None,
            "specific_gravity": (row.get("Specific Gravity") or "").strip() or None,
        }
        parsed.append(entry)

    return parsed


def parse_mineral_composition(raw: str | None) -> dict | None:
    """Parse embedded JSON mineral composition from CSV cell."""
    if not raw:
        return None
    # Skip plain text values like "Basalt"
    stripped = raw.strip()
    if not stripped.startswith("{"):
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        # Try closing truncated JSON by adding closing braces
        fixed = stripped.rstrip().rstrip(",")
        open_braces = fixed.count("{") - fixed.count("}")
        fixed += "}" * open_braces
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            print(f"  WARNING: Could not parse mineral composition JSON (len={len(raw)})")
            return None


def parse_chemical_composition(raw: str | None) -> list[dict] | None:
    """Parse chemical composition string into list of {oxide, value_wt_pct}."""
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return [{"oxide": k, "value_wt_pct": v} for k, v in data.items() if v is not None]
    except json.JSONDecodeError:
        pass

    # Try semicolon-separated format: "SiO2;45.5;Al2O3;12.3"
    parts = re.split(r'[;,]', raw)
    results = []
    i = 0
    while i < len(parts) - 1:
        oxide = parts[i].strip()
        try:
            val = float(parts[i + 1].strip())
            results.append({"oxide": oxide, "value_wt_pct": val})
            i += 2
        except (ValueError, IndexError):
            i += 1
    return results if results else None


def find_matching_simulant(name: str, simulants: list[dict]) -> list[dict]:
    """Find matching simulant(s) by name, using NAME_MAP for known variants."""
    # Direct match
    matches = [s for s in simulants if s["name"] == name]
    if matches:
        return matches

    # Check NAME_MAP
    if name in NAME_MAP:
        targets = NAME_MAP[name]
        return [s for s in simulants if s["name"] in targets]

    # Case-insensitive match
    matches = [s for s in simulants if s["name"].lower() == name.lower()]
    if matches:
        return matches

    # Fuzzy match (>0.8 similarity)
    best_score = 0
    best_match = None
    for s in simulants:
        score = SequenceMatcher(None, name.lower(), s["name"].lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = s
    if best_score > 0.8 and best_match:
        return [best_match]

    return []


def gap_fill(target: dict, source: dict, fields: list[str]):
    """Fill missing/null fields in target from source. Returns count of fields filled."""
    filled = 0
    for field in fields:
        src_val = source.get(field)
        if src_val is None:
            continue
        tgt_val = target.get(field)
        if tgt_val is None or tgt_val == "" or tgt_val == "null":
            target[field] = src_val
            filled += 1
    return filled


def backup_file(path: Path):
    """Create a .bak backup of a file."""
    bak = path.with_suffix(path.suffix + ".bak")
    if path.exists():
        shutil.copy2(path, bak)
        print(f"  Backed up {path.name} -> {bak.name}")


def merge_simulant_data(csv_rows: list[dict], simulants: list[dict], extras: list[dict]):
    """Merge CSV data into simulant.json and simulant_extra.json entries."""
    sim_by_id = {s["simulant_id"]: s for s in simulants}
    extra_by_id = {e["simulant_id"]: e for e in extras}

    stats = {"matched": 0, "unmatched": 0, "fields_filled": 0, "compositions_added": 0}

    for csv_row in csv_rows:
        name = csv_row["name"]
        matches = find_matching_simulant(name, simulants)

        if not matches:
            print(f"  SKIP: No match for '{name}'")
            stats["unmatched"] += 1
            continue

        stats["matched"] += 1

        for sim in matches:
            sid = sim["simulant_id"]
            extra = extra_by_id.get(sid, {})

            # Gap-fill simulant.json fields
            sim_source = {}
            if csv_row["type"]:
                sim_source["type"] = csv_row["type"]
            if csv_row["institution"]:
                sim_source["institution"] = csv_row["institution"]
            if csv_row["stage"]:
                # Map stage to availability
                stage_map = {
                    "Available": "Available",
                    "Limited stock": "Limited Stock",
                    "Production stopped": "Production stopped",
                }
                sim_source["availability"] = stage_map.get(csv_row["stage"], csv_row["stage"])
            if csv_row["release_date"]:
                try:
                    sim_source["release_date"] = int(csv_row["release_date"])
                except ValueError:
                    pass
            if csv_row["notes"]:
                sim_source["notes"] = csv_row["notes"]
            if csv_row["specific_gravity"]:
                try:
                    sim_source["specific_gravity"] = float(csv_row["specific_gravity"])
                except ValueError:
                    pass
            if csv_row["tons_produced"]:
                try:
                    sim_source["tons_produced_mt"] = float(csv_row["tons_produced"])
                except ValueError:
                    pass

            filled = gap_fill(sim, sim_source, list(sim_source.keys()))
            stats["fields_filled"] += filled

            # Gap-fill simulant_extra.json fields
            extra_source = {}
            if csv_row["classification"]:
                extra_source["classification"] = csv_row["classification"]
            if csv_row["application"]:
                extra_source["application"] = csv_row["application"]
            if csv_row["feedstock"]:
                extra_source["feedstock"] = csv_row["feedstock"]
            if csv_row["replica_of"]:
                extra_source["replica_of"] = csv_row["replica_of"]
            if csv_row["grain_size_mm"]:
                extra_source["grain_size_mm"] = csv_row["grain_size_mm"]
            if csv_row["petrographic_class"]:
                extra_source["petrographic_class"] = csv_row["petrographic_class"]
            if csv_row["reference"]:
                extra_source["reference"] = csv_row["reference"]
            if csv_row["publicly_available"]:
                extra_source["publicly_available_composition"] = csv_row["publicly_available"].upper() == "TRUE"

            if extra:
                filled = gap_fill(extra, extra_source, list(extra_source.keys()))
                stats["fields_filled"] += filled

    return stats


def merge_mineral_compositions(csv_rows: list[dict], simulants: list[dict],
                                compositions: list[dict]) -> int:
    """Merge mineral composition JSON from CSV into composition.json."""
    existing_sims = {c["simulant_id"] for c in compositions}
    added = 0

    for csv_row in csv_rows:
        mineral_data = parse_mineral_composition(csv_row.get("mineral_composition_raw"))
        if not mineral_data:
            continue

        matches = find_matching_simulant(csv_row["name"], simulants)
        if not matches:
            continue

        for sim in matches:
            sid = sim["simulant_id"]
            # Only add if no composition exists for this simulant
            if sid in existing_sims:
                continue

            # Flatten the grouped structure into individual composition entries
            for group, minerals in mineral_data.items():
                if isinstance(minerals, dict):
                    for mineral_name, percentage in minerals.items():
                        if percentage and percentage > 0:
                            compositions.append({
                                "simulant_id": sid,
                                "mineral_name": mineral_name,
                                "percentage": percentage,
                                "group": group,
                            })
                            added += 1
            existing_sims.add(sid)

    return added


def merge_chemical_compositions(csv_rows: list[dict], simulants: list[dict],
                                 chemicals: list[dict]) -> int:
    """Merge chemical composition data from CSV into chemical_composition.json."""
    existing_sims = {c["simulant_id"] for c in chemicals}
    added = 0

    for csv_row in csv_rows:
        chem_data = parse_chemical_composition(csv_row.get("chemical_composition_raw"))
        if not chem_data:
            continue

        matches = find_matching_simulant(csv_row["name"], simulants)
        if not matches:
            continue

        for sim in matches:
            sid = sim["simulant_id"]
            if sid in existing_sims:
                continue

            for entry in chem_data:
                chemicals.append({
                    "simulant_id": sid,
                    "oxide": entry["oxide"],
                    "value_wt_pct": entry["value_wt_pct"],
                })
                added += 1
            existing_sims.add(sid)

    return added


def merge_mineral_sourcing(mineral_csv: Path, prelim_csv: Path, existing: list[dict]) -> list[dict]:
    """Merge mineral sourcing data from both CSV tabs, enriching existing records."""
    existing_by_name = {m["mineral_name"].lower(): m for m in existing}

    # Parse the refined mineral constituents CSV
    with open(mineral_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Chemical compound present in LRS") or "").strip()
            if not name:
                continue

            key = name.lower()
            if key in existing_by_name:
                entry = existing_by_name[key]
            else:
                entry = {"mineral_name": name}
                existing_by_name[key] = entry

            # Gap-fill from CSV
            source_mineral = (row.get("Source mineral") or "").strip()
            if source_mineral and not entry.get("source_mineral"):
                entry["source_mineral"] = source_mineral
                entry["chemistry"] = source_mineral  # backwards compat

            mining_locs = (row.get("Mine currently operative") or "").strip()
            if mining_locs and not entry.get("mining_locations"):
                entry["mining_locations"] = mining_locs

            company = (row.get("Mining Company") or "").strip()
            if company and not entry.get("mining_company"):
                entry["mining_company"] = company

    # Parse the preliminary (Nabila) CSV for supplier info
    with open(prelim_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        current_constituent = None
        for row in reader:
            constituent = (row.get("Constituent") or "").strip()
            if constituent:
                current_constituent = constituent

            if not current_constituent:
                continue

            key = current_constituent.lower()
            if key not in existing_by_name:
                continue

            entry = existing_by_name[key]

            source = (row.get("Source (Exolith)") or "").strip()
            if source and not entry.get("supplier"):
                entry["supplier"] = source

            chemistry = (row.get("Chemistry") or "").strip()
            if chemistry and not entry.get("chemistry"):
                entry["chemistry"] = chemistry

            desc = (row.get("Description") or "").strip()
            if desc and not entry.get("description"):
                entry["description"] = desc

            desc_simple = (row.get("Description in simple language") or "").strip()
            if desc_simple and not entry.get("description_simple"):
                entry["description_simple"] = desc_simple

            reading = (row.get("Further reading") or "").strip()
            if reading and not entry.get("further_reading"):
                entry["further_reading"] = reading

            europe = (row.get("Where to find in Europe") or "").strip()
            if europe and not entry.get("european_sources"):
                entry["european_sources"] = europe

    return list(existing_by_name.values())


def main():
    print("=== LRS Spreadsheet Merge ===\n")

    # Load existing data
    print("Loading existing data...")
    with open(DATA_DIR / "simulant.json") as f:
        simulants = json.load(f)
    with open(DATA_DIR / "simulant_extra.json") as f:
        extras = json.load(f)
    with open(DATA_DIR / "composition.json") as f:
        compositions = json.load(f)
    with open(DATA_DIR / "chemical_composition.json") as f:
        chemicals = json.load(f)
    with open(DATA_DIR / "mineral_sourcing.json") as f:
        mineral_sourcing = json.load(f)

    print(f"  {len(simulants)} simulants, {len(extras)} extras")
    print(f"  {len(compositions)} compositions, {len(chemicals)} chemicals")
    print(f"  {len(mineral_sourcing)} mineral sourcing records\n")

    # Parse CSV
    print("Parsing spreadsheet CSV...")
    csv_rows = parse_lrs_csv(LRS_CSV)
    print(f"  {len(csv_rows)} rows parsed\n")

    # Backup files
    print("Creating backups...")
    for fname in ["simulant.json", "simulant_extra.json", "composition.json",
                   "chemical_composition.json", "mineral_sourcing.json"]:
        backup_file(DATA_DIR / fname)
    print()

    # Merge simulant + extra data
    print("Merging simulant data...")
    stats = merge_simulant_data(csv_rows, simulants, extras)
    print(f"  Matched: {stats['matched']}/{len(csv_rows)}")
    print(f"  Unmatched: {stats['unmatched']}")
    print(f"  Fields gap-filled: {stats['fields_filled']}\n")

    # Merge mineral compositions
    print("Merging mineral compositions...")
    comp_added = merge_mineral_compositions(csv_rows, simulants, compositions)
    print(f"  Composition entries added: {comp_added}\n")

    # Merge chemical compositions
    print("Merging chemical compositions...")
    chem_added = merge_chemical_compositions(csv_rows, simulants, chemicals)
    print(f"  Chemical entries added: {chem_added}\n")

    # Merge mineral sourcing
    print("Merging mineral sourcing...")
    mineral_sourcing = merge_mineral_sourcing(MINERAL_CSV, MINERAL_PRELIM_CSV, mineral_sourcing)
    print(f"  Total mineral sourcing records: {len(mineral_sourcing)}\n")

    # Write updated files
    print("Writing updated data files...")
    with open(DATA_DIR / "simulant.json", "w") as f:
        json.dump(simulants, f, indent=2, ensure_ascii=False)
    with open(DATA_DIR / "simulant_extra.json", "w") as f:
        json.dump(extras, f, indent=2, ensure_ascii=False)
    with open(DATA_DIR / "composition.json", "w") as f:
        json.dump(compositions, f, indent=2, ensure_ascii=False)
    with open(DATA_DIR / "chemical_composition.json", "w") as f:
        json.dump(chemicals, f, indent=2, ensure_ascii=False)
    with open(DATA_DIR / "mineral_sourcing.json", "w") as f:
        json.dump(mineral_sourcing, f, indent=2, ensure_ascii=False)

    print("  Done!\n")
    print("=== Summary ===")
    print(f"  Simulants matched: {stats['matched']}/{len(csv_rows)}")
    print(f"  Fields gap-filled: {stats['fields_filled']}")
    print(f"  Mineral compositions added: {comp_added}")
    print(f"  Chemical compositions added: {chem_added}")
    print(f"  Mineral sourcing records: {len(mineral_sourcing)}")


if __name__ == "__main__":
    main()

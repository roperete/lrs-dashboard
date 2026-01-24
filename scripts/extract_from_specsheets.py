#!/usr/bin/env python3
"""
Extract composition data from spec sheets with validation.

Rules:
1. Manual data prevails - never overwrite existing entries
2. Only use spec sheets (most reliable source)
3. Validate totals sum to ~100% before adding
4. Extract both mineralogy and bulk chemistry
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

DATA_DIR = Path(__file__).parent.parent / 'data'
DOCS_DIR = Path("/home/alvaro/Spring - Forest on the moon/DIRT/DIRT Papers")

@dataclass
class ExtractedData:
    simulant_name: str
    minerals: Dict[str, float] = field(default_factory=dict)
    chemicals: Dict[str, float] = field(default_factory=dict)
    source_file: str = ""


# Map spec sheet files to simulant names in database
SPECSHEET_MAP = {
    "LMS-2-SPEC-SHEET-DEC2025.pptx.txt": "LMS-2",
    "LHS-2-SPEC-SHEET-DEC2025.pptx.txt": "LHS-2",
    "LHS-2E-SPEC-SHEET-DEC2025.pptx.txt": "LHS-2E",
    "LSP-2-SPEC-SHEET-DEC2025.pptx.txt": "LSP-2",
    "LMS-1-SPEC-SHEET-DEC2025.pptx.txt": "LMS-1",
    "LHS-1-SPEC-SHEET-DEC2025.pptx.txt": "LHS-1",
    "TLH-0_TDS.txt": "TLH-0",
    "TLM-0_TDS.txt": "TLM-0",
    # Add more as needed
}


def parse_specsheet(filepath: Path) -> Optional[ExtractedData]:
    """Parse a spec sheet text file and extract composition data."""

    with open(filepath) as f:
        content = f.read()

    lines = [l.strip() for l in content.split('\n')]

    # Determine simulant name from filename or content
    filename = filepath.name
    simulant_name = SPECSHEET_MAP.get(filename)

    if not simulant_name:
        # Try to extract from content
        for line in lines[:10]:
            if 'Simulant Name:' in line:
                simulant_name = line.split(':')[1].strip()
                break

    if not simulant_name:
        print(f"  Warning: Could not determine simulant name for {filename}")
        return None

    data = ExtractedData(simulant_name=simulant_name, source_file=filename)

    # Known minerals (from space resource spec sheets)
    KNOWN_MINERALS = {
        'Bronzite', 'Anorthosite', 'Olivine', 'Ilmenite', 'Basalt', 'Glass-rich Basalt',
        'Anorthite', 'Plagioclase', 'Pyroxene', 'Augite', 'Forsterite', 'Fayalite',
        'Glass', 'Volcanic Glass', 'Agglutinate', 'Norite', 'Feldspar', 'K-feldspar',
        'Labradorite', 'Bytownite', 'Clinopyroxene', 'Orthopyroxene', 'Magnetite',
        'Hematite', 'Apatite', 'Quartz', 'Smectite', 'Illite'
    }

    # Known oxides
    KNOWN_OXIDES = {
        'SiO2', 'TiO2', 'Al2O3', 'FeO', 'Fe2O3', 'MnO', 'MgO', 'CaO',
        'Na2O', 'K2O', 'P2O5', 'Cr2O3', 'NiO', 'SO3', 'LOI'
    }

    # Find the mineralogy/chemistry section (after "Mineralogy" header)
    start_idx = 0
    for i, line in enumerate(lines):
        if line == 'Mineralogy':
            start_idx = i
            break

    # Find end of section (at "Safety" or end of file)
    end_idx = len(lines)
    for i, line in enumerate(lines[start_idx:], start_idx):
        if line == 'Safety' or line.startswith('*Glass-rich basalt sourced'):
            end_idx = i
            break

    # Process the data section line by line
    i = start_idx
    pending_mineral = None
    pending_oxide = None

    while i < end_idx:
        line = lines[i]

        # Skip empty lines and headers
        if not line or line in ['Mineralogy', 'Bulk Chemistry', 'Component', 'Wt.%', 'Oxide', 'As mixed.', 'Relative abundances.', 'Measured by XRF.', 'Total']:
            i += 1
            continue

        # Handle multi-line mineral names (e.g., "*Glass-rich" + "Basalt")
        if line.startswith('*'):
            # Could be start of multi-line mineral name
            potential_name = line.replace('*', '').strip()
            if i + 1 < end_idx:
                next_line = lines[i + 1]
                # Check if next line completes the name
                if next_line and not any(c.isdigit() for c in next_line) and next_line not in KNOWN_OXIDES:
                    potential_name = f"{potential_name} {next_line}".strip()
                    pending_mineral = potential_name
                    i += 2
                    continue

        # Check if it's a known mineral name
        mineral_match = None
        for m in KNOWN_MINERALS:
            if m.lower() == line.lower() or line.lower().replace('*', '').strip() == m.lower():
                mineral_match = m
                break

        if mineral_match:
            pending_mineral = mineral_match
            i += 1
            continue

        # Check if it's a known oxide
        oxide_match = None
        # Handle "P 2O 5" -> "P2O5"
        normalized_line = line.replace(' ', '')
        for o in KNOWN_OXIDES:
            if o == normalized_line or o.lower() == normalized_line.lower():
                oxide_match = o
                break

        if oxide_match:
            pending_oxide = oxide_match
            i += 1
            continue

        # Check if it's a numeric value
        try:
            value = float(line)
            if 0 < value <= 100:
                if pending_mineral:
                    data.minerals[pending_mineral] = value
                    pending_mineral = None
                elif pending_oxide:
                    data.chemicals[pending_oxide] = value
                    pending_oxide = None
        except ValueError:
            pass

        i += 1

    return data


def validate_composition(data: ExtractedData) -> Tuple[bool, str]:
    """Validate that composition totals make sense."""

    mineral_total = sum(data.minerals.values())
    chemical_total = sum(data.chemicals.values())

    issues = []

    # Minerals should sum to ~100%
    if data.minerals:
        if mineral_total < 90:
            issues.append(f"Mineral total too low: {mineral_total:.1f}%")
        elif mineral_total > 105:
            issues.append(f"Mineral total too high: {mineral_total:.1f}%")

    # Chemicals should sum to ~100%
    if data.chemicals:
        if chemical_total < 90:
            issues.append(f"Chemical total too low: {chemical_total:.1f}%")
        elif chemical_total > 105:
            issues.append(f"Chemical total too high: {chemical_total:.1f}%")

    if issues:
        return False, "; ".join(issues)

    return True, f"Minerals: {mineral_total:.1f}%, Chemicals: {chemical_total:.1f}%"


def get_simulant_id(simulant_name: str, simulants: List[dict]) -> Optional[str]:
    """Find simulant ID by name."""
    for s in simulants:
        if s['name'] == simulant_name:
            return s['simulant_id']
    return None


def get_existing_minerals(simulant_id: str, compositions: List[dict]) -> set:
    """Get set of existing mineral names for a simulant."""
    return {
        c['component_name']
        for c in compositions
        if c['simulant_id'] == simulant_id and c.get('component_type') == 'mineral'
    }


def get_existing_chemicals(simulant_id: str, chemicals: List[dict]) -> set:
    """Get set of existing chemical names for a simulant."""
    return {c['component_name'] for c in chemicals if c['simulant_id'] == simulant_id}


def main():
    # Load existing data
    with open(DATA_DIR / 'simulant.json') as f:
        simulants = json.load(f)

    with open(DATA_DIR / 'composition.json') as f:
        compositions = json.load(f)

    with open(DATA_DIR / 'chemical_composition.json') as f:
        chemicals = json.load(f)

    # Get next IDs
    max_comp_id = max(int(c['composition_id'][1:]) for c in compositions) if compositions else 0
    max_chem_id = max(int(c['composition_id'][2:]) for c in chemicals) if chemicals else 0

    # Track changes
    new_minerals = []
    new_chemicals = []
    skipped = []

    print("=" * 60)
    print("Extracting composition data from spec sheets")
    print("=" * 60)

    # Process each spec sheet
    for filename, expected_name in SPECSHEET_MAP.items():
        filepath = DOCS_DIR / filename

        if not filepath.exists():
            print(f"\n✗ File not found: {filename}")
            continue

        print(f"\n→ Processing: {filename}")

        # Parse the spec sheet
        data = parse_specsheet(filepath)

        if not data:
            print(f"  ✗ Could not parse file")
            continue

        # Validate
        valid, msg = validate_composition(data)
        print(f"  Validation: {msg}")

        if not valid:
            print(f"  ✗ SKIPPED - {msg}")
            skipped.append((filename, msg))
            continue

        # Find simulant ID
        simulant_id = get_simulant_id(data.simulant_name, simulants)

        if not simulant_id:
            print(f"  ✗ Simulant '{data.simulant_name}' not found in database")
            continue

        print(f"  ✓ Matched to {data.simulant_name} ({simulant_id})")

        # Check for existing data (manual entries)
        existing_minerals = get_existing_minerals(simulant_id, compositions)
        existing_chemicals = get_existing_chemicals(simulant_id, chemicals)

        if existing_minerals:
            print(f"  ⚠ Has {len(existing_minerals)} existing minerals - preserving manual data")

        if existing_chemicals:
            print(f"  ⚠ Has {len(existing_chemicals)} existing chemicals - preserving manual data")

        # Add new minerals (only if no existing data)
        if not existing_minerals and data.minerals:
            print(f"  + Adding {len(data.minerals)} minerals:")
            for mineral, value in data.minerals.items():
                max_comp_id += 1
                new_entry = {
                    "composition_id": f"C{max_comp_id:03d}",
                    "simulant_id": simulant_id,
                    "component_type": "mineral",
                    "component_name": mineral,
                    "value_pct": value
                }
                new_minerals.append(new_entry)
                print(f"      {mineral}: {value}%")

        # Add new chemicals (only if no existing data)
        if not existing_chemicals and data.chemicals:
            print(f"  + Adding {len(data.chemicals)} chemicals:")
            for chemical, value in data.chemicals.items():
                max_chem_id += 1
                new_entry = {
                    "composition_id": f"CH{max_chem_id:03d}",
                    "simulant_id": simulant_id,
                    "component_type": "oxide",
                    "component_name": chemical,
                    "value_wt_pct": value
                }
                new_chemicals.append(new_entry)
                print(f"      {chemical}: {value}%")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  New mineral entries: {len(new_minerals)}")
    print(f"  New chemical entries: {len(new_chemicals)}")
    print(f"  Skipped (validation failed): {len(skipped)}")

    if skipped:
        print("\n  Skipped files:")
        for filename, reason in skipped:
            print(f"    - {filename}: {reason}")

    # Save if there are new entries
    if new_minerals or new_chemicals:
        response = input("\nSave changes? [y/N]: ")
        if response.lower() == 'y':
            if new_minerals:
                compositions.extend(new_minerals)
                with open(DATA_DIR / 'composition.json', 'w') as f:
                    json.dump(compositions, f, indent=2)
                print(f"  ✓ Saved {len(new_minerals)} minerals to composition.json")

            if new_chemicals:
                chemicals.extend(new_chemicals)
                with open(DATA_DIR / 'chemical_composition.json', 'w') as f:
                    json.dump(chemicals, f, indent=2)
                print(f"  ✓ Saved {len(new_chemicals)} chemicals to chemical_composition.json")
        else:
            print("  Changes not saved.")
    else:
        print("\n  No new data to add.")


if __name__ == '__main__':
    main()

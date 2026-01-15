#!/usr/bin/env python3
"""
Composition Database Update Script for LRS Dashboard

Extracts data from TDS/spec sheet PDFs and updates the main database files:
- composition.json (detailed minerals)
- mineral_groups.json (NASA mineral groups)
- chemical_composition.json (oxide composition)
- simulant.json (FoM scores, types)
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add extractors to path
sys.path.insert(0, str(Path(__file__).parent))
from extractors.specsheet_extractor import SpecSheetExtractor, SimulantData


class CompositionDatabaseUpdater:
    """Updates LRS Dashboard database from extracted PDF data"""

    def __init__(self, data_dir: Path, pdf_dir: Path):
        self.data_dir = Path(data_dir)
        self.pdf_dir = Path(pdf_dir)
        self.extractor = SpecSheetExtractor()

        # Load existing data
        self.simulants = self._load_json('simulant.json')
        self.composition = self._load_json('composition.json')
        self.chemicals = self._load_json('chemical_composition.json')
        self.mineral_groups = self._load_json('mineral_groups.json')

        # Build name-to-id mapping
        self.name_to_id = {s['name'].upper(): s['simulant_id'] for s in self.simulants}

        # Track changes
        self.changes = {
            'minerals_added': 0,
            'chemicals_added': 0,
            'groups_added': 0,
            'simulants_updated': 0
        }

    def _load_json(self, filename: str) -> List[Dict]:
        """Load JSON file, return empty list if not found"""
        filepath = self.data_dir / filename
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
        return []

    def _save_json(self, filename: str, data: List[Dict]):
        """Save data to JSON file"""
        filepath = self.data_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  Saved {filepath.name}: {len(data)} entries")

    def _backup_file(self, filename: str):
        """Create backup of existing file"""
        filepath = self.data_dir / filename
        if filepath.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.data_dir / f"{filepath.stem}_backup_{timestamp}.json"
            with open(filepath) as f:
                data = json.load(f)
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  Backup created: {backup_path.name}")

    def find_simulant_id(self, name: str) -> Optional[str]:
        """Find simulant ID by name"""
        name_upper = name.upper()

        # Direct match
        if name_upper in self.name_to_id:
            return self.name_to_id[name_upper]

        # Partial match
        for db_name, sim_id in self.name_to_id.items():
            if name_upper in db_name or db_name in name_upper:
                return sim_id

        return None

    def get_next_composition_id(self) -> str:
        """Get next composition ID"""
        existing_ids = [int(c['composition_id'][1:]) for c in self.composition
                       if c['composition_id'].startswith('C') and c['composition_id'][1:].isdigit()]
        next_num = max(existing_ids, default=0) + 1
        return f"C{next_num:03d}"

    def get_next_chemical_id(self) -> str:
        """Get next chemical composition ID"""
        existing_ids = [int(c['composition_id'][2:]) for c in self.chemicals
                       if c['composition_id'].startswith('CH') and c['composition_id'][2:].isdigit()]
        next_num = max(existing_ids, default=0) + 1
        return f"CH{next_num:03d}"

    def get_next_group_id(self) -> str:
        """Get next mineral group ID"""
        existing_ids = [int(g['group_id'][2:]) for g in self.mineral_groups
                       if g['group_id'].startswith('MG') and g['group_id'][2:].isdigit()]
        next_num = max(existing_ids, default=0) + 1
        return f"MG{next_num:03d}"

    def update_minerals(self, simulant_id: str, minerals: Dict[str, float]):
        """Update mineral composition for a simulant"""
        # Remove existing entries for this simulant
        self.composition = [c for c in self.composition
                          if not (c['simulant_id'] == simulant_id and c.get('component_type') == 'mineral')]

        # Add new entries
        for mineral_name, value in minerals.items():
            if value > 0:
                entry = {
                    'composition_id': self.get_next_composition_id(),
                    'simulant_id': simulant_id,
                    'component_type': 'mineral',
                    'component_name': mineral_name.title(),
                    'value_pct': round(value, 2)
                }
                self.composition.append(entry)
                self.changes['minerals_added'] += 1

    def update_chemicals(self, simulant_id: str, oxides: Dict[str, float]):
        """Update chemical composition for a simulant"""
        # Remove existing entries for this simulant
        self.chemicals = [c for c in self.chemicals
                        if c['simulant_id'] != simulant_id]

        # Add new entries
        for oxide_name, value in oxides.items():
            if value >= 0:  # Include 0 values for completeness
                entry = {
                    'composition_id': self.get_next_chemical_id(),
                    'simulant_id': simulant_id,
                    'component_type': 'oxide',
                    'component_name': oxide_name,
                    'value_wt_pct': round(value, 2)
                }
                self.chemicals.append(entry)
                self.changes['chemicals_added'] += 1

    def update_mineral_groups(self, simulant_id: str, groups: Dict[str, float]):
        """Update NASA mineral groups for a simulant"""
        # Remove existing entries for this simulant
        self.mineral_groups = [g for g in self.mineral_groups
                              if g['simulant_id'] != simulant_id]

        # Add new entries
        for group_name, value in groups.items():
            entry = {
                'group_id': self.get_next_group_id(),
                'simulant_id': simulant_id,
                'group_name': group_name,
                'value_pct': round(value, 2)
            }
            self.mineral_groups.append(entry)
            self.changes['groups_added'] += 1

    def update_simulant_info(self, simulant_id: str, data: SimulantData):
        """Update simulant metadata (FoM, type, etc.)"""
        for sim in self.simulants:
            if sim['simulant_id'] == simulant_id:
                updated = False

                if data.nasa_fom_score and not sim.get('nasa_fom_score'):
                    sim['nasa_fom_score'] = data.nasa_fom_score
                    updated = True

                if data.type and not sim.get('type'):
                    sim['type'] = data.type
                    updated = True

                if data.density_mean and not sim.get('bulk_density'):
                    sim['bulk_density'] = f"{data.density_mean} g/cm³"
                    updated = True

                if data.particle_size_median and not sim.get('particle_size_d50'):
                    sim['particle_size_d50'] = f"{data.particle_size_median} µm"
                    updated = True

                if updated:
                    self.changes['simulants_updated'] += 1
                break

    def process_pdf(self, pdf_path: Path) -> Optional[Tuple[str, SimulantData]]:
        """Process a single PDF and return (simulant_id, extracted_data)"""
        print(f"\nProcessing: {pdf_path.name}")

        data = self.extractor.extract_from_pdf(pdf_path)

        if not data.name:
            print(f"  Warning: Could not extract simulant name")
            return None

        simulant_id = self.find_simulant_id(data.name)

        if not simulant_id:
            print(f"  Warning: '{data.name}' not found in database")
            return None

        print(f"  Matched to: {simulant_id}")
        print(f"  Type: {data.type or 'N/A'}")
        print(f"  FoM: {data.nasa_fom_score or 'N/A'}")
        print(f"  Confidence: {data.extraction_confidence}%")
        print(f"  Minerals: {len(data.mineral_composition)}")
        print(f"  Groups: {len(data.mineral_groups)}")
        print(f"  Oxides: {len(data.chemical_composition)}")

        return (simulant_id, data)

    def run(self, backup: bool = True):
        """Run the full database update"""
        print("=" * 60)
        print("LRS Dashboard Composition Database Update")
        print("=" * 60)

        # Find TDS files
        tds_files = list(self.pdf_dir.glob('*TDS*.pdf')) + list(self.pdf_dir.glob('*_TDS.pdf'))
        tds_files = list(set(tds_files))  # Deduplicate

        if not tds_files:
            print("No TDS files found!")
            return

        print(f"\nFound {len(tds_files)} TDS file(s)")

        # Create backups
        if backup:
            print("\nCreating backups...")
            self._backup_file('composition.json')
            self._backup_file('chemical_composition.json')
            self._backup_file('mineral_groups.json')
            self._backup_file('simulant.json')

        # Process each PDF
        for pdf_path in sorted(tds_files):
            result = self.process_pdf(pdf_path)

            if result:
                simulant_id, data = result

                # Update all databases
                if data.mineral_composition:
                    self.update_minerals(simulant_id, data.mineral_composition)

                if data.mineral_groups:
                    self.update_mineral_groups(simulant_id, data.mineral_groups)

                if data.chemical_composition:
                    self.update_chemicals(simulant_id, data.chemical_composition)

                self.update_simulant_info(simulant_id, data)

        # Save updated databases
        print("\n" + "=" * 60)
        print("Saving updated databases...")
        self._save_json('composition.json', self.composition)
        self._save_json('chemical_composition.json', self.chemicals)
        self._save_json('mineral_groups.json', self.mineral_groups)
        self._save_json('simulant.json', self.simulants)

        # Print summary
        print("\n" + "=" * 60)
        print("Update Summary:")
        print(f"  Minerals added: {self.changes['minerals_added']}")
        print(f"  Chemicals added: {self.changes['chemicals_added']}")
        print(f"  Mineral groups added: {self.changes['groups_added']}")
        print(f"  Simulants updated: {self.changes['simulants_updated']}")
        print("=" * 60)


def main():
    data_dir = Path("/home/alvaro/lrs-dashboard/data")
    pdf_dir = Path("/home/alvaro/Spring - Forest on the moon/DIRT/DIRT Papers")

    updater = CompositionDatabaseUpdater(data_dir, pdf_dir)
    updater.run(backup=True)


if __name__ == "__main__":
    main()

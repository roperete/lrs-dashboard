#!/usr/bin/env python3
"""
Full Database Update Script for LRS Dashboard

Extracts data from ALL supported document formats and updates the database:
- PDF (spec sheets, research papers, books)
- HTML (saved web pages)
- PPTX (PowerPoint)
- DOCX (Word documents)

Updates:
- composition.json (detailed minerals)
- mineral_groups.json (NASA mineral groups)
- chemical_composition.json (oxide composition)
- simulant.json (metadata)
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from collections import defaultdict

# Add extractors to path
sys.path.insert(0, str(Path(__file__).parent))
from extractors.multiformat_extractor import MultiFormatExtractor, SimulantData


class FullDatabaseUpdater:
    """Updates LRS Dashboard database from all document types"""

    def __init__(self, data_dir: Path, docs_dir: Path):
        self.data_dir = Path(data_dir)
        self.docs_dir = Path(docs_dir)
        self.extractor = MultiFormatExtractor()

        # Load existing data
        self.simulants = self._load_json('simulant.json')
        self.composition = self._load_json('composition.json')
        self.chemicals = self._load_json('chemical_composition.json')
        self.mineral_groups = self._load_json('mineral_groups.json')

        # Build name-to-id mapping (handle variations)
        self.name_to_id = {}
        for s in self.simulants:
            name = s['name'].upper()
            self.name_to_id[name] = s['simulant_id']
            # Also add without hyphens for matching
            self.name_to_id[name.replace('-', '')] = s['simulant_id']

        # Track changes
        self.changes = {
            'files_processed': 0,
            'simulants_found': 0,
            'minerals_added': 0,
            'chemicals_added': 0,
            'groups_added': 0,
            'simulants_updated': 0,
            'skipped_no_match': []
        }

        # Aggregate data by simulant (merge from multiple sources)
        self.aggregated_data: Dict[str, SimulantData] = {}

    def _load_json(self, filename: str) -> List[Dict]:
        """Load JSON file"""
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
        """Create backup"""
        filepath = self.data_dir / filename
        if filepath.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.data_dir / f"{filepath.stem}_backup_{timestamp}.json"
            with open(filepath) as f:
                data = json.load(f)
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  Backup: {backup_path.name}")

    def find_simulant_id(self, name: str) -> Optional[str]:
        """Find simulant ID by name"""
        name_upper = name.upper().strip()

        # Direct match
        if name_upper in self.name_to_id:
            return self.name_to_id[name_upper]

        # Without hyphens
        name_no_hyphen = name_upper.replace('-', '')
        if name_no_hyphen in self.name_to_id:
            return self.name_to_id[name_no_hyphen]

        # Partial match
        for db_name, sim_id in self.name_to_id.items():
            if name_upper in db_name or db_name in name_upper:
                return sim_id

        return None

    def get_next_composition_id(self) -> str:
        """Get next composition ID"""
        existing = [int(c['composition_id'][1:]) for c in self.composition
                   if c['composition_id'].startswith('C') and c['composition_id'][1:].isdigit()]
        return f"C{max(existing, default=0) + 1:03d}"

    def get_next_chemical_id(self) -> str:
        """Get next chemical ID"""
        existing = [int(c['composition_id'][2:]) for c in self.chemicals
                   if c['composition_id'].startswith('CH') and c['composition_id'][2:].isdigit()]
        return f"CH{max(existing, default=0) + 1:03d}"

    def get_next_group_id(self) -> str:
        """Get next mineral group ID"""
        existing = [int(g['group_id'][2:]) for g in self.mineral_groups
                   if g['group_id'].startswith('MG') and g['group_id'][2:].isdigit()]
        return f"MG{max(existing, default=0) + 1:03d}"

    def merge_data(self, existing: SimulantData, new: SimulantData) -> SimulantData:
        """Merge new data into existing, preferring higher-confidence values"""
        # Merge chemical composition (keep all unique)
        for oxide, value in new.chemical_composition.items():
            if oxide not in existing.chemical_composition:
                existing.chemical_composition[oxide] = value
            elif new.extraction_confidence > existing.extraction_confidence:
                existing.chemical_composition[oxide] = value

        # Merge mineral composition
        for mineral, value in new.mineral_composition.items():
            if mineral not in existing.mineral_composition:
                existing.mineral_composition[mineral] = value

        # Merge mineral groups
        for group, value in new.mineral_groups.items():
            if group not in existing.mineral_groups:
                existing.mineral_groups[group] = value

        # Merge scalar fields (prefer non-empty)
        if new.type and not existing.type:
            existing.type = new.type
        if new.nasa_fom_score and not existing.nasa_fom_score:
            existing.nasa_fom_score = new.nasa_fom_score
        if new.bulk_density and not existing.bulk_density:
            existing.bulk_density = new.bulk_density
        if new.particle_size_median and not existing.particle_size_median:
            existing.particle_size_median = new.particle_size_median
        if new.cohesion_kpa and not existing.cohesion_kpa:
            existing.cohesion_kpa = new.cohesion_kpa
        if new.friction_angle_deg and not existing.friction_angle_deg:
            existing.friction_angle_deg = new.friction_angle_deg

        # Update confidence
        existing.extraction_confidence = max(existing.extraction_confidence, new.extraction_confidence)
        existing.extraction_methods.extend(new.extraction_methods)

        return existing

    def process_file(self, file_path: Path) -> List[SimulantData]:
        """Process a single file and return extracted data"""
        try:
            results = self.extractor.extract_from_file(file_path)
            self.changes['files_processed'] += 1
            return results
        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
            return []

    def aggregate_results(self, results: List[SimulantData]):
        """Aggregate extraction results by simulant"""
        for data in results:
            if not data.name:
                continue

            sim_id = self.find_simulant_id(data.name)
            if not sim_id:
                if data.name not in self.changes['skipped_no_match']:
                    self.changes['skipped_no_match'].append(data.name)
                continue

            self.changes['simulants_found'] += 1

            if sim_id in self.aggregated_data:
                self.aggregated_data[sim_id] = self.merge_data(
                    self.aggregated_data[sim_id], data
                )
            else:
                data.simulant_id = sim_id
                self.aggregated_data[sim_id] = data

    def update_minerals(self, simulant_id: str, minerals: Dict[str, float]):
        """Update mineral composition"""
        # Remove existing
        self.composition = [c for c in self.composition
                          if not (c['simulant_id'] == simulant_id and c.get('component_type') == 'mineral')]

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
        """Update chemical composition"""
        # Remove existing
        self.chemicals = [c for c in self.chemicals if c['simulant_id'] != simulant_id]

        for oxide_name, value in oxides.items():
            if value >= 0:
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
        """Update NASA mineral groups"""
        # Remove existing
        self.mineral_groups = [g for g in self.mineral_groups if g['simulant_id'] != simulant_id]

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
        """Update simulant metadata"""
        for sim in self.simulants:
            if sim['simulant_id'] == simulant_id:
                updated = False

                if data.nasa_fom_score and not sim.get('nasa_fom_score'):
                    sim['nasa_fom_score'] = data.nasa_fom_score
                    updated = True

                if data.type and not sim.get('type'):
                    sim['type'] = data.type
                    updated = True

                if data.bulk_density and not sim.get('bulk_density'):
                    sim['bulk_density'] = f"{data.bulk_density} g/cm³"
                    updated = True

                if data.particle_size_median and not sim.get('particle_size_d50'):
                    sim['particle_size_d50'] = f"{data.particle_size_median} µm"
                    updated = True

                if data.cohesion_kpa and not sim.get('cohesion'):
                    sim['cohesion'] = f"{data.cohesion_kpa} kPa"
                    updated = True

                if data.friction_angle_deg and not sim.get('friction_angle'):
                    sim['friction_angle'] = f"{data.friction_angle_deg}°"
                    updated = True

                if updated:
                    self.changes['simulants_updated'] += 1
                break

    def apply_aggregated_data(self):
        """Apply all aggregated data to database"""
        print(f"\nApplying data for {len(self.aggregated_data)} simulants...")

        for sim_id, data in self.aggregated_data.items():
            # Only update if we have meaningful data
            has_data = (
                len(data.chemical_composition) >= 3 or
                len(data.mineral_composition) >= 2 or
                data.nasa_fom_score or
                data.type
            )

            if has_data:
                if data.mineral_composition:
                    self.update_minerals(sim_id, data.mineral_composition)

                if data.mineral_groups:
                    self.update_mineral_groups(sim_id, data.mineral_groups)

                if data.chemical_composition:
                    self.update_chemicals(sim_id, data.chemical_composition)

                self.update_simulant_info(sim_id, data)

    def run(self, backup: bool = True):
        """Run the full database update"""
        print("=" * 70)
        print("LRS Dashboard Full Database Update")
        print("=" * 70)

        # Find all supported files
        supported_extensions = ['.pdf', '.html', '.htm', '.pptx', '.docx']
        all_files = []
        for ext in supported_extensions:
            all_files.extend(self.docs_dir.glob(f'*{ext}'))

        # Filter out Zone.Identifier files (Windows metadata)
        all_files = [f for f in all_files if 'Zone.Identifier' not in f.name]

        print(f"\nFound {len(all_files)} documents to process")
        print(f"  PDFs: {len([f for f in all_files if f.suffix == '.pdf'])}")
        print(f"  HTML: {len([f for f in all_files if f.suffix in ['.html', '.htm']])}")
        print(f"  PPTX: {len([f for f in all_files if f.suffix == '.pptx'])}")
        print(f"  DOCX: {len([f for f in all_files if f.suffix == '.docx'])}")

        # Create backups
        if backup:
            print("\nCreating backups...")
            self._backup_file('composition.json')
            self._backup_file('chemical_composition.json')
            self._backup_file('mineral_groups.json')
            self._backup_file('simulant.json')

        # Process files (prioritize spec sheets)
        spec_sheets = [f for f in all_files if 'SPEC' in f.name.upper() or 'TDS' in f.name.upper()]
        other_files = [f for f in all_files if f not in spec_sheets]

        print("\nProcessing spec sheets first...")
        for file_path in spec_sheets:
            print(f"  {file_path.name[:50]}...")
            results = self.process_file(file_path)
            self.aggregate_results(results)
            for r in results:
                if r.name:
                    print(f"    -> {r.name}: chem={len(r.chemical_composition)}, min={len(r.mineral_composition)}")

        print("\nProcessing other documents...")
        for file_path in other_files:
            results = self.process_file(file_path)
            if results:
                self.aggregate_results(results)

        # Apply aggregated data
        self.apply_aggregated_data()

        # Save updated databases
        print("\n" + "=" * 70)
        print("Saving updated databases...")
        self._save_json('composition.json', self.composition)
        self._save_json('chemical_composition.json', self.chemicals)
        self._save_json('mineral_groups.json', self.mineral_groups)
        self._save_json('simulant.json', self.simulants)

        # Print summary
        print("\n" + "=" * 70)
        print("Update Summary:")
        print(f"  Files processed: {self.changes['files_processed']}")
        print(f"  Simulant matches: {self.changes['simulants_found']}")
        print(f"  Minerals added: {self.changes['minerals_added']}")
        print(f"  Chemicals added: {self.changes['chemicals_added']}")
        print(f"  Mineral groups added: {self.changes['groups_added']}")
        print(f"  Simulants updated: {self.changes['simulants_updated']}")

        if self.changes['skipped_no_match']:
            print(f"\n  Unmatched simulants ({len(self.changes['skipped_no_match'])}):")
            for name in sorted(set(self.changes['skipped_no_match']))[:10]:
                print(f"    - {name}")
            if len(self.changes['skipped_no_match']) > 10:
                print(f"    ... and {len(self.changes['skipped_no_match']) - 10} more")

        print("=" * 70)


def main():
    data_dir = Path("/home/alvaro/lrs-dashboard/data")
    docs_dir = Path("/home/alvaro/Spring - Forest on the moon/DIRT/DIRT Papers")

    updater = FullDatabaseUpdater(data_dir, docs_dir)
    updater.run(backup=True)


if __name__ == "__main__":
    main()

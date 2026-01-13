#!/usr/bin/env python3
"""
Simplified AI pipeline test - outputs to CSV instead of Google Sheets
Perfect for testing without Google Cloud setup
"""
import json
import sys
import csv
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from extractors.pdf_extractor import PDFExtractor
from extractors.web_scraper import WebScraper
from extractors.claude_extractor import ClaudeExtractor
from validation import DataValidator
from config import PDF_DIRECTORY, EXTRACTABLE_FIELDS


class SimplePipelineTest:
    """Simplified pipeline for testing - outputs to CSV"""

    def __init__(self):
        print("🤖 Initializing Test Pipeline...")
        self.pdf_extractor = PDFExtractor(PDF_DIRECTORY)
        self.web_scraper = WebScraper()
        self.claude_extractor = ClaudeExtractor()
        self.validator = DataValidator()
        print("✅ Pipeline initialized\n")

    def load_current_data(self):
        """Load current simulant data"""
        data_path = Path(__file__).parent.parent / "data" / "simulant.json"
        with open(data_path, 'r') as f:
            return json.load(f)

    def gather_sources(self, simulant_name: str):
        """Gather sources for a simulant"""
        print(f"{'='*60}")
        print(f"Gathering sources for: {simulant_name}")
        print('='*60)

        all_sources = []

        # Search PDFs
        print("\n📄 Searching local PDFs...")
        pdf_results = self.pdf_extractor.search_for_simulant(simulant_name)
        all_sources.extend(pdf_results)
        print(f"   Found {len(pdf_results)} PDF excerpts")

        # Search web
        print("\n🌐 Searching web...")
        web_results = self.web_scraper.search_for_simulant(simulant_name)
        all_sources.extend(web_results)
        print(f"   Found {len(web_results)} web pages")

        print(f"\n✅ Total sources found: {len(all_sources)}")
        return all_sources

    def extract_and_validate(self, simulant_name: str, simulant_id: str, sources: list):
        """Extract and validate data"""
        if not sources:
            return None

        print(f"\n{'='*60}")
        print("Claude API Extraction")
        print('='*60)

        # Extract from all sources
        extractions = self.claude_extractor.extract_from_multiple_sources(
            simulant_name,
            simulant_id,
            sources
        )

        if not extractions:
            print("⚠️  No data extracted")
            return None

        print(f"\n{'='*60}")
        print("Multi-Source Validation")
        print('='*60)

        # Validate
        validation_results = self.validator.resolve_conflicts_with_claude(
            simulant_name,
            extractions
        )

        # Separate by confidence
        auto_fill = self.validator.get_auto_fillable_fields(validation_results)
        review_required = self.validator.get_review_required_fields(validation_results)

        print(f"\n✅ Validation Results:")
        print(f"   High confidence (auto-fill): {len(auto_fill)} fields")
        print(f"   Low confidence (review): {len(review_required)} fields")

        return {
            "auto_fill": auto_fill,
            "review_required": review_required,
            "all_validations": validation_results,
            "extractions": extractions
        }

    def test_simulant(self, simulant_name: str):
        """Test pipeline on a single simulant"""
        print("\n" + "="*80)
        print(f"TESTING AI PIPELINE: {simulant_name}")
        print("="*80 + "\n")

        # Load data to get simulant info
        simulants = self.load_current_data()
        simulant = next((s for s in simulants if s['name'] == simulant_name), None)

        if not simulant:
            print(f"❌ Simulant '{simulant_name}' not found in database")
            return None

        simulant_id = simulant['simulant_id']

        # Show current data
        print("📊 Current Data:")
        print("-" * 60)
        for field in EXTRACTABLE_FIELDS:
            value = simulant.get(field)
            status = "✓" if value and value not in ['None', 'null', ''] else "✗ MISSING"
            print(f"   {status:12} {field:20}: {value}")
        print()

        # Gather sources
        sources = self.gather_sources(simulant_name)

        if not sources:
            print("\n❌ No sources found. Cannot extract data.")
            return None

        # Extract and validate
        results = self.extract_and_validate(simulant_name, simulant_id, sources)

        if not results:
            print("\n❌ Extraction failed.")
            return None

        # Display results
        print("\n" + "="*80)
        print("EXTRACTION RESULTS")
        print("="*80)

        print("\n🟢 HIGH CONFIDENCE (Auto-fill ready):")
        print("-" * 60)
        if results['auto_fill']:
            for field, value in results['auto_fill'].items():
                validation = results['all_validations'].get(field, {})
                confidence = validation.get('confidence', 0)
                num_sources = validation.get('num_sources', 0)
                print(f"   ✅ {field:20}: {value}")
                print(f"      Confidence: {confidence:.2f} ({num_sources} sources)")
        else:
            print("   (none)")

        print("\n🟡 LOW CONFIDENCE (Manual review needed):")
        print("-" * 60)
        if results['review_required']:
            for field, validation in results['review_required'].items():
                value = validation.get('value')
                confidence = validation.get('confidence', 0)
                all_values = validation.get('all_values')
                print(f"   ⚠️  {field:20}: {value}")
                print(f"      Confidence: {confidence:.2f}")
                if all_values:
                    print(f"      Conflict: {all_values}")
        else:
            print("   (none)")

        # Save to CSV
        self.save_to_csv(simulant_name, simulant_id, results)

        return results

    def save_to_csv(self, simulant_name: str, simulant_id: str, results: dict):
        """Save results to CSV file"""
        output_file = Path(__file__).parent / "extraction_results.csv"

        # Prepare row data
        row = {
            'simulant_id': simulant_id,
            'simulant_name': simulant_name,
            'timestamp': datetime.now().isoformat(),
        }

        # Add extracted fields
        all_validations = results['all_validations']
        for field in EXTRACTABLE_FIELDS:
            if field in all_validations:
                validation = all_validations[field]
                row[f'{field}_value'] = validation.get('value', '')
                row[f'{field}_confidence'] = f"{validation.get('confidence', 0):.2f}"
                row[f'{field}_sources'] = validation.get('num_sources', 0)
                row[f'{field}_status'] = 'AUTO-FILL' if field in results['auto_fill'] else 'REVIEW'

        # Write to CSV
        file_exists = output_file.exists()
        with open(output_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

        print(f"\n💾 Results saved to: {output_file}")

        # Also save detailed JSON
        json_file = Path(__file__).parent / f"extraction_results_{simulant_id}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Detailed results: {json_file}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test AI pipeline on a single simulant")
    parser.add_argument(
        "simulant_name",
        help="Name of simulant to test (e.g., 'JSC-1A', 'EAC-1')"
    )

    args = parser.parse_args()

    # Test
    pipeline = SimplePipelineTest()
    results = pipeline.test_simulant(args.simulant_name)

    if results:
        print("\n" + "="*80)
        print("✅ TEST COMPLETE!")
        print("="*80)
        print("\nNext steps:")
        print("1. Review extraction_results.csv")
        print("2. Check detailed JSON file")
        print("3. If results look good, run on more simulants")
        print("4. Eventually set up Google Sheets for auto-population")
    else:
        print("\n❌ Test failed - see errors above")


if __name__ == "__main__":
    main()

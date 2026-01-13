#!/usr/bin/env python3
"""
AI-powered Data Extraction Pipeline for LRS Dashboard

Automatically extracts and populates missing simulant data from multiple sources
"""
import json
import sys
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from extractors.pdf_extractor import PDFExtractor
from extractors.web_scraper import WebScraper
from extractors.claude_extractor import ClaudeExtractor
from validation import DataValidator
from sheets_writer import SheetsWriter
from config import (
    PDF_DIRECTORY,
    EXTRACTABLE_FIELDS,
    SUPPLIER_SITES
)


class AIDataPipeline:
    """Complete AI-powered data extraction and validation pipeline"""

    def __init__(self, credentials_file: str):
        """
        Initialize the pipeline

        Args:
            credentials_file: Path to Google Sheets service account credentials
        """
        print("🤖 Initializing AI Data Pipeline...")

        self.pdf_extractor = PDFExtractor(PDF_DIRECTORY)
        self.web_scraper = WebScraper()
        self.claude_extractor = ClaudeExtractor()
        self.validator = DataValidator()
        self.sheets_writer = SheetsWriter(credentials_file)

        print("✅ Pipeline initialized")

    def load_current_data(self) -> List[Dict]:
        """Load current simulant data to identify gaps"""
        data_path = Path(__file__).parent.parent / "data" / "simulant.json"
        with open(data_path, 'r') as f:
            return json.load(f)

    def gather_sources_for_simulant(self, simulant_name: str) -> List[Dict[str, str]]:
        """
        Gather all available sources for a simulant

        Returns: List of {source, text, source_type} dicts
        """
        print(f"\n{'='*60}")
        print(f"Gathering sources for: {simulant_name}")
        print('='*60)

        all_sources = []

        # 1. Search PDFs
        print("📄 Searching local PDFs...")
        pdf_results = self.pdf_extractor.search_for_simulant(simulant_name)
        all_sources.extend(pdf_results)

        # 2. Search web
        print("🌐 Searching web...")
        web_results = self.web_scraper.search_for_simulant(simulant_name)
        all_sources.extend(web_results)

        # 3. Check supplier sites
        print("🏢 Checking supplier sites...")
        for supplier, url in SUPPLIER_SITES.items():
            result = self.web_scraper.scrape_supplier_site(url, simulant_name)
            if result:
                all_sources.append(result)

        print(f"✅ Found {len(all_sources)} sources total")
        return all_sources

    def extract_and_validate(
        self,
        simulant_name: str,
        simulant_id: str,
        sources: List[Dict[str, str]]
    ) -> Dict:
        """
        Extract data from sources and validate

        Returns: {
            "auto_fill": {field: value},  # High confidence, can auto-fill
            "review_required": {field: validation_result}  # Needs review
        }
        """
        if not sources:
            return {"auto_fill": {}, "review_required": {}}

        print(f"\n🤖 Extracting data with Claude API...")

        # Extract from all sources
        extractions = self.claude_extractor.extract_from_multiple_sources(
            simulant_name,
            simulant_id,
            sources
        )

        if not extractions:
            print("⚠️  No data extracted")
            return {"auto_fill": {}, "review_required": {}}

        print(f"\n🔍 Validating across {len(extractions)} extractions...")

        # Validate with multi-source checking
        validation_results = self.validator.resolve_conflicts_with_claude(
            simulant_name,
            extractions
        )

        # Separate auto-fillable from review-required
        auto_fill = self.validator.get_auto_fillable_fields(validation_results)
        review_required = self.validator.get_review_required_fields(validation_results)

        print(f"\n✅ Validation complete:")
        print(f"   Auto-fill ready: {len(auto_fill)} fields")
        print(f"   Review required: {len(review_required)} fields")

        return {
            "auto_fill": auto_fill,
            "review_required": review_required,
            "all_validations": validation_results
        }

    def process_simulant(self, simulant: Dict) -> Dict:
        """
        Process a single simulant: gather sources, extract, validate, update

        Returns: Results summary
        """
        simulant_name = simulant['name']
        simulant_id = simulant['simulant_id']

        # Check which fields are missing
        missing_fields = [
            field for field in EXTRACTABLE_FIELDS
            if not simulant.get(field) or simulant.get(field) in ['None', 'null', '']
        ]

        if not missing_fields:
            print(f"\n✅ {simulant_name}: No missing fields, skipping")
            return {"status": "complete", "updated": {}}

        print(f"\n📋 {simulant_name}: Missing {len(missing_fields)} fields: {missing_fields}")

        # Gather sources
        sources = self.gather_sources_for_simulant(simulant_name)

        if not sources:
            print(f"⚠️  No sources found for {simulant_name}")
            return {"status": "no_sources", "updated": {}}

        # Extract and validate
        results = self.extract_and_validate(simulant_name, simulant_id, sources)

        # Update Google Sheets with auto-fillable data
        auto_fill = results['auto_fill']
        if auto_fill:
            print(f"\n📝 Writing {len(auto_fill)} fields to Google Sheets...")
            update_results = self.sheets_writer.update_simulant(
                simulant_name,
                auto_fill,
                provenance="AI-extracted (multi-source validated)"
            )

            updated_count = sum(1 for success in update_results.values() if success)
            print(f"   ✅ Successfully updated {updated_count}/{len(auto_fill)} fields")

        # Report review-required fields
        review_required = results['review_required']
        if review_required:
            print(f"\n⚠️  {len(review_required)} fields require manual review:")
            for field, validation in review_required.items():
                print(f"   - {field}: {validation}")

        return {
            "status": "processed",
            "auto_filled": auto_fill,
            "review_required": review_required,
            "sources_found": len(sources)
        }

    def run_pipeline(self, limit: int = None, simulant_names: List[str] = None):
        """
        Run the complete pipeline

        Args:
            limit: Max number of simulants to process (None for all)
            simulant_names: Specific simulant names to process (None for all)
        """
        print("=" * 80)
        print("AI-POWERED DATA EXTRACTION PIPELINE")
        print("=" * 80)

        # Load current data
        simulants = self.load_current_data()
        print(f"\n📊 Loaded {len(simulants)} simulants from database")

        # Filter if specific names provided
        if simulant_names:
            simulants = [s for s in simulants if s['name'] in simulant_names]
            print(f"   Processing only: {simulant_names}")

        # Apply limit
        if limit:
            simulants = simulants[:limit]
            print(f"   Limited to first {limit} simulants")

        # Ensure provenance column exists
        self.sheets_writer.add_provenance_column()

        # Process each simulant
        results = {}
        for simulant in tqdm(simulants, desc="Processing simulants"):
            try:
                result = self.process_simulant(simulant)
                results[simulant['name']] = result
            except Exception as e:
                print(f"\n❌ Error processing {simulant['name']}: {e}")
                results[simulant['name']] = {"status": "error", "error": str(e)}

        # Summary
        print("\n" + "=" * 80)
        print("PIPELINE COMPLETE")
        print("=" * 80)

        total_processed = sum(1 for r in results.values() if r.get('status') == 'processed')
        total_updated = sum(len(r.get('auto_filled', {})) for r in results.values())
        total_review = sum(len(r.get('review_required', {})) for r in results.values())

        print(f"\n📊 Summary:")
        print(f"   Simulants processed: {total_processed}/{len(simulants)}")
        print(f"   Fields auto-filled: {total_updated}")
        print(f"   Fields requiring review: {total_review}")

        # Save detailed results
        results_file = Path(__file__).parent / "pipeline_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Detailed results saved to: {results_file}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="AI-powered data extraction pipeline")
    parser.add_argument(
        "--credentials",
        required=True,
        help="Path to Google Sheets service account credentials JSON"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Max number of simulants to process (for testing)"
    )
    parser.add_argument(
        "--simulants",
        nargs="+",
        help="Specific simulant names to process"
    )

    args = parser.parse_args()

    # Initialize and run pipeline
    pipeline = AIDataPipeline(args.credentials)
    pipeline.run_pipeline(
        limit=args.limit,
        simulant_names=args.simulants
    )


if __name__ == "__main__":
    main()

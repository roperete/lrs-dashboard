#!/usr/bin/env python3
"""
Quick test of the AI pipeline - PDF only, limited sources
Run: python quick_test.py "JSC-1A"
"""
import json
import sys
import csv
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from extractors.pdf_extractor import PDFExtractor
from extractors.claude_extractor import ClaudeExtractor
from config import PDF_DIRECTORY, EXTRACTABLE_FIELDS, CLAUDE_MODEL

# Test settings - keep it fast and cheap
MAX_PDF_SOURCES = 10  # Process top 10 unique PDF sources
SKIP_WEB_SCRAPING = True  # Skip slow web scraping


def load_simulant_data():
    """Load current simulant data"""
    data_path = Path(__file__).parent.parent / "data" / "simulant.json"
    with open(data_path, 'r') as f:
        return json.load(f)


def find_simulant(data, name):
    """Find simulant by name (case-insensitive, partial match)"""
    name_lower = name.lower()
    for s in data:
        sim_name = s.get('name', '').lower()
        # Try exact match first
        if sim_name == name_lower:
            return s
        # Try partial match (simulant name contains search term)
        if name_lower in sim_name or sim_name in name_lower:
            return s
    return None


def run_quick_test(simulant_name: str):
    """Run a quick test on a single simulant"""
    print(f"\n{'='*60}")
    print(f"QUICK TEST: {simulant_name}")
    print(f"Model: {CLAUDE_MODEL}")
    print(f"Max sources: {MAX_PDF_SOURCES}")
    print(f"Web scraping: {'Enabled' if not SKIP_WEB_SCRAPING else 'Disabled (for speed)'}")
    print(f"{'='*60}\n")

    # Load data
    data = load_simulant_data()
    simulant = find_simulant(data, simulant_name)

    if not simulant:
        print(f"ERROR: Simulant '{simulant_name}' not found in database")
        return None

    simulant_id = simulant.get('simulant_id', 'unknown')
    print(f"Found: {simulant_name} (ID: {simulant_id})")

    # Show current data gaps
    print("\nCurrent data status:")
    for field in EXTRACTABLE_FIELDS:
        value = simulant.get(field)
        status = "OK" if value else "MISSING"
        print(f"  [{status:7}] {field}: {value or '(empty)'}")

    # Step 1: Search PDFs
    print(f"\n{'='*60}")
    print("Step 1: Searching PDFs")
    print('='*60)

    pdf_extractor = PDFExtractor(PDF_DIRECTORY)
    pdf_results = pdf_extractor.search_for_simulant(simulant_name)
    print(f"Found {len(pdf_results)} PDF excerpts")

    if len(pdf_results) > MAX_PDF_SOURCES:
        # Get one excerpt per unique PDF file for better diversity
        seen_files = set()
        diverse_results = []
        for result in pdf_results:
            file_path = result.get('file_path', '')
            if file_path not in seen_files:
                seen_files.add(file_path)
                diverse_results.append(result)
                if len(diverse_results) >= MAX_PDF_SOURCES:
                    break
        print(f"Selected {len(diverse_results)} sources from different PDFs (found {len(pdf_results)} total excerpts)")
        pdf_results = diverse_results

    if not pdf_results:
        print("No PDF sources found!")
        return None

    # Step 2: Extract with Claude
    print(f"\n{'='*60}")
    print("Step 2: Claude API Extraction")
    print('='*60)

    claude = ClaudeExtractor()
    extractions = []

    for i, source in enumerate(pdf_results, 1):
        source_name = source.get('source', 'Unknown')[:50]
        print(f"\n[{i}/{len(pdf_results)}] Processing: {source_name}...")

        try:
            result = claude.extract_from_text(
                simulant_name,
                simulant_id,
                source.get('text', '')
            )
            if result:
                extractions.append(result)
                print(f"   Extracted: {list(k for k,v in result.items() if v)}")
            else:
                print("   No data extracted")
        except Exception as e:
            print(f"   ERROR: {e}")

    # Step 3: Aggregate results
    print(f"\n{'='*60}")
    print("Step 3: Results Summary")
    print('='*60)

    if not extractions:
        print("No data was extracted from any source.")
        return None

    # Aggregate extracted values
    aggregated = {}
    for field in EXTRACTABLE_FIELDS:
        values = [e.get(field) for e in extractions if e.get(field)]
        if values:
            # Take most common value (simple approach)
            aggregated[field] = max(set(values), key=values.count)
            agreement = values.count(aggregated[field]) / len(values) * 100
            print(f"  {field}: {aggregated[field]} ({agreement:.0f}% agreement, {len(values)} sources)")
        else:
            print(f"  {field}: (no data found)")

    # Save results
    output_file = Path(__file__).parent / f"test_results_{simulant_id}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'simulant_name': simulant_name,
            'simulant_id': simulant_id,
            'timestamp': datetime.now().isoformat(),
            'sources_searched': len(pdf_results),
            'extractions': extractions,
            'aggregated': aggregated
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    return aggregated


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_test.py <simulant_name>")
        print("Example: python quick_test.py 'JSC-1A'")
        sys.exit(1)

    simulant_name = sys.argv[1]
    run_quick_test(simulant_name)

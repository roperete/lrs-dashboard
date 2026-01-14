#!/usr/bin/env python3
"""
Fast AI pipeline test - uses pre-built PDF index for instant lookups.
Run build_pdf_index.py first to create the index.

Usage: python fast_test.py "JSC-1A"
"""
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from extractors.document_extractor import DocumentExtractor
from extractors.claude_extractor import ClaudeExtractor
from config import PDF_DIRECTORY, EXTRACTABLE_FIELDS, CLAUDE_MODEL

# Settings
MAX_PDF_SOURCES = 10
INDEX_FILE = Path(__file__).parent / "pdf_index.json"


def load_index():
    """Load the pre-built PDF index"""
    if not INDEX_FILE.exists():
        print(f"ERROR: Index file not found: {INDEX_FILE}")
        print("Run 'python build_pdf_index.py' first to create the index.")
        sys.exit(1)

    with open(INDEX_FILE, 'r') as f:
        return json.load(f)


def load_simulant_data():
    """Load current simulant data"""
    data_path = Path(__file__).parent.parent / "data" / "simulant.json"
    with open(data_path, 'r') as f:
        return json.load(f)


def find_simulant(data, name):
    """Find simulant by name"""
    name_lower = name.lower()
    for s in data:
        sim_name = s.get('name', '').lower()
        if sim_name == name_lower or name_lower in sim_name:
            return s
    return None


def get_pdfs_for_simulant(index, simulant_id):
    """Get list of PDFs that mention this simulant (from index)"""
    return index.get("simulant_to_pdfs", {}).get(simulant_id, [])


def run_fast_test(simulant_name: str):
    """Run a fast test using the pre-built index"""
    print(f"\n{'='*60}")
    print(f"FAST TEST: {simulant_name}")
    print(f"Model: {CLAUDE_MODEL}")
    print(f"Using pre-built PDF index (instant lookup)")
    print(f"{'='*60}\n")

    # Load index
    index = load_index()
    print(f"Index loaded: {index.get('num_documents', index.get('num_pdfs', 0))} documents, {index['num_simulants']} simulants")

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

    # Get PDFs from index (INSTANT - no scanning!)
    print(f"\n{'='*60}")
    print("Step 1: Looking up PDFs from index (instant!)")
    print('='*60)

    pdf_list = get_pdfs_for_simulant(index, simulant_id)
    print(f"Found {len(pdf_list)} PDFs mentioning {simulant_name}")

    if not pdf_list:
        print("No PDFs found in index for this simulant.")
        return None

    # Limit to top PDFs by mention count
    if len(pdf_list) > MAX_PDF_SOURCES:
        pdf_list = pdf_list[:MAX_PDF_SOURCES]
        print(f"Using top {MAX_PDF_SOURCES} PDFs by mention count")

    # Now extract text from those specific PDFs only
    print(f"\n{'='*60}")
    print("Step 2: Extracting text from indexed PDFs")
    print('='*60)

    extractor = DocumentExtractor(PDF_DIRECTORY)
    sources = []

    for pdf_info in pdf_list:
        pdf_path = Path(pdf_info['path'])
        if pdf_path.exists():
            text = extractor.extract_text(pdf_path)
            # Extract context around simulant mention
            excerpts = extractor._extract_context(text, simulant_name, context_size=4000)
            if excerpts:
                sources.append({
                    "source": f"PDF: {pdf_path.name}",
                    "file_path": str(pdf_path),
                    "text": excerpts[0],  # Take first excerpt
                    "source_type": "pdf",
                    "mentions": pdf_info['mentions']
                })
                print(f"  Extracted from: {pdf_path.name} ({pdf_info['mentions']} mentions)")

    print(f"\nTotal sources ready: {len(sources)}")

    if not sources:
        print("No text extracted from PDFs.")
        return None

    # Extract with Claude
    print(f"\n{'='*60}")
    print("Step 3: Claude API Extraction")
    print('='*60)

    claude = ClaudeExtractor()
    extractions = []

    for i, source in enumerate(sources, 1):
        source_name = source.get('source', 'Unknown')[:50]
        print(f"\n[{i}/{len(sources)}] Processing: {source_name}...")

        try:
            result = claude.extract_from_text(
                simulant_name,
                simulant_id,
                source.get('text', '')
            )
            if result:
                extractions.append(result)
                extracted_fields = [k for k, v in result.items() if v and not k.startswith('_')]
                print(f"   Extracted: {extracted_fields}")
            else:
                print("   No data extracted")
        except Exception as e:
            print(f"   ERROR: {e}")

    # Aggregate results
    print(f"\n{'='*60}")
    print("Step 4: Results Summary")
    print('='*60)

    if not extractions:
        print("No data was extracted from any source.")
        return None

    aggregated = {}
    for field in EXTRACTABLE_FIELDS:
        values = [e.get(field) for e in extractions if e.get(field)]
        if values:
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
            'sources_searched': len(sources),
            'extractions': extractions,
            'aggregated': aggregated
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    return aggregated


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fast_test.py <simulant_name>")
        print("Example: python fast_test.py 'JSC-1A'")
        sys.exit(1)

    simulant_name = sys.argv[1]
    run_fast_test(simulant_name)

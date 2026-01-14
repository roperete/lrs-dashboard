#!/usr/bin/env python3
"""
Batch extraction - Process all simulants.
Automatically rebuilds the PDF index before extraction to pick up new files.

Usage: python batch_extract.py
"""
import json
import sys
import csv
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import time

sys.path.insert(0, str(Path(__file__).parent))

from extractors.document_extractor import DocumentExtractor
from extractors.claude_extractor import ClaudeExtractor
from config import PDF_DIRECTORY, EXTRACTABLE_FIELDS, CLAUDE_MODEL
from build_pdf_index import build_index

# Settings
MAX_SOURCES_PER_SIMULANT = 10
INDEX_FILE = Path(__file__).parent / "pdf_index.json"
RESULTS_DIR = Path(__file__).parent / "extraction_results"
CSV_OUTPUT = Path(__file__).parent / "all_extractions.csv"


def load_index():
    """Load the pre-built document index"""
    if not INDEX_FILE.exists():
        print(f"ERROR: Index file not found: {INDEX_FILE}")
        print("Run 'python build_pdf_index.py' first.")
        sys.exit(1)
    with open(INDEX_FILE, 'r') as f:
        return json.load(f)


def load_all_simulants():
    """Load all simulants from the database"""
    data_path = Path(__file__).parent.parent / "data" / "simulant.json"
    with open(data_path, 'r') as f:
        return json.load(f)


def get_docs_for_simulant(index, simulant_id):
    """Get list of documents that mention this simulant"""
    return index.get("simulant_to_pdfs", {}).get(simulant_id, [])


def process_simulant(simulant, index, extractor, claude):
    """Process a single simulant and return extracted data"""
    name = simulant.get('name', 'Unknown')
    sim_id = simulant.get('simulant_id', 'unknown')

    # Get documents from index
    doc_list = get_docs_for_simulant(index, sim_id)

    if not doc_list:
        return {
            'simulant_id': sim_id,
            'name': name,
            'status': 'no_documents',
            'sources_found': 0,
            'extractions': [],
            'aggregated': {}
        }

    # Limit sources
    doc_list = doc_list[:MAX_SOURCES_PER_SIMULANT]

    # Extract text from documents
    sources = []
    for doc_info in doc_list:
        doc_path = Path(doc_info['path'])
        if doc_path.exists():
            text = extractor.extract_text(doc_path)
            excerpts = extractor._extract_context(text, name, context_size=4000)
            if excerpts:
                sources.append({
                    "source": doc_path.name,
                    "text": excerpts[0],
                    "mentions": doc_info['mentions']
                })

    if not sources:
        return {
            'simulant_id': sim_id,
            'name': name,
            'status': 'no_text_extracted',
            'sources_found': len(doc_list),
            'extractions': [],
            'aggregated': {}
        }

    # Extract with Claude
    extractions = []
    for source in sources:
        try:
            result = claude.extract_from_text(name, sim_id, source['text'])
            if result:
                extractions.append(result)
        except Exception as e:
            pass  # Skip failed extractions

        # Small delay to avoid rate limiting
        time.sleep(0.5)

    # Aggregate results
    aggregated = {}
    for field in EXTRACTABLE_FIELDS:
        values = [e.get(field) for e in extractions if e.get(field)]
        if values:
            aggregated[field] = max(set(values), key=values.count)

    return {
        'simulant_id': sim_id,
        'name': name,
        'status': 'success',
        'sources_found': len(doc_list),
        'sources_processed': len(sources),
        'extractions_successful': len(extractions),
        'extractions': extractions,
        'aggregated': aggregated
    }


def save_results_csv(all_results, simulants):
    """Save all results to a single CSV file"""
    # Build rows with both existing and extracted data
    rows = []

    for simulant in simulants:
        sim_id = simulant.get('simulant_id', '')
        result = next((r for r in all_results if r['simulant_id'] == sim_id), None)

        row = {
            'simulant_id': sim_id,
            'name': simulant.get('name', ''),
            'status': result['status'] if result else 'not_processed',
            'sources_found': result['sources_found'] if result else 0,
        }

        # Add existing data and extracted data for each field
        for field in EXTRACTABLE_FIELDS:
            existing = simulant.get(field)
            extracted = result['aggregated'].get(field) if result else None

            row[f'{field}_existing'] = existing if existing else ''
            row[f'{field}_extracted'] = extracted if extracted else ''
            row[f'{field}_final'] = existing if existing else (extracted if extracted else '')

        rows.append(row)

    # Write CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(CSV_OUTPUT, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"\nCSV saved to: {CSV_OUTPUT}")


def main():
    print("="*70)
    print("BATCH EXTRACTION - Processing All Simulants")
    print("="*70)
    print(f"Model: {CLAUDE_MODEL}")
    print(f"Max sources per simulant: {MAX_SOURCES_PER_SIMULANT}")
    print()

    # Rebuild index to pick up any new files
    print("Rebuilding document index...")
    build_index()
    print()

    # Load index and data
    index = load_index()
    simulants = load_all_simulants()

    print(f"Index: {index.get('num_documents', 0)} documents")
    print(f"Simulants to process: {len(simulants)}")
    print()

    # Create results directory
    RESULTS_DIR.mkdir(exist_ok=True)

    # Initialize extractors
    extractor = DocumentExtractor(PDF_DIRECTORY)
    claude = ClaudeExtractor()

    # Process all simulants
    all_results = []
    stats = {'success': 0, 'no_documents': 0, 'no_text': 0, 'errors': 0}

    print("Starting extraction...\n")

    for simulant in tqdm(simulants, desc="Processing simulants"):
        name = simulant.get('name', 'Unknown')
        sim_id = simulant.get('simulant_id', 'unknown')

        try:
            result = process_simulant(simulant, index, extractor, claude)
            all_results.append(result)

            # Update stats
            if result['status'] == 'success':
                stats['success'] += 1
            elif result['status'] == 'no_documents':
                stats['no_documents'] += 1
            else:
                stats['no_text'] += 1

            # Save individual result
            result_file = RESULTS_DIR / f"{sim_id}.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)

        except Exception as e:
            stats['errors'] += 1
            tqdm.write(f"  Error processing {name}: {e}")
            all_results.append({
                'simulant_id': sim_id,
                'name': name,
                'status': 'error',
                'error': str(e)
            })

    # Save combined results
    combined_file = RESULTS_DIR / "all_results.json"
    with open(combined_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_simulants': len(simulants),
            'stats': stats,
            'results': all_results
        }, f, indent=2)

    # Save CSV
    save_results_csv(all_results, simulants)

    # Print summary
    print("\n" + "="*70)
    print("EXTRACTION COMPLETE")
    print("="*70)
    print(f"\nResults:")
    print(f"  Successful extractions: {stats['success']}")
    print(f"  No documents found: {stats['no_documents']}")
    print(f"  No text extracted: {stats['no_text']}")
    print(f"  Errors: {stats['errors']}")
    print(f"\nFiles saved:")
    print(f"  Individual results: {RESULTS_DIR}/")
    print(f"  Combined JSON: {combined_file}")
    print(f"  CSV summary: {CSV_OUTPUT}")

    # Show fields with most extractions
    print("\nFields with extracted data:")
    field_counts = {field: 0 for field in EXTRACTABLE_FIELDS}
    for result in all_results:
        for field in EXTRACTABLE_FIELDS:
            if result.get('aggregated', {}).get(field):
                field_counts[field] += 1

    for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {field}: {count} simulants")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Build a PDF index mapping simulants to PDFs that mention them.
Run this once to speed up all subsequent searches.

Usage: python build_pdf_index.py
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))

from extractors.document_extractor import DocumentExtractor
from config import PDF_DIRECTORY

# Output file
INDEX_FILE = Path(__file__).parent / "pdf_index.json"


def load_simulant_names():
    """Load all simulant names from the database"""
    data_path = Path(__file__).parent.parent / "data" / "simulant.json"
    with open(data_path, 'r') as f:
        data = json.load(f)

    simulants = []
    for s in data:
        name = s.get('name', '')
        sim_id = s.get('simulant_id', '')
        if name:
            simulants.append({
                'name': name,
                'id': sim_id,
                # Also create search variants
                'variants': [
                    name,
                    name.lower(),
                    name.replace('-', ' '),
                    name.replace('-', ''),
                ]
            })
    return simulants


def build_index():
    """Build the PDF index"""
    print("="*60)
    print("Building PDF Index")
    print("="*60)

    # Load simulants
    simulants = load_simulant_names()
    print(f"\nLoaded {len(simulants)} simulants from database")

    # Initialize extractor
    extractor = DocumentExtractor(PDF_DIRECTORY)
    documents = extractor.find_documents()

    if not documents:
        print("No documents found!")
        return

    # Index structure
    index = {
        "created": datetime.now().isoformat(),
        "document_directory": str(PDF_DIRECTORY),
        "num_documents": len(documents),
        "num_simulants": len(simulants),
        # Mapping: simulant_id -> list of {doc_path, excerpt_count}
        "simulant_to_pdfs": {},
        # Mapping: doc_path -> list of simulant_ids found
        "pdf_to_simulants": {},
        # Store document metadata
        "pdf_metadata": {},
    }

    print(f"\nScanning {len(documents)} documents for {len(simulants)} simulants...")
    print("This will take a few minutes but only needs to run once.\n")

    # Scan each document
    for doc_path in tqdm(documents, desc="Scanning documents"):
        try:
            # Extract text once
            text = extractor.extract_text(doc_path)
            text_lower = text.lower()

            pdf_key = str(doc_path)
            index["pdf_metadata"][pdf_key] = {
                "name": doc_path.name,
                "size_chars": len(text),
            }

            found_simulants = []

            # Check each simulant
            for sim in simulants:
                # Check if any variant is mentioned
                for variant in sim['variants']:
                    if variant.lower() in text_lower:
                        found_simulants.append(sim['id'])

                        # Count mentions
                        count = text_lower.count(variant.lower())

                        # Add to simulant_to_pdfs
                        if sim['id'] not in index["simulant_to_pdfs"]:
                            index["simulant_to_pdfs"][sim['id']] = []

                        # Check if PDF already added
                        existing = [p for p in index["simulant_to_pdfs"][sim['id']]
                                   if p['path'] == pdf_key]
                        if not existing:
                            index["simulant_to_pdfs"][sim['id']].append({
                                "path": pdf_key,
                                "name": doc_path.name,
                                "mentions": count,
                            })
                        break  # Found in this PDF, no need to check other variants

            # Add to pdf_to_simulants
            if found_simulants:
                index["pdf_to_simulants"][pdf_key] = list(set(found_simulants))

        except Exception as e:
            print(f"\n  Error processing {doc_path.name}: {e}")

    # Sort simulant PDFs by mention count
    for sim_id in index["simulant_to_pdfs"]:
        index["simulant_to_pdfs"][sim_id].sort(key=lambda x: x['mentions'], reverse=True)

    # Save index
    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f, indent=2)

    # Print summary
    print("\n" + "="*60)
    print("Index Built Successfully!")
    print("="*60)
    print(f"\nSaved to: {INDEX_FILE}")
    print(f"Documents scanned: {len(documents)}")
    print(f"Simulants indexed: {len(index['simulant_to_pdfs'])}")

    # Show top simulants by document coverage
    print("\nTop 10 simulants by document coverage:")
    coverage = [(sim_id, len(docs)) for sim_id, docs in index["simulant_to_pdfs"].items()]
    coverage.sort(key=lambda x: x[1], reverse=True)
    for sim_id, count in coverage[:10]:
        # Get name
        name = next((s['name'] for s in simulants if s['id'] == sim_id), sim_id)
        print(f"  {name}: {count} PDFs")

    return index


if __name__ == "__main__":
    build_index()

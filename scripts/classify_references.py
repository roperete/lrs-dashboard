#!/usr/bin/env python3
"""
Classify references into composition sources vs usage papers.

Composition source = The paper that INTRODUCES/CREATES/DEFINES the simulant
Usage paper = Papers that USE the simulant in experiments/studies
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'

# Strong indicators that this is THE composition paper (introducing the simulant)
COMPOSITION_STRONG = [
    'preparation and characterization',
    'development and mechanical properties',
    'new lunar soil simulant',
    'new martian soil simulant',
    'lunar soil simulant.',  # Title ends with simulant name
    'regolith simulant.',
    'spec sheet', 'technical data sheet', 'tds',
    'cas-1 lunar soil simulant',  # Specific simulant introductions
    'jsc-1 lunar soil simulant',
    'jsc mars-1',
    'mms-1', 'mms-2',
    'produced a new'
]

# Keywords that strongly indicate USAGE (applying simulant in experiments)
USAGE_STRONG = [
    'sintered lunar soil',
    'sintering',
    'geopolymer based on',
    'sustain plant growth',
    'excavation',
    '3d printing',
    'additive manufacturing',
    'building components',
    'micromechanical behavior',
    'grown on',
    'cultivat',
    'with lunar simulant',
    'with martian simulant',
    'using lunar',
    'using martian',
    'tested on',
    'experiments with',
    'low gravity simulation'
]

def classify_reference(ref_text: str, simulant_name: str) -> str:
    """
    Classify a reference as 'composition' or 'usage'.

    Composition = Paper introducing/defining the simulant and its properties
    Usage = Paper using the simulant for experiments/applications
    """
    text_lower = ref_text.lower()
    simulant_lower = simulant_name.lower() if simulant_name else ''

    # Check for strong composition indicators
    for kw in COMPOSITION_STRONG:
        if kw in text_lower:
            return 'composition'

    # Check if simulant name is prominently in title (likely composition paper)
    # e.g., "CAS-1 lunar soil simulant" or "JSC-1A simulant"
    if simulant_lower and simulant_lower.replace('-', ' ') in text_lower.replace('-', ' '):
        # Check if it's describing the simulant itself vs using it
        words_after_sim = text_lower.split(simulant_lower)[-1][:50] if simulant_lower in text_lower else ''
        if any(kw in words_after_sim for kw in ['soil simulant', 'regolith simulant', 'properties', 'characterization']):
            return 'composition'

    # Check for strong usage indicators
    for kw in USAGE_STRONG:
        if kw in text_lower:
            return 'usage'

    # Default to usage (most papers in a database are usage papers)
    return 'usage'


def main():
    # Load references
    refs_path = DATA_DIR / 'references.json'
    simulants_path = DATA_DIR / 'simulant.json'

    with open(refs_path) as f:
        references = json.load(f)

    with open(simulants_path) as f:
        simulants = json.load(f)

    # Create simulant lookup
    sim_lookup = {s['simulant_id']: s['name'] for s in simulants}

    # Classify each reference
    classified = []
    composition_count = 0
    usage_count = 0

    for ref in references:
        sim_name = sim_lookup.get(ref.get('simulant_id'), '')
        ref_type = classify_reference(ref.get('reference_text', ''), sim_name)

        # Add reference_type field
        ref['reference_type'] = ref_type
        classified.append(ref)

        if ref_type == 'composition':
            composition_count += 1
        else:
            usage_count += 1

    # Save updated references
    with open(refs_path, 'w') as f:
        json.dump(classified, f, indent=2)

    print(f"Classified {len(classified)} references:")
    print(f"  Composition sources: {composition_count}")
    print(f"  Usage papers: {usage_count}")

    # Show some examples
    print("\nSample composition sources:")
    for ref in classified[:5]:
        if ref['reference_type'] == 'composition':
            sim = sim_lookup.get(ref['simulant_id'], 'Unknown')
            text = ref['reference_text'][:80] + '...' if len(ref['reference_text']) > 80 else ref['reference_text']
            print(f"  [{sim}] {text}")

    print("\nSample usage papers:")
    for ref in classified[:5]:
        if ref['reference_type'] == 'usage':
            sim = sim_lookup.get(ref['simulant_id'], 'Unknown')
            text = ref['reference_text'][:80] + '...' if len(ref['reference_text']) > 80 else ref['reference_text']
            print(f"  [{sim}] {text}")


if __name__ == '__main__':
    main()

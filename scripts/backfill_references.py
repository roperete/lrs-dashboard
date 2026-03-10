#!/usr/bin/env python3
"""
Backfill references for simulants that currently have none.
Uses the source-simulant-index.json to match simulants to sources,
then creates proper citation entries in references.json.
"""

import json
import re
from pathlib import Path
from html.parser import HTMLParser

DATA_DIR = Path(__file__).parent.parent / "public" / "data"
SOURCES_DIR = Path("/home/alvaro/LRS/Sources")
INDEX_FILE = Path(__file__).parent.parent / "documentation" / "source-simulant-index.json"

# ── Manually curated citation metadata for key sources ──
# These are the real papers/reports that our source index matched to simulants.
# Each key is the HTML filename from LRS/Sources/.

CITATION_DB = {
    "Chen et al. - 2025 - An overview on lunar rego.html": {
        "title": "An overview on lunar regolith simulants solidification methods: integrating chemical, physical, and MICP strategies for extraterrestrial construction",
        "authors": "Chen, Y., Tian, A., Min, G., Fukuda, D., Kawasaki, S.",
        "year": 2025,
        "doi": "10.1016/j.bgtech.2025.100212",
        "url": "https://doi.org/10.1016/j.bgtech.2025.100212",
        "reference_type": "review"
    },
    "In-Situ Resource Utilization Gap Assessment Re.html": {
        "title": "In-Situ Resource Utilization Gap Assessment Report",
        "authors": "International Space Exploration Coordination Group (ISECG)",
        "year": 2021,
        "doi": None,
        "url": "https://www.globalspaceexploration.org/wordpress/wp-content/uploads/2021/04/ISRU-Gap-Assessment-Report-2021.pdf",
        "reference_type": "report"
    },
    "2024_Lunar_Simulant_Assessment_Report.pdf.html": {
        "title": "2024 Lunar Simulant Assessment",
        "authors": "Martin, A., Wagoner, C., Stockstill-Cahill, K., Blewett, D., Bobea Graziano, M.",
        "year": 2025,
        "doi": None,
        "url": None,
        "reference_type": "report"
    },
    "1-s2.0-S2095268621001002-main.pdf.html": {
        "title": "Preparation and characterization of a specialized lunar regolith simulant for use in lunar oxygen extraction",
        "authors": "International Journal of Mining Science and Technology",
        "year": 2022,
        "doi": "10.1016/j.ijmst.2021.09.003",
        "url": "https://doi.org/10.1016/j.ijmst.2021.09.003",
        "reference_type": "composition"
    },
    "Sibille et al. - Lunar Regolith Simulant Mater.html": {
        "title": "Lunar Regolith Simulant Materials: Recommendations for Standardization, Production, and Usage",
        "authors": "Sibille, L., Carpenter, P., Schlagheck, R., French, R.A.",
        "year": 2006,
        "doi": None,
        "url": "https://ntrs.nasa.gov/citations/20060051776",
        "reference_type": "report"
    },
    "2022 Lunar Simulants Assessment Final.pdf.html": {
        "title": "Lunar Simulants Assessment",
        "authors": "Johns Hopkins Applied Physics Laboratory / LSII",
        "year": 2022,
        "doi": None,
        "url": None,
        "reference_type": "report"
    },
    "1-s2.0-S0094576525001109-main.pdf.html": {
        "title": "Lunar regolith simulant review",  # Will extract better from HTML
        "authors": None,
        "year": 2025,
        "doi": None,
        "url": None,
        "reference_type": "review"
    },
    "LEAG-SIM-SAT2010_LunarRegolithSimulants.html": {
        "title": "LEAG-SIM-SAT 2010: Lunar Regolith Simulants",
        "authors": "Lunar Exploration Analysis Group",
        "year": 2010,
        "doi": None,
        "url": None,
        "reference_type": "report"
    },
    "Engelschiøn et al. - 2020 - EAC-1A A novel large-volume luna.html": {
        "title": "EAC-1A: A novel large-volume lunar regolith simulant",
        "authors": "Engelschiøn, V.S., Eriksson, S.R., Stensvold, A., et al.",
        "year": 2020,
        "doi": "10.1038/s41598-020-62312-4",
        "url": "https://doi.org/10.1038/s41598-020-62312-4",
        "reference_type": "composition"
    },
    "A Review on Geopolymer Technology for Lunar Ba.html": {
        "title": "A Review on Geopolymer Technology for Lunar Base Construction",
        "authors": None,
        "year": None,
        "doi": None,
        "url": None,
        "reference_type": "review"
    },
    "A Review on Geopolymer Technology for Lunar Ba(1).html": {
        "title": "A Review on Geopolymer Technology for Lunar Base Construction",
        "authors": None,
        "year": None,
        "doi": None,
        "url": None,
        "reference_type": "review"
    },
    "Preparation and characterization of a specialized lunar rego.html": {
        "title": "Preparation and characterization of a specialized lunar regolith simulant",
        "authors": None,
        "year": None,
        "doi": "10.1016/j.ijmst.2021.09.003",
        "url": "https://doi.org/10.1016/j.ijmst.2021.09.003",
        "reference_type": "composition"
    },
    "A Comprehensive Review of Lunar-based Manufact.html": {
        "title": "A Comprehensive Review of Lunar-based Manufacturing and Construction",
        "authors": None,
        "year": None,
        "doi": None,
        "url": None,
        "reference_type": "review"
    },
}


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'): self.skip = True
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.skip = False
    def handle_data(self, data):
        if not self.skip: self.text.append(data)
    def get_text(self): return ' '.join(self.text)


def extract_doi_from_html(filepath: Path) -> str | None:
    """Try to extract a DOI from the first 2000 chars of HTML text."""
    try:
        with open(filepath, 'r', errors='replace') as f:
            content = f.read()
        p = TextExtractor()
        p.feed(content)
        text = p.get_text()[:3000]
        dois = re.findall(r'(10\.\d{4,}/[^\s,;)]+)', text)
        return dois[0].rstrip('.') if dois else None
    except:
        return None


def extract_title_from_html(filepath: Path) -> str | None:
    """Try to extract paper title from first paragraph of HTML."""
    try:
        with open(filepath, 'r', errors='replace') as f:
            content = f.read()
        p = TextExtractor()
        p.feed(content)
        text = p.get_text().strip()
        # Take first meaningful line (>10 chars, <200 chars)
        for line in text.split('\n'):
            line = line.strip()
            if 10 < len(line) < 200 and not line.startswith('http'):
                return line
    except:
        pass
    return None


def get_citation(source_file: str) -> dict:
    """Get citation metadata for a source file, from DB or by extraction."""
    # Check manual DB first
    if source_file in CITATION_DB:
        return CITATION_DB[source_file]

    # Try to extract from the HTML
    filepath = SOURCES_DIR / source_file
    if not filepath.exists():
        return {"title": source_file, "reference_type": "general"}

    doi = extract_doi_from_html(filepath)
    title = extract_title_from_html(filepath)

    # Try to parse author/year from filename pattern "Author et al. - YYYY - Title"
    fname = source_file.replace('.html', '').replace('.pdf', '')
    m = re.match(r'^(.+?)\s*-\s*(\d{4})\s*-\s*(.+)$', fname)
    authors = None
    year = None
    if m:
        authors = m.group(1).strip()
        year = int(m.group(2))
        if not title or len(title) < 10:
            title = m.group(3).strip()

    # Clean up Elsevier-style filenames
    if source_file.startswith('1-s2.0-'):
        if title:
            pass  # use extracted title
        else:
            title = fname

    return {
        "title": title or fname,
        "authors": authors,
        "year": year,
        "doi": doi,
        "url": f"https://doi.org/{doi}" if doi else None,
        "reference_type": "general"
    }


def main():
    # Load current data
    with open(DATA_DIR / "references.json") as f:
        refs = json.load(f)
    with open(DATA_DIR / "simulant.json") as f:
        sims = json.load(f)
    with open(INDEX_FILE) as f:
        idx = json.load(f)

    name_lookup = {s['simulant_id']: s['name'] for s in sims}
    ref_sids = {r['simulant_id'] for r in refs}
    all_sids = {s['simulant_id'] for s in sims}
    missing_sids = sorted(all_sids - ref_sids)

    print(f"Simulants without references: {len(missing_sids)}")

    sim_sources = idx.get('simulant_to_sources', {})

    # Find next reference ID
    max_ref = max(int(r['reference_id'][1:]) for r in refs) if refs else 0
    next_ref_id = max_ref + 1

    new_refs = []
    no_source = []

    for sid in missing_sids:
        info = sim_sources.get(sid, {'sources': []})
        sources = info.get('sources', [])
        # Filter out dashboard/database/registry meta-sources
        good = [s for s in sources
                if not any(skip in s['title'] for skip in
                    ['Dashboard', 'Database', 'Registry', 'Dataset', 'Wikipedia'])]

        if not good:
            no_source.append(sid)
            continue

        # Take the best source (most mentions, excluding generic ones)
        best = good[0]
        source_file = best['source']

        # Get citation metadata
        citation = get_citation(source_file)

        ref_entry = {
            "reference_id": f"R{next_ref_id:03d}",
            "simulant_id": sid,
        }

        # Use new-schema format (title, authors, year, doi, url)
        if citation.get('title'):
            ref_entry['title'] = citation['title']
        if citation.get('authors'):
            ref_entry['authors'] = citation['authors']
        if citation.get('year'):
            ref_entry['year'] = citation['year']
        if citation.get('doi'):
            ref_entry['doi'] = citation['doi']
        if citation.get('url'):
            ref_entry['url'] = citation['url']
        if citation.get('reference_type'):
            ref_entry['reference_type'] = citation.get('reference_type', 'general')

        # If no structured fields, at minimum create reference_text
        if not any(k in ref_entry for k in ('title', 'doi', 'url')):
            ref_entry['reference_text'] = f"Source: {source_file}"

        new_refs.append(ref_entry)
        next_ref_id += 1

    print(f"New references created: {len(new_refs)}")
    print(f"Simulants with no matchable source: {len(no_source)}")
    if no_source:
        for sid in no_source:
            print(f"  {sid}: {name_lookup[sid]}")

    # Preview first 5
    print("\n--- Preview (first 5 new refs) ---")
    for ref in new_refs[:5]:
        print(json.dumps(ref, indent=2))

    # Merge and write
    all_refs = refs + new_refs
    with open(DATA_DIR / "references.json", 'w') as f:
        json.dump(all_refs, f, indent=2)
    print(f"\nTotal references: {len(all_refs)} (was {len(refs)})")

    # Coverage report
    covered = {r['simulant_id'] for r in all_refs}
    still_missing = all_sids - covered
    print(f"Simulants now covered: {len(covered)}/{len(all_sids)}")
    if still_missing:
        print(f"Still missing: {sorted(still_missing)}")


if __name__ == '__main__':
    main()

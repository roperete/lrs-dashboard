#!/usr/bin/env python3
"""
Build a reference index mapping LRS/Sources/ files to simulants they mention.

Reads HTML files (text-extracted PDFs/web pages) from LRS/Sources/,
searches for simulant name mentions, and outputs a structured index.
"""

import json
import os
import re
import sys
from pathlib import Path
from html.parser import HTMLParser
from collections import defaultdict

SOURCES_DIR = Path("/home/alvaro/LRS/Sources")
SIMULANT_JSON = Path(__file__).parent.parent / "public" / "data" / "simulant.json"
OUTPUT_FILE = Path(__file__).parent.parent / "documentation" / "source-simulant-index.json"
OUTPUT_MD = Path(__file__).parent.parent / "documentation" / "source-simulant-index.md"


class HTMLTextExtractor(HTMLParser):
    """Strip HTML tags and extract plain text."""
    def __init__(self):
        super().__init__()
        self.result = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip = False

    def handle_data(self, data):
        if not self.skip:
            self.result.append(data)

    def get_text(self):
        return ' '.join(self.result)


def extract_text_from_html(filepath: Path) -> str:
    """Extract plain text from an HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        parser = HTMLTextExtractor()
        parser.feed(content)
        return parser.get_text()
    except Exception as e:
        print(f"  Warning: Could not read {filepath.name}: {e}", file=sys.stderr)
        return ""


def load_metadata(html_path: Path) -> dict:
    """Try to load the companion metadata JSON for an HTML file."""
    # Try patterns: "filename metadata.json", "filename meta.json", "filename.json"
    stem = html_path.stem  # e.g. "paper.pdf" from "paper.pdf.html" or "Paper Title" from "Paper Title.html"

    candidates = [
        html_path.parent / f"{stem} metadata.json",
        html_path.parent / f"{stem} meta.json",
        html_path.parent / f"{stem}.json",
        # For ".pdf.html" files, try without .pdf
        html_path.parent / f"{html_path.stem.replace('.pdf', '')} metadata.json",
    ]

    for candidate in candidates:
        if candidate.exists():
            try:
                with open(candidate, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
    return {}


def build_simulant_patterns(simulants: list) -> list:
    """Build regex patterns for each simulant name."""
    patterns = []
    for sim in simulants:
        name = sim['name']
        sid = sim['simulant_id']

        # Escape for regex, then allow flexible whitespace/hyphens
        escaped = re.escape(name)
        # Allow optional hyphens/spaces between letter-number boundaries
        # e.g. "JSC-1A" should also match "JSC 1A" or "JSC1A"
        pattern = escaped.replace(r'\-', r'[\s\-]?')

        # Word boundary matching — but careful with names ending in digits
        # Use negative lookbehind/ahead for alphanumeric to avoid partial matches
        # e.g. "FJS-1" shouldn't match inside "FJS-1g" unless that's a separate simulant
        regex = re.compile(
            r'(?<![A-Za-z0-9])' + pattern + r'(?![A-Za-z0-9])',
            re.IGNORECASE
        )
        patterns.append((sid, name, regex))

    # Sort by name length descending so longer names match first
    # (e.g. "JSC-1AF" before "JSC-1A" before "JSC-1")
    patterns.sort(key=lambda x: -len(x[1]))
    return patterns


def find_simulant_mentions(text: str, patterns: list) -> dict:
    """Find all simulant mentions in text, return {sid: count}."""
    mentions = {}
    for sid, name, regex in patterns:
        matches = regex.findall(text)
        if matches:
            mentions[sid] = len(matches)
    return mentions


def extract_title_from_filename(filename: str) -> str:
    """Clean up filename to get a readable title."""
    # Remove common suffixes
    title = filename
    for suffix in ['.pdf.html', '.html', '.pdf']:
        if title.endswith(suffix):
            title = title[:-len(suffix)]
    # Remove elsevier-style IDs
    if title.startswith('1-s2.0-'):
        title = title  # keep as-is, metadata will have better title
    return title


def main():
    # Load simulants
    with open(SIMULANT_JSON, 'r') as f:
        simulants = json.load(f)

    print(f"Loaded {len(simulants)} simulants")
    patterns = build_simulant_patterns(simulants)

    # Build name lookup
    name_lookup = {s['simulant_id']: s['name'] for s in simulants}

    # Find all HTML files
    html_files = sorted([
        f for f in SOURCES_DIR.iterdir()
        if f.suffix == '.html' and 'Zone.Identifier' not in f.name
    ])
    print(f"Found {len(html_files)} HTML source files")

    # Process each file
    index = []
    simulant_to_sources = defaultdict(list)

    for i, html_path in enumerate(html_files):
        if (i + 1) % 20 == 0:
            print(f"  Processing {i+1}/{len(html_files)}...")

        # Extract text
        text = extract_text_from_html(html_path)
        if not text or len(text) < 100:
            continue

        # Load metadata
        meta = load_metadata(html_path)
        title = meta.get('title', extract_title_from_filename(html_path.name))

        # Find simulant mentions
        mentions = find_simulant_mentions(text, patterns)

        if not mentions:
            continue

        # Check if there's a matching PDF in LRS/
        pdf_name = html_path.stem  # "paper.pdf" from "paper.pdf.html"
        if not pdf_name.endswith('.pdf'):
            pdf_name = pdf_name + '.pdf'  # web sources won't have .pdf
        pdf_path = Path("/home/alvaro/LRS") / pdf_name
        has_pdf = pdf_path.exists()

        entry = {
            'source_file': html_path.name,
            'title': title.strip(),
            'has_pdf': has_pdf,
            'pdf_filename': pdf_name if has_pdf else None,
            'simulants_mentioned': {
                sid: {
                    'name': name_lookup[sid],
                    'mention_count': count
                }
                for sid, count in sorted(mentions.items(), key=lambda x: -x[1])
            },
            'simulant_count': len(mentions),
            'text_length': len(text),
        }
        index.append(entry)

        for sid in mentions:
            simulant_to_sources[sid].append({
                'source': html_path.name,
                'title': title.strip(),
                'mentions': mentions[sid],
                'has_pdf': has_pdf,
            })

    # Sort by number of simulants mentioned (multi-simulant papers first)
    index.sort(key=lambda x: -x['simulant_count'])

    # Output JSON
    output = {
        'total_sources_processed': len(html_files),
        'sources_with_simulant_mentions': len(index),
        'source_index': index,
        'simulant_to_sources': {
            sid: {
                'name': name_lookup[sid],
                'source_count': len(sources),
                'sources': sorted(sources, key=lambda x: -x['mentions'])
            }
            for sid, sources in sorted(simulant_to_sources.items())
        }
    }

    os.makedirs(OUTPUT_FILE.parent, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nJSON index written to {OUTPUT_FILE}")

    # Output Markdown summary
    with open(OUTPUT_MD, 'w') as f:
        f.write("# Source-Simulant Reference Index\n\n")
        f.write(f"Generated from {len(html_files)} sources in `LRS/Sources/`\n\n")
        f.write(f"**{len(index)}** sources mention at least one simulant.\n\n")

        # Top multi-simulant sources
        f.write("## Multi-Simulant Sources (5+ simulants)\n\n")
        f.write("| Source | Simulants | Title |\n")
        f.write("|--------|-----------|-------|\n")
        for entry in index:
            if entry['simulant_count'] >= 5:
                sims = ', '.join(
                    f"{v['name']}({v['mention_count']})"
                    for sid, v in list(entry['simulants_mentioned'].items())[:8]
                )
                if entry['simulant_count'] > 8:
                    sims += f" +{entry['simulant_count'] - 8} more"
                title = entry['title'][:60]
                f.write(f"| {entry['source_file'][:50]} | {entry['simulant_count']} | {title} |\n")

        # Per-simulant coverage
        f.write("\n## Simulant Coverage\n\n")
        f.write("| Simulant | Sources | Top Source |\n")
        f.write("|----------|---------|------------|\n")
        for sid in sorted(simulant_to_sources.keys()):
            sources = simulant_to_sources[sid]
            name = name_lookup[sid]
            top = sources[0]['title'][:40] if sources else '-'
            f.write(f"| {name} | {len(sources)} | {top} |\n")

        # Simulants with NO sources
        f.write("\n## Simulants with No Source Coverage\n\n")
        uncovered = [s for s in simulants if s['simulant_id'] not in simulant_to_sources]
        if uncovered:
            for s in uncovered:
                f.write(f"- {s['name']} ({s['simulant_id']})\n")
        else:
            f.write("All simulants have at least one source.\n")

    print(f"Markdown summary written to {OUTPUT_MD}")

    # Print summary stats
    print(f"\n--- Summary ---")
    print(f"Sources with simulant mentions: {len(index)}/{len(html_files)}")
    covered = len(simulant_to_sources)
    print(f"Simulants covered: {covered}/{len(simulants)}")
    print(f"Simulants uncovered: {len(simulants) - covered}")

    # Top 10 multi-simulant sources
    print(f"\nTop 10 multi-simulant sources:")
    for entry in index[:10]:
        sims = [v['name'] for v in entry['simulants_mentioned'].values()][:5]
        print(f"  {entry['simulant_count']:3d} sims: {entry['title'][:60]}")


if __name__ == '__main__':
    main()

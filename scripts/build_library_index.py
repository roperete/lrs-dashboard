#!/usr/bin/env python3
"""Index the local PDF library by which simulants each document actually names.

Extracts the text of every PDF under DIRT/Sources (cached as .txt beside a mirror
tree), then searches each text for every simulant name in the database with word
boundaries. Very short names (four characters or fewer) must occur at least twice
and are matched case-sensitively, because "ALS", "EB-2" or "ES-1" also occur as
ordinary tokens.

Outputs documentation/library-simulant-index-<date>.json with
    documents: {relative_path: {title, pages, chars, simulants: {name: mentions}}}
    simulants: {name: [relative_path, ...]}
and prints a coverage summary. Read-only with respect to lrs.sqlite.

Usage:  python3 scripts/build_library_index.py [--library PATH]
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"
DEFAULT_LIBRARY = Path("/Volumes/Extreme SSD/Spring - Forest on the moon/DIRT/Sources")
TEXT_CACHE = DEFAULT_LIBRARY.parent / "Sources_text"


def _html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return html.unescape(re.sub(r"[ \t]+", " ", raw))


def extract_text(doc: Path, cache_root: Path, library: Path) -> str:
    """Text of a PDF (pdftotext) or a saved web page (tags stripped), cached beside a mirror tree."""
    rel = doc.relative_to(library)
    out = cache_root / rel.with_suffix(rel.suffix + ".txt")
    if out.exists() and out.stat().st_mtime >= doc.stat().st_mtime:
        return out.read_text(errors="ignore")
    out.parent.mkdir(parents=True, exist_ok=True)
    if doc.suffix.lower() in (".html", ".htm"):
        txt = _html_to_text(doc.read_text(errors="ignore"))
    else:
        try:
            txt = subprocess.run(["pdftotext", "-layout", str(doc), "-"], capture_output=True, text=True,
                                 errors="ignore", timeout=180).stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            txt = ""
    out.write_text(txt)
    return txt


def is_summary(path: Path) -> bool:
    """NotebookLM narrative summaries live under .../LRS/Sources/. They describe the PDFs
    we already index and are machine-written, so they are not evidence on their own."""
    return "Sources" in path.parts and path.parent.name == "Sources" and path.suffix.lower() in (".html", ".htm", ".json")


def name_pattern(name: str) -> re.Pattern:
    # JSC-1A also appears as "JSC 1A" or "JSC1A"; allow the separator to vary.
    parts = [re.escape(p) for p in re.split(r"[-\s]", name) if p]
    core = r"[-\s]?".join(parts)
    flags = 0 if len(name) <= 4 else re.IGNORECASE
    return re.compile(r"(?<![A-Za-z0-9])" + core + r"(?![A-Za-z0-9])", flags)


SHORT_NAME = 4          # "ALS", "OB-1", "TJ-2" — short enough to occur by accident
WEAK_BELOW = 2          # ...so one mention of such a name is a candidate, not evidence


def scan_text(txt: str, patterns: dict) -> tuple[dict, dict]:
    """Names found in this text, split into confident and weak matches.

    A short name mentioned once is usually a false positive — "ALS" and "OB-1" occur as
    ordinary abbreviations — but it is sometimes the only sentence in the library that
    names a product. Keeping those separately lets a reader judge them, which is their
    job, instead of a threshold discarding them unseen.
    """
    strong, weak = {}, {}
    for name, pat in patterns.items():
        n = len(pat.findall(txt))
        if n == 0:
            continue
        if len(name) <= SHORT_NAME and n < WEAK_BELOW:
            weak[name] = n
        else:
            strong[name] = n
    return strong, weak


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    args = ap.parse_args()
    library = args.library

    con = sqlite3.connect(DB)
    sims = [(r[0], r[1]) for r in con.execute("SELECT simulant_id, name FROM simulants ORDER BY simulant_id")]
    con.close()
    patterns = {name: name_pattern(name) for _, name in sims}

    pdfs = sorted(p for p in library.rglob("*")
                  if p.is_file() and p.suffix.lower() in (".pdf", ".html", ".htm")
                  and "Sources_text" not in p.parts and not is_summary(p))
    n_pdf = sum(1 for p in pdfs if p.suffix.lower() == ".pdf")
    print(f"{len(pdfs)} documents under {library}: {n_pdf} PDFs, {len(pdfs) - n_pdf} saved web pages (NotebookLM summaries excluded)")
    documents = {}
    simulants: dict[str, list[str]] = {name: [] for _, name in sims}
    simulants_weak: dict[str, list[str]] = {name: [] for _, name in sims}
    for i, pdf in enumerate(pdfs, 1):
        txt = extract_text(pdf, TEXT_CACHE, library)
        rel = str(pdf.relative_to(library))
        first = next((ln.strip() for ln in txt.splitlines() if len(ln.strip()) > 12), "")[:140]
        found, weak = scan_text(txt, patterns)
        for name in found:
            simulants[name].append(rel)
        for name in weak:
            simulants_weak[name].append(rel)
        documents[rel] = {"title_line": first, "chars": len(txt), "simulants": found, "simulants_weak": weak}
        if i % 25 == 0:
            print(f"  {i}/{len(pdfs)}")

    out = ROOT / "documentation" / f"library-simulant-index-{date.today().isoformat()}.json"
    out.write_text(json.dumps({"library": str(library), "documents": documents,
                               "simulants": simulants, "simulants_weak": simulants_weak}, indent=1))

    named = {n for n, docs in simulants.items() if docs}
    weak_only = sorted(n for n, docs in simulants_weak.items() if docs and n not in named)
    unnamed = [(sid, n) for sid, n in sims if n not in named and not simulants_weak.get(n)]
    n_weak = sum(len(v) for v in simulants_weak.values())
    print(f"weak matches kept for a reader to judge (one mention of a short name): {n_weak} pair(s)")
    if weak_only:
        print("named ONLY by a weak match: " + ", ".join(weak_only))
    empty = [d for d, v in documents.items() if v["chars"] < 200]
    print(f"\nsimulants named in at least one library document: {len(named)}/{len(sims)}")
    print(f"simulants named in NO library document ({len(unnamed)}): " + ", ".join(f"{n} ({sid})" for sid, n in unnamed))
    print(f"PDFs with no extractable text (scans?): {len(empty)}")
    for d in empty[:10]:
        print("   ", d)
    print(f"\nindex: {out}")


if __name__ == "__main__":
    main()

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
    for i, pdf in enumerate(pdfs, 1):
        txt = extract_text(pdf, TEXT_CACHE, library)
        rel = str(pdf.relative_to(library))
        first = next((ln.strip() for ln in txt.splitlines() if len(ln.strip()) > 12), "")[:140]
        found = {}
        for name, pat in patterns.items():
            n = len(pat.findall(txt))
            if n == 0:
                continue
            if len(name) <= 4 and n < 2:
                continue
            found[name] = n
            simulants[name].append(rel)
        documents[rel] = {"title_line": first, "chars": len(txt), "simulants": found}
        if i % 25 == 0:
            print(f"  {i}/{len(pdfs)}")

    out = ROOT / "documentation" / f"library-simulant-index-{date.today().isoformat()}.json"
    out.write_text(json.dumps({"library": str(library), "documents": documents, "simulants": simulants}, indent=1))

    named = {n for n, docs in simulants.items() if docs}
    unnamed = [(sid, n) for sid, n in sims if n not in named]
    empty = [d for d, v in documents.items() if v["chars"] < 200]
    print(f"\nsimulants named in at least one library document: {len(named)}/{len(sims)}")
    print(f"simulants named in NO library document ({len(unnamed)}): " + ", ".join(f"{n} ({sid})" for sid, n in unnamed))
    print(f"PDFs with no extractable text (scans?): {len(empty)}")
    for d in empty[:10]:
        print("   ", d)
    print(f"\nindex: {out}")


if __name__ == "__main__":
    main()

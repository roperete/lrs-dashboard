#!/usr/bin/env python3
"""Moon values where the reader and the checker agreed on the number but disagreed on form, so the
apply step (scripts/apply_moon.py) left them without a source. Each is written only if its quote
is found, verbatim, in the saved copy of the document; otherwise it is skipped and reported.

  * Apollo 16 latitude: the reader called it "differs"; the checker says the stored -8.97301 is
    the source's 8.9730 S at its own precision. The same NSSDCA sentence states the longitude
    the checker confirmed (15.5002 E), so both coordinates are taken from it.
  * Luna 21 latitude: 25.9994 N is right (checker), but the reader's quote had an added clause;
    the checker supplied the verbatim sentence.

Idempotent; logs to documentation/curation-log-2026-09-25-moon.json.
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT.parent / "Sources"
LOG = ROOT / "documentation" / "curation-log-2026-09-25-moon.json"

ADJUDICATED = [
    ("A16", "lat", -8.9730, "papers/lunar/NSSDCA_Apollo16_LM_1972-031C.html", "NSSDCA Apollo 16 (LM) mission-profile paragraph",
     "in the Descartes highland region just north of the crater Dolland at 8.9730 S latitude, 15.5002 E longitude"),
    ("A16", "lng", 15.5002, "papers/lunar/NSSDCA_Apollo16_LM_1972-031C.html", "NSSDCA Apollo 16 (LM) mission-profile paragraph",
     "in the Descartes highland region just north of the crater Dolland at 8.9730 S latitude, 15.5002 E longitude"),
    ("L21", "lat", 25.9994, "papers/lunar/NSSDCA_Luna21.txt", "Mission Profile section",
     "Landing occurred at 23:35 UT in LeMonnier crater at 25.9994 degrees N, 30.4076 degrees E."),
    ("L21", "lng", 30.4076, "papers/lunar/NSSDCA_Luna21.txt", "Mission Profile section",
     "Landing occurred at 23:35 UT in LeMonnier crater at 25.9994 degrees N, 30.4076 degrees E."),
]

# A document the checker refused only because the reader misquoted its naming sentence: registered
# here if the page itself names the mission, with a sentence found verbatim in it.
REGISTER = {
    "papers/lunar/NSSDCA_Luna21.txt": ("L21", "Luna 21", "Luna 21 — NSSDCA Master Catalog spacecraft page",
                                        "https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=1973-001A"),
}


def _text(path: Path) -> str:
    raw = path.read_text(errors="ignore")
    if path.suffix in (".html", ".htm"):
        raw = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return re.sub(r"\s+", " ", raw)


def curate(con: sqlite3.Connection) -> list[dict]:
    log = []
    for local_path, (sid, name, title, url) in REGISTER.items():
        path = SOURCES / local_path
        if not path.exists() or con.execute("SELECT 1 FROM lunar_documents WHERE local_path=?", (local_path,)).fetchone():
            continue
        m = re.search(rf"[^.]*\b{re.escape(name)}\b[^.]*\.", _text(path))
        if not m:
            log.append({"entity_id": sid, "action": f"not registered: the page does not name {name}", "document": local_path})
            continue
        n = con.execute("SELECT count(*) FROM lunar_documents").fetchone()[0] + 1
        did = f"LD-{n:03d}"
        while con.execute("SELECT 1 FROM lunar_documents WHERE document_id=?", (did,)).fetchone():
            n += 1; did = f"LD-{n:03d}"
        con.execute("INSERT INTO lunar_documents (document_id, title, url, local_path, kind, checked_on) VALUES (?,?,?,?,?,?)",
                    (did, title, url, local_path, "catalogue", "2026-09-25"))
        con.execute("INSERT OR IGNORE INTO lunar_mentions (entity_id, document_id, mention_quote, location) VALUES (?,?,?,?)",
                    (sid, did, m.group(0).strip(), "page text"))
        log.append({"entity_id": sid, "document_id": did, "action": "document registered: it names the mission (sentence found verbatim)"})
    for sid, field, value, local_path, location, quote in ADJUDICATED:
        doc = con.execute("SELECT document_id FROM lunar_documents WHERE local_path=?", (local_path,)).fetchone()
        path = SOURCES / local_path
        if not doc or not path.exists():
            log.append({"entity_id": sid, "field": field, "action": "skipped: document not on record or not on disk", "document": local_path})
            continue
        if re.sub(r"\s+", " ", quote) not in _text(path):
            log.append({"entity_id": sid, "field": field, "action": "skipped: the quote is not in the document", "document": local_path})
            continue
        cur = con.execute(f"SELECT {field} FROM lunar_sites WHERE site_id=?", (sid,)).fetchone()[0]
        have = con.execute("SELECT quote FROM lunar_sources WHERE entity_id=? AND field=? AND document_id=?", (sid, field, doc[0])).fetchone()
        if cur == value and have and have[0] == quote:
            continue
        con.execute(f"UPDATE lunar_sites SET {field}=? WHERE site_id=?", (value, sid))
        con.execute("INSERT OR REPLACE INTO lunar_sources (entity_id, field, document_id, location, quote, value_text) VALUES (?,?,?,?,?,?)",
                    (sid, field, doc[0], location, quote, str(value)))
        log.append({"entity_id": sid, "field": field, "was": cur, "now": value, "document_id": doc[0],
                    "action": "written: number agreed by reader and checker, quote verified in the document"})
    con.commit()
    return log


def main() -> None:
    con = sqlite3.connect(ROOT / "lrs.sqlite")
    log = curate(con)
    if log:
        old = json.loads(LOG.read_text()) if LOG.exists() else []
        LOG.write_text(json.dumps(old + log, indent=2, ensure_ascii=False) + "\n")
    for e in log:
        print(f"  {e['entity_id']} {e.get('field', '')}: {e['action']}")
    print(f"{len(log)} change(s)")


if __name__ == "__main__":
    main()

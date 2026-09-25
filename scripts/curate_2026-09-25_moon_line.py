#!/usr/bin/env python3
"""The Moon line, chosen by the owner on 2026-09-25: papers, the flying agency's own records
(mission and technical reports, the Lunar Sample Compendium, the NSSDCA catalogue, LROC
coordinate tables) and the Lunar Sourcebook stay; web articles, educational pages and
compilations of other people's data go (scripts/source_policy.py, MOON_ACCEPTED_KINDS).

  * LD-036 is the LROC coordinate table (Wagner et al. 2017 values): filed as "web", it is a
    "catalogue".
  * Every lunar_sources row citing a document outside the line is deleted, with that document's
    mentions and record. The value stays in the database, unsourced, so the export hides it
    until a paper or an agency record is found for it.

Run after curate_2026-09-25_no_wiki.py. Idempotent; each removed value is logged with its
quote, for the tracing run, to documentation/curation-log-2026-09-25-moon-line.json.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from source_policy import is_accepted_moon_document

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "documentation" / "curation-log-2026-09-25-moon-line.json"

RECLASSIFY = {"LD-036": ("catalogue", "the LROC 2016 coordinate table, an agency data table, not a web article")}


def _rows(con: sqlite3.Connection, sql: str, args=()) -> list[dict]:
    cur = con.execute(sql, args)
    names = [c[0] for c in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


def curate(con: sqlite3.Connection) -> list[dict]:
    log = []
    for did, (kind, why) in RECLASSIFY.items():
        row = con.execute("SELECT kind FROM lunar_documents WHERE document_id=?", (did,)).fetchone()
        if row and row[0] != kind:
            con.execute("UPDATE lunar_documents SET kind=? WHERE document_id=?", (kind, did))
            log.append({"document_id": did, "was": row[0], "now": kind, "action": f"reclassified: {why}"})
    for d in _rows(con, "SELECT * FROM lunar_documents ORDER BY document_id"):
        if is_accepted_moon_document(d):
            continue
        did = d["document_id"]
        for s in _rows(con, "SELECT * FROM lunar_sources WHERE document_id=?", (did,)):
            log.append({"entity_id": s["entity_id"], "field": s["field"], "document_id": did, "document": d["title"], "kind": d["kind"],
                        "url": d["url"], "value_text": s["value_text"], "location": s["location"], "quote": s["quote"],
                        "action": "source removed: outside the Moon line; value hidden until a paper or agency record states it"})
        con.execute("DELETE FROM lunar_sources WHERE document_id=?", (did,))
        con.execute("DELETE FROM lunar_mentions WHERE document_id=?", (did,))
        con.execute("DELETE FROM lunar_documents WHERE document_id=?", (did,))
        log.append({"document_id": did, "document": d["title"], "kind": d["kind"], "url": d["url"],
                    "action": "document removed: outside the Moon line"})
    con.commit()
    return log


def main() -> None:
    con = sqlite3.connect(ROOT / "lrs.sqlite")
    log = curate(con)
    if log:
        old = json.loads(LOG.read_text()) if LOG.exists() else []
        LOG.write_text(json.dumps(old + log, indent=2, ensure_ascii=False) + "\n")
    print(f"{sum(1 for e in log if 'field' in e)} value source(s) removed, "
          f"{sum(1 for e in log if e['action'].startswith('document removed'))} document(s) removed, "
          f"{sum(1 for e in log if e['action'].startswith('reclassified'))} reclassified")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Wiki pages removed as sources (owner, 2026-09-25: "please dont reference wikipedia. If the
data is not peer-reviewed, dont include it"; "If a wikipedia value can be traced to a paper,
then cite the paper").

  * Moon: every lunar_sources row citing a wiki page (Wikipedia, the-moon.us wiki) is deleted,
    with the page's lunar_mentions and lunar_documents rows. The values stay in lunar_sites and
    lunar_references, unsourced, so the export hides them until a paper is found for them.
  * Simulants: reference rows that are Wikipedia pages are deleted (none carries a value).
  * Mineral sourcing: Wikipedia links are taken out of each mineral's list of European sources.

Each removed value is logged with the wiki's quote, so a reader can trace it to the paper the
wiki relies on. Idempotent; logs to documentation/curation-log-2026-09-25-no-wiki.json.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from source_policy import is_wiki_document, strip_wiki_links

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "documentation" / "curation-log-2026-09-25-no-wiki.json"


def _rows(con: sqlite3.Connection, sql: str, args=()) -> list[dict]:
    cur = con.execute(sql, args)
    names = [c[0] for c in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


def curate(con: sqlite3.Connection) -> list[dict]:
    log = []
    for d in _rows(con, "SELECT * FROM lunar_documents ORDER BY document_id"):
        if not is_wiki_document(d):
            continue
        did = d["document_id"]
        for s in _rows(con, "SELECT * FROM lunar_sources WHERE document_id=?", (did,)):
            log.append({"entity_id": s["entity_id"], "field": s["field"], "document_id": did, "document": d["title"], "url": d["url"],
                        "value_text": s["value_text"], "location": s["location"], "quote": s["quote"],
                        "action": "source removed: wiki page; value hidden until a paper states it"})
        con.execute("DELETE FROM lunar_sources WHERE document_id=?", (did,))
        con.execute("DELETE FROM lunar_mentions WHERE document_id=?", (did,))
        con.execute("DELETE FROM lunar_documents WHERE document_id=?", (did,))
        log.append({"document_id": did, "document": d["title"], "url": d["url"], "action": "document removed: wiki page"})
    ref_tables = [t for t in ("property_sources", "mineral_compositions", "chemical_compositions", "figures_of_merit")
                  if "reference_id" in {c[1] for c in con.execute(f"PRAGMA table_info({t})")}]
    for r in _rows(con, "SELECT * FROM references_ ORDER BY reference_id"):
        if not is_wiki_document(r):
            continue
        used = {t: con.execute(f"SELECT count(*) FROM {t} WHERE reference_id=?", (r["reference_id"],)).fetchone()[0] for t in ref_tables}
        if any(used.values()):
            # a value cites it: leave the row for the owner rather than orphan the citation
            log.append({"reference_id": r["reference_id"], "simulant_id": r["simulant_id"], "url": r["url"], "cited_by": used,
                        "action": "kept for review: values cite this wiki page", "needs_review": True})
            continue
        con.execute("DELETE FROM references_ WHERE reference_id=?", (r["reference_id"],))
        log.append({"reference_id": r["reference_id"], "simulant_id": r["simulant_id"], "url": r["url"],
                    "action": "reference removed: wiki page (no value cited it)"})
    ms_cols = [c[1] for c in con.execute("PRAGMA table_info(mineral_sourcing)")]
    for row in _rows(con, "SELECT * FROM mineral_sourcing ORDER BY mineral_name"):
        for col in ms_cols:
            v = row[col]
            if isinstance(v, str) and (new := strip_wiki_links(v)) != v:
                con.execute(f"UPDATE mineral_sourcing SET {col}=? WHERE mineral_name=?", (new, row["mineral_name"]))
                log.append({"mineral": row["mineral_name"], "column": col, "was": v, "now": new, "action": "wiki links removed"})
    con.commit()
    return log


def main() -> None:
    con = sqlite3.connect(ROOT / "lrs.sqlite")
    log = curate(con)
    if log:
        old = json.loads(LOG.read_text()) if LOG.exists() else []
        LOG.write_text(json.dumps(old + log, indent=2, ensure_ascii=False) + "\n")
    values = [e for e in log if "field" in e]
    print(f"{len(values)} value source(s) removed, {sum(1 for e in log if e['action'].startswith('document removed'))} wiki document(s), "
          f"{sum(1 for e in log if e['action'].startswith('reference removed'))} simulant reference(s), "
          f"{sum(1 for e in log if e['action'] == 'wiki links removed')} mineral-sourcing field(s); "
          f"{sum(1 for e in log if e.get('needs_review'))} for review")


if __name__ == "__main__":
    main()

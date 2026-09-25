#!/usr/bin/env python3
"""Moon values that the checker confirmed but that would mislead on the page, removed under
"empty rather than wrong". Removing the source is enough: the export hides an unsourced value,
and the database keeps the number.

  * 60501 MnO 0.07 wt%: the document gives several MnO analyses (0.072, 0.08, 0.07, 0.067,
    0.076) and the reader read 0.07 as a coarse-fraction one. It would be the only oxide shown
    for the sample, presented as its bulk composition.

Run after scripts/apply_moon.py --write and curate_2026-09-25_moon_adjudicated.py.
Idempotent; logs to documentation/curation-log-2026-09-25-moon.json.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "documentation" / "curation-log-2026-09-25-moon.json"

OMIT = {
    ("60501", "oxide:MnO"): "one of five MnO analyses in the document, read as a coarse fraction; "
                            "alone it would stand for the sample's bulk chemistry",
}


def curate(con: sqlite3.Connection) -> list[dict]:
    log = []
    for (eid, field), why in OMIT.items():
        row = con.execute("SELECT document_id, value_text FROM lunar_sources WHERE entity_id=? AND field=?", (eid, field)).fetchone()
        if not row:
            continue
        con.execute("DELETE FROM lunar_sources WHERE entity_id=? AND field=?", (eid, field))
        log.append({"entity_id": eid, "field": field, "document_id": row[0], "value_text": row[1],
                    "action": f"source removed, value hidden: {why}"})
    con.commit()
    return log


def main() -> None:
    con = sqlite3.connect(ROOT / "lrs.sqlite")
    log = curate(con)
    if log:
        old = json.loads(LOG.read_text()) if LOG.exists() else []
        LOG.write_text(json.dumps(old + log, indent=2, ensure_ascii=False) + "\n")
    for e in log:
        print(f"  {e['entity_id']} {e['field']}: {e['action']}")
    print(f"{len(log)} change(s)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Reference metadata corrections from the batch-2 verifiers (2026-09-22).

The extractors' new reference rows carried three errors the independent checkers caught
by reading the title pages, and two documents were typed as if they were primary
sources when they reproduce another paper's numbers:

  * Slabic et al. 2024, Lunar Regolith Simulant User's Guide Rev. A: the extractor's author
    list included names not on the title page. Set to "Slabic, A. et al." rather than
    guess a list.
  * Rickman et al. 2024, Characterization of NUW-LHT-5M: the report number is
    NASA/TP-20240007991, not TM.
  * CAS-1 (S007): the composition was read from the CUMT-1 paper's comparison table, which
    reproduces Zheng et al. 2009 (not openable). That row is a reproduction, not the
    primary source: type it `review` so the status refresh labels it as such.
  * CLDS-i (S009): read from the Planetary Simulant Database page, which transcribes
    Tang et al. 2017 (not in the library). Type it `general` for the same reason.

Run:  python3 scripts/curate_2026-09-22_batch2.py [--db lrs.sqlite]
Idempotent; logs to documentation/curation-log-2026-09-22-batch2.json.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"
LOG = ROOT / "documentation" / "curation-log-2026-09-22-batch2.json"


def curate(db: Path) -> list[dict]:
    con = sqlite3.connect(db)
    log: list[dict] = []

    def upd(sql: str, params: tuple, why: str) -> None:
        cur = con.execute(sql, params)
        if cur.rowcount:
            log.append({"rows": cur.rowcount, "sql": sql, "params": list(params), "why": why})

    upd("UPDATE references_ SET authors='Slabic, A. et al.' WHERE title LIKE 'Lunar Regolith Simulant User%s Guide%Revision A%' AND authors IS NOT NULL AND authors!='Slabic, A. et al.'",
        (), "verifier (S047): extractor's author list does not match the title page")
    upd("UPDATE references_ SET title=REPLACE(title,'NASA/TM-20240007991','NASA/TP-20240007991'), reference_text=REPLACE(reference_text,'NASA/TM-20240007991','NASA/TP-20240007991') WHERE title LIKE '%NASA/TM-20240007991%'",
        (), "verifier (S047): the NUW-LHT-5M characterization is a Technical Publication")
    upd("UPDATE references_ SET reference_type='review' WHERE simulant_id='S007' AND title LIKE 'Preparation and characterization of a specialized lunar regolith simulant%' AND reference_type!='review'",
        (), "extractor and verifier (S007): CAS-1 values in the CUMT-1 paper reproduce Zheng et al. 2009")
    upd("UPDATE references_ SET reference_type='general' WHERE simulant_id='S009' AND title LIKE 'Planetary Simulant Database: CLDS-i%' AND reference_type!='general'",
        (), "extractor (S009): simulantdb transcribes Tang et al. 2017, which is not in the library")
    con.commit()
    con.close()
    return log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DB)
    args = ap.parse_args()
    log = curate(args.db)
    for e in log:
        print(f"{e['rows']} row(s): {e['why']}")
    if log:
        prev = json.loads(LOG.read_text()) if LOG.exists() else []
        LOG.write_text(json.dumps(prev + log, indent=1))
    print(f"{len(log)} change(s)")


if __name__ == "__main__":
    main()

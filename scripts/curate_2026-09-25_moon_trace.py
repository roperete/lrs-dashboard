#!/usr/bin/env python3
"""After the Moon tracing run (documentation/moon-trace-findings-2026-09-25.json) is applied
with scripts/apply_moon.py --write, three values need what the apply step does not do:

  * Chang'e 6 date: the paper states "06:24 on June 2, 2024 (Beijing time)"; every other date on
    the page is UTC, so it is stored as June 1, 2024 (22:24 UTC, Beijing is UTC+8). The source
    row keeps the paper's own sentence.
  * Descriptions with a claim no document confirms keep only their confirmed claims (the apply
    step sources a description only when every claim is): Surveyor 1 loses "Conducted surface
    mechanics experiments", which its mission report contradicts ("Surveyor I did not carry any
    instrumentation for scientific experiments"); Chandrayaan-3 loses "First Indian lunar
    landing", which no allowed document the reader opened states.

Each kept claim is cited to the document the checker confirmed for it. Idempotent; logs to
documentation/curation-log-2026-09-25-moon-trace.json.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FINDINGS = ROOT / "documentation" / "moon-trace-findings-2026-09-25.json"
LOG = ROOT / "documentation" / "curation-log-2026-09-25-moon-trace.json"

DATES = {"CE6": ("June 1, 2024", "the paper gives 06:24 on June 2, 2024, Beijing time (UTC+8): 22:24 UTC on June 1")}
DESCRIPTIONS = {
    "S1": "First US soft landing on the Moon.",
    "CH3": "Pragyan rover explored near the south pole.",
}


def confirmed_claims(findings: dict, eid: str) -> list[tuple[dict, dict]]:
    """(claim, its reference) for each description claim of `eid` the checker confirmed."""
    out = []
    for g in findings["results"]:
        reading = {e["id"]: e for e in g["reading"]["entities"]}.get(eid)
        if not reading:
            continue
        check = {e["id"]: e for e in g["check"]["entities"]}[eid]
        ok = {c["field"] for c in check["value_checks"] if c["verdict"] == "CONFIRMED"}
        refs = {r["temp_id"]: r for r in reading["references"]}
        for v in reading["values"]:
            if v["field"].startswith("description:") and v["field"] in ok and v["status"] == "supported" and v.get("reference_id") in refs:
                out.append((v, refs[v["reference_id"]]))
    return out


def curate(con: sqlite3.Connection, findings: dict) -> list[dict]:
    log = []
    for sid, (date, why) in DATES.items():
        src = con.execute("SELECT 1 FROM lunar_sources WHERE entity_id=? AND field='date'", (sid,)).fetchone()
        cur = con.execute("SELECT date FROM lunar_sites WHERE site_id=?", (sid,)).fetchone()
        if src and cur and cur[0] != date:
            con.execute("UPDATE lunar_sites SET date=? WHERE site_id=?", (date, sid))
            log.append({"entity_id": sid, "field": "date", "was": cur[0], "now": date, "action": f"stated in UTC: {why}"})
    for sid, text in DESCRIPTIONS.items():
        claims = confirmed_claims(findings, sid)
        if not claims:
            log.append({"entity_id": sid, "field": "description", "action": "skipped: no confirmed claim in the findings"})
            continue
        v, ref = claims[0]
        doc = con.execute("SELECT document_id FROM lunar_documents WHERE local_path=?", (ref["local_path"],)).fetchone()
        if not doc:
            log.append({"entity_id": sid, "field": "description", "action": "skipped: the claim's document is not on record"})
            continue
        cur = con.execute("SELECT description FROM lunar_sites WHERE site_id=?", (sid,)).fetchone()[0]
        have = con.execute("SELECT document_id FROM lunar_sources WHERE entity_id=? AND field='description'", (sid,)).fetchone()
        if cur == text and have:
            continue
        con.execute("UPDATE lunar_sites SET description=? WHERE site_id=?", (text, sid))
        con.execute("INSERT OR REPLACE INTO lunar_sources (entity_id, field, document_id, location, quote, value_text) VALUES (?,?,?,?,?,?)",
                    (sid, "description", doc[0], v.get("location"), v.get("quote") or "", None))
        log.append({"entity_id": sid, "field": "description", "was": cur, "now": text, "document_id": doc[0],
                    "action": "kept only the confirmed claim, cited to its document"})
    con.commit()
    return log


def main() -> None:
    con = sqlite3.connect(ROOT / "lrs.sqlite")
    log = curate(con, json.loads(FINDINGS.read_text()))
    if log:
        old = json.loads(LOG.read_text()) if LOG.exists() else []
        LOG.write_text(json.dumps(old + log, indent=2, ensure_ascii=False) + "\n")
    for e in log:
        print(f"  {e['entity_id']} {e['field']}: {e['action']}")
    print(f"{len(log)} change(s)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""The owner's decisions of 2026-09-24 on the value audit's judgement calls.

Alvaro: "I'd rather have an empty value than a wrong value."

  * NAO-1 cohesion 95.3 kPa — omitted. The paper states it, then calls it an artefact of the
    dense (1.93 g/cm3) specimen and assumes the cohesion is about 0.
  * FEFU-1 mean particle size 0.8 um — omitted. It is the powder size in one sintering study
    (a review's Table 4), not necessarily the simulant as supplied.
  * NEU-1B lunar analogue — "whatever the source says, provided it's real": its own primary
    paper, Li et al. 2019 (RN-S124-1, confirmed by the checker), calls NEU-1b the variant
    "with high titanium content" (TiO2 6.5%); Patzwald et al. 2025 calls it "the high-Ti
    variant" of the low-Ti mare simulant NEU-1a. Set to "High-Ti Mare", cited.

Idempotent; logs to documentation/curation-log-2026-09-24-owner.json.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "documentation" / "curation-log-2026-09-24-owner.json"

OMIT = {
    ("S045", "cohesion"): "the paper calls 95.3 kPa an artefact of the dense specimen and assumes ~0",
    ("S157", "particle_size_mean_um"): "powder size in one sintering study, not the simulant as supplied",
}
SET = {
    ("S124", "lunar_sample_reference"): ("High-Ti Mare", "RN-S124-1", "Abstract",
                                          "Northeastern University-1b (NEU-1b) with high titanium content ... "
                                          "TiO2 contents in NEU-1a and NEU-1b lunar soil simulants are 2.87% and 6.5% by mass, respectively."),
}


def curate(con: sqlite3.Connection) -> list[dict]:
    log = []
    for (sid, field), why in OMIT.items():
        v = con.execute(f"SELECT {field} FROM simulants WHERE simulant_id=?", (sid,)).fetchone()
        if v and v[0] not in (None, ""):
            src = con.execute("SELECT reference_id, quote FROM property_sources WHERE simulant_id=? AND field=?", (sid, field)).fetchone()
            con.execute(f"UPDATE simulants SET {field}=NULL WHERE simulant_id=?", (sid,))
            con.execute("DELETE FROM property_sources WHERE simulant_id=? AND field=?", (sid, field))
            log.append({"simulant_id": sid, "field": field, "was": v[0], "source": list(src) if src else None,
                        "why": why, "action": "omitted at the owner's decision"})
    for (sid, field), (value, rid, location, quote) in SET.items():
        assert con.execute("SELECT names_simulant FROM references_ WHERE reference_id=? AND simulant_id=?", (rid, sid)).fetchone() == (1,), rid
        was = con.execute(f"SELECT {field} FROM simulants WHERE simulant_id=?", (sid,)).fetchone()[0]
        have = con.execute("SELECT reference_id, location, quote FROM property_sources WHERE simulant_id=? AND field=?", (sid, field)).fetchone()
        if was == value and have and tuple(have) == (rid, location, quote):
            continue
        con.execute(f"UPDATE simulants SET {field}=? WHERE simulant_id=?", (value, sid))
        con.execute("INSERT OR REPLACE INTO property_sources (simulant_id, field, reference_id, location, quote) VALUES (?,?,?,?,?)",
                    (sid, field, rid, location, quote))
        log.append({"simulant_id": sid, "field": field, "was": was, "now": value, "reference_id": rid,
                    "action": "set to what its source states, at the owner's decision"})
    con.commit()
    return log


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "lrs.sqlite")
    log = curate(con)
    con.close()
    for e in log:
        print(f"{e['simulant_id']} {e['field']}: {e['action']} ({e.get('was')!r}{' -> ' + repr(e['now']) if 'now' in e else ''})")
    if log:
        prev = json.loads(LOG.read_text()) if LOG.exists() else []
        LOG.write_text(json.dumps(prev + log, indent=1, ensure_ascii=False))
    print(f"{len(log)} change(s)")

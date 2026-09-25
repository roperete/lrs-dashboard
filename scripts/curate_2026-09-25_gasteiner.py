#!/usr/bin/env python3
"""Values Gasteiner et al. (2026) list for simulants, checked against the papers they name
(documentation/gasteiner-lead-findings-2026-09-25.json; their dataset was a finding aid only,
nothing is cited to it). Run after scripts/apply_provenance.py has applied the same findings.

  * blanked: stored values the papers do not state, none of them shown (none had a source):
    a density copied from another simulant, values of another simulant, midpoints of ranges,
    and ends of ranges;
  * corrected: EAC-1A's bulk density, 1.95 g/cm3 (the compacted cohesion-test specimen) to the
    1.45 g/cm3 the paper gives for the material, cited to it.

Only a value without a source row is blanked: a sourced value is left and reported. Idempotent;
logs to documentation/curation-log-2026-09-25-gasteiner.json.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "documentation" / "curation-log-2026-09-25-gasteiner.json"

BLANK = {
    ("S038", "bulk_density"): "1.065 g/cm3 is TLS-01's density (Siriluck, Chancharoen & Seehanam 2021, p. 2), copied onto LSS-ISAC-1",
    ("S027", "bulk_density"): "1.065 g/cm3 is TLS-01's density; McKay et al. 1994, JSC-1's paper, does not state it",
    ("S012", "bulk_density"): "the CUG-1A abstract gives a range, 1.45-1.90 g/cm3; 1.45 is only its lower end",
    ("S012", "friction_angle"): "the abstract gives 20-21 deg ('approximately 20'); 21.0 is only the upper end",
    ("S012", "cohesion"): "the abstract gives 5-21 kPa; 5.0 is only the lower end",
    ("S120", "friction_angle"): "38.0 deg is the midpoint of the 35.7-40.3 deg the paper gives; it states no single value",
    ("S120", "cohesion"): "6.75 kPa is the midpoint of the 0-13.5 kPa the paper gives",
    ("S058", "friction_angle"): "36 deg is OPRH2N's (the JHU-APL 2022 assessment tested only OPRH2N); the NASA user's guide labels it OPRH3N",
    ("S058", "cohesion"): "12 kPa is OPRH2N's, as for the friction angle",
}

CORRECT = {
    ("S018", "bulk_density"): {
        "value": 1.45, "reference_id": "R018",
        "location": "p. 3, Results, Density (bulk density 'at optimal packing', measured by weighing a specific volume)",
        "quote": "The bulk density (density of material at optimal packing) of EAC-1A, JSC-1A, JSC-2A, DNA and NU-LHT-3M "
                 "was measured, resulting in 1.45, 1.56, 1.44, 1.27 and 1.54 g/cm3 respectively.",
        "why": "1.95 g/cm3 was the compacted cohesion-test specimen ('The cohesion of EAC-1A at a density of 1.95 g/cm3 was "
               "estimated to be 0.38 kPa'); the paper gives 1.45 g/cm3 for the material",
    },
}


def curate(con: sqlite3.Connection) -> list[dict]:
    log = []
    sourced = lambda sid, f: con.execute("SELECT 1 FROM property_sources WHERE simulant_id=? AND field=?", (sid, f)).fetchone()
    for (sid, f), why in BLANK.items():
        cur = con.execute(f"SELECT {f} FROM simulants WHERE simulant_id=?", (sid,)).fetchone()
        if not cur or cur[0] in (None, ""):
            continue
        if sourced(sid, f):
            log.append({"simulant_id": sid, "field": f, "value": cur[0], "action": "kept: the value has a source row", "needs_review": True})
            continue
        con.execute(f"UPDATE simulants SET {f}=NULL WHERE simulant_id=?", (sid,))
        log.append({"simulant_id": sid, "field": f, "was": cur[0], "now": None, "action": f"blanked: {why}"})
    for (sid, f), c in CORRECT.items():
        cur = con.execute(f"SELECT {f} FROM simulants WHERE simulant_id=?", (sid,)).fetchone()[0]
        have = con.execute("SELECT reference_id, quote FROM property_sources WHERE simulant_id=? AND field=?", (sid, f)).fetchone()
        # the simulants columns are TEXT: compare as numbers
        same = cur not in (None, "") and abs(float(cur) - c["value"]) < 1e-9
        if same and have == (c["reference_id"], c["quote"]):
            continue
        if not con.execute("SELECT 1 FROM references_ WHERE reference_id=? AND simulant_id=?", (c["reference_id"], sid)).fetchone():
            log.append({"simulant_id": sid, "field": f, "action": "skipped: the reference is not on file for this simulant", "needs_review": True})
            continue
        con.execute(f"UPDATE simulants SET {f}=? WHERE simulant_id=?", (c["value"], sid))
        con.execute("DELETE FROM property_sources WHERE simulant_id=? AND field=?", (sid, f))
        con.execute("INSERT INTO property_sources (simulant_id, field, reference_id, location, quote) VALUES (?,?,?,?,?)",
                    (sid, f, c["reference_id"], c["location"], c["quote"]))
        log.append({"simulant_id": sid, "field": f, "was": cur, "now": c["value"], "reference_id": c["reference_id"],
                    "action": f"corrected to the source: {c['why']}"})
    con.commit()
    return log


def main() -> None:
    con = sqlite3.connect(ROOT / "lrs.sqlite")
    log = curate(con)
    if log:
        old = json.loads(LOG.read_text()) if LOG.exists() else []
        LOG.write_text(json.dumps(old + log, indent=2, ensure_ascii=False) + "\n")
    for e in log:
        print(f"  {e['simulant_id']} {e['field']}: {e['action'][:110]}")
    print(f"{len(log)} change(s)")


if __name__ == "__main__":
    main()

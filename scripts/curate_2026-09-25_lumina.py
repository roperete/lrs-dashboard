#!/usr/bin/env python3
"""Corrections to the three Lumina products added from Zémeny et al. 2024 (RN-S159-1 .. RN-S161-1).

  * Particle morphology is restated in the paper's own numbers. The reader's wording carried
    method labels ("2D", "3D", "mm3") whose digits the paper does not state as values.
  * Lunar2000's mean particle size of 2.4 mm is omitted, and so are the size-dependent µCT
    figures (average volume 73 mm3, volume-to-surface ratio ca. 14). The same paper gives the
    product as 0–2000 µm (Table 1), and a 73 mm3 grain is about 5 mm across, so the µCT
    figures cannot describe the product as supplied. Owner's rule: "I'd rather have an empty
    value than a wrong value." The unitless shape figures (angularity, aspect ratio,
    sphericity) contradict nothing and stay.
  * Lunar250 gains a second reference that names it, found by the Lumina web search of
    2026-09-25 and confirmed by the checker: Knapmeyer-Endrun et al., EGU General Assembly 2026
    abstract EGU26-19748 ("a smaller dust lab filled to about 60 cm depth with the Lumina250
    highland simulant"). It states no value the database stores.

Idempotent; logs to documentation/curation-log-2026-09-25-lumina.json.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "documentation" / "curation-log-2026-09-25-lumina.json"

OMIT = {
    ("S161", "particle_size_mean_um"): "2.4 mm exceeds the 0–2000 µm range the same paper gives for the product (Table 1)",
}
RESTATE = {
    ("S159", "particle_morphology"): ("average sphericity 0.46 (VisiSize image analysis)", None),
    ("S160", "particle_morphology"): ("average sphericity 0.47 (VisiSize image analysis)", None),
    ("S161", "particle_morphology"): (
        "average angularity 0.41; average aspect ratio 2.14; average sphericity 0.55 (X-ray µCT, NGI)",
        "Three-dimensional particle shape analysis was carried out by NGI on the Lumina 2000 sample. ... "
        "the average angularity is 0.41. The average aspect ratio is 2.14, and the average sphericity is 0.55."),
}


ADD_REFERENCES = [
    {"reference_id": "RN-S160-2", "simulant_id": "S160", "reference_type": "abstract",
     "title": "First seismic in-situ characterization of regolith simulants in LUNA (EGU General Assembly 2026, EGU26-19748)",
     "authors": "Knapmeyer-Endrun, B., et al.", "year": 2026, "doi": "10.5194/egusphere-egu26-19748",
     "url": "https://meetingorganizer.copernicus.org/EGU26/EGU26-19748.html",
     "local_path": "datasheets/Lumina/EGU26-19748_Knapmeyer-Endrun_abstract.html",
     "mention_quote": "a smaller dust lab filled to about 60 cm depth with the Lumina250 highland simulant"},
]


def curate(con: sqlite3.Connection) -> list[dict]:
    log = []
    for ref in ADD_REFERENCES:
        if con.execute("SELECT 1 FROM references_ WHERE reference_id=?", (ref["reference_id"],)).fetchone():
            continue
        con.execute("INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type, title, authors, year, doi, url, "
                    "names_simulant, mention_quote, local_path, checked_on) VALUES (?,?,?,?,?,?,?,?,?,1,?,?,?)",
                    (ref["reference_id"], ref["simulant_id"], ref["title"], ref["reference_type"], ref["title"], ref["authors"],
                     ref["year"], ref["doi"], ref["url"], ref["mention_quote"], ref["local_path"], "2026-09-25"))
        log.append({"simulant_id": ref["simulant_id"], "reference_id": ref["reference_id"], "action": "reference added: names the product"})
    for (sid, field), why in OMIT.items():
        v = con.execute(f"SELECT {field} FROM simulants WHERE simulant_id=?", (sid,)).fetchone()
        if v and v[0] not in (None, ""):
            src = con.execute("SELECT reference_id, quote FROM property_sources WHERE simulant_id=? AND field=?", (sid, field)).fetchone()
            con.execute(f"UPDATE simulants SET {field}=NULL WHERE simulant_id=?", (sid,))
            con.execute("DELETE FROM property_sources WHERE simulant_id=? AND field=?", (sid, field))
            log.append({"simulant_id": sid, "field": field, "was": v[0], "source": list(src) if src else None,
                        "why": why, "action": "omitted: the documents contradict it"})
    for (sid, field), (value, quote) in RESTATE.items():
        was = con.execute(f"SELECT {field} FROM simulants WHERE simulant_id=?", (sid,)).fetchone()[0]
        have = con.execute("SELECT quote FROM property_sources WHERE simulant_id=? AND field=?", (sid, field)).fetchone()
        assert have, (sid, field)
        if was == value and (quote is None or have[0] == quote):
            continue
        con.execute(f"UPDATE simulants SET {field}=? WHERE simulant_id=?", (value, sid))
        if quote is not None:
            con.execute("UPDATE property_sources SET quote=? WHERE simulant_id=? AND field=?", (quote, sid, field))
        log.append({"simulant_id": sid, "field": field, "was": was, "now": value,
                    "quote_was": have[0] if quote is not None else None,
                    "action": "restated in its quote's own numbers"})
    con.commit()
    return log


def main() -> None:
    con = sqlite3.connect(ROOT / "lrs.sqlite")
    log = curate(con)
    if log:
        old = json.loads(LOG.read_text()) if LOG.exists() else []
        LOG.write_text(json.dumps(old + log, indent=2, ensure_ascii=False) + "\n")
    for e in log:
        print(f"  {e['simulant_id']} {e.get('field') or e.get('reference_id')}: {e['action']}")
    print(f"{len(log)} change(s)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Map sites and types corrected to their sources (owner, 2026-09-25: "please correct to their
source"), from the map-site run (reader + adversarial checker, workflow map-site-sources).

  * GreenSpar (S025) was placed in Anchorage, Alaska. Gruener et al. 2020 (RN-S025-1, checker
    CONFIRMED): "Hudson Resources, Inc. is mining surface exposed anorthosite with their White
    Mountain Anorthosite Project, located approximately 85 km southwest of Kangerlussuaq,
    Greenland." Coordinates from the EGDI mines layer, record CRM25.MFO223 "Qaqortorssuaq,
    Najaat-White Mountain" (66.544 N, 52.3085 W), checked live by the checker.
  * FEFU-1 (S157) was placed on central Moscow with the site name "Russia", which no document
    supports. The checker found no verbatim statement of where FEFU-1 is made (the paper is
    paywalled; "Vladivostok" is an author's address), while the paper does state where its
    material comes from: andesite-basalts from the Gorely (Kamchatka) and Baranovskiy
    (Primorsky Krai) volcanoes. "Empty rather than wrong": the Moscow point is removed and the
    place left for the owner to decide.
  * Lunar90, Lunar250, Lunar2000 (S159-S161) had no type. Zémeny et al. 2024 Table 1 caption,
    checker CONFIRMED: "The three lunar highland simulants purchased from Lumina Sustainable
    Materials Ltd." -> Highlands. Their country and map site stay empty: the paper mentions a
    visit to the Greenland mine but never says the products come from it (checker UNCERTAIN).

Idempotent; logs to documentation/curation-log-2026-09-25-sites.json.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "documentation" / "curation-log-2026-09-25-sites.json"

GREENSPAR = {
    "site_id": "X025", "simulant_id": "S025",
    "site_name": "White Mountain Anorthosite Project (Qaqortorsuaq), Greenland", "site_type": "Mine",
    "country_code": "Greenland", "lat": 66.544, "lon": -52.3085,
    "reference_id": "RN-S025-1",
    "location": "p. 1, Greenland Anorthosite; coordinates: EGDI mines layer, record CRM25.MFO223 'Qaqortorssuaq, Najaat-White Mountain'",
    "quote": "Hudson Resources, Inc. is mining surface exposed anorthosite with their White Mountain Anorthosite Project, "
             "located approximately 85 km southwest of Kangerlussuaq, Greenland.",
}
LUMINA_TYPE = {
    sid: (f"RN-{sid}-1", "Table 1 caption, p. 3",
          "The three lunar highland simulants purchased from Lumina Sustainable Materials Ltd. and the lunar mare simulant EAC-1 "
          "received from the European Astronaut Centre (EAC).")
    for sid in ("S159", "S160", "S161")
}


def curate(con: sqlite3.Connection) -> list[dict]:
    log = []
    g = GREENSPAR
    cur = con.execute("SELECT site_name, site_type, country_code, lat, lon FROM sites WHERE site_id=?", (g["site_id"],)).fetchone()
    new = (g["site_name"], g["site_type"], g["country_code"], g["lat"], g["lon"])
    if cur and tuple(cur) != new:
        con.execute("UPDATE sites SET site_name=?, site_type=?, country_code=?, lat=?, lon=? WHERE site_id=?", (*new, g["site_id"]))
        log.append({"simulant_id": g["simulant_id"], "field": "site", "was": list(cur), "now": list(new), "action": "moved to the place its source states"})
    con.execute("INSERT OR REPLACE INTO property_sources (simulant_id, field, reference_id, location, quote) VALUES (?,?,?,?,?)",
                (g["simulant_id"], "site", g["reference_id"], g["location"], g["quote"]))

    cur = con.execute("SELECT site_id, site_name, lat, lon FROM sites WHERE simulant_id='S157'").fetchall()
    for row in cur:
        con.execute("DELETE FROM sites WHERE site_id=?", (row[0],))
        log.append({"simulant_id": "S157", "field": "site", "was": list(row), "now": None,
                    "action": "removed: no document places FEFU-1 there (the Moscow point was a placeholder)",
                    "documented_places": ["material: Gorely volcano, Kamchatka Krai", "material: Baranovskiy volcano, Primorsky Krai",
                                          "authors' address: Far Eastern Federal University, Russky Island, Vladivostok"]})

    for sid, (rid, location, quote) in LUMINA_TYPE.items():
        cur = con.execute("SELECT type FROM simulants WHERE simulant_id=?", (sid,)).fetchone()
        if cur and cur[0] != "Highlands":
            con.execute("UPDATE simulants SET type='Highlands' WHERE simulant_id=?", (sid,))
            log.append({"simulant_id": sid, "field": "type", "was": cur[0], "now": "Highlands", "reference_id": rid, "action": "set from its source"})
        con.execute("INSERT OR REPLACE INTO property_sources (simulant_id, field, reference_id, location, quote) VALUES (?,?,?,?,?)",
                    (sid, "type", rid, location, quote))
    con.commit()
    return log


def main() -> None:
    con = sqlite3.connect(ROOT / "lrs.sqlite")
    log = curate(con)
    if log:
        old = json.loads(LOG.read_text()) if LOG.exists() else []
        LOG.write_text(json.dumps(old + log, indent=2, ensure_ascii=False) + "\n")
    for e in log:
        print(f"  {e['simulant_id']} {e['field']}: {e['action']}")
    print(f"{len(log)} change(s)")


if __name__ == "__main__":
    main()

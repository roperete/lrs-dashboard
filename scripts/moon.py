#!/usr/bin/env python3
"""The Moon section of data.json: landing sites and lunar reference samples, each value
exported only when a document stating it is on record in `lunar_sources`.

Identity fields are not gated: a site's id, name, mission and programme, and a sample's
number and mission (the number fixes the mission). A site whose coordinates are not both
sourced is left out, since it cannot be placed on the map. Hidden values stay in the
database and are listed so the owner can see what left the page.
"""

from __future__ import annotations

import json
import sqlite3

SITE_FIELDS = ("date", "lat", "lng", "samples_returned", "description")
GEOTECHNICAL = ("bulk_density", "friction_angle", "cohesion", "bearing_capacity")
SAMPLE_FIELDS = ("landing_site", "coordinates", "type", "sample_description")
PRIVATE_DOCUMENT_COLUMNS = ("local_path", "checked_on")


def _rows(con: sqlite3.Connection, sql: str) -> list[dict]:
    cur = con.execute(sql)
    names = [c[0] for c in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


def export_moon(con: sqlite3.Connection) -> dict:
    sources = _rows(con, "SELECT entity_id, field, document_id, location, quote, value_text FROM lunar_sources ORDER BY entity_id, field, document_id")
    sourced = {(s["entity_id"], s["field"]) for s in sources}
    hidden: list[dict] = []

    def keep(entity: str, field: str, value):
        if value in (None, "", {}):
            return None
        if (entity, field) in sourced:
            return value
        hidden.append({"entity_id": entity, "field": field, "value": value})
        return None

    sites = []
    for s in _rows(con, "SELECT * FROM lunar_sites ORDER BY site_id"):
        sid = s["site_id"]
        out = {"id": sid, "name": s["name"], "mission": s["mission"], "type": s["programme"]}
        out.update({f: keep(sid, f, s[f]) for f in SITE_FIELDS})
        out["geotechnical"] = {f: v for f in GEOTECHNICAL if (v := keep(sid, f, s[f])) is not None}
        if out["lat"] is None or out["lng"] is None:
            continue
        sites.append(out)

    samples = []
    for r in _rows(con, "SELECT * FROM lunar_references ORDER BY sample_id"):
        sid = r["sample_id"]
        out = {"sample_id": sid, "mission": r["mission"]}
        for f in SAMPLE_FIELDS:
            v = json.loads(r[f]) if f == "coordinates" and r[f] else r[f]
            out[f] = keep(sid, f, v)
        for col, kind in (("chemical_composition", "oxide"), ("mineral_composition", "mineral")):
            comp = json.loads(r[col]) if r[col] else {}
            kept = {k: v for k, v in comp.items() if keep(sid, f"{kind}:{k}", v) is not None}
            out[col] = kept or None
        samples.append(out)

    cited = {s["document_id"] for s in sources}
    documents = [{k: v for k, v in d.items() if k not in PRIVATE_DOCUMENT_COLUMNS}
                 for d in _rows(con, "SELECT * FROM lunar_documents ORDER BY document_id") if d["document_id"] in cited]
    return {"lunar_sites": sites, "lunar_reference": samples, "lunar_documents": documents,
            "lunar_sources": sources, "hidden": hidden}

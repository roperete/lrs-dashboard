#!/usr/bin/env python3
"""One-off follow-up to the 2026-09-21 composition audit: physical properties,
reference-material strings, reference retyping and the publicly-available flag.

Runs after `reconcile.py --write`. Every change is logged with its reason to
documentation/physical-audit-log-2026-09-21.json. Idempotent.
"""

import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from reconcile import apply_physical, ensure_schema, physical_corrections  # noqa: E402

DB = ROOT / "lrs.sqlite"
FINDINGS = ROOT / "documentation" / "composition-audit-findings-2026-09-21.json"
LOG_OUT = ROOT / "documentation" / "physical-audit-log-2026-09-21.json"


def clean_physical(sid: str, ph: dict) -> dict:
    """Keep only values the audited source itself states, in the schema's units."""
    out = {}
    for k, v in (ph or {}).items():
        if k == "ph" or v in (None, ""):
            continue
        v = str(v).strip()
        if "[" in v:  # extractor annotated this value as coming from somewhere else
            continue
        if k == "bulk_density" and "loose" in v:  # OPR: "1.2 loose / 1.5 settled" -> uncompressed = loose
            v = v.split()[0]
        if k == "particle_size_range":
            m = re.match(r"^(<?)\s*([\d.]+)\s*-\s*([\d.]+)$", v)
            if m:
                v = f"{m.group(1)}{m.group(2)} – {m.group(3)} µm"
            elif sid == "S100":
                v = "Q25 21.5 µm, Q50 46.9 µm, Q75 128.4 µm"
            else:
                continue
        out[k] = v
    return out


def main() -> None:
    findings = json.loads(FINDINGS.read_text())
    verified = {}
    for g in findings["groups"]:
        if not g.get("verification"):
            continue
        for it in g["extraction"]["results"]:
            if it["verdict"] != "SOURCE_HAS_NO_COMPOSITION":
                verified[it["simulant_id"]] = it

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    ensure_schema(con)
    corrections = {}
    for sid, it in verified.items():
        row = dict(con.execute("SELECT * FROM simulants WHERE simulant_id=?", (sid,)).fetchone())
        c = physical_corrections(clean_physical(sid, it.get("physical")), row)
        if c:
            corrections[sid] = c
    con.close()

    log = apply_physical(DB, corrections)
    sg_clears = sum(1 for e in log if e["field"] == "specific_gravity" and e["new"] is None)
    print(f"physical: {len(log)} field changes, of which {sg_clears} specific-gravity clears")

    con = sqlite3.connect(DB)

    nulls = [
        ("S037", "nasa_fom_score", "not on any SRT fact sheet; 1.5 is also on a different scale from the Hispansion FoM percentages"),
        ("S065", "ti_content_percent", "0.82 is the TiO2 wt%, already in the oxide table; the TDS states no Ti content"),
        ("S066", "ti_content_percent", "0.82 is TLH-0's TiO2 copied across; TLM-0's TiO2 is 1.72 and the TDS states no Ti content"),
        ("S065", "density_g_cm3", "equals the mean bulk density; the TDS states no grain density"),
        ("S066", "density_g_cm3", "equals the mean bulk density; the TDS states no grain density"),
        ("S093", "glass_content_percent", "25.0 is the agglutinate fraction, not a glass content; the sheet states no glass content"),
        ("S079", "glass_content_percent", "10.0 is the glass-rich basalt fraction, not a glass content; the sheet states no glass content"),
    ]
    for sid, col, why in nulls:
        old = con.execute(f"SELECT {col}, name FROM simulants WHERE simulant_id=?", (sid,)).fetchone()
        if old and old[0] is not None:
            con.execute(f"UPDATE simulants SET {col}=NULL WHERE simulant_id=?", (sid,))
            log.append({"simulant_id": sid, "name": old[1], "field": col, "old": old[0], "new": None, "reason": why})

    reference_material = {
        "S036": "Average lunar highlands", "S091": "Average lunar highlands", "S092": "Average lunar highlands",
        "S077": "Average lunar highlands", "S078": "Average lunar highlands", "S093": "Lunar Highlands",
        "S065": "Highlands", "S066": "Low-Ti Mare",
        "S060": "Mare regolith (Apollo)",
    }
    reasons = {
        "S060": "offplanetresearch.com/simulants: 'Replicates: Mare regolith from Apollo missions'; 'High-Ti Mare' describes the OPRL2NT variant",
    }
    default_reason = "the source's own 'Reference Material' / 'Type' statement; the previous value named a mission the source never names"
    for sid, val in reference_material.items():
        old = con.execute("SELECT lunar_sample_reference, name FROM simulants WHERE simulant_id=?", (sid,)).fetchone()
        if old and (old[0] or "") != val:
            con.execute("UPDATE simulants SET lunar_sample_reference=? WHERE simulant_id=?", (val, sid))
            log.append({"simulant_id": sid, "name": old[1], "field": "lunar_sample_reference",
                        "old": old[0], "new": val, "reason": reasons.get(sid, default_reason)})

    retyped = 0
    for sid in verified:
        rows = con.execute(
            "SELECT reference_id, reference_type, coalesce(reference_text, title, '') FROM references_ "
            "WHERE simulant_id=? AND reference_type LIKE '%composition%'", (sid,)).fetchall()
        for rid, rtype, text in rows:
            new = "geotechnical" if re.search(r"geomech|shear|geotech|mechanical", text, re.I) else "usage"
            con.execute("UPDATE references_ SET reference_type=? WHERE reference_id=?", (new, rid))
            log.append({"simulant_id": sid, "field": f"references_.{rid}.reference_type", "old": rtype, "new": new,
                        "reason": "not the composition source recorded on the simulant; the data sheet is"})
            retyped += 1

    marks = ",".join("?" * len(verified))
    con.execute(f"UPDATE simulant_extra SET publicly_available_composition=1 WHERE simulant_id IN ({marks})", list(verified))
    con.execute("UPDATE simulant_extra SET publicly_available_composition=0 WHERE simulant_id='S016'")
    con.commit()
    con.close()

    LOG_OUT.write_text(json.dumps(log, indent=1))
    print(f"total physical/provenance log entries: {len(log)} (references retyped: {retyped}) -> {LOG_OUT.name}")


if __name__ == "__main__":
    main()

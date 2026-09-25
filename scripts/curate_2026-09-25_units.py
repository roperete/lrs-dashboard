#!/usr/bin/env python3
"""Units and bases audit of 2026-09-25 (owner: "a couple agents making sure that the units make
sense for all simulants data points"), applied. Two finders checked 280 property values and
915 composition rows against the quotes; two checkers re-opened the documents. Only findings the
checker CONFIRMED are applied here (and one UNCERTAIN one, removed under "empty rather than
wrong"). Findings and verdicts: documentation/units-audit-2026-09-25.json.

  * omitted: values that are a different quantity from the field (LX rheometer "AP-cohesive
    strength" as cohesion; TiO2 as Ti; a compacted test specimen as bulk density), a qualitative
    phrase as a size distribution, implausible mineral values, oxide rows from another batch;
  * restated to what the document says: log χ with its unit, a missing degree sign, Cu/Cc as
    dimensionless coefficients, "glass-rich basalt", "opaques (probably magnetite)", GreenSpar's
    XRD plagioclase instead of a CIPW norm mixed into an XRD table;
  * the basis of each mineral table (vol%, area%, modal, normative, % of crystalline fraction)
    written into value_text, so the page can say what the "%" is.

Idempotent; logs to documentation/curation-log-2026-09-25-units.json.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "documentation" / "curation-log-2026-09-25-units.json"

OMIT_SCALAR = {
    ("S040", "cohesion"): "rheometer 'AP-cohesive strength', which the paper says is not an absolute value; not Mohr-Coulomb cohesion",
    ("S041", "cohesion"): "rheometer 'AP-cohesive strength', not cohesion",
    ("S138", "cohesion"): "rheometer 'AP-cohesive strength', not cohesion",
    ("S043", "ti_content_percent"): "6.8 is TiO2 wt% (User's Guide Table 7), not Ti; it is in the oxide table already",
    ("S045", "bulk_density"): "1.93 g/cm3 is a compacted triaxial specimen near maximum density, not the simulant's bulk density",
    ("S014", "particle_size_distribution"): "a qualitative phrase about lunar soils, no size stated",
}
SET_SCALAR = {
    ("S037", "magnetic_susceptibility"): "log χ = 3.43 (χ in 10⁻⁹ m³/kg)",
    ("S043", "magnetic_susceptibility"): "log χ = 4.01 (χ in 10⁻⁹ m³/kg)",
    ("S024", "angle_of_repose"): "35.3 ± 0.711°",
    ("S008", "particle_size_distribution"): "Cu = 3.68, Cc = 0.66 (gradation coefficients, dimensionless)",
}
# (table, simulant, component, reference or None) -> why
OMIT_ROWS = {
    ("chemical_compositions", "S081", "Fe2O3", None): "stated for a different batch; contradicts the cited analysis",
    ("mineral_compositions", "S067", "ilmenite", "RN-S067-2"): "implausible against the chemistry shown beside it",
    ("mineral_compositions", "S067", "quartz", "RN-S067-2"): "cannot be reconciled with the chemistry shown (checker UNCERTAIN): empty rather than wrong",
    ("mineral_compositions", "S012", "Olivine", None): "implausible for this simulant (checker CONFIRMED)",
    ("mineral_compositions", "S012", "Plagioclase", None): "implausible for this simulant (checker CONFIRMED)",
    ("chemical_compositions", "S018", "Na2O", None): "from the RN-S018-1 batch, not the analysis the rest of the table cites",
    ("chemical_compositions", "S018", "K2O", None): "from the RN-S018-1 batch, not the analysis the rest of the table cites",
}
RENAME_ROWS = {
    ("mineral_compositions", "S028", "Glass"): ("Glass-rich basalt", "Coker et al. 2026 Table 1: 'glass-rich basalt ... 49.3'"),
    ("mineral_compositions", "S117", "Magnetite"): ("Opaques (probably magnetite)", "'opaques (probably magnetite, 5%'"),
}
SET_ROWS = {
    # GreenSpar: the XRD value, on the same basis as the pyroxene and quartz rows
    ("mineral_compositions", "S025", "Plagioclase"): (82.0, "~82 wt% (XRD, Rietveld)",
        "X-ray diffraction analyses and whole pattern fitting and Rietveld refinement suggest a plagioclase content of approximately 82 wt. %."),
}
ADD_ROWS = [
    ("mineral_compositions", "S005", "Synthetic agglutinates", 35.0, "RN-S005-1", "35 (%)",
     "Table 3 'Mineral compositions and percentages of lunar regolith simulants, %': BHLD20 ... Other minerals 'Synthetic agglutinates (35)'"),
]
# the basis of a whole mineral table, as its document states it
BASIS = {
    "S045": "vol%", "S009": "vol%",
    "S159": "area% (AMICS SEM-EDS)", "S160": "area% (AMICS SEM-EDS)", "S161": "area% (AMICS SEM-EDS)",
    "S049": "particle-type modal %", "S051": "particle-type modal %", "S053": "particle-type modal %",
    "S070": "vol% (thin section)", "S117": "estimated modal % (thin section)",
    "S007": "normative wt% (CIPW, calculated)", "S017": "normative wt% (calculated from bulk chemistry)",
    "S081": "% of crystalline fraction (Rietveld XRD)", "S052": "wt% of the feedstock recipe",
    "S025": "wt% (XRD)", "S082": "wt% total crystalline silica",
}


def _fmt(v: float) -> str:
    return f"{v:g}"


def curate(con: sqlite3.Connection) -> list[dict]:
    log = []
    for (sid, field), why in OMIT_SCALAR.items():
        v = con.execute(f"SELECT {field} FROM simulants WHERE simulant_id=?", (sid,)).fetchone()
        if v and v[0] not in (None, ""):
            src = con.execute("SELECT reference_id, quote FROM property_sources WHERE simulant_id=? AND field=?", (sid, field)).fetchone()
            con.execute(f"UPDATE simulants SET {field}=NULL WHERE simulant_id=?", (sid,))
            con.execute("DELETE FROM property_sources WHERE simulant_id=? AND field=?", (sid, field))
            log.append({"simulant_id": sid, "field": field, "was": v[0], "source": list(src) if src else None, "why": why, "action": "omitted"})
    for (sid, field), value in SET_SCALAR.items():
        v = con.execute(f"SELECT {field} FROM simulants WHERE simulant_id=?", (sid,)).fetchone()
        if v and v[0] != value:
            con.execute(f"UPDATE simulants SET {field}=? WHERE simulant_id=?", (value, sid))
            log.append({"simulant_id": sid, "field": field, "was": v[0], "now": value, "action": "restated as the document states it"})
    # log χ values: the quote carries the table header that states the quantity and its unit
    for sid in ("S037", "S043"):
        row = con.execute("SELECT quote FROM property_sources WHERE simulant_id=? AND field='magnetic_susceptibility'", (sid,)).fetchone()
        if row and not row[0].startswith("Table 22."):
            con.execute("UPDATE property_sources SET quote=? WHERE simulant_id=? AND field='magnetic_susceptibility'",
                        ("Table 22. Lunar Simulant MS Values (log(χ) with χ in 10-9m3/kg) ... " + " ".join(row[0].split()), sid))
            log.append({"simulant_id": sid, "field": "magnetic_susceptibility", "action": "quote given its table header (log χ, unit)"})
    for (table, sid, comp, rid), why in OMIT_ROWS.items():
        q = f"SELECT composition_id, {'value_wt_pct' if table == 'chemical_compositions' else 'value_pct'}, reference_id FROM {table} WHERE simulant_id=? AND component_name=?"
        args = [sid, comp]
        if rid:
            q += " AND reference_id=?"; args.append(rid)
        for cid, val, r in con.execute(q, args).fetchall():
            con.execute(f"DELETE FROM {table} WHERE composition_id=?", (cid,))
            log.append({"simulant_id": sid, "field": f"{table}:{comp}", "was": val, "reference_id": r, "why": why, "action": "row omitted"})
    for (table, sid, comp), (new, quote) in RENAME_ROWS.items():
        for (cid,) in con.execute(f"SELECT composition_id FROM {table} WHERE simulant_id=? AND component_name=?", (sid, comp)).fetchall():
            con.execute(f"UPDATE {table} SET component_name=? WHERE composition_id=?", (new, cid))
            log.append({"simulant_id": sid, "field": f"{table}:{comp}", "now": new, "quote": quote, "action": "renamed as the document names it"})
    for (table, sid, comp), (val, text, quote) in SET_ROWS.items():
        for cid, cur in con.execute(f"SELECT composition_id, value_pct FROM {table} WHERE simulant_id=? AND component_name=?", (sid, comp)).fetchall():
            if cur != val:
                con.execute(f"UPDATE {table} SET value_pct=?, value_text=? WHERE composition_id=?", (val, text, cid))
                log.append({"simulant_id": sid, "field": f"{table}:{comp}", "was": cur, "now": val, "quote": quote, "action": "restated as the document states it"})
    for table, sid, comp, val, rid, text, quote in ADD_ROWS:
        if not con.execute(f"SELECT 1 FROM {table} WHERE simulant_id=? AND component_name=?", (sid, comp)).fetchone():
            n = con.execute(f"SELECT count(*) FROM {table} WHERE simulant_id=?", (sid,)).fetchone()[0] + 1
            cid = f"C-{sid}-{n:02d}"
            while con.execute(f"SELECT 1 FROM {table} WHERE composition_id=?", (cid,)).fetchone():
                n += 1; cid = f"C-{sid}-{n:02d}"
            con.execute(f"INSERT INTO {table} (composition_id, simulant_id, component_type, component_name, value_pct, reference_id, value_text) "
                        "VALUES (?,?,?,?,?,?,?)", (cid, sid, "mineral", comp, val, rid, text))
            log.append({"simulant_id": sid, "field": f"{table}:{comp}", "now": val, "reference_id": rid, "quote": quote, "action": "row added from its document"})
    for sid, basis in BASIS.items():
        for cid, val, text in con.execute("SELECT composition_id, value_pct, value_text FROM mineral_compositions WHERE simulant_id=?", (sid,)).fetchall():
            words = [w for w in __import__('re').findall(r"[A-Za-z]+", basis)]
            if text and all(w.lower() in text.lower() for w in words):
                continue      # the text already states this basis
            approx = "~" if text and text.strip().startswith("~") else ""
            bare = not text or text.strip().rstrip('%').replace('~', '').strip() == _fmt(val)
            new = f"{approx}{_fmt(val)} {basis}" if bare else f"{text.strip()} [{basis}]"
            con.execute("UPDATE mineral_compositions SET value_text=? WHERE composition_id=?", (new, cid))
            log.append({"simulant_id": sid, "field": f"mineral_compositions:{cid}", "was": text, "now": new, "action": "basis written"})
    con.commit()
    return log


def main() -> None:
    con = sqlite3.connect(ROOT / "lrs.sqlite")
    log = curate(con)
    if log:
        old = json.loads(LOG.read_text()) if LOG.exists() else []
        LOG.write_text(json.dumps(old + log, indent=2, ensure_ascii=False) + "\n")
    from collections import Counter
    for k, v in Counter(e["action"] for e in log).most_common():
        print(f"  {v:3}  {k}")
    print(f"{len(log)} change(s)")


if __name__ == "__main__":
    main()

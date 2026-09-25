#!/usr/bin/env python3
"""Where does every simulant stand against the three provenance tests?

  1. named in at least one reference (names_simulant = 1)
  2. references confirmed to concern it; stored values traced to a document
  3. every displayed value carries a source (property_sources / reference_id)

Reads lrs.sqlite only. Writes documentation/provenance-status-<date>.md and .csv.

Usage:  python3 scripts/provenance_report.py
"""

from __future__ import annotations

import csv
import sqlite3
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"

SCALAR_FIELDS = [
    "bulk_density", "cohesion", "friction_angle", "specific_gravity", "density_g_cm3",
    "particle_size_d50", "particle_size_distribution", "particle_morphology", "particle_ruggedness",
    "glass_content_percent", "nasa_fom_score", "ti_content_percent",
    "ph", "angle_of_repose", "particle_size_mean_um", "bulk_density_range", "magnetic_susceptibility",
]


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    sims = [dict(r) for r in con.execute("SELECT * FROM simulants ORDER BY simulant_id")]
    refs = defaultdict(list)
    for r in con.execute("SELECT * FROM references_"):
        refs[r["simulant_id"]].append(dict(r))
    sourced = defaultdict(set)
    for r in con.execute("SELECT simulant_id, field FROM property_sources"):
        sourced[r["simulant_id"]].add(r["field"])
    comp = defaultdict(lambda: [0, 0])  # [rows, rows with reference]
    for t in ("chemical_compositions", "mineral_compositions"):
        for r in con.execute(f"SELECT simulant_id, reference_id FROM {t}"):
            comp[r["simulant_id"]][0] += 1
            comp[r["simulant_id"]][1] += 1 if r["reference_id"] else 0
    con.close()

    rows = []
    for s in sims:
        sid = s["simulant_id"]
        rs = refs.get(sid, [])
        naming = sum(1 for r in rs if r.get("names_simulant") == 1)
        not_naming = sum(1 for r in rs if r.get("names_simulant") == 0)
        unchecked = sum(1 for r in rs if r.get("names_simulant") is None)
        scalars_present = [f for f in SCALAR_FIELDS if s.get(f) not in (None, "")]
        scalars_sourced = [f for f in scalars_present if f in sourced.get(sid, set())]
        crow, cref = comp.get(sid, [0, 0])
        test1 = "pass" if naming > 0 else ("unknown" if unchecked and not naming else "FAIL")
        if not scalars_present and not crow:
            test3 = "n/a"
        elif len(scalars_sourced) == len(scalars_present) and cref == crow:
            test3 = "pass"
        elif scalars_sourced or cref:
            test3 = "partial"
        else:
            test3 = "FAIL"
        rows.append({
            "simulant_id": sid, "name": s["name"], "status": s.get("composition_status"),
            "references": len(rs), "naming": naming, "not_naming": not_naming, "unchecked": unchecked,
            "scalars_present": len(scalars_present), "scalars_sourced": len(scalars_sourced),
            "scalars_unsourced": ", ".join(f for f in scalars_present if f not in sourced.get(sid, set())),
            "composition_rows": crow, "composition_rows_cited": cref,
            "test1_named": test1, "test3_all_values_sourced": test3,
        })

    today = date.today().isoformat()
    out_csv = ROOT / "documentation" / f"provenance-status-{today}.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    t1 = Counter(r["test1_named"] for r in rows)
    t3 = Counter(r["test3_all_values_sourced"] for r in rows)
    total_scalars = sum(r["scalars_present"] for r in rows)
    total_sourced = sum(r["scalars_sourced"] for r in rows)
    total_comp = sum(r["composition_rows"] for r in rows)
    total_cited = sum(r["composition_rows_cited"] for r in rows)
    n_refs = sum(r["references"] for r in rows)
    n_naming = sum(r["naming"] for r in rows)
    n_not = sum(r["not_naming"] for r in rows)

    L = [f"# Provenance status, {today}", "",
         "Three tests per simulant. Detail per simulant in the CSV beside this file.", "",
         "| Test | Result |", "|---|---|",
         f"| 1. Named in at least one reference | pass {t1.get('pass', 0)}, unknown (references unchecked) {t1.get('unknown', 0)}, FAIL {t1.get('FAIL', 0)} |",
         f"| 2. References checked against the document | {n_naming} confirmed to name their simulant, {n_not} confirmed not to, {n_refs - n_naming - n_not} unchecked, of {n_refs} |",
         f"| 3. Every value traced to a document | scalars {total_sourced} of {total_scalars} sourced; composition rows {total_cited} of {total_comp} cited; simulants fully sourced {t3.get('pass', 0)}, partial {t3.get('partial', 0)}, none {t3.get('FAIL', 0)}, nothing to source {t3.get('n/a', 0)} |",
         "", "## Simulants failing test 1 (no reference confirmed to name them)", ""]
    fails = [r for r in rows if r["test1_named"] == "FAIL"]
    L += [f"- {r['name']} ({r['simulant_id']}): {r['references']} references, {r['not_naming']} confirmed not to name it" for r in fails] or ["- none"]
    L += ["", "## Simulants with unsourced values still in the database (hidden from the page)", ""]
    for r in rows:
        if r["scalars_unsourced"]:
            L.append(f"- {r['name']} ({r['simulant_id']}): {r['scalars_unsourced']}")
    out_md = ROOT / "documentation" / f"provenance-status-{today}.md"
    out_md.write_text("\n".join(L) + "\n")
    print("\n".join(L[:9]))
    print(f"\n-> {out_md.name}, {out_csv.name}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Task 3: cite the data sheet, per value, for the simulants verified against one.

For every simulant with composition_status = 'verified':
  1. its composition source becomes a reference row `DS-<simulant_id>` (type `datasheet`
     for a manufacturer sheet, `report` for an agency document), marked as naming the
     simulant, with the local copy recorded;
  2. every composition row cites that reference;
  3. every scalar field the sheet states gets a property_sources row carrying the sheet
     line that states it;
  4. any other non-null scalar on the simulant is logged as "unsourced on a verified
     simulant". It is not deleted here; the export (task 5) suppresses it.

`backfill(db, sheet_fields, checked_on)` is the pure step, tested on a fixture.
`main()` builds sheet_fields for the real database from the audit findings and the
sheet fill spec, quoting the actual line from each sheet's extracted text.

Usage:  python3 scripts/backfill_sheet_sources.py [--write]
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from provenance import ensure_provenance_schema  # noqa: E402

DB = ROOT / "lrs.sqlite"
SOURCES = Path("/Volumes/Extreme SSD/Spring - Forest on the moon/DIRT/Sources")
FINDINGS = ROOT / "documentation" / "composition-audit-findings-2026-09-21.json"
LOG_OUT = ROOT / "documentation" / "sheet-sources-backfill-log-2026-09-22.json"

# Scalar columns on simulants that a source can be cited for.
SCALAR_FIELDS = [
    "bulk_density", "cohesion", "friction_angle", "specific_gravity", "density_g_cm3",
    "particle_size_d50", "particle_size_distribution", "particle_morphology", "particle_ruggedness",
    "glass_content_percent", "nasa_fom_score", "ti_content_percent",
    "ph", "angle_of_repose", "particle_size_mean_um", "bulk_density_range", "magnetic_susceptibility",
]

REFERENCE_TYPE_FOR_KIND = {"manufacturer_datasheet": "datasheet", "agency_report": "report", "primary_paper": "composition"}


def datasheet_reference_id(simulant_id: str) -> str:
    return f"DS-{simulant_id}"


def backfill(db_path: Path | str, sheet_fields: dict[str, dict[str, str]], checked_on: str,
             local_paths: dict[str, str] | None = None) -> list[dict]:
    local_paths = local_paths or {}
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    ensure_provenance_schema(con)
    log: list[dict] = []

    verified = [dict(r) for r in con.execute("SELECT * FROM simulants WHERE composition_status='verified' ORDER BY simulant_id")]
    for s in verified:
        sid = s["simulant_id"]
        rid = datasheet_reference_id(sid)
        rtype = REFERENCE_TYPE_FOR_KIND.get(s.get("composition_source_kind") or "", "datasheet")
        title = s.get("composition_source_title") or f"{s['name']} data sheet"
        url = s.get("composition_source_url")
        year = (s.get("datasheet_date") or "")[:4] or None

        exists = con.execute("SELECT 1 FROM references_ WHERE reference_id=?", (rid,)).fetchone()
        if not exists:
            con.execute(
                """INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type, title, year, url,
                                            names_simulant, mention_quote, local_path, checked_on)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (rid, sid, title, rtype, title, int(year) if year and year.isdigit() else None, url,
                 1, title, local_paths.get(sid), checked_on),
            )
            log.append({"simulant_id": sid, "reference_id": rid, "outcome": "reference row created", "type": rtype})

        n_chem = con.execute("UPDATE chemical_compositions SET reference_id=? WHERE simulant_id=? AND (reference_id IS NULL OR reference_id!=?)", (rid, sid, rid)).rowcount
        n_min = con.execute("UPDATE mineral_compositions SET reference_id=? WHERE simulant_id=? AND (reference_id IS NULL OR reference_id!=?)", (rid, sid, rid)).rowcount
        if n_chem or n_min:
            log.append({"simulant_id": sid, "reference_id": rid, "outcome": "composition rows cited", "oxide_rows": n_chem, "mineral_rows": n_min})

        stated = sheet_fields.get(sid, {})
        for field, quote in stated.items():
            if field not in SCALAR_FIELDS or s.get(field) in (None, ""):
                continue
            have = con.execute("SELECT 1 FROM property_sources WHERE simulant_id=? AND field=?", (sid, field)).fetchone()
            if have:
                continue
            con.execute("INSERT INTO property_sources (simulant_id, field, reference_id, location, quote) VALUES (?,?,?,?,?)",
                        (sid, field, rid, "data sheet", quote))
            log.append({"simulant_id": sid, "field": field, "reference_id": rid, "outcome": "source row written", "quote": quote})

        sourced = {r[0] for r in con.execute("SELECT field FROM property_sources WHERE simulant_id=?", (sid,))}
        for field in SCALAR_FIELDS:
            if s.get(field) not in (None, "") and field not in sourced:
                log.append({"simulant_id": sid, "field": field, "value": s.get(field), "outcome": "unsourced on a verified simulant"})

    con.commit()
    con.close()
    return log


# ---------------------------------------------------------------------------------------
# Building sheet_fields for the real database
# ---------------------------------------------------------------------------------------

def sheet_text(path: Path) -> str:
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, errors="ignore").stdout


def find_quote(text: str, value) -> str | None:
    """First line of the sheet text containing the value as a whole number or phrase."""
    s = str(value).strip()
    nums = re.findall(r"\d+(?:\.\d+)?", s)
    for line in text.splitlines():
        if not line.strip():
            continue
        if nums:
            if all(re.search(r"(?<![\d.])" + re.escape(n) + r"0*(?!\d)", line) for n in nums):
                return re.sub(r"\s{2,}", "  ", line.strip())[:200]
        elif s.lower() in line.lower():
            return re.sub(r"\s{2,}", "  ", line.strip())[:200]
    return None


def build_sheet_fields() -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    import importlib.util
    spec_ = importlib.util.spec_from_file_location("apply_audit", ROOT / "scripts" / "apply_audit_2026-09-21.py")
    apply_audit = importlib.util.module_from_spec(spec_)
    spec_.loader.exec_module(apply_audit)  # type: ignore[union-attr]
    clean_physical = apply_audit.clean_physical
    from datasheet_fill import FILL
    from reconcile import physical_corrections

    findings = json.loads(FINDINGS.read_text())
    ext = {}
    for g in findings["groups"]:
        if not g.get("verification"):
            continue
        for it in g["extraction"]["results"]:
            ext[it["simulant_id"]] = it

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    fields: dict[str, dict[str, str]] = {}
    local_paths: dict[str, str] = {}
    texts: dict[str, str] = {}
    for sid, it in ext.items():
        if it.get("verdict") == "SOURCE_HAS_NO_COMPOSITION":
            continue
        row = dict(con.execute("SELECT * FROM simulants WHERE simulant_id=?", (sid,)).fetchone())
        # the sheet on disk: the extractor's source_url when local, else the fill spec's sheet
        spec = FILL.get(sid, {})
        local = it.get("source_url") if str(it.get("source_url", "")).startswith("/") else None
        if not local and spec.get("sheet"):
            local = str(SOURCES / "datasheets" / spec["sheet"])
        if not local and sid == "S100":
            local = str(SOURCES / "papers" / "Slabic_etal_2024_Lunar_Regolith_Simulant_Users_Guide_RevA_NASA-TM-20240011783.pdf")
        if local:
            local_paths[sid] = str(Path(local).relative_to(SOURCES)) if str(local).startswith(str(SOURCES)) else local
            if local not in texts:
                texts[local] = sheet_text(Path(local))
        text = texts.get(local, "")

        stated: dict[str, str] = {}
        # (a) physical values the extractor read from the sheet, mapped to columns
        for col, val in physical_corrections(clean_physical(sid, it.get("physical")), {}).items():
            if row.get(col) in (None, ""):
                continue
            stated[col] = find_quote(text, row.get(col)) or find_quote(text, val) or f"{col}: {row.get(col)}"
        # sheet-stated values whose DB value equals what the extractor read (no correction needed)
        for k, v in (it.get("physical") or {}).items():
            col = {"bulk_density": "bulk_density", "specific_gravity": "specific_gravity", "particle_size_d50": "particle_size_d50",
                   "particle_size_range": "particle_size_distribution", "cohesion": "cohesion", "friction_angle": "friction_angle",
                   "glass_content_percent": "glass_content_percent", "nasa_fom_score": "nasa_fom_score"}.get(k)
            if col and col not in stated and row.get(col) not in (None, "") and "[" not in str(v):
                stated[col] = find_quote(text, row.get(col)) or f"{col}: {row.get(col)}"
        # the sheet states grain density, which the schema stores twice
        if sid == "S095" and row.get("density_g_cm3") not in (None, ""):
            stated["density_g_cm3"] = find_quote(text, "Estimated Grain Density") or "Estimated Grain Density: 2.70 g/cm3"
        # (b) the 2026-09-22 sheet fill
        for col, val in spec.items():
            if col in SCALAR_FIELDS and val is not None and row.get(col) not in (None, ""):
                stated[col] = find_quote(text, val) or find_quote(text, row.get(col)) or str(val)[:200]
        fields[sid] = stated
    con.close()
    return fields, local_paths


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    fields, local_paths = build_sheet_fields()
    print(f"sheet-stated scalar fields found for {len(fields)} verified simulants: "
          f"{sum(len(v) for v in fields.values())} field citations")
    if not args.write:
        for sid, f in sorted(fields.items()):
            print(f"  {sid}: {', '.join(sorted(f))}")
        print("dry run; add --write to apply")
        return
    log = backfill(DB, fields, checked_on=date.today().isoformat(), local_paths=local_paths)
    LOG_OUT.write_text(json.dumps(log, indent=1))
    by = {}
    for e in log:
        by[e["outcome"]] = by.get(e["outcome"], 0) + 1
    for k, v in sorted(by.items()):
        print(f"  {k}: {v}")
    for e in log:
        if e["outcome"] == "unsourced on a verified simulant":
            print(f"    unsourced: {e['simulant_id']} {e['field']} = {e['value']}")
    print(f"log -> {LOG_OUT.name}")


if __name__ == "__main__":
    main()

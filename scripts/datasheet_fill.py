#!/usr/bin/env python3
"""Fill parameters the manufacturer sheets state but the schema had no column for.

Scope: the 17 simulants whose composition source is a manufacturer data sheet on disk
(Space Resource Technologies x11, Hispansion x2, Off Planet Research x4). Every value
below was transcribed from the sheet by hand and is checked, before writing, to occur
verbatim in that sheet's extracted text (`value_in_text`). A value that fails the check
aborts the run, so nothing can be written that the sheet does not say.

New columns on `simulants`:
    ph                       REAL   pH as stated (SRT sheets)
    angle_of_repose          TEXT   as stated, with the sample mass used
    particle_size_mean_um    REAL   mean particle size where the sheet gives one
    bulk_density_range       TEXT   min-max or loose-settled where the sheet gives a range
    magnetic_susceptibility  TEXT   mass susceptibility as stated (Hispansion)
    product_grade            TEXT   the sheet's own "Simulant Type" / series wording
    datasheet_document_id    TEXT   document / batch code printed on the sheet
    datasheet_date           TEXT   revision date of the sheet used
    datasheet_notes          TEXT   methods, labs and caveats printed on the sheet

Existing columns filled where the sheet states them: particle_morphology (Hispansion
particle geometry), particle_size_distribution (OPR cumulative size table), and in
simulant_extra: feedstock (normalised to the sheet's component list) and application.

Usage:
    python3 scripts/datasheet_fill.py            # dry run: report what would change
    python3 scripts/datasheet_fill.py --write
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"
SHEETS = Path("/Volumes/Extreme SSD/Spring - Forest on the moon/DIRT/Sources/datasheets")
LOG_OUT = ROOT / "documentation" / "datasheet-fill-log-2026-09-22.json"

NEW_SIMULANT_COLUMNS = [
    ("ph", "REAL"),
    ("angle_of_repose", "TEXT"),
    ("particle_size_mean_um", "REAL"),
    ("bulk_density_range", "TEXT"),
    ("magnetic_susceptibility", "TEXT"),
    ("product_grade", "TEXT"),
    ("datasheet_document_id", "TEXT"),
    ("datasheet_date", "TEXT"),
    ("datasheet_notes", "TEXT"),
]

_NUM = re.compile(r"\d+(?:\.\d+)?")


def _norm(s: str) -> str:
    # NFKC folds PDF ligatures such as "ﬁ" back to "fi"
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s)).lower()


def _alnum(s: str) -> str:
    # Drop ™ ® © before folding: NFKC would otherwise spell ™ as the letters "tm"
    s = re.sub(r"[™®©]", "", s)
    return re.sub(r"[^a-z0-9]+", "", _norm(s))


def _number_present(text: str, num: str) -> bool:
    """The number must stand alone. 9.7 is not evidence for 9.75 and 10 is not evidence
    for 100, but a decimal may carry trailing zeros on the sheet: 10.3 matches 10.30."""
    tail = r"0*(?!\d)" if "." in num else r"(?!\d)"
    return re.search(r"(?<![\d.])" + re.escape(num) + tail, text) is not None


def value_in_text(text: str, value) -> bool:
    """Does the sheet text state this value? Numbers must appear verbatim and whole;
    a text value must have every number in it present, or, if it has none, appear as
    a phrase (ignoring case, whitespace, ligatures and symbols such as ™)."""
    t = _norm(text)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        s = repr(value) if isinstance(value, float) else str(value)
        if s.endswith(".0"):
            s = s[:-2]
        return _number_present(t, s)
    s = str(value)
    nums = _NUM.findall(s)
    if nums:
        return all(_number_present(t, n) for n in nums)
    return _alnum(s) in _alnum(text)


def ensure_columns(con: sqlite3.Connection, table: str, cols: list[tuple[str, str]]) -> list[str]:
    have = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
    added = []
    for name, decl in cols:
        if name not in have:
            con.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
            added.append(name)
    return added


def sheet_text(path: Path) -> str:
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=True).stdout


# --------------------------------------------------------------------------------------
# Transcriptions. Keys are column names; "extra" holds simulant_extra columns.
# --------------------------------------------------------------------------------------

SRT_NOTES = (
    "Bulk chemistry by XRF, relative abundances. Mineralogy 'as mixed', by feedstock component. "
    "Glass-rich basalt sourced from Merriam Crater, the same source as JSC-1. pH measured with a "
    "calibrated digital probe at ambient temperature in a humidity-neutral environment. Primary hazard "
    "is dust inhalation; wear a respirator in dusty conditions."
)
SRT_HL = "Anorthosite; Glass-rich basalt (Merriam Crater); Ilmenite; Bronzite; Olivine"
SRT_HL_E = "Anorthosite; Glass-rich basalt (Merriam Crater)"
SRT_MARE = "Bronzite; Glass-rich basalt (Merriam Crater); Anorthosite; Olivine; Ilmenite"

FILL = {
    "S036": {"sheet": "SRT/LHS-1_spec_Dec2025.pdf", "product_grade": "General purpose", "ph": 9.75,
             "angle_of_repose": "22.62° (10 g), 36.58° (250 g)", "datasheet_document_id": "003-01-001-1225",
             "datasheet_date": "2025-12", "datasheet_notes": SRT_NOTES, "extra": {"feedstock": SRT_HL}},
    "S091": {"sheet": "SRT/LHS-1D_spec_Dec2025.pdf", "product_grade": "Extra-fine lunar highlands simulant for dust studies",
             "ph": 9.87, "particle_size_mean_um": 7, "angle_of_repose": "48.6° (10 g), 45.2° (250 g)",
             "datasheet_document_id": "003-03-001-1225", "datasheet_date": "2025-12", "datasheet_notes": SRT_NOTES,
             "extra": {"feedstock": SRT_HL}},
    "S092": {"sheet": "SRT/LHS-1E_spec_Dec2025.pdf", "product_grade": "Engineering Grade", "ph": 10.30,
             "angle_of_repose": "21.97° (10 g), 41.92° (250 g)", "datasheet_document_id": "003-09-001-1225",
             "datasheet_date": "2025-12", "datasheet_notes": SRT_NOTES, "extra": {"feedstock": SRT_HL_E}},
    "S077": {"sheet": "SRT/LHS-2_spec_Dec2025.pdf", "product_grade": "General purpose", "ph": 10.16,
             "angle_of_repose": "30.61° (10 g), 42.71° (250 g)", "datasheet_document_id": "001-11-001-1225",
             "datasheet_date": "2025-12", "datasheet_notes": SRT_NOTES, "extra": {"feedstock": SRT_HL}},
    "S078": {"sheet": "SRT/LHS-2E_spec_Dec2025.pdf", "product_grade": "Engineering Grade 2mm", "ph": 10.17,
             "angle_of_repose": "23.13° (10 g), 39.55° (250 g)", "datasheet_document_id": "001-13-001-1225",
             "datasheet_date": "2025-12", "datasheet_notes": SRT_NOTES, "extra": {"feedstock": SRT_HL_E}},
    "S093": {"sheet": "SRT/LHS-1-25A_spec.pdf", "product_grade": "Higher Fidelity", "particle_size_mean_um": 93,
             "angle_of_repose": "44.4° (10 g), 42.78° (250 g)", "datasheet_document_id": "LHS-1-25A fact sheet, April 2023",
             "datasheet_date": "2023-04",
             "datasheet_notes": "Bulk chemistry by XRF, relative abundances. Mineralogy 'as mixed'. Agglutinate mineralogy: "
                                "Anorthosite 99.0, Iron Powder 1.0. Primary hazard is dust inhalation.",
             "extra": {"feedstock": "Anorthosite; Agglutinates (99.0 anorthosite, 1.0 iron powder); Glass-rich basalt; Ilmenite; Pyroxene; Olivine"}},
    "S037": {"sheet": "SRT/LMS-1_spec_Dec2025.pdf", "product_grade": "General purpose", "ph": 9.65,
             "angle_of_repose": "11.79° (10 g), 34.02° (250 g)", "datasheet_document_id": "003-02-001-1225",
             "datasheet_date": "2025-12", "datasheet_notes": SRT_NOTES, "extra": {"feedstock": SRT_MARE}},
    "S094": {"sheet": "SRT/LMS-1D_spec_Dec2025.pdf", "product_grade": "Extra-fine Lunar mare simulant for dust studies",
             "ph": 10.49, "particle_size_mean_um": 9.34, "angle_of_repose": "46.5°",
             "datasheet_document_id": "003-04-001-1225", "datasheet_date": "2025-12", "datasheet_notes": SRT_NOTES,
             "extra": {"feedstock": SRT_MARE}},
    "S095": {"sheet": "SRT/LMS-1E_spec_Dec2025.pdf", "product_grade": "Engineering Grade", "ph": 10.17,
             "angle_of_repose": "18.99° (10 g), 30.89° (250 g)", "datasheet_document_id": "001-23-001-1225",
             "datasheet_date": "2025-12",
             "datasheet_notes": "Bulk chemistry by XRF, relative abundances. Estimated grain density 2.70 g/cm3. "
                                "No mineralogy is published for this grade. pH by calibrated digital probe. "
                                "Primary hazard is dust inhalation."},
    "S076": {"sheet": "SRT/LMS-2_spec_Dec2025.pdf", "product_grade": "General purpose", "ph": 10.02,
             "angle_of_repose": "19.36° (10 g), 34.85° (250 g)", "datasheet_document_id": "001-14-001-1225",
             "datasheet_date": "2025-12", "datasheet_notes": SRT_NOTES, "extra": {"feedstock": SRT_MARE}},
    "S079": {"sheet": "SRT/LSP-2_spec_Dec2025.pdf", "product_grade": "General purpose", "ph": 10.14,
             "angle_of_repose": "14.96° (10 g), 37.39° (250 g)", "datasheet_document_id": "001-12-001-1225",
             "datasheet_date": "2025-12", "datasheet_notes": SRT_NOTES, "extra": {"feedstock": SRT_HL_E}},
    # Hispansion does not publish its TDS online, so there is no public datasheet_url; the
    # source line links the product page and names the document. The audit had left the
    # local working-copy path in datasheet_url (reported by Alvaro 2026-09-22): cleared here.
    "S065": {"sheet": "Hispansion/TLH-0_TDS.pdf", "datasheet_url": None, "product_grade": "TerraLun Core",
             "particle_size_mean_um": 390.50, "bulk_density_range": "1.40 – 1.94 g/cm3 (min – max; mean 1.67)",
             "particle_morphology": "Aspect ratio 0.70287; root form factor / circularity 0.88048 (dynamic image analysis, CAMSIZER X2)",
             "magnetic_susceptibility": "4495.7 x10-9 m3/kg (mass susceptibility)",
             "datasheet_document_id": "TDS-TLH-0-v1.1", "datasheet_date": "2025-11-11",
             "datasheet_notes": "Chemistry by XRF, Bruker M4 TORNADO (UPV/EHU). Mineralogy by XRD, PANalytical Xpert PRO (UCLM), "
                                "supplemented by Raman spectroscopy (UPV/EHU). PSD and particle geometry by dynamic image analysis, "
                                "CAMSIZER X2. Cohesion and friction angle by direct shear at ~25 kPa and ~50 kPa (UPM-ETSIME). "
                                "Magnetic susceptibility by PPMS DynaCool magnetometer (UGR-CIC). 100 % European sourced and "
                                "manufactured. Na2O below the instrument's quantification limit. Safety data sheet available on request.",
             "extra": {"feedstock": "Anorthosite; Basalt; Altered Peridotite",
                       "application": "Geotechnical and mobility testing; excavation and construction trials; large-scale testbeds; "
                                      "ISRU process development; dust and environmental studies; filtration and sealing validation; "
                                      "scientific research; technology demonstration"}},
    "S066": {"sheet": "Hispansion/TLM-0_TDS.pdf", "datasheet_url": None, "product_grade": "TerraLun Core",
             "particle_size_mean_um": 291.67, "bulk_density_range": "1.27 – 1.76 g/cm3 (min – max; mean 1.52)",
             "particle_morphology": "Aspect ratio 0.71469; root form factor / circularity 0.87628 (dynamic image analysis, CAMSIZER X2)",
             "magnetic_susceptibility": "7536.7 x10-9 m3/kg (mass susceptibility)",
             "datasheet_document_id": "TDS-TLM-0-v1.1", "datasheet_date": "2025-11-11",
             "datasheet_notes": "Chemistry by XRF, Bruker M4 TORNADO (UPV/EHU). Mineralogy by XRD, PANalytical Xpert PRO (UCLM), "
                                "supplemented by Raman spectroscopy (UPV/EHU). PSD and particle geometry by dynamic image analysis, "
                                "CAMSIZER X2. Cohesion and friction angle by direct shear at ~25 kPa and ~50 kPa (UPM-ETSIME). "
                                "Magnetic susceptibility by PPMS DynaCool magnetometer (UGR-CIC). 100 % European sourced and "
                                "manufactured. Na2O below the instrument's quantification limit. Safety data sheet available on request.",
             "extra": {"feedstock": "Basalt; Anorthosite; Altered Peridotite",
                       "application": "Geotechnical and mobility testing; excavation and construction trials; large-scale testbeds; "
                                      "ISRU process development; dust and environmental studies; filtration and sealing validation; "
                                      "scientific research; technology demonstration"}},
}

OPR_PSD = ("Cumulative, % by mass coarser than: 4750.0 µm 0.65; 2000.0 µm 4.19; 850.0 µm 9.09; 425.0 µm 15.43; "
           "250.0 µm 20.32; 150.0 µm 26.81; 75.0 µm 37.99; 32.0 µm 61.31; 22.0 µm 71.04; 13.0 µm 80.38; 9.0 µm 85.42; "
           "7.0 µm 91.36; 3.2 µm 96.51; 1.3 µm 98.25; 1.0 µm 100.00")
OPR_NOTES = ("XRF by Washington State University's Peter Hooper Geoanalytical Laboratory. XRD by Washington State "
             "University's Institute of Materials Research, cobalt anode. Particle size distribution by Materials Testing "
             "& Consulting. Density measured in-house. Standard particle size distribution has a majority of grains 4 mm "
             "and finer with some particles up to 10-15 mm. The anorthosite component contains 1 % ± 1 % crystalline "
             "silica (quartz). Ilmenite present as trace. Titanium can be increased with an ilmenite additive on request. "
             "One data sheet covers the four general simulants; values are not normalised to 100.")
for sid, feed, settled in (("S060", "Anorthosite 10; Basalt 90", "1.5"), ("S057", "Anorthosite 70; Basalt 30", "1.5"),
                           ("S058", "Anorthosite 80; Basalt 20", "1.4"), ("S059", "Anorthosite 90; Basalt 10", "1.4")):
    FILL[sid] = {"sheet": "OPR/OPR_General_Lunar_Simulants_Data_Sheet.pdf", "product_grade": "General simulant",
                 "bulk_density_range": f"1.2 (loose) – {settled} (settled) g/cc", "particle_size_distribution": OPR_PSD,
                 "datasheet_document_id": "Off Planet Research General Lunar Regolith Simulants data sheet",
                 "datasheet_date": "2024", "datasheet_notes": OPR_NOTES, "extra": {"feedstock": feed}}

# Fields whose value is a free-text note rather than a sheet statement to be checked verbatim
UNCHECKED = {"datasheet_notes", "datasheet_date", "datasheet_document_id"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    texts: dict[str, str] = {}
    problems = []
    for sid, spec in FILL.items():
        path = SHEETS / spec["sheet"]
        if spec["sheet"] not in texts:
            texts[spec["sheet"]] = sheet_text(path)
        t = texts[spec["sheet"]]
        for col, val in spec.items():
            if col in ("sheet", "extra") or col in UNCHECKED or val is None:
                continue
            if not value_in_text(t, val):
                problems.append(f"{sid} {col}={val!r} not found in {spec['sheet']}")
        for col, val in spec.get("extra", {}).items():
            if col == "feedstock" and not value_in_text(t, val.split(" (")[0].split(";")[0]):
                problems.append(f"{sid} extra.{col} first component {val!r} not found in {spec['sheet']}")
    if problems:
        print("REFUSING TO WRITE. Values not found verbatim in their sheet:")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print(f"all transcribed values found verbatim in their sheets ({len(FILL)} simulants)")

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    added = ensure_columns(con, "simulants", NEW_SIMULANT_COLUMNS)
    log = []
    for sid, spec in FILL.items():
        row = dict(con.execute("SELECT * FROM simulants WHERE simulant_id=?", (sid,)).fetchone())
        extra = dict(con.execute("SELECT * FROM simulant_extra WHERE simulant_id=?", (sid,)).fetchone() or {})
        for col, val in spec.items():
            if col in ("sheet", "extra"):
                continue
            if row.get(col) != val:
                log.append({"simulant_id": sid, "name": row["name"], "table": "simulants", "field": col,
                            "old": row.get(col), "new": val, "source": spec["sheet"]})
                if args.write:
                    con.execute(f"UPDATE simulants SET {col}=? WHERE simulant_id=?", (val, sid))
        for col, val in spec.get("extra", {}).items():
            if extra.get(col) != val:
                log.append({"simulant_id": sid, "name": row["name"], "table": "simulant_extra", "field": col,
                            "old": extra.get(col), "new": val, "source": spec["sheet"]})
                if args.write:
                    con.execute(f"UPDATE simulant_extra SET {col}=? WHERE simulant_id=?", (val, sid))
    if args.write:
        con.commit()
        LOG_OUT.write_text(json.dumps(log, indent=1))
    con.close()

    print(f"columns added: {added or 'none'}")
    print(f"{len(log)} field changes{' written' if args.write else ' (dry run)'}")
    by_field = {}
    for e in log:
        by_field[e["field"]] = by_field.get(e["field"], 0) + 1
    for k, v in sorted(by_field.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()

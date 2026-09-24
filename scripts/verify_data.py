#!/usr/bin/env python3
"""Verify referential integrity across all JSON data files.

Usage:
    python scripts/verify_data.py
"""

import json
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_json import SUPPRESSED_SCALAR_FIELDS  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "public" / "data"

# The app loads one bundle, data.json (exported from lrs.sqlite by export_json.py).
# The per-table files this script used to read were stale copies and were removed
# on 2026-09-21, so verification now reads the same bundle the frontend does.
_BUNDLE = None
_KEYS = {
    "simulant.json": "simulants", "simulant_extra.json": "simulant_extra", "site.json": "sites",
    "composition.json": "compositions", "chemical_composition.json": "chemical_compositions",
    "references.json": "references", "mineral_groups.json": "mineral_groups",
    "mineral_sourcing.json": "mineral_sourcing", "lunar_reference.json": "lunar_reference",
    "property_sources.json": "property_sources",
}


def load(name):
    global _BUNDLE
    if _BUNDLE is None:
        with open(DATA_DIR / "data.json") as f:
            _BUNDLE = json.load(f)
    return _BUNDLE.get(_KEYS[name], [])


# REAL columns on simulants. A value in one of these must reach the page as a number: the
# page coerces with Number() and hides anything that fails, silently.
NUMERIC_SCALAR_FIELDS = (
    "tons_produced_mt", "specific_gravity", "density_g_cm3", "particle_size_d50",
    "glass_content_percent", "nasa_fom_score", "ti_content_percent", "ph", "particle_size_mean_um",
)


# Text columns shown as numbers in a fixed unit: bulk density g/cm³, cohesion kPa, friction °.
TEXT_NUMBER_FIELDS = ("bulk_density", "cohesion", "friction_angle")


def _is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_numeric_values(simulants, compositions, chemicals):
    """Every composition value and every numeric property in the bundle is a number.

    A value stored as text ("22.4 (vol%)", "38.22 μm") is dropped by the page without a
    word, so it must fail here rather than disappear there."""
    errors = []
    for c in compositions:
        if not _is_number(c.get("value_pct")):
            errors.append(f"Mineral value is not a number: {c.get('simulant_id')} {c.get('composition_id')} = {c.get('value_pct')!r}")
    for c in chemicals:
        if not _is_number(c.get("value_wt_pct")):
            errors.append(f"Oxide value is not a number: {c.get('simulant_id')} {c.get('composition_id')} = {c.get('value_wt_pct')!r}")
    for s in simulants:
        for f in NUMERIC_SCALAR_FIELDS:
            v = s.get(f)
            if v is not None and not _is_number(v):
                errors.append(f"Numeric property is not a number: {s.get('simulant_id')} {f} = {v!r}")
        # Text columns the page reads with Number() and labels g/cm³, kPa, °: a unit inside the
        # value hides it or, worse, is read in the wrong unit ("185.2 Pa" shown as 185.2 kPa).
        for f in TEXT_NUMBER_FIELDS:
            v = s.get(f)
            if v in (None, "") or _is_number(v):
                continue
            try:
                float(str(v))
            except ValueError:
                errors.append(f"Physical value is not a bare number: {s.get('simulant_id')} {f} = {v!r}")
    return errors


def check_scalar_provenance(simulants, property_sources):
    """The per-value rule as it reaches the reader: no gated scalar may be non-null in the
    exported bundle without a property_sources row for (simulant_id, field). Returns one
    error string per violation."""
    sourced = {(p["simulant_id"], p["field"]) for p in property_sources}
    errors = []
    for s in simulants:
        for field in SUPPRESSED_SCALAR_FIELDS:
            if s.get(field) is not None and (s["simulant_id"], field) not in sourced:
                errors.append(f"Unsourced scalar exported: {s['simulant_id']} {field} = {s[field]!r} (no property_sources row)")
    return errors


def main():
    print("=== LRS Data Verification ===\n")

    simulants = load("simulant.json")
    extras = load("simulant_extra.json")
    sites = load("site.json")
    compositions = load("composition.json")
    chemicals = load("chemical_composition.json")
    references = load("references.json")
    mineral_groups = load("mineral_groups.json")
    mineral_sourcing = load("mineral_sourcing.json")
    lunar_ref = load("lunar_reference.json")
    property_sources = load("property_sources.json")

    sim_ids = {s["simulant_id"] for s in simulants}
    ref_ids = {r["reference_id"] for r in references}
    errors = []
    warnings = []

    # 1. Duplicate simulant IDs
    id_counts = Counter(s["simulant_id"] for s in simulants)
    for sid, count in id_counts.items():
        if count > 1:
            errors.append(f"Duplicate simulant_id: {sid} ({count} times)")

    # 2. Every extra has a matching simulant
    for e in extras:
        if e["simulant_id"] not in sim_ids:
            errors.append(f"simulant_extra orphan: {e['simulant_id']} ({e.get('name')})")

    # 3. Every site has a matching simulant
    for s in sites:
        if s["simulant_id"] not in sim_ids:
            errors.append(f"site orphan: {s['simulant_id']} ({s.get('site_name')})")

    # 4. Every composition has a matching simulant
    for c in compositions:
        if c["simulant_id"] not in sim_ids:
            errors.append(f"composition orphan: {c['simulant_id']} ({c.get('mineral_name')})")

    # 5. Every chemical has a matching simulant
    for c in chemicals:
        if c["simulant_id"] not in sim_ids:
            errors.append(f"chemical orphan: {c['simulant_id']} ({c.get('oxide')})")

    # 6. Every reference has a matching simulant
    for r in references:
        if r["simulant_id"] not in sim_ids:
            errors.append(f"reference orphan: {r['simulant_id']}")

    # 7. Every mineral group has a matching simulant
    for mg in mineral_groups:
        if mg["simulant_id"] not in sim_ids:
            errors.append(f"mineral_group orphan: {mg['simulant_id']}")

    # 8. Required fields check
    for s in simulants:
        if not s.get("name"):
            errors.append(f"Simulant {s['simulant_id']} missing name")
        if not s.get("simulant_id"):
            errors.append(f"Simulant missing simulant_id")

    # 9. Coverage stats
    sids_with_comp = set(c["simulant_id"] for c in compositions)
    sids_with_chem = set(c["simulant_id"] for c in chemicals)
    sids_with_ref = set(r["simulant_id"] for r in references)
    sids_with_site = set(s["simulant_id"] for s in sites)
    sids_with_extra = set(e["simulant_id"] for e in extras)

    no_comp = sim_ids - sids_with_comp
    no_chem = sim_ids - sids_with_chem
    no_ref = sim_ids - sids_with_ref
    no_site = sim_ids - sids_with_site

    if no_comp:
        warnings.append(f"{len(no_comp)} simulants without mineral composition")
    if no_chem:
        warnings.append(f"{len(no_chem)} simulants without chemical composition")
    if no_ref:
        warnings.append(f"{len(no_ref)} simulants without references")
    if no_site:
        warnings.append(f"{len(no_site)} simulants without site/location")

    # 10. Availability normalization check
    avail_values = Counter(s.get("availability") for s in simulants)
    for val, count in avail_values.most_common():
        if val and val not in ("Available", "Unknown", "Production stopped", "Limited Stock"):
            warnings.append(f"Non-standard availability: '{val}' ({count} records)")

    # 11. Per-value provenance: every exported scalar has a source row, and every
    #     source row and composition citation points at a real simulant and reference
    errors.extend(check_scalar_provenance(simulants, property_sources))
    # 12. Numbers reach the page as numbers
    errors.extend(check_numeric_values(simulants, compositions, chemicals))
    # 13. No citation of the project's own registry — it is the data being checked
    for r in references:
        hay = f"{r.get('title') or ''} {r.get('reference_text') or ''}".lower()
        if "global registry of lunar regolith simulants" in hay:
            errors.append(f"Reference cites the project's own registry: {r.get('simulant_id')} {r.get('reference_id')}")
    for p in property_sources:
        if p["simulant_id"] not in sim_ids:
            errors.append(f"property_sources orphan: {p['simulant_id']} {p['field']}")
        if p["reference_id"] not in ref_ids:
            errors.append(f"property_sources cites unknown reference: {p['simulant_id']} {p['field']} -> {p['reference_id']}")
    for label, rows in (("composition", compositions), ("chemical", chemicals)):
        for c in rows:
            rid = c.get("reference_id")
            if rid is not None and rid not in ref_ids:
                errors.append(f"{label} row cites unknown reference: {c['composition_id']} -> {rid}")
    sids_with_sources = {p["simulant_id"] for p in property_sources}

    # Report
    print(f"Files loaded:")
    print(f"  simulants: {len(simulants)}")
    print(f"  extras: {len(extras)}")
    print(f"  sites: {len(sites)}")
    print(f"  compositions: {len(compositions)}")
    print(f"  chemicals: {len(chemicals)}")
    print(f"  references: {len(references)}")
    print(f"  mineral_groups: {len(mineral_groups)}")
    print(f"  mineral_sourcing: {len(mineral_sourcing)}")
    print(f"  lunar_reference: {len(lunar_ref)}")
    print(f"  property_sources: {len(property_sources)}")
    print()

    print(f"Coverage:")
    print(f"  With mineral composition: {len(sids_with_comp)}/{len(sim_ids)}")
    print(f"  With chemical composition: {len(sids_with_chem)}/{len(sim_ids)}")
    print(f"  With references: {len(sids_with_ref)}/{len(sim_ids)}")
    print(f"  With site/location: {len(sids_with_site)}/{len(sim_ids)}")
    print(f"  With extra data: {len(sids_with_extra)}/{len(sim_ids)}")
    print(f"  With sourced scalar values: {len(sids_with_sources)}/{len(sim_ids)}")
    print()

    print(f"Availability distribution:")
    for val, count in avail_values.most_common():
        print(f"  {val or 'null'}: {count}")
    print()

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  [ERROR] {e}")
    else:
        print("No errors found.")
    print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  [WARN] {w}")
    else:
        print("No warnings.")

    print()
    print("PASS" if not errors else "FAIL")
    return len(errors) == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)

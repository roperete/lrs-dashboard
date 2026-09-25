#!/usr/bin/env python3
"""Apply composition-audit findings to lrs.sqlite.

Policy (set by the project owner, 2026-09-18): a composition value is published
only when it is traced to an acceptable source AND an independent second read
confirmed it. Everything else is withheld, and the simulant records why.

Acceptable composition sources, best first:
    manufacturer_datasheet   the producer's spec / technical data sheet for that exact product
    primary_paper            the paper that introduced and characterised the simulant
    agency_report            an agency report tabulating measured data

A review paper that reprints someone else's table is NOT an acceptable source.
Reviews are where most of this database's unsourced numbers came from.

Sum rules: a mineral modal analysis must sum to 90-101 %, a bulk oxide analysis
to 95-102 % once aggregate rows (Sum, Total, LOI) and duplicated iron / alkali
totals are excluded. A list failing its rule is dropped on its own; a sound list
alongside it survives.

Usage:
    python3 scripts/reconcile.py --findings audit.json            # dry run, prints plan
    python3 scripts/reconcile.py --findings audit.json --write    # apply to lrs.sqlite
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "lrs.sqlite"

STATUS_VERIFIED = "verified"
STATUS_WITHHELD = "withheld_unverified"
STATUS_NOT_PUBLISHED = "not_published"
STATUS_NOT_EXTRACTED = "not_extracted"

ACCEPTABLE_SOURCE_KINDS = {"manufacturer_datasheet", "primary_paper", "agency_report"}

AGGREGATE_OXIDES = {"Sum", "Total", "LOI"}
MINERAL_SUM_RANGE = (90.0, 101.0)
OXIDE_SUM_RANGE = (95.0, 102.0)

NEW_COLUMNS = [
    ("composition_status", "TEXT"),
    ("composition_source_title", "TEXT"),
    ("composition_source_url", "TEXT"),
    ("composition_source_kind", "TEXT"),
    ("composition_needs_review", "INTEGER"),
]


def oxide_sum(oxides: list[dict]) -> float:
    """Sum oxide wt%, excluding aggregate rows and totals that double-count."""
    names = {o["name"] for o in oxides}
    skip = set(AGGREGATE_OXIDES)
    if "FeOT" in names and ("FeO" in names or "Fe2O3" in names):
        skip.add("FeOT")
    if "Fe2O3T" in names and ("FeO" in names or "Fe2O3" in names):
        skip.add("Fe2O3T")
    if "Na2O+K2O" in names and ("Na2O" in names or "K2O" in names):
        skip.add("Na2O+K2O")
    return round(sum(float(o["wt_pct"]) for o in oxides
                     if o["name"] not in skip and isinstance(o.get("wt_pct"), (int, float))), 2)


def mineral_sum(minerals: list[dict]) -> float:
    return round(sum(float(m["pct"]) for m in minerals if isinstance(m.get("pct"), (int, float))), 2)


def _withhold(status, reason, needs_review=False, ext=None):
    ext = ext or {}
    return {
        "action": "withhold", "status": status, "oxides": [], "minerals": [],
        "source_url": ext.get("source_url", "") or "", "source_title": ext.get("source_title", "") or "",
        "source_kind": ext.get("source_kind", "none") or "none",
        "reason": reason, "needs_review": needs_review,
    }


def decide(ext: dict | None, chk: dict | None) -> dict:
    """Decide what to do with one simulant's composition, given audit findings."""
    if not ext:
        return _withhold(STATUS_WITHHELD, "no extraction result (agent produced nothing)", needs_review=True)
    if not chk:
        return _withhold(STATUS_WITHHELD, "no independent verification of the extraction", needs_review=True, ext=ext)

    problems = "; ".join(chk.get("problems") or [])
    verdict = chk.get("verdict")
    needs_review = False

    if verdict == "REFUTED":
        return _withhold(STATUS_WITHHELD, f"verification refuted the extraction: {problems}", ext=ext)

    corrected_ox = chk.get("corrected_oxides") or []
    corrected_mn = chk.get("corrected_minerals") or []
    used_corrections = bool(corrected_ox or corrected_mn)

    if verdict == "PARTIAL":
        if not used_corrections:
            return _withhold(
                STATUS_WITHHELD,
                f"verification could not confirm the numbers and supplied no correction: {problems}",
                ext=ext,
            )
        needs_review = True

    if not ext.get("found") or ext.get("verdict") == "NO_SOURCE_FOUND":
        return _withhold(STATUS_WITHHELD, "no acceptable source could be obtained for this simulant", ext=ext)

    if ext.get("verdict") == "SOURCE_HAS_NO_COMPOSITION":
        return _withhold(STATUS_NOT_PUBLISHED, "the defining source publishes no composition", ext=ext)

    kind = ext.get("source_kind") or "none"
    if kind not in ACCEPTABLE_SOURCE_KINDS:
        return _withhold(
            STATUS_WITHHELD,
            f"only a review or secondary source was found ({kind}); a review reprinting a table is not an acceptable composition source",
            ext=ext,
        )

    oxides = corrected_ox or list(ext.get("oxides") or [])
    minerals = corrected_mn or list(ext.get("minerals") or [])

    reasons = []
    if oxides:
        s = oxide_sum(oxides)
        if not (OXIDE_SUM_RANGE[0] <= s <= OXIDE_SUM_RANGE[1]):
            reasons.append(f"oxide analysis sums to {s}%, outside {OXIDE_SUM_RANGE[0]:g}-{OXIDE_SUM_RANGE[1]:g}% so it is incomplete; oxides dropped")
            oxides = []
            needs_review = True
    if minerals:
        s = mineral_sum(minerals)
        if not (MINERAL_SUM_RANGE[0] <= s <= MINERAL_SUM_RANGE[1]):
            reasons.append(f"mineral analysis sums to {s}%, outside {MINERAL_SUM_RANGE[0]:g}-{MINERAL_SUM_RANGE[1]:g}% so it is incomplete or double-counted; minerals dropped")
            minerals = []
            needs_review = True

    if not oxides and not minerals:
        base = "; ".join(reasons) if reasons else "the source states no composition for this product"
        status = STATUS_WITHHELD if reasons else STATUS_NOT_PUBLISHED
        return _withhold(status, base, ext=ext)

    if reasons:
        reason = "; ".join(reasons)
    elif used_corrections:
        reason = f"verification corrected the extraction: {problems}"
    elif ext.get("verdict") == "DB_WRONG_SOURCE_FOUND":
        reason = "database disagreed with the source: " + "; ".join(ext.get("db_discrepancies") or [])
    else:
        reason = "confirmed against source"

    changed = used_corrections or bool(reasons) or ext.get("verdict") == "DB_WRONG_SOURCE_FOUND"
    return {
        "action": "replace" if changed else "keep",
        "status": STATUS_VERIFIED,
        "oxides": oxides,
        "minerals": minerals,
        "source_url": ext.get("source_url", "") or "",
        "source_title": ext.get("source_title", "") or "",
        "source_kind": kind,
        "reason": reason,
        "needs_review": needs_review,
    }


def ensure_schema(con: sqlite3.Connection) -> None:
    have = {r[1] for r in con.execute("PRAGMA table_info(simulants)")}
    for name, decl in NEW_COLUMNS:
        if name not in have:
            con.execute(f"ALTER TABLE simulants ADD COLUMN {name} {decl}")


def apply_decisions(db_path: Path | str, decisions: dict[str, dict]) -> list[dict]:
    con = sqlite3.connect(str(db_path))
    ensure_schema(con)

    con.execute(
        "UPDATE simulants SET composition_status=?, composition_needs_review=0 WHERE composition_status IS NULL",
        (STATUS_NOT_EXTRACTED,),
    )
    audited = list(decisions)
    if audited:
        marks = ",".join("?" * len(audited))
        con.execute(
            f"UPDATE simulants SET composition_status=? WHERE simulant_id NOT IN ({marks}) AND composition_status!=?",
            [STATUS_NOT_EXTRACTED, *audited, STATUS_NOT_EXTRACTED],
        )

    log: list[dict] = []
    for sid, d in sorted(decisions.items()):
        n_ox = con.execute("SELECT count(*) FROM chemical_compositions WHERE simulant_id=?", (sid,)).fetchone()[0]
        n_mn = con.execute("SELECT count(*) FROM mineral_compositions WHERE simulant_id=?", (sid,)).fetchone()[0]

        if d["action"] in ("replace", "withhold"):
            con.execute("DELETE FROM chemical_compositions WHERE simulant_id=?", (sid,))
            con.execute("DELETE FROM mineral_compositions WHERE simulant_id=?", (sid,))
            con.execute("DELETE FROM mineral_groups WHERE simulant_id=?", (sid,))

        if d["action"] == "replace":
            for i, o in enumerate(d["oxides"], 1):
                con.execute(
                    "INSERT INTO chemical_compositions (composition_id, simulant_id, component_type, component_name, value_wt_pct) VALUES (?,?,?,?,?)",
                    (f"CH-{sid}-{i:02d}", sid, "oxide", o["name"], o["wt_pct"]),
                )
            for i, m in enumerate(d["minerals"], 1):
                con.execute(
                    "INSERT INTO mineral_compositions (composition_id, simulant_id, component_type, component_name, value_pct) VALUES (?,?,?,?,?)",
                    (f"C-{sid}-{i:02d}", sid, "mineral", m["name"], m["pct"]),
                )

        # Only a web address is stored as a source URL. Extractors often open a local
        # working copy and report its path; that path is kept in the findings file, not
        # here, because on the site it would render as a link into github.io and 404.
        public_url = d["source_url"] if str(d["source_url"] or "").lower().startswith(("http://", "https://")) else None
        con.execute(
            """UPDATE simulants SET composition_status=?, composition_source_title=?, composition_source_url=?,
                                    composition_source_kind=?, composition_needs_review=?
               WHERE simulant_id=?""",
            (d["status"], d["source_title"] or None, public_url,
             d["source_kind"] if d["source_kind"] != "none" else None,
             1 if d["needs_review"] else 0, sid),
        )
        # A datasheet link is a public claim that this exact product has a sheet we checked.
        # Only a verified simulant earns one; a withheld one loses any it had, so a sheet
        # belonging to a sibling product (JSC-1A's sheet on JSC-1AC) cannot survive here.
        if d["status"] == STATUS_VERIFIED and d["source_kind"] == "manufacturer_datasheet" and public_url:
            con.execute("UPDATE simulants SET datasheet_url=? WHERE simulant_id=?", (public_url, sid))
        elif d["action"] == "withhold":
            con.execute("UPDATE simulants SET datasheet_url=NULL WHERE simulant_id=?", (sid,))

        name = con.execute("SELECT name FROM simulants WHERE simulant_id=?", (sid,)).fetchone()
        log.append({
            "simulant_id": sid,
            "name": name[0] if name else "",
            "action": d["action"],
            "status": d["status"],
            "reason": d["reason"],
            "source_kind": d["source_kind"],
            "source_title": d["source_title"],
            "source_url": d["source_url"],
            "needs_review": d["needs_review"],
            "oxides_before": n_ox,
            "minerals_before": n_mn,
            "oxides_after": len(d["oxides"]) if d["action"] != "withhold" else 0,
            "minerals_after": len(d["minerals"]) if d["action"] != "withhold" else 0,
            "oxides_removed": n_ox if d["action"] == "withhold" else max(0, n_ox - len(d["oxides"])),
            "minerals_removed": n_mn if d["action"] == "withhold" else max(0, n_mn - len(d["minerals"])),
        })

    con.commit()
    con.close()
    return log



# ---------------------------------------------------------------------------
# Physical properties
# ---------------------------------------------------------------------------

# Agent field name -> database column
PHYSICAL_FIELD_MAP = {
    "bulk_density": "bulk_density",
    "specific_gravity": "specific_gravity",
    "particle_size_d50": "particle_size_d50",
    "particle_size_range": "particle_size_distribution",
    "cohesion": "cohesion",
    "friction_angle": "friction_angle",
    "glass_content_percent": "glass_content_percent",
    "nasa_fom_score": "nasa_fom_score",
    # "ph" has no column in this schema and is dropped on purpose
}

NUMERIC_COLUMNS = {
    "specific_gravity", "particle_size_d50", "density_g_cm3",
    "glass_content_percent", "nasa_fom_score", "ti_content_percent",
}

# No silicate mineral is this light, so a smaller value is not a specific gravity.
MIN_PLAUSIBLE_SPECIFIC_GRAVITY = 2.0


def _num(v):
    """Best-effort float, or None when the value is not a plain number."""
    if isinstance(v, (int, float)):
        return float(v)
    if v is None:
        return None
    try:
        return float(str(v).strip().replace("%", ""))
    except (TypeError, ValueError):
        return None


def suspect_specific_gravity(specific_gravity, bulk_density):
    """Is this specific_gravity provably not a specific gravity? -> (bool, why)."""
    sg = _num(specific_gravity)
    if sg is None:
        return False, ""
    bd = _num(bulk_density)
    if bd is not None and abs(sg - bd) < 0.005:
        return True, "value equals the bulk density, so the bulk density was copied into this column"
    if sg < MIN_PLAUSIBLE_SPECIFIC_GRAVITY:
        return True, f"value is below {MIN_PLAUSIBLE_SPECIFIC_GRAVITY}, lighter than any silicate mineral"
    return False, ""


def physical_corrections(source_physical: dict, db_row: dict) -> dict:
    """Columns where an audited source disagrees with, or fills in, the database."""
    out = {}
    for field, value in (source_physical or {}).items():
        col = PHYSICAL_FIELD_MAP.get(field)
        if not col or value in (None, ""):
            continue
        current = db_row.get(col)
        sv, cv = _num(value), _num(current)
        if sv is not None and cv is not None:
            if abs(sv - cv) < 1e-6:
                continue
        elif str(current or "").strip() == str(value).strip():
            continue
        out[col] = sv if (col in NUMERIC_COLUMNS and sv is not None) else value
    return out


def apply_physical(db_path, corrections_by_simulant: dict) -> list:
    """Clear provably-copied specific gravities and apply audited corrections.

    corrections_by_simulant maps simulant_id -> {column: value}. Run the agent
    field names through physical_corrections() first to get column names.
    """
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    ensure_schema(con)
    log = []

    for row in con.execute("SELECT * FROM simulants").fetchall():
        row = dict(row)
        sid = row["simulant_id"]
        bad, why = suspect_specific_gravity(row.get("specific_gravity"), row.get("bulk_density"))
        if bad:
            con.execute("UPDATE simulants SET specific_gravity=NULL WHERE simulant_id=?", (sid,))
            log.append({"simulant_id": sid, "name": row.get("name"), "field": "specific_gravity",
                        "old": row.get("specific_gravity"), "new": None, "reason": why})

    for sid, corrections in sorted((corrections_by_simulant or {}).items()):
        row = con.execute("SELECT * FROM simulants WHERE simulant_id=?", (sid,)).fetchone()
        if row is None:
            continue
        row = dict(row)
        for col, value in corrections.items():
            current = row.get(col)
            sv, cv = _num(value), _num(current)
            if sv is not None and cv is not None and abs(sv - cv) < 1e-6:
                continue
            if sv is None and str(current or "").strip() == str(value).strip():
                continue
            con.execute(f"UPDATE simulants SET {col}=? WHERE simulant_id=?", (value, sid))
            log.append({"simulant_id": sid, "name": row.get("name"), "field": col,
                        "old": current, "new": value,
                        "reason": "database disagreed with the audited source"})

    con.commit()
    con.close()
    return log

def decisions_from_findings(findings: dict) -> dict[str, dict]:
    """Turn the audit workflow's output into per-simulant decisions."""
    out: dict[str, dict] = {}
    for grp in findings.get("groups", []):
        ext = (grp.get("extraction") or {}).get("results") or []
        ver = (grp.get("verification") or {}).get("checks") or []
        checks = {c.get("simulant_id"): c for c in ver}
        seen = set()
        for e in ext:
            sid = e.get("simulant_id")
            if not sid:
                continue
            seen.add(sid)
            out[sid] = decide(e, checks.get(sid))
        for sid in grp.get("ids", []):
            if sid not in seen:
                out[sid] = _withhold(STATUS_WITHHELD, "the audit produced no result for this simulant", needs_review=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--findings", type=Path, required=True, help="JSON output of the audit workflow")
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--write", action="store_true", help="apply changes; without it, prints the plan only")
    ap.add_argument("--log-out", type=Path, default=ROOT / "documentation" / "composition-audit-log.json")
    args = ap.parse_args()

    findings = json.loads(args.findings.read_text())
    decisions = decisions_from_findings(findings)

    counts: dict[str, int] = {}
    for d in decisions.values():
        counts[d["status"]] = counts.get(d["status"], 0) + 1
    print(f"{len(decisions)} simulants audited")
    for k in (STATUS_VERIFIED, STATUS_WITHHELD, STATUS_NOT_PUBLISHED):
        print(f"  {k}: {counts.get(k, 0)}")
    print(f"  flagged for human review: {sum(1 for d in decisions.values() if d['needs_review'])}")

    if not args.write:
        print("\nDry run. Re-run with --write to apply.")
        for sid, d in sorted(decisions.items()):
            print(f"  {sid:6} {d['action']:8} {d['status']:20} {d['reason'][:100]}")
        return

    log = apply_decisions(args.db, decisions)
    args.log_out.parent.mkdir(parents=True, exist_ok=True)
    args.log_out.write_text(json.dumps(log, indent=1))
    print(f"\nApplied to {args.db}. Audit log: {args.log_out}")
    print(f"  rows removed: {sum(e['oxides_removed'] for e in log)} oxide, {sum(e['minerals_removed'] for e in log)} mineral")


if __name__ == "__main__":
    main()

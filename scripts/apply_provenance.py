#!/usr/bin/env python3
"""Task 7.1: apply agent findings to lrs.sqlite under the per-value provenance policy.

Inputs per simulant (produced by the extraction agent, checked by the verification agent):

  extraction = {
    "simulant_id": "S010",
    "references": [{"reference_id", "opened", "names_simulant", "mention_quote", "location"}],
    "values":     [{"field", "stored", "status": "supported"|"unsupported", "reference_id", "location", "quote"}],
    "new_values": [{"field", "value", "reference_id", "location", "quote"}],
  }
  verification = {
    "simulant_id": "S010",
    "reference_checks": [{"reference_id", "verdict"}],
    "value_checks":     [{"field", "verdict", "problems"}],
    "new_value_checks": [{"field", "verdict", "problems"}],
  }
  verdict in CONFIRMED | REFUTED | UNCERTAIN

`field` is a scalar column name, or "oxide:<component>" / "mineral:<component>".

Rules:
  * write only what both agents agree on (extractor claim + CONFIRMED);
  * an unsupported value, a refuted claim, or a disagreement writes nothing; the value stays
    in the database and is logged (the export hides scalars without a source row);
  * a reference confirmed to name no simulant is marked names_simulant = 0, never deleted;
  * a confirmed new value is inserted with its source row; it never overwrites a value
    already present, which is logged as a conflict for a human.

Usage:  python3 scripts/apply_provenance.py --findings <workflow result json> [--write]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"

SCALAR_FIELDS = {
    "bulk_density", "cohesion", "friction_angle", "specific_gravity", "density_g_cm3",
    "particle_size_d50", "particle_size_distribution", "particle_morphology", "particle_ruggedness",
    "glass_content_percent", "nasa_fom_score", "ti_content_percent",
    "ph", "angle_of_repose", "particle_size_mean_um", "bulk_density_range", "magnetic_susceptibility",
    "release_date", "availability", "lunar_sample_reference", "institution",
}


def _split_field(field: str) -> tuple[str, str | None]:
    if field.startswith("oxide:"):
        return "oxide", field[len("oxide:"):]
    if field.startswith("mineral:"):
        return "mineral", field[len("mineral:"):]
    return "scalar", None


def _write_source(con, sid, field, reference_id, location, quote) -> bool:
    """Write a property_sources row or a composition reference_id. Returns True if anything changed."""
    kind, component = _split_field(field)
    if kind == "scalar":
        have = con.execute("SELECT reference_id, location, quote FROM property_sources WHERE simulant_id=? AND field=?", (sid, field)).fetchone()
        if have and tuple(have) == (reference_id, location, quote):
            return False
        con.execute("INSERT OR REPLACE INTO property_sources (simulant_id, field, reference_id, location, quote) VALUES (?,?,?,?,?)",
                    (sid, field, reference_id, location, quote))
        return True
    table = "chemical_compositions" if kind == "oxide" else "mineral_compositions"
    cur = con.execute(f"UPDATE {table} SET reference_id=? WHERE simulant_id=? AND component_name=? AND (reference_id IS NULL OR reference_id!=?)",
                      (reference_id, sid, component, reference_id))
    return cur.rowcount > 0


def apply_group(db_path: Path | str, extractions: list[dict], verifications: list[dict], checked_on: str | None = None) -> list[dict]:
    checked_on = checked_on or date.today().isoformat()
    con = sqlite3.connect(str(db_path))
    ver_by = {v.get("simulant_id"): v for v in verifications or []}
    log: list[dict] = []

    def note(**e):
        e.setdefault("needs_review", False)
        e.setdefault("field", None)   # reference-level entries have no field
        log.append(e)

    for ext in extractions or []:
        sid = ext.get("simulant_id")
        if not sid:
            continue
        v = ver_by.get(sid)
        if v is None:
            for c in ext.get("values", []):
                note(simulant_id=sid, field=c.get("field"), outcome="flagged: no independent verification for this simulant", needs_review=True)
            for c in ext.get("references", []):
                note(simulant_id=sid, reference_id=c.get("reference_id"), outcome="flagged: no independent verification for this simulant", needs_review=True)
            continue

        ref_checks = {c.get("reference_id"): c for c in v.get("reference_checks", [])}
        val_checks = {c.get("field"): c for c in v.get("value_checks", [])}
        new_checks = {c.get("field"): c for c in v.get("new_value_checks", [])}

        # documents the extractor opened that were not yet references: create rows for the
        # confirmed ones and map the temp ids the value claims use
        temp_ids: dict[str, str | None] = {}
        for nr in ext.get("new_references", []):
            tid = nr.get("temp_id")
            chk = ref_checks.get(tid)
            if not tid:
                continue
            if not chk or chk.get("verdict") != "CONFIRMED":
                temp_ids[tid] = None
                note(simulant_id=sid, reference_id=tid, outcome="flagged: proposed new reference not confirmed", needs_review=True,
                     problems=(chk or {}).get("problems", []), title=nr.get("title"))
                continue
            doi = (nr.get("doi") or "").strip() or None
            local_path = (nr.get("local_path") or "").strip() or None
            title = (nr.get("title") or "").strip() or None
            existing = None
            if doi:
                existing = con.execute("SELECT reference_id FROM references_ WHERE simulant_id=? AND doi=?", (sid, doi)).fetchone()
            if not existing and local_path:
                existing = con.execute("SELECT reference_id FROM references_ WHERE simulant_id=? AND local_path=?", (sid, local_path)).fetchone()
            if not existing and title:
                existing = con.execute("SELECT reference_id FROM references_ WHERE simulant_id=? AND title=?", (sid, title)).fetchone()
            if existing:
                temp_ids[tid] = existing[0]
                continue
            n = con.execute("SELECT count(*) FROM references_ WHERE reference_id LIKE ?", (f"RN-{sid}-%",)).fetchone()[0]
            rid = f"RN-{sid}-{n + 1}"
            con.execute(
                """INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type, title, authors, year, doi, url,
                                            names_simulant, mention_quote, local_path, checked_on)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (rid, sid, title, nr.get("kind") or "general", title, nr.get("authors"), nr.get("year"), doi,
                 (nr.get("url") or "").strip() or None, 1, nr.get("mention_quote") or None, local_path, checked_on),
            )
            temp_ids[tid] = rid
            note(simulant_id=sid, reference_id=rid, outcome="new reference row created", title=title)

        def resolve(reference_id: str | None) -> str | None:
            if reference_id and reference_id.upper().startswith("NEW"):
                return temp_ids.get(reference_id)
            return reference_id or None

        # references: does the document name this simulant?
        for c in ext.get("references", []):
            rid = c.get("reference_id")
            if rid and rid.upper().startswith("NEW"):
                continue  # handled above
            chk = ref_checks.get(rid)
            if not chk or chk.get("verdict") != "CONFIRMED":
                note(simulant_id=sid, reference_id=rid, outcome="flagged: reference claim not confirmed", needs_review=True,
                     problems=(chk or {}).get("problems", []))
                continue
            if not c.get("opened", True):
                note(simulant_id=sid, reference_id=rid, outcome="document unavailable; reference left unchecked")
                continue
            names = 1 if c.get("names_simulant") else 0
            quote = c.get("mention_quote") or None
            row = con.execute("SELECT names_simulant, mention_quote FROM references_ WHERE reference_id=?", (rid,)).fetchone()
            if row and (row[0], row[1]) == (names, quote):
                continue
            con.execute("UPDATE references_ SET names_simulant=?, mention_quote=?, checked_on=? WHERE reference_id=?",
                        (names, quote, checked_on, rid))
            note(simulant_id=sid, reference_id=rid, outcome="reference names the simulant" if names else "reference does NOT name the simulant; kept, marked 0")

        # stored values: supported by which document?
        for c in ext.get("values", []):
            field = c.get("field")
            chk = val_checks.get(field)
            verdict = (chk or {}).get("verdict")
            if verdict == "REFUTED":
                note(simulant_id=sid, field=field, outcome="withheld: refuted by verification", problems=(chk or {}).get("problems", []))
                continue
            if verdict != "CONFIRMED":
                note(simulant_id=sid, field=field, outcome="flagged: verifier could not confirm", needs_review=True,
                     problems=(chk or {}).get("problems", []))
                continue
            if c.get("status") != "supported" or not c.get("reference_id"):
                note(simulant_id=sid, field=field, outcome="withheld: unsupported by any cited document")
                continue
            rid = resolve(c.get("reference_id"))
            if not rid:
                note(simulant_id=sid, field=field, outcome="flagged: cites an unconfirmed new reference", needs_review=True,
                     reference_id=c.get("reference_id"))
                continue
            changed = _write_source(con, sid, field, rid, c.get("location") or "", c.get("quote") or "")
            if changed:
                note(simulant_id=sid, field=field, reference_id=rid, outcome="source row written")

        # values the documents state that we lack
        for c in ext.get("new_values", []):
            field = c.get("field")
            chk = new_checks.get(field)
            if (chk or {}).get("verdict") != "CONFIRMED" or not c.get("reference_id"):
                note(simulant_id=sid, field=field, outcome="flagged: new value not confirmed", needs_review=True,
                     problems=(chk or {}).get("problems", []))
                continue
            rid_new = resolve(c.get("reference_id"))
            if not rid_new:
                note(simulant_id=sid, field=field, outcome="flagged: new value cites an unconfirmed new reference", needs_review=True)
                continue
            c = {**c, "reference_id": rid_new}
            kind, component = _split_field(field)
            if kind == "scalar":
                if field not in SCALAR_FIELDS:
                    note(simulant_id=sid, field=field, outcome="ignored: not a known scalar field")
                    continue
                cur = con.execute(f"SELECT {field} FROM simulants WHERE simulant_id=?", (sid,)).fetchone()
                existing = cur[0] if cur else None
                if existing not in (None, ""):
                    if str(existing) != str(c.get("value")):
                        note(simulant_id=sid, field=field, outcome="conflict: existing value kept, document states a different one",
                             existing=existing, proposed=c.get("value"), reference_id=c["reference_id"], needs_review=True)
                    continue
                con.execute(f"UPDATE simulants SET {field}=? WHERE simulant_id=?", (c.get("value"), sid))
                _write_source(con, sid, field, c["reference_id"], c.get("location") or "", c.get("quote") or "")
                note(simulant_id=sid, field=field, reference_id=c["reference_id"], outcome="new value inserted with source", value=c.get("value"))
            else:
                table, col = ("chemical_compositions", "value_wt_pct") if kind == "oxide" else ("mineral_compositions", "value_pct")
                exists = con.execute(f"SELECT 1 FROM {table} WHERE simulant_id=? AND component_name=?", (sid, component)).fetchone()
                if exists:
                    note(simulant_id=sid, field=field, outcome="conflict: composition row already present, kept", needs_review=True)
                    continue
                prefix = "CH" if kind == "oxide" else "C"
                n = con.execute(f"SELECT count(*) FROM {table} WHERE simulant_id=?", (sid,)).fetchone()[0]
                comp_type = "oxide" if kind == "oxide" else "mineral"
                con.execute(f"INSERT INTO {table} (composition_id, simulant_id, component_type, component_name, {col}, reference_id) VALUES (?,?,?,?,?,?)",
                            (f"{prefix}-{sid}-{n + 1:02d}", sid, comp_type, component, c.get("value"), c["reference_id"]))
                note(simulant_id=sid, field=field, reference_id=c["reference_id"], outcome="new value inserted with source", value=c.get("value"))

    con.commit()
    con.close()
    return log


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--findings", type=Path, required=True, help="workflow result JSON: {groups: [{extraction: {results: [...]}, verification: {checks: [...]}}]}")
    ap.add_argument("--db", type=Path, default=DB)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--log-out", type=Path, default=None)
    args = ap.parse_args()

    findings = json.loads(args.findings.read_text())
    exts, vers = [], []
    for g in findings.get("groups", []):
        exts += ((g.get("extraction") or {}).get("results") or [])
        vers += ((g.get("verification") or {}).get("checks") or [])

    target = args.db if args.write else Path("/tmp") / "apply_provenance_dryrun.sqlite"
    if not args.write:
        import shutil
        shutil.copy(args.db, target)
    log = apply_group(target, exts, vers)
    by: dict[str, int] = {}
    for e in log:
        by[e["outcome"]] = by.get(e["outcome"], 0) + 1
    for k, v in sorted(by.items(), key=lambda kv: -kv[1]):
        print(f"  {v:4}  {k}")
    print(f"{len(log)} log entries; needs_review: {sum(1 for e in log if e['needs_review'])}; {'written' if args.write else 'DRY RUN on a copy'}")
    out = args.log_out or (ROOT / "documentation" / f"provenance-apply-log-{date.today().isoformat()}.json")
    if args.write:
        out.write_text(json.dumps(log, indent=1))
        print(f"log -> {out}")


if __name__ == "__main__":
    main()

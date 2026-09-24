#!/usr/bin/env python3
"""Audit every value the page shows, mechanically, and list what needs a second reading.

Each value was read from its document by one agent and confirmed by a second, but the errors
found on 2026-09-23/24 all entered afterwards — parsing, unit conversion, a superseded sheet.
So this tests the value as it reaches the page (public/data/data.json), against:

  1. its own quote: the quote must state that number, allowing only the unit conversions the
     pipeline itself makes (Pa -> kPa, kg/m3 -> g/cm3) and rounding in the last place;
  2. physical plausibility for the field;
  3. composition totals: oxides near 100%, minerals not above it;
  4. the simulant's other values: a High-Ti label needs titanium, a highland label alumina,
     bulk density must be below particle density, glass content must match the glass row;
  5. its citation: the reference it cites must be one confirmed to name the product.

Writes documentation/value-audit-<date>.json and .md. Nothing is changed.

    python3 scripts/audit_values.py
"""

from __future__ import annotations

import glob
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_value import COLUMN_UNITS, parse_number, to_column_unit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

_NUM = re.compile(r"(?<![A-Za-z0-9.])\d+(?:\.\d+)?")
TEXT_WITH_NUMBERS = {"bulk_density_range", "particle_size_distribution", "magnetic_susceptibility",
                     "angle_of_repose", "particle_morphology"}
DESCRIPTIVE = {"institution", "availability", "lunar_sample_reference", "type", "product_grade", "particle_ruggedness"}
# The conversions the pipeline itself makes when storing a value; anything else is a mismatch.
FACTORS = {"bulk_density": (1.0, 0.001), "cohesion": (1.0, 0.001, 1000.0),
           # a size quoted in mm or cm and stored in µm
           "particle_size_d50": (1.0, 1000.0, 10000.0), "particle_size_mean_um": (1.0, 1000.0, 10000.0),
           "particle_size_distribution": (1.0, 1000.0, 10000.0)}
RANGES = {
    "bulk_density": (0.7, 2.4, "g/cm³"), "density_g_cm3": (2.3, 3.7, "g/cm³"), "specific_gravity": (2.3, 3.7, ""),
    "cohesion": (0.0, 30.0, "kPa"), "friction_angle": (15.0, 65.0, "°"), "particle_size_d50": (1.0, 3000.0, "µm"),
    "particle_size_mean_um": (1.0, 5000.0, "µm"), "glass_content_percent": (0.0, 100.0, "%"),
    "nasa_fom_score": (0.0, 100.0, "%"), "ti_content_percent": (0.0, 20.0, "%"), "ph": (4.0, 12.0, ""),
}


_WORDS = re.compile(r"\b(half|zero|none|nil|absent|fully crystalli[sz]ed|no glass|negligible|too low to (?:measure|make))\b", re.I)
_BACKREF = re.compile(r"\b(same (?:table )?row|as above|see above|ditto)\b", re.I)


def stated_in_words(quote) -> bool:
    """The quote states the value in words ("approximately half", "considered to be zero")."""
    return bool(_WORDS.search(str(quote or "")))


def is_back_reference(quote) -> bool:
    """The quote points at another quote instead of stating the value ("(same row as above)")."""
    return bool(_BACKREF.search(str(quote or ""))) and len(numbers_in(quote)) < 2


def numbers_in(text) -> list[float]:
    """Numbers stated in a text; digits inside formulas and units (SiO2, cm3, x10) are skipped.
    A decimal split by PDF extraction ("5. 6", "0. 09") is read whole."""
    t = re.sub(r"(?<=\d)\. (?=\d)", ".", str(text or ""))
    return [float(m) for m in _NUM.findall(t)]


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(0.005, 0.006 * abs(b))


def _as_number(field: str, stored):
    if field in COLUMN_UNITS:
        return to_column_unit(field, stored)
    p = parse_number(stored)
    return p.value if p else None


def quote_supports(field: str, stored, quote) -> tuple[bool, str]:
    if not (quote or "").strip():
        return False, "no quote on record"
    qn = numbers_in(quote)
    if field == "release_date":
        years = re.findall(r"(?:19|20)\d\d", str(stored))
        ok = bool(years) and all(y in str(quote) for y in years)
        return ok, "" if ok else f"year {stored} not in its quote"
    if field in DESCRIPTIVE:
        return True, "descriptive"
    if field in TEXT_WITH_NUMBERS:
        fs = FACTORS.get(field, (1.0,))
        missing = [n for n in numbers_in(stored) if not any(_close(q * f, n) for q in qn for f in fs)]
        return (not missing), "" if not missing else f"{', '.join(f'{m:g}' for m in missing)} not in its quote"
    x = _as_number(field, stored)
    if x is None:
        return False, f"{stored!r} is not a number"
    for f in FACTORS.get(field, (1.0,)):
        if any(_close(q * f, x) for q in qn):
            return True, ""
    return False, f"{x:g} not stated in its quote (quote gives {', '.join(f'{q:g}' for q in qn[:6]) or 'no number'})"


def implausible(field: str, value) -> str | None:
    if field not in RANGES or value in (None, ""):
        return None
    x = _as_number(field, value)
    if x is None:
        return None
    lo, hi, unit = RANGES[field]
    if not (lo <= x <= hi):
        return f"{x:g} {unit} is outside the plausible range {lo:g}–{hi:g} {unit}".strip()
    return None


def composition_total_problem(kind: str, values: list[float]) -> str | None:
    total = sum(values)
    if kind == "oxide" and not (90.0 <= total <= 103.0):
        return f"oxide total {total:.1f}% (expected 90–103%)"
    if kind == "mineral" and total > 103.0:
        return f"mineral total {total:.1f}% exceeds 100%"
    return None


def cross_field_problems(sim: dict, oxides: dict, minerals: dict) -> list[str]:
    out = []
    lsr = (sim.get("lunar_sample_reference") or "").lower()
    ti, al = oxides.get("TiO2"), oxides.get("Al2O3")
    if ti is not None:
        if "high-ti" in lsr and ti < 4.0:
            out.append(f"labelled {sim['lunar_sample_reference']!r} but TiO2 is {ti:g}%")
        if "low-ti" in lsr and ti > 6.0:
            out.append(f"labelled {sim['lunar_sample_reference']!r} but TiO2 is {ti:g}%")
    if al is not None:
        if "highland" in lsr and al < 18.0:
            out.append(f"labelled {sim['lunar_sample_reference']!r} but Al2O3 is {al:g}%")
        if "mare" in lsr and "highland" not in lsr and al > 26.0:
            out.append(f"labelled {sim['lunar_sample_reference']!r} but Al2O3 is {al:g}%, highland-like")
    bd = to_column_unit("bulk_density", sim["bulk_density"]) if sim.get("bulk_density") not in (None, "") else None
    pd = sim.get("density_g_cm3") or sim.get("specific_gravity")
    if bd is not None and pd and bd >= float(pd):
        out.append(f"bulk density {bd:g} is not below particle density {float(pd):g}")
    g = sim.get("glass_content_percent")
    rows = [v for k, v in minerals.items() if re.search(r"glass|amorphous", k, re.I)]
    if g not in (None, "") and rows and abs(float(g) - sum(rows)) > 1.0:
        out.append(f"glass content {float(g):g}% but the glass row is {sum(rows):g}%")
    return out


def _norm(name: str) -> str:
    n = re.sub(r"[^a-z0-9]", "", (name or "").lower())
    return {"fosterite": "forsterite"}.get(n, n)


def _quotes(root: Path) -> dict:
    """(simulant_id, 'oxide'|'mineral', normalised name) -> quotes readers gave for it."""
    q = defaultdict(list)
    for fp in sorted(glob.glob(str(root / "documentation/provenance-findings-*.json"))):
        try:
            data = json.load(open(fp))
        except json.JSONDecodeError:
            continue
        for g in data.get("groups", []):
            if not g.get("verification"):
                continue
            for r in (g.get("extraction") or {}).get("results", []):
                for v in r.get("new_values", []) + r.get("values", []):
                    f = v.get("field") or ""
                    if ":" in f and v.get("quote"):
                        kind, name = f.split(":", 1)
                        q[(r["simulant_id"], kind, _norm(name))].append(v["quote"])
    for fp in glob.glob(str(root / "documentation/hispansion-sheet-findings-*.json")):
        for s in json.load(open(fp)).get("sheets", []):
            for v in (s.get("reading") or {}).get("values", []):
                f = v.get("field") or ""
                if ":" in f:
                    kind, name = f.split(":", 1)
                    q[(s["simulant_id"], kind, _norm(name))].insert(0, v["quote"])
    return q


def audit(root: Path = ROOT) -> list[dict]:
    d = json.load(open(root / "public/data/data.json"))
    con = sqlite3.connect(root / "lrs.sqlite")
    refs = {r[0]: {"names": r[1], "type": r[2]} for r in con.execute("SELECT reference_id, names_simulant, reference_type FROM references_")}
    sims = {s["simulant_id"]: s for s in d["simulants"]}
    quotes = _quotes(root)
    out: list[dict] = []

    def flag(sid, where, check, severity, detail, reference_id=None, value=None):
        out.append({"simulant_id": sid, "name": sims.get(sid, {}).get("name"), "where": where, "check": check,
                    "severity": severity, "detail": detail, "reference_id": reference_id, "value": value})

    def citation(sid, where, rid):
        r = refs.get(rid)
        if r is None:
            flag(sid, where, "citation", "error", f"cites {rid}, which does not exist", rid)
        elif r["names"] == 0:
            flag(sid, where, "citation", "error", f"cites {rid}, which a reader confirmed does NOT name this product", rid)
        elif r["names"] is None:
            flag(sid, where, "citation", "warn", f"cites {rid}, not yet checked against its document", rid)

    for p in d["property_sources"]:
        sid, field = p["simulant_id"], p["field"]
        s = sims.get(sid)
        if not s or s.get(field) in (None, ""):
            continue
        v = s[field]
        ok, why = quote_supports(field, v, p.get("quote"))
        if not ok and stated_in_words(p.get("quote")):
            flag(sid, field, "stated in words", "warn", f"{v!r} rests on wording, not a number: {p['quote'][:90]!r}", p["reference_id"], v)
        elif not ok:
            flag(sid, field, "quote", "error", why, p["reference_id"], v)
        bad = implausible(field, v)
        if bad:
            flag(sid, field, "plausibility", "error", bad, p["reference_id"], v)
        citation(sid, field, p["reference_id"])

    by_sim = defaultdict(lambda: {"oxide": {}, "mineral": {}})
    for kind, rows, col in (("oxide", d["chemical_compositions"], "value_wt_pct"), ("mineral", d["compositions"], "value_pct")):
        for c in rows:
            sid, name, v = c["simulant_id"], c["component_name"], c[col]
            by_sim[sid][kind][name] = v
            where = f"{kind}:{name}"
            if not (0 <= v <= 100):
                flag(sid, where, "plausibility", "error", f"{v:g}% is outside 0–100%", c.get("reference_id"), v)
            qs = quotes.get((sid, kind, _norm(name)), [])
            if qs and all(is_back_reference(q) for q in qs):
                qs = [q for (s2, k2, _), lst in quotes.items() if s2 == sid and k2 == kind for q in lst if not is_back_reference(q)]
            stated = c.get("value_text") or v
            if not qs:
                flag(sid, where, "quote", "warn", "no reader's quote on record for this row", c.get("reference_id"), v)
            elif not any(quote_supports("composition", stated, q)[0] for q in qs):
                flag(sid, where, "quote", "error", f"{v:g} not stated in the quote the reader gave: {qs[0][:90]!r}", c.get("reference_id"), v)
            if c.get("reference_id"):
                citation(sid, where, c["reference_id"])

    for sid, comp in by_sim.items():
        for kind in ("oxide", "mineral"):
            if comp[kind]:
                prob = composition_total_problem(kind, [x for x in comp[kind].values() if x is not None])
                if prob:
                    flag(sid, f"{kind} table", "total", "warn", prob)
    for sid, s in sims.items():
        for prob in cross_field_problems(s, by_sim[sid]["oxide"], by_sim[sid]["mineral"]):
            flag(sid, "cross-field", "consistency", "warn", prob)
    return out


def main() -> None:
    findings = audit()
    today = date.today().isoformat()
    (ROOT / "documentation" / f"value-audit-{today}.json").write_text(json.dumps(findings, indent=1, ensure_ascii=False, default=str))
    d = json.load(open(ROOT / "public/data/data.json"))
    shown = sum(1 for p in d["property_sources"] if (s := next((x for x in d["simulants"] if x["simulant_id"] == p["simulant_id"]), None)) and s.get(p["field"]) not in (None, ""))
    total = shown + len(d["chemical_compositions"]) + len(d["compositions"])
    sev = Counter(f["severity"] for f in findings)
    by = Counter((f["severity"], f["check"]) for f in findings)
    print(f"values audited: {total} ({shown} properties, {len(d['chemical_compositions'])} oxide rows, {len(d['compositions'])} mineral rows) across {len(d['simulants'])} simulants")
    print(f"findings: {sev.get('error', 0)} errors, {sev.get('warn', 0)} warnings")
    for (s, c), n in sorted(by.items()):
        print(f"   {s:5} {c:12} {n}")
    lines = [f"# Value audit, {today}", "",
             f"Every value the page shows — {total} across {len(d['simulants'])} simulants — tested against its own quote,",
             "physical plausibility, composition totals, the simulant's other values, and its citation.",
             "Nothing was changed. Errors go to an agent to re-read; warnings are for a human.", "",
             "| Severity | Check | Count |", "|---|---|---:|"] + [f"| {s} | {c} | {n} |" for (s, c), n in sorted(by.items())] + [""]
    for sev_name in ("error", "warn"):
        lines += [f"## {sev_name.capitalize()}s", ""]
        for f in sorted((x for x in findings if x["severity"] == sev_name), key=lambda x: (x["name"] or "", x["where"])):
            lines.append(f"- **{f['name']}** ({f['simulant_id']}) `{f['where']}` — {f['check']}: {f['detail']}")
        lines.append("")
    (ROOT / "documentation" / f"value-audit-{today}.md").write_text("\n".join(lines))
    print(f"-> documentation/value-audit-{today}.md")


if __name__ == "__main__":
    main()

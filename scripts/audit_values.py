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


_TI = {"high": re.compile(r"high[- ]?ti(?:tanium)?\b|high titanium", re.I), "low": re.compile(r"low[- ]?ti(?:tanium)?\b|low titanium", re.I)}
# "terrae" and "maria" are the Latin names for highlands and mare that some papers use.
_TERRAIN = {"highland": re.compile(r"highland|terra(?:e|e-type)?\b|terrae", re.I), "mare": re.compile(r"\bmare\b|maria\b|maria-type", re.I)}
# Apollo sample numbers: 10xxx Apollo 11, 12xxx 12, 14xxx 14, 15xxx 15, 6xxxx 16, 7xxxx 17.
_APOLLO = [(re.compile(r"\b10\d{3}\b"), "11"), (re.compile(r"\b12\d{3}\b"), "12"), (re.compile(r"\b14\d{3}\b"), "14"),
           (re.compile(r"\b15\d{3}\b"), "15"), (re.compile(r"\b6\d{4}\b"), "16"), (re.compile(r"\b7\d{4}\b"), "17")]


def label_supported(label: str, quote: str) -> bool:
    """A lunar-analogue label is supported when its quote states the same titanium class and
    terrain, and does not state the opposite titanium class."""
    lab, q = (label or "").lower(), quote or ""
    for cls, other in (("high", "low"), ("low", "high")):
        if f"{cls}-ti" in lab or f"{cls} ti" in lab:
            if not _TI[cls].search(q) or (_TI[other].search(q) and not _TI[cls].search(q)):
                return False
    for terrain, pat in _TERRAIN.items():
        if terrain in lab and not pat.search(q):
            if terrain == "mare" and (_TI["high"].search(q) or _TI["low"].search(q)):
                continue          # "high-Ti" / "low-Ti" alone implies a mare analogue
            return False
    m = re.search(r"apollo\s*(\d+)", lab)
    if m:
        return (re.search(rf"apollo[\s-]*{m.group(1)}\b", q, re.I) is not None
                or any(pat.search(q) and mission == m.group(1) for pat, mission in _APOLLO))
    if lab.strip() in ("mixed", "intermediate", "mixed mare/highland"):
        return bool(_TERRAIN["highland"].search(q) and _TERRAIN["mare"].search(q))
    if "highland" not in lab and "mare" not in lab and "-ti" not in lab:
        return any(w in q.lower() for w in re.findall(r"[a-z]{4,}", lab)) or not lab
    return True


_ALIASES = {"orbitec": "orbital technologies", "sciences": "science", "zybek": "zybeck", "usgs": "geological survey",
            "msfc": "marshall"}


def institution_supported(institution: str, quote: str) -> bool:
    """At least half the distinctive words of the institution's name appear in its quote
    (the quote may name only one of two partners, or abbreviate), allowing known aliases."""
    common = {"university", "institute", "institution", "center", "centre", "the", "and", "for", "technical",
              "technology", "research", "school", "national", "academy", "of"}
    words = [w for w in re.findall(r"[A-Za-zÀ-ÿ]{3,}", institution or "") if w.lower() not in common]
    q = (quote or "").lower()
    if re.search(r"[\u4e00-\u9fff]", q):
        return True                      # a Chinese-language quote; not checkable word by word
    if not words:
        return (institution or "").lower() in q
    hits = sum(1 for w in words if w.lower() in q or _ALIASES.get(w.lower(), "\x00") in q or w.lower().rstrip("s") in q)
    return hits * 2 >= len(words)


# Also the forms sources print that are not single oxides but are faithful: SO2 (CUMT-1's paper),
# combined alkalis and total iron as printed (TLS-01's).
AS_PRINTED = {"SO2", "Na2O+K2O", "FeO Total"}
OXIDES = AS_PRINTED | {"SiO2", "TiO2", "Al2O3", "Fe2O3", "Fe2O3T", "FeO", "FeOT", "MnO", "MgO", "CaO", "Na2O", "K2O", "P2O5",
          "Cr2O3", "SO3", "NiO", "ZnO", "SrO", "BaO", "V2O5", "CoO", "CuO", "ZrO2", "Cl", "S", "LOI", "H2O", "CO2"}
MINERAL_MISSPELLINGS = {"fosterite": "forsterite", "plagiclase": "plagioclase", "pyroxine": "pyroxene",
                        "ilminite": "ilmenite", "olivene": "olivine", "anorthosite ": "anorthosite"}


def component_name_problem(kind: str, name: str) -> str | None:
    if kind == "oxide":
        return None if name in OXIDES else f"{name!r} is not an oxide formula this table expects"
    if "_" in name or name != name.strip():
        return f"{name!r} is a code, not a display name"
    if name.lower() in MINERAL_MISSPELLINGS:
        return f"{name!r} is a misspelling of {MINERAL_MISSPELLINGS[name.lower()]!r}"
    if re.fullmatch(r"(?:SiO2|TiO2|Al2O3|FeO|Fe2O3|MgO|CaO|Na2O|K2O)", name):
        return f"{name!r} is an oxide in the mineral table"
    return None


def shared_values(rows) -> dict:
    """(field, value, reference) stated for three or more simulants: possibly a family-level
    statement copied onto each member. rows: (simulant_id, field, value, reference_id)."""
    by = defaultdict(list)
    for sid, field, value, rid in rows:
        by[(field, str(value), rid)].append(sid)
    return {k: sorted(v) for k, v in by.items() if len(v) >= 3}


def _title_key(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\[.*?\]", "", (t or "").lower()))


def duplicate_references(refs: list[dict]) -> list[list[str]]:
    """Groups of reference ids that are the same document twice in one simulant's list."""
    groups = []
    by_sim = defaultdict(list)
    for r in refs:
        by_sim[r["simulant_id"]].append(r)
    for sid, rs in by_sim.items():
        seen: dict[str, list[str]] = defaultdict(list)
        for r in rs:
            if r.get("doi") and r["doi"].strip():
                key = "doi:" + r["doi"].strip().lower()
            else:
                key = "t:" + _title_key(r.get("title") or r.get("reference_text") or "")
                if len(key) < 17:          # too short a title to call two entries the same document
                    continue
            seen[key].append(r["reference_id"])
        groups += [ids for ids in seen.values() if len(ids) > 1]
    return groups


def vocabulary_variants(values) -> list[list[str]]:
    """Spellings of one label that differ only in case, plural or spacing ("Highland"/"Highlands")."""
    by = defaultdict(set)
    for v in values:
        if v:
            by[re.sub(r"s\b", "", re.sub(r"[^a-z0-9]", "", v.lower()))].add(v)
    return [sorted(v) for v in by.values() if len(v) > 1]


def link_verdict(status) -> str:
    if status is None:
        return "unreachable"
    if status in (401, 403, 405, 406, 429, 999):
        return "blocked"
    return "ok" if status < 400 else "broken"


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


# Findings checked by hand against the source document, with what was found.
VERIFIED_BY_HAND = {
    ("S060", "particle_size_distribution"): "all 30 numbers occur in the OPR General Lunar Simulants data sheet (the quote was shortened)",
}


def audit(root: Path = ROOT) -> list[dict]:
    d = json.load(open(root / "public/data/data.json"))
    con = sqlite3.connect(root / "lrs.sqlite")
    refs = {r[0]: {"names": r[1], "type": r[2]} for r in con.execute("SELECT reference_id, names_simulant, reference_type FROM references_")}
    sims = {s["simulant_id"]: s for s in d["simulants"]}
    quotes = _quotes(root)
    out: list[dict] = []

    def flag(sid, where, check, severity, detail, reference_id=None, value=None):
        out.append({"simulant_id": sid, "name": sims.get(sid, {}).get("name") if sid else "(page)", "where": where, "check": check,
                    "severity": severity, "detail": detail, "reference_id": reference_id, "value": value})

    def citation(sid, where, rid):
        r = refs.get(rid)
        if r is None:
            flag(sid, where, "citation", "error", f"cites {rid}, which does not exist", rid)
        elif r["names"] == 0:
            flag(sid, where, "citation", "error", f"cites {rid}, which a reader confirmed does NOT name this product", rid)
        elif r["names"] is None:
            flag(sid, where, "citation", "warn", f"cites {rid}, not yet checked against its document", rid)

    ref_owner = {r["reference_id"]: r["simulant_id"] for r in d["references"]}
    for p in d["property_sources"]:
        sid, field = p["simulant_id"], p["field"]
        s = sims.get(sid)
        if not s or s.get(field) in (None, ""):
            continue
        v = s[field]
        if ref_owner.get(p["reference_id"]) not in (None, sid):
            flag(sid, field, "citation", "error", f"cites {p['reference_id']}, which belongs to another simulant's list", p["reference_id"], v)
        if field == "lunar_sample_reference" and not label_supported(str(v), p.get("quote") or ""):
            flag(sid, field, "label", "error", f"{v!r} is not what its quote says: {(p.get('quote') or '')[:100]!r}", p["reference_id"], v)
        if field == "institution" and not institution_supported(str(v), p.get("quote") or ""):
            flag(sid, field, "institution", "warn", f"{v!r} not named in its quote: {(p.get('quote') or '')[:100]!r}", p["reference_id"], v)
        ok, why = quote_supports(field, v, p.get("quote"))
        if not ok and (sid, field) in VERIFIED_BY_HAND:
            ok = True
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
            bad_name = component_name_problem(kind, name)
            if bad_name:
                flag(sid, where, "component name", "warn", bad_name, c.get("reference_id"), v)
            if c.get("reference_id") and ref_owner.get(c["reference_id"]) not in (None, sid):
                flag(sid, where, "citation", "error", f"cites {c['reference_id']}, which belongs to another simulant's list", c["reference_id"], v)
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
    for f in d.get("figures_of_merit", []):
        sid = f["simulant_id"]
        where = f"FoM {f['property_label']} vs {f.get('reference_sample') or '—'}"
        if not quote_supports("composition", f.get("score_text") or f["score"], f.get("quote") or "")[0]:
            flag(sid, where, "quote", "error", f"FoM {f['score']:g} not stated in its quote: {(f.get('quote') or '')[:90]!r}", f["reference_id"], f["score"])
        if ref_owner.get(f["reference_id"]) not in (None, sid):
            flag(sid, where, "citation", "error", f"cites {f['reference_id']}, which belongs to another simulant's list", f["reference_id"], f["score"])
        citation(sid, where, f["reference_id"])

    for sid, s in sims.items():
        for prob in cross_field_problems(s, by_sim[sid]["oxide"], by_sim[sid]["mineral"]):
            flag(sid, "cross-field", "consistency", "warn", prob)

    rows = [(p["simulant_id"], p["field"], sims[p["simulant_id"]].get(p["field"]), p["reference_id"])
            for p in d["property_sources"] if p["simulant_id"] in sims and sims[p["simulant_id"]].get(p["field"]) not in (None, "")
            and p["field"] not in DESCRIPTIVE and p["field"] not in ("release_date",)]
    for (field, value, rid), members in shared_values(rows).items():
        names = ", ".join(sims[m]["name"] for m in members)
        flag(members[0], field, "shared value", "warn",
             f"{field} = {value} for {len(members)} simulants from one document {rid} ({names}): a family figure on each member?", rid, value)

    sourced = {(p["simulant_id"], p["field"]) for p in d["property_sources"]}
    for sid, s in sims.items():
        for field in ("availability", "release_date", "lunar_sample_reference", "institution"):
            if s.get(field) not in (None, "") and (sid, field) not in sourced:
                flag(sid, field, "unsourced", "info", f"shown without a source: {s[field]!r}", None, s[field])
    for e in d.get("simulant_extra", []):
        if e.get("grain_size_mm") not in (None, "") and e["simulant_id"] in sims:
            flag(e["simulant_id"], "grain_size_mm", "unsourced", "warn",
                 f"grain size {e['grain_size_mm']} mm is shown among the physical properties with no source (Gasteiner database)", None, e["grain_size_mm"])

    # Reference hygiene: what the numbered list under each simulant shows.
    for ids in duplicate_references(d["references"]):
        sid = ref_owner.get(ids[0])
        flag(sid, "references", "duplicate", "warn", f"the same document is listed {len(ids)} times: {', '.join(ids)}", ids[0])
    for r in d["references"]:
        if r.get("names_simulant") == 0:
            flag(r["simulant_id"], "references", "not about it", "warn",
                 f"{r['reference_id']} is listed although a reader confirmed it does not name this product", r["reference_id"])
        if not (r.get("title") or r.get("reference_text") or r.get("doi") or r.get("url")):
            flag(r["simulant_id"], "references", "empty entry", "warn", f"{r['reference_id']} has no title, citation, DOI or link", r["reference_id"])
        y = r.get("year")
        if isinstance(y, int) and not (1950 <= y <= date.today().year):
            flag(r["simulant_id"], "references", "year", "warn", f"{r['reference_id']} has year {y}", r["reference_id"])
        if re.search(r"\[=|existing ref|NEW\d|temp id", f"{r.get('title') or ''} {r.get('reference_text') or ''}"):
            flag(r["simulant_id"], "references", "reader note", "warn", f"{r['reference_id']} shows a reader's working note", r["reference_id"])
    for field in ("lunar_sample_reference", "availability", "type"):
        for variants in vocabulary_variants([s.get(field) for s in d["simulants"]]):
            flag(None, field, "vocabulary", "warn", f"one label spelled {len(variants)} ways: {' / '.join(variants)}")

    for L in d.get("lunar_reference", []):
        chem = L.get("chemical_composition") or {}
        if isinstance(chem, str):
            try: chem = json.loads(chem)
            except json.JSONDecodeError: chem = {}
        total = sum(v for v in chem.values() if isinstance(v, (int, float)))
        srcs = L.get("sources") or []
        if chem and not (90 <= total <= 103):
            flag(None, f"lunar reference {L.get('mission')}", "total", "warn", f"Apollo comparison chemistry totals {total:.1f}%")
        if not srcs:
            flag(None, f"lunar reference {L.get('mission')}", "unsourced", "warn", "Apollo comparison data shown with no source")
    for site in d.get("sites", []):
        lat, lon = site.get("lat"), site.get("lon")
        if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180) or (lat == 0 and lon == 0):
            flag(site.get("simulant_id"), "map site", "site", "warn", f"implausible map position {lat}, {lon} for {site.get('site_name')!r}")
    return out


def links(root: Path = ROOT) -> list[dict]:
    """Every link the page shows, requested once: data sheets, source lines, references, vendors."""
    import concurrent.futures, urllib.request, urllib.error
    d = json.load(open(root / "public/data/data.json"))
    names = {s["simulant_id"]: s["name"] for s in d["simulants"]}
    targets = []
    for s in d["simulants"]:
        for f in ("datasheet_url", "composition_source_url"):
            if (s.get(f) or "").startswith("http"):
                targets.append((s["simulant_id"], f, s[f]))
    for r in d["references"]:
        u = r.get("url") if (r.get("url") or "").startswith("http") else (f"https://doi.org/{r['doi'].strip()}" if r.get("doi") else None)
        if u:
            targets.append((r["simulant_id"], f"reference {r['reference_id']}", u))
    for pi in d.get("purchase_info", []):
        if (pi.get("url") or "").startswith("http"):
            targets.append((pi["simulant_id"], "vendor link", pi["url"]))
    seen = {}

    def fetch(u):
        for method in ("HEAD", "GET"):
            try:
                req = urllib.request.Request(u, method=method, headers={"User-Agent": "Mozilla/5.0 (Macintosh) lrs-link-check"})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    return resp.status
            except urllib.error.HTTPError as e:
                if method == "HEAD" and e.code in (403, 405, 400, 501):
                    continue
                return e.code
            except Exception:
                if method == "HEAD":
                    continue
                return None
        return None

    urls = sorted({t[2] for t in targets})
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        for u, st in zip(urls, ex.map(fetch, urls)):
            seen[u] = st
    out = []
    for sid, where, u in targets:
        v = link_verdict(seen.get(u))
        if v in ("broken", "unreachable"):
            out.append({"simulant_id": sid, "name": names.get(sid), "where": where, "check": "link", "severity": "error" if v == "broken" else "warn",
                        "detail": f"{v} ({seen.get(u)}): {u}", "reference_id": None, "value": u})
    return out


def main() -> None:
    findings = audit()
    if "--no-links" not in sys.argv:
        findings += links()
    today = date.today().isoformat()
    (ROOT / "documentation" / f"value-audit-{today}.json").write_text(json.dumps(findings, indent=1, ensure_ascii=False, default=str))
    d = json.load(open(ROOT / "public/data/data.json"))
    shown = sum(1 for p in d["property_sources"] if (s := next((x for x in d["simulants"] if x["simulant_id"] == p["simulant_id"]), None)) and s.get(p["field"]) not in (None, ""))
    total = shown + len(d["chemical_compositions"]) + len(d["compositions"])
    sev = Counter(f["severity"] for f in findings)
    by = Counter((f["severity"], f["check"]) for f in findings)
    print(f"values audited: {total} ({shown} properties, {len(d['chemical_compositions'])} oxide rows, {len(d['compositions'])} mineral rows) across {len(d['simulants'])} simulants")
    print(f"findings: {sev.get('error', 0)} errors, {sev.get('warn', 0)} warnings, {sev.get('info', 0)} for information")
    for (s, c), n in sorted(by.items()):
        print(f"   {s:5} {c:12} {n}")
    lines = [f"# Value audit, {today}", "",
             f"Every value the page shows — {total} across {len(d['simulants'])} simulants — tested against its own quote,",
             "physical plausibility, composition totals, the simulant's other values, and its citation.",
             "Nothing was changed. Errors go to an agent to re-read; warnings are for a human.", "",
             "| Severity | Check | Count |", "|---|---|---:|"] + [f"| {s} | {c} | {n} |" for (s, c), n in sorted(by.items())] + [""]
    for sev_name in ("error", "warn", "info"):
        lines += [f"## {sev_name.capitalize()}s", ""]
        for f in sorted((x for x in findings if x["severity"] == sev_name), key=lambda x: (x["name"] or "", x["where"])):
            lines.append(f"- **{f['name']}** ({f['simulant_id']}) `{f['where']}` — {f['check']}: {f['detail']}")
        lines.append("")
    (ROOT / "documentation" / f"value-audit-{today}.md").write_text("\n".join(lines))
    print(f"-> documentation/value-audit-{today}.md")


if __name__ == "__main__":
    main()

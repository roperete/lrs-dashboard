#!/usr/bin/env python3
"""Task 7.2: group simulants for the agent verification run.

Each group is a set of simulants that share documents, so one agent can open a document
once and read for all of them. Inputs: the library index (which documents name which
simulants), the references_ table (what we cite), and the database values to verify.
Verified-by-sheet simulants are included too, so agents can re-read the sheets for
per-value locations (owner preference: extraction is agent work).

Output: documentation/agent-groups-<date>.json, a list of
    {key, simulant_ids, documents: [local paths], references: [...], values: {...}}
sized to at most MAX_SIMULANTS per group.

Usage:  python3 scripts/build_groups.py
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"
SOURCES = Path("/Volumes/Extreme SSD/Spring - Forest on the moon/DIRT/Sources")
MAX_SIMULANTS = 6
MAX_DOCS_PER_SIMULANT = 8
# The first two runs died on the session limit: an agent opening 30 documents costs far
# more than one opening 10. Cited references with a local copy come first, then the
# library documents that name the group's simulants most often, up to this many.
MAX_DOCS_PER_GROUP = 12

SCALAR_FIELDS = [
    "bulk_density", "cohesion", "friction_angle", "specific_gravity", "density_g_cm3",
    "particle_size_d50", "particle_size_distribution", "particle_morphology", "particle_ruggedness",
    "glass_content_percent", "nasa_fom_score", "ti_content_percent",
    "ph", "angle_of_repose", "particle_size_mean_um", "bulk_density_range", "magnetic_susceptibility",
    "release_date", "availability", "lunar_sample_reference", "institution",
]


def already_read(docs_dir: Path) -> set[str]:
    """Simulant ids a reader-checker pair has already been through, from the findings files.

    A value no document states never gains a source row, so "not fully sourced" is not a
    reason to read a simulant again — what is left there is an owner decision. Having been
    read is what marks the reading done.
    """
    ids: set[str] = set()
    for f in sorted(docs_dir.glob("provenance-findings-*.json")):
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError:
            print(f"warning: {f.name} is not readable JSON; ignored")
            continue
        for g in data.get("groups", []):
            for r in (g.get("extraction") or {}).get("results", []):
                if r.get("simulant_id"):
                    ids.add(r["simulant_id"])
    return ids


def unfinished_reason(sim: dict, refs: list[dict], chem: list[dict], mins: list[dict],
                      sourced: set[str]) -> str | None:
    """Why this simulant still needs a reader, or None when all three tests pass for it.

    Test 1 and 2: every reference on file has been checked against its document
    (names_simulant set either way); a simulant with no reference at all fails test 1 and
    needs a reader to establish the product exists. Test 3: every composition row cites a
    document and every stored value has a property_sources row.
    """
    if not refs:
        return "no reference on file"
    unchecked = sum(1 for r in refs if r.get("names_simulant") is None)
    if unchecked:
        return f"{unchecked} reference{'s' if unchecked > 1 else ''} unchecked"
    uncited = sum(1 for c in chem + mins if not c.get("reference_id"))
    if uncited:
        return f"{uncited} composition row{'s' if uncited > 1 else ''} without a citation"
    missing = sum(1 for f in SCALAR_FIELDS if sim.get(f) not in (None, "") and f not in sourced)
    if missing:
        return f"{missing} value{'s' if missing > 1 else ''} without a source"
    return None


def latest_index() -> dict:
    files = sorted((ROOT / "documentation").glob("library-simulant-index-*.json"))
    return json.loads(files[-1].read_text())


def family_key(name: str) -> str:
    """JSC-1, JSC-1A, JSC-1AF share a family; NU-LHT-2M and NU-LHT-1D too."""
    m = re.match(r"^([A-Za-z]+(?:-[A-Za-z]+)?)[-\s]?\d", name)
    return (m.group(1) if m else name).upper()


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-simulant", action="store_true",
                    help="one unit per simulant (owner preference 2026-09-22) instead of family/institution groups")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--skip-finished", action="store_true",
                    help="leave out simulants whose references are all checked and whose every value is sourced")
    ap.add_argument("--exclude", default="", help="comma-separated simulant ids to leave out (e.g. one already running)")
    ap.add_argument("--skip-read", action="store_true",
                    help="leave out simulants a reader-checker pair has already been through")
    ap.add_argument("--max-simulants", type=int, default=None, help="override the group size")
    cli = ap.parse_args()
    global MAX_SIMULANTS
    if cli.per_simulant:
        MAX_SIMULANTS = 1
    if cli.max_simulants:
        MAX_SIMULANTS = cli.max_simulants

    index = latest_index()
    docs_for = {name: docs for name, docs in index["simulants"].items()}
    # One mention of a short name: a candidate the reader judges, never evidence on its own.
    weak_for = {name: docs for name, docs in index.get("simulants_weak", {}).items()}

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    sims = [dict(r) for r in con.execute("SELECT * FROM simulants ORDER BY simulant_id")]
    refs = defaultdict(list)
    for r in con.execute("SELECT * FROM references_ ORDER BY reference_id"):
        refs[r["simulant_id"]].append(dict(r))
    chem = defaultdict(list)
    for r in con.execute("SELECT * FROM chemical_compositions ORDER BY composition_id"):
        chem[r["simulant_id"]].append(dict(r))
    mins = defaultdict(list)
    for r in con.execute("SELECT * FROM mineral_compositions ORDER BY composition_id"):
        mins[r["simulant_id"]].append(dict(r))
    sourced = defaultdict(set)
    for r in con.execute("SELECT simulant_id, field FROM property_sources"):
        sourced[r["simulant_id"]].add(r["field"])
    con.close()

    excluded = {x.strip() for x in cli.exclude.split(",") if x.strip()}
    if excluded:
        sims = [s for s in sims if s["simulant_id"] not in excluded]
        print(f"excluded by request: {', '.join(sorted(excluded))}")
    if cli.skip_read:
        read = already_read(ROOT / "documentation")
        before = len(sims)
        sims = [s for s in sims if s["simulant_id"] not in read]
        print(f"skipping {before - len(sims)} simulant(s) already read by an agent pair")
    if cli.skip_finished:
        keep, done = [], []
        for s in sims:
            sid = s["simulant_id"]
            why = unfinished_reason(s, refs.get(sid, []), chem.get(sid, []), mins.get(sid, []), sourced.get(sid, set()))
            (keep if why else done).append(s)
        print(f"skipping {len(done)} simulant(s) with nothing left to verify")
        sims = keep

    # mention counts per (document, simulant) so documents can be ranked
    mentions: dict[str, dict[str, int]] = defaultdict(dict)
    for doc, meta in index["documents"].items():
        for name, n in meta.get("simulants", {}).items():
            mentions[name][doc] = n

    def ranked_docs(s: dict) -> list[str]:
        """Documents worth opening for this simulant: every cited reference with a local copy,
        then library documents that name it, most mentions first, then the weak candidates —
        a single mention of a short name, which for six products is the only document there
        is. Capped, so an agent is not handed thirty documents to open."""
        cited = [r.get("local_path") for r in refs.get(s["simulant_id"], []) if r.get("local_path")]
        by_mentions = sorted(mentions.get(s["name"], {}).items(), key=lambda kv: -kv[1])
        weak = weak_for.get(s["name"], [])
        out: list[str] = []
        for d in cited + [d for d, _ in by_mentions] + weak:
            if d and d not in out:
                out.append(d)
            if len(out) >= MAX_DOCS_PER_SIMULANT:
                break
        return out

    # 1) cluster by family name; 2) fold small buckets into their institution; 3) fold the
    #    remaining singletons by country so that agents are not spawned one per simulant
    buckets: dict[str, list[dict]] = defaultdict(list)
    for s in sims:
        buckets[(s["name"] if cli.per_simulant else family_key(s["name"]))].append(s)
    small = {} if cli.per_simulant else {k: v for k, v in buckets.items() if len(v) <= 2}
    for k in small:
        del buckets[k]
    by_inst: dict[str, list[dict]] = defaultdict(list)
    for members in small.values():
        for s in members:
            inst = re.sub(r"[^A-Za-z]+", "", (s.get("institution") or "").split("/")[0])[:18].upper() or "NOINST"
            by_inst["INST:" + inst].append(s)
    for k, v in list(by_inst.items()):
        if len(v) == 1:
            s = v[0]
            country = re.sub(r"[^A-Za-z]+", "", s.get("country_code") or "XX")[:12].upper()
            by_inst["COUNTRY:" + country].append(s)
            del by_inst[k]
    buckets.update(by_inst)

    groups = []
    for key, members in sorted(buckets.items()):
        for i in range(0, len(members), MAX_SIMULANTS):
            chunk = members[i:i + MAX_SIMULANTS]
            ids = [s["simulant_id"] for s in chunk]
            cited_first = []
            others = []
            for s in chunk:
                cited = {r.get("local_path") for r in refs.get(s["simulant_id"], []) if r.get("local_path")}
                for d in ranked_docs(s):
                    target = cited_first if d in cited else others
                    if d not in cited_first and d not in others:
                        target.append(d)
            documents = (cited_first + others)[:MAX_DOCS_PER_GROUP]
            # What the group still has to establish, not what it already holds: a simulant
            # whose values are all sourced and whose references are all checked adds
            # nothing, so the run reaches the least-verified material first.
            priority = 0
            for s in chunk:
                sid = s["simulant_id"]
                done = sourced.get(sid, set())
                priority += sum(1 for f in SCALAR_FIELDS if s.get(f) not in (None, "") and f not in done)
                priority += sum(1 for c in chem.get(sid, []) + mins.get(sid, []) if not c.get("reference_id"))
                priority += sum(1 for r in refs.get(sid, []) if r.get("names_simulant") is None)
                if not refs.get(sid):
                    priority += 5          # existence itself is unestablished
                if s.get("composition_status") == "withheld_unverified":
                    priority += 10         # data on record that the page is hiding
            group = {
                "key": f"{key}" + (f"-{i // MAX_SIMULANTS + 1}" if len(members) > MAX_SIMULANTS else ""),
                "simulant_ids": ids,
                "simulants": [
                    {
                        "simulant_id": s["simulant_id"], "name": s["name"], "institution": s.get("institution"),
                        "composition_status": s.get("composition_status"),
                        "scalars": {f: s.get(f) for f in SCALAR_FIELDS if s.get(f) not in (None, "")},
                        "already_sourced_fields": sorted(sourced.get(s["simulant_id"], [])),
                        "oxides": [{"composition_id": c["composition_id"], "name": c["component_name"], "wt_pct": c["value_wt_pct"], "reference_id": c.get("reference_id")} for c in chem.get(s["simulant_id"], [])],
                        "minerals": [{"composition_id": m["composition_id"], "name": m["component_name"], "pct": m["value_pct"], "reference_id": m.get("reference_id")} for m in mins.get(s["simulant_id"], [])],
                        "references": [
                            {"reference_id": r["reference_id"], "type": r.get("reference_type"),
                             "citation": (r.get("reference_text") or r.get("title") or "")[:300],
                             "doi": r.get("doi"), "url": r.get("url"), "local_path": r.get("local_path")}
                            for r in refs.get(s["simulant_id"], [])
                        ],
                        "library_documents_naming_it": ranked_docs(s),
                        "library_documents_naming_it_total": len(docs_for.get(s["name"], [])),
                        # A single mention of a short name: open it, but decide for yourself
                        # whether the sentence is about this product.
                        "library_documents_possibly_naming_it": weak_for.get(s["name"], []),
                    }
                    for s in chunk
                ],
                "documents": documents,
                "documents_available": len(cited_first) + len(others),
                "priority": priority,
            }
            groups.append(group)

    # highest-value groups first, so a run cut short by the session limit still did the
    # simulants that carry the most unverified data
    groups.sort(key=lambda g: -g["priority"])

    default_name = f"agent-{'units' if cli.per_simulant else 'groups'}-{date.today().isoformat()}.json"
    out = cli.out or (ROOT / "documentation" / default_name)
    out.write_text(json.dumps(groups, indent=1))
    n_docs = sum(len(g["documents"]) for g in groups)
    print(f"{len(groups)} groups covering {sum(len(g['simulant_ids']) for g in groups)} simulants; {n_docs} document slots")
    sizes = defaultdict(int)
    for g in groups:
        sizes[len(g["simulant_ids"])] += 1
    print("group sizes:", dict(sorted(sizes.items())))
    print("groups with no library document at all:", [g["key"] for g in groups if not g["documents"]])
    print(f"-> {out}")


if __name__ == "__main__":
    main()

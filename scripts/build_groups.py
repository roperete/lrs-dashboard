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

SCALAR_FIELDS = [
    "bulk_density", "cohesion", "friction_angle", "specific_gravity", "density_g_cm3",
    "particle_size_d50", "particle_size_distribution", "particle_morphology", "particle_ruggedness",
    "glass_content_percent", "nasa_fom_score", "ti_content_percent",
    "ph", "angle_of_repose", "particle_size_mean_um", "bulk_density_range", "magnetic_susceptibility",
    "release_date", "availability", "lunar_sample_reference", "institution",
]


def latest_index() -> dict:
    files = sorted((ROOT / "documentation").glob("library-simulant-index-*.json"))
    return json.loads(files[-1].read_text())


def family_key(name: str) -> str:
    """JSC-1, JSC-1A, JSC-1AF share a family; NU-LHT-2M and NU-LHT-1D too."""
    m = re.match(r"^([A-Za-z]+(?:-[A-Za-z]+)?)[-\s]?\d", name)
    return (m.group(1) if m else name).upper()


def main() -> None:
    index = latest_index()
    docs_for = {name: docs for name, docs in index["simulants"].items()}

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

    # mention counts per (document, simulant) so documents can be ranked
    mentions: dict[str, dict[str, int]] = defaultdict(dict)
    for doc, meta in index["documents"].items():
        for name, n in meta.get("simulants", {}).items():
            mentions[name][doc] = n

    def ranked_docs(s: dict) -> list[str]:
        """Documents worth opening for this simulant: every cited reference with a local copy,
        then library documents that name it, most mentions first, capped."""
        cited = [r.get("local_path") for r in refs.get(s["simulant_id"], []) if r.get("local_path")]
        by_mentions = sorted(mentions.get(s["name"], {}).items(), key=lambda kv: -kv[1])
        out: list[str] = []
        for d in cited + [d for d, _ in by_mentions]:
            if d and d not in out:
                out.append(d)
            if len(out) >= MAX_DOCS_PER_SIMULANT:
                break
        return out

    # 1) cluster by family name; 2) fold small buckets into their institution; 3) fold the
    #    remaining singletons by country so that agents are not spawned one per simulant
    buckets: dict[str, list[dict]] = defaultdict(list)
    for s in sims:
        buckets[family_key(s["name"])].append(s)
    small = {k: v for k, v in buckets.items() if len(v) <= 2}
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
            documents = []
            for s in chunk:
                for d in ranked_docs(s):
                    if d not in documents:
                        documents.append(d)
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
                    }
                    for s in chunk
                ],
                "documents": documents,
            }
            groups.append(group)

    out = ROOT / "documentation" / f"agent-groups-{date.today().isoformat()}.json"
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

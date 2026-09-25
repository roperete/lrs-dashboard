#!/usr/bin/env python3
"""Move the lunar landing sites from src/lunarData.ts into lrs.sqlite (2026-09-25).

The sites were hard-coded in the page, so none of their values could carry a source. They
now live in `lunar_sites`, and every value needs a `lunar_sources` row to be exported. The
values as the page showed them before verification are kept in
documentation/lunar-sites-before-verification-2026-09-25.json.

Idempotent: a site already in the table is left alone.

Usage:  python3 scripts/migrate_lunar_sites.py [--from-json sites.json]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from pathlib import Path

from provenance import ensure_provenance_schema

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"
TS = ROOT / "src" / "lunarData.ts"
RECORD = ROOT / "documentation" / "lunar-sites-before-verification-2026-09-25.json"
GEO = ("bulk_density", "friction_angle", "cohesion", "bearing_capacity")


def sites_from_ts() -> list[dict]:
    script = f"import {{ lunarSites }} from {json.dumps(str(TS))}; console.log(JSON.stringify(lunarSites));"
    out = subprocess.run([str(ROOT / "node_modules" / ".bin" / "tsx"), "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def migrate(con: sqlite3.Connection, sites: list[dict]) -> int:
    ensure_provenance_schema(con)
    n = 0
    for s in sites:
        g = s.get("geotechnical") or {}
        cur = con.execute(
            "INSERT OR IGNORE INTO lunar_sites (site_id, name, mission, programme, date, lat, lng, samples_returned, description, "
            + ", ".join(GEO) + ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (s["id"], s["name"], s["mission"], s["type"], s.get("date"), s.get("lat"), s.get("lng"), s.get("samples_returned"),
             s.get("description"), *(g.get(k) for k in GEO)))
        n += cur.rowcount
    con.commit()
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-json", type=Path)
    args = ap.parse_args()
    sites = json.loads(args.from_json.read_text()) if args.from_json else sites_from_ts()
    if not RECORD.exists():
        RECORD.write_text(json.dumps(sites, indent=1, ensure_ascii=False) + "\n")
    con = sqlite3.connect(DB)
    print(f"{migrate(con, sites)} site(s) added; {con.execute('SELECT count(*) FROM lunar_sites').fetchone()[0]} in the table")


if __name__ == "__main__":
    main()

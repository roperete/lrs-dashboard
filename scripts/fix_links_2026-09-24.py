#!/usr/bin/env python3
"""Dead links on the page, 2026-09-24 (found by scripts/audit_values.py).

  * Space Resource Technologies renamed its product pages; each simulant is matched to the
    current page whose title carries its exact product code.
  * Off Planet Research moved its catalogue to /simulants. Products the new page lists keep a
    link there; those it does not list (the W variants, OPRFLCROSS2) lose the link rather
    than point at a page that does not sell them.
  * The ESRIC knowledge base (knowledge.esric.lu) no longer resolves; its simulant catalogue,
    which the readers worked from, is linked at the Wayback Machine's copy of 25 Sep 2025.
  * astroport.us no longer resolves: LCATS-1's vendor link is removed.
  * R080 (TLS-01) cited a DOI that was never registered; the paper is a Sciforum conference
    paper and prints its own address, which is used instead.

Idempotent; logs to documentation/link-repair-log-2026-09-24.json.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "documentation" / "link-repair-log-2026-09-24.json"

SRT = {  # product code -> current page (the page title carries the code)
    "LHS-1E": "https://spaceresourcetech.com/products/lhs-1e-simplified-lunar-highlands-simulant",
    "LHS-2": "https://spaceresourcetech.com/products/lunar-highlands-simulant-lhs-2",
    "LHS-2E": "https://spaceresourcetech.com/products/lunar-highland-lhs-2e-simulant",
    "LMS-1D": "https://spaceresourcetech.com/products/lms-1d",
    "LMS-1E": "https://spaceresourcetech.com/products/standard-basalt-simulant",
    "LMS-2": "https://spaceresourcetech.com/products/lunar-mare-lms-2-high-fidelity-simulant",
    "LSP-2": "https://spaceresourcetech.com/products/lunar-south-pole-simulant-lsp-2",
}
OPR_OLD = "https://www.offplanetresearch.com/simulants-feedstocks-and-additives"
OPR_NEW = "https://www.offplanetresearch.com/simulants"
OPR_LISTED = {"OPRFLCROSS1", "OPRH2N", "OPRH3N", "OPRH4N", "OPRL2N", "OPRL2NT", "OPR Agglutinate"}
ESRIC_OLD = "http://knowledge.esric.lu/simulants/"
ESRIC_ARCHIVE = "http://web.archive.org/web/20250925225326/http://knowledge.esric.lu/simulants/"
DEAD_VENDORS = {"https://astroport.us/"}
R080 = {"doi": None, "url": "https://iaai-2021.sciforum.net", "local_path": "papers/LRS/manuscript.pdf"}
# Links a reader saved the document from but never recorded (checked: the file at this address
# is byte-identical to the verified copy).
MISSING_URLS = {"RN-S043-2": "https://www.nasa.gov/wp-content/uploads/2019/04/batiste.pdf"}


def fix(con: sqlite3.Connection) -> list[dict]:
    log = []
    names = {sid: n for sid, n in con.execute("SELECT simulant_id, name FROM simulants")}
    for sid, url in con.execute("SELECT simulant_id, url FROM purchase_info").fetchall():
        name, new = names.get(sid), url
        if name in SRT and url != SRT[name]:
            new = SRT[name]
        elif url == OPR_OLD:
            new = OPR_NEW if name in OPR_LISTED else None
        elif url in DEAD_VENDORS:
            new = None
        if new != url:
            con.execute("UPDATE purchase_info SET url=? WHERE simulant_id=?", (new, sid))
            log.append({"simulant_id": sid, "name": name, "table": "purchase_info", "was": url, "now": new,
                        "action": "vendor link updated" if new else "vendor link removed: the page no longer exists or does not list it"})
    for rid, url, title in con.execute("SELECT reference_id, url, title FROM references_ WHERE url=?", (ESRIC_OLD,)).fetchall():
        con.execute("UPDATE references_ SET url=? WHERE reference_id=?", (ESRIC_ARCHIVE, rid))
        log.append({"reference_id": rid, "was": url, "now": ESRIC_ARCHIVE, "action": "linked to the archived copy (site gone)"})
    r = con.execute("SELECT doi, url, local_path, reference_text FROM references_ WHERE reference_id='R080'").fetchone()
    if r and (r[0], r[1], r[2]) != (R080["doi"], R080["url"], R080["local_path"]):
        text = (r[3] or "").replace(" https://doi.org/10.3390/IAAI-2021-10583", "").replace("https://doi.org/10.3390/IAAI-2021-10583", "").strip()
        text += " Presented at the 2nd Innovation Aviation & Aerospace Industry International Conference (IAAI 2021), 28-30 June 2021."
        con.execute("UPDATE references_ SET doi=?, url=?, local_path=?, reference_text=? WHERE reference_id='R080'",
                    (R080["doi"], R080["url"], R080["local_path"], text))
        log.append({"reference_id": "R080", "was": {"doi": r[0], "url": r[1]}, "now": R080,
                    "action": "unregistered DOI removed; the paper's own address used"})
    for rid, url in MISSING_URLS.items():
        cur = con.execute("UPDATE references_ SET url=? WHERE reference_id=? AND coalesce(url,'')!=?", (url, rid, url))
        if cur.rowcount:
            log.append({"reference_id": rid, "now": url, "action": "link added (the reader saved the document from here)"})
    # A reader's note is not part of a title: "Evaluations of lunar regolith simulants [= existing reference R066 ...]".
    for rid, title in con.execute("SELECT reference_id, title FROM references_ WHERE title LIKE '%[=%'").fetchall():
        clean = re.sub(r"\s*\[=[^\]]*\]?.*$", "", title).strip()
        if clean and clean != title:
            con.execute("UPDATE references_ SET title=? WHERE reference_id=?", (clean, rid))
            log.append({"reference_id": rid, "was": title, "now": clean, "action": "reader's note removed from the title"})
    con.commit()
    return log


if __name__ == "__main__":
    con = sqlite3.connect(ROOT / "lrs.sqlite")
    log = fix(con)
    con.close()
    for e in log:
        print(f"  {e.get('name') or e.get('reference_id')}: {e['action']}")
    if log:
        LOG.write_text(json.dumps(log, indent=1, ensure_ascii=False))
    print(f"{len(log)} change(s)")

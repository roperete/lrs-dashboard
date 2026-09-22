#!/usr/bin/env python3
"""Replace local working-copy paths in composition_source_url / datasheet_url with the
public URL of the original document.

The 2026-09-21 audit recorded, for each verified simulant, the path of the PDF the
extractor opened on disk. Rendered as a link on the site that path resolves against
github.io and 404s. This maps each verified simulant to the document's original,
publicly served URL, verified with a HEAD request on 2026-09-22.

Hispansion does not publish its technical data sheets; the TDS states they are
available on request. Its two simulants link to the manufacturer's TerraLun Core
product page, and the title carries the TDS document number. The sheets themselves
are kept under DIRT/Sources/datasheets/Hispansion/ and on the project Drive.
"""

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "lrs.sqlite"
LOG_OUT = ROOT / "documentation" / "source-url-fix-log-2026-09-22.json"

SRT = "https://cdn.shopify.com/s/files/1/0398/9268/0862/files"

PUBLIC = {
    # simulant_id: (composition_source_url, datasheet_url or None, title override or None)
    "S036": (f"{SRT}/LHS-1-SPEC-SHEET-DEC2025.pptx.pdf?v=1764081545", "same", None),
    "S091": (f"{SRT}/LHS-1D-SPEC-SHEET-DEC2025.pptx.pdf?v=1764081546", "same", None),
    "S092": (f"{SRT}/LHS-1E-SPEC-SHEET-DEC2025.pptx.pdf?v=1764081546", "same", None),
    "S077": (f"{SRT}/LHS-2-SPEC-SHEET-DEC2025.pptx.pdf?v=1764081545", "same", None),
    "S078": (f"{SRT}/LHS-2E-SPEC-SHEET-DEC2025.pptx.pdf?v=1764081545", "same", None),
    "S093": (f"{SRT}/LHS-1-25A_Spec_Sheet.pptx.pdf?v=1761053856", "same", None),
    "S037": (f"{SRT}/LMS-1-SPEC-SHEET-DEC2025.pptx.pdf?v=1764081546", "same", None),
    "S094": (f"{SRT}/LMS-1D-SPEC-SHEET-DEC2025.pptx_a39cf2a4-4f51-4714-b6ad-421e25e0f295.pdf?v=1765990108", "same", None),
    "S095": (f"{SRT}/LMS-1E-SPEC-SHEET-DEC2025.pptx.pdf?v=1764081546", "same", None),
    "S076": (f"{SRT}/LMS-2-SPEC-SHEET-DEC2025.pptx.pdf?v=1764081545", "same", None),
    "S079": (f"{SRT}/LSP-2-SPEC-SHEET-DEC2025.pptx.pdf?v=1764081545", "same", None),
    "S057": ("https://www.offplanetresearch.com/s/OPR-General-Lunar-Regolith-Simulants-Data-Sheet-yek3.pdf", "same", None),
    "S058": ("https://www.offplanetresearch.com/s/OPR-General-Lunar-Regolith-Simulants-Data-Sheet-yek3.pdf", "same", None),
    "S059": ("https://www.offplanetresearch.com/s/OPR-General-Lunar-Regolith-Simulants-Data-Sheet-yek3.pdf", "same", None),
    "S060": ("https://www.offplanetresearch.com/s/OPR-General-Lunar-Regolith-Simulants-Data-Sheet-yek3.pdf", "same", None),
    "S065": ("https://www.hispansion.io/product-services/regolith-simulants/core-simulant", None,
             "Hispansion Technical Data Sheet TDS-TLH-0-v1.1 (11 Nov 2025), supplied by the manufacturer; TerraLun Core product page linked"),
    "S066": ("https://www.hispansion.io/product-services/regolith-simulants/core-simulant", None,
             "Hispansion Technical Data Sheet TDS-TLM-0-v1.1 (11 Nov 2025), supplied by the manufacturer; TerraLun Core product page linked"),
    "S100": ("https://ntrs.nasa.gov/api/citations/20240011783/downloads/Lunar_Regolith_Simulant_Users_Guide_Rev_A_28OCT.pdf", None, None),
    # DUST-Y is not displayed (not_published) but its recorded source should still be the public document
    "S016": ("https://lsic.jhuapl.edu/Our-Work/Working-Groups/files/Lunar-Simulants/simulant_eval_2020.pdf", None, None),
}


def main() -> None:
    con = sqlite3.connect(DB)
    log = []
    for sid, (src_url, ds_url, title) in PUBLIC.items():
        assert src_url.startswith("https://"), sid
        row = con.execute(
            "SELECT name, composition_source_url, datasheet_url, composition_source_title FROM simulants WHERE simulant_id=?",
            (sid,),
        ).fetchone()
        if row is None:
            continue
        name, old_src, old_ds, old_title = row
        if ds_url == "same":
            ds_url = src_url
        if old_src != src_url:
            con.execute("UPDATE simulants SET composition_source_url=? WHERE simulant_id=?", (src_url, sid))
            log.append({"simulant_id": sid, "name": name, "field": "composition_source_url", "old": old_src, "new": src_url,
                        "reason": "local working-copy path replaced by the document's public URL (HEAD-checked 2026-09-22)"})
        if ds_url and old_ds != ds_url:
            con.execute("UPDATE simulants SET datasheet_url=? WHERE simulant_id=?", (ds_url, sid))
            log.append({"simulant_id": sid, "name": name, "field": "datasheet_url", "old": old_ds, "new": ds_url,
                        "reason": "manufacturer data sheet public URL"})
        if title and old_title != title:
            con.execute("UPDATE simulants SET composition_source_title=? WHERE simulant_id=?", (title, sid))
            log.append({"simulant_id": sid, "name": name, "field": "composition_source_title", "old": old_title, "new": title,
                        "reason": "manufacturer does not publish the TDS; title names the document, link goes to the product page"})
    con.commit()

    bad = con.execute(
        "SELECT simulant_id FROM simulants WHERE composition_status='verified' AND (composition_source_url IS NULL OR composition_source_url NOT LIKE 'http%')"
    ).fetchall()
    con.close()
    LOG_OUT.write_text(json.dumps(log, indent=1))
    print(f"{len(log)} field changes -> {LOG_OUT.name}")
    print("verified simulants without a public source URL:", [b[0] for b in bad] or "none")


if __name__ == "__main__":
    main()

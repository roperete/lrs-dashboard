"""After agent findings insert composition rows, the simulant's composition_status must
follow: rows that two readers agreed on, all citing a document, make the composition
`verified`, with the source line pointing at the most-cited document. The kind of that
document decides the label and whether a human check is still flagged:

  datasheet -> manufacturer_datasheet      report -> agency_report
  composition / geotechnical / untyped -> primary_paper
  review / general / usage -> secondary_reproduction (needs_review = 1)

A simulant with any composition row lacking reference_id is left alone, as is one that
is already verified (the 2026-09-21 sheet audit set those by hand).

Run:  python3 -m unittest scripts.tests.test_refresh_composition_status
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from provenance import ensure_provenance_schema  # noqa: E402
from refresh_composition_status import refresh, kind_for  # noqa: E402


def make_db(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript((ROOT / "scripts" / "schema.sql").read_text())
    ensure_provenance_schema(con)
    sims = [
        ("S1", "A", "withheld_unverified"), ("S2", "B", "withheld_unverified"), ("S3", "C", "withheld_unverified"),
        ("S4", "D", "verified"), ("S5", "E", "not_extracted"), ("S6", "F", "withheld_unverified"),
    ]
    con.executemany("INSERT INTO simulants (simulant_id, name, composition_status) VALUES (?,?,?)", sims)
    con.execute("UPDATE simulants SET composition_source_title='Sheet D', composition_source_kind='manufacturer_datasheet', composition_needs_review=0 WHERE simulant_id='S4'")
    refs = [
        ("R1", "S1", "Zhou 2020 primary", "composition", "Primary paper on A", "10.1000/a", None),
        ("RN-S2-1", "S2", "Review", "review", "A review reproducing the table", None, "https://example.org/review"),
        ("R3", "S3", "x", "composition", "Paper C", None, None),
        ("DS-S4", "S4", "sheet", "datasheet", "Sheet D", None, "https://example.org/sheet"),
        ("R5a", "S5", "NASA TM", "report", "NASA/TM-2013 report", None, "https://ntrs.nasa.gov/x"),
        ("R5b", "S5", "paper", "composition", "Paper E", "10.1000/e", None),
        ("R6", "S6", "untyped", None, None, "10.1000/f", None),
    ]
    con.executemany("INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type, title, doi, url) VALUES (?,?,?,?,?,?,?)", refs)
    ox = [
        ("CH1", "S1", "oxide", "SiO2", 47.0, "R1"), ("CH2", "S1", "oxide", "TiO2", 1.0, "R1"),
        ("CH3", "S2", "oxide", "SiO2", 49.0, "RN-S2-1"),
        ("CH4", "S3", "oxide", "SiO2", 45.0, "R3"), ("CH5", "S3", "oxide", "Al2O3", 15.0, None),
        ("CH6", "S4", "oxide", "SiO2", 50.0, "DS-S4"),
        ("CH7", "S5", "oxide", "SiO2", 46.0, "R5a"), ("CH8", "S5", "oxide", "TiO2", 0.5, "R5a"), ("CH9", "S5", "oxide", "MgO", 8.0, "R5b"),
        ("CH10", "S6", "oxide", "SiO2", 44.0, "R6"),
    ]
    con.executemany("INSERT INTO chemical_compositions (composition_id, simulant_id, component_type, component_name, value_wt_pct, reference_id) VALUES (?,?,?,?,?,?)", ox)
    con.execute("INSERT INTO mineral_compositions (composition_id, simulant_id, component_type, component_name, value_pct, reference_id) VALUES ('C1','S5','mineral','Plagioclase',60.0,'R5a')")
    con.commit()
    con.close()


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "lrs.sqlite"
        make_db(self.db)
        self.log = refresh(self.db)
        self.con = sqlite3.connect(self.db)
        self.con.row_factory = sqlite3.Row

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def sim(self, sid):
        return self.con.execute("SELECT * FROM simulants WHERE simulant_id=?", (sid,)).fetchone()

    def test_kind_mapping(self):
        self.assertEqual(kind_for("datasheet"), "manufacturer_datasheet")
        self.assertEqual(kind_for("report"), "agency_report")
        for t in ("composition", "geotechnical", None, ""):
            self.assertEqual(kind_for(t), "primary_paper")
        for t in ("review", "general", "usage"):
            self.assertEqual(kind_for(t), "secondary_reproduction")

    def test_primary_paper_becomes_verified_with_doi_link(self):
        s = self.sim("S1")
        self.assertEqual(s["composition_status"], "verified")
        self.assertEqual(s["composition_source_kind"], "primary_paper")
        self.assertEqual(s["composition_source_title"], "Primary paper on A")
        self.assertEqual(s["composition_source_url"], "https://doi.org/10.1000/a")
        self.assertEqual(s["composition_needs_review"], 0)

    def test_secondary_reproduction_is_verified_but_flagged(self):
        s = self.sim("S2")
        self.assertEqual(s["composition_status"], "verified")
        self.assertEqual(s["composition_source_kind"], "secondary_reproduction")
        self.assertEqual(s["composition_source_url"], "https://example.org/review")
        self.assertEqual(s["composition_needs_review"], 1)

    def test_row_without_reference_leaves_status_alone(self):
        s = self.sim("S3")
        self.assertEqual(s["composition_status"], "withheld_unverified")
        self.assertIsNone(s["composition_source_kind"])
        self.assertTrue(any(e["simulant_id"] == "S3" and e["outcome"] == "skipped: composition row without reference" for e in self.log))

    def test_already_verified_untouched(self):
        s = self.sim("S4")
        self.assertEqual(s["composition_source_title"], "Sheet D")
        self.assertFalse(any(e["simulant_id"] == "S4" for e in self.log))

    def test_most_cited_document_wins_across_both_tables(self):
        s = self.sim("S5")
        self.assertEqual(s["composition_status"], "verified")
        self.assertEqual(s["composition_source_kind"], "agency_report")
        self.assertEqual(s["composition_source_title"], "NASA/TM-2013 report")

    def test_untyped_reference_falls_back_to_reference_text_and_doi(self):
        s = self.sim("S6")
        self.assertEqual(s["composition_source_kind"], "primary_paper")
        self.assertEqual(s["composition_source_title"], "untyped")
        self.assertEqual(s["composition_source_url"], "https://doi.org/10.1000/f")

    def test_idempotent(self):
        before = [tuple(r) for r in self.con.execute("SELECT * FROM simulants ORDER BY simulant_id")]
        self.con.close()
        log2 = refresh(self.db)
        self.con = sqlite3.connect(self.db); self.con.row_factory = sqlite3.Row
        after = [tuple(r) for r in self.con.execute("SELECT * FROM simulants ORDER BY simulant_id")]
        self.assertEqual(before, after)
        self.assertFalse(any(e["outcome"].startswith("verified") for e in log2))


if __name__ == "__main__":
    unittest.main()

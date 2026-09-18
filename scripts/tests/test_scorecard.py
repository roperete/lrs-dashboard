"""Tests for scripts/scorecard.py — per-simulant data-quality scorecard.

Run:  python3 -m unittest scripts/tests/test_scorecard.py
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from scorecard import build_scorecard  # noqa: E402


def make_db(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript((ROOT / "scripts" / "schema.sql").read_text())

    sims = [
        # id, name, institution, availability, datasheet_url
        ("S001", "SPEC-1", "Space Resource Technologies", "Available", None),
        ("S002", "PAPER-1", "Some University", "Available", None),
        ("S003", "REVIEW-1", None, "Unavailable", None),
        ("S004", "EMPTY-1", None, "Unknown", None),
        ("S005", "NULLS-1", None, "Unknown", None),
        ("S006", "URL-1", "Hispansion", "Available", "https://hispansion.io/tds.pdf"),
    ]
    con.executemany(
        "INSERT INTO simulants (simulant_id, name, institution, availability, datasheet_url) VALUES (?,?,?,?,?)",
        sims,
    )

    refs = [
        # id, simulant, text, type, title, url
        ("R001", "S001", "LHS-1 Lunar Highlands Simulant Fact Sheet", "general", None, "https://exolithsimulants.com"),
        ("R002", "S002", "Li, R. et al. (2022). Preparation and characterization of a specialized lunar regolith simulant", "composition", None, None),
        ("R003", "S003", None, "review", "An overview on lunar regolith simulants solidification methods", "https://doi.org/10.1/x"),
        ("R004", "S003", None, "report", "Lunar Regolith Simulant User's Guide Revision A", None),
        ("R005", "S005", None, "usage", "Sintering behaviour of NULLS-1 bricks", None),
    ]
    con.executemany(
        "INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type, title, url) VALUES (?,?,?,?,?,?)",
        refs,
    )

    chem = [
        ("CH001", "S001", "oxide", "SiO2", 46.0),
        ("CH002", "S001", "oxide", "Al2O3", 25.0),
        ("CH003", "S001", "oxide", "CaO", 14.0),
        ("CH004", "S001", "oxide", "FeO", 7.0),
        ("CH005", "S001", "oxide", "MgO", 5.0),
        ("CH006", "S001", "oxide", "Na2O", 2.5),
        ("CH007", "S001", "oxide", "Sum", 99.5),          # must be excluded from the sum
        ("CH008", "S003", "oxide", "SiO2", 45.0),
        ("CH009", "S003", "oxide", "Al2O3", 25.0),
        ("CH010", "S005", "oxide", "SiO2", None),
    ]
    con.executemany(
        "INSERT INTO chemical_compositions (composition_id, simulant_id, component_type, component_name, value_wt_pct) VALUES (?,?,?,?,?)",
        chem,
    )

    minerals = [
        ("C001", "S001", "mineral", "Plagioclase", 75.0),
        ("C002", "S001", "mineral", "Pyroxene", 25.0),
        ("C003", "S002", "mineral", "Plagioclase", 100.0),
        ("C004", "S002", "mineral", "Glass", 84.6),            # sums to 184.6 -> flagged
        ("C005", "S005", "mineral", "Albite", None),
        ("C006", "S005", "mineral", "Anorthite", None),
    ]
    con.executemany(
        "INSERT INTO mineral_compositions (composition_id, simulant_id, component_type, component_name, value_pct) VALUES (?,?,?,?,?)",
        minerals,
    )
    con.commit()
    con.close()


class ScorecardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = Path(cls.tmp.name) / "test.sqlite"
        make_db(cls.db)
        cls.rows = {r["simulant_id"]: r for r in build_scorecard(cls.db)}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_one_row_per_simulant(self):
        self.assertEqual(sorted(self.rows), ["S001", "S002", "S003", "S004", "S005", "S006"])

    def test_spec_sheet_reference_gives_tier_a(self):
        self.assertEqual(self.rows["S001"]["source_tier"], "A")

    def test_datasheet_url_alone_gives_tier_a(self):
        self.assertEqual(self.rows["S006"]["source_tier"], "A")
        self.assertTrue(self.rows["S006"]["has_datasheet_url"])

    def test_primary_composition_paper_gives_tier_b(self):
        self.assertEqual(self.rows["S002"]["source_tier"], "B")

    def test_review_only_references_give_tier_d(self):
        self.assertEqual(self.rows["S003"]["source_tier"], "D")

    def test_no_references_gives_tier_e(self):
        self.assertEqual(self.rows["S004"]["source_tier"], "E")

    def test_chem_sum_excludes_sum_row(self):
        self.assertAlmostEqual(self.rows["S001"]["chem_sum"], 99.5)
        self.assertTrue(self.rows["S001"]["chem_sum_ok"])

    def test_mineral_sum_out_of_range_is_flagged(self):
        self.assertAlmostEqual(self.rows["S002"]["min_sum"], 184.6)
        self.assertFalse(self.rows["S002"]["min_sum_ok"])
        self.assertIn("mineral sum 184.6% outside 90-101%", self.rows["S002"]["issues"])

    def test_null_values_are_counted_and_flagged(self):
        self.assertEqual(self.rows["S005"]["n_null_values"], 3)
        self.assertTrue(any("null" in i for i in self.rows["S005"]["issues"]))

    def test_composition_without_primary_source_is_priority_1(self):
        # S003 has oxide numbers but only review-type references
        self.assertEqual(self.rows["S003"]["priority"], "P1")

    def test_integrity_problem_is_priority_2(self):
        self.assertEqual(self.rows["S002"]["priority"], "P2")
        self.assertEqual(self.rows["S005"]["priority"], "P2")

    def test_sourced_composition_is_priority_3(self):
        self.assertEqual(self.rows["S001"]["priority"], "P3")

    def test_no_composition_is_priority_4(self):
        self.assertEqual(self.rows["S004"]["priority"], "P4")
        self.assertEqual(self.rows["S006"]["priority"], "P4")

    def test_counts(self):
        self.assertEqual(self.rows["S001"]["n_oxides"], 6)   # Sum row excluded
        self.assertEqual(self.rows["S001"]["n_minerals"], 2)
        self.assertEqual(self.rows["S003"]["n_refs"], 2)
        self.assertEqual(self.rows["S002"]["n_comp_refs"], 1)


if __name__ == "__main__":
    unittest.main()

"""Tests for scripts/reconcile.py — applying audit findings to lrs.sqlite.

Policy under test: a composition list is published only when it is traced to an
acceptable source, an independent second read confirmed it, and it sums like a
real analysis. Anything else is withheld, and the simulant records why.

A failing oxide list does not discard a sound mineral list, or vice versa.

Run:  python3 -m unittest scripts.tests.test_reconcile
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from reconcile import (  # noqa: E402
    STATUS_NOT_EXTRACTED,
    STATUS_NOT_PUBLISHED,
    STATUS_VERIFIED,
    STATUS_WITHHELD,
    apply_decisions,
    decide,
)

# Real LHS-1 Dec 2025 fact-sheet numbers: oxides sum 98.74 excluding LOI, minerals sum 100.0
GOOD_OXIDES = [
    {"name": "SiO2", "wt_pct": 49.12}, {"name": "TiO2", "wt_pct": 0.63},
    {"name": "Al2O3", "wt_pct": 26.29}, {"name": "FeO", "wt_pct": 3.20},
    {"name": "MnO", "wt_pct": 0.06}, {"name": "MgO", "wt_pct": 2.86},
    {"name": "CaO", "wt_pct": 13.52}, {"name": "Na2O", "wt_pct": 2.55},
    {"name": "K2O", "wt_pct": 0.34}, {"name": "P2O5", "wt_pct": 0.17},
    {"name": "LOI", "wt_pct": 0.41},
]
GOOD_MINERALS = [
    {"name": "Anorthosite", "pct": 74.4}, {"name": "Glass-rich Basalt", "pct": 24.7},
    {"name": "Ilmenite", "pct": 0.4}, {"name": "Bronzite", "pct": 0.3},
    {"name": "Olivine", "pct": 0.2},
]


def extraction(**kw):
    base = {
        "simulant_id": "S001", "name": "TEST-1", "found": True,
        "source_kind": "manufacturer_datasheet",
        "source_title": "TEST-1 Fact Sheet",
        "source_url": "https://example.org/test-1.pdf",
        "source_version": "Dec 2025",
        "evidence_quote": "SiO2 49.12 Al2O3 26.29 ...",
        "oxides": list(GOOD_OXIDES), "minerals": list(GOOD_MINERALS),
        "physical": {"bulk_density": "1.40"},
        "db_discrepancies": [], "verdict": "DB_MATCHES_SOURCE", "notes": "",
    }
    base.update(kw)
    return base


def check(**kw):
    base = {
        "simulant_id": "S001", "source_exists_and_matches_claim": True,
        "quote_is_genuine": True, "numbers_match_source": True,
        "verdict": "CONFIRMED", "problems": [],
        "corrected_oxides": [], "corrected_minerals": [],
    }
    base.update(kw)
    return base


class DecideTest(unittest.TestCase):
    def test_confirmed_match_keeps_data_and_marks_verified(self):
        d = decide(extraction(), check())
        self.assertEqual(d["action"], "keep")
        self.assertEqual(d["status"], STATUS_VERIFIED)
        self.assertEqual(d["source_url"], "https://example.org/test-1.pdf")
        self.assertFalse(d["needs_review"])

    def test_confirmed_mismatch_replaces_with_source_values(self):
        d = decide(
            extraction(verdict="DB_WRONG_SOURCE_FOUND", db_discrepancies=["SiO2: db 42.81, source 49.12"]),
            check(),
        )
        self.assertEqual(d["action"], "replace")
        self.assertEqual(d["status"], STATUS_VERIFIED)
        self.assertEqual(d["oxides"][0]["wt_pct"], 49.12)

    def test_refuted_verification_withholds(self):
        d = decide(extraction(), check(verdict="REFUTED", quote_is_genuine=False, problems=["quote not in document"]))
        self.assertEqual(d["action"], "withhold")
        self.assertEqual(d["status"], STATUS_WITHHELD)
        self.assertIn("quote not in document", d["reason"])

    def test_no_source_found_withholds(self):
        d = decide(
            extraction(found=False, verdict="NO_SOURCE_FOUND", oxides=[], minerals=[], source_kind="none"),
            check(),
        )
        self.assertEqual(d["action"], "withhold")
        self.assertEqual(d["status"], STATUS_WITHHELD)

    def test_source_without_composition_is_not_published(self):
        d = decide(
            extraction(verdict="SOURCE_HAS_NO_COMPOSITION", oxides=[], minerals=[], source_kind="primary_paper"),
            check(),
        )
        self.assertEqual(d["action"], "withhold")
        self.assertEqual(d["status"], STATUS_NOT_PUBLISHED)

    def test_review_source_is_not_acceptable_even_when_confirmed(self):
        d = decide(extraction(source_kind="review_or_secondary"), check())
        self.assertEqual(d["action"], "withhold")
        self.assertEqual(d["status"], STATUS_WITHHELD)
        self.assertIn("review", d["reason"].lower())

    def test_partial_with_corrections_uses_verifier_numbers_and_flags_review(self):
        corrected = [dict(o) for o in GOOD_OXIDES]
        corrected[0] = {"name": "SiO2", "wt_pct": 47.10}
        corrected[6] = {"name": "CaO", "wt_pct": 15.54}
        d = decide(
            extraction(),
            check(verdict="PARTIAL", numbers_match_source=False, corrected_oxides=corrected,
                  problems=["extractor read SiO2 49.12, source says 47.10"]),
        )
        self.assertEqual(d["action"], "replace")
        self.assertEqual(d["status"], STATUS_VERIFIED)
        self.assertEqual(d["oxides"][0]["wt_pct"], 47.10)
        self.assertTrue(d["needs_review"])

    def test_partial_without_corrections_withholds(self):
        d = decide(extraction(), check(verdict="PARTIAL", numbers_match_source=False))
        self.assertEqual(d["action"], "withhold")
        self.assertEqual(d["status"], STATUS_WITHHELD)

    def test_missing_verification_withholds(self):
        d = decide(extraction(), None)
        self.assertEqual(d["action"], "withhold")
        self.assertTrue(d["needs_review"])

    def test_confirmed_but_no_values_is_not_published(self):
        d = decide(extraction(oxides=[], minerals=[]), check())
        self.assertEqual(d["action"], "withhold")
        self.assertEqual(d["status"], STATUS_NOT_PUBLISHED)

    def test_bad_mineral_sum_drops_minerals_but_keeps_sound_oxides(self):
        d = decide(
            extraction(minerals=[{"name": "Plagioclase", "pct": 100.0}, {"name": "Glass", "pct": 84.6}]),
            check(),
        )
        self.assertEqual(d["action"], "replace")
        self.assertEqual(d["status"], STATUS_VERIFIED)
        self.assertEqual(d["minerals"], [])
        self.assertEqual(len(d["oxides"]), len(GOOD_OXIDES))
        self.assertTrue(d["needs_review"])
        self.assertIn("mineral", d["reason"].lower())

    def test_bad_oxide_sum_drops_oxides_but_keeps_sound_minerals(self):
        d = decide(
            extraction(oxides=[{"name": "SiO2", "wt_pct": 40.0}, {"name": "Al2O3", "wt_pct": 20.0}]),
            check(),
        )
        self.assertEqual(d["action"], "replace")
        self.assertEqual(d["oxides"], [])
        self.assertEqual(len(d["minerals"]), len(GOOD_MINERALS))
        self.assertIn("oxide", d["reason"].lower())

    def test_both_lists_failing_sums_withholds_entirely(self):
        d = decide(
            extraction(oxides=[{"name": "SiO2", "wt_pct": 40.0}],
                       minerals=[{"name": "Plagioclase", "pct": 45.0}]),
            check(),
        )
        self.assertEqual(d["action"], "withhold")
        self.assertEqual(d["status"], STATUS_WITHHELD)

    def test_sum_and_total_rows_are_excluded_from_the_oxide_sum(self):
        with_total = list(GOOD_OXIDES) + [{"name": "Total", "wt_pct": 99.15}, {"name": "Sum", "wt_pct": 99.15}]
        d = decide(extraction(oxides=with_total), check())
        self.assertEqual(d["action"], "keep")
        self.assertEqual(d["status"], STATUS_VERIFIED)

    def test_duplicate_iron_aggregate_is_not_double_counted(self):
        # FeOT alongside FeO would push the sum over 102 if naively added
        oxides = list(GOOD_OXIDES) + [{"name": "FeOT", "wt_pct": 3.20}]
        d = decide(extraction(oxides=oxides), check())
        self.assertEqual(d["status"], STATUS_VERIFIED)


def make_db(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript((ROOT / "scripts" / "schema.sql").read_text())
    con.executemany(
        "INSERT INTO simulants (simulant_id, name) VALUES (?,?)",
        [("S001", "KEEP-1"), ("S002", "REPLACE-1"), ("S003", "WITHHOLD-1"),
         ("S004", "UNAUDITED-1"), ("S005", "NODATA-1")],
    )
    con.executemany(
        "INSERT INTO chemical_compositions (composition_id, simulant_id, component_type, component_name, value_wt_pct) VALUES (?,?,?,?,?)",
        [("CH001", "S001", "oxide", "SiO2", 49.12), ("CH002", "S002", "oxide", "SiO2", 42.81),
         ("CH003", "S003", "oxide", "SiO2", 46.0), ("CH004", "S004", "oxide", "SiO2", 44.0)],
    )
    con.executemany(
        "INSERT INTO mineral_compositions (composition_id, simulant_id, component_type, component_name, value_pct) VALUES (?,?,?,?,?)",
        [("C001", "S003", "mineral", "Plagioclase", 45.0)],
    )
    con.commit()
    con.close()


class ApplyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "t.sqlite"
        make_db(self.db)
        self.decisions = {
            "S001": {"action": "keep", "status": STATUS_VERIFIED, "oxides": [{"name": "SiO2", "wt_pct": 49.12}],
                     "minerals": [], "source_url": "https://example.org/a.pdf", "source_title": "A Fact Sheet",
                     "source_kind": "manufacturer_datasheet", "reason": "confirmed", "needs_review": False},
            "S002": {"action": "replace", "status": STATUS_VERIFIED, "oxides": [{"name": "SiO2", "wt_pct": 48.22}],
                     "minerals": [{"name": "Bronzite", "pct": 32.8}], "source_url": "https://example.org/b.pdf",
                     "source_title": "B Fact Sheet", "source_kind": "manufacturer_datasheet",
                     "reason": "db disagreed with source", "needs_review": False},
            "S003": {"action": "withhold", "status": STATUS_WITHHELD, "oxides": [], "minerals": [],
                     "source_url": "", "source_title": "", "source_kind": "none",
                     "reason": "no source found", "needs_review": False},
        }
        self.log = apply_decisions(self.db, self.decisions)

    def tearDown(self):
        self.tmp.cleanup()

    def rows(self, table, sid):
        con = sqlite3.connect(self.db)
        n = con.execute(f"SELECT count(*) FROM {table} WHERE simulant_id=?", (sid,)).fetchone()[0]
        con.close()
        return n

    def status(self, sid):
        con = sqlite3.connect(self.db)
        v = con.execute("SELECT composition_status FROM simulants WHERE simulant_id=?", (sid,)).fetchone()[0]
        con.close()
        return v

    def test_keep_leaves_rows_intact(self):
        self.assertEqual(self.rows("chemical_compositions", "S001"), 1)
        self.assertEqual(self.status("S001"), STATUS_VERIFIED)

    def test_replace_swaps_values(self):
        con = sqlite3.connect(self.db)
        vals = con.execute("SELECT component_name, value_wt_pct FROM chemical_compositions WHERE simulant_id='S002'").fetchall()
        mins = con.execute("SELECT component_name, value_pct FROM mineral_compositions WHERE simulant_id='S002'").fetchall()
        con.close()
        self.assertEqual(vals, [("SiO2", 48.22)])
        self.assertEqual(mins, [("Bronzite", 32.8)])

    def test_withhold_deletes_all_composition_rows(self):
        self.assertEqual(self.rows("chemical_compositions", "S003"), 0)
        self.assertEqual(self.rows("mineral_compositions", "S003"), 0)
        self.assertEqual(self.status("S003"), STATUS_WITHHELD)

    def test_datasheet_url_recorded_for_verified(self):
        con = sqlite3.connect(self.db)
        url = con.execute("SELECT datasheet_url FROM simulants WHERE simulant_id='S001'").fetchone()[0]
        con.close()
        self.assertEqual(url, "https://example.org/a.pdf")

    def test_unaudited_simulant_with_data_is_untouched_but_marked(self):
        self.assertEqual(self.rows("chemical_compositions", "S004"), 1)
        self.assertEqual(self.status("S004"), STATUS_NOT_EXTRACTED)

    def test_simulant_with_no_data_is_marked_not_extracted(self):
        self.assertEqual(self.status("S005"), STATUS_NOT_EXTRACTED)

    def test_log_records_every_change(self):
        ids = {e["simulant_id"] for e in self.log}
        self.assertEqual(ids, {"S001", "S002", "S003"})
        withheld = [e for e in self.log if e["action"] == "withhold"][0]
        self.assertEqual(withheld["oxides_removed"], 1)
        self.assertEqual(withheld["minerals_removed"], 1)

    def test_local_file_path_is_never_stored_as_a_source_url(self):
        # S005 has never been given any URL, so both columns must stay empty
        decisions = {
            "S005": {"action": "replace", "status": STATUS_VERIFIED, "oxides": [{"name": "SiO2", "wt_pct": 49.12}],
                     "minerals": [], "source_url": "/Volumes/SSD/DIRT/Sources/datasheets/SRT/LHS-1.pdf",
                     "source_title": "LHS-1 Fact Sheet", "source_kind": "manufacturer_datasheet",
                     "reason": "confirmed", "needs_review": False},
        }
        apply_decisions(self.db, decisions)
        con = sqlite3.connect(self.db)
        src, ds = con.execute("SELECT composition_source_url, datasheet_url FROM simulants WHERE simulant_id='S005'").fetchone()
        con.close()
        self.assertIsNone(src)
        self.assertIsNone(ds)

    def test_withheld_simulant_never_gets_a_datasheet_link(self):
        # JSC-1AC case: the extractor named the JSC-1A sheet as the family's document and the
        # decision was withhold. A datasheet link must only ever appear on a verified simulant.
        decisions = {
            "S005": {"action": "withhold", "status": STATUS_WITHHELD, "oxides": [], "minerals": [],
                     "source_url": "https://ares.jsc.nasa.gov/projects/simulants/attachments/JSC-1A_MSDS.pdf",
                     "source_title": "JSC-1A MSDS", "source_kind": "manufacturer_datasheet",
                     "reason": "no independent verification", "needs_review": True},
        }
        apply_decisions(self.db, decisions)
        con = sqlite3.connect(self.db)
        ds = con.execute("SELECT datasheet_url FROM simulants WHERE simulant_id='S005'").fetchone()[0]
        con.close()
        self.assertIsNone(ds)

    def test_apply_is_idempotent(self):
        apply_decisions(self.db, self.decisions)
        self.assertEqual(self.rows("chemical_compositions", "S002"), 1)
        self.assertEqual(self.rows("chemical_compositions", "S003"), 0)
        self.assertEqual(self.status("S002"), STATUS_VERIFIED)


if __name__ == "__main__":
    unittest.main()

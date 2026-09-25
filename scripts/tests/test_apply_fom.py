"""Figures of Merit, stored one score per (simulant, property, lunar reference).

An FoM compares a simulant with a lunar reference material property by property, so a single
"FoM score" column loses what it measures and against what. Each confirmed score becomes a
row with its property, reference, score as printed and scale, cited to the document with the
quote. A score is attached only to the exact product named: "MLS-1 processed for glass" is not
MLS-1. Names the database does not hold are listed for a human, never guessed.

Run:  python3 -m unittest scripts.tests.test_apply_fom
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from provenance import ensure_provenance_schema  # noqa: E402
from apply_fom import apply_document, match_simulant, property_kind  # noqa: E402


def result(rows, verdicts):
    return {"doc": {"key": "slabic2024", "title": "Slabic et al. 2024, Lunar Regolith Simulant User's Guide, Revision A",
                    "path": "papers/Slabic_2024.pdf"},
            "reading": {"document_key": "slabic2024", "document_title": "Slabic, A., et al. (2024). Lunar Regolith Simulant User's Guide, Revision A. NASA/TM-20240011783",
                        "document_path": "papers/Slabic_2024.pdf", "method": "FoM 0-1, 1 = identical", "rows": rows, "notes": ""},
            "check": {"document_key": "slabic2024", "missed": [], "notes": "",
                      "checks": [{"row": i, "simulant": r["simulant"], "property": r["property"], "verdict": v, "note": ""} for i, (r, v) in enumerate(zip(rows, verdicts))]}}


def row(sim, prop, score, ref="Apollo 16 64500"):
    return {"simulant": sim, "property": prop, "reference": ref, "score": score, "scale": "0-1", "table": "Table 12", "page": "34",
            "quote": f"{sim} {prop} {score}"}


class ApplyFomTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        con = sqlite3.connect(Path(self.tmp.name) / "lrs.sqlite")
        con.executescript((ROOT / "scripts" / "schema.sql").read_text()); ensure_provenance_schema(con)
        con.executemany("INSERT INTO simulants (simulant_id, name) VALUES (?,?)", [("S043", "MLS-1"), ("S051", "NU-LHT-2M"), ("S028", "JSC-1A")])
        con.execute("INSERT INTO references_ (reference_id, simulant_id, title, local_path, names_simulant) VALUES "
                    "('R090','S043','Lunar Regolith Simulant User''s Guide: Revision A','papers/Slabic_2024.pdf',1)")
        con.commit(); self.con = con

    def tearDown(self):
        self.con.close(); self.tmp.cleanup()

    def test_names_match_only_the_exact_product(self):
        names = {"MLS-1": "S043", "NU-LHT-2M": "S051", "JSC-1A": "S028"}
        self.assertEqual(match_simulant("NU-LHT-2M", names), "S051")
        self.assertEqual(match_simulant("NU LHT 2M", names), "S051")
        self.assertEqual(match_simulant("jsc-1a", names), "S028")
        self.assertIsNone(match_simulant("MLS-1 (processed for glass)", names))
        self.assertIsNone(match_simulant("JSC-1AF", names))

    def test_property_kinds(self):
        self.assertEqual(property_kind("Composition"), "composition")
        self.assertEqual(property_kind("Chemistry"), "composition")
        self.assertEqual(property_kind("Size"), "particle_size")
        self.assertEqual(property_kind("Particle size distribution"), "particle_size")
        self.assertEqual(property_kind("Shape"), "shape")
        self.assertEqual(property_kind("Mean NASA FoM"), "overall")
        self.assertEqual(property_kind("Modal mineralogy"), "mineralogy")

    def test_confirmed_scores_are_stored_with_their_citation(self):
        log = apply_document(self.con, result([row("MLS-1", "Composition", "0.82"), row("NU-LHT-2M", "Size", "0.91")], ["CONFIRMED", "CONFIRMED"]), checked_on="2026-09-25")
        got = self.con.execute("SELECT simulant_id, property, property_label, reference_sample, score, scale, reference_id FROM figures_of_merit ORDER BY simulant_id").fetchall()
        self.assertEqual(got[0], ("S043", "composition", "Composition", "Apollo 16 64500", 0.82, "0-1", "R090"))   # reuses MLS-1's row for the guide
        rid = got[1][6]
        self.assertTrue(rid.startswith("RN-S051-"))
        self.assertEqual(self.con.execute("SELECT names_simulant FROM references_ WHERE reference_id=?", (rid,)).fetchone(), (1,))

    def test_a_reused_unchecked_reference_records_the_confirmed_mention(self):
        # JSC-1A lists the guide but nobody has checked that it names JSC-1A; a confirmed score row does
        self.con.execute("INSERT INTO references_ (reference_id, simulant_id, title) VALUES ('R132','S028','Lunar Regolith Simulant User''s Guide Revision A')")
        apply_document(self.con, result([row("JSC-1A", "Chemistry", "0.88")], ["CONFIRMED"]), checked_on="2026-09-25")
        self.assertEqual(self.con.execute("SELECT reference_id FROM figures_of_merit").fetchone(), ("R132",))
        self.assertEqual(self.con.execute("SELECT names_simulant, mention_quote, local_path, checked_on FROM references_ WHERE reference_id='R132'").fetchone(),
                         (1, "JSC-1A Chemistry 0.88", "papers/Slabic_2024.pdf", "2026-09-25"))

    def test_a_reference_confirmed_not_to_name_the_product_is_left_alone(self):
        self.con.execute("INSERT INTO references_ (reference_id, simulant_id, title, names_simulant) VALUES ('R132','S028','Lunar Regolith Simulant User''s Guide Revision A',0)")
        apply_document(self.con, result([row("JSC-1A", "Chemistry", "0.88")], ["CONFIRMED"]), checked_on="2026-09-25")
        self.assertEqual(self.con.execute("SELECT names_simulant, mention_quote FROM references_ WHERE reference_id='R132'").fetchone(), (0, None))

    def test_an_owner_decided_name_is_stored_on_that_product_with_the_footnote(self):
        # Slabic 2024 prints "OB-1(A*)": OB-1 measurements extrapolated to OB-1A (owner, 2026-09-25: keep on OB-1)
        self.con.execute("INSERT INTO simulants (simulant_id, name) VALUES ('S053','OB-1'), ('S054','OB-1A')")
        apply_document(self.con, result([row("OB-1(A*)", "Chemistry", "0.87")], ["CONFIRMED"]), checked_on="2026-09-25")
        sid, quote = self.con.execute("SELECT simulant_id, quote FROM figures_of_merit").fetchone()
        self.assertEqual(sid, "S053")
        self.assertIn("extrapolated to OB-1A", quote)

    def test_refuted_and_unmatched_rows_are_not_stored(self):
        log = apply_document(self.con, result([row("JSC-1A", "Shape", "0.7"), row("MLS-1 (processed for glass)", "Composition", "0.9"),
                                               row("KLS-1", "Size", "0.8")], ["REFUTED", "CONFIRMED", "CONFIRMED"]), checked_on="2026-09-25")
        self.assertEqual(self.con.execute("SELECT count(*) FROM figures_of_merit").fetchone(), (0,))
        outcomes = [e["outcome"] for e in log]
        self.assertIn("not stored: refuted by the checker", outcomes)
        self.assertEqual(outcomes.count("not stored: no simulant of exactly this name"), 2)

    def test_applying_twice_does_not_duplicate(self):
        r = result([row("MLS-1", "Composition", "0.82")], ["CONFIRMED"])
        apply_document(self.con, r, checked_on="2026-09-25"); log = apply_document(self.con, r, checked_on="2026-09-25")
        self.assertEqual(self.con.execute("SELECT count(*) FROM figures_of_merit").fetchone(), (1,))
        self.assertEqual([e["outcome"] for e in log], ["already stored"])   # a re-run's log still lists the row

    def test_a_score_that_is_not_a_number_is_not_stored(self):
        log = apply_document(self.con, result([row("MLS-1", "Composition", "n/a")], ["CONFIRMED"]), checked_on="2026-09-25")
        self.assertEqual(self.con.execute("SELECT count(*) FROM figures_of_merit").fetchone(), (0,))


class MethodQualifierTests(unittest.TestCase):
    """A measurement method in brackets is not a different product.

    Schrader et al. 2010, Table 5, "FoM size results for all simulants", writes "JSC-1A (dry
    sieve)", "NU-LHT-1M (laser diffractometry)": the same product, its size distribution
    measured one way or another. "MLS-1 (processed for glass)" is a different material."""

    def test_the_method_moves_into_the_property(self):
        from apply_fom import split_method
        self.assertEqual(split_method("JSC-1A (dry sieve)"), ("JSC-1A", "dry sieve"))
        self.assertEqual(split_method("NU-LHT-1M (laser diffractometry)"), ("NU-LHT-1M", "laser diffractometry"))
        self.assertEqual(split_method("Chenobi (dry sieve + laser diffractometry)"), ("Chenobi", "dry sieve + laser diffractometry"))
        self.assertEqual(split_method("OB-1 (section image analysis)"), ("OB-1", "section image analysis"))
        self.assertEqual(split_method("MLS-1 (processed for glass)"), ("MLS-1 (processed for glass)", None))
        self.assertEqual(split_method("OB-1(A*)"), ("OB-1(A*)", None))

    def test_a_method_qualified_row_is_stored_on_the_base_product(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        con = sqlite3.connect(Path(tmp.name) / "lrs.sqlite"); self.addCleanup(con.close)
        con.executescript((ROOT / "scripts" / "schema.sql").read_text()); ensure_provenance_schema(con)
        con.execute("INSERT INTO simulants (simulant_id, name) VALUES ('S028','JSC-1A')"); con.commit()
        apply_document(con, result([row("JSC-1A (dry sieve)", "Particle size distribution", "0.35")], ["CONFIRMED"]), checked_on="2026-09-25")
        self.assertEqual(con.execute("SELECT simulant_id, property, property_label FROM figures_of_merit").fetchone(),
                         ("S028", "particle_size", "Particle size distribution (dry sieve)"))

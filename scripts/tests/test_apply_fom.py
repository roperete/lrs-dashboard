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

    def test_refuted_and_unmatched_rows_are_not_stored(self):
        log = apply_document(self.con, result([row("JSC-1A", "Shape", "0.7"), row("MLS-1 (processed for glass)", "Composition", "0.9"),
                                               row("KLS-1", "Size", "0.8")], ["REFUTED", "CONFIRMED", "CONFIRMED"]), checked_on="2026-09-25")
        self.assertEqual(self.con.execute("SELECT count(*) FROM figures_of_merit").fetchone(), (0,))
        outcomes = [e["outcome"] for e in log]
        self.assertIn("not stored: refuted by the checker", outcomes)
        self.assertEqual(outcomes.count("not stored: no simulant of exactly this name"), 2)

    def test_applying_twice_does_not_duplicate(self):
        r = result([row("MLS-1", "Composition", "0.82")], ["CONFIRMED"])
        apply_document(self.con, r, checked_on="2026-09-25"); apply_document(self.con, r, checked_on="2026-09-25")
        self.assertEqual(self.con.execute("SELECT count(*) FROM figures_of_merit").fetchone(), (1,))

    def test_a_score_that_is_not_a_number_is_not_stored(self):
        log = apply_document(self.con, result([row("MLS-1", "Composition", "n/a")], ["CONFIRMED"]), checked_on="2026-09-25")
        self.assertEqual(self.con.execute("SELECT count(*) FROM figures_of_merit").fetchone(), (0,))

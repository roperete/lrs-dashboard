"""Adding a simulant the database lacks, from a paper that characterises it.

Zémeny et al. 2024 (the Luna Analog Facility paper) characterises three lunar highland
simulants from Lumina Sustainable Minerals — Lunar90, Lunar250, Lunar2000 — that the database
did not hold. A new record starts from the paper: it exists because a reader and a checker
confirmed the paper names it, and every value it carries comes from the same confirmed reading,
cited to the paper as a reference of its own (not a data sheet).

Run:  python3 -m unittest scripts.tests.test_add_simulant
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from provenance import ensure_provenance_schema  # noqa: E402
from add_simulant import add_from_paper, next_simulant_id  # noqa: E402

PAPER = {"doi": "10.3389/frspt.2024.1510635", "title": "The Luna Analog Facility testbeds (ESA, EAC)", "authors": "Zémeny et al.",
         "year": 2024, "path": "/x/Sources/papers/Zemeny_2024.pdf", "url": "https://doi.org/10.3389/frspt.2024.1510635"}


def finding(name="Lunar90", verdict="CONFIRMED"):
    reading = {"simulant_id": name, "document_id": "", "notes": "", "not_stated": [],
               "names_quote": "Lumina Sustainable Lunar90 Lumina90 0-90 um 4.95 kg", "names_location": "Table 1, p.3",
               "values": [
                   {"field": "institution", "value": "Lumina Sustainable Materials Ltd.", "table": "Table 1", "page": "3", "quote": "Lumina Sustainable Materials Ltd."},
                   {"field": "lunar_sample_reference", "value": "Highlands", "table": "Table 1", "page": "3", "quote": "The three lunar highland simulants purchased from Lumina"},
                   {"field": "particle_size_distribution", "value": "0–90 µm", "table": "Table 1", "page": "3", "quote": "Lunar90 Lumina90 0–90 μm"},
                   {"field": "oxide:SiO2", "value": "46.1", "table": "Table 4", "page": "9", "quote": "SiO2 46.1"},
                   {"field": "mineral:Anorthite", "value": "88.0", "table": "Table 5", "page": "10", "quote": "anorthite 88.0"},
                   {"field": "cohesion", "value": "0.5 kPa", "table": "Table 3", "page": "7", "quote": "c = 0.5 kPa"},
               ]}
    check = {"simulant_id": name, "notes": "", "missed": [],
             "names_verdict": verdict,
             "checks": [{"field": v["field"], "verdict": "CONFIRMED", "note": ""} for v in reading["values"]]}
    return {"name": name, "reading": reading, "check": check}


class AddTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        con = sqlite3.connect(Path(self.tmp.name) / "lrs.sqlite")
        con.executescript((ROOT / "scripts" / "schema.sql").read_text()); ensure_provenance_schema(con)
        con.execute("INSERT INTO simulants (simulant_id, name) VALUES ('S158','LuSIC-1')")
        con.commit(); self.con = con

    def tearDown(self):
        self.con.close(); self.tmp.cleanup()

    def test_ids_continue_from_the_highest(self):
        self.assertEqual(next_simulant_id(self.con), "S159")

    def test_a_confirmed_product_becomes_a_record_with_every_value_cited(self):
        log = add_from_paper(self.con, finding(), PAPER, sources_root="/x/Sources", checked_on="2026-09-25")
        s = self.con.execute("SELECT simulant_id, name, institution, lunar_sample_reference, cohesion, composition_status FROM simulants WHERE name='Lunar90'").fetchone()
        self.assertEqual(s[:4], ("S159", "Lunar90", "Lumina Sustainable Materials Ltd.", "Highlands"))
        self.assertAlmostEqual(float(s[4]), 0.5)
        self.assertEqual(s[5], "verified")
        ref = self.con.execute("SELECT reference_id, reference_type, doi, names_simulant, mention_quote FROM references_ WHERE simulant_id='S159'").fetchone()
        self.assertEqual(ref[1:4], ("composition", "10.3389/frspt.2024.1510635", 1))
        self.assertIn("Lunar90", ref[4])
        cited = {r[0] for r in self.con.execute("SELECT reference_id FROM property_sources WHERE simulant_id='S159'")}
        self.assertEqual(cited, {ref[0]})
        self.assertEqual(self.con.execute("SELECT reference_id FROM chemical_compositions WHERE simulant_id='S159'").fetchone(), (ref[0],))
        self.assertEqual(self.con.execute("SELECT datasheet_url FROM simulants WHERE simulant_id='S159'").fetchone(), (None,))

    def test_a_product_the_checker_did_not_confirm_is_not_added(self):
        log = add_from_paper(self.con, finding(verdict="REFUTED"), PAPER, sources_root="/x/Sources", checked_on="2026-09-25")
        self.assertEqual(self.con.execute("SELECT count(*) FROM simulants WHERE name='Lunar90'").fetchone(), (0,))
        self.assertTrue(any(e["outcome"] == "not added: the checker did not confirm the paper names it" for e in log))

    def test_adding_twice_does_not_duplicate(self):
        add_from_paper(self.con, finding(), PAPER, sources_root="/x/Sources", checked_on="2026-09-25")
        add_from_paper(self.con, finding(), PAPER, sources_root="/x/Sources", checked_on="2026-09-25")
        self.assertEqual(self.con.execute("SELECT count(*) FROM simulants WHERE name='Lunar90'").fetchone(), (1,))


class PaperShapeTests(unittest.TestCase):
    """What the Lumina reading actually looked like (2026-09-25)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        con = sqlite3.connect(Path(self.tmp.name) / "lrs.sqlite")
        con.executescript((ROOT / "scripts" / "schema.sql").read_text()); ensure_provenance_schema(con)
        con.execute("INSERT INTO simulants (simulant_id, name) VALUES ('S158','LuSIC-1')"); con.commit()
        self.con = con
        V = lambda f, v, t: {"field": f, "value": v, "table": t, "page": "3", "quote": f"{f} {v}"}
        reading = {"names_quote": "Lumina Sustainable Lunar90 Lumina90 0-90 um", "names_location": "Table 1", "notes": "", "values": [
            V("institution", "Lumina Sustainable Materials Ltd.", "Table 1"),
            V("institution", "Lumina Sustainable Materials Ltd. (https://www.luminamaterials.com)", "running text, Section 2.1"),
            V("mineral:Ca plagioclase (AMICS, area%)", "86.67% (major phase)", "AMICS modal mineralogy"),
            V("mineral:quartz (AMICS, area%)", "4.14% (minor phase)", "AMICS modal mineralogy"),
            V("mineral:muscovite (AMICS, area%)", "1.91%", "AMICS modal mineralogy"),
            V("mineral:quartz (Mineralogic SEM-EDS, petrolab, wt%)", "3.1 wt%", "Section 3.6.4"),
            V("mineral:anorthite (Mineralogic SEM-EDS, petrolab, wt%)", "87.4–89.9 wt%", "Section 3.6.4"),
        ]}
        check = {"names_verdict": "CONFIRMED", "missed": [], "checks": [
            {"field": "institution [Lumina Sustainable Materials Ltd., Table 1]", "verdict": "CONFIRMED", "note": ""},
            {"field": "institution [with URL, Section 2.1]", "verdict": "CONFIRMED", "note": ""},
            {"field": "mineral:Ca plagioclase (AMICS, area%) [86.67%]", "verdict": "CONFIRMED", "note": ""},
            {"field": "mineral:quartz (AMICS, area%) [4.14%]", "verdict": "CONFIRMED", "note": ""},
            {"field": "mineral:muscovite (AMICS, area%)", "verdict": "CONFIRMED", "note": ""},
            {"field": "mineral:quartz (Mineralogic SEM-EDS, petrolab, wt%)", "verdict": "CONFIRMED", "note": ""},
            {"field": "mineral:anorthite (Mineralogic SEM-EDS, petrolab, wt%)", "verdict": "CONFIRMED", "note": ""},
        ]}
        self.log = add_from_paper(con, {"name": "Lunar90", "reading": reading, "check": check}, PAPER, sources_root="/x/Sources", checked_on="2026-09-25")

    def tearDown(self):
        self.con.close(); self.tmp.cleanup()

    def test_a_checker_label_in_brackets_still_matches_the_field(self):
        self.assertEqual(self.con.execute("SELECT institution FROM simulants WHERE name='Lunar90'").fetchone(), ("Lumina Sustainable Materials Ltd.",))

    def test_one_mineral_analysis_per_table_named_without_its_method(self):
        rows = self.con.execute("SELECT component_name, value_pct, value_text FROM mineral_compositions ORDER BY value_pct DESC").fetchall()
        self.assertEqual([r[0] for r in rows], ["Ca plagioclase", "quartz", "muscovite"])
        self.assertAlmostEqual(rows[1][1], 4.14)
        self.assertIn("AMICS", rows[0][2])
        self.assertTrue(any(e["outcome"].startswith("not merged: a second mineral analysis") for e in self.log))


class FreeFormCheckerLabelTests(unittest.TestCase):
    def test_a_checker_rewording_the_field_still_matches(self):
        from add_simulant import field_key
        self.assertEqual(field_key("mineral:Ca plagioclase (AMICS) 86.67%"), field_key("mineral:Ca plagioclase (AMICS, area%)"))
        self.assertEqual(field_key("oxide:SiO2 48.4–49.8 wt% joint"), field_key("oxide:SiO2"))
        self.assertEqual(field_key("institution [Table 1]"), field_key("institution"))
        self.assertNotEqual(field_key("mineral:quartz (AMICS)"), field_key("mineral:quartz (Mineralogic SEM-EDS)"))

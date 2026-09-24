"""Moving a simulant to a newer version of its manufacturer data sheet.

Hispansion published new data sheets for TLH-0 (v1.4) and TLM-0 (v2.2) after the database
was built from v1.1. The new sheets report iron as FeO rather than Fe2O3 and measure sodium
that v1.1 reported as below detection, so linking them over the old numbers would put a
citation above values it does not state. Rules under test:

  * a composition table is one analysis: when the new sheet restates it, the whole table is
    replaced, never merged row by row (Fe2O3 from one version and FeO from the other would
    count the iron twice);
  * a value is taken from the new sheet only when the reader and the checker both confirm
    it; a refuted value, or one only the checker found, is logged and not applied;
  * a value the new sheet does not restate keeps its citation to the previous version;
  * the new sheet becomes a reference row of its own, the link and source line point at it,
    and the previous version stays as a reference marked superseded;
  * running it twice changes nothing.

Run:  python3 -m unittest scripts.tests.test_supersede_sheet
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from provenance import ensure_provenance_schema  # noqa: E402
from supersede_sheet import supersede, version_of  # noqa: E402

URL = "https://www.hispansion.io/_files/ugd/abc.pdf"


def make_db(path):
    con = sqlite3.connect(path)
    con.executescript((ROOT / "scripts" / "schema.sql").read_text())
    ensure_provenance_schema(con)
    con.execute("INSERT INTO simulants (simulant_id, name, composition_status, nasa_fom_score, bulk_density, datasheet_document_id, "
                "composition_source_title, composition_source_kind) VALUES ('S1','TLH-0','verified',91.7,'1.67','TDS-TLH-0-v1.1',"
                "'Hispansion TDS v1.1','manufacturer_datasheet')")
    con.execute("INSERT INTO references_ (reference_id, simulant_id, reference_type, title, names_simulant) "
                "VALUES ('DS-S1','S1','datasheet','Hispansion Technical Data Sheet TDS-TLH-0-v1.1',1)")
    con.executemany("INSERT INTO chemical_compositions (composition_id, simulant_id, component_type, component_name, value_wt_pct, reference_id) VALUES (?,?,?,?,?,?)",
                    [("CH1", "S1", "oxide", "SiO2", 46.43, "DS-S1"), ("CH2", "S1", "oxide", "Fe2O3", 6.78, "DS-S1"),
                     ("CH3", "S1", "oxide", "Na2O", 0.0, "DS-S1")])
    con.execute("INSERT INTO mineral_compositions (composition_id, simulant_id, component_type, component_name, value_pct, reference_id) "
                "VALUES ('C1','S1','mineral','Anorthite',57.0,'DS-S1')")
    con.executemany("INSERT INTO property_sources (simulant_id, field, reference_id, location, quote) VALUES (?,?,?,?,?)",
                    [("S1", "nasa_fom_score", "DS-S1", "p.1", "Mean NASA FoM Score: 91.7%"),
                     ("S1", "bulk_density", "DS-S1", "Table 6", "mean 1.67")])
    con.commit()
    return con


def finding():
    reading = {"simulant_id": "S1", "document_id": "TDS-TLH-0-v1.4", "not_stated": ["bulk_density"], "notes": "",
               "values": [
                   {"field": "oxide:SiO2", "value": "46.08", "table": "Table 1", "page": "1", "quote": "46.08 0.81 24.87"},
                   {"field": "oxide:FeO", "value": "6.73", "table": "Table 1", "page": "1", "quote": "6.73"},
                   {"field": "oxide:Na2O", "value": "1.51", "table": "Table 1", "page": "1", "quote": "1.51"},
                   {"field": "mineral:Anorthite", "value": "55.1", "table": "Table 4", "page": "2", "quote": "Anorthite 55.1"},
                   {"field": "nasa_fom_score", "value": "88.7%", "table": "Summary", "page": "1", "quote": "Mean NASA FoM Score: 88.7%"},
                   {"field": "cohesion", "value": "9.9", "table": "Table 7", "page": "3", "quote": "cohesion 9.9"},
                   {"field": "datasheet_document_id", "value": "TDS-TLH-0-v1.4", "table": "header", "page": "1", "quote": "TDS-TLH-0-v1.4"},
               ]}
    check = {"simulant_id": "S1", "notes": "",
             "checks": [{"field": f, "verdict": "CONFIRMED", "note": ""} for f in
                        ("oxide:SiO2", "oxide:FeO", "oxide:Na2O", "mineral:Anorthite", "nasa_fom_score", "datasheet_document_id")]
                       + [{"field": "cohesion", "verdict": "REFUTED", "note": "not on the sheet"}],
             "missed": [{"field": "ph", "value": "8.1", "table": "Table 9", "page": "4", "quote": "pH 8.1"}]}
    return {"simulant_id": "S1", "name": "TLH-0", "path": "/x/Sources/datasheets/Hispansion/TLH-0_TDS_v1.4.pdf",
            "url": URL, "reading": reading, "check": check}


class SupersedeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.con = make_db(Path(self.tmp.name) / "lrs.sqlite")
        self.log = supersede(self.con, finding(), sources_root="/x/Sources", checked_on="2026-09-24")

    def tearDown(self):
        self.con.close(); self.tmp.cleanup()

    def q(self, sql, *a):
        return self.con.execute(sql, a).fetchall()

    def test_version_is_read_from_the_document_id(self):
        self.assertEqual(version_of("TDS-TLH-0-v1.4"), "v1.4")
        self.assertEqual(version_of("TDS-TLM-0-v2.2"), "v2.2")

    def test_the_new_sheet_is_its_own_reference(self):
        self.assertEqual(self.q("SELECT reference_type, url, local_path, names_simulant FROM references_ WHERE reference_id='DS-S1-v1.4'"),
                         [("datasheet", URL, "datasheets/Hispansion/TLH-0_TDS_v1.4.pdf", 1)])

    def test_the_oxide_table_is_replaced_whole(self):
        rows = self.q("SELECT component_name, value_wt_pct, reference_id FROM chemical_compositions WHERE simulant_id='S1' ORDER BY component_name")
        self.assertEqual(rows, [("FeO", 6.73, "DS-S1-v1.4"), ("Na2O", 1.51, "DS-S1-v1.4"), ("SiO2", 46.08, "DS-S1-v1.4")])

    def test_the_mineral_table_is_replaced_whole(self):
        self.assertEqual(self.q("SELECT component_name, value_pct, reference_id FROM mineral_compositions WHERE simulant_id='S1'"),
                         [("Anorthite", 55.1, "DS-S1-v1.4")])

    def test_a_confirmed_value_replaces_the_old_one_with_its_new_source(self):
        self.assertEqual(self.q("SELECT nasa_fom_score FROM simulants WHERE simulant_id='S1'"), [(88.7,)])
        self.assertEqual(self.q("SELECT reference_id, quote FROM property_sources WHERE simulant_id='S1' AND field='nasa_fom_score'"),
                         [("DS-S1-v1.4", "Mean NASA FoM Score: 88.7%")])

    def test_a_value_the_new_sheet_does_not_restate_keeps_its_old_citation(self):
        self.assertEqual(self.q("SELECT bulk_density FROM simulants WHERE simulant_id='S1'"), [("1.67",)])
        self.assertEqual(self.q("SELECT reference_id FROM property_sources WHERE simulant_id='S1' AND field='bulk_density'"), [("DS-S1",)])

    def test_refuted_and_checker_only_values_are_not_applied(self):
        self.assertEqual(self.q("SELECT cohesion, ph FROM simulants WHERE simulant_id='S1'"), [(None, None)])
        outcomes = {e["outcome"] for e in self.log}
        self.assertIn("not applied: refuted by the checker", outcomes)
        self.assertIn("not applied: found only by the checker", outcomes)

    def test_the_link_and_source_line_point_at_the_new_sheet(self):
        s = self.q("SELECT datasheet_url, composition_source_url, composition_source_title, datasheet_document_id FROM simulants WHERE simulant_id='S1'")[0]
        self.assertEqual(s[0], URL); self.assertEqual(s[1], URL)
        self.assertIn("v1.4", s[2]); self.assertEqual(s[3], "TDS-TLH-0-v1.4")

    def test_the_previous_version_is_kept_and_marked_superseded(self):
        self.assertIn("superseded by v1.4", self.q("SELECT title FROM references_ WHERE reference_id='DS-S1'")[0][0])

    def test_running_it_twice_changes_nothing(self):
        before = [tuple(r) for t in ("simulants", "chemical_compositions", "mineral_compositions", "property_sources", "references_")
                  for r in self.con.execute(f"SELECT * FROM {t} ORDER BY 1")]
        supersede(self.con, finding(), sources_root="/x/Sources", checked_on="2026-09-24")
        after = [tuple(r) for t in ("simulants", "chemical_compositions", "mineral_compositions", "property_sources", "references_")
                 for r in self.con.execute(f"SELECT * FROM {t} ORDER BY 1")]
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()


class NormalisationTests(unittest.TestCase):
    """What a sheet prints is not always fit to show as printed.

    Both 2026 Hispansion sheets misspell forsterite as "Fosterite"; a reader wrote
    "Amorphous / Glass" where the sheet prints "Amorphous/Glass"; and availability is a
    paragraph where the database keeps a category that drives the filters.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.con = make_db(Path(self.tmp.name) / "lrs.sqlite")
        self.con.execute("UPDATE simulants SET availability='Available' WHERE simulant_id='S1'")
        f = finding()
        f["reading"]["values"] += [
            {"field": "mineral:Fosterite", "value": "1.8", "table": "Table 4", "page": "2", "quote": "Fosterite 1.8"},
            {"field": "mineral:Amorphous / Glass", "value": "19.2", "table": "Table 4", "page": "2", "quote": "Amorphous/Glass 19.2"},
            {"field": "availability", "value": "Available for purchase at https://www.hispansion.io/shop for low-volume orders.",
             "table": "3. Other Information", "page": "7", "quote": "Available for purchase at https://www.hispansion.io/shop"},
        ]
        f["check"]["checks"] += [{"field": x, "verdict": "CONFIRMED", "note": ""} for x in
                                 ("mineral:Fosterite", "mineral:Amorphous / Glass", "availability")]
        self.log = supersede(self.con, f, sources_root="/x/Sources", checked_on="2026-09-24")

    def tearDown(self):
        self.con.close(); self.tmp.cleanup()

    def test_a_misspelt_mineral_is_stored_under_its_name(self):
        names = {r[0] for r in self.con.execute("SELECT component_name FROM mineral_compositions WHERE simulant_id='S1'")}
        self.assertIn("Forsterite", names)
        self.assertNotIn("Fosterite", names)
        self.assertTrue(any(e.get("outcome") == "renamed: Fosterite -> Forsterite" for e in self.log))

    def test_spacing_inside_a_mineral_name_follows_the_sheet(self):
        names = {r[0] for r in self.con.execute("SELECT component_name FROM mineral_compositions WHERE simulant_id='S1'")}
        self.assertIn("Amorphous/Glass", names)

    def test_availability_wording_becomes_its_category_and_keeps_the_quote(self):
        self.assertEqual(self.con.execute("SELECT availability FROM simulants WHERE simulant_id='S1'").fetchone(), ("Available",))
        self.assertEqual(self.con.execute("SELECT reference_id, quote FROM property_sources WHERE simulant_id='S1' AND field='availability'").fetchone(),
                         ("DS-S1-v1.4", "Available for purchase at https://www.hispansion.io/shop"))

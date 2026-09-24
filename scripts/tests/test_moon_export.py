"""The Moon section is exported under the same rule as the simulants: a value is shown only
when a document stating it is on record (lunar_sources). Identity fields (a site's id, name,
mission and programme; a sample's number and mission) are not measurements and are not gated.

Run:  python3 -m unittest scripts.tests.test_moon_export
"""

import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from provenance import ensure_provenance_schema  # noqa: E402
from moon import export_moon  # noqa: E402


class MoonExportTests(unittest.TestCase):
    def setUp(self):
        con = sqlite3.connect(":memory:")
        con.executescript((ROOT / "scripts" / "schema.sql").read_text()); ensure_provenance_schema(con)
        con.execute("INSERT INTO lunar_sites (site_id, name, mission, programme, date, lat, lng, samples_returned, description, "
                    "bulk_density, friction_angle, cohesion) VALUES ('A11','Apollo 11 - Sea of Tranquility','Apollo 11','Apollo',"
                    "'July 20, 1969',0.67416,23.47314,'21.55 kg','First crewed landing.',1.61,40.7,1.06)")
        con.execute("INSERT INTO lunar_references (sample_id, mission, landing_site, coordinates, type, sample_description, "
                    "chemical_composition, mineral_composition, sources) VALUES ('10084','Apollo 11','Mare Tranquillitatis',"
                    "'{\"lat\": 0.67, \"lon\": 23.47}','Mare','Bulk soil','{\"SiO2\": 42.2, \"TiO2\": 7.5}','{\"Plagioclase\": 21.0}','[\"x\"]')")
        con.execute("INSERT INTO lunar_documents (document_id, title, local_path) VALUES ('LD-001','Wagner et al. 2017','papers/lunar/w.pdf'),"
                    "('LD-002','Lunar Sample Compendium 10084','papers/lunar/LSC_10084.pdf'),('LD-003','Unused','papers/lunar/u.pdf')")
        rows = [("A11", "lat", "LD-001", "Table 1", "Apollo 11 LM 0.67416 23.47314"),
                ("A11", "lng", "LD-001", "Table 1", "Apollo 11 LM 0.67416 23.47314"),
                ("A11", "bulk_density", "LD-002", "p. 3", "1.61 g/cm3"),
                ("10084", "oxide:SiO2", "LD-002", "Table 1", "SiO2 42.2"),
                ("10084", "landing_site", "LD-002", "p. 1", "Mare Tranquillitatis")]
        con.executemany("INSERT INTO lunar_sources (entity_id, field, document_id, location, quote) VALUES (?,?,?,?,?)", rows)
        self.con = con

    def test_only_sourced_site_values_are_exported(self):
        out = export_moon(self.con)
        a11 = out["lunar_sites"][0]
        self.assertEqual((a11["id"], a11["name"], a11["mission"], a11["type"]), ("A11", "Apollo 11 - Sea of Tranquility", "Apollo 11", "Apollo"))
        self.assertEqual((a11["lat"], a11["lng"]), (0.67416, 23.47314))
        self.assertEqual(a11["geotechnical"], {"bulk_density": 1.61})       # friction and cohesion have no source
        for k in ("date", "samples_returned", "description"):
            self.assertIsNone(a11[k])

    def test_only_sourced_sample_values_are_exported(self):
        s = export_moon(self.con)["lunar_reference"][0]
        self.assertEqual((s["sample_id"], s["mission"]), ("10084", "Apollo 11"))
        self.assertEqual(s["chemical_composition"], {"SiO2": 42.2})
        self.assertIsNone(s["mineral_composition"])
        self.assertEqual(s["landing_site"], "Mare Tranquillitatis")
        self.assertIsNone(s["type"])

    def test_hidden_values_are_listed(self):
        hidden = {(h["entity_id"], h["field"]) for h in export_moon(self.con)["hidden"]}
        self.assertIn(("A11", "cohesion"), hidden)
        self.assertIn(("10084", "oxide:TiO2"), hidden)
        self.assertIn(("10084", "mineral:Plagioclase"), hidden)
        self.assertNotIn(("A11", "lat"), hidden)

    def test_only_cited_documents_and_their_sources_are_exported(self):
        out = export_moon(self.con)
        self.assertEqual([d["document_id"] for d in out["lunar_documents"]], ["LD-001", "LD-002"])
        self.assertEqual(len(out["lunar_sources"]), 5)
        self.assertNotIn("local_path", out["lunar_documents"][0])

    def test_a_site_without_sourced_coordinates_is_not_exported(self):
        # a marker needs both coordinates; a site we cannot place is left off the map
        self.con.execute("DELETE FROM lunar_sources WHERE field='lng'")
        self.assertEqual(export_moon(self.con)["lunar_sites"], [])


if __name__ == "__main__":
    unittest.main()

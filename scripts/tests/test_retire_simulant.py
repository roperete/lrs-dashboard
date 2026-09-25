"""Retiring a simulant record that is not a real product.

TUBS-H (S068) was entered as an ESA product, but the only document cited for it is the
TUBS-M / TUBS-T paper, which describes no such product; the owner decided to retire it.
Retirement removes the record from every table so it leaves the export, keeps a full
copy of the deleted rows under documentation/retired/, and appends a line to the register
so the decision and its reason stay on record.

Run:  python3 -m unittest scripts.tests.test_retire_simulant
"""

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from provenance import ensure_provenance_schema  # noqa: E402
from retire_simulant import retire, tables_with_simulant_id, write_archive, append_register  # noqa: E402


def make_db(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript((ROOT / "scripts" / "schema.sql").read_text())
    ensure_provenance_schema(con)
    con.execute("INSERT INTO simulants (simulant_id, name, institution, composition_status) VALUES ('S068','TUBS-H','ESA','not_extracted')")
    con.execute("INSERT INTO simulants (simulant_id, name, institution, composition_status) VALUES ('S069','TUBS-M','TU Braunschweig','withheld_unverified')")
    con.execute("INSERT INTO sites (site_id, simulant_id, site_name) VALUES ('X068','S068','EAC Cologne')")
    con.execute("INSERT INTO sites (site_id, simulant_id, site_name) VALUES ('X069','S069','Braunschweig')")
    con.execute("INSERT INTO references_ (reference_id, simulant_id, reference_text, doi) VALUES ('R053','S068','Linke 2020','10.1016/j.pss.2019.104747')")
    con.execute("INSERT INTO references_ (reference_id, simulant_id, reference_text, doi) VALUES ('R054','S069','Linke 2020','10.1016/j.pss.2019.104747')")
    con.execute("INSERT INTO simulant_extra (simulant_id, name) VALUES ('S068','TUBS-H')")
    con.execute("INSERT INTO purchase_info (simulant_id, vendor) VALUES ('S068','ESA')")
    con.execute("INSERT INTO property_sources (simulant_id, field, reference_id) VALUES ('S068','cohesion','R053')")
    con.commit()
    con.close()


class RetireTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "lrs.sqlite"
        make_db(self.db)
        self.con = sqlite3.connect(self.db)
        self.con.row_factory = sqlite3.Row

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def test_every_table_with_a_simulant_id_column_is_covered(self):
        tables = tables_with_simulant_id(self.con)
        for t in ("simulants", "sites", "references_", "simulant_extra", "purchase_info", "property_sources", "chemical_compositions", "mineral_compositions", "mineral_groups"):
            self.assertIn(t, tables)
        self.assertNotIn("lunar_references", tables)

    def test_retire_removes_every_row_and_archives_them(self):
        archive = retire(self.con, "S068", reason="Not a distinct product; the cited paper describes TUBS-M and TUBS-T.", alias_of=["S069", "S070"], today="2026-09-22")
        for t in ("simulants", "sites", "references_", "simulant_extra", "purchase_info", "property_sources"):
            self.assertEqual(self.con.execute(f"SELECT COUNT(*) FROM {t} WHERE simulant_id='S068'").fetchone()[0], 0, t)
        # The sibling record is untouched.
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM simulants WHERE simulant_id='S069'").fetchone()[0], 1)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM references_ WHERE simulant_id='S069'").fetchone()[0], 1)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM sites").fetchone()[0], 1)
        # The archive holds what was deleted.
        self.assertEqual(archive["simulant_id"], "S068")
        self.assertEqual(archive["name"], "TUBS-H")
        self.assertEqual(archive["retired_on"], "2026-09-22")
        self.assertEqual(archive["alias_of"], ["S069", "S070"])
        self.assertEqual(archive["rows"]["simulants"][0]["institution"], "ESA")
        self.assertEqual(archive["rows"]["references_"][0]["reference_id"], "R053")
        self.assertEqual(archive["rows"]["property_sources"][0]["field"], "cohesion")
        self.assertEqual(sum(len(v) for v in archive["rows"].values()), 6)

    def test_unknown_id_is_refused(self):
        with self.assertRaises(ValueError):
            retire(self.con, "S999", reason="x", alias_of=[], today="2026-09-22")

    def test_archive_file_and_register_line(self):
        archive = retire(self.con, "S068", reason="Not a distinct product.", alias_of=["S069"], today="2026-09-22")
        docs = Path(self.tmp.name) / "documentation"
        path = write_archive(archive, docs)
        self.assertEqual(path, docs / "retired" / "S068-TUBS-H-2026-09-22.json")
        self.assertEqual(json.loads(path.read_text())["name"], "TUBS-H")
        register = docs / "retired-simulants.md"
        append_register(archive, register)
        text = register.read_text()
        self.assertIn("# Retired simulants", text)
        self.assertIn("| S068 | TUBS-H | 2026-09-22 | S069 | Not a distinct product. |", text)
        # A second retirement appends without repeating the header.
        append_register(dict(archive, simulant_id="S001", name="AGK-2010", alias_of=[]), register)
        text = register.read_text()
        self.assertEqual(text.count("# Retired simulants"), 1)
        self.assertIn("| S001 | AGK-2010 | 2026-09-22 | — | Not a distinct product. |", text)


if __name__ == "__main__":
    unittest.main()

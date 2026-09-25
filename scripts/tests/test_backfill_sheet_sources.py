"""Task 3 of the per-value provenance plan: cite the data sheet for the 18 verified simulants.

For a simulant whose composition was verified against a manufacturer data sheet, the
sheet becomes a `datasheet` reference row, every composition row cites it, and every
scalar field the sheet states gets a property_sources row. A scalar the sheet does NOT
state (LHS-1's specific gravity 2.77) gets no row and will therefore not be exported.

Run:  python3 -m unittest scripts.tests.test_backfill_sheet_sources
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from backfill_sheet_sources import backfill, datasheet_reference_id  # noqa: E402
from provenance import ensure_provenance_schema  # noqa: E402


def make_db(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript((ROOT / "scripts" / "schema.sql").read_text())
    ensure_provenance_schema(con)
    con.execute("""INSERT INTO simulants (simulant_id, name, bulk_density, specific_gravity, cohesion, ph,
                   composition_status, composition_source_kind, composition_source_title, composition_source_url,
                   datasheet_url, datasheet_document_id, datasheet_date)
                   VALUES ('S001','LHS-1','1.40',2.77,'0.311',9.75,'verified','manufacturer_datasheet',
                           'LHS-1 Fact Sheet','https://cdn.example/LHS-1.pdf','https://cdn.example/LHS-1.pdf','003-01-001-1225','2025-12')""")
    con.execute("""INSERT INTO simulants (simulant_id, name, bulk_density, composition_status)
                   VALUES ('S002','WITHHELD-1','1.2','withheld_unverified')""")
    con.executemany(
        "INSERT INTO chemical_compositions (composition_id, simulant_id, component_type, component_name, value_wt_pct) VALUES (?,?,?,?,?)",
        [("CH-S001-01", "S001", "oxide", "SiO2", 49.12), ("CH-S001-02", "S001", "oxide", "Al2O3", 26.29)])
    con.executemany(
        "INSERT INTO mineral_compositions (composition_id, simulant_id, component_type, component_name, value_pct) VALUES (?,?,?,?,?)",
        [("C-S001-01", "S001", "mineral", "Anorthosite", 74.4)])
    con.execute("INSERT INTO references_ (reference_id, simulant_id, reference_text, reference_type) VALUES ('R001','S001','Long-Fox 2023 geomechanics','geotechnical')")
    con.commit()
    con.close()


# Which scalar fields the sheet states, per simulant: the shape backfill() consumes.
SHEET_FIELDS = {"S001": {"bulk_density": "Uncompressed Bulk Density: 1.40 g/cm3",
                         "cohesion": "Cohesion: 0.311 kPa",
                         "ph": "pH: 9.75"}}


class BackfillTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "b.sqlite"
        make_db(self.db)
        self.log = backfill(self.db, SHEET_FIELDS, checked_on="2026-09-22")
        self.con = sqlite3.connect(self.db)

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def test_datasheet_reference_row_is_created_once(self):
        rid = datasheet_reference_id("S001")
        rows = self.con.execute("SELECT reference_type, title, url, names_simulant, checked_on FROM references_ WHERE reference_id=?", (rid,)).fetchall()
        self.assertEqual(len(rows), 1)
        rtype, title, url, names, checked = rows[0]
        self.assertEqual(rtype, "datasheet")
        self.assertIn("LHS-1", title)
        self.assertEqual(url, "https://cdn.example/LHS-1.pdf")
        self.assertEqual(names, 1)
        self.assertEqual(checked, "2026-09-22")

    def test_all_composition_rows_cite_the_sheet(self):
        rid = datasheet_reference_id("S001")
        chem = [r[0] for r in self.con.execute("SELECT reference_id FROM chemical_compositions WHERE simulant_id='S001'")]
        mins = [r[0] for r in self.con.execute("SELECT reference_id FROM mineral_compositions WHERE simulant_id='S001'")]
        self.assertEqual(chem, [rid, rid])
        self.assertEqual(mins, [rid])

    def test_sheet_stated_scalars_get_a_source_row_with_the_quote(self):
        rows = {f: (r, q) for f, r, q in self.con.execute("SELECT field, reference_id, quote FROM property_sources WHERE simulant_id='S001'")}
        self.assertEqual(set(rows), {"bulk_density", "cohesion", "ph"})
        self.assertEqual(rows["cohesion"], (datasheet_reference_id("S001"), "Cohesion: 0.311 kPa"))

    def test_scalar_the_sheet_does_not_state_gets_no_row(self):
        n = self.con.execute("SELECT count(*) FROM property_sources WHERE simulant_id='S001' AND field='specific_gravity'").fetchone()[0]
        self.assertEqual(n, 0)
        unsourced = [e for e in self.log if e.get("outcome") == "unsourced on a verified simulant"]
        self.assertEqual([(e["simulant_id"], e["field"]) for e in unsourced], [("S001", "specific_gravity")])

    def test_withheld_simulant_is_untouched(self):
        self.assertEqual(self.con.execute("SELECT count(*) FROM references_ WHERE simulant_id='S002' AND reference_type='datasheet'").fetchone()[0], 0)
        self.assertEqual(self.con.execute("SELECT count(*) FROM property_sources WHERE simulant_id='S002'").fetchone()[0], 0)

    def test_existing_paper_reference_is_left_alone(self):
        row = self.con.execute("SELECT reference_type, names_simulant FROM references_ WHERE reference_id='R001'").fetchone()
        self.assertEqual(row, ("geotechnical", None))

    def test_second_run_is_idempotent(self):
        again = backfill(self.db, SHEET_FIELDS, checked_on="2026-09-22")
        self.assertEqual([e for e in again if e.get("outcome") not in ("unsourced on a verified simulant",)], [])
        self.assertEqual(self.con.execute("SELECT count(*) FROM references_ WHERE reference_type='datasheet'").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()

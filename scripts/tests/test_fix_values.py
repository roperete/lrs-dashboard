"""Repairing values already stored as text, and citations that prove nothing.

The same defect the apply step now refuses was already in the database on 2026-09-23:
107 values that parse to one number were sitting as text, 22 more were not numbers at all,
eight mineral rows were feedstock mixing ratios rather than minerals, and five references
pointed at this project's own registry. The repair converts what can be converted, keeps
the statement verbatim, removes the rest, and logs every change so none of it is lost.

Run:  python3 -m unittest scripts.tests.test_fix_values
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from provenance import ensure_provenance_schema  # noqa: E402
from fix_values import repair  # noqa: E402


def make_db(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.executescript((ROOT / "scripts" / "schema.sql").read_text())
    ensure_provenance_schema(con)
    con.executemany("INSERT INTO simulants (simulant_id, name, composition_status, particle_size_d50) VALUES (?,?,?,?)", [
        ("S1", "LX-M100", "verified", None), ("S2", "DNA-1", "verified", None), ("S3", "BH-1", "withheld_unverified", "38.22 μm"),
        ("S4", "NAO-1", "verified", "41–61 µm (median; mean 53–81 µm)"), ("S5", "CMU-1", "verified", None)])
    con.executemany("INSERT INTO references_ (reference_id, simulant_id, title, local_path, names_simulant) VALUES (?,?,?,?,?)", [
        ("R1", "S1", "Patzwald 2025", "papers/LRS/lx.pdf", 1),
        ("RN-S1-9", "S1", "Global Registry of Lunar Regolith Simulants (CSV compilation)", "papers/LRS/Sources/Global Registry of Lunar Regolith Simulants.html", 1),
        ("R3", "S3", "BH-1 paper", None, 1), ("R4", "S4", "NAO-1 paper", None, 1), ("R5", "S5", "CMU-1 paper", None, 1)])
    con.executemany("INSERT INTO chemical_compositions (composition_id, simulant_id, component_type, component_name, value_wt_pct, reference_id) VALUES (?,?,?,?,?,?)", [
        ("CH1", "S1", "oxide", "SiO2", "49.96 ± 0.60 wt.-%", "R1"),
        ("CH2", "S1", "oxide", "TiO2", 2.33, "R1"),
        ("CH3", "S1", "oxide", "P2O5", "<0.02", "R1")])
    con.executemany("INSERT INTO mineral_compositions (composition_id, simulant_id, component_type, component_name, value_pct, reference_id) VALUES (?,?,?,?,?,?)", [
        ("C1", "S1", "mineral", "Plagioclase", "31 wt.-%", "R1"),
        ("C2", "S2", "mineral", "Plagioclase", "present (checkmark, no wt% reported)", "R1"),
        ("C3", "S5", "mineral", "Coal", 63.0, "R5"),
        ("C4", "S5", "mineral", "Limestone", 37.0, "R5")])
    con.executemany("INSERT INTO property_sources (simulant_id, field, reference_id, location, quote) VALUES (?,?,?,?,?)", [
        ("S3", "particle_size_d50", "R3", "Table 2", "D50 38.22 μm"),
        ("S4", "particle_size_d50", "R4", "p.54", "median 41–61 µm")])
    con.commit()
    return con


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.con = make_db(Path(self.tmp.name) / "lrs.sqlite")
        self.log = repair(self.con, feedstock={("S5", "Coal"), ("S5", "Limestone")})

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def one(self, sql, *a):
        return self.con.execute(sql, a).fetchall()

    def test_a_stated_number_becomes_a_number_and_keeps_its_statement(self):
        self.assertEqual(self.one("SELECT value_wt_pct, typeof(value_wt_pct), value_text FROM chemical_compositions WHERE composition_id='CH1'"),
                         [(49.96, "real", "49.96 ± 0.60 wt.-%")])
        self.assertEqual(self.one("SELECT value_pct, value_text FROM mineral_compositions WHERE composition_id='C1'"), [(31.0, "31 wt.-%")])

    def test_a_row_already_numeric_is_untouched(self):
        self.assertEqual(self.one("SELECT value_wt_pct, value_text FROM chemical_compositions WHERE composition_id='CH2'"), [(2.33, None)])

    def test_a_row_that_is_not_a_number_is_removed_and_logged_verbatim(self):
        self.assertEqual(self.one("SELECT count(*) FROM chemical_compositions WHERE composition_id='CH3'"), [(0,)])
        self.assertEqual(self.one("SELECT count(*) FROM mineral_compositions WHERE composition_id='C2'"), [(0,)])
        gone = [e for e in self.log if e["action"] == "removed: not a single number"]
        self.assertEqual({e["stated"] for e in gone}, {"<0.02", "present (checkmark, no wt% reported)"})
        self.assertTrue(all(e["reference_id"] for e in gone))

    def test_feedstock_ratios_leave_the_mineral_table(self):
        self.assertEqual(self.one("SELECT count(*) FROM mineral_compositions WHERE simulant_id='S5'"), [(0,)])
        self.assertEqual(sum(1 for e in self.log if e["action"] == "removed: feedstock ratio, not a mineral"), 2)

    def test_a_numeric_property_stated_with_its_unit_is_parsed(self):
        self.assertEqual(self.one("SELECT particle_size_d50, typeof(particle_size_d50) FROM simulants WHERE simulant_id='S3'"), [(38.22, "real")])
        self.assertEqual(self.one("SELECT count(*) FROM property_sources WHERE simulant_id='S3'"), [(1,)])

    def test_a_range_in_a_numeric_property_is_cleared_with_its_source_row(self):
        self.assertEqual(self.one("SELECT particle_size_d50 FROM simulants WHERE simulant_id='S4'"), [(None,)])
        self.assertEqual(self.one("SELECT count(*) FROM property_sources WHERE simulant_id='S4'"), [(0,)])
        e = [e for e in self.log if e["action"] == "cleared: not a single number" and e["simulant_id"] == "S4"][0]
        self.assertEqual(e["quote"], "median 41–61 µm")

    def test_registry_citations_are_deleted(self):
        self.assertEqual(self.one("SELECT count(*) FROM references_ WHERE reference_id='RN-S1-9'"), [(0,)])
        self.assertEqual(self.one("SELECT count(*) FROM references_ WHERE reference_id='R1'"), [(1,)])
        self.assertTrue(any(e["action"] == "deleted: the project's own registry is not evidence" for e in self.log))

    def test_idempotent(self):
        again = repair(self.con, feedstock={("S5", "Coal"), ("S5", "Limestone")})
        self.assertEqual(again, [])


class ColumnUnitRepairTests(unittest.TestCase):
    """What was already stored with a unit is converted; what cannot be, is cleared and logged."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        con = sqlite3.connect(Path(self.tmp.name) / "lrs.sqlite")
        con.executescript((ROOT / "scripts" / "schema.sql").read_text())
        ensure_provenance_schema(con)
        con.executemany("INSERT INTO simulants (simulant_id, name, bulk_density, cohesion, friction_angle) VALUES (?,?,?,?,?)", [
            ("S1", "TLH-0", "1.80 g/cm3", "2.896 kPa", "46.12 º"),
            ("S2", "LX-M100", None, "185.2 Pa (AP-cohesive strength)", None),
            ("S3", "QH-E", None, "3.1 kPa (low stress level); 18.80 kPa (conventional stress level)", "1.2"),
        ])
        con.execute("INSERT INTO references_ (reference_id, simulant_id, title) VALUES ('R3','S3','QH-E paper')")
        con.execute("INSERT INTO property_sources (simulant_id, field, reference_id, quote) VALUES ('S3','cohesion','R3','3.1 kPa (low); 18.80 kPa')")
        con.commit()
        self.con = con
        self.log = repair(con, feedstock=set())

    def tearDown(self):
        self.con.close(); self.tmp.cleanup()

    def row(self, sid):
        return self.con.execute("SELECT bulk_density, cohesion, friction_angle FROM simulants WHERE simulant_id=?", (sid,)).fetchone()

    def test_units_are_stripped_into_the_column_unit(self):
        bd, c, f = self.row("S1")
        self.assertAlmostEqual(float(bd), 1.8); self.assertAlmostEqual(float(c), 2.896); self.assertAlmostEqual(float(f), 46.12)
        self.assertAlmostEqual(float(self.row("S2")[1]), 0.1852)

    def test_a_bare_number_is_left_alone(self):
        self.assertEqual(self.row("S3")[2], "1.2")

    def test_two_values_are_cleared_with_their_source_row(self):
        self.assertIsNone(self.row("S3")[1])
        self.assertEqual(self.con.execute("SELECT count(*) FROM property_sources WHERE simulant_id='S3' AND field='cohesion'").fetchone(), (0,))
        self.assertTrue(any(e["action"] == "cleared: not a single number" and e["field"] == "cohesion" for e in self.log))

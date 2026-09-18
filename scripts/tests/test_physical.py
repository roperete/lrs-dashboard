"""Tests for physical-property cleanup in scripts/reconcile.py.

Same policy as composition: a number stays only if a source supports it.
Two defects are provable without any source and are cleared everywhere:

  1. specific_gravity equal to bulk_density  -> the bulk density was copied
     into the specific-gravity column; it is not a measured specific gravity.
  2. specific_gravity below 2.0             -> below the density of any
     silicate mineral, so it cannot be a specific gravity.

Everything else is only corrected where an audited source states a value.

Run:  python3 -m unittest scripts.tests.test_physical
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from reconcile import (  # noqa: E402
    apply_physical,
    physical_corrections,
    suspect_specific_gravity,
)


class SuspectSpecificGravityTest(unittest.TestCase):
    def test_specific_gravity_equal_to_bulk_density_is_suspect(self):
        ok, why = suspect_specific_gravity(specific_gravity=1.67, bulk_density="1.67")
        self.assertTrue(ok)
        self.assertIn("bulk density", why.lower())

    def test_specific_gravity_below_two_is_suspect(self):
        ok, why = suspect_specific_gravity(specific_gravity=1.31, bulk_density="1.43")
        self.assertTrue(ok)
        self.assertIn("2.0", why)

    def test_plausible_specific_gravity_is_kept(self):
        ok, _ = suspect_specific_gravity(specific_gravity=2.77, bulk_density="1.40")
        self.assertFalse(ok)

    def test_missing_values_are_not_suspect(self):
        self.assertFalse(suspect_specific_gravity(None, "1.40")[0])
        self.assertFalse(suspect_specific_gravity(2.9, None)[0])

    def test_non_numeric_bulk_density_does_not_crash(self):
        ok, _ = suspect_specific_gravity(2.9, "1.40 - 1.65")
        self.assertFalse(ok)


class PhysicalCorrectionsTest(unittest.TestCase):
    def test_source_value_replaces_a_disagreeing_db_value(self):
        c = physical_corrections(
            source_physical={"bulk_density": "1.40", "particle_size_d50": "81.62"},
            db_row={"bulk_density": "0.81", "particle_size_d50": 10.22},
        )
        self.assertEqual(c["bulk_density"], "1.40")
        self.assertEqual(c["particle_size_d50"], 81.62)

    def test_agreeing_values_are_not_listed_as_corrections(self):
        c = physical_corrections(
            source_physical={"bulk_density": "1.40"},
            db_row={"bulk_density": "1.40"},
        )
        self.assertEqual(c, {})

    def test_numeric_agreement_ignores_string_versus_float(self):
        c = physical_corrections(
            source_physical={"particle_size_d50": "81.62"},
            db_row={"particle_size_d50": 81.62},
        )
        self.assertEqual(c, {})

    def test_source_fills_a_missing_db_value(self):
        c = physical_corrections(
            source_physical={"friction_angle": "31.49"},
            db_row={"friction_angle": None},
        )
        self.assertEqual(c["friction_angle"], "31.49")

    def test_particle_size_range_maps_to_the_distribution_column(self):
        c = physical_corrections(
            source_physical={"particle_size_range": "<0.04 - 1000 um"},
            db_row={"particle_size_distribution": None},
        )
        self.assertEqual(c["particle_size_distribution"], "<0.04 - 1000 um")

    def test_ph_is_ignored_because_there_is_no_column_for_it(self):
        c = physical_corrections(source_physical={"ph": "9.75"}, db_row={})
        self.assertEqual(c, {})

    def test_empty_source_values_are_ignored(self):
        c = physical_corrections(
            source_physical={"bulk_density": "", "cohesion": None},
            db_row={"bulk_density": "0.81"},
        )
        self.assertEqual(c, {})


def make_db(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript((ROOT / "scripts" / "schema.sql").read_text())
    con.executemany(
        "INSERT INTO simulants (simulant_id, name, bulk_density, specific_gravity, particle_size_d50) VALUES (?,?,?,?,?)",
        [
            ("S001", "COPY-SG", "1.67", 1.67, 137.6),   # SG copied from bulk density
            ("S002", "LOW-SG", "1.43", 1.31, 36.5),     # SG below 2.0
            ("S003", "GOOD-SG", "1.40", 2.77, 81.62),   # plausible, keep
            ("S004", "WRONG-PHYS", "0.81", None, 10.22),  # audited, source disagrees
        ],
    )
    con.commit()
    con.close()


class ApplyPhysicalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "p.sqlite"
        make_db(self.db)
        self.log = apply_physical(
            self.db,
            {"S004": {"bulk_density": "1.40", "particle_size_d50": 81.62}},
        )

    def tearDown(self):
        self.tmp.cleanup()

    def val(self, sid, col):
        con = sqlite3.connect(self.db)
        v = con.execute(f"SELECT {col} FROM simulants WHERE simulant_id=?", (sid,)).fetchone()[0]
        con.close()
        return v

    def test_copied_specific_gravity_is_cleared(self):
        self.assertIsNone(self.val("S001", "specific_gravity"))

    def test_low_specific_gravity_is_cleared(self):
        self.assertIsNone(self.val("S002", "specific_gravity"))

    def test_plausible_specific_gravity_survives(self):
        self.assertEqual(self.val("S003", "specific_gravity"), 2.77)

    def test_bulk_density_is_never_touched_by_the_sg_rule(self):
        self.assertEqual(self.val("S001", "bulk_density"), "1.67")

    def test_audited_corrections_are_applied(self):
        self.assertEqual(self.val("S004", "bulk_density"), "1.40")
        self.assertEqual(self.val("S004", "particle_size_d50"), 81.62)

    def test_log_explains_each_change(self):
        by = {(e["simulant_id"], e["field"]): e for e in self.log}
        self.assertIn(("S001", "specific_gravity"), by)
        self.assertIn("bulk density", by[("S001", "specific_gravity")]["reason"].lower())
        self.assertIn(("S004", "bulk_density"), by)
        self.assertEqual(by[("S004", "bulk_density")]["old"], "0.81")
        self.assertEqual(by[("S004", "bulk_density")]["new"], "1.40")

    def test_apply_is_idempotent(self):
        again = apply_physical(self.db, {"S004": {"bulk_density": "1.40", "particle_size_d50": 81.62}})
        self.assertEqual(again, [])


if __name__ == "__main__":
    unittest.main()

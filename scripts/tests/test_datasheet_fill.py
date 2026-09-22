"""Tests for scripts/datasheet_fill.py helpers.

The fill script transcribes values from manufacturer sheets into columns the schema
did not have. Two guards keep that honest: every numeric value written must appear
verbatim in the sheet's extracted text, and new columns are added idempotently.

Run:  python3 -m unittest scripts.tests.test_datasheet_fill
"""

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from datasheet_fill import ensure_columns, value_in_text  # noqa: E402


class ValueInTextTest(unittest.TestCase):
    SHEET = "Uncompressed Bulk Density: 1.40 g/cm3\nMedian Particle Size: 81.62 µm\npH: 9.75\nAngle of Repose (10g): 22.62°"

    def test_number_present_in_sheet_passes(self):
        self.assertTrue(value_in_text(self.SHEET, 81.62))
        self.assertTrue(value_in_text(self.SHEET, "1.40"))

    def test_number_absent_from_sheet_fails(self):
        self.assertFalse(value_in_text(self.SHEET, 0.81))

    def test_substring_of_a_longer_number_does_not_count(self):
        # 1.4 is not the same statement as 1.40; 9.7 is not 9.75
        self.assertFalse(value_in_text(self.SHEET, 9.7))

    def test_text_values_are_checked_case_insensitively(self):
        self.assertTrue(value_in_text(self.SHEET, "median particle size"))

    def test_trailing_zero_on_the_sheet_still_matches_the_same_number(self):
        # the sheet prints 10.30 and 390.50; Python spells them 10.3 and 390.5
        self.assertTrue(value_in_text("pH: 10.30\nMean: 390.50 µm", 10.3))
        self.assertTrue(value_in_text("pH: 10.30\nMean: 390.50 µm", 390.5))

    def test_trailing_zero_never_turns_an_integer_into_a_bigger_one(self):
        self.assertFalse(value_in_text("Total 100.00", 10))

    def test_ligatures_and_symbols_in_the_pdf_text_do_not_block_a_phrase(self):
        self.assertTrue(value_in_text("Simulant Type: Extra-ﬁne lunar highlands\n simulant for dust studies",
                                      "Extra-fine lunar highlands simulant for dust studies"))
        self.assertTrue(value_in_text("Series: TerraLun™- Core", "TerraLun Core"))

    def test_compound_text_checks_every_number_in_it(self):
        self.assertTrue(value_in_text(self.SHEET, "22.62° (10 g)"))
        self.assertFalse(value_in_text(self.SHEET, "22.62° (10 g), 36.58° (250 g)"))


class EnsureColumnsTest(unittest.TestCase):
    def test_adds_missing_columns_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "t.sqlite"
            con = sqlite3.connect(db)
            con.executescript((ROOT / "scripts" / "schema.sql").read_text())
            # columns the schema file does not define, so the first call has work to do
            wanted = [("zz_probe_a", "REAL"), ("zz_probe_b", "TEXT")]
            added = ensure_columns(con, "simulants", wanted)
            self.assertEqual(added, ["zz_probe_a", "zz_probe_b"])
            again = ensure_columns(con, "simulants", wanted)
            self.assertEqual(again, [])
            cols = {r[1] for r in con.execute("PRAGMA table_info(simulants)")}
            self.assertIn("zz_probe_a", cols)
            # and the schema file itself already carries the real sheet columns
            self.assertIn("ph", cols)
            con.close()


if __name__ == "__main__":
    unittest.main()

"""A physical value is stored as a bare number in the unit its column is shown in.

bulk_density, cohesion and friction_angle are text columns — some hold ranges — but the page
reads them as numbers and prints a fixed unit after them: g/cm³, kPa, °. A value stored with
its unit either disappeared (Number("1.80 g/cm3") is NaN) or was read in the wrong unit: the LX
simulants' "185.2 Pa" was shown as 185.2 kPa, a thousand times too large.

to_column_unit() converts a stated value into its column's unit, or refuses it. The
statement itself stays verbatim in the value's source row.

Run:  python3 -m unittest scripts.tests.test_column_units
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from parse_value import parse_number, to_column_unit, COLUMN_UNITS  # noqa: E402


class ColumnUnitTests(unittest.TestCase):
    CASES = {
        ("bulk_density", "1.80 g/cm3"): 1.8,
        ("bulk_density", "1.314 (kg/l, i.e. g/cm3)"): 1.314,
        ("bulk_density", "1.72 g/cc"): 1.72,
        ("bulk_density", "1640 kg/m3"): 1.64,
        ("bulk_density", "1.67"): 1.67,
        ("cohesion", "2.896 kPa"): 2.896,
        ("cohesion", "3.78 (kPa)"): 3.78,
        ("cohesion", "6.32 ± 0.7 kPa"): 6.32,
        ("cohesion", "185.2 Pa (AP-cohesive strength, ambient pressure, rheometer)"): 0.1852,
        ("cohesion", "0.02 MPa"): 20.0,
        ("cohesion", "1.0"): 1.0,
        ("friction_angle", "46.12 º"): 46.12,       # U+00BA, printed on the Hispansion sheets
        ("friction_angle", "44.6 ± 0.8°"): 44.6,
        ("friction_angle", "34.76 ± 6.79 (°)"): 34.76,
        ("friction_angle", "45 deg"): 45.0,
    }

    def test_each_value_lands_in_its_column_unit(self):
        for (field, raw), want in self.CASES.items():
            with self.subTest(field=field, raw=raw):
                got = to_column_unit(field, raw)
                self.assertIsNotNone(got, raw)
                self.assertAlmostEqual(got, want, places=6)

    REFUSE = [
        ("bulk_density", "1.72 and 2.30 g/cm3 (pre- and post-crushed, respectively)"),
        ("bulk_density", "minimum (1.15 g/cc) and maximum (1.88 g/cc)"),
        ("cohesion", "3.1 kPa (low stress level); 18.80 kPa (conventional stress level)"),
        ("friction_angle", "51.55° (low stress level); 48.17° (conventional stress level)"),
        ("cohesion", "12 psi"),                     # a unit the column does not convert: refuse, do not guess
        ("bulk_density", "1.5-1.6"),
    ]

    def test_ambiguous_or_unconvertible_values_are_refused(self):
        for field, raw in self.REFUSE:
            with self.subTest(field=field, raw=raw):
                self.assertIsNone(to_column_unit(field, raw))

    def test_the_three_columns_and_their_units(self):
        self.assertEqual(set(COLUMN_UNITS), {"bulk_density", "cohesion", "friction_angle"})

    def test_the_ordinal_indicator_counts_as_a_degree_sign(self):
        self.assertAlmostEqual(parse_number("46.12 º").value, 46.12)


if __name__ == "__main__":
    unittest.main()

"""The integrity check must fail when a number reaches the page as text.

A composition value stored as "22.4 (vol%)" passed every check for a day: the page drops a
row whose value is not a number, and the render check counted only the rows the page
shows, so it agreed with the page. This makes the bundle itself the thing checked.

Run:  python3 -m unittest scripts.tests.test_verify_numeric
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_data import check_numeric_values, NUMERIC_SCALAR_FIELDS  # noqa: E402


class NumericTests(unittest.TestCase):
    def test_the_numeric_fields_are_the_real_columns(self):
        for f in ("specific_gravity", "density_g_cm3", "particle_size_d50", "ph", "nasa_fom_score"):
            self.assertIn(f, NUMERIC_SCALAR_FIELDS)
        self.assertNotIn("bulk_density", NUMERIC_SCALAR_FIELDS)          # TEXT: ranges are legitimate there

    def test_clean_bundle_passes(self):
        errs = check_numeric_values(
            [{"simulant_id": "S1", "particle_size_d50": 38.22, "ph": None, "bulk_density": "1.5", "bulk_density_range": "1.5-1.6"}],
            [{"composition_id": "C1", "simulant_id": "S1", "value_pct": 31.0}],
            [{"composition_id": "CH1", "simulant_id": "S1", "value_wt_pct": 49.96}])
        self.assertEqual(errs, [])

    def test_text_in_a_composition_value_fails(self):
        errs = check_numeric_values([], [{"composition_id": "C1", "simulant_id": "S1", "value_pct": "22.4 (vol%)"}],
                                    [{"composition_id": "CH1", "simulant_id": "S1", "value_wt_pct": "<0.02"}])
        self.assertEqual(len(errs), 2)
        self.assertIn("22.4 (vol%)", errs[0])

    def test_text_in_a_numeric_property_fails(self):
        errs = check_numeric_values([{"simulant_id": "S1", "particle_size_d50": "38.22 μm"}], [], [])
        self.assertEqual(len(errs), 1)
        self.assertIn("particle_size_d50", errs[0])

    def test_a_boolean_is_not_a_number(self):
        self.assertEqual(len(check_numeric_values([{"simulant_id": "S1", "ph": True}], [], [])), 1)


if __name__ == "__main__":
    unittest.main()


class ColumnUnitVerifyTests(unittest.TestCase):
    def test_a_unit_inside_a_physical_value_fails(self):
        from verify_data import check_numeric_values
        errs = check_numeric_values([{"simulant_id": "S1", "bulk_density": "1.80 g/cm3", "cohesion": "185.2 Pa", "friction_angle": "46.12"}], [], [])
        self.assertEqual(len(errs), 2)

    def test_a_bare_number_as_text_passes(self):
        from verify_data import check_numeric_values
        self.assertEqual(check_numeric_values([{"simulant_id": "S1", "bulk_density": "1.8", "cohesion": 0.1852, "friction_angle": "46.12"}], [], []), [])


class RangeBelongsInItsOwnColumnTests(unittest.TestCase):
    """The page reads bulk_density with Number(); a range stored there is never shown.
    Ranges go in bulk_density_range, which the page prints as text."""

    def test_a_range_in_bulk_density_fails(self):
        from verify_data import check_numeric_values
        self.assertEqual(len(check_numeric_values([{"simulant_id": "S1", "bulk_density": "1.5-1.6"}], [], [])), 1)

    def test_a_range_in_bulk_density_range_is_fine(self):
        from verify_data import check_numeric_values
        self.assertEqual(check_numeric_values([{"simulant_id": "S1", "bulk_density_range": "1.40 – 1.94 g/cm3"}], [], []), [])

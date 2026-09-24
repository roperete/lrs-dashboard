"""The value audit: every value the page shows, tested mechanically.

Each value was read from its document by one agent and confirmed by another, but the errors
found on 2026-09-23/24 all entered afterwards — parsing, unit conversion, a superseded sheet.
So the audit tests what reaches the page: does the value's own quote state that number (in
that unit, allowing the conversions the pipeline makes)? Is it physically plausible? Do
composition totals add up? Does it agree with the simulant's other values? Does the cited
reference name the product? Anything it flags goes to an agent to re-read.

Run:  python3 -m unittest scripts.tests.test_audit_values
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_values import numbers_in, quote_supports, implausible, composition_total_problem, cross_field_problems  # noqa: E402


class NumbersTests(unittest.TestCase):
    def test_numbers_in_text(self):
        self.assertEqual(numbers_in("ρo = 1.295 kg/l (s = 0.0097 kg/l)"), [1.295, 0.0097])
        self.assertEqual(numbers_in("1.40 – 1.94 g/cm3"), [1.40, 1.94])
        self.assertEqual(numbers_in("SiO2 TiO2 | 46.08 0.81"), [46.08, 0.81])   # formula digits are not values
        self.assertEqual(numbers_in("4495.7 x10-9 m3/kg")[0], 4495.7)          # exponents are not the value


class QuoteTests(unittest.TestCase):
    def test_the_number_is_in_its_quote(self):
        self.assertTrue(quote_supports("cohesion", "2.896", "Cohesion (c): 2.896 kPa")[0])

    def test_a_unit_conversion_the_pipeline_makes_is_allowed(self):
        self.assertTrue(quote_supports("cohesion", "0.1852", "185.2 Pa (AP-cohesive strength)")[0])
        self.assertTrue(quote_supports("bulk_density", "1.295", "ρo = 1.295 kg/l")[0])
        self.assertTrue(quote_supports("bulk_density", "1.64", "density of 1640 kg/m3")[0])

    def test_rounding_in_the_last_place_is_tolerated(self):
        self.assertTrue(quote_supports("particle_size_d50", 137.6, "Median(D50): 137.56 µm")[0])

    def test_a_number_not_in_the_quote_fails(self):
        ok, why = quote_supports("cohesion", "15.79", "cohesion 16.93 kPa at 106-197 kPa")
        self.assertFalse(ok)
        self.assertIn("15.79", why)

    def test_every_number_of_a_text_value_must_be_in_the_quote(self):
        self.assertTrue(quote_supports("bulk_density_range", "1.40 – 1.94 g/cm3", "Minimum Density: 1.40 / Maximum Density: 1.94")[0])
        self.assertFalse(quote_supports("bulk_density_range", "1.45 – 2.14 g/cm3", "Minimum Density: 1.45")[0])

    def test_a_year_must_appear(self):
        self.assertTrue(quote_supports("release_date", "2019", '"datePublished":"2019-02-06"')[0])
        self.assertFalse(quote_supports("release_date", "2010", "founded in 2015")[0])

    def test_no_quote_is_its_own_finding(self):
        ok, why = quote_supports("cohesion", "1.0", "")
        self.assertFalse(ok)
        self.assertIn("no quote", why)


class PlausibilityTests(unittest.TestCase):
    def test_in_range_values_pass(self):
        for f, v in (("bulk_density", 1.5), ("density_g_cm3", 2.9), ("cohesion", 1.0), ("friction_angle", 45),
                     ("particle_size_d50", 70), ("ph", 8.1), ("nasa_fom_score", 88.7)):
            self.assertIsNone(implausible(f, v), f)

    def test_out_of_range_values_are_named(self):
        self.assertIn("185.2", implausible("cohesion", 185.2))               # the pascal/kilopascal slip
        self.assertIsNotNone(implausible("bulk_density", 2.9))                # a particle density in the bulk column
        self.assertIsNotNone(implausible("particle_size_d50", 0.07))          # millimetres in a micrometre column
        self.assertIsNotNone(implausible("friction_angle", 5))
        self.assertIsNotNone(implausible("nasa_fom_score", 180))


class CompositionTotalTests(unittest.TestCase):
    def test_an_oxide_total_near_100_passes(self):
        self.assertIsNone(composition_total_problem("oxide", [46.08, 0.81, 24.87, 6.73, 5.05, 14.02, 1.51, 0.66]))

    def test_an_oxide_total_far_from_100_is_flagged(self):
        self.assertIn("85", composition_total_problem("oxide", [46.0, 25.0, 14.0]))
        self.assertIsNotNone(composition_total_problem("oxide", [60.0, 30.0, 20.0]))

    def test_a_mineral_total_over_100_is_flagged(self):
        self.assertIsNotNone(composition_total_problem("mineral", [90.0, 10.0, 30.0]))

    def test_a_partial_mineral_list_is_not_an_error(self):
        self.assertIsNone(composition_total_problem("mineral", [55.1, 20.0]))


class CrossFieldTests(unittest.TestCase):
    def test_a_high_ti_label_needs_titanium(self):
        self.assertTrue(cross_field_problems({"lunar_sample_reference": "High-Ti Mare"}, {"TiO2": 1.2}, {}))

    def test_a_low_ti_label_with_high_titanium_is_flagged(self):
        self.assertTrue(cross_field_problems({"lunar_sample_reference": "Low-Ti Mare"}, {"TiO2": 6.5}, {}))

    def test_a_highland_label_needs_alumina(self):
        self.assertTrue(cross_field_problems({"lunar_sample_reference": "Highlands"}, {"Al2O3": 12.0}, {}))
        self.assertFalse(cross_field_problems({"lunar_sample_reference": "Highlands"}, {"Al2O3": 24.9}, {}))

    def test_bulk_density_cannot_exceed_particle_density(self):
        self.assertTrue(cross_field_problems({"bulk_density": "3.0", "density_g_cm3": 2.9}, {}, {}))
        self.assertFalse(cross_field_problems({"bulk_density": "1.6", "density_g_cm3": 2.9}, {}, {}))

    def test_glass_content_should_match_the_glass_mineral_row(self):
        self.assertTrue(cross_field_problems({"glass_content_percent": 40.0}, {}, {"Amorphous/Glass": 19.2}))
        self.assertFalse(cross_field_problems({"glass_content_percent": 19.2}, {}, {"Amorphous/Glass": 19.2}))


if __name__ == "__main__":
    unittest.main()


class FalsePositiveTests(unittest.TestCase):
    """Correct values the first run of the audit flagged, 2026-09-24."""

    def test_millimetres_and_centimetres_convert_to_micrometres(self):
        self.assertTrue(quote_supports("particle_size_d50", "77.0", "D50 ... were found to be 0.077 mm, 16.58")[0])
        self.assertTrue(quote_supports("particle_size_distribution", "<1000 µm", "would not contain particles greater than 1 mm")[0])
        self.assertTrue(quote_supports("particle_size_distribution", "up to 100000 µm", "contains particles to 10 cm")[0])

    def test_a_decimal_split_by_pdf_extraction_is_read_whole(self):
        self.assertTrue(quote_supports("ph", "5.6", "was found to have a pH of 5. 6, a conductivity of 0. 09 dS/ m.")[0])

    def test_descriptive_text_fields_are_not_numbers(self):
        self.assertTrue(quote_supports("particle_ruggedness", "sharp", "angular, sharp")[0])


if __name__ == "__main__":
    unittest.main()


class SecondPassTests(unittest.TestCase):
    def test_a_value_stated_in_words_is_its_own_finding(self):
        from audit_values import stated_in_words
        self.assertTrue(stated_in_words("Approximately half of the volume of a typical particle is glass"))
        self.assertTrue(stated_in_words("The measured cohesion ... is considered to be zero here"))
        self.assertTrue(stated_in_words("EAC-1A is fully crystallized and contains plagioclase"))
        self.assertFalse(stated_in_words("Cohesion (c): 2.896 kPa"))

    def test_a_back_reference_is_read_against_the_table_it_points_to(self):
        from audit_values import is_back_reference
        self.assertTrue(is_back_reference("(same row as above)"))
        self.assertTrue(is_back_reference("same table row as SiO2"))
        self.assertFalse(is_back_reference("OB-1 Canada NORCAT Anorthosite 46.60 0.12 21.55"))

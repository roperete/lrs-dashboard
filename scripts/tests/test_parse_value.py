"""Turning a value as a document states it into the number the database stores.

Readers quote values as the document prints them — "49.96 ± 0.60 wt.-%", "22.4 (vol%)",
"~5". Written verbatim into a REAL column, SQLite keeps such a string as text, and the page
then drops the row without a word: 123 composition values and six physical values went
missing that way while their compositions showed as verified.

The parser is deliberately strict. A value is stored only when the text states exactly one
number for it; an uncertainty after ± and qualifiers in parentheses are allowed and kept
verbatim alongside. Anything else — a range, two measurements, a detection limit, "present",
"trace" — is not a single number, and goes to a human rather than being guessed at.

Run:  python3 -m unittest scripts.tests.test_parse_value
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from parse_value import parse_number  # noqa: E402


class SingleNumberTests(unittest.TestCase):
    """Taken verbatim from what readers returned on 2026-09-22 and 2026-09-23."""

    CASES = {
        "47.71": (47.71, False),
        "49.96 ± 0.60 wt.-%": (49.96, False),
        "0.01 ± 0.00 wt.-%": (0.01, False),
        "22.4 (vol%)": (22.4, False),
        "38.8 (vol%; An 80)": (38.8, False),
        "0.18 (vol%, nonlunar phase, SEM modal)": (0.18, False),
        "51.87 wt%": (51.87, False),
        "70%": (70.0, False),
        "30 wt%": (30.0, False),
        "4.15 (total Fe expressed as Fe2O3)": (4.15, False),
        "15.02 (reported as 'Fe2O3; FeO', i.e. total iron)": (15.02, False),
        "32.4 (anorthite)": (32.4, False),
        "38.22 μm": (38.22, False),
        "85.7 µm": (85.7, False),
        "260.0 μm": (260.0, False),
        "~5": (5.0, True),
        "~7": (7.0, True),
        "ca. 92 (of crystalline fraction, Rietveld XRD; amorphous phase present but not quantified)": (92.0, True),
        "ca. 8 (of crystalline fraction, Rietveld XRD)": (8.0, True),
        "12": (12.0, False),
        "  3.5  ": (3.5, False),
        "1,5": None,          # a decimal comma is ambiguous with a thousands separator
        # CUG-1A's paper prints the unit with a space inside it (wave 2, 2026-09-24)
        "9% wt": (9.0, False),
        "23% wt%": (23.0, False),
        "20 wt %": (20.0, False),
        "12 vol %": (12.0, False),
    }

    def test_every_case(self):
        for text, want in self.CASES.items():
            with self.subTest(text=text):
                got = parse_number(text)
                if want is None:
                    self.assertIsNone(got)
                else:
                    self.assertIsNotNone(got, text)
                    self.assertAlmostEqual(got.value, want[0])
                    self.assertEqual(got.approximate, want[1])

    def test_numbers_pass_straight_through(self):
        self.assertEqual(parse_number(47.71).value, 47.71)
        self.assertEqual(parse_number(0).value, 0.0)


class NotASingleNumberTests(unittest.TestCase):
    REJECT = [
        "present (checkmark, no wt% reported)",
        "present (main mineral; wt% not quantified)",
        "Minor/trace",
        "Quartz (unquantified)",
        "K-feldspar + Chromite + Calcite + Quartz (unquantified)",
        "<0.02",
        "<1 wt.-%",
        "41–61 µm (median; mean 53–81 µm)",       # a range
        "1.43-1.86",
        "98 (UTD) / 117 (NASA) µm",              # two measurements
        "88 chemistry FoM (Table 8); Table 24 summary: chemistry 88, mineralogy n/a",
        "",
        "n/a",
    ]

    def test_every_case_is_refused(self):
        for text in self.REJECT:
            with self.subTest(text=text):
                self.assertIsNone(parse_number(text))

    def test_none_is_refused(self):
        self.assertIsNone(parse_number(None))


if __name__ == "__main__":
    unittest.main()

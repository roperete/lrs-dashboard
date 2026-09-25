"""Task 2 of the per-value provenance plan: repair truncated identifiers.

Run:  python3 -m unittest scripts.tests.test_repair_references
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from repair_references import doi_from_text  # noqa: E402


class DoiFromTextTest(unittest.TestCase):
    def test_full_asce_doi_with_parentheses_is_recovered(self):
        text = ("A. Bonanno, L. Bernold, Exploratory review of sintered lunar soil, J. Aero. Eng. 28 (2015) "
                "04014114, https://doi.org/10.1061/(ASCE)AS.1943-5525.0000428")
        self.assertEqual(doi_from_text(text), "10.1061/(ASCE)AS.1943-5525.0000428")

    def test_bare_doi_without_url_prefix(self):
        self.assertEqual(doi_from_text("Zheng et al. CAS-1 lunar soil simulant. doi:10.1016/j.asr.2008.07.006"),
                         "10.1016/j.asr.2008.07.006")

    def test_trailing_punctuation_is_dropped(self):
        self.assertEqual(doi_from_text("see https://doi.org/10.1038/s41598-020-62312-4."), "10.1038/s41598-020-62312-4")
        self.assertEqual(doi_from_text("(doi 10.1007/s11837-019-03329-x)"), "10.1007/s11837-019-03329-x")

    def test_spaces_inside_a_wrapped_doi_are_closed(self):
        # citation text copied from a PDF where the DOI wrapped onto a new line
        self.assertEqual(doi_from_text("https://doi.org/10.1016/j. asr.2008.07.006"), "10.1016/j.asr.2008.07.006")

    def test_no_doi_returns_none(self):
        self.assertIsNone(doi_from_text("Hispansion.io"))
        self.assertIsNone(doi_from_text(""))
        self.assertIsNone(doi_from_text(None))


if __name__ == "__main__":
    unittest.main()

"""Which documents the index offers a reader for a given simulant.

A short product name matched once in a long document is usually a false positive: "ALS"
and "OB-1" occur as ordinary abbreviations. The index therefore required two mentions
before it would credit a name of four characters or fewer — and silently dropped 75
document-simulant pairs, among them the only sentence in the library that names TJ-2
("In addition, a variant TJ-2 exists in which silicon..."), which left six products
reported as named in no document at all.

Judging whether a mention really refers to the product is the reader's job, not a
threshold's. Single mentions of short names are therefore kept, separately, as weak
matches: offered to a reader after the confident ones and never counted as evidence on
their own.

Run:  python3 -m unittest scripts.tests.test_library_index
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from build_library_index import name_pattern, scan_text, is_summary  # noqa: E402


class PatternTests(unittest.TestCase):
    def test_separator_may_vary(self):
        pat = name_pattern("JSC-1A")
        for s in ("JSC-1A", "JSC 1A", "JSC1A"):
            self.assertTrue(pat.search(f"the {s} simulant"), s)

    def test_a_longer_name_does_not_match_a_prefix_of_another(self):
        self.assertIsNone(name_pattern("JSC-1").search("JSC-1A was produced"))
        self.assertIsNone(name_pattern("LHS-1").search("LHS-1D and LHS-1E"))

    def test_short_names_are_matched_case_sensitively(self):
        self.assertIsNone(name_pattern("ALS").search("als lunar soil"))
        self.assertTrue(name_pattern("TUBS-M").search("tubs-m appears lowercased here"))


class ScanTests(unittest.TestCase):
    def scan(self, text, names=("ALS", "TJ-2", "TUBS-M", "JSC-1A")):
        return scan_text(text, {n: name_pattern(n) for n in names})

    def test_repeated_mentions_are_confident(self):
        strong, weak = self.scan("TJ-2 was made. Later TJ-2 was tested.")
        self.assertEqual(strong, {"TJ-2": 2})
        self.assertEqual(weak, {})

    def test_a_single_mention_of_a_short_name_is_weak_not_discarded(self):
        strong, weak = self.scan("In addition, a variant TJ-2 exists in which silicon is replaced.")
        self.assertEqual(strong, {})
        self.assertEqual(weak, {"TJ-2": 1})

    def test_a_single_mention_of_a_longer_name_is_confident(self):
        strong, weak = self.scan("The JSC-1A simulant was used once.")
        self.assertEqual(strong, {"JSC-1A": 1})
        self.assertEqual(weak, {})

    def test_absent_names_appear_in_neither(self):
        strong, weak = self.scan("This document is about basalt in general.")
        self.assertEqual((strong, weak), ({}, {}))

    def test_a_short_name_twice_beats_the_threshold_even_in_a_long_document(self):
        strong, weak = self.scan("ALS is a simulant. " + ("filler. " * 500) + "ALS again.")
        self.assertEqual(strong, {"ALS": 2})


class SummaryTests(unittest.TestCase):
    """NotebookLM writes its narrative summaries as saved web pages under .../Sources/.
    A PDF sitting in the same folder is a real document and stays in the index."""

    def test_saved_pages_under_sources_are_excluded(self):
        self.assertTrue(is_summary(Path("/x/papers/LRS/Sources/Some summary.html")))
        self.assertTrue(is_summary(Path("/x/papers/LRS/Sources/notes.json")))

    def test_a_pdf_under_sources_is_still_a_document(self):
        self.assertFalse(is_summary(Path("/x/papers/LRS/Sources/Some summary.pdf")))

    def test_documents_elsewhere_are_never_excluded(self):
        self.assertFalse(is_summary(Path("/x/papers/LRS/Some paper.pdf")))
        self.assertFalse(is_summary(Path("/x/papers/LRS/a page.html")))


if __name__ == "__main__":
    unittest.main()

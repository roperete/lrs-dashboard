"""Assemble apply-ready findings from a workflow journal, even when the run died part way.

The journal holds one {"type": "result", "key": ..., "result": ...} line per finished
agent. An extraction result has group_key + results; a verification result has
group_key + checks. Pair them by group_key; an extraction without a verification is kept
(the apply step then flags every claim for review) and a verification without its
extraction is dropped.

Run:  python3 -m unittest scripts.tests.test_collect_findings
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from collect_findings import pair_results  # noqa: E402

EXT_A = {"group_key": "A", "results": [{"simulant_id": "S001"}]}
VER_A = {"group_key": "A", "checks": [{"simulant_id": "S001"}]}
EXT_B = {"group_key": "B", "results": [{"simulant_id": "S002"}]}
VER_C = {"group_key": "C", "checks": [{"simulant_id": "S003"}]}


class PairResultsTest(unittest.TestCase):
    def test_pairs_extraction_and_verification_by_group_key(self):
        groups = pair_results([{"type": "result", "result": EXT_A}, {"type": "result", "result": VER_A}])
        self.assertEqual(groups, [{"group_key": "A", "extraction": EXT_A, "verification": VER_A}])

    def test_extraction_without_verification_is_kept_unverified(self):
        groups = pair_results([{"type": "result", "result": EXT_B}])
        self.assertEqual(groups, [{"group_key": "B", "extraction": EXT_B, "verification": None}])

    def test_verification_without_extraction_is_dropped(self):
        self.assertEqual(pair_results([{"type": "result", "result": VER_C}]), [])

    def test_non_result_lines_and_null_results_are_ignored(self):
        groups = pair_results([{"type": "started"}, {"type": "result", "result": None}, {"type": "result", "result": EXT_A}])
        self.assertEqual(len(groups), 1)

    def test_later_duplicate_for_the_same_group_wins(self):
        newer = {"group_key": "A", "results": [{"simulant_id": "S001"}, {"simulant_id": "S009"}]}
        groups = pair_results([{"type": "result", "result": EXT_A}, {"type": "result", "result": newer}, {"type": "result", "result": VER_A}])
        self.assertEqual(groups[0]["extraction"], newer)


if __name__ == "__main__":
    unittest.main()

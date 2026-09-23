"""Stop long agent runs before they eat the week's budget.

A provenance run spends millions of agent tokens unattended. Alvaro asked for it to stop
at 80% of the weekly allowance, so the rest of the week is not spent on this. The reading
comes from the CLI's own cached utilisation in ~/.claude.json, which is the same figure
/usage shows.

Rules under test:
  * the seven-day percentage is read, not the five-hour one;
  * at or above the threshold the answer is stop, below it carry on;
  * a reading older than the staleness limit is not trusted to say "carry on";
  * missing or malformed data never reads as "plenty left".

Run:  python3 -m unittest scripts.tests.test_usage_guard
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from usage_guard import read_utilization, should_stop, STALE_AFTER_S  # noqa: E402

NOW_MS = 1790165691459


def config(seven_day=48, five_hour=10, fetched_ms=NOW_MS, resets="2026-09-27T20:00:00+00:00"):
    return {
        "cachedUsageUtilization": {
            "fetchedAtMs": fetched_ms,
            "utilization": {
                "five_hour": {"utilization": five_hour, "resets_at": "2026-09-23T20:00:00+00:00"},
                "seven_day": {"utilization": seven_day, "resets_at": resets},
            },
        }
    }


class ReadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "claude.json"

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, data):
        self.path.write_text(json.dumps(data))
        return self.path

    def test_reads_the_seven_day_figure_not_the_five_hour_one(self):
        u = read_utilization(self.write(config(seven_day=48, five_hour=100)), now_ms=NOW_MS)
        self.assertEqual(u["seven_day"], 48)
        self.assertEqual(u["five_hour"], 100)
        self.assertEqual(u["resets_at"], "2026-09-27T20:00:00+00:00")
        self.assertFalse(u["stale"])

    def test_an_old_reading_is_flagged_stale(self):
        old = NOW_MS - (STALE_AFTER_S + 60) * 1000
        self.assertTrue(read_utilization(self.write(config(fetched_ms=old)), now_ms=NOW_MS)["stale"])

    def test_missing_file_is_unknown_not_zero(self):
        u = read_utilization(Path(self.tmp.name) / "absent.json", now_ms=NOW_MS)
        self.assertIsNone(u["seven_day"])
        self.assertTrue(u["stale"])

    def test_malformed_file_is_unknown_not_zero(self):
        self.path.write_text("{not json")
        self.assertIsNone(read_utilization(self.path, now_ms=NOW_MS)["seven_day"])

    def test_absent_utilization_block_is_unknown(self):
        self.assertIsNone(read_utilization(self.write({"other": 1}), now_ms=NOW_MS)["seven_day"])


class ThresholdTests(unittest.TestCase):
    def test_below_the_threshold_carries_on(self):
        stop, why = should_stop({"seven_day": 79, "stale": False}, threshold=80)
        self.assertFalse(stop)
        self.assertIn("79", why)

    def test_at_the_threshold_stops(self):
        stop, why = should_stop({"seven_day": 80, "stale": False}, threshold=80)
        self.assertTrue(stop)
        self.assertIn("80", why)

    def test_above_the_threshold_stops(self):
        self.assertTrue(should_stop({"seven_day": 93, "stale": False}, threshold=80)[0])

    def test_an_unknown_reading_stops_rather_than_guessing(self):
        stop, why = should_stop({"seven_day": None, "stale": True}, threshold=80)
        self.assertTrue(stop)
        self.assertIn("unknown", why.lower())

    def test_a_stale_reading_below_the_threshold_still_stops(self):
        """A figure hours old cannot show a run that has been spending since."""
        stop, why = should_stop({"seven_day": 50, "stale": True}, threshold=80)
        self.assertTrue(stop)
        self.assertIn("stale", why.lower())


if __name__ == "__main__":
    unittest.main()


class MonitorTests(unittest.TestCase):
    """Watching a run in flight is a different question from deciding to start one.

    should_stop() is the pre-flight gate: anything it cannot confirm, it refuses. While a
    run is already going, refusing on an unreadable figure would kill a healthy run over a
    cache nobody is refreshing, so a stale reading is reported as "cannot tell" and the
    decision goes to a human instead.
    """

    def test_fresh_reading_at_the_threshold_stops(self):
        from usage_guard import monitor_verdict
        v, why = monitor_verdict({"seven_day": 81, "stale": False}, threshold=80)
        self.assertEqual(v, "stop")
        self.assertIn("81", why)

    def test_fresh_reading_below_the_threshold_carries_on(self):
        from usage_guard import monitor_verdict
        self.assertEqual(monitor_verdict({"seven_day": 62, "stale": False}, threshold=80)[0], "carry_on")

    def test_stale_reading_cannot_tell(self):
        from usage_guard import monitor_verdict
        v, why = monitor_verdict({"seven_day": 48, "stale": True, "age_s": 63000}, threshold=80)
        self.assertEqual(v, "cannot_tell")
        self.assertIn("stale", why.lower())

    def test_unknown_reading_cannot_tell(self):
        from usage_guard import monitor_verdict
        self.assertEqual(monitor_verdict({"seven_day": None, "stale": True}, threshold=80)[0], "cannot_tell")

    def test_a_stale_reading_that_already_exceeds_the_threshold_still_stops(self):
        """Usage only rises within a week, so an old figure over the line is already over it."""
        from usage_guard import monitor_verdict
        v, why = monitor_verdict({"seven_day": 84, "stale": True, "age_s": 63000}, threshold=80)
        self.assertEqual(v, "stop")

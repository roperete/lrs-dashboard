#!/usr/bin/env python3
"""Is there enough of the week's allowance left to keep an agent run going?

A provenance run spends millions of agent tokens while nobody is watching. Alvaro asked
for it to stop at 80% of the weekly allowance so the rest of the week is not spent on this
one task. The reading is the CLI's own cached utilisation in ~/.claude.json — the same
figure /usage shows — and the answer is deliberately conservative: an unknown or stale
reading says stop, because a figure taken hours ago cannot show what a run has spent since.

    python3 scripts/usage_guard.py              # human summary, exit 0 carry on / 1 stop
    python3 scripts/usage_guard.py --threshold 90
    python3 scripts/usage_guard.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

CONFIG = Path.home() / ".claude.json"
DEFAULT_THRESHOLD = 80
STALE_AFTER_S = 45 * 60      # the CLI refreshes as it works; older than this is not current


def read_utilization(path: Path = CONFIG, now_ms: int | None = None) -> dict:
    """The cached seven-day and five-hour percentages, with how old the reading is."""
    now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    out = {"seven_day": None, "five_hour": None, "resets_at": None, "age_s": None, "stale": True}
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return out
    cached = data.get("cachedUsageUtilization") or {}
    u = cached.get("utilization") or {}
    if not u:
        return out
    seven, five = u.get("seven_day") or {}, u.get("five_hour") or {}
    out["seven_day"] = seven.get("utilization")
    out["five_hour"] = five.get("utilization")
    out["resets_at"] = seven.get("resets_at")
    fetched = cached.get("fetchedAtMs")
    if isinstance(fetched, (int, float)):
        out["age_s"] = max(0, (now_ms - fetched) / 1000)
        out["stale"] = out["age_s"] > STALE_AFTER_S
    return out


def should_stop(u: dict, threshold: int = DEFAULT_THRESHOLD) -> tuple[bool, str]:
    """(stop, why). Anything other than a fresh reading below the threshold stops the run."""
    pct = u.get("seven_day")
    if pct is None:
        return True, "weekly usage unknown (no reading available) — stopping rather than guessing"
    if u.get("stale"):
        age = u.get("age_s")
        age_txt = f", {age / 60:.0f} min old" if age else ""
        return True, f"weekly usage reading is stale{age_txt}; last said {pct}% — stopping rather than trusting it"
    if pct >= threshold:
        return True, f"weekly usage {pct}% has reached the {threshold}% stop"
    return False, f"weekly usage {pct}%, below the {threshold}% stop"


def monitor_verdict(u: dict, threshold: int = DEFAULT_THRESHOLD) -> tuple[str, str]:
    """"stop" | "carry_on" | "cannot_tell", for a run that is already going.

    Refusing on an unreadable figure is right before starting work and wrong while it is
    under way: nothing in this session refreshes the cached utilisation, so treating stale
    as stop would kill a healthy run every time. A stale figure already over the line does
    stop it, since usage only rises inside a week.
    """
    pct = u.get("seven_day")
    if pct is None:
        return "cannot_tell", "no weekly usage reading available; ask for /usage"
    if pct >= threshold:
        return "stop", f"weekly usage {pct}% is at or over the {threshold}% stop"
    if u.get("stale"):
        age = u.get("age_s")
        age_txt = f" ({age / 3600:.1f} h old)" if age else ""
        return "cannot_tell", f"last reading {pct}%{age_txt} is stale; ask for /usage"
    return "carry_on", f"weekly usage {pct}%, below the {threshold}% stop"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--monitor", action="store_true",
                    help="verdict for a run already going: stop / carry_on / cannot_tell")
    args = ap.parse_args()
    u = read_utilization()
    if args.monitor:
        verdict, why = monitor_verdict(u, args.threshold)
        print(f"{verdict.upper()}: {why}")
        sys.exit({"stop": 1, "cannot_tell": 2, "carry_on": 0}[verdict])
    stop, why = should_stop(u, args.threshold)
    if args.json:
        print(json.dumps({**u, "stop": stop, "why": why, "threshold": args.threshold}, indent=1))
    else:
        age = f"{u['age_s'] / 60:.0f} min ago" if u.get("age_s") is not None else "never"
        print(f"seven-day {u['seven_day']}%  five-hour {u['five_hour']}%  read {age}  resets {u['resets_at']}")
        print(("STOP: " if stop else "CARRY ON: ") + why)
    sys.exit(1 if stop else 0)


if __name__ == "__main__":
    main()

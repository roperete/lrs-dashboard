#!/usr/bin/env python3
"""The number a document states, from the text a reader quoted.

Readers return values as printed — "49.96 ± 0.60 wt.-%", "22.4 (vol%)", "~5". Stored
verbatim in a REAL column, SQLite keeps such a string as text and the page drops the row
without a word. parse_number() is strict: it returns a value only when the text states
exactly one number, optionally approximate ("~", "ca."), optionally followed by an
uncertainty after "±", a unit, and qualifiers in parentheses. A range, two measurements,
a detection limit ("<0.02") or a word ("present", "trace") is not a single number and
returns None, so it goes to a human instead of being guessed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_NUM = r"[-+]?\d+(?:\.\d+)?"
_APPROX = re.compile(r"^(?:~|≈|ca\.?|approx\.?|approximately|about)\s*", re.I)
# What may follow the number: an uncertainty, and a unit made of letters, %, µ/μ, dots,
# hyphens, degrees and slashes between letters (g/cm3) — but no further digits except
# the exponent in a unit such as cm3 or m2.
_UNIT = r"(?:[A-Za-zµμ°%][A-Za-z0-9µμ°%.\-/]*)?"
_FULL = re.compile(rf"^({_NUM})(?:\s*±\s*{_NUM})?\s*{_UNIT}\s*$")


@dataclass(frozen=True)
class Parsed:
    value: float
    approximate: bool
    text: str            # the statement as the reader quoted it


def _strip_parens(s: str) -> str:
    """Drop parenthesised qualifiers, nested or not: '38.8 (vol%; An 80)' -> '38.8 '."""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\([^()]*\)", " ", s)
    return s


def parse_number(raw) -> Parsed | None:
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return Parsed(float(raw), False, str(raw))
    text = str(raw).strip()
    if not text:
        return None
    body = _strip_parens(text).strip()
    approximate = bool(_APPROX.match(body))
    body = _APPROX.sub("", body).strip()
    # A unit printed with a space inside it — "9% wt", "20 wt %", "12 vol %" — is one unit.
    body = re.sub(r"\s*%\s*", "%", body)
    if "," in body:                      # decimal comma or a list: ambiguous either way
        return None
    m = _FULL.match(body)
    if not m:
        return None
    unit_tail = body[m.end(1):]
    # A second number outside the uncertainty is a range or a second measurement.
    tail_without_uncertainty = re.sub(rf"^\s*±\s*{_NUM}", "", unit_tail)
    if re.search(r"(?<![A-Za-z])\d", tail_without_uncertainty):
        return None
    return Parsed(float(m.group(1)), approximate, text)

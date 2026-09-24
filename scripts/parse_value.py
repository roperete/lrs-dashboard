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
# "º" (U+00BA, the ordinal indicator) and "˚" stand in for the degree sign on some sheets.
_UNIT = r"(?:[A-Za-zµμ°º˚%][A-Za-z0-9µμ°º˚%.\-/³]*)?"
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


# The unit each text-typed physical column is shown in on the page, and how a stated unit
# converts into it. These columns are text because some hold ranges, but the page reads them
# as numbers and prints this unit after them — so what is stored must be a bare number in it.
COLUMN_UNITS = {
    "bulk_density": {"": 1.0, "g/cm3": 1.0, "g/cc": 1.0, "g/ml": 1.0, "kg/l": 1.0, "t/m3": 1.0,
                     "kg/m3": 0.001},
    "cohesion": {"": 1.0, "kpa": 1.0, "pa": 0.001, "mpa": 1000.0},
    "friction_angle": {"": 1.0, "°": 1.0, "º": 1.0, "˚": 1.0, "deg": 1.0, "degree": 1.0, "degrees": 1.0},
    # Particle sizes are shown in µm; a size printed in mm or cm is converted.
    "particle_size_d50": {"": 1.0, "µm": 1.0, "μm": 1.0, "um": 1.0, "micron": 1.0, "microns": 1.0, "mm": 1000.0, "cm": 10000.0, "nm": 0.001},
    "particle_size_mean_um": {"": 1.0, "µm": 1.0, "μm": 1.0, "um": 1.0, "micron": 1.0, "microns": 1.0, "mm": 1000.0, "cm": 10000.0, "nm": 0.001},
}
_UNIT_TOKEN = r"([A-Za-zµμ°º˚%][A-Za-z0-9µμ°º˚%/³.]*)"
_LEAD = re.compile(rf"^\s*(?:~|≈|ca\.?|approx\.?)?\s*{_NUM}(?:\s*±\s*{_NUM})?\s*")


def _unit_key(token: str) -> str:
    return token.lower().rstrip(".").replace("³", "3")


def to_column_unit(field: str, raw) -> float | None:
    """The stated value converted into the unit its column is shown in, or None.

    None when the text is not a single number, or states a unit the column does not convert
    ("12 psi"). A unit is read directly after the number ("185.2 Pa") or as the first word in
    parentheses ("3.78 (kPa)"); a parenthesised word that is not a unit ("(Table 4)") leaves
    the number bare, taken to be in the column's unit already."""
    table = COLUMN_UNITS[field]
    p = parse_number(raw)
    if p is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip()
    m = _LEAD.match(text)
    tail = text[m.end():] if m else ""
    direct = re.match(_UNIT_TOKEN, tail)
    if direct:
        factor = table.get(_unit_key(direct.group(1)))
        if factor is None:
            return None
    else:
        inner = re.match(r"\(\s*" + _UNIT_TOKEN, tail)
        factor = table.get(_unit_key(inner.group(1)), 1.0) if inner else 1.0
    return round(p.value * factor, 10)

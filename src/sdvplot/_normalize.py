"""How raw team values and seasons are compared: one normal form, so 14, "14", 14.0, "14.0" and " 14 " are equal."""

from __future__ import annotations

import math
import numbers
import re
import unicodedata
from typing import Any

from sdvplot import _index
from sdvplot._errors import InputError

_FLOAT_ID = re.compile(r"-?\d+\.0+")
# typographic punctuation providers write inconsistently (sdvplotR fold_accents): curly apostrophes, en/em dashes
_PUNCT = str.maketrans({"\u2018": "'", "\u2019": "'", "\u2013": "-", "\u2014": "-"})


def _is_na(value: Any) -> bool:
    return value is None or type(value).__name__ in ("NAType", "NaTType")


def norm_value(value: Any) -> str | None:
    """A team value as a comparison key: trimmed, accents and typographic punctuation folded, case-folded,
    integral numbers without a decimal point."""
    if _is_na(value):
        return None
    if isinstance(value, bool):
        return str(value).casefold()
    if isinstance(value, numbers.Integral):
        return str(int(value))
    if isinstance(value, numbers.Real):
        f = float(value)
        if math.isnan(f):
            return None
        return str(int(f)) if f.is_integer() else str(f)
    s = str(value).strip()
    if not s.isascii():  # "San José State" == "San Jose State": decompose, then drop the combining accents
        s = "".join(c for c in unicodedata.normalize("NFKD", s.translate(_PUNCT)) if not unicodedata.combining(c))
    s = s.casefold()
    if _FLOAT_ID.fullmatch(s):  # "13.0": an id that went through a float before it became text
        s = s.split(".")[0]
    return s or None


_SPLIT_SEASON = re.compile(r"\s*(\d{4})\s*[-/]\s*(\d{2}|\d{4})\s*")


def check_season(year: int, league: str | None = None) -> None:
    """InputError unless ``year`` is a season sdvplot knows for ``league`` (any league when None): the bounds come from
    the bundled index (``_index.season_bounds``)."""
    bounds = _index.season_bounds(league)
    if bounds is not None and not bounds[0] <= year <= bounds[1]:
        scope = "" if league is None else f" for {league}"
        raise InputError(
            f"season {year} is outside the seasons sdvplot knows{scope} ({bounds[0]} to {bounds[1]}); pass a year such "
            "as 2020"
        )


def norm_season(value: Any, league: str | None = None) -> int | None:
    """A season as an int year. Accepts 2020, 2020.0, "2020"; None/NaN mean no season; anything else is an error, and
    so is a year outside the seasons the bundled index holds for ``league`` (any league when None)."""
    if _is_na(value):
        return None
    year = None
    if isinstance(value, numbers.Real) and not isinstance(value, bool):
        f = float(value)
        if math.isnan(f):
            return None
        if f.is_integer():
            year = int(f)
    elif isinstance(value, str) and value.strip().isdigit():
        year = int(value.strip())
    if year is None:
        hint = ""
        if isinstance(value, str) and (m := _SPLIT_SEASON.fullmatch(value)):
            end = int(m.group(1)) + 1
            hint = f"; for a split season pass its ending year ({end} for {value.strip()!r})"
        raise InputError(f"season must be a year such as 2020, got {value!r}{hint}")
    check_season(year, league)
    return year

"""How raw team values and seasons are compared: one normal form, so 14, "14", 14.0 and " 14 " are equal."""

from __future__ import annotations

import math
import numbers
from typing import Any


def _is_na(value: Any) -> bool:
    return value is None or type(value).__name__ in ("NAType", "NaTType")


def norm_value(value: Any) -> str | None:
    """A team value as a comparison key: trimmed, case-folded, integral numbers without a decimal point."""
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
    s = str(value).strip().casefold()
    return s or None


def norm_season(value: Any) -> int | None:
    """A season as an int year. Accepts 2020, 2020.0, "2020"; None/NaN mean no season; anything else is an error."""
    if _is_na(value):
        return None
    if isinstance(value, numbers.Real) and not isinstance(value, bool):
        f = float(value)
        if math.isnan(f):
            return None
        if f.is_integer():
            return int(f)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    raise ValueError(f"season must be a year such as 2020, got {value!r}")

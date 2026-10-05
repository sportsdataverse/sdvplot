"""Shot locations from the stats.nba.com legacy frame to sportypy's court: the port of sdvplotR's sdv_court_coords()."""

from __future__ import annotations

import math
from typing import Any

import narwhals as nw

from sdvplot._placement import _missing

BASKET_X = -47 + 5.25  # sportypy's NBA/WNBA/NCAA courts: center-court origin, baseline at -47, basket 5.25 ft in


def _tenths(frame: Any, name: str) -> Any:
    """Column ``name`` (tenths of a foot) as a Float64 Series; strings of numbers are coerced."""
    s = frame[name]
    if s.dtype.is_numeric():
        return s.cast(nw.Float64)
    all_null_bool = s.dtype == nw.Boolean and s.null_count() == len(s)  # R/arrow write an all-NA column as logical
    if s.dtype not in (nw.String, nw.Object, nw.Unknown) and not all_null_bool:  # Unknown: a polars Null column
        raise TypeError(f"column {name!r} must be numeric or strings of numbers, not {s.dtype}")
    values: list[float | None] = []
    bad: list[Any] = []
    for v in s.to_list():
        if _missing(v):
            values.append(None)
            continue
        if type(v).__name__ in ("bool", "bool_"):  # Python and numpy booleans, which float() reads as 1.0 / 0.0
            raise TypeError(f"column {name!r} must be numeric or strings of numbers, not booleans")
        try:  # float() reads strings and numbers; R's as.numeric() reads no "_" digit separators, so neither do we
            f = math.nan if isinstance(v, str) and "_" in v else float(v)
        except (TypeError, ValueError):
            f = math.nan
        if math.isnan(f):
            bad.append(v)
        values.append(f)
    if bad:
        raise ValueError(
            f"column {name!r} has values that are not numbers: {sorted(set(map(str, bad)))}; name the coordinate "
            "columns with x=/y=, or fix the input data"
        )
    return nw.new_series(name, values, nw.Float64(), backend=nw.get_native_namespace(frame))


def court_coords(data: Any, x: str = "x_legacy", y: str = "y_legacy") -> Any:
    """Convert stats.nba.com / stats.wnba.com shot locations to the court frame sportypy draws.

    The stats API's legacy shot frame (``LOC_X``/``LOC_Y``; hoopR, wehoop and sdv-py ``x_legacy``/``y_legacy``) is in
    tenths of a foot with the hoop at the origin, relative to the shooter's basket. sportypy's ``NBACourt``,
    ``WNBACourt`` and ``NCAACourt`` (what ``surface("nba")`` draws) put the origin at center court, the baseline at
    ``x = -47`` and the basket at ``x = -41.75``. So ``court_x = -47 + 5.25 + y / 10`` and ``court_y = x / 10``, with no
    sign flip: a left-corner three lands at negative ``court_y``. Every shot falls on the TV-left half; draw a half
    court with ``surface("nba", display_range="defense")``. Don't pass ESPN ``coordinate_x``/``coordinate_y``: they
    are already in feet on a center-court frame.

    Args:
        data: A pandas or polars DataFrame of shots.
        x: The column holding ``LOC_X`` / ``x_legacy`` (tenths of a foot, across the court).
        y: The column holding ``LOC_Y`` / ``y_legacy`` (tenths of a foot, toward half court).

    Returns:
        DataFrame: ``data``'s type, with ``court_x`` and ``court_y`` (feet, Float64) added; existing columns of those
        names are replaced in place, every other column is kept. Numeric columns and strings of numbers (stats.nba.com
        payloads arrive as strings) convert; nulls stay null, and an all-null column gives null coordinates.

    Raises:
        TypeError: If ``data`` is not a pandas/polars DataFrame, ``x``/``y`` is not a string, or a coordinate column
            is boolean (or holds booleans), categorical or another non-numeric type.
        ValueError: If ``x`` and ``y`` name the same column, a column is missing, or a string is not a number (such
            as ``""``, ``"NA"`` or ``"1_0"``).

    Example:
        ::

            import polars as pl
            import sdvplot

            shots = pl.DataFrame({"LOC_X": [-224, 240], "LOC_Y": [39, 29]})
            out = sdvplot.court_coords(shots, x="LOC_X", y="LOC_Y")
            out["court_y"].to_list()   # [-22.4, 24.0]: a left and a right corner three

            ax = sdvplot.surface("nba", display_range="defense")
            ax.scatter(out["court_x"], out["court_y"], zorder=20)

    See Also:
        sdvplotR sdv_court_coords(): https://sdvplotR.sportsdataverse.org/ ;
        sportypy: https://sportypy.sportsdataverse.org/ ;
        nba_api shotchartdetail: https://github.com/swar/nba_api
    """
    try:
        frame = nw.from_native(data, eager_only=True)
    except TypeError:
        raise TypeError(f"data must be a pandas or polars DataFrame, got {type(data).__name__}") from None
    for arg, column in (("x", x), ("y", y)):
        if not isinstance(column, str):
            raise TypeError(f"{arg} must be a single column name (a string), got {column!r}")
    if x == y:
        raise ValueError(f"x and y must name different columns, not both {x!r}")
    missing = [c for c in (x, y) if c not in frame.columns]
    if missing:
        raise ValueError(
            f"data is missing column(s) {missing}; name the stats-API columns with x=/y=, e.g. x='LOC_X', y='LOC_Y'"
        )
    # Divide by a Series of tens, not the scalar: polars divides by a scalar through its reciprocal, so -224 / 10 would
    # be -22.400000000000002 instead of R's (and IEEE division's) -22.4.
    ten = nw.new_series("ten", [10.0] * len(frame), nw.Float64(), backend=nw.get_native_namespace(frame))
    xs, ys = _tenths(frame, x) / ten, _tenths(frame, y) / ten
    return frame.with_columns(court_x=ys + BASKET_X, court_y=xs).to_native()

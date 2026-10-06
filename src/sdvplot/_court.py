"""Shot locations from the stats.nba.com legacy frame (or the Euroleague one) to sportypy's court: the port of
sdvplotR's sdv_court_coords()."""

from __future__ import annotations

import math
from typing import Any

import narwhals as nw

from sdvplot._errors import InputError
from sdvplot._placement import _missing

BASKET_X = -47 + 5.25  # sportypy's NBA/WNBA/NCAA courts: center-court origin, baseline at -47, basket 5.25 ft in

# One row per shot frame: input units per output unit, the basket's x on the sportypy court the output lands on
# (center-court origin), and the provider's "no location" pair, if any. The same table as sdvplotR's court_providers.
PROVIDERS: dict[str, tuple[float, float, tuple[float, float] | None]] = {
    "nba": (10.0, BASKET_X, None),  # tenths of a foot -> feet
    "euroleague": (100.0, -12.425, (-1.0, -1.0)),  # cm -> meters; sportypy's FIBACourt: 28 m long, basket 1.575 m in
}


def _numeric(frame: Any, name: str) -> Any:
    """Column ``name`` as a Float64 Series; strings of numbers are coerced (court_coords and pitch_coords share it)."""
    s = frame[name]
    if s.dtype.is_numeric():  # rebuilt like the coerced columns, so both outputs share one dtype (pandas nullable too)
        floats = [None if _missing(v) else v for v in s.cast(nw.Float64).to_list()]
        return nw.new_series(name, floats, nw.Float64(), backend=nw.get_native_namespace(frame))
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


def court_coords(data: Any, *, x: str = "x_legacy", y: str = "y_legacy", provider: str = "nba") -> Any:
    """Convert stats.nba.com / stats.wnba.com (or Euroleague) shot locations to the court frame sportypy draws.

    The stats API's legacy shot frame (``LOC_X``/``LOC_Y``; hoopR, wehoop and sdv-py ``x_legacy``/``y_legacy``) is in
    tenths of a foot with the hoop at the origin, relative to the shooter's basket. sportypy's ``NBACourt``,
    ``WNBACourt`` and ``NCAACourt`` (what ``surface("nba")`` draws) put the origin at center court, the baseline at
    ``x = -47`` and the basket at ``x = -41.75``. So ``court_x = -47 + 5.25 + y / 10`` and ``court_y = x / 10``, with no
    sign flip: a left-corner three lands at negative ``court_y``. Every shot falls on the TV-left half; draw a half
    court with ``surface("nba", display_range="defense")``. Don't pass ESPN ``coordinate_x``/``coordinate_y``: they
    are already in feet on a center-court frame.

    ``provider="euroleague"`` converts the Euroleague shot frame of sportsdataverse-py's ``euroleague_game_points()``
    (``coord_x``/``coord_y``; measured on real games, 2026-10-06): integer centimeters with the hoop at the origin,
    both teams mapped onto one basket, ``coord_y`` growing away from the baseline toward the court, and free throws
    encoded as ``coord_x = coord_y = -1`` (a sentinel, not a location), which become null. The output is meters on
    sportypy's ``FIBACourt`` (what ``surface("fiba")`` draws): 28 x 15 m, basket 1.575 m from the baseline, so
    ``court_x = -12.425 + coord_y / 100`` and ``court_y = coord_x / 100``. Which sideline is positive ``coord_x`` is
    unverified, so a chart may be left-right mirrored; the court is symmetric, so distances and zones are unaffected.

    Args:
        data: A pandas or polars DataFrame of shots.
        x: The column holding ``LOC_X`` / ``x_legacy`` (tenths of a foot, across the court), or Euroleague
            ``coord_x`` (centimeters).
        y: The column holding ``LOC_Y`` / ``y_legacy`` (tenths of a foot, toward half court), or Euroleague
            ``coord_y`` (centimeters).
        provider: The frame of ``data``, which sets the output's units: ``"nba"`` (the default; stats.nba.com /
            stats.wnba.com, tenths of a foot in, **feet** out on the NBA/WNBA/NCAA court) or ``"euroleague"``
            (``euroleague_game_points()`` ``coord_x``/``coord_y``, centimeters in, **meters** out on the FIBA court).
            Case is ignored.

    Returns:
        DataFrame: ``data``'s type, with ``court_x`` and ``court_y`` (Float64; feet for ``"nba"``, meters for
        ``"euroleague"``) added; existing columns of those names are replaced in place, every other column is kept.
        Numeric columns and strings of numbers (stats.nba.com payloads arrive as strings) convert; nulls stay null,
        and an all-null column gives null coordinates.

    Raises:
        TypeError: If ``data`` is not a pandas/polars DataFrame, ``x``/``y``/``provider`` is not a string, or a
            coordinate column is boolean (or holds booleans), categorical or another non-numeric type.
        InputError: If ``provider`` is not ``"nba"`` or ``"euroleague"``.
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

            # Euroleague shots (sportsdataverse-py euroleague_game_points() columns) onto the FIBA court: the
            # rim, the lane, a corner three and a free throw
            euro = pl.DataFrame({"coord_x": [0, 0, -650, -1], "coord_y": [0, 400, 50, -1]})
            euro = sdvplot.court_coords(euro, x="coord_x", y="coord_y", provider="euroleague")
            euro["court_x"].to_list()   # [-12.425, -8.425, -11.925, None]: meters; the free throw is null
            ax = sdvplot.surface("fiba", display_range="defense")
            ax.scatter(euro["court_x"], euro["court_y"], zorder=20)

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
    if not isinstance(provider, str):
        raise TypeError(f"provider must be a string such as 'nba', got {type(provider).__name__}")
    if provider.lower() not in PROVIDERS:
        raise InputError(f"provider must be one of {list(PROVIDERS)}, got {provider!r}")
    per_unit, basket_x, sentinel = PROVIDERS[provider.lower()]
    if x == y:
        raise ValueError(f"x and y must name different columns, not both {x!r}")
    missing = [c for c in (x, y) if c not in frame.columns]
    if missing:
        raise ValueError(
            f"data is missing column(s) {missing}; name the stats-API columns with x=/y=, e.g. x='LOC_X', y='LOC_Y'"
        )
    backend = nw.get_native_namespace(frame)
    xs, ys = _numeric(frame, x), _numeric(frame, y)
    if sentinel is not None:  # the provider's "no location" pair -> null on both outputs, like sdvplotR's NA
        none = ((xs == sentinel[0]) & (ys == sentinel[1])).fill_null(False)
        null = nw.new_series("null", [None] * len(frame), nw.Float64(), backend=backend)
        xs, ys = xs.zip_with(~none, null), ys.zip_with(~none, null)
    # Divide by a Series, not the scalar: polars divides by a scalar through its reciprocal, so -224 / 10 would be
    # -22.400000000000002 instead of R's (and IEEE division's) -22.4.
    per = nw.new_series("per", [per_unit] * len(frame), nw.Float64(), backend=backend)
    xs, ys = xs / per, ys / per
    return frame.with_columns(court_x=ys + basket_x, court_y=xs).to_native()

---
title: court_coords
sidebar_label: court_coords
sidebar_position: 15
---

# court_coords

<div class="sdv-signature">

```python
court_coords(
    data: Any,
    *,
    x: str = 'x_legacy',
    y: str = 'y_legacy',
    provider: str = 'nba',
) -> Any
```

</div>

Convert stats.nba.com / stats.wnba.com (or Euroleague) shot locations to the court frame sportypy draws.

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

## Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | A pandas or polars DataFrame of shots. |
| `x` | `str` | The column holding ``LOC_X`` / ``x_legacy`` (tenths of a foot, across the court), or Euroleague ``coord_x`` (centimeters). |
| `y` | `str` | The column holding ``LOC_Y`` / ``y_legacy`` (tenths of a foot, toward half court), or Euroleague ``coord_y`` (centimeters). |
| `provider` | `str` | The frame of ``data``, which sets the output's units: ``"nba"`` (the default; stats.nba.com / stats.wnba.com, tenths of a foot in, **feet** out on the NBA/WNBA/NCAA court) or ``"euroleague"`` (``euroleague_game_points()`` ``coord_x``/``coord_y``, centimeters in, **meters** out on the FIBA court). Case is ignored. |

## Returns

`DataFrame` — ``data``'s type, with ``court_x`` and ``court_y`` (Float64; feet for ``"nba"``, meters for ``"euroleague"``) added; existing columns of those names are replaced in place, every other column is kept. Numeric columns and strings of numbers (stats.nba.com payloads arrive as strings) convert; nulls stay null, and an all-null column gives null coordinates.

## Raises

- `TypeError`: If ``data`` is not a pandas/polars DataFrame, ``x``/``y``/``provider`` is not a string, or a coordinate column is boolean (or holds booleans), categorical or another non-numeric type.
- `InputError`: If ``provider`` is not ``"nba"`` or ``"euroleague"``.
- `ValueError`: If ``x`` and ``y`` name the same column, a column is missing, or a string is not a number (such as ``""``, ``"NA"`` or ``"1_0"``).

## Example

```python
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
```

## See also

- [sdvplotR sdv_court_coords()](https://sdvplotR.sportsdataverse.org/)
- [sportypy](https://sportypy.sportsdataverse.org/)
- [nba_api shotchartdetail](https://github.com/swar/nba_api)

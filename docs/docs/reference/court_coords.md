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
) -> Any
```

</div>

Convert stats.nba.com / stats.wnba.com shot locations to the court frame sportypy draws.

The stats API's legacy shot frame (``LOC_X``/``LOC_Y``; hoopR, wehoop and sdv-py ``x_legacy``/``y_legacy``) is in
tenths of a foot with the hoop at the origin, relative to the shooter's basket. sportypy's ``NBACourt``,
``WNBACourt`` and ``NCAACourt`` (what ``surface("nba")`` draws) put the origin at center court, the baseline at
``x = -47`` and the basket at ``x = -41.75``. So ``court_x = -47 + 5.25 + y / 10`` and ``court_y = x / 10``, with no
sign flip: a left-corner three lands at negative ``court_y``. Every shot falls on the TV-left half; draw a half
court with ``surface("nba", display_range="defense")``. Don't pass ESPN ``coordinate_x``/``coordinate_y``: they
are already in feet on a center-court frame.

## Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | A pandas or polars DataFrame of shots. |
| `x` | `str` | The column holding ``LOC_X`` / ``x_legacy`` (tenths of a foot, across the court). |
| `y` | `str` | The column holding ``LOC_Y`` / ``y_legacy`` (tenths of a foot, toward half court). |

## Returns

`DataFrame` — ``data``'s type, with ``court_x`` and ``court_y`` (feet, Float64) added; existing columns of those names are replaced in place, every other column is kept. Numeric columns and strings of numbers (stats.nba.com payloads arrive as strings) convert; nulls stay null, and an all-null column gives null coordinates.

## Raises

- `TypeError`: If ``data`` is not a pandas/polars DataFrame, ``x``/``y`` is not a string, or a coordinate column is boolean (or holds booleans), categorical or another non-numeric type.
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
```

## See also

- [sdvplotR sdv_court_coords()](https://sdvplotR.sportsdataverse.org/)
- [sportypy](https://sportypy.sportsdataverse.org/)
- [nba_api shotchartdetail](https://github.com/swar/nba_api)

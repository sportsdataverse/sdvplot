---
title: pitch_coords
sidebar_label: pitch_coords
sidebar_position: 16
---

# pitch_coords

<div class="sdv-signature">

```python
pitch_coords(
    data: Any,
    *,
    provider: str,
    x: str | None = None,
    y: str | None = None,
    flip: bool | str | None = None,
    pitch_length: float | None = None,
    pitch_width: float | None = None,
) -> Any
```

</div>

Convert soccer event coordinates from any provider's frame to the pitch ``surface("soccer")`` draws.

Opta and Wyscout run 0-100 on both axes and are not to scale, StatsBomb uses 120 x 80, tracking providers use
meters or centimeters from the center spot, and ESPN reports the distance from the attacked goal as a fraction of
half the pitch. This converts any of them to one frame: meters, origin at the center spot, a regulation 105 x 68 m
pitch, attacking toward +x, with +y on the attacker's left. The conversion is piecewise-linear between pitch
landmarks (goal line, six-yard line, penalty spot, box edge and halfway line along the pitch; touchline, box side,
six-yard side and post across it), so a shot on the edge of an Opta box lands on the edge of the regulation box;
points beyond the outermost landmark are extrapolated, not clamped. The landmarks come from mplsoccer and ship in
``sdvplot/data/pitch_landmarks.csv``, byte-identical to sdvplotR's.

ESPN's frame is derived from Opta's (``opta_x = 100 - 50 * x``, ``opta_y = 100 * (1 - y)``), and ESPN's ``(0, 0)``
"no location" becomes null. Event providers record every action as if the team attacked left to right; ``flip``
turns rows half a turn (``pitch_x`` and ``pitch_y`` both change sign) so two teams attack opposite ends with each
wing on its own side.

## Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | A pandas or polars DataFrame of events. |
| `provider` | `str` | The frame of ``data``: "opta" (alias "statsperform"), "wyscout", "statsbomb", "uefa", "impect", "espn", "tracab" (cm), "skillcorner", "secondspectrum" (m) or "metrica" (0-1). Case is ignored. |
| `x` | `str \| None` | The x column; None uses the provider's usual name ("field_position_x" for ESPN, as sportsdataverse-py's ``espn_soccer_game_plays`` returns it; "x" otherwise). |
| `y` | `str \| None` | The y column; None uses "field_position_y" for ESPN, "y" otherwise. |
| `flip` | `bool \| str \| None` | None (no row flipped), True/False for every row, or the name of a boolean column with no missing values. |
| `pitch_length` | `float \| None` | The venue's length in meters (90-120), for tracking providers only. |
| `pitch_width` | `float \| None` | The venue's width in meters (45-90), for tracking providers only. |

## Returns

`DataFrame` — ``data``'s type, with ``pitch_x`` (meters along the pitch: -52.5 is the defended goal line, 52.5 the attacked one) and ``pitch_y`` (meters across: -34 to 34, positive = the attacker's left) added as Float64; existing columns of those names are replaced in place, every other column is kept. Nulls stay null.

## Raises

- `TypeError`: If ``data`` is not a pandas/polars DataFrame, ``provider`` is not a string, ``x``/``y`` is not a string, ``flip`` has the wrong type, or a coordinate column is boolean or another non-numeric type.
- `InputError`: If ``provider`` is unknown, ``pitch_length``/``pitch_width`` are given to a fixed-frame provider, missing for a tracking one or out of range, ``x`` and ``y`` name the same column, a column is missing, a string is not a number, or the ``flip`` column is not boolean or has missing values.

## Example

```python
import polars as pl
import sdvplot

shots = pl.DataFrame({"x": [88.5, 83, 50], "y": [50.0, 21.1, 100.0], "away": [False, True, False]})
out = sdvplot.pitch_coords(shots, provider="opta", flip="away")
out["pitch_x"].to_list()   # [41.5, -36.0, 0.0]: the spot, the far box edge, halfway

ax = sdvplot.surface("soccer")
ax.scatter(out["pitch_x"], out["pitch_y"], zorder=20)
```

## See also

- [sdvplotR sdv_pitch_coords()](https://sdvplotR.sportsdataverse.org/)
- [mplsoccer Standardizer](https://mplsoccer.readthedocs.io/)
- [ggsoccer rescale_coordinates()](https://github.com/Torvaney/ggsoccer)

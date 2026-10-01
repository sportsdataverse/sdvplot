---
title: palette
sidebar_label: palette
sidebar_position: 4
---

# `palette`

```python
palette(league: str, which: str = 'primary', teams: Any = None, season: Any = None) -> dict[typing.Any, str]
```

A ``{team: "#hex"}`` dict for a league, ready for seaborn, Plotly, Altair, Bokeh or PyPalettes.

Without ``teams`` the keys are canonical abbreviations. With ``teams`` the keys are the caller's own values, so
they match a seaborn ``hue`` column or a Plotly color column exactly.

## Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `which` | `str` | "primary" or "secondary". |
| `teams` | `Any` | Team values to key the dict by; None returns the whole league. |
| `season` | `Any` | One season, or one per team, for values reused across eras. |

## Returns

`dict` — ``{team: "#hex"}``. Teams that do not resolve, or have no color, are left out.

## Raises

- `ValueError`: If ``league`` is unknown or ``which`` is not "primary"/"secondary".

## Example

```python
import sdvplot

sdvplot.palette("nfl", teams=["KC", "SF"])   # {'KC': '#e31837', 'SF': '#aa0000'}
```

## See also

sdvplotR: https://sdvplotR.sportsdataverse.org/ ; sdv-py: https://py.sportsdataverse.org/

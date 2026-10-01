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

Without ``teams`` the keys are canonical abbreviations, or the team_id where a team has no abbreviation or shares
it with another team of the league (never guessing which team an abbreviation means). With ``teams`` the keys are
the caller's own values, so they match a seaborn ``hue`` column or a Plotly color column exactly.

## Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `which` | `str` | "primary" or "secondary". |
| `teams` | `Any` | Team values to key the dict by; None returns the whole league. |
| `season` | `Any` | One season, or one per team, for values reused across eras. |

## Returns

`dict` — ``{team: "#hex"}``. Teams that do not resolve, or have no color, are left out. Without ``teams``, a team whose abbreviation another team of the league shares is keyed by its team_id, with one SdvplotWarning naming the shared abbreviations.

## Raises

- `TypeError`: If ``teams`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
- `ValueError`: If ``league`` is unknown, ``which`` is not "primary"/"secondary", or ``season`` is not a year (or a list whose length does not match the teams).

## Example

```python
import sdvplot

sdvplot.palette("nfl", teams=["KC", "SF"])   # {'KC': '#e31837', 'SF': '#aa0000'}
```

## See also

sdvplotR: https://sdvplotR.sportsdataverse.org/ ; sdv-py: https://py.sportsdataverse.org/

---
title: palette
sidebar_label: palette
sidebar_position: 4
---

# palette

<div class="sdv-signature">

```python
palette(
    league: str,
    teams: Any = None,
    *,
    which: Literal['primary', 'secondary'] = 'primary',
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
) -> dict[Any, str]
```

</div>

A ``{team: "#hex"}`` dict for a league, ready for seaborn, Plotly, Altair, Bokeh or PyPalettes.

Without ``teams`` the keys are canonical abbreviations, or the team_id where a team has no abbreviation or shares
it with another team of the league (never guessing which team an abbreviation means). With ``teams`` the keys are
the caller's own values, so they match a seaborn ``hue`` column or a Plotly color column exactly.

## Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `teams` | `Any` | Team values to key the dict by; None returns the whole league. |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary". |
| `season` | `Any` | One season, or one per team, for values reused across eras. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``teams``, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |

## Returns

`dict` — ``{team: "#hex"}``. Teams that do not resolve, or have no color, are left out. Without ``teams``, a team whose abbreviation another team of the league shares is keyed by its team_id, with one SdvplotWarning naming the shared abbreviations.

## Raises

- `TypeError`: If ``teams`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
- `InputError`: (a ValueError) If ``league`` is not a known league key, ``which`` is not "primary"/"secondary", or ``teams`` holds "primary" or "secondary" (the slot goes in ``which=``).
- `ValueError`: If ``season`` is not a year (or a list whose length does not match the teams), or ``id_system`` is unknown.
- `UnresolvedTeamError`: If ``strict=True`` and a team does not resolve.

## Example

```python
import sdvplot

sdvplot.palette("nfl", teams=["KC", "SF"])   # {'KC': '#e31837', 'SF': '#aa0000'}
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

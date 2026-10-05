---
title: team_colors
sidebar_label: team_colors
sidebar_position: 5
---

# team_colors

<div class="sdv-signature">

```python
team_colors(
    league: str,
    teams: Any,
    *,
    which: Literal['primary', 'secondary'] = 'primary',
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
) -> Any
```

</div>

One "#hex" (or None) per team value, in the same container the values came in.

## Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `teams` | `Any` | A scalar, list/tuple, numpy array, or pandas/polars Series of team identifiers. |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary". |
| `season` | `Any` | One season, or one per team, for values reused across eras. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``teams``, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |

## Returns

str | list | Series | None: The hex color for each team, None where a team does not resolve or has no color.

## Raises

- `TypeError`: If ``teams`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
- `InputError`: (a ValueError) If ``league`` is not a known league key (a list or Series there is the pre-0.1 ``team_colors(teams, league)`` order), ``which`` is not "primary"/"secondary", ``id_system`` is unknown, or ``season`` is not a year, is outside the seasons sdvplot knows for the league, or is a list whose length does not match the teams.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

## Example

```python
import sdvplot

sdvplot.team_colors("nfl", ["KC", "SF"])              # ['#e31837', '#aa0000']
sdvplot.team_colors("nfl", "KC", which="secondary")   # '#ffb612'
sdvplot.team_colors("nhl", [1, 6, 10], id_system="nhl_id")   # NHL stats ids: Devils, Bruins, Leafs
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

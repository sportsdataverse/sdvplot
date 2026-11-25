---
title: team_factor
sidebar_label: team_factor
sidebar_position: 6
---

# team_factor

<div class="sdv-signature">

```python
team_factor(
    teams: Any,
    league: str,
    *,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'yahoo', 'kenpom', 'torvik', 'sdvplotr', 'name', 'nhl_id', 'fox', 'cbs', 'sports247', 'on3'] = 'auto',
    strict: bool = False,
) -> Any
```

</div>

The team values as an ordered categorical, its categories ordered by each team's abbreviation.

For a discrete axis or legend in team order (sdvplotR's ``sdv_team_factor()``, cfbplotR's ``cfb_team_factor()``):
plotnine, seaborn and Altair keep a categorical's order. The categories are the values as given (the first of each),
so labels stay the caller's; a value that does not resolve is null (with the resolver's warning), so a scale drops
it.

## Arguments

| Name | Type | Description |
|---|---|---|
| `teams` | `Any` | A scalar, list/tuple, numpy array, or pandas/polars Series of team identifiers. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per team, for values reused across eras. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'yahoo', 'kenpom', 'torvik', 'sdvplotr', 'name', 'nhl_id', 'fox', 'cbs', 'sports247', 'on3']` | The id system of ``teams``, as in ``resolve``. |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |

## Returns

`Series` — A pandas Series of an ordered ``category`` dtype for a pandas Series (its index kept), else a polars Series of dtype ``pl.Enum``, of the values as text (an integral number as its digits). The categories are the resolved values, by abbreviation (a team with none by its team_id), then value.

## Raises

- `TypeError`: If ``teams`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
- `InputError`: (a ValueError) If ``league`` or ``id_system`` is unknown, or ``season`` is not a year, is outside the seasons sdvplot knows for the league, or is a list whose length does not match the teams.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

## Example

```python
import sdvplot

f = sdvplot.team_factor(["KC", "BUF", "Kansas City Chiefs"], "nfl")
f.dtype.categories.to_list()   # ['BUF', 'KC', 'Kansas City Chiefs']
```

## See also

- [sdvplotR sdv_team_factor()](https://sdvplotR.sportsdataverse.org/reference/sdv_team_factor.html)
- sdvplot.resolve: the team ids behind the order

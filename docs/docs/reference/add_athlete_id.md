---
title: add_athlete_id
sidebar_label: add_athlete_id
sidebar_position: 13
---

# add_athlete_id

<div class="sdv-signature">

```python
add_athlete_id(
    df: Any,
    name_col: str,
    *,
    team_col: str | None = None,
    season_col: str | None = None,
    league: str = 'cfb',
    headshot_urls: bool = False,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'yahoo', 'kenpom', 'torvik', 'sdvplotr', 'name', 'nhl_id', 'fox', 'cbs', 'sports247', 'on3'] = 'auto',
    strict: bool = False,
) -> Any
```

</div>

Add each player's ESPN athlete id to a data frame of player names, matched to published rosters.

The id is the one the headshot helpers (``headshot_url``, ``add_headshots``) read. sdvplotR's
``sdv_add_athlete_id()``, cfbplotR's ``add_athlete_id_col()``. The rosters are cfbfastR-data's college football
rosters, 2009 on, downloaded when first needed and cached. Like cfbplotR's, the match is experimental: check the
ids.

Names match ignoring case, accents and surrounding spaces. Teams match through ``resolve``, so any name or id it
reads for the roster's team works; a team it cannot resolve matches by name. A name that matches more than one
athlete is left null (cfbplotR returns a row for each), so the result has a row per row of ``df``: pass
``team_col`` and ``season_col`` to tell players with one name apart. Without a season column the latest season's
rosters are read, or the season before when the latest is not published yet. Offline, or when a roster cannot be
read, the call warns and the ids it could not find are null; it does not raise.

## Arguments

| Name | Type | Description |
|---|---|---|
| `df` | `Any` | A pandas or polars DataFrame (any narwhals-supported eager frame). |
| `name_col` | `str` | The column with player names. |
| `team_col` | `str \| None` | The column with each player's team, or None: then a "team" or "school" column of ``df``, if any. |
| `season_col` | `str \| None` | The column with each row's season, or None: then a "season" column of ``df``, if any. Seasons outside the rosters' (2009 to the latest) match no one. |
| `league` | `str` | A league with rosters: "cfb". |
| `headshot_urls` | `bool` | Also add each player's headshot URL (the roster's ESPN headshot). |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'yahoo', 'kenpom', 'torvik', 'sdvplotr', 'name', 'nhl_id', 'fox', 'cbs', 'sports247', 'on3']` | The id system of ``team_col``'s values, as in ``resolve`` ("auto" tries each in order). The rosters' own team names always resolve under "auto". |
| `strict` | `bool` | Raise UnresolvedTeamError when a team in ``team_col`` does not resolve, instead of matching it by name. |

## Returns

`DataFrame` — ``df`` (same library) with an ``athlete_id`` String column, null where no single athlete matched, and with ``headshot_urls=True`` a ``headshot_url`` column.

## Raises

- `InputError`: (a ValueError) If ``league`` is not a known league key or ``id_system`` is unknown.
- `ValueError`: If ``league`` has no rosters, ``df`` already has an ``athlete_id`` column, or a column named is not in ``df``.
- `TypeError`: If ``df`` is not a data frame.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team in ``team_col`` does not resolve.

## Example

```python
import polars as pl
import sdvplot

x = pl.DataFrame({"player_name": ["Britain Covey", "JT Daniels"], "team": ["Utah", "Georgia"],
                  "season": [2021, 2021]})
sdvplot.add_athlete_id(x, "player_name", headshot_urls=True)   # needs the network once
```

## See also

- [sdvplotR sdv_add_athlete_id()](https://sdvplotR.sportsdataverse.org/reference/sdv_add_athlete_id.html)
- sdvplot.headshot_url: the headshot behind an id

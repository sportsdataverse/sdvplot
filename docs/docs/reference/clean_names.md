---
title: clean_names
sidebar_label: clean_names
sidebar_position: 5
---

# clean_names

<div class="sdv-signature">

```python
clean_names(
    values: Any,
    league: str,
    *,
    column: str = 'location',
    keep_non_matches: bool = True,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'yahoo', 'kenpom', 'torvik', 'sdvplotr', 'name', 'nhl_id', 'fox', 'cbs', 'sports247', 'on3'] = 'auto',
    strict: bool = False,
) -> Any
```

</div>

One display name per team value, for joins and labels (cfbplotR's ``clean_school_names()``).

Every alias and id system ``resolve`` reads cleans to the same name, and a value it cannot resolve without guessing
(an unknown name, or one that names two teams) is not cleaned. sdvplotR's ``sdv_clean_names()``; with
``column="abbr"`` it is cfbplotR's ``clean_team_abbrs()`` and nflplotR's abbreviation cleaner.

## Arguments

| Name | Type | Description |
|---|---|---|
| `values` | `Any` | A scalar, list/tuple, numpy array, or pandas/polars Series of team identifiers. |
| `league` | `str` | The SDV league key, e.g. "cfb". |
| `column` | `str` | The ``teams`` column to return: "location" (the default; the school in college sports, the city in the pros, and closest to cfbplotR's names), "short_name", "name", "abbr" or "team_id". |
| `keep_non_matches` | `bool` | True (the default) keeps a value that does not resolve as it is, quietly (an integral number as its digits, 14.0 as "14"). False makes it None, with one SdvplotWarning per call. |
| `season` | `Any` | One season, or one per value, for values reused across eras. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'yahoo', 'kenpom', 'torvik', 'sdvplotr', 'name', 'nhl_id', 'fox', 'cbs', 'sports247', 'on3']` | The id system of ``values``, as in ``resolve``. |
| `strict` | `bool` | Raise UnresolvedTeamError when a value does not resolve, whatever ``keep_non_matches`` says. |

## Returns

str | list | Series | None: The same shape as ``values``: the name for each value (None where a resolved team has no value in ``column``), as text.

## Raises

- `TypeError`: If ``values`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
- `InputError`: (a ValueError) If ``column`` is not one of the five above, ``league`` or ``id_system`` is unknown, or ``season`` is not a year, is outside the seasons sdvplot knows for the league, or is a list whose length does not match the values.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a value does not resolve.

## Example

```python
import sdvplot

x = ["utah", "San Jose State", "Hawaii", "UTSA", "SLC", "USC"]
sdvplot.clean_names(x, "cfb")                          # unresolved values kept as given
sdvplot.clean_names(x, "cfb", keep_non_matches=False)  # or None, with one warning
sdvplot.clean_names(["Kansas City Chiefs", "OAK"], "nfl", column="abbr")   # ['KC', 'LV']
```

## See also

- [sdvplotR sdv_clean_names()](https://sdvplotR.sportsdataverse.org/reference/sdv_clean_names.html)
- sdvplot.aliases: every name the index knows

---
title: Seasons and eras
sidebar_label: Seasons and eras
---

# Seasons and eras

`resolve()`, `palette()`, `team_colors()`, `logo_url()`, `logo_image()` and `marks()` all take a `season`.

## Season conventions

Seasons follow the SportsDataverse conventions, the same as the logo archive:

- **NHL, NBA, men's and women's college basketball (`nhl`, `nba`, `mbb`, `wbb`):** the **ending** year. The 1994-95
  NHL season is `1995`.
- **Every other league:** the single or **starting** year. The 2010 NFL season is `2010`.

For example, the Quebec Nordiques' last season was 1994-95 and the Colorado Avalanche's first was 1995-96:

```python
import sdvplot

sdvplot.logo_url("COL", "nhl", season=1995)  # the Quebec Nordiques mark (archived for 1980-1995)
sdvplot.logo_url("COL", "nhl", season=1996)  # the first Avalanche mark (1996-1999)
```

A season is a year: `2010`, `2010.0` or `"2010"`. `None` or NaN means no season. Anything else, such as `"2019-20"`,
raises `InputError` (a `ValueError`), and so does a year outside the seasons the index knows for the league (the NFL's
start at 1920). Pass one season for every value, or a list with one season per value:

```python
sdvplot.resolve(["OAK", "LV"], "nfl", season=[2010, 2024])  # ['13', '13']
```

## Reused codes

Aliases can carry a season range. When you pass a season, `resolve()` first looks only at aliases whose range covers
it, so a code that two teams used in different eras goes to the team that held it that season. Without a season, a
reused code means its current holder: `resolve()` reads it in the latest season the league's aliases name. Last, it
looks at every alias, so a code still resolves when the season is outside its range, such as a modern abbreviation on
old data.

In the bundled index the reused codes are MLB Stats API abbreviations. `KCA` is the Kansas City Royals, but the
Athletics in 1955-67. `WAS` is the Washington Nationals, but the Twins' franchise in 1901-60 and the Rangers' in
1961-71. `SEA` is the Seattle Mariners, but the Brewers' franchise (the Pilots) in 1968-69. `MIL` is the Milwaukee
Brewers, but the Braves in 1953-65. Elsewhere a season does not change which team a value resolves to (nflverse's
`"LA"` is always the Rams); where it does matter is the logo.

## Relocations

A relocated franchise keeps one `team_id`. Its old codes are aliases with the seasons they were used, and its old marks
are dated the same way:

| League | Code | Franchise | Old mark's seasons |
|---|---|---|---|
| NFL | `OAK` | Raiders (`"13"`, now `LV`) | 1960-2019 |
| NFL | `SD` | Chargers (`"24"`, now `LAC`) | 1961-2016 |
| NFL | `STL` | Rams (`"14"`, now `LAR`) | 1995-2015 |
| WNBA | `SAS` | Aces (`"17"`, now `LV`), in San Antonio | 2003-2013 |
| WNBA | `SA` | Aces (`"17"`), in San Antonio | 2014-2017 |
| WNBA | `DET` | Wings (`"3"`, now `DAL`), in Detroit | 1998-2009 |
| WNBA | `TUL` | Wings (`"3"`), in Tulsa | 2010-2015 |

```python
sdvplot.resolve(["OAK", "SD", "STL"], "nfl")  # ['13', '24', '14']
sdvplot.resolve(["SAS", "SA", "DET", "TUL"], "wnba")  # ['17', '17', '3', '3']
```

## Today's mark, or that era's

Without a season, `logo_url()` and `logo_image()` return the team's current mark. With a season, they return the mark
in use that season. The season picks the mark, not the code you passed:

```python
sdvplot.logo_url("LV", "nfl")  # the Las Vegas mark
sdvplot.logo_url("LV", "nfl", season=2010)  # the Oakland mark
sdvplot.logo_url("OAK", "nfl", season=2010)  # the same Oakland mark
sdvplot.logo_url("OAK", "nfl", season=2024)  # the Las Vegas mark again
```

With a season, a mark whose dated range covers it wins over an undated (current) mark. If nothing covers the season,
you get the best mark of any era. [Logos](logos.md) has the full selection order, and the
[logos tutorial](../tutorials/03_logos_and_seasons.md) shows the eras side by side.

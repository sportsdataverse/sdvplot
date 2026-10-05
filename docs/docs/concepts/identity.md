---
title: Team identity
sidebar_label: Team identity
---

# Team identity

Every team in sdvplot has one canonical key: **`(league, team_id)`**.

- `league` is an SDV league key such as `"nfl"`, `"cfb"`, `"nhl"` or `"ohl"`. It is always required, because the same
  abbreviation means different teams in different leagues.
- `team_id` is always a **string**: the id the logo archive uses for that team. For ESPN leagues that is ESPN's team id,
  so the Kansas City Chiefs are `("nfl", "12")`.

`sdvplot.teams(league)` returns the bundled index, one row per team:

```python
import sdvplot

sdvplot.teams("nfl").shape  # (32, 12)
```

## Resolving what you have

`resolve()` turns the identifiers in your data into canonical `team_id`s:

```python
sdvplot.resolve("LV", "nfl")  # '13'
sdvplot.resolve(["KC", "kc", "Kansas City Chiefs", 12, "12.0"], "nfl")  # ['12', '12', '12', '12', '12']
```

Values are compared in one normal form: trimmed, case-folded, with accents and typographic punctuation folded, so
`"San José State"` matches `"San Jose State"`. Integral numbers lose their decimal point, so `12`, `"12"`, `12.0` and
`"12.0"` are the same value.

### Id systems

The index holds aliases from these id systems. With the default `id_system="auto"`, `resolve()` tries them in this order
(`sdvplot._resolve.PRIORITY`):

| Order | `id_system` | What it holds |
|---|---|---|
| 1 | `team_id` | the canonical id itself |
| 2 | `espn` | ESPN team ids |
| 3 | `espn_abbr` | ESPN abbreviations |
| 4 | `nhl` | NHL tri-codes, such as `"NJD"` |
| 5 | `nflverse` | nflverse abbreviations |
| 6 | `mlbstats` | MLB Stats API team ids (MLB and MiLB) |
| 7 | `nba_api` | nba_api team ids, such as `1610612747` |
| 8 | `hockeytech` | HockeyTech team ids (AHL, ECHL, OHL, PWHL, QMJHL, USHL, WHL) |
| 9 | `ncaa` | NCAA team ids (college football) |
| 10 | `pff` | PFF franchise ids (AAF) |
| 11 | `cricinfo` | Cricinfo team ids |
| 12 | `cfbd` | CFBD school names and abbreviations |
| 13 | `bref` | Sports Reference abbreviations (MLB, NBA, NFL, WNBA) |
| 14 | `sportsipy` | sportsipy abbreviations (MLB, NBA, NFL, WNBA) |
| 15 | `fangraphs` | FanGraphs abbreviations (MLB) |
| 16 | `sdvplotr` | sdvplotR's `clean_team_abbrs` keys |
| 17 | `name` | team names, short names and locations |

`sdvplotr` sits after every id system, so it only fills gaps. `name` comes last.

Pass `id_system=` to use a single system instead, for example `resolve(values, "mlb", id_system="fangraphs")`. An
`id_system` or `league` sdvplot does not know raises `InputError` (a `ValueError`), as does a `season` that is not a
year or is outside the seasons the index knows for the league.

### How "auto" decides

- The **first system that has a candidate** for the value decides. Later systems are not consulted.
- Only a **unique** match counts. If that system names more than one team, the value is ambiguous.
- With a `season`, sdvplot first considers only aliases whose season range covers that season. Then (or first, without
  a `season`) it reads the value in the latest season the league's aliases name, so a code two franchises used means its
  current holder. Last, it considers every alias, so a unique code still resolves when no range covers the season. See
  [Seasons and eras](seasons-and-eras.md).

## Never guessing

An unknown or ambiguous value comes back as `None`. One `SdvplotWarning` lists every value that failed, and why:

```python
sdvplot.resolve(["KC", "XXX"], "nfl")
# ['12', None]
# SdvplotWarning: 1 value(s) did not resolve to a nfl team: 'XXX' (unknown). Use sdvplot.suggest() for
# candidates, or strict=True to raise.

sdvplot.resolve("New York", "nfl")
# None, with a warning: 'New York' (ambiguous), because the Giants and the Jets share it
```

Pass `strict=True` to raise `UnresolvedTeamError` (a `ValueError`) instead.

`suggest()` is the only fuzzy matching in sdvplot. It returns `(team_id, name)` candidates, best first, and never picks
one for you:

```python
sdvplot.suggest("Kansas Cty Chiefs", "nfl")  # [('12', 'Kansas City Chiefs')]
sdvplot.suggest("New York", "nfl")
# [('19', 'New York Giants'), ('20', 'New York Jets'), ('18', 'New Orleans Saints')]
```

## Numeric NHL API ids

The NHL stats API numbers its teams 1 and up, and those numbers are also ESPN ids for other NHL teams. Under `"auto"` a
number is read as an ESPN id, so pass `id_system="nhl_id"` for NHL API ids. `"auto"` never tries `nhl_id`
(`sdvplot._resolve.EXPLICIT_ONLY`). NHL tri-codes resolve under `"auto"`.

```python
sdvplot.resolve(1, "nhl")  # '1'  (ESPN id 1: the Boston Bruins)
sdvplot.resolve(1, "nhl", id_system="nhl_id")  # '11' (NHL API id 1: the New Jersey Devils)
sdvplot.resolve("NJD", "nhl")  # '11'
```

## Containers

`resolve()` returns the shape it was given:

| Input | Output |
|---|---|
| a scalar | a `str`, or `None` |
| a list, tuple or numpy array | a `list` |
| a pandas Series | a pandas Series of strings, with the same name and index |
| a polars Series | a polars `String` Series with the same name |

```python
import pandas as pd

sdvplot.resolve(pd.Series(["KC", "SF"], index=[10, 20], name="team"), "nfl")
# 10    12
# 20    25
# Name: team
```

`team_colors()` follows the same rule.

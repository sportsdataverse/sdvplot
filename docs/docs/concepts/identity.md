---
title: Team identity
sidebar_label: Team identity
description: "How sdvplot resolves a team abbreviation, name or provider id to one canonical (league, team_id) key, and why it never guesses."
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

sdvplot.teams("nfl").shape  # (32, 13)
```

A college team's `division` is its NCAA division in its latest season in ESPN's groups: `"FBS"`, `"FCS"`, `"DII"` or
`"DIII"` in `cfb` (`teams("cfb").filter(pl.col("division") == "FCS")`), `"DI"`, `"DII"` or `"DIII"` in the other
college leagues, and null for a team with no NCAA division there (NAIA, a dropped program) and for pro teams. cfbplotR's
P5/G5 split is not a column: it is a grouping of conferences that changes (the Power Five became the Power Four in
2024), so take it from `conference_id` (the Power Four today: `cfb:acc`, `cfb:big-ten`, `cfb:big-12`, `cfb:sec`)
for the seasons you mean.

Conferences are opt-in (sdvplotR's `include_conferences`): `teams("cfb", include_conferences=True)` adds the league's
conference rows (and the league's own: the AFC, NFC and NFL; MLB, `AL` and `NL`; the NBA and WNBA with `East` and
`West`; the NHL with its division marks; the AAF; `NCAA` in every college league), with `program` `"conference"` or
`"league"` and the short name (`"SEC"`, `"Big 12"`, `"AFC"`, `"East"`) as `team_id` and `abbr`; a team's `conference_id` equals its
conference row's. Every other listing shows teams only, and `resolve()` and `palette()` never answer a conference key
(CFB's `MAC` is Macalester, not the Mid-American Conference). The logo functions take a conference's key and sdvplotR's
other names for it (`logo_url("Southeastern Conference", "cfb")` is `logo_url("SEC", "cfb")`), after every team.

Soccer is one league key, `soccer`, for every club ESPN covers. There `conference_id` and `conference` mean a club's
**domestic league**: the league competition it was seen in in its latest season, as ESPN's slug and name (`"eng.1"`,
`"English Premier League"`), so `teams("soccer").filter(pl.col("conference_id") == "eng.1")` is the Premier League.
Cups and the confederations' competitions are not leagues, and a club in two leagues that season gets none. National
teams (a World Cup or its qualifying) have `program` `"national"` and no domestic league. Every competition a club was
seen in, the Champions League and the cups included, is an alias of id system `"competition"` (value: the slug, dated
by that competition's season) in the index's alias table; `resolve()` never reads it, since one slug names many clubs.

## Resolving what you have

`resolve()` turns the identifiers in your data into canonical `team_id`s:

```python
sdvplot.resolve("LV", "nfl")  # '13'
sdvplot.resolve(["KC", "kc", "Kansas City Chiefs", 12, "12.0"], "nfl")  # ['12', '12', '12', '12', '12']
```

Values are compared in one normal form: trimmed, case-folded, with accents and typographic punctuation folded, so
`"San José State"` matches `"San Jose State"`. Eight Latin letters with no accent to drop fold too: `ø` to `o`, `æ` to
`ae`, `œ` to `oe`, `đ` and `ð` to `d`, `ł` to `l`, `þ` to `th` and `ı` to `i` (`ß` is `ss`), so `"Køge"` matches
`"Koge"` and `"Łódź"` matches `"Lodz"`. Integral numbers lose their decimal point, so `12`, `"12"`, `12.0` and
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
| 7 | `nba_api` | NBA and WNBA Stats team ids, such as `1610612747` (the Lakers) and `1611661319` (the Aces), and their tricodes (WNBA: `LVA`) |
| 8 | `hockeytech` | HockeyTech team ids (AHL, ECHL, OHL, PWHL, QMJHL, USHL, WHL, and the junior and minor leagues SPHL, CHL, BCHL, AJHL, SJHL, OJHL, CCHL, GOJHL, MHL, NOJHL, VIJHL, KIJHL, MJHL) |
| 9 | `ncaa` | stats.ncaa.org team ids: each season's team id (college football, men's and women's basketball, college baseball) and, outside football, each school's org id (Duke is `193`; college softball has org ids only) |
| 10 | `pff` | PFF franchise ids (AAF) |
| 11 | `cricinfo` | Cricinfo team ids |
| 12 | `cfbd` | CFBD school names and abbreviations |
| 13 | `bref` | Sports Reference abbreviations (MLB, NBA, NFL, WNBA) |
| 14 | `sportsipy` | sportsipy abbreviations (MLB, NBA, NFL, WNBA) |
| 15 | `fangraphs` | FanGraphs abbreviations (MLB) |
| 16 | `yahoo` | Yahoo team ids, such as `"nba.t.1"` and `"ncaaf.t.1"` (NFL, college football, NBA, WNBA, men's and women's college basketball, MLB, NHL) |
| 17 | `kenpom` | KenPom team names (men's college basketball) |
| 18 | `torvik` | Torvik (Barttorvik) team names (men's and women's college basketball) |
| 19 | `sdvplotr` | sdvplotR's `clean_team_abbrs` keys |
| 20 | `name` | team names, short names and locations, and cfbplotR's `team_name_mapping` spellings |

`sdvplotr` sits after every id system, so it only fills gaps. `name` comes last. A name that `name` or `cfbd` gives
several teams, none of them for a season range, goes to the one team whose own name (`name` or `short_name`) it is, so
another team's location never shadows it: `"Charlotte"` is the 49ers, not the Charlotte Saints (Faith NC, located in
Charlotte). One that is several teams' own name (`"Bethany"`), or no team's (`"New York"`), stays ambiguous. A
season-dated alias keeps its range: in a season it covers that also has another team's own-name alias, the value stays
ambiguous. cfbplotR's spellings (the `ARK STATE`, `VA TECH` feed forms, `NC St.`, `UT San Antonio`) only fill gaps:
one the index already has, for any team, adds nothing, and one cfbplotR's rows give two teams or no team adds nothing.

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

## Numeric NHL API, Fox, CBS, 247Sports and On3 ids

The NHL stats API numbers its teams 1 and up, and those numbers are also ESPN ids for other NHL teams. Under `"auto"` a
number is read as an ESPN id, so pass `id_system="nhl_id"` for NHL API ids. `"auto"` never tries `nhl_id`
(`sdvplot._resolve.EXPLICIT_ONLY`). NHL tri-codes resolve under `"auto"`.

```python
sdvplot.resolve(1, "nhl")  # '1'  (ESPN id 1: the Boston Bruins)
sdvplot.resolve(1, "nhl", id_system="nhl_id")  # '11' (NHL API id 1: the New Jersey Devils)
sdvplot.resolve("NJD", "nhl")  # '11'
```

Fox, CBS, 247Sports and On3 number teams too, and their numbers are also other teams' ESPN ids, so they are
explicit-only as well: `id_system="fox"`, `"cbs"`, `"sports247"` (247Sports team ids and institution keys) or `"on3"`
(On3 org keys). They come from sdv-reference-data's `{league}_team_aliases` tables, as do the Yahoo, KenPom and Torvik
aliases, with the seasons the source gives each id.

```python
sdvplot.resolve("25", "cfb")  # '25'  (ESPN id 25: California)
sdvplot.resolve("25", "cfb", id_system="fox")  # '194' (Fox id 25: Ohio State)
sdvplot.resolve("ncaaf.t.1", "cfb")  # Yahoo's dotted ids resolve under "auto"
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

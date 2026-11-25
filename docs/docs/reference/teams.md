---
title: teams
sidebar_label: teams
sidebar_position: 3
---

# teams

<div class="sdv-signature">

```python
teams(
    league: str | None = None,
    *,
    include_conferences: bool = False,
    division: str | collections.abc.Sequence[str] | None = None,
) -> polars.dataframe.frame.DataFrame
```

</div>

The bundled team index: one row per (league, team_id), with names, abbreviation, conference and colors.

## Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str \| None` | An SDV league key such as "nfl"; None returns every league. |
| `include_conferences` | `bool` | Also list the conference and league rows (sdvplotR's ``include_conferences``): the college conferences of cfb, mbb and wbb, the AFC, NFC and NFL, MLB with the AL and NL, the NBA and WNBA with their East and West, the NHL with its division marks, the AAF, and the NCAA in every college league. Their ``program`` is "conference" or "league", their ``team_id`` and ``abbr`` the short name ("SEC", "Big 12", "AFC", "East"), their colors cbbplotR's (``color_source`` "cbbplotR") or the placeholder, and a team's ``conference_id`` equals its conference row's. The default, False, lists teams only, so code that loops over teams sees only teams; conferences are opt-in everywhere (``resolve`` and ``palette`` never answer one). The mark helpers (``logo_url``, ``marks``, ``add_logos`` and the rest) do draw one, by this key, from the archive's conference, league and division marks ("SEC", "Big 12", "AFC", "NFL", "MLB"). |
| `division` | `str \| collections.abc.Sequence[str] \| None` | None (every team), or one or more of "FBS", "FCS", "DI", "DII", "DIII", "P4", "P5", "G5" and "Conference": only the teams in any of them, as cfbplotR's division filter keeps (sdvplotR's ``sdv_teams(division=)``). It needs a ``league``. "FBS", "FCS", "DI", "DII" and "DIII" read the ``division`` column; an index with no divisions for the league is an error. "P4" (the ACC, Big Ten, Big 12 and SEC, and Notre Dame), "P5" (the P4 and the Pac-12 as the index lists it) and "G5" (the American, Conference USA, the MAC, the Mountain West, the Sun Belt and the FBS independents but Notre Dame) are college football's, from each team's ``conference_id``, so they follow realignment as the index does. "Conference" gives the conference and league rows. With ``division``, ``include_conferences`` is not read. |

## Returns

`polars.DataFrame` — The index columns ``league``, ``team_id``, ``abbr``, ``name``, ``short_name``, ``location``, ``program``, ``conference_id``, ``conference``, ``color_primary``, ``color_secondary``, ``color_source`` ("nflverse", "espn" or "openf1": published colors; "logo": derived from the team's archived logo, where no source publishes any; "cbbplotR": a conference row's; "fallback": a placeholder) and ``division``. In ``soccer``, one pool of ESPN club ids, ``conference_id`` and ``conference`` are a club's domestic league (ESPN's slug and name: "eng.1", "English Premier League"), null for a national team (``program`` "national"). ``division`` is a college team's NCAA division in its latest season in ESPN's groups: "FBS", "FCS", "DII" or "DIII" in ``cfb``, "DI", "DII" or "DIII" in the other college leagues; null for a team with no NCAA division there (NAIA, a dropped program), a pro team and a conference or league row. cfbplotR's P5/G5 split is a conference grouping that changes (now the Power Four), so it is not a column: take it from ``conference_id``.

## Raises

- `InputError`: (a ValueError) If ``league`` is given and is not a known league key; with ``division``, if there is no ``league``, a value is not one of the divisions above, "P4"/"P5"/"G5" is asked of a league other than "cfb", or the index has no divisions for the league.

## Example

```python
import polars as pl
import sdvplot

sdvplot.teams("nfl").shape   # (32, 13)
sdvplot.teams("cfb", include_conferences=True).filter(pl.col("program") == "conference")["abbr"]
sdvplot.teams("cfb", division="P5")["location"]   # cfbplotR's P5 school list
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

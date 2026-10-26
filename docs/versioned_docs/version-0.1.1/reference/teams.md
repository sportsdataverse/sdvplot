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
) -> polars.dataframe.frame.DataFrame
```

</div>

The bundled team index: one row per (league, team_id), with names, abbreviation, conference and colors.

## Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str \| None` | An SDV league key such as "nfl"; None returns every league. |
| `include_conferences` | `bool` | Also list the conference and league rows (sdvplotR's ``include_conferences``): the college conferences of cfb, mbb and wbb, and the AFC, NFC and NFL. Their ``program`` is "conference" or "league", their ``team_id`` and ``abbr`` the conference's short name ("SEC", "Big 12", "AFC"), their colors cbbplotR's (``color_source`` "cbbplotR"), and a team's ``conference_id`` equals its conference row's. The default, False, lists teams only, so code that loops over teams sees only teams; conferences are opt-in everywhere (``resolve`` and ``palette`` never answer one). The mark helpers (``logo_url``, ``marks``, ``add_logos`` and the rest) do draw one, by this key, from the archive's conference and league marks ("SEC", "Big 12", "AFC", "NFL"). |

## Returns

`polars.DataFrame` — The index columns ``league``, ``team_id``, ``abbr``, ``name``, ``short_name``, ``location``, ``program``, ``conference_id``, ``conference``, ``color_primary``, ``color_secondary`` and ``color_source``: "nflverse" or "espn" (published colors), "logo" (derived from the team's archived logo, where no source publishes any), "cbbplotR" (a conference row's) or "fallback" (a placeholder).

## Raises

- `InputError`: (a ValueError) If ``league`` is given and is not a known league key.

## Example

```python
import polars as pl
import sdvplot

sdvplot.teams("nfl").shape   # (32, 12)
sdvplot.teams("cfb", include_conferences=True).filter(pl.col("program") == "conference")["abbr"]
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

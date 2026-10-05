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
) -> polars.dataframe.frame.DataFrame
```

</div>

The bundled team index: one row per (league, team_id), with names, abbreviation, conference and colors.

## Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str \| None` | An SDV league key such as "nfl"; None returns every league. |

## Returns

`polars.DataFrame` — The index columns ``league``, ``team_id``, ``abbr``, ``name``, ``short_name``, ``location``, ``program``, ``conference_id``, ``conference``, ``color_primary``, ``color_secondary`` and ``color_source``.

## Raises

- `ValueError`: If ``league`` is given and unknown.

## Example

```python
import sdvplot

sdvplot.teams("nfl").shape   # (32, 12)
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

---
title: aliases
sidebar_label: aliases
sidebar_position: 4
---

# aliases

<div class="sdv-signature">

```python
aliases(
    league: str | None = None,
) -> polars.dataframe.frame.DataFrame
```

</div>

Every team name, abbreviation and provider id the bundled index resolves, one row per alias.

What ``resolve`` reads, as a table (sdvplotR's ``sdv_aliases()``, and the counterpart of cfbplotR's
``team_name_mapping``: join ``team_id`` to ``teams`` for each alias's school).

## Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str \| None` | An SDV league key such as "cfb"; None returns every league. |

## Returns

`polars.DataFrame` — ``league``, ``id_system`` (the id system of ``value``: "name", "espn", "cfbd", ...; the "mark", "conference" and "competition" rows serve the mark functions only, ``resolve`` never reads them), ``value`` (the alias as the index stores it; lookups ignore case and accents), ``team_id`` (the ``teams`` row it names), ``valid_from`` and ``valid_to`` (Int32: the first and last season the alias names that team; null for always and still).

## Raises

- `InputError`: (a ValueError) If ``league`` is given and is not a known league key.

## Example

```python
import polars as pl
import sdvplot

a = sdvplot.aliases("cfb").filter(pl.col("id_system") == "name")
# cfbplotR's team_name_mapping: each name -> its school
a.join(sdvplot.teams("cfb").select("team_id", "location"), on="team_id").select("value", "location")
```

## See also

- [sdvplotR sdv_aliases()](https://sdvplotR.sportsdataverse.org/reference/sdv_aliases.html)
- sdvplot.clean_names: one display name per team value

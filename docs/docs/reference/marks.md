---
title: marks
sidebar_label: marks
sidebar_position: 8
---

# `marks`

```python
marks(team: Any, league: str, season: Any = None, *, id_system: str = 'auto') -> polars.dataframe.frame.DataFrame
```

Every archived mark for one team, best first.

Manifest entity ids are per-source, so rows reach a team only through its "mark" aliases; rows without a unique
mapping are dropped, never matched on the raw id. ``valid_from``/``valid_to`` are each row's effective range: the
manifest's, else the mark alias's.

## Arguments

| Name | Type | Description |
|---|---|---|
| `team` | `Any` | One team identifier (abbreviation, name, ESPN id, ...). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | A season year, used to resolve a reused code. |
| `id_system` | `str` | "auto" or one id-system name, as in ``resolve``. |

## Returns

`polars.DataFrame` — One row per archived mark (logos and wordmarks, every variant and source) with its ``variant``, ``mark_type``, ``archive_url`` and ``source_rank``.

## Raises

- `TypeError`: If ``team`` is not a single value.
- `ValueError`: If ``league`` or ``id_system`` is unknown.
- `UnresolvedTeamError`: If the team is null or does not resolve.
- `OfflineError`: If the logo manifest cannot be downloaded and no cached copy exists.

## Example

```python
import sdvplot

sdvplot.marks("KC", "nfl").shape   # (19, 21)
```

## See also

sdvplotR: https://sdvplotR.sportsdataverse.org/ ; sdv-py: https://py.sportsdataverse.org/

---
title: resolve
sidebar_label: resolve
sidebar_position: 1
---

# `resolve`

```python
resolve(values: Any, league: str, season: Any = None, id_system: str = 'auto', strict: bool = False) -> Any
```

Canonical team_id(s) for team values in one league.

Accepts ids and names from any supported source (ESPN, nflverse, MLB Stats, nba_api, HockeyTech, CFBD, sdvplotR) and
returns the bundled index's canonical team_id, in the same container the values came in. Values that do not resolve
come back as None with one SdvplotWarning, or raise with ``strict=True``.

## Arguments

| Name | Type | Description |
|---|---|---|
| `values` | `Any` | A scalar, list/tuple, numpy array, or pandas/polars Series of team identifiers in any supported id system. NHL stats API ids overlap ESPN's, so "auto" never reads a number as one: pass ``id_system="nhl_id"`` for them (NHL tri-codes such as "NJD" resolve under "auto"). |
| `league` | `str` | The SDV league key, e.g. "nfl", "cfb", "ohl". Required: the same abbreviation means different teams in different leagues. |
| `season` | `Any` | One season for all values, or one per value. Picks the right team for a reused code. |
| `id_system` | `str` | "auto" (try the priority order) or one system name. |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a value does not resolve. |

## Returns

str | list | Series | None: The same shape as ``values``: a team_id string (or None), a list, or a Series of the caller's library.

## Raises

- `TypeError`: If ``values`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
- `ValueError`: If ``league`` or ``id_system`` is unknown, or ``season`` is not a year (or a list whose length does not match the teams).
- `UnresolvedTeamError`: If ``strict=True`` and a value does not resolve.

## Example

```python
import sdvplot

sdvplot.resolve("LV", "nfl")                  # '13'
sdvplot.resolve(["KC", "SF"], "nfl")          # ['12', '25']
```

## See also

sdvplotR: https://sdvplotR.sportsdataverse.org/ ; sdv-py: https://py.sportsdataverse.org/

---
title: team_colors
sidebar_label: team_colors
sidebar_position: 5
---

# team_colors

<div class="sdv-signature">

```python
team_colors(
    league: str,
    teams: Any,
    *,
    which: str = 'primary',
    season: Any = None,
) -> Any
```

</div>

One "#hex" (or None) per team value, in the same container the values came in.

## Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `teams` | `Any` | A scalar, list/tuple, numpy array, or pandas/polars Series of team identifiers. |
| `which` | `str` | "primary" or "secondary". |
| `season` | `Any` | One season, or one per team, for values reused across eras. |

## Returns

str | list | Series | None: The hex color for each team, None where a team does not resolve or has no color.

## Raises

- `TypeError`: If ``teams`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
- `ValueError`: If ``league`` is unknown, ``which`` is not "primary"/"secondary", or ``season`` is not a year (or a list whose length does not match the teams).

## Example

```python
import sdvplot

sdvplot.team_colors("nfl", ["KC", "SF"])              # ['#e31837', '#aa0000']
sdvplot.team_colors("nfl", "KC", which="secondary")   # '#ffb612'
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

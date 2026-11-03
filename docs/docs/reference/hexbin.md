---
title: hexbin
sidebar_label: hexbin
sidebar_position: 33
---

# hexbin

<div class="sdv-signature">

```python
hexbin(
    x: collections.abc.Sequence[Any],
    y: collections.abc.Sequence[Any],
    *,
    radius: float,
    ids: collections.abc.Sequence[Any] | None = None,
) -> list[sdvplot._bins.Bin]
```

</div>

Bin points into pointy-top hexagons of circumradius ``radius``, in the points' own units.

The port of sdvplot-js ``hexbin`` (itself d3-hexbin 0.2.2's): the same lattice, centres and bin order. Each point
goes to the centre d3-hexbin picks, which is close to but not exactly the nearest: it compares two candidates in
lattice units, so about 1-2% of points sit just outside the hexagon drawn for their bin (22 of 2000 real Brooklyn
shots at radius 10). That is faithful to d3-hexbin and sdvplot-js; squares contain every point they bin.

## Arguments

| Name | Type | Description |
|---|---|---|
| `x` | `collections.abc.Sequence[Any]` | The points' x values (a list, numpy array, or pandas / polars Series). |
| `y` | `collections.abc.Sequence[Any]` | The points' y values, one per x. |
| `radius` | `float` | The hexagon's circumradius, in the points' units (a finite number > 0). |
| `ids` | `collections.abc.Sequence[Any] \| None` | Optional link ids, one per point (e.g. a shot id column); each becomes a string, as sdvplot-js's ``toId`` (``None``, NaN and ``""`` become ``""``). Default: the row number. |

## Returns

`list[Bin]` — The non-empty cells in first-seen order, each with ``id`` (``"x,y"``, the centre as JavaScript prints it), ``x``, ``y`` (``-0`` folded to ``0``), ``rows`` (the points' 0-based positions), ``ids`` and ``count``. A point with a missing (None), NaN or infinite coordinate is in no bin.

## Raises

- `InputError`: If ``radius`` is not a finite number greater than 0.
- `ValueError`: If ``x``, ``y`` and ``ids`` differ in length, or a coordinate is not a number.

## Example

```python
import sdvplot

# three Brooklyn shots of 2025-26 in tenths of a foot from the hoop (sportsdataverse-data
# nba_stats_shots): the two at the rim share a 1 ft hexagon
bins = sdvplot.hexbin([0, -1, -44], [0, 7, 252], radius=10)
[(b.id, b.count) for b in bins]   # [('0,0', 2), ('-43.301270189221924,255', 1)]
```

## See also

- [binner](https://sdvplot.sportsdataverse.org/docs/reference/binner)
- [sdvplot-js hexbin](https://sdvplot-js.sportsdataverse.org/)

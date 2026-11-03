---
title: squarebin
sidebar_label: squarebin
sidebar_position: 34
---

# squarebin

<div class="sdv-signature">

```python
squarebin(
    x: collections.abc.Sequence[Any],
    y: collections.abc.Sequence[Any],
    *,
    side: float,
    ids: collections.abc.Sequence[Any] | None = None,
) -> list[sdvplot._bins.Bin]
```

</div>

Bin points into axis-aligned squares of side ``side``, in the points' own units.

The port of sdvplot-js ``squarebin``. As in d3-hexbin's lattice a cell is centred on the origin, so centres are
``(i * side, j * side)``. Cells are half-open, ``[c - side/2, c + side/2)`` on each axis: a point exactly on an edge
goes to the higher cell, because the cell index is JavaScript's ``Math.round(x / side)`` (halves round up, also
below zero: -5 with side 10 is in the cell at 0).

## Arguments

| Name | Type | Description |
|---|---|---|
| `x` | `collections.abc.Sequence[Any]` | The points' x values (a list, numpy array, or pandas / polars Series). |
| `y` | `collections.abc.Sequence[Any]` | The points' y values, one per x. |
| `side` | `float` | The square's side, in the points' units (a finite number > 0). |
| `ids` | `collections.abc.Sequence[Any] \| None` | Optional link ids, one per point; as in ``hexbin``. Default: the row number. |

## Returns

`list[Bin]` — The non-empty cells in first-seen order, as ``hexbin`` returns them.

## Raises

- `InputError`: If ``side`` is not a finite number greater than 0.
- `ValueError`: If ``x``, ``y`` and ``ids`` differ in length, or a coordinate is not a number.

## Example

```python
import sdvplot

# x = 5 sits on a cell edge and goes to the higher cell
bins = sdvplot.squarebin([0, -1, 5], [0, 7, 91], side=10)
[(b.x, b.y, b.count) for b in bins]   # [(0.0, 0.0, 1), (0.0, 10.0, 1), (10.0, 90.0, 1)]
```

## See also

- [binner](https://sdvplot.sportsdataverse.org/docs/reference/binner)
- [sdvplot-js squarebin](https://sdvplot-js.sportsdataverse.org/)

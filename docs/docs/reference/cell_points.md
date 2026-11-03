---
title: cell_points
sidebar_label: cell_points
sidebar_position: 35
---

# cell_points

<div class="sdv-signature">

```python
cell_points(
    shape: Literal['hex', 'square'],
    size: float,
) -> list[tuple[float, float]]
```

</div>

A cell's vertices around (0, 0), in the points' units, to outline a bin as a polygon.

A pointy-top hexagon of circumradius ``size`` (d3-hexbin's vertex order, starting at the top in a y-down frame) or a
square of side ``size``, the port of sdvplot-js ``cellPoints``. Add a bin's centre to each vertex.

## Arguments

| Name | Type | Description |
|---|---|---|
| `shape` | `Literal['hex', 'square']` | ``"hex"`` or ``"square"``. |
| `size` | `float` | The hexagon's circumradius or the square's side (a finite number > 0). |

## Returns

`list[tuple[float, float]]` — Six vertices for a hexagon, four for a square.

## Raises

- `InputError`: If ``shape`` is not ``"hex"`` or ``"square"``, or ``size`` is not a finite number > 0.

## Example

```python
import sdvplot

sdvplot.cell_points("square", 10)   # [(-5.0, -5.0), (5.0, -5.0), (5.0, 5.0), (-5.0, 5.0)]
b = sdvplot.hexbin([0, -1, -44], [0, 7, 252], radius=10)[0]
[(b.x + dx, b.y + dy) for dx, dy in sdvplot.cell_points("hex", 10)]
```

## See also

- [binner](https://sdvplot.sportsdataverse.org/docs/reference/binner)

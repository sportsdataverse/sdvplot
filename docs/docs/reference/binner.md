---
title: binner
sidebar_label: binner
sidebar_position: 32
---

# binner

<div class="sdv-signature">

```python
binner(
    *,
    shape: Literal['hex', 'square'] = 'hex',
    radius: float | None = None,
    side: float | None = None,
    equal_area: bool = False,
    origin: tuple[float, float] = (0.0, 0.0),
) -> sdvplot._bins.Binner
```

</div>

One binning API for both lattices, the port of sdvplot-js ``binner``.

``binner(radius=15)`` is d3-hexbin's lattice, ``binner(shape="square", side=15)`` squares, and
``binner(shape="square", radius=15, equal_area=True)`` squares of side ``15 * sqrt(3 * sqrt(3) / 2)`` (about 24.18),
each the area of a radius-15 hexagon, so a hex and a square chart of the same data compare cell for cell.

## Arguments

| Name | Type | Description |
|---|---|---|
| `shape` | `Literal['hex', 'square']` | ``"hex"`` (the default) or ``"square"``. |
| `radius` | `float \| None` | The hexagon's circumradius; with ``shape="square"`` only together with ``equal_area=True``. |
| `side` | `float \| None` | The square's side (``shape="square"`` only). |
| `equal_area` | `bool` | With ``shape="square"`` and ``radius``: squares of the area of that hexagon. |
| `origin` | `tuple[float, float]` | The point a cell centre falls on (default ``(0.0, 0.0)``): a hoop-centred lattice, origin = the basket's coordinates; as in ``hexbin``. |

## Returns

`Binner` — ``shape``, ``size`` (the circumradius, or the side), ``origin``, ``lattice`` (the resolved options: ``{"radius": r}`` or ``{"shape": "square", "side": s}``, plus ``"origin"`` when it is not (0, 0)), ``bins(x, y, *, ids=None, weights=None)`` (as ``hexbin`` / ``squarebin``) and ``cell_points(size=None)``.

## Raises

- `InputError`: If ``shape`` is not ``"hex"`` or ``"square"``, the size is missing or not a finite number > 0, ``origin`` is not two finite numbers, or the options do not name one lattice (a hexagon with ``side``, a square with both ``side`` and ``radius``, or ``radius`` without ``equal_area=True``).

## Example

```python
import sdvplot

b = sdvplot.binner(shape="square", radius=10, equal_area=True)
b.size   # 16.11854897735313: the side of a square with a radius-10 hexagon's area
[(c.id, c.count) for c in b.bins([0, -1, -44], [0, 7, 252])]
```

## See also

- [hexbin](https://sdvplot.sportsdataverse.org/docs/reference/hexbin)
- [squarebin](https://sdvplot.sportsdataverse.org/docs/reference/squarebin)

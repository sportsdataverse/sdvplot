---
title: add_logos
sidebar_label: add_logos
sidebar_position: 10
---

# add_logos

<div class="sdv-signature">

```python
add_logos(target: Any, *args: Any, **kwargs: Any) -> Any
```

</div>

Add team logos to a plot or table of any supported library.

Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. Every
adapter takes the same arguments.

## Arguments

| Name | Description |
|---|---|
| `target` | The plot or table object. Its type picks the adapter. |
| `*args` | Passed to the adapter. By convention ``x``, ``y`` (positions in the target's own coordinates) and ``teams`` (the team values to draw), in that order. |
| `**kwargs` | Passed to the adapter: ``league`` (the SDV league key), ``season`` (one season or one per team), ``height`` (the mark's height as a fraction of the plot height), ``alpha`` (opacity, 0 to 1) and ``variant`` (a mark variant, as in ``logo_url``). |

## Returns

`object` — The drawn-on plot or table: ``target`` itself, or the new object the adapter built.

## Raises

- `UnsupportedTargetError`: If no adapter is registered for ``target``'s library.
- `OptionalDependencyError`: If the adapter's optional extra is not installed.

## Example

```python
import matplotlib.pyplot as plt
import sdvplot

fig, ax = plt.subplots()
ax.set_xlim(0, 30)
ax.set_ylim(-10, 0)
sdvplot.add_logos(ax, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

---
title: add_wordmarks
sidebar_label: add_wordmarks
sidebar_position: 11
---

# add_wordmarks

<div class="sdv-signature">

```python
add_wordmarks(target: Any, *args: Any, **kwargs: Any) -> Any
```

</div>

Add team wordmarks to a plot or table of any supported library.

Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. Plots and
tables take different arguments. A plot (matplotlib, plotnine, Plotly, Altair, Bokeh, HoloViews, folium and pygal)
takes ``x``, ``y`` and ``teams``, and a ``height`` that is a fraction of the plot height. A great_tables ``GT``
takes ``columns`` and a ``height`` in pixels, with no ``alpha`` or ``variant`` (see
``sdvplot.great_tables.gt_sdv_wordmarks``).

## Arguments

| Name | Description |
|---|---|
| `target` | The plot or table object. Its type picks the adapter. |
| `*args` | Passed to the adapter. For a plot: ``x``, ``y`` (positions in the target's own coordinates) and ``teams`` (the team values to draw), in that order. For a table: ``columns`` (the columns whose cells become marks). |
| `**kwargs` | Passed to the adapter: ``league`` (the SDV league key) and ``season`` (one season or one per team). For a plot, also ``height`` (a fraction of the plot height, in (0, 1]), ``alpha`` (opacity, 0 to 1) and ``variant`` (a mark variant, as in ``logo_url``); for a table, ``height`` is in pixels (default 30). |

## Returns

`object` — The drawn-on plot or table: ``target`` itself, or the new object the adapter built.

## Raises

- `UnsupportedTargetError`: If no adapter is registered for ``target``'s library.
- `OptionalDependencyError`: If the adapter's optional extra is not installed.
- `TypeError`: If the adapter does not take an argument given (a table takes no ``x``, ``y``, ``alpha``).
- `ValueError`: If a value is out of range: a plot ``height`` outside (0, 1], or a table ``height`` below 1 pixel (a fraction such as 0.1 is a plot's unit, not a table's).

## Example

```python
import matplotlib.pyplot as plt
import sdvplot

fig, ax = plt.subplots()
sdvplot.add_wordmarks(ax, [0.5], [0.5], ["KC"], league="nfl", height=0.1)
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

---
title: add_bins
sidebar_label: add_bins
sidebar_position: 31
---

# add_bins

<div class="sdv-signature">

```python
add_bins(target: Any, *args: Any, **kwargs: Any) -> Any
```

</div>

Draw hexagonal or square bins, colored by count, on a plot of any library that has a binned form.

Routes to the adapter's ``add_bins``: matplotlib (a ``PolyCollection``), Plotly (path shapes plus a selectable
trace), Bokeh (a ``patches`` glyph, with linked selection) and Altair (an ``area`` layer with a selection param).
Every adapter bins with ``sdvplot.binner``, so the cells, their ids (``"x,y"``, the ``data-sdv-id`` of sdvplot-js)
and the points in each are the same everywhere; each adapter's page says how its cells link to points and tables.

## Arguments

| Name | Description |
|---|---|
| `target` | The plot object. Its type picks the adapter. |
| `*args` | Passed to the adapter: ``x`` and ``y``, the points' coordinates in the plot's data units. |
| `**kwargs` | Passed to the adapter: ``shape`` (``"hex"`` or ``"square"``), ``radius``, ``side``, ``equal_area`` (as ``sdvplot.binner``), and the adapter's own styling and linking options. |

## Returns

`object` — The drawn-on plot: ``target`` itself, or the new chart (Altair).

## Raises

- `UnsupportedTargetError`: (a TypeError) If no adapter is registered for ``target``'s library, or its library has no ``add_bins`` (plotnine, HoloViews, folium, pygal and the table libraries).
- `OptionalDependencyError`: (a ModuleNotFoundError) If the adapter's optional extra is not installed.
- `InputError`: (a ValueError) If the lattice options are not valid (see ``sdvplot.binner``).
- `ValueError`: If ``x`` and ``y`` differ in length.

## Example

```python
import matplotlib.pyplot as plt
import sdvplot

# three Brooklyn shots of 2025-26, legacy tenths of a foot (sportsdataverse-data nba_stats_shots)
fig, ax = plt.subplots()
sdvplot.add_bins(ax, [0, -1, -44], [0, 7, 252], shape="square", side=15, cmap="Blues")
```

## See also

- [sdvplot.binner](https://sdvplot.sportsdataverse.org/docs/reference/binner)
- [sdvplot-js shot charts](https://sdvplot-js.sportsdataverse.org/)

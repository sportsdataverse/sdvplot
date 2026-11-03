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

Draw hexagonal or square bins, colored by count or weight, on a plot of any library that has a binned form.

Routes to the adapter's ``add_bins``: matplotlib (a ``PolyCollection``), plotnine (a ``geom_polygon`` layer),
Plotly (path shapes plus a selectable trace; ``sdvplot.plotly.link_script`` links it in static HTML), Bokeh (a
``patches`` glyph, with linked selection), HoloViews (the Bokeh glyph through a plot hook, linked the same way),
Altair (an ``area`` layer with a selection param), folium (GeoJSON polygons, in degrees of longitude and latitude)
and pygal (SVG polygons). Every adapter bins with ``sdvplot.binner``, so the cells, their ids (``"x,y"``, the
``data-sdv-id`` of sdvplot-js) and the points in each are the same everywhere; each adapter's page says how its
cells link to points and tables.

## Arguments

| Name | Description |
|---|---|
| `target` | The plot object. Its type picks the adapter. |
| `*args` | Passed to the adapter: ``x`` and ``y``, the points' coordinates in the plot's data units. |
| `**kwargs` | Passed to the adapter: ``shape`` (``"hex"`` or ``"square"``), ``radius``, ``side``, ``equal_area``, ``origin`` (as ``sdvplot.binner``: ``origin`` is the point a cell centre falls on, a hoop-centred lattice with origin = the basket's coordinates), ``weights`` (one per point, each bin's ``weight``), ``value`` (``"count"`` or ``"weight"``, what the fill encodes), ``fill`` (the drawn cell's size as a fraction of the lattice cell: 0.88 for squares, 1.0 for hexagons by default), ``min_count`` (cells with fewer points are not drawn; ``min_count=2`` drops single attempts from a shot chart), and the adapter's own styling and linking options. |

## Returns

`object` — The drawn-on plot: ``target`` itself, or the new chart (Altair, plotnine, HoloViews).

## Raises

- `UnsupportedTargetError`: (a TypeError) If no adapter is registered for ``target``'s library, or its library has no ``add_bins`` (the table libraries).
- `OptionalDependencyError`: (a ModuleNotFoundError) If the adapter's optional extra is not installed.
- `InputError`: (a ValueError) If the lattice options are not valid (see ``sdvplot.binner``), or ``value``, ``fill`` or ``min_count`` is not one ``add_bins`` takes.
- `ValueError`: If ``x``, ``y`` and ``weights`` differ in length, or a weight is negative.

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

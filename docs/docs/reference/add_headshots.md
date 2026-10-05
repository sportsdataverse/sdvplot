---
title: add_headshots
sidebar_label: add_headshots
sidebar_position: 12
---

# add_headshots

<div class="sdv-signature">

```python
add_headshots(target: Any, *args: Any, **kwargs: Any) -> Any
```

</div>

Add player headshots to a plot or table of any supported library.

Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. For
headshots, ``teams`` holds player ids and ``league`` picks the ESPN league. Plots and tables take different
arguments. A plot (matplotlib, plotnine, Plotly, Altair, Bokeh, HoloViews, folium and pygal) takes ``x``, ``y`` and
``teams``, and a ``height`` that is a fraction of the plot height. A great_tables ``GT`` takes ``columns`` and a
``height`` in pixels, with no ``alpha`` (see ``sdvplot.great_tables.gt_sdv_headshots``).

## Arguments

| Name | Description |
|---|---|
| `target` | The plot or table object. Its type picks the adapter. |
| `*args` | Passed to the adapter. For a plot: ``x``, ``y`` (positions in the target's own coordinates) and ``teams`` (the player ids to draw), in that order. For a table: ``columns`` (the columns whose cells become headshots). |
| `**kwargs` | Passed to the adapter: ``league`` (the SDV league key) and ``id_system`` (``"espn"`` or ``"gsis"``, as in ``headshot_url``). For a plot, also ``height`` (a fraction of the plot height, in (0, 1]) and ``alpha`` (opacity, 0 to 1); for a table, ``height`` is in pixels (default 30). Headshots take no ``season`` or ``variant``. |

## Returns

`object` — The drawn-on plot or table: ``target`` itself, or the new object the adapter built.

## Raises

- `UnsupportedTargetError`: (a TypeError) If no adapter is registered for ``target``'s library, or the adapter cannot draw on this kind of ``target`` (a pygal Bar chart, a folium FeatureGroup).
- `OptionalDependencyError`: (a ModuleNotFoundError) If the adapter's optional extra is not installed, or a mark a raster adapter draws is an SVG and the ``svg`` extra is not installed.
- `TypeError`: If the adapter does not take an argument given (a table takes no ``x``, ``y``, ``alpha``).
- `InputError`: (a ValueError) If a value is out of range: a plot ``height`` outside (0, 1] or ``alpha`` outside [0, 1], or a table ``height`` below 1 pixel (a fraction such as 0.1 is a plot's unit, not a table's); or ``league`` has no ESPN headshots or ``id_system`` is not valid for it.
- `ValueError`: If the adapter's own checks fail (inputs of different lengths, an axis it cannot place on); its page lists them.
- `OfflineError`: If a download the adapter needs (the logo manifest, a mark's image, a headshot) fails and no cached copy exists: a DownloadError (also an OSError) for an HTTP error status, an IntegrityError for a file that does not match the manifest's sha256. Which downloads an adapter makes is on its page.
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.

## Example

```python
import matplotlib.pyplot as plt
import sdvplot

fig, ax = plt.subplots()
sdvplot.add_headshots(ax, [0.5], [0.5], ["3139477"], league="nfl", height=0.2)
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

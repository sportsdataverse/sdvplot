---
title: axis_logos
sidebar_label: axis_logos
sidebar_position: 13
---

# axis_logos

<div class="sdv-signature">

```python
axis_logos(target: Any, *args: Any, **kwargs: Any) -> Any
```

</div>

Replace an axis' team labels with team logos (or a player axis' with headshots) on any supported library.

Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. The
adapters that draw axis logos (matplotlib, plotnine, Plotly and Altair) all take ``axis_logos(target, axis, *,
league, season=None, height=0.1, variant="default", mark_type="logo", id_system="auto")``, and Plotly and Altair
also take ``embed``. Bokeh, HoloViews, folium, pygal and great_tables have no axis logos: there it raises
UnsupportedTargetError (a TypeError).

## Arguments

| Name | Description |
|---|---|
| `target` | The plot object. Its type picks the adapter. |
| `*args` | Passed to the adapter: ``axis`` (which axis' tick labels to replace, ``"x"`` or ``"y"``). |
| `**kwargs` | Passed to the adapter: ``league`` (the SDV league key, required), ``season`` (one season for every label, default ``None``), ``height`` (the mark's height as a fraction of the plot height, default 0.1), and ``variant``, ``mark_type`` and ``id_system`` as in ``logo_url`` and ``resolve``. ``mark_type="headshot"`` reads the labels as player ids (``id_system`` "espn", "gsis" or "league" as in ``headshot_url``; "auto" means "espn") and draws their headshots at their own aspect, as sdvplotR's ``scale_*_sdv_headshots()``. |

## Returns

`object` — The drawn-on plot: ``target`` itself, or the new object the adapter built.

## Raises

- `UnsupportedTargetError`: (a TypeError) If no adapter is registered for ``target``'s library, its library has no axis logos (Bokeh, HoloViews, folium, pygal, great_tables), or the adapter cannot draw on this kind of ``target``.
- `OptionalDependencyError`: (a ModuleNotFoundError) If the adapter's optional extra is not installed, or a mark a raster adapter draws is an SVG and the ``svg`` extra is not installed.
- `InputError`: (a ValueError) If ``height`` is outside (0, 1], or ``league``, ``id_system``, ``mark_type``, ``variant`` or ``season`` is not one sdvplot knows.
- `ValueError`: If ``axis`` is not "x"/"y", or the axis is not one the adapter can read team labels from (its page lists the cases).
- `OfflineError`: If a download the adapter needs (the logo manifest, a mark's image) fails and no cached copy exists: a DownloadError (also an OSError) for an HTTP error status, an IntegrityError for a file that does not match the manifest's sha256. Which downloads an adapter makes is on its page.
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.

## Example

```python
import matplotlib.pyplot as plt
import sdvplot

fig, ax = plt.subplots()
ax.bar(["KC", "BUF", "BAL"], [12, 10, 9])
sdvplot.axis_logos(ax, "x", league="nfl", height=0.08)
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

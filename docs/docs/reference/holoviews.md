---
title: sdvplot.holoviews
sidebar_label: sdvplot.holoviews
sidebar_position: 21
---

# sdvplot.holoviews

The HoloViews adapter: a Bokeh plot hook that draws the marks through the Bokeh adapter when the element renders.

| Name | What it is |
|---|---|
| [add_logos](#add_logos) | Draw each team's logo centred on its (x, y) point of a HoloViews element (Bokeh backend). |
| [add_wordmarks](#add_wordmarks) | Draw each team's wordmark centred on its (x, y) point of a HoloViews element (Bokeh backend). |
| [add_headshots](#add_headshots) | Draw each player's headshot centred on its (x, y) point of a HoloViews element (Bokeh backend). |
| [axis_logos](#axis_logos) | Not supported on HoloViews (it draws through Bokeh, which has no axis logos yet). |

## add_logos

<div class="sdv-signature">

```python
add_logos(
    element: Any,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = 'default',
    embed: bool = False,
    id_system: str = 'auto',
) -> Any
```

</div>

Draw each team's logo centred on its (x, y) point of a HoloViews element (Bokeh backend).

Returns a copy of the element with a Bokeh plot hook; the logos appear when it renders (``hv.render``, a notebook,
``hv.save``). Sizing is the Bokeh adapter's: a fraction of the plot's ``frame_height`` when set, else its height;
a responsive plot has neither, so give it a ``frame_height`` (without one, HoloViews logs the hook's ValueError and
draws no marks).

### Arguments

| Name | Type | Description |
|---|---|---|
| `element` | `Any` | A HoloViews element or overlay (``hv.Scatter``, ``hv.Points * hv.Curve``, ...). |
| `x` | `Any` | The points' x positions, in the element's x values. |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point, to pick each team's mark for that era. |
| `height` | `float` | The logo height as a fraction of the plot's reference height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`object` — A copy of ``element`` with the drawing hook added to its existing hooks.

### Raises

- `ValueError`: If ``height`` or ``alpha`` is out of range, or the inputs differ in length.
- `TypeError`: If ``element`` is not a HoloViews object, or the current backend is not Bokeh.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

### Example

```python
import holoviews as hv
import sdvplot

hv.extension("bokeh")
points = hv.Scatter([(10, -3), (20, -7)]).opts(frame_height=300)
points = sdvplot.add_logos(points, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)
```

### See also

- [sdvplotR geom_nfl_logos()](https://sdvplotR.sportsdataverse.org/)
- [HoloViews plot hooks](https://holoviews.org/user_guide/Customizing_Plots.html)

## add_wordmarks

<div class="sdv-signature">

```python
add_wordmarks(
    element: Any,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = 'default',
    embed: bool = False,
    id_system: str = 'auto',
) -> Any
```

</div>

Draw each team's wordmark centred on its (x, y) point of a HoloViews element (Bokeh backend).

### Arguments

| Name | Type | Description |
|---|---|---|
| `element` | `Any` | A HoloViews element or overlay. |
| `x` | `Any` | The points' x positions, in the element's x values. |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point. |
| `height` | `float` | The wordmark height as a fraction of the plot's reference height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`object` — A copy of ``element`` with the drawing hook added.

### Raises

- `ValueError`: If ``height`` or ``alpha`` is out of range, or the inputs differ in length.
- `TypeError`: If ``element`` is not a HoloViews object, or the current backend is not Bokeh.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

### Example

```python
import holoviews as hv
import sdvplot

hv.extension("bokeh")
bars = hv.Bars([("KC", 12), ("BUF", 10)])
bars = sdvplot.add_wordmarks(bars, ["KC", "BUF"], [12, 10], ["KC", "BUF"], league="nfl", height=0.06)
```

### See also

- [sdvplotR geom_nfl_wordmarks()](https://sdvplotR.sportsdataverse.org/)

## add_headshots

<div class="sdv-signature">

```python
add_headshots(
    element: Any,
    x: Any,
    y: Any,
    players: Any,
    *,
    league: str,
    height: float = 0.1,
    alpha: float = 1,
    embed: bool = False,
    id_system: str = 'espn',
) -> Any
```

</div>

Draw each player's headshot centred on its (x, y) point of a HoloViews element (Bokeh backend).

### Arguments

| Name | Type | Description |
|---|---|---|
| `element` | `Any` | A HoloViews element or overlay. |
| `x` | `Any` | The points' x positions, in the element's x values. |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `players` | `Any` | The player id for each point. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `float` | The headshot height as a fraction of the plot's reference height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``. |

### Returns

`object` — A copy of ``element`` with the drawing hook added.

### Raises

- `ValueError`: If ``height`` or ``alpha`` is out of range, or the inputs differ in length.
- `TypeError`: If ``element`` is not a HoloViews object, or the current backend is not Bokeh.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

### Example

```python
import holoviews as hv
import sdvplot

hv.extension("bokeh")
sdvplot.add_headshots(hv.Scatter([(0.5, 0.5)]), [0.5], [0.5], ["3139477"], league="nfl", height=0.2)
```

### See also

- [sdvplotR geom_nfl_headshots()](https://sdvplotR.sportsdataverse.org/)

## axis_logos

<div class="sdv-signature">

```python
axis_logos(target: Any, axis: str, **kwargs: Any) -> Any
```

</div>

Not supported on HoloViews (it draws through Bokeh, which has no axis logos yet).

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A HoloViews element. |
| `axis` | `str` | "x" or "y". |
| `**kwargs` | `Any` | Ignored. |

### Returns

`object` — Never returns.

### Raises

- `TypeError`: Always. Draw the logos inside the plot with ``add_logos``, or use the matplotlib, Plotly or Altair adapter for axis logos.

### Example

```python
import holoviews as hv
import sdvplot

try:
    sdvplot.axis_logos(hv.Bars([("KC", 12)]), "x", league="nfl")
except TypeError:
    pass   # raised: HoloViews has no axis logos yet
```

### See also

- [sdvplotR element_sdv_logo()](https://sdvplotR.sportsdataverse.org/)

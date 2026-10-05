---
title: sdvplot.plotly
sidebar_label: sdvplot.plotly
sidebar_position: 18
---

# sdvplot.plotly

The Plotly adapter: logos, wordmarks, headshots and axis logos as layout images on a Plotly Figure.

| Name | What it is |
|---|---|
| [add_headshots](#add_headshots) | Draw each player's headshot centred on its (x, y) point of a Plotly figure. |
| [add_logos](#add_logos) | Draw each team's logo centred on its (x, y) point of a Plotly figure, as layout images. |
| [add_wordmarks](#add_wordmarks) | Draw each team's wordmark centred on its (x, y) point of a Plotly figure. |
| [axis_logos](#axis_logos) | Replace a category axis' team labels with the teams' logos (or wordmarks). |

## add_headshots

<div class="sdv-signature">

```python
add_headshots(
    target: Any,
    x: Any,
    y: Any,
    players: Any,
    *,
    league: str,
    height: float = 0.1,
    alpha: float = 1,
    xref: str = 'x',
    yref: str = 'y',
    layer: str = 'above',
    embed: bool = False,
    id_system: str = 'espn',
) -> Any
```

</div>

Draw each player's headshot centred on its (x, y) point of a Plotly figure.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``plotly.graph_objects.Figure``. |
| `x` | `Any` | The points' x positions in the axis' own values. |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `players` | `Any` | The player id for each point. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `float` | The headshot height as a fraction of the plot area's height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `xref` | `str` | The x axis to place on. |
| `yref` | `str` | The y axis to place on. |
| `layer` | `str` | "above" or "below" the traces. |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``. |

### Returns

`object` — ``target`` itself, with the images added.

### Raises

- `ValueError`: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or an axis is not supported (see ``add_logos``).
- `TypeError`: If the target is not a Plotly ``Figure``.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

### Example

```python
import plotly.graph_objects as go
import sdvplot

fig = go.Figure(go.Scatter(x=[0.3, 0.7], y=[0.5, 0.5], mode="markers"))
sdvplot.add_headshots(fig, [0.3], [0.5], ["3139477"], league="nfl", height=0.2)
```

### See also

- [sdvplotR geom_nfl_headshots()](https://sdvplotR.sportsdataverse.org/)

## add_logos

<div class="sdv-signature">

```python
add_logos(
    target: Any,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = 'default',
    xref: str = 'x',
    yref: str = 'y',
    layer: str = 'above',
    embed: bool = False,
    id_system: str = 'auto',
) -> Any
```

</div>

Draw each team's logo centred on its (x, y) point of a Plotly figure, as layout images.

Call it after adding the traces: an axis range that is not set is worked out from the scatter and bar traces
(stacked bars included) and the new points, with half a logo of room at each end (Plotly clips images at the plot
edge), and pinned, because a data-placed image is sized in axis units. The logos then zoom with the data. Linear
and category axes are supported (a category is placed at its index).

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``plotly.graph_objects.Figure`` (or ``FigureWidget``). |
| `x` | `Any` | The points' x positions in the axis' own values (numbers, or category names). |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point, to pick each team's mark for that era. |
| `height` | `float` | The logo height as a fraction of the plot area's height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `xref` | `str` | The x axis to place on ("x", "x2", ...), for subplots. |
| `yref` | `str` | The y axis to place on ("y", "y2", ...). |
| `layer` | `str` | "above" or "below" the traces. |
| `embed` | `bool` | Inline each image as a data URI (HTML that renders offline, and static export with kaleido) instead of linking its URL. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`object` — ``target`` itself, with the images added (like Plotly's own ``add_*`` methods).

### Raises

- `ValueError`: If ``height`` or ``alpha`` is out of range, the inputs differ in length, an axis is a log or date axis, or the range must be worked out from a trace type other than scatter or bar, stacked scatter traces (``stackgroup``), or bars with a ``base``, ``barnorm`` or stacked ``offsetgroup`` (set the range first).
- `TypeError`: If the target is not a Plotly ``Figure``.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

### Example

```python
import plotly.graph_objects as go
import sdvplot

fig = go.Figure(go.Scatter(x=[10, 20], y=[-3, -7], mode="markers"))
sdvplot.add_logos(fig, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)
```

### See also

- [sdvplotR geom_nfl_logos()](https://sdvplotR.sportsdataverse.org/)
- [Plotly layout images](https://plotly.com/python/images/)

## add_wordmarks

<div class="sdv-signature">

```python
add_wordmarks(
    target: Any,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = 'default',
    xref: str = 'x',
    yref: str = 'y',
    layer: str = 'above',
    embed: bool = False,
    id_system: str = 'auto',
) -> Any
```

</div>

Draw each team's wordmark centred on its (x, y) point of a Plotly figure.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``plotly.graph_objects.Figure``. |
| `x` | `Any` | The points' x positions in the axis' own values. |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point. |
| `height` | `float` | The wordmark height as a fraction of the plot area's height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `xref` | `str` | The x axis to place on. |
| `yref` | `str` | The y axis to place on. |
| `layer` | `str` | "above" or "below" the traces. |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`object` — ``target`` itself, with the images added.

### Raises

- `ValueError`: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or an axis is not supported (see ``add_logos``).
- `TypeError`: If the target is not a Plotly ``Figure``.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

### Example

```python
import plotly.graph_objects as go
import sdvplot

fig = go.Figure(go.Bar(x=["KC", "BUF"], y=[12, 10]))
sdvplot.add_wordmarks(fig, ["KC", "BUF"], [12, 10], ["KC", "BUF"], league="nfl", height=0.08)
```

### See also

- [sdvplotR geom_nfl_wordmarks()](https://sdvplotR.sportsdataverse.org/)

## axis_logos

<div class="sdv-signature">

```python
axis_logos(
    target: Any,
    axis: str,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    variant: str = 'default',
    mark_type: str = 'logo',
    embed: bool = False,
    id_system: str = 'auto',
) -> Any
```

</div>

Replace a category axis' team labels with the teams' logos (or wordmarks).

The images sit in paper coordinates just outside the plot (under the x axis, left of the y axis), ``height`` of
the plot area tall; labels that are not teams stay as text, with one SdvplotWarning. The bottom (left) margin grows
to make room. Call it after adding the traces, so the axis has its categories.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``plotly.graph_objects.Figure`` whose ``axis`` is a category axis. |
| `axis` | `str` | "x" or "y" (the first x or y axis). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season for every label. |
| `height` | `float` | The image height as a fraction of the plot area's height, in (0, 1]. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `mark_type` | `str` | "logo" or "wordmark". |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | The id system of the labels; "auto" tries each in order. |

### Returns

`object` — ``target`` itself, with the images added and the resolved labels blanked.

### Raises

- `ValueError`: If ``axis`` is not "x"/"y", ``height`` is out of range, or the axis is not a category axis.
- `TypeError`: If the target is not a Plotly ``Figure``.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

### Example

```python
import plotly.graph_objects as go
import sdvplot

fig = go.Figure(go.Bar(x=["KC", "BUF", "BAL"], y=[12, 10, 9]))
sdvplot.axis_logos(fig, "x", league="nfl", height=0.1)
```

### See also

- [sdvplotR element_sdv_logo()](https://sdvplotR.sportsdataverse.org/)

---
title: sdvplot.plotly
sidebar_label: sdvplot.plotly
sidebar_position: 19
---

# sdvplot.plotly

The Plotly adapter: logos, wordmarks, headshots and axis logos as layout images on a Plotly Figure.

| Name | What it is |
|---|---|
| [add_bins](#add_bins) | Draw hexagonal or square bins, colored by count or weight, on a Plotly Figure. |
| [add_headshots](#add_headshots) | Draw each player's headshot centred on its (x, y) point of a Plotly figure. |
| [add_logos](#add_logos) | Draw each team's logo centred on its (x, y) point of a Plotly figure, as layout images. |
| [add_wordmarks](#add_wordmarks) | Draw each team's wordmark centred on its (x, y) point of a Plotly figure. |
| [axis_logos](#axis_logos) | Replace a category axis' team labels with the teams' logos (or wordmarks), or a player axis' with headshots. |
| [link_script](#link_script) | The JavaScript that links ``add_bins``' cells to a points trace in a static HTML file, with no Python running. |

## add_bins

<div class="sdv-signature">

```python
add_bins(
    target: Any,
    x: Any,
    y: Any,
    *,
    shape: Literal['hex', 'square'] = 'hex',
    radius: float | None = None,
    side: float | None = None,
    equal_area: bool = False,
    ids: Any = None,
    weights: Any = None,
    origin: tuple[float, float] = (0.0, 0.0),
    value: Literal['count', 'weight'] = 'count',
    fill: float | None = None,
    min_count: int = 1,
    colorscale: Any = 'Viridis',
    opacity: float = 1.0,
    xref: str = 'x',
    yref: str = 'y',
) -> Any
```

</div>

Draw hexagonal or square bins, colored by count or weight, on a Plotly Figure.

The cells are ``sdvplot.binner``'s, in data units: one ``path`` layout shape per cell (``layer="below"``, so
traces draw over it), filled from ``colorscale`` by ``value`` (count or weight). One scatter trace named
``"sdvplot_bins"`` holds a marker at each centre (invisible until selected) that carries the cell for interaction:
``ids`` are the bin ids (``"x,y"``, as sdvplot-js stamps ``data-sdv-id``), ``customdata`` each cell's point ids,
the marker colors the values (and draw the colorbar), and hovering a cell shows its count and weight.

Linking: in a static HTML file, pass ``sdvplot.plotly.link_script(fig)`` to ``fig.write_html(post_script=...)``
(or ``to_html``): plotly.js handlers then link cell and point selections and hover in the browser, with no Python.
In a ``FigureWidget`` (or Dash) the link is a callback instead: selecting cells gives ``points.point_inds``; the
``customdata`` of those markers are the point ids (the row numbers when no ``ids`` were given), which set a points
trace's ``selectedpoints``. The other way, set the bins trace's ``selectedpoints`` to the cells whose ``customdata``
holds a selected point. ``sdvplot.bin_ids`` gives a table the same key.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``plotly.graph_objects.Figure`` (or ``FigureWidget``). |
| `x` | `Any` | The points' x values, in the axes' data units. |
| `y` | `Any` | The points' y values. |
| `shape` | `Literal['hex', 'square']` | ``"hex"`` (the default) or ``"square"``. |
| `radius` | `float \| None` | The hexagon's circumradius, in data units; for squares, with ``equal_area=True``. |
| `side` | `float \| None` | The square's side (``shape="square"``). |
| `equal_area` | `bool` | Squares of a radius-``radius`` hexagon's area. |
| `ids` | `Any` | Optional link ids, one per point (default the row number); see ``sdvplot.hexbin``. |
| `weights` | `Any` | Optional non-negative weights, one per point (see ``sdvplot.hexbin``): each bin's ``weight``. |
| `origin` | `tuple[float, float]` | The point a cell centre falls on (default ``(0.0, 0.0)``): a hoop-centred lattice, origin = the basket's coordinates. |
| `value` | `Literal['count', 'weight']` | What the fill encodes: ``"count"`` (the default, the points in each cell) or ``"weight"`` (the sum of their ``weights``). |
| `fill` | `float \| None` | The drawn cell's size as a fraction of the lattice cell, in (0, 1]: default 0.88 for squares (a gap, so they do not touch edge to edge) and 1.0 for hexagons (the tiled hexbin look). |
| `min_count` | `int` | Cells with fewer points are not drawn (default 1, every cell). ``min_count=2`` suits shot charts: single attempts are not drawn. ``sdvplot.hexbin`` / ``squarebin`` still return every cell. |
| `colorscale` | `Any` | A Plotly colorscale name or list (default ``"Viridis"``), mapped from the fewest to the most points. |
| `opacity` | `float` | The cells' opacity, 0 to 1. |
| `xref` | `str` | The x axis to draw on ("x", "x2", ...), for subplots: the shapes' ``xref`` and the trace's ``xaxis``. |
| `yref` | `str` | The y axis to draw on ("y", "y2", ...). |

### Returns

`Figure` — ``target``, with the shapes and the trace added.

### Raises

- `InputError`: If the lattice options are not valid (see ``sdvplot.binner``), ``value`` is not "count" or "weight", ``fill`` is not in (0, 1], ``min_count`` is not a whole number >= 1, or ``opacity`` is outside [0, 1].
- `UnsupportedTargetError`: If ``target`` is not a Plotly Figure.
- `ValueError`: If ``x``, ``y`` and ``ids`` differ in length, or ``xref``/``yref`` does not name an x/y axis.

### Example

```python
import plotly.graph_objects as go
from sdvplot.plotly import add_bins

# three Brooklyn shots of 2025-26, legacy tenths of a foot (sportsdataverse-data nba_stats_shots)
x, y = [0, -1, -44], [0, 7, 252]
fig = go.Figure(go.Scatter(x=x, y=y, mode="markers", name="shots"))
add_bins(fig, x, y, shape="square", side=15, colorscale="Blues")
```

### See also

- [sdvplot.binner](https://sdvplot.sportsdataverse.org/docs/reference/binner)
- [Plotly FigureWidget selection](https://plotly.com/python/click-events/)

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
| `id_system` | `str` | "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``. |

### Returns

`object` — ``target`` itself, with the images added.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league`` has no ESPN headshots, or ``id_system`` is not valid for ``league``.
- `ValueError`: If the inputs differ in length, or an axis is not supported (see ``add_logos``).
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a Plotly ``Figure``.
- `OfflineError`: If the nflverse player table (``id_system="gsis"``), or with ``embed=True`` a headshot, is neither cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.

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

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If the inputs differ in length, ``xref``/``yref`` does not name an x/y axis, an axis is a log or date axis, or the range must be worked out from a trace type other than scatter or bar, stacked scatter traces (``stackgroup``), or bars with a ``base``, ``barnorm`` or stacked ``offsetgroup`` (set the range first).
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a Plotly ``Figure``.
- `OfflineError`: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would put the file outside the cache directory.

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

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If the inputs differ in length, or an axis is not supported (see ``add_logos``).
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a Plotly ``Figure``.
- `OfflineError`: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would put the file outside the cache directory.

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
    mark_type: Literal['logo', 'wordmark', 'headshot'] = 'logo',
    embed: bool = False,
    id_system: str = 'auto',
) -> Any
```

</div>

Replace a category axis' team labels with the teams' logos (or wordmarks), or a player axis' with headshots.

The images sit in paper coordinates just outside the plot (under the x axis, left of the y axis), ``height`` of
the plot area tall; labels that are not teams stay as text, with one SdvplotWarning. The bottom (left) margin grows
to make room. Call it after adding the traces, so the axis has its categories.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``plotly.graph_objects.Figure`` whose ``axis`` is a category axis. Player ids look numeric to Plotly (and to this inference): for a headshot axis give the axis ``type="category"``. |
| `axis` | `str` | "x" or "y" (the first x or y axis). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season for every label. |
| `height` | `float` | The image height as a fraction of the plot area's height, in (0, 1]. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `mark_type` | `Literal['logo', 'wordmark', 'headshot']` | "logo", "wordmark" or "headshot". With "headshot" the labels are player ids (``id_system`` "espn", "gsis" or "league" as in ``headshot_url``, "auto" meaning "espn"; ``season`` is ignored), drawn at their own aspect. |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | The id system of the labels; "auto" tries each in order. |

### Returns

`object` — ``target`` itself, with the images added and the resolved labels blanked.

### Raises

- `InputError`: (a ValueError) If ``height`` is out of range, ``league``, ``id_system``, ``mark_type`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If ``axis`` is not "x"/"y", or the axis is not a category axis.
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a Plotly ``Figure``.
- `OfflineError`: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would put the file outside the cache directory.

### Example

```python
import plotly.graph_objects as go
import sdvplot

fig = go.Figure(go.Bar(x=["KC", "BUF", "BAL"], y=[12, 10, 9]))
sdvplot.axis_logos(fig, "x", league="nfl", height=0.1)
```

### See also

- [sdvplotR element_sdv_logo()](https://sdvplotR.sportsdataverse.org/)

## link_script

<div class="sdv-signature">

```python
link_script(
    target: Any,
    *,
    points: int = 0,
    bins: int | None = None,
) -> str
```

</div>

The JavaScript that links ``add_bins``' cells to a points trace in a static HTML file, with no Python running.

Pass it to ``fig.write_html(post_script=...)`` or ``fig.to_html(post_script=...)``: Plotly runs it after the plot
is drawn (its ``{plot_id}`` placeholder becomes the div's id). It registers plotly.js handlers on the div:
selecting cells (box or lasso select) selects their points on the points trace, selecting points selects the cells
holding them, double-click deselects both, and hovering a cell highlights its points until the pointer leaves. A
point belongs to a cell when its link id is among the cell's ``customdata``: the points trace's own ``customdata``
(its first element when each is a list) as a string, as ``sdvplot.hexbin`` writes ids, else its row number, which
is ``add_bins``' default id. The figure is read once, now: call it after the traces are final.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``plotly.graph_objects.Figure`` that ``add_bins`` drew on. |
| `points` | `int` | The index of the points trace in ``fig.data`` (default 0, the first trace). |
| `bins` | `int \| None` | The index of the bins trace (default the last trace named ``"sdvplot_bins"``). |

### Returns

`str` — The script, for ``post_script``.

### Raises

- `UnsupportedTargetError`: If ``target`` is not a Plotly Figure.
- `ValueError`: If the figure has no ``add_bins`` trace, ``bins`` is not one, or ``points`` is not the index of another trace.

### Example

```python
import plotly.graph_objects as go
from sdvplot.plotly import add_bins, link_script

# three Brooklyn shots of 2025-26, legacy tenths of a foot (sportsdataverse-data nba_stats_shots)
x, y = [0, -1, -44], [0, 7, 252]
fig = go.Figure(go.Scatter(x=x, y=y, mode="markers", name="shots"))
add_bins(fig, x, y, radius=15)
fig.update_layout(dragmode="select")
html = fig.to_html(post_script=link_script(fig))  # or fig.write_html("shots.html", post_script=...)
```

### See also

- [sdvplot.plotly.add_bins](https://sdvplot.sportsdataverse.org/docs/reference/plotly)
- [Plotly post_script](https://plotly.com/python-api-reference/generated/plotly.io.to_html.html)

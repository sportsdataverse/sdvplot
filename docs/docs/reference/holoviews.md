---
title: sdvplot.holoviews
sidebar_label: sdvplot.holoviews
sidebar_position: 22
---

# sdvplot.holoviews

The HoloViews adapter: a Bokeh plot hook that draws the marks through the Bokeh adapter when the element renders.

| Name | What it is |
|---|---|
| [add_bins](#add_bins) | Hexagonal or square bins, colored by count or weight, on a HoloViews element: the Bokeh adapter's ``add_bins``. |
| [add_headshots](#add_headshots) | Draw each player's headshot centred on its (x, y) point of a HoloViews element (Bokeh backend). |
| [add_logos](#add_logos) | Draw each team's logo centred on its (x, y) point of a HoloViews element (Bokeh backend). |
| [add_wordmarks](#add_wordmarks) | Draw each team's wordmark centred on its (x, y) point of a HoloViews element (Bokeh backend). |
| [axis_logos](#axis_logos) | Not supported on HoloViews (it draws through Bokeh, which has no axis logos yet). |

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
    palette: Any = 'Viridis256',
    alpha: float = 1.0,
    link: Any = None,
) -> Any
```

</div>

Hexagonal or square bins, colored by count or weight, on a HoloViews element: the Bokeh adapter's ``add_bins``.

A Bokeh plot hook draws the cells with ``sdvplot.bokeh.add_bins`` when the element renders (one ``patches`` glyph
named ``"sdvplot_bins"``, with its ``ColumnDataSource`` of ``bin_id``, ``count``, ``weight``, ``point_ids`` and
``rows``), so the cells, ids and colors are the Bokeh adapter's. Only the Bokeh backend is supported.

Linking: as Bokeh's, in the browser with no server. Pass the points element of the plot (e.g. the ``hv.Points`` in
``target``, or ``target`` itself) as ``link``: its rendered ``ColumnDataSource`` is linked both ways, so selecting
cells (add ``tools=["tap", "box_select"]``) selects their points and selecting points selects their cells. Its rows
must be the points of ``x`` and ``y``, in that order.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A HoloViews element or overlay. |
| `x` | `Any` | The points' x values, in data units. |
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
| `palette` | `Any` | A Bokeh palette name or list of colors (default ``"Viridis256"``), lowest to highest value. |
| `alpha` | `float` | The cells' fill opacity, 0 to 1. |
| `link` | `Any` | Optional points element of ``target`` (or ``target`` itself) to link selections with. |

### Returns

`element` — A clone of ``target`` with the hook added.

### Raises

- `InputError`: If the lattice options are not valid (see ``sdvplot.binner``), ``value`` is not "count" or "weight", ``fill`` is not in (0, 1], ``min_count`` is not a whole number >= 1, or ``alpha`` is outside [0, 1].
- `UnsupportedTargetError`: If ``target`` is not a HoloViews element or overlay.
- `TypeError`: If the current HoloViews backend is not Bokeh.
- `ValueError`: If ``x``, ``y``, ``ids`` and ``weights`` differ in length, or ``link`` is not an element of ``target``.

### Example

```python
import holoviews as hv
from sdvplot.holoviews import add_bins

hv.extension("bokeh")
# three Brooklyn shots of 2025-26, legacy tenths of a foot (sportsdataverse-data nba_stats_shots)
x, y = [0, -1, -44], [0, 7, 252]
shots = hv.Points({"x": x, "y": y}, ["x", "y"]).opts(tools=["tap", "box_select"])
plot = add_bins(shots, x, y, shape="square", side=15, alpha=0.6, link=shots)
```

### See also

- [sdvplot.bokeh.add_bins](https://sdvplot.sportsdataverse.org/docs/reference/bokeh)
- [HoloViews hooks](https://holoviews.org/user_guide/Customizing_Plots.html)

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
| `id_system` | `str` | "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``. |

### Returns

`object` — A copy of ``element`` with the drawing hook added.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league`` has no ESPN headshots, or ``id_system`` is not valid for ``league``.
- `ValueError`: If the inputs differ in length; when the plot renders, if its figure has no pixel height (no ``frame_height`` or ``height`` option).
- `TypeError`: If the current HoloViews backend is not Bokeh.
- `UnsupportedTargetError`: (a TypeError) If ``element`` is not a HoloViews element or overlay.
- `OfflineError`: If the nflverse player table (``id_system="gsis"``), or with ``embed=True`` a headshot, is neither cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
import holoviews as hv
import sdvplot

hv.extension("bokeh")
sdvplot.add_headshots(hv.Scatter([(0.5, 0.5)]), [0.5], [0.5], ["3139477"], league="nfl", height=0.2)
```

### See also

- [sdvplotR geom_nfl_headshots()](https://sdvplotR.sportsdataverse.org/)

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

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If the inputs differ in length; when the plot renders, if its figure has no pixel height (no ``frame_height`` or ``height`` option).
- `TypeError`: If the current HoloViews backend is not Bokeh.
- `UnsupportedTargetError`: (a TypeError) If ``element`` is not a HoloViews element or overlay.
- `OfflineError`: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would put the file outside the cache directory.

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

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If the inputs differ in length; when the plot renders, if its figure has no pixel height (no ``frame_height`` or ``height`` option).
- `TypeError`: If the current HoloViews backend is not Bokeh.
- `UnsupportedTargetError`: (a TypeError) If ``element`` is not a HoloViews element or overlay.
- `OfflineError`: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would put the file outside the cache directory.

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

- `UnsupportedTargetError`: (a TypeError) Always. Draw the logos inside the plot with ``add_logos``, or use the matplotlib, Plotly or Altair adapter for axis logos.

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

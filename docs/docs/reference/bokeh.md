---
title: sdvplot.bokeh
sidebar_label: sdvplot.bokeh
sidebar_position: 21
---

# sdvplot.bokeh

The Bokeh adapter: logos, wordmarks and headshots as one ``image_url`` glyph per call on a Bokeh figure.

| Name | What it is |
|---|---|
| [add_bins](#add_bins) | Draw hexagonal or square bins, colored by count, as one ``patches`` glyph on a Bokeh figure. |
| [add_headshots](#add_headshots) | Draw each player's headshot centred on its (x, y) point of a Bokeh figure. |
| [add_logos](#add_logos) | Draw each team's logo centred on its (x, y) point of a Bokeh figure. |
| [add_wordmarks](#add_wordmarks) | Draw each team's wordmark centred on its (x, y) point of a Bokeh figure. |
| [axis_logos](#axis_logos) | Not supported on Bokeh: Bokeh glyphs cannot sit outside the plot frame at a fixed pixel offset. |

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
    palette: Any = 'Viridis256',
    alpha: float = 1.0,
    link: Any = None,
) -> Any
```

</div>

Draw hexagonal or square bins, colored by count, as one ``patches`` glyph on a Bokeh figure.

The cells are ``sdvplot.binner``'s, in data units. The glyph (named ``"sdvplot_bins"``) has its own
``ColumnDataSource``, one row per cell: ``xs``/``ys`` (the polygon), ``x``/``y`` (the centre), ``count``,
``bin_id`` (``"x,y"``, as sdvplot-js stamps ``data-sdv-id``), ``point_ids`` (the ids of its points) and ``rows``
(their row numbers); a ``linear_cmap`` on ``count`` colors it.

Linking: pass the points' ``ColumnDataSource`` (row ``i`` is the point at ``x[i]``, ``y[i]``) as ``link``, and
two ``CustomJS`` callbacks tie the selections in the browser, with no server: selecting cells (with a ``tap`` or
``box_select`` tool on the figure) selects their points, and selecting points (in any glyph or ``DataTable`` on
that source) selects the cells holding them. A selection already consistent both ways is left as it is.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``bokeh.plotting`` figure. |
| `x` | `Any` | The points' x values, in data units. |
| `y` | `Any` | The points' y values. |
| `shape` | `Literal['hex', 'square']` | ``"hex"`` (the default) or ``"square"``. |
| `radius` | `float \| None` | The hexagon's circumradius, in data units; for squares, with ``equal_area=True``. |
| `side` | `float \| None` | The square's side (``shape="square"``). |
| `equal_area` | `bool` | Squares of a radius-``radius`` hexagon's area. |
| `ids` | `Any` | Optional link ids, one per point (default the row number); see ``sdvplot.hexbin``. |
| `palette` | `Any` | A Bokeh palette name or list of colors (default ``"Viridis256"``), fewest to most points. |
| `alpha` | `float` | The cells' fill opacity, 0 to 1. |
| `link` | `Any` | Optional ``ColumnDataSource`` of the same points, in the same order, to link selections with. |

### Returns

`figure` — ``target``, with the glyph added.

### Raises

- `InputError`: If the lattice options are not valid (see ``sdvplot.binner``) or ``alpha`` is outside [0, 1].
- `UnsupportedTargetError`: If ``target`` is not a ``bokeh.plotting`` figure.
- `TypeError`: If ``link`` is not a ``ColumnDataSource``.
- `ValueError`: If ``x``, ``y`` and ``ids`` differ in length, or ``link`` does not hold one row per point.

### Example

```python
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from sdvplot.bokeh import add_bins

# three Brooklyn shots of 2025-26, legacy tenths of a foot (sportsdataverse-data nba_stats_shots)
shots = ColumnDataSource({"x": [0, -1, -44], "y": [0, 7, 252]})
p = figure(tools="tap,box_select,reset", frame_height=300)
p.scatter("x", "y", source=shots)
add_bins(p, shots.data["x"], shots.data["y"], shape="square", side=15, alpha=0.6, link=shots)
```

### See also

- [sdvplot.binner](https://sdvplot.sportsdataverse.org/docs/reference/binner)
- [Bokeh linked selection](https://docs.bokeh.org/en/latest/docs/user_guide/interaction/linking.html)

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
    embed: bool = False,
    id_system: str = 'espn',
) -> Any
```

</div>

Draw each player's headshot centred on its (x, y) point of a Bokeh figure.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``bokeh.plotting.figure``. |
| `x` | `Any` | The points' x positions, in the figure's x values. |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `players` | `Any` | The player id for each point. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `float` | The headshot height as a fraction of the reference height (see ``add_logos``), in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``. |

### Returns

`object` — ``target`` itself, with one renderer named ``sdvplot_headshot`` added.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league`` has no ESPN headshots, or ``id_system`` is not valid for ``league``.
- `ValueError`: If the inputs differ in length, or the figure has no pixel height (neither ``frame_height`` nor ``height`` is set).
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a Bokeh figure.
- `OfflineError`: If the nflverse player table (``id_system="gsis"``), or with ``embed=True`` a headshot, is neither cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
from bokeh.plotting import figure
import sdvplot

p = figure(frame_height=300)
sdvplot.add_headshots(p, [0.5], [0.5], ["3139477"], league="nfl", height=0.2)
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
    embed: bool = False,
    id_system: str = 'auto',
) -> Any
```

</div>

Draw each team's logo centred on its (x, y) point of a Bokeh figure.

The logos are sized in screen pixels, so they keep their size when the user zooms. ``height`` is a fraction of
the figure's ``frame_height`` (the plot area) when it is set, else of its ``height`` (the whole canvas, a little
taller than the plot area): set ``frame_height`` for the same sizing as the other libraries.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``bokeh.plotting.figure``. |
| `x` | `Any` | The points' x positions, in the figure's x values (numbers, factors or datetimes). |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point, to pick each team's mark for that era. |
| `height` | `float` | The logo height as a fraction of the reference height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `embed` | `bool` | Inline each image as a data URI (HTML that renders offline) instead of linking its URL. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`object` — ``target`` itself, with one ``image_url`` renderer named ``sdvplot_logo`` added.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If the inputs differ in length, or the figure has no pixel height (neither ``frame_height`` nor ``height`` is set).
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a Bokeh figure.
- `OfflineError`: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would put the file outside the cache directory.

### Example

```python
from bokeh.plotting import figure
import sdvplot

p = figure(frame_width=400, frame_height=300)
p.scatter([10, 20], [-3, -7])
sdvplot.add_logos(p, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)
```

### See also

- [sdvplotR geom_nfl_logos()](https://sdvplotR.sportsdataverse.org/)
- [Bokeh ImageURL](https://docs.bokeh.org/en/latest/docs/reference/models/glyphs/image_url.html)

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
    embed: bool = False,
    id_system: str = 'auto',
) -> Any
```

</div>

Draw each team's wordmark centred on its (x, y) point of a Bokeh figure.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``bokeh.plotting.figure``. |
| `x` | `Any` | The points' x positions, in the figure's x values. |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point. |
| `height` | `float` | The wordmark height as a fraction of the reference height (see ``add_logos``), in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`object` — ``target`` itself, with one renderer named ``sdvplot_wordmark`` added.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If the inputs differ in length, or the figure has no pixel height (neither ``frame_height`` nor ``height`` is set).
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a Bokeh figure.
- `OfflineError`: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would put the file outside the cache directory.

### Example

```python
from bokeh.plotting import figure
import sdvplot

p = figure(x_range=["KC", "BUF"], frame_height=300)
p.vbar(x=["KC", "BUF"], top=[12, 10], width=0.8)
sdvplot.add_wordmarks(p, ["KC", "BUF"], [12, 10], ["KC", "BUF"], league="nfl", height=0.06)
```

### See also

- [sdvplotR geom_nfl_wordmarks()](https://sdvplotR.sportsdataverse.org/)

## axis_logos

<div class="sdv-signature">

```python
axis_logos(target: Any, axis: str, **kwargs: Any) -> Any
```

</div>

Not supported on Bokeh: Bokeh glyphs cannot sit outside the plot frame at a fixed pixel offset.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A Bokeh figure. |
| `axis` | `str` | "x" or "y". |
| `**kwargs` | `Any` | Ignored. |

### Returns

`object` — Never returns.

### Raises

- `UnsupportedTargetError`: (a TypeError) Always. Draw the logos inside the plot with ``add_logos`` at a y below the bars, or use the matplotlib, Plotly or Altair adapter for axis logos.

### Example

```python
from bokeh.plotting import figure
import sdvplot

try:
    sdvplot.axis_logos(figure(), "x", league="nfl")
except TypeError:
    pass   # raised: Bokeh has no axis logos yet
```

### See also

- [sdvplotR element_sdv_logo()](https://sdvplotR.sportsdataverse.org/)

---
title: sdvplot.bokeh
sidebar_label: sdvplot.bokeh
sidebar_position: 20
---

# sdvplot.bokeh

The Bokeh adapter: logos, wordmarks and headshots as one ``image_url`` glyph per call on a Bokeh figure.

| Name | What it is |
|---|---|
| [add_headshots](#add_headshots) | Draw each player's headshot centred on its (x, y) point of a Bokeh figure. |
| [add_logos](#add_logos) | Draw each team's logo centred on its (x, y) point of a Bokeh figure. |
| [add_wordmarks](#add_wordmarks) | Draw each team's wordmark centred on its (x, y) point of a Bokeh figure. |
| [axis_logos](#axis_logos) | Not supported on Bokeh: Bokeh glyphs cannot sit outside the plot frame at a fixed pixel offset. |

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
| `id_system` | `str` | "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``. |

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

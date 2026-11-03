---
title: sdvplot.pygal
sidebar_label: sdvplot.pygal
sidebar_position: 24
---

# sdvplot.pygal

The pygal adapter: logos, wordmarks and headshots on pygal XY charts, plus team colors as a pygal Style.

| Name | What it is |
|---|---|
| [add_bins](#add_bins) | Hexagonal or square bins, colored by count or weight, as SVG polygons on a pygal XY chart. |
| [add_headshots](#add_headshots) | Draw each player's headshot centred on its (x, y) point of a pygal XY chart, in every render of the chart. |
| [add_logos](#add_logos) | Draw each team's logo centred on its (x, y) point of a pygal XY chart, in every render of the chart. |
| [add_wordmarks](#add_wordmarks) | Draw each team's wordmark centred on its (x, y) point of a pygal XY chart, in every render of the chart. |
| [axis_logos](#axis_logos) | Not supported: pygal draws axis labels as text nodes, so sdvplot.pygal cannot put logos in their place. |
| [team_style](#team_style) | A pygal Style whose series colors are the teams' colors, in the order the series are added. |

## add_bins

<div class="sdv-signature">

```python
add_bins(
    chart: Any,
    x: Any,
    y: Any,
    *,
    shape: Literal['hex', 'square'] = 'hex',
    radius: float | None = None,
    side: float | None = None,
    equal_area: bool = False,
    weights: Any = None,
    origin: tuple[float, float] = (0.0, 0.0),
    value: Literal['count', 'weight'] = 'count',
    fill: float | None = None,
    min_count: int = 1,
    low: str = '#deebf7',
    high: str = '#08519c',
    opacity: float = 1.0,
) -> Any
```

</div>

Hexagonal or square bins, colored by count or weight, as SVG polygons on a pygal XY chart.

As the marks: ``add_bins`` records the cells on the chart and one xml filter (``chart.add_xml_filter``) draws them
at each render, through ``chart.view``, pygal's own projection, so each vertex sits where pygal would draw that
point. The cells go under pygal's series, clipped to the plot area; each is a ``<polygon>`` with a ``<title>``
(its ``bin_id``, count and weight, the browser's hover text). The fill runs from ``low`` (the lowest value) to
``high`` (the highest), in RGB. Linking: none, pygal's SVG is static.

### Arguments

| Name | Type | Description |
|---|---|---|
| `chart` | `Any` | A pygal XY-family chart (``pygal.XY``, ``DateTimeLine``, ...). |
| `x` | `Any` | The points' x values, in the chart's x units. |
| `y` | `Any` | The points' y values. |
| `shape` | `Literal['hex', 'square']` | ``"hex"`` (the default) or ``"square"``. |
| `radius` | `float \| None` | The hexagon's circumradius, in data units; for squares, with ``equal_area=True``. |
| `side` | `float \| None` | The square's side (``shape="square"``). |
| `equal_area` | `bool` | Squares of a radius-``radius`` hexagon's area. |
| `weights` | `Any` | Optional non-negative weights, one per point (see ``sdvplot.hexbin``): each bin's ``weight``. |
| `origin` | `tuple[float, float]` | The point a cell centre falls on (default ``(0.0, 0.0)``): a hoop-centred lattice, origin = the basket's coordinates. |
| `value` | `Literal['count', 'weight']` | What the fill encodes: ``"count"`` (the default, the points in each cell) or ``"weight"`` (the sum of their ``weights``). |
| `fill` | `float \| None` | The drawn cell's size as a fraction of the lattice cell, in (0, 1]: default 0.88 for squares (a gap, so they do not touch edge to edge) and 1.0 for hexagons (the tiled hexbin look). |
| `min_count` | `int` | Cells with fewer points are not drawn (default 1, every cell). ``min_count=2`` suits shot charts: single attempts are not drawn. ``sdvplot.hexbin`` / ``squarebin`` still return every cell. |
| `low` | `str` | The color of the lowest value (default ``"#deebf7"``), any CSS color. |
| `high` | `str` | The color of the highest value (default ``"#08519c"``). |
| `opacity` | `float` | The cells' fill opacity, 0 to 1. |

### Returns

`chart` — ``chart``, with the cells recorded.

### Raises

- `InputError`: If the lattice options are not valid (see ``sdvplot.binner``), ``value`` is not "count" or "weight", ``fill`` is not in (0, 1], ``min_count`` is not a whole number >= 1, or ``opacity`` is outside [0, 1].
- `UnsupportedTargetError`: If ``chart`` is not an XY-family chart.
- `ValueError`: If ``x``, ``y`` and ``weights`` differ in length, or ``low`` / ``high`` is not a color.

### Example

```python
import pygal
from sdvplot.pygal import add_bins

# three Brooklyn shots of 2025-26, legacy tenths of a foot (sportsdataverse-data nba_stats_shots)
x, y = [0, -1, -44], [0, 7, 252]
chart = pygal.XY(stroke=False)
chart.add("shots", list(zip(x, y)))
add_bins(chart, x, y, shape="square", side=15, opacity=0.7)
svg = chart.render()
```

### See also

- [sdvplot.binner](https://sdvplot.sportsdataverse.org/docs/reference/binner)
- [pygal xml filters](https://www.pygal.org/en/stable/documentation/output.html)

## add_headshots

<div class="sdv-signature">

```python
add_headshots(
    chart: Any,
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

Draw each player's headshot centred on its (x, y) point of a pygal XY chart, in every render of the chart.

Copy the chart with ``copy.deepcopy`` (the copy keeps the headshots); a shallow copy shares pygal's own series and
filters.

### Arguments

| Name | Type | Description |
|---|---|---|
| `chart` | `Any` | A pygal ``XY`` chart or one of its time variants (``DateTimeLine``, ``DateLine``, ...). |
| `x` | `Any` | The points' x positions in the chart's units (read by position). |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `players` | `Any` | The player id for each point. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `float` | The headshot height as a fraction of the plot height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `embed` | `bool` | True puts the image bytes in the SVG as data URIs (no network when rendering). |
| `id_system` | `str` | "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``. |

### Returns

`object` — ``chart`` itself, with a filter that draws the headshots whenever it renders.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league`` has no ESPN headshots, or ``id_system`` is not valid for ``league``.
- `ValueError`: If the inputs differ in length.
- `UnsupportedTargetError`: (a TypeError) If ``chart`` is not an XY-family chart.
- `OfflineError`: If the nflverse player table (``id_system="gsis"``), or with ``embed=True`` a headshot, is neither cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
import pygal
import sdvplot

chart = pygal.XY(stroke=False)
chart.add("passing", [(4.2, 0.31)])
sdvplot.add_headshots(chart, [4.2], [0.31], ["3139477"], league="nfl", height=0.15)
```

### See also

- [sdvplotR geom_nfl_headshots()](https://sdvplotR.sportsdataverse.org/)

## add_logos

<div class="sdv-signature">

```python
add_logos(
    chart: Any,
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

Draw each team's logo centred on its (x, y) point of a pygal XY chart, in every render of the chart.

Copy the chart with ``copy.deepcopy`` (the copy keeps the logos); a shallow copy shares pygal's own series and
filters.

### Arguments

| Name | Type | Description |
|---|---|---|
| `chart` | `Any` | A pygal ``XY`` chart (``XY(stroke=False)`` for a scatter) or a ``DateTimeLine``/``DateLine``/ ``TimeLine``/``TimeDeltaLine``. |
| `x` | `Any` | The points' x positions in the chart's units (numbers, or dates for the time charts; read by position). |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point, to pick each team's mark for that era. |
| `height` | `float` | The logo height as a fraction of the plot height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `embed` | `bool` | True puts the image bytes in the SVG as data URIs, so the SVG and ``render_to_png()`` need no network. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`object` — ``chart`` itself, with a filter that draws the logos whenever it renders.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If ``x``/``y``/``teams`` differ in length.
- `UnsupportedTargetError`: (a TypeError) If ``chart`` is not an XY-family chart (Bar, Line and Pie place values by category or angle).
- `OfflineError`: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would put the file outside the cache directory.

### Example

```python
import pygal
import sdvplot

chart = pygal.XY(stroke=False)
chart.add("games", [(10, -3), (20, -7)])
sdvplot.add_logos(chart, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)
chart.render_to_file("chart.svg")
```

### See also

- [sdvplotR geom_nfl_logos()](https://sdvplotR.sportsdataverse.org/)
- [pygal](https://www.pygal.org/)

## add_wordmarks

<div class="sdv-signature">

```python
add_wordmarks(
    chart: Any,
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

Draw each team's wordmark centred on its (x, y) point of a pygal XY chart, in every render of the chart.

Copy the chart with ``copy.deepcopy`` (the copy keeps the wordmarks); a shallow copy shares pygal's own series and
filters.

### Arguments

| Name | Type | Description |
|---|---|---|
| `chart` | `Any` | A pygal ``XY`` chart or one of its time variants (``DateTimeLine``, ``DateLine``, ...). |
| `x` | `Any` | The points' x positions in the chart's units (read by position). |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point. |
| `height` | `float` | The wordmark height as a fraction of the plot height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `embed` | `bool` | True puts the image bytes in the SVG as data URIs (no network when rendering). |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`object` — ``chart`` itself, with a filter that draws the wordmarks whenever it renders.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If the inputs differ in length.
- `UnsupportedTargetError`: (a TypeError) If ``chart`` is not an XY-family chart.
- `OfflineError`: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would put the file outside the cache directory.

### Example

```python
import pygal
import sdvplot

chart = pygal.XY(stroke=False)
chart.add("games", [(10, -3)])
sdvplot.add_wordmarks(chart, [10], [-3], ["KC"], league="nfl", height=0.08)
```

### See also

- [sdvplotR geom_nfl_wordmarks()](https://sdvplotR.sportsdataverse.org/)

## axis_logos

<div class="sdv-signature">

```python
axis_logos(chart: Any, axis: str, **kwargs: Any) -> Any
```

</div>

Not supported: pygal draws axis labels as text nodes, so sdvplot.pygal cannot put logos in their place.

### Arguments

| Name | Type | Description |
|---|---|---|
| `chart` | `Any` | A pygal chart. |
| `axis` | `str` | "x" or "y". |
| `**kwargs` | `Any` | The arguments the other adapters take (``league``, ``height``, ...); ignored. |

### Returns

`object` — Never returns.

### Raises

- `UnsupportedTargetError`: (a TypeError) Always.

### Example

```python
import pygal
import sdvplot.pygal

try:
    sdvplot.pygal.axis_logos(pygal.Bar(), "x", league="nfl")
except TypeError:
    pass   # use matplotlib, plotnine or Plotly for axis logos
```

### See also

- [sdvplot.matplotlib.axis_logos()](https://sdvplot.sportsdataverse.org/)

## team_style

<div class="sdv-signature">

```python
team_style(
    teams: Any,
    *,
    league: str,
    which: Literal['primary', 'secondary'] = 'primary',
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'yahoo', 'kenpom', 'torvik', 'sdvplotr', 'name', 'nhl_id', 'fox', 'cbs', 'sports247', 'on3'] = 'auto',
    strict: bool = False,
    **style_kwargs: Any,
) -> pygal.style.Style
```

</div>

A pygal Style whose series colors are the teams' colors, in the order the series are added.

A team that does not resolve keeps pygal's default color for its position (with one SdvplotWarning), so the
other series keep theirs.

### Arguments

| Name | Type | Description |
|---|---|---|
| `teams` | `Any` | One team per series, in series order (or one team, for one series), in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary". |
| `season` | `Any` | One season, or one per team. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'yahoo', 'kenpom', 'torvik', 'sdvplotr', 'name', 'nhl_id', 'fox', 'cbs', 'sports247', 'on3']` | The id system of ``teams``: ``"auto"`` (the default) tries them in order; pass ``"nhl_id"`` for NHL stats ids, which ``"auto"`` never tries. |
| `strict` | `bool` | Raise ``UnresolvedTeamError`` for a team that does not resolve, instead of keeping pygal's default color for it with one ``SdvplotWarning``. |
| `**style_kwargs` | `Any` | Any other ``pygal.style.Style`` option (``background``, ``font_family``, ...). |

### Returns

`pygal.style.Style` — A style for ``pygal.XY(style=...)`` or any other pygal chart.

### Raises

- `TypeError`: If ``teams`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
- `InputError`: (a ValueError) If ``league`` or ``id_system`` is unknown, ``which`` is not "primary"/"secondary", or ``season`` is not a year or is outside the seasons sdvplot knows for the league (or a list whose length does not match the teams).
- `UnresolvedTeamError`: (a ValueError) With ``strict=True``, for a team that does not resolve.

### Example

```python
import pygal
import sdvplot.pygal

chart = pygal.Bar(style=sdvplot.pygal.team_style(["KC", "BUF"], league="nfl"))
chart.add("KC", [12])
chart.add("BUF", [10])
```

### See also

- [sdvplot.team_colors()](https://sdvplot.sportsdataverse.org/)
- [pygal styles](https://www.pygal.org/en/stable/documentation/styles.html)

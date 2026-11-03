---
title: sdvplot.folium
sidebar_label: sdvplot.folium
sidebar_position: 23
---

# sdvplot.folium

The Folium adapter: logos, wordmarks and headshots as map markers with image icons.

| Name | What it is |
|---|---|
| [add_bins](#add_bins) | Hexagonal or square bins, colored by count or weight, as one GeoJSON layer of polygons on a folium map. |
| [add_headshots](#add_headshots) | Put each player's headshot on a Folium map at its (longitude, latitude). |
| [add_logos](#add_logos) | Put each team's logo on a Folium map at its (longitude, latitude), with the team name as a tooltip. |
| [add_wordmarks](#add_wordmarks) | Put each team's wordmark on a Folium map at its (longitude, latitude). |
| [axis_logos](#axis_logos) | Not supported: a map has no category axes. |

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
    weights: Any = None,
    origin: tuple[float, float] = (0.0, 0.0),
    value: Literal['count', 'weight'] = 'count',
    fill: float | None = None,
    min_count: int = 1,
    palette: Any = 'viridis',
    opacity: float = 0.7,
) -> Any
```

</div>

Hexagonal or square bins, colored by count or weight, as one GeoJSON layer of polygons on a folium map.

On a map ``x`` is longitude and ``y`` latitude, so the lattice is in degrees: ``radius``, ``side`` and ``origin``
are degrees of longitude and latitude, not metres. Leaflet's Web Mercator stretches a degree of longitude less than
one of latitude away from the equator, so cells look taller than wide by ``1 / cos(latitude)`` (about 1.3 at 40
degrees); bin projected coordinates and convert the vertices yourself for equal-area cells on the ground. The
layer is a ``folium.GeoJson`` named ``"sdvplot bins"`` (a ``LayerControl`` toggles it), one ``Polygon`` feature
per cell with ``bin_id`` (``"x,y"``), ``count`` and ``weight`` properties, shown on hover. Linking: none, the
layer is static.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``folium.Map``. |
| `x` | `Any` | The points' longitudes, in degrees. |
| `y` | `Any` | The points' latitudes, in degrees. |
| `shape` | `Literal['hex', 'square']` | ``"hex"`` (the default) or ``"square"``. |
| `radius` | `float \| None` | The hexagon's circumradius, in degrees; for squares, with ``equal_area=True``. |
| `side` | `float \| None` | The square's side, in degrees (``shape="square"``). |
| `equal_area` | `bool` | Squares of a radius-``radius`` hexagon's area. |
| `weights` | `Any` | Optional non-negative weights, one per point (see ``sdvplot.hexbin``): each bin's ``weight``. |
| `origin` | `tuple[float, float]` | The point a cell centre falls on, ``(longitude, latitude)`` (default ``(0.0, 0.0)``): as a hoop-centred lattice puts origin at the basket's coordinates. |
| `value` | `Literal['count', 'weight']` | What the fill encodes: ``"count"`` (the default, the points in each cell) or ``"weight"`` (the sum of their ``weights``). |
| `fill` | `float \| None` | The drawn cell's size as a fraction of the lattice cell, in (0, 1]: default 0.88 for squares (a gap, so they do not touch edge to edge) and 1.0 for hexagons (the tiled hexbin look). |
| `min_count` | `int` | Cells with fewer points are not drawn (default 1, every cell). ``min_count=2`` suits shot charts: single attempts are not drawn. ``sdvplot.hexbin`` / ``squarebin`` still return every cell. |
| `palette` | `Any` | A ``branca.colormap.linear`` name (default ``"viridis"``) or a branca colormap, lowest to highest value. |
| `opacity` | `float` | The cells' fill opacity, 0 to 1. |

### Returns

`Map` — ``target``, with the layer added.

### Raises

- `InputError`: If the lattice options are not valid (see ``sdvplot.binner``), ``value`` is not "count" or "weight", ``fill`` is not in (0, 1], ``min_count`` is not a whole number >= 1, or ``opacity`` is outside [0, 1].
- `UnsupportedTargetError`: If ``target`` is not a ``folium.Map``.
- `ValueError`: If ``x``, ``y`` and ``weights`` differ in length, or ``palette`` is not a branca linear colormap.

### Example

```python
import folium
from sdvplot.folium import add_bins

# three stadiums' longitudes and latitudes: two in New Jersey share a half-degree hexagon
lon, lat = [-74.074, -74.07, -71.264], [40.813, 40.81, 42.091]
m = folium.Map(location=[41.5, -72.5], zoom_start=6)
add_bins(m, lon, lat, radius=0.5)
```

### See also

- [sdvplot.binner](https://sdvplot.sportsdataverse.org/docs/reference/binner)
- [folium GeoJson](https://python-visualization.github.io/folium/latest/user_guide/geojson/geojson.html)

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

Put each player's headshot on a Folium map at its (longitude, latitude).

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``folium.Map``. |
| `x` | `Any` | The longitudes. |
| `y` | `Any` | The latitudes, the same length as ``x``. |
| `players` | `Any` | The player id for each point (shown as the tooltip). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `float` | The headshot height as a fraction of the map's reference height (see ``add_logos``), in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``. |

### Returns

`object` — ``target`` itself, with the markers added.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league`` has no ESPN headshots, or ``id_system`` is not valid for ``league``.
- `ValueError`: If the inputs differ in length, or a location is not a number.
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a ``folium.Map``.
- `OfflineError`: If the nflverse player table (``id_system="gsis"``), or with ``embed=True`` a headshot, is neither cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
import folium
import sdvplot

m = folium.Map(location=[39, -95], zoom_start=4)
sdvplot.add_headshots(m, [-94.48], [39.05], ["3139477"], league="nfl", height=0.08)
```

### See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)

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

Put each team's logo on a Folium map at its (longitude, latitude), with the team name as a tooltip.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``folium.Map``. |
| `x` | `Any` | The longitudes. |
| `y` | `Any` | The latitudes, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point, to pick each team's mark for that era. |
| `height` | `float` | The logo height as a fraction of the map's pixel height (or of _FOLIUM_REFERENCE_HEIGHT, 500 px, when the map height is not in pixels), in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `embed` | `bool` | Inline each image as a data URI (a map that renders offline) instead of linking its URL. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`object` — ``target`` itself, with the markers in the "sdvplot logos" feature group.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If the inputs differ in length, or a location is not a number.
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a ``folium.Map``.
- `OfflineError`: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would put the file outside the cache directory.

### Example

```python
import folium
import sdvplot

m = folium.Map(location=[39, -95], zoom_start=4, height=600)
sdvplot.add_logos(m, [-94.48, -78.79], [39.05, 42.77], ["KC", "BUF"], league="nfl", height=0.06)
```

### See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [Folium CustomIcon](https://python-visualization.github.io/folium/latest/user_guide/ui_elements/icons.html)

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

Put each team's wordmark on a Folium map at its (longitude, latitude).

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``folium.Map``. |
| `x` | `Any` | The longitudes. |
| `y` | `Any` | The latitudes, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point. |
| `height` | `float` | The wordmark height as a fraction of the map's reference height (see ``add_logos``), in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`object` — ``target`` itself, with the markers added.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If the inputs differ in length, or a location is not a number.
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a ``folium.Map``.
- `OfflineError`: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would put the file outside the cache directory.

### Example

```python
import folium
import sdvplot

m = folium.Map(location=[39, -95], zoom_start=4)
sdvplot.add_wordmarks(m, [-94.48], [39.05], ["KC"], league="nfl", height=0.04)
```

### See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)

## axis_logos

<div class="sdv-signature">

```python
axis_logos(target: Any, axis: str, **kwargs: Any) -> Any
```

</div>

Not supported: a map has no category axes.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A ``folium.Map``. |
| `axis` | `str` | "x" or "y". |
| `**kwargs` | `Any` | Ignored. |

### Returns

`object` — Never returns.

### Raises

- `UnsupportedTargetError`: (a TypeError) Always. Put the logos on the map with ``add_logos`` instead.

### Example

```python
import folium
import sdvplot

try:
    sdvplot.axis_logos(folium.Map(), "x", league="nfl")
except TypeError:
    pass   # raised: maps have no axis logos
```

### See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)

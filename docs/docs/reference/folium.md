---
title: sdvplot.folium
sidebar_label: sdvplot.folium
sidebar_position: 22
---

# sdvplot.folium

The Folium adapter: logos, wordmarks and headshots as map markers with image icons.

| Name | What it is |
|---|---|
| [add_headshots](#add_headshots) | Put each player's headshot on a Folium map at its (longitude, latitude). |
| [add_logos](#add_logos) | Put each team's logo on a Folium map at its (longitude, latitude), with the team name as a tooltip. |
| [add_wordmarks](#add_wordmarks) | Put each team's wordmark on a Folium map at its (longitude, latitude). |
| [axis_logos](#axis_logos) | Not supported: a map has no category axes. |

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
| `id_system` | `str` | "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``. |

### Returns

`object` — ``target`` itself, with the markers added.

### Raises

- `ValueError`: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or a location is not a number.
- `TypeError`: If ``target`` is not a ``folium.Map``.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

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

- `ValueError`: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or a location is not a number.
- `TypeError`: If ``target`` is not a ``folium.Map``.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

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

- `ValueError`: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or a location is not a number.
- `TypeError`: If ``target`` is not a ``folium.Map``.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

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

- `TypeError`: Always. Put the logos on the map with ``add_logos`` instead.

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

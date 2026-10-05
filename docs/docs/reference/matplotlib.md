---
title: sdvplot.matplotlib
sidebar_label: sdvplot.matplotlib
sidebar_position: 16
---

# sdvplot.matplotlib

The matplotlib adapter: logos, wordmarks and headshots on Axes, single-Axes Figures and seaborn grids.

| Name | What it is |
|---|---|
| [add_headshots](#add_headshots) | Draw each player's headshot centred on its (x, y) point of a matplotlib or seaborn plot. |
| [add_images](#add_images) | Draw any image, by local path or URL, centred on each (x, y) point of a matplotlib or seaborn plot. |
| [add_logos](#add_logos) | Draw each team's logo centred on its (x, y) point of a matplotlib or seaborn plot. |
| [add_wordmarks](#add_wordmarks) | Draw each team's wordmark centred on its (x, y) point of a matplotlib or seaborn plot. |
| [axis_logos](#axis_logos) | Replace a team axis' tick labels with the teams' logos (or wordmarks). |
| [team_tiers](#team_tiers) | A tier list: each team's logo in its tier's row, tier 1 on top, on a dark (sdvplotR) or light theme. |
| [title_image](#title_image) | Set the plot title and draw an image (a team logo, or any image) beside it. |

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
    zorder: float = 3,
    id_system: str = 'espn',
    transform: Any = None,
) -> Any
```

</div>

Draw each player's headshot centred on its (x, y) point of a matplotlib or seaborn plot.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A matplotlib Axes, a Figure with one Axes, or a seaborn grid with one Axes (or a JointGrid). |
| `x` | `Any` | The points' x positions, in data coordinates (read by position). |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `players` | `Any` | The player id for each point. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `float` | The headshot height as a fraction of the Axes height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `zorder` | `float` | matplotlib drawing order. |
| `id_system` | `str` | "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``. |
| `transform` | `Any` | The coordinates x and y are in, when not the Axes' data: a Cartopy CRS such as ``ccrs.PlateCarree()`` (longitude/latitude, required on a GeoAxes) or a matplotlib Transform. A mark whose position falls outside the Axes is not drawn, whatever the transform. |

### Returns

`object` — ``target`` itself, drawn on.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league`` has no ESPN headshots, or ``id_system`` is not valid for ``league``.
- `ValueError`: If the inputs differ in length, the target has several Axes, or the target is a Cartopy GeoAxes and ``transform`` is None.
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a matplotlib Axes, a Figure or a seaborn grid.
- `OfflineError`: If a headshot, or with ``id_system="gsis"`` the nflverse player table, is neither cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
import matplotlib.pyplot as plt
import sdvplot

fig, ax = plt.subplots()
sdvplot.add_headshots(ax, [0.5], [0.5], ["3139477"], league="nfl", height=0.2)
```

### See also

- [sdvplotR geom_nfl_headshots()](https://sdvplotR.sportsdataverse.org/)

## add_images

<div class="sdv-signature">

```python
add_images(
    target: Any,
    x: Any,
    y: Any,
    paths: Any,
    *,
    height: float = 0.1,
    alpha: float = 1,
    zorder: float = 3,
    transform: Any = None,
) -> Any
```

</div>

Draw any image, by local path or URL, centred on each (x, y) point of a matplotlib or seaborn plot.

The image counterpart of ``add_logos``, with the same sizing: ``height`` is a fraction of the Axes height, and
each image keeps its aspect ratio. URLs are downloaded once and cached (like headshots); local files are read
as they are. PNG, JPEG, GIF, WebP and the other formats Pillow reads work; SVG does not.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A matplotlib Axes, a Figure with one Axes, or a seaborn grid with one Axes (or a JointGrid). |
| `x` | `Any` | The points' x positions, in data coordinates (list, numpy array, or pandas/polars Series; read by position). |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `paths` | `Any` | The image for each point (or one ``pathlib.Path`` for one point): a local path (str or ``pathlib.Path``), a ``file://`` URI or an https URL (http is refused). A null path draws nothing. |
| `height` | `float` | The image height as a fraction of the Axes height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `zorder` | `float` | matplotlib drawing order (3 draws above lines and markers). |
| `transform` | `Any` | The coordinates x and y are in, when not the Axes' data: a Cartopy CRS (required on a GeoAxes) or a matplotlib Transform such as ``ax.transAxes``. |

### Returns

`object` — ``target`` itself, drawn on. Points whose image cannot be read (a missing file, a file that is not an image, a failed download) or whose x or y is missing are skipped, with one SdvplotWarning per reason.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range.
- `ValueError`: If ``x``/``y``/``paths`` differ in length, the target has several Axes, or the target is a Cartopy GeoAxes and ``transform`` is None. (An image that cannot be read or downloaded is skipped with a warning, not raised.)
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a matplotlib Axes, a Figure or a seaborn grid.

### Example

```python
import matplotlib.pyplot as plt
from sdvplot.matplotlib import add_images

fig, ax = plt.subplots()
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
add_images(ax, [3, 7], [5, 5], ["court.png", "https://www.python.org/static/img/python-logo.png"],
           height=0.2)
```

### See also

- [ggpath geom_from_path()](https://mrcaseb.github.io/ggpath/)
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
    zorder: float = 3,
    id_system: str = 'auto',
    transform: Any = None,
) -> Any
```

</div>

Draw each team's logo centred on its (x, y) point of a matplotlib or seaborn plot.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A matplotlib Axes, a Figure with one Axes, or a seaborn grid with one Axes (or a JointGrid). |
| `x` | `Any` | The points' x positions, in data coordinates (list, numpy array, or pandas/polars Series; read by position). |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point, to pick each team's mark for that era. |
| `height` | `float` | The logo height as a fraction of the Axes height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `zorder` | `float` | matplotlib drawing order (3 draws above lines and markers). |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |
| `transform` | `Any` | The coordinates x and y are in, when not the Axes' data: a Cartopy CRS such as ``ccrs.PlateCarree()`` (longitude/latitude, required on a GeoAxes) or a matplotlib Transform. A mark whose position falls outside the Axes is not drawn, whatever the transform. |

### Returns

`object` — ``target`` itself, drawn on.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If ``x``/``y``/``teams`` differ in length, the target has several Axes, or the target is a Cartopy GeoAxes and ``transform`` is None.
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a matplotlib Axes, a Figure or a seaborn grid.
- `OfflineError`: If the logo manifest or a mark's image is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If the manifest's sha256 or extension for a mark would put the file outside the cache directory.
- `OptionalDependencyError`: If a mark is an SVG and the ``svg`` extra is not installed.

### Example

```python
import matplotlib.pyplot as plt
import sdvplot

fig, ax = plt.subplots()
ax.set_xlim(0, 30)
ax.set_ylim(-10, 0)
sdvplot.add_logos(ax, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)

# On a Cartopy map, at longitude/latitude:
#   import cartopy.crs as ccrs
#   ax = plt.axes(projection=ccrs.Robinson())
#   ax.set_global()
#   sdvplot.add_logos(ax, [-94.48], [39.05], ["KC"], league="nfl", transform=ccrs.PlateCarree())
```

### See also

- [sdvplotR geom_nfl_logos()](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

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
    zorder: float = 3,
    id_system: str = 'auto',
    transform: Any = None,
) -> Any
```

</div>

Draw each team's wordmark centred on its (x, y) point of a matplotlib or seaborn plot.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A matplotlib Axes, a Figure with one Axes, or a seaborn grid with one Axes (or a JointGrid). |
| `x` | `Any` | The points' x positions, in data coordinates (read by position). |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point. |
| `height` | `float` | The wordmark height as a fraction of the Axes height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `zorder` | `float` | matplotlib drawing order. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |
| `transform` | `Any` | The coordinates x and y are in, when not the Axes' data: a Cartopy CRS such as ``ccrs.PlateCarree()`` (longitude/latitude, required on a GeoAxes) or a matplotlib Transform. A mark whose position falls outside the Axes is not drawn, whatever the transform. |

### Returns

`object` — ``target`` itself, drawn on.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If the inputs differ in length, the target has several Axes, or the target is a Cartopy GeoAxes and ``transform`` is None.
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a matplotlib Axes, a Figure or a seaborn grid.
- `OfflineError`: If the logo manifest or a mark's image is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If the manifest's sha256 or extension for a mark would put the file outside the cache directory.
- `OptionalDependencyError`: If a mark is an SVG and the ``svg`` extra is not installed.

### Example

```python
import matplotlib.pyplot as plt
import sdvplot

fig, ax = plt.subplots()
sdvplot.add_wordmarks(ax, [0.5], [0.5], ["KC"], league="nfl", height=0.1)
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
    id_system: str = 'auto',
) -> Any
```

</div>

Replace a team axis' tick labels with the teams' logos (or wordmarks).

Reads the axis' ticks and labels when called, so call it after setting the categories and limits. Labels that are
not teams stay as text, with one SdvplotWarning.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A matplotlib Axes, a Figure with one Axes, or a seaborn grid with one Axes. |
| `axis` | `str` | "x" or "y". |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season for every label. |
| `height` | `float` | The image height as a fraction of the Axes height, in (0, 1]. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `mark_type` | `str` | "logo" or "wordmark". |
| `id_system` | `str` | The id system of the labels; "auto" tries each in order. |

### Returns

`object` — ``target`` itself, drawn on.

### Raises

- `InputError`: (a ValueError) If ``height`` is out of range, ``league``, ``id_system``, ``mark_type`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If ``axis`` is not "x"/"y", or the target has several Axes.
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a matplotlib Axes, a Figure or a seaborn grid.
- `OfflineError`: If the logo manifest or a mark's image is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode).
- `UnsafeDownloadError`: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If the manifest's sha256 or extension for a mark would put the file outside the cache directory.
- `OptionalDependencyError`: If a mark is an SVG and the ``svg`` extra is not installed.

### Example

```python
import matplotlib.pyplot as plt
import sdvplot

fig, ax = plt.subplots()
ax.bar(["KC", "BUF", "BAL"], [12, 10, 9])
sdvplot.axis_logos(ax, "x", league="nfl", height=0.08)
```

### See also

- [sdvplotR element_sdv_logo()](https://sdvplotR.sportsdataverse.org/)

## team_tiers

<div class="sdv-signature">

```python
team_tiers(
    data: Any,
    league: str,
    *,
    title: str | None = None,
    subtitle: str | None = 'created with the #sdvplot Tiermaker',
    caption: str | None = None,
    tier_desc: dict[Any, str] | None = None,
    presort: bool = False,
    alpha: float = 0.8,
    height: float | None = None,
    no_line_below_tier: Any = None,
    devel: bool = False,
    theme: Literal['dark', 'light'] = 'dark',
) -> matplotlib.figure.Figure
```

</div>

A tier list: each team's logo in its tier's row, tier 1 on top, on a dark (sdvplotR) or light theme.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | A pandas or polars DataFrame with ``tier_no`` (1 is the top tier) and ``team`` (any id system ``resolve()`` understands), and optionally ``tier_rank``, the position within the tier; without it, teams keep their order in ``data``. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `title` | `str \| None` | The title; None gives "{LEAGUE} Team Tiers", "" none. |
| `subtitle` | `str \| None` | The subtitle; None or "" for none. |
| `caption` | `str \| None` | The caption, bottom right; None for none. |
| `tier_desc` | `dict[Any, str] \| None` | Each tier's label, keyed by tier number; None gives sdvplotR's (1 "Elite" ... 5 "What are they doing?"). Labels wrap at 15 characters; a tier without one gets none. |
| `presort` | `bool` | Sort teams alphabetically within each tier (ignores ``tier_rank``). |
| `alpha` | `float` | Logo opacity, 0 to 1. |
| `height` | `float \| None` | Logo height as a fraction of the panel height; None gives 0.1, about the largest height at which 32 logos in 5 tiers (7, 7, 6, 6, 6) neither overlap nor leave the panel at the default 6.4 x 4.8 in figure. |
| `no_line_below_tier` | `Any` | A tier number, or several, with no separator line below. |
| `devel` | `bool` | Draw each team as text instead of its logo (fast, and needs no download). |
| `theme` | `Literal['dark', 'light']` | "dark" (sdvplotR's: a near-black background) or "light" (white, for dark logos such as Ohio State's, Texas A&M's or Penn State's, which vanish on dark). |

### Returns

`matplotlib.figure.Figure` — A new figure with one Axes; a team that does not resolve is skipped with one SdvplotWarning, keeping its slot.

### Raises

- `TypeError`: If ``data`` is not a DataFrame, or ``tier_no``/``tier_rank`` hold non-numbers.
- `InputError`: (a ValueError) If ``height``/``alpha`` is out of range, or ``league`` is unknown.
- `ValueError`: If ``data`` lacks ``tier_no`` or ``team``, has no row with a tier, or ``theme`` is not "dark" or "light".
- `OfflineError`: Unless ``devel=True``, if the logo manifest or a mark's image is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode).
- `UnsafeDownloadError`: (an OSError) Unless ``devel=True``, if a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) Unless ``devel=True``, if the manifest's sha256 or extension for a mark would put the file outside the cache directory.
- `OptionalDependencyError`: Unless ``devel=True``, if a logo is an SVG and the ``svg`` extra is not installed.

### Example

```python
import pandas as pd
from sdvplot.matplotlib import team_tiers

df = pd.DataFrame({"tier_no": [1, 1, 2, 3], "team": ["KC", "BUF", "BAL", "NYJ"]})
fig = team_tiers(df, "nfl")

# Draft it as text first, then add logos:
fig = team_tiers(df, "nfl", devel=True, no_line_below_tier=1)

# Dark logos on a white background:
fig = team_tiers(df, "cfb", theme="light")
```

### See also

- [sdvplotR sdv_team_tiers()](https://sdvplotR.sportsdataverse.org/reference/sdv_team_tiers.html)
- sdvplot.plotnine.team_tiers: the same as a plotnine ggplot.

## title_image

<div class="sdv-signature">

```python
title_image(
    target: Any,
    image: Any,
    title: str = '',
    *,
    league: str | None = None,
    season: Any = None,
    side: str = 'left',
    height: float = 15,
    **text_kw: Any,
) -> Any
```

</div>

Set the plot title and draw an image (a team logo, or any image) beside it.

The title and the image are aligned together, like the image inside sdvplotR's title: a centred title centres the
pair, a left-aligned one starts with the image.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | A matplotlib Axes (sets its title), a Figure (sets its suptitle), or a seaborn grid with one Axes. |
| `image` | `Any` | A team, in any id system ``resolve()`` understands, when ``league`` is given; otherwise an image URL (https; http is refused) or a local file path. |
| `title` | `str` | The title text. |
| `league` | `str \| None` | The SDV league key, e.g. "nfl"; None reads ``image`` as a URL or path. |
| `season` | `Any` | One season, to pick the team's logo for that era. |
| `side` | `str` | "left" or "right" of the title text. |
| `height` | `float` | The image height in points (1/72 inch), at any dpi. The title keeps its own line height, so an image much taller than the text needs room: ``pad=`` on an Axes title, ``y=`` on a Figure's suptitle. |
| `**text_kw` | `Any` | Passed to ``Axes.set_title`` (``loc``, ``fontsize``, ``pad``, ...) or ``Figure.suptitle``. |

### Returns

`object` — ``target`` itself, titled. Calling it again on the same title replaces the image. An image by URL or path that cannot be read gives one SdvplotWarning and the title without it.

### Raises

- `TypeError`: If ``league`` is given and ``image`` is not one team.
- `InputError`: (a ValueError) If ``height`` is not a number of points of at least 1, or ``league`` is given and it is unknown or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If ``side`` is not "left"/"right", or the target has several Axes.
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a matplotlib Axes, a Figure or a seaborn grid.
- `OfflineError`: If ``league`` is given and the team's logo (or the logo manifest) is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode). An image by URL or path that cannot be read is skipped with a warning instead.
- `UnsafeDownloadError`: (an OSError) If ``league`` is given and a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``league`` is given and the manifest's sha256 or extension for the logo would put the file outside the cache directory.
- `OptionalDependencyError`: If ``league`` is given, the logo is an SVG and the ``svg`` extra is not installed.

### Example

```python
import matplotlib.pyplot as plt
from sdvplot.matplotlib import title_image

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [3, 1, 2])
title_image(ax, "KC", "Kansas City Chiefs Analysis", league="nfl", height=20)

# A Figure's suptitle, the image on the right:
title_image(fig, "https://example.com/banner.png", "Week 1", side="right")
```

### See also

- [sdvplotR ggtitle_image()](https://sdvplotR.sportsdataverse.org/reference/ggtitle_image.html)
- sdvplot.plotnine.title_image: the same for plotnine.

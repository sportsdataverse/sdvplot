---
title: sdvplot.plotnine
sidebar_label: sdvplot.plotnine
sidebar_position: 18
---

# sdvplot.plotnine

The plotnine adapter: logo, wordmark, headshot and image geoms, axis logos, team color scales and reference lines.

| Name | What it is |
|---|---|
| [add_headshots](#add_headshots) | A copy of the plot with each player's headshot at its (x, y). |
| [add_logos](#add_logos) | A copy of the plot with each team's logo at its (x, y); the front door's plotnine adapter. |
| [add_wordmarks](#add_wordmarks) | A copy of the plot with each team's wordmark at its (x, y). |
| [axis_logos](#axis_logos) | A copy of the plot whose team axis shows logos or wordmarks (or whose player axis shows headshots), not text. |
| [geom_from_path](#geom_from_path) | Any image, by local path or URL, at (x, y): ``aes(x=..., y=..., path=...)``, plus ``height`` (fraction of the |
| [geom_mean_lines](#geom_mean_lines) | Reference lines at the mean of ``x0`` (vertical) and/or ``y0`` (horizontal), per panel: the port of ggpath's |
| [geom_median_lines](#geom_median_lines) | Reference lines at the median of ``x0`` (vertical) and/or ``y0`` (horizontal), per panel: the port of ggpath's |
| [geom_sdv_headshots](#geom_sdv_headshots) | Player headshots at (x, y), as a plotnine layer. |
| [geom_sdv_logos](#geom_sdv_logos) | Team logos at (x, y), as a plotnine layer. |
| [geom_sdv_wordmarks](#geom_sdv_wordmarks) | Team wordmarks at (x, y), as a plotnine layer: the same aesthetics and parameters as ``geom_sdv_logos``. |
| [scale_color_sdv](#scale_color_sdv) | A discrete color scale that maps each team value (any id system) to its team color. |
| [scale_colour_sdv](#scale_colour_sdv) | A discrete color scale that maps each team value (any id system) to its team color. |
| [scale_fill_sdv](#scale_fill_sdv) | A discrete fill scale that maps each team value (any id system) to its team color. |
| [team_tiers](#team_tiers) | A tier list as a ggplot: each team's logo in its tier's row, tier 1 on top, on a dark (sdvplotR) or light theme. |
| [title_image](#title_image) | A plot title with an image (a team logo, or any image) beside it, added to a ggplot with ``+``. |

## add_headshots

<div class="sdv-signature">

```python
add_headshots(
    target: plotnine.ggplot.ggplot,
    x: Any,
    y: Any,
    players: Any,
    *,
    league: str,
    height: float = 0.1,
    alpha: float = 1,
    id_system: str = 'espn',
) -> plotnine.ggplot.ggplot
```

</div>

A copy of the plot with each player's headshot at its (x, y).

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `plotnine.ggplot.ggplot` | A plotnine ggplot. |
| `x` | `Any` | The points' x positions (read by position). |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `players` | `Any` | The player id for each point. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `float` | The headshot height as a fraction of the panel height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `id_system` | `str` | "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``. |

### Returns

`ggplot` — A new plot with a ``geom_sdv_headshots`` layer.

### Raises

- `ValueError`: If the inputs differ in length.
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a plotnine ggplot.
- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range; when the plot is drawn, if ``league`` has no ESPN headshots or ``id_system`` is not valid for it.
- `OfflineError`: When the plot is drawn, if a headshot, or with ``id_system="gsis"`` the nflverse player table, is neither cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
- `UnsafeDownloadError`: (an OSError) When the plot is drawn, if a download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
import pandas as pd
import sdvplot
from plotnine import aes, geom_point, ggplot

df = pd.DataFrame({"epa": [0.2, 0.15], "sr": [0.48, 0.47]})
p = ggplot(df, aes("epa", "sr")) + geom_point()
p2 = sdvplot.add_headshots(p, [0.2], [0.48], ["3139477"], league="nfl")
```

### See also

- [sdvplotR geom_nfl_headshots()](https://sdvplotR.sportsdataverse.org/)
- sdvplot.plotnine.geom_sdv_headshots: the layer this adds

## add_logos

<div class="sdv-signature">

```python
add_logos(
    target: plotnine.ggplot.ggplot,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = 'default',
    id_system: str = 'auto',
) -> plotnine.ggplot.ggplot
```

</div>

A copy of the plot with each team's logo at its (x, y); the front door's plotnine adapter.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `plotnine.ggplot.ggplot` | A plotnine ggplot. |
| `x` | `Any` | The points' x positions (read by position). |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point, to pick each team's mark for that era. |
| `height` | `float` | The logo height as a fraction of the panel height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`ggplot` — A new plot with a ``geom_sdv_logos`` layer; ``target`` is unchanged.

### Raises

- `ValueError`: If the inputs differ in length.
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a plotnine ggplot.
- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, or ``season`` is not a year (or a list whose length does not match the teams); when the plot is drawn, if ``league``, ``id_system`` or ``variant`` is unknown, or a season is not a year or is outside the seasons sdvplot knows for the league.
- `OfflineError`: When the plot is drawn, if the logo manifest or a mark's image is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode).
- `UnsafeDownloadError`: (an OSError) When the plot is drawn, if a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) When the plot is drawn, if the manifest's sha256 or extension for a mark would put the file outside the cache directory.
- `OptionalDependencyError`: When the plot is drawn, if a mark is an SVG and the ``svg`` extra is not installed.

### Example

```python
import pandas as pd
import sdvplot
from plotnine import aes, geom_point, ggplot

df = pd.DataFrame({"epa": [0.2, 0.15], "sr": [0.48, 0.47]})
p = ggplot(df, aes("epa", "sr")) + geom_point()
p2 = sdvplot.add_logos(p, [0.2], [0.48], ["KC"], league="nfl")
```

### See also

- [sdvplotR geom_nfl_logos()](https://sdvplotR.sportsdataverse.org/)
- sdvplot.plotnine.geom_sdv_logos: the layer this adds

## add_wordmarks

<div class="sdv-signature">

```python
add_wordmarks(
    target: plotnine.ggplot.ggplot,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = 'default',
    id_system: str = 'auto',
) -> plotnine.ggplot.ggplot
```

</div>

A copy of the plot with each team's wordmark at its (x, y).

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `plotnine.ggplot.ggplot` | A plotnine ggplot. |
| `x` | `Any` | The points' x positions (read by position). |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point, to pick each team's wordmark for that era. |
| `height` | `float` | The wordmark height as a fraction of the panel height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `id_system` | `str` | The id system of ``teams``. |

### Returns

`ggplot` — A new plot with a ``geom_sdv_wordmarks`` layer.

### Raises

- `ValueError`: If the inputs differ in length.
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a plotnine ggplot.
- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range, or ``season`` is not a year (or a list whose length does not match the teams); when the plot is drawn, if ``league``, ``id_system`` or ``variant`` is unknown, or a season is not a year or is outside the seasons sdvplot knows for the league.
- `OfflineError`: When the plot is drawn, if the logo manifest or a mark's image is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode).
- `UnsafeDownloadError`: (an OSError) When the plot is drawn, if a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) When the plot is drawn, if the manifest's sha256 or extension for a mark would put the file outside the cache directory.
- `OptionalDependencyError`: When the plot is drawn, if a mark is an SVG and the ``svg`` extra is not installed.

### Example

```python
import pandas as pd
import sdvplot
from plotnine import aes, geom_point, ggplot

df = pd.DataFrame({"epa": [0.2, 0.15], "sr": [0.48, 0.47]})
p = ggplot(df, aes("epa", "sr")) + geom_point()
p2 = sdvplot.add_wordmarks(p, [0.2], [0.48], ["KC"], league="nfl")
```

### See also

- [sdvplotR geom_nfl_wordmarks()](https://sdvplotR.sportsdataverse.org/)
- sdvplot.plotnine.geom_sdv_wordmarks: the layer this adds

## axis_logos

<div class="sdv-signature">

```python
axis_logos(
    target: plotnine.ggplot.ggplot,
    axis: str,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    variant: str = 'default',
    mark_type: Literal['logo', 'wordmark', 'headshot'] = 'logo',
    id_system: str = 'auto',
) -> plotnine.ggplot.ggplot
```

</div>

A copy of the plot whose team axis shows logos or wordmarks (or whose player axis shows headshots), not text.

### Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `plotnine.ggplot.ggplot` | A plotnine ggplot whose ``axis`` is a discrete team axis. |
| `axis` | `str` | "x" or "y". |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season for every label. |
| `height` | `float` | The image height as a fraction of the panel height, in (0, 1]. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `mark_type` | `Literal['logo', 'wordmark', 'headshot']` | "logo", "wordmark" or "headshot". With "headshot" the labels are player ids (``id_system`` "espn", "gsis" or "league" as in ``headshot_url``, "auto" meaning "espn"; ``season`` is ignored), drawn at their own aspect. |
| `id_system` | `str` | The id system of the labels. |

### Returns

`ggplot` — A new plot; labels that are not teams stay as text, with one SdvplotWarning when drawn.

### Raises

- `ValueError`: If ``axis`` is not "x"/"y".
- `UnsupportedTargetError`: (a TypeError) If ``target`` is not a plotnine ggplot.
- `InputError`: (a ValueError) If ``height`` is out of range or ``mark_type`` is not "logo", "wordmark" or "headshot"; when the plot is drawn, if ``league``, ``id_system`` or ``variant`` is unknown, or a season is not a year or is outside the seasons sdvplot knows for the league.
- `OfflineError`: When the plot is drawn, if the logo manifest or a mark's image is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode).
- `UnsafeDownloadError`: (an OSError) When the plot is drawn, if a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) When the plot is drawn, if the manifest's sha256 or extension for a mark would put the file outside the cache directory.
- `OptionalDependencyError`: When the plot is drawn, if a mark is an SVG and the ``svg`` extra is not installed.

### Example

```python
import pandas as pd
import sdvplot
from plotnine import aes, geom_col, ggplot

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "epa": [0.2, 0.15, 0.1]})
p = ggplot(df, aes("team", "epa")) + geom_col()
p2 = sdvplot.axis_logos(p, "x", league="nfl")

# player headshots as the labels (ESPN athlete ids)
qb = pd.DataFrame({"player": ["3139477", "3918298"], "epa": [0.31, 0.27]})
p3 = sdvplot.axis_logos(ggplot(qb, aes("player", "epa")) + geom_col(), "x", league="nfl",
                        mark_type="headshot")
```

### See also

- [sdvplotR element_sdv_logo(), scale_x_sdv_headshots()](https://sdvplotR.sportsdataverse.org/)
- sdvplot.plotnine.title_image: an image beside the plot title

## geom_from_path

<div class="sdv-signature">

```python
geom_from_path(
    mapping: Any = None,
    data: Any = None,
    **kwargs: Any,
) -> None
```

</div>

Any image, by local path or URL, at (x, y): ``aes(x=..., y=..., path=...)``, plus ``height`` (fraction of the

panel height, default 0.1) and ``alpha``. The port of ggpath's ``geom_from_path()``, sized like the logo geoms.

### Arguments

| Name | Description |
|---|---|
| `mapping` | ``aes(x=..., y=..., path=...)``; ``path`` holds a local file path, ``file://`` URI or https URL per row (http is refused). |
| `data` | The layer's data (pandas or polars), when not the plot's. |
| `**kwargs` | ``height`` in (0, 1], ``alpha`` in [0, 1], and plotnine's layer arguments (``inherit_aes``, ...). |

### Returns

`geom` — A plotnine layer to add with ``+``. Images that cannot be read (a missing file, a file that is not an image, a failed download) are skipped with one SdvplotWarning when the plot is drawn; SVG is not read.

### Raises

- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range (when the layer is built). An image that cannot be read or downloaded is skipped with a warning when the plot is drawn, not raised.

### Example

```python
import pandas as pd
from plotnine import aes, ggplot
from sdvplot.plotnine import geom_from_path

df = pd.DataFrame({"x": [1, 2], "y": [1, 2], "img": ["a.png", "https://www.python.org/static/favicon.ico"]})
p = ggplot(df, aes("x", "y", path="img")) + geom_from_path(height=0.15)
```

### See also

- [ggpath geom_from_path()](https://mrcaseb.github.io/ggpath/)
- sdvplot.matplotlib.add_images: the matplotlib counterpart

## geom_mean_lines

<div class="sdv-signature">

```python
geom_mean_lines(
    mapping: Any = None,
    data: Any = None,
    **kwargs: Any,
) -> None
```

</div>

Reference lines at the mean of ``x0`` (vertical) and/or ``y0`` (horizontal), per panel: the port of ggpath's

``geom_mean_lines()``.

### Arguments

| Name | Description |
|---|---|
| `mapping` | ``aes(x0=..., y0=...)``, at least one of them (``x0`` alone draws only the vertical line). |
| `data` | The layer's data (pandas or polars), when not the plot's. |
| `**kwargs` | ``color`` (default "red"), ``size`` (line width, default 0.5), ``linetype`` (default "dashed"), ``alpha``, ``na_rm`` and plotnine's layer arguments. With ``na_rm=False`` (the default) a panel whose values include a missing one draws no line on that axis, with a PlotnineWarning, as ggpath does; ``na_rm=True`` ignores the missing values. |

### Returns

`geom` — A plotnine layer to add with ``+``; each facet panel gets its own reference value.

### Raises

- `ValueError`: When the plot is drawn, if neither ``x0`` nor ``y0`` is mapped.

### Example

```python
import pandas as pd
from plotnine import aes, geom_point, ggplot
from sdvplot.plotnine import geom_mean_lines

df = pd.DataFrame({"epa": [0.2, 0.15, 0.05], "success_rate": [0.48, 0.47, 0.44]})
p = (ggplot(df, aes("epa", "success_rate", x0="epa", y0="success_rate"))
     + geom_point() + geom_mean_lines(color="grey"))
```

### See also

- [ggpath geom_mean_lines()](https://mrcaseb.github.io/ggpath/)
- geom_median_lines: the same at the median

## geom_median_lines

<div class="sdv-signature">

```python
geom_median_lines(
    mapping: Any = None,
    data: Any = None,
    **kwargs: Any,
) -> None
```

</div>

Reference lines at the median of ``x0`` (vertical) and/or ``y0`` (horizontal), per panel: the port of ggpath's

``geom_median_lines()``.

### Arguments

| Name | Description |
|---|---|
| `mapping` | ``aes(x0=..., y0=...)``, at least one of them. |
| `data` | The layer's data (pandas or polars), when not the plot's. |
| `**kwargs` | ``color`` (default "red"), ``size`` (default 0.5), ``linetype`` (default "dashed"), ``alpha``, ``na_rm`` (as ``geom_mean_lines``) and plotnine's layer arguments. |

### Returns

`geom` — A plotnine layer to add with ``+``; each facet panel gets its own reference value.

### Raises

- `ValueError`: When the plot is drawn, if neither ``x0`` nor ``y0`` is mapped.

### Example

```python
import pandas as pd
from plotnine import aes, geom_point, ggplot
from sdvplot.plotnine import geom_median_lines

df = pd.DataFrame({"epa": [0.2, 0.15, 0.05], "success_rate": [0.48, 0.47, 0.44]})
p = ggplot(df, aes("epa", "success_rate", x0="epa", y0="success_rate")) + geom_point() + geom_median_lines()
```

### See also

- [ggpath geom_median_lines()](https://mrcaseb.github.io/ggpath/)
- geom_mean_lines: the same at the mean

## geom_sdv_headshots

<div class="sdv-signature">

```python
geom_sdv_headshots(
    mapping: Any = None,
    data: Any = None,
    **kwargs: Any,
) -> None
```

</div>

Player headshots at (x, y), as a plotnine layer.

### Arguments

| Name | Description |
|---|---|
| `mapping` | ``aes(x=..., y=..., player_id=...)``. |
| `data` | The layer's data (pandas or polars), when not the plot's. |
| `**kwargs` | ``league`` (required, e.g. "nfl"), ``height`` (a fraction of the panel height, in (0, 1], default 0.1), ``alpha`` (0 to 1), ``id_system`` ("espn", "gsis" or "league", as in ``headshot_url``) and plotnine's layer arguments (``inherit_aes``, ...). |

### Returns

`geom` — A plotnine layer to add with ``+``. Marks that cannot be placed (an unknown team, a missing mark) are skipped with one SdvplotWarning when the plot is drawn.

### Raises

- `TypeError`: If ``league`` is missing.
- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range (when the layer is built); when the plot is drawn, if ``league`` has no ESPN headshots or ``id_system`` is not valid for it.
- `OfflineError`: When the plot is drawn, if a headshot, or with ``id_system="gsis"`` the nflverse player table, is neither cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
- `UnsafeDownloadError`: (an OSError) When the plot is drawn, if a download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
import pandas as pd
from plotnine import aes, ggplot
from sdvplot.plotnine import geom_sdv_headshots

df = pd.DataFrame({"x": [0.3, 0.7], "y": [0.4, 0.6], "espn_id": ["3139477", "3918298"]})
p = ggplot(df, aes("x", "y", player_id="espn_id")) + geom_sdv_headshots(league="nfl", height=0.15)
```

### See also

- [sdvplotR geom_nfl_headshots()](https://sdvplotR.sportsdataverse.org/)
- sdvplot.plotnine.geom_sdv_logos: the same with team logos

## geom_sdv_logos

<div class="sdv-signature">

```python
geom_sdv_logos(
    mapping: Any = None,
    data: Any = None,
    **kwargs: Any,
) -> None
```

</div>

Team logos at (x, y), as a plotnine layer.

For a season per row, map it instead of passing ``season=``: ``aes(..., season="season")`` (a ``season=``
parameter wins over the mapping).

### Arguments

| Name | Description |
|---|---|
| `mapping` | ``aes(x=..., y=..., team=...)``, plus optional ``season``. |
| `data` | The layer's data (pandas or polars), when not the plot's. |
| `**kwargs` | ``league`` (required, e.g. "nfl"), ``season``, ``height`` (a fraction of the panel height, in (0, 1], default 0.1), ``alpha`` (0 to 1), ``variant`` ("default", "dark" or a named variant), ``id_system`` and plotnine's layer arguments (``inherit_aes``, ...). |

### Returns

`geom` — A plotnine layer to add with ``+``. Marks that cannot be placed (an unknown team, a missing mark) are skipped with one SdvplotWarning when the plot is drawn.

### Raises

- `TypeError`: If ``league`` is missing.
- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range (when the layer is built); when the plot is drawn, if ``league``, ``id_system`` or ``variant`` is unknown, or a season is not a year or is outside the seasons sdvplot knows for the league.
- `OfflineError`: When the plot is drawn, if the logo manifest or a mark's image is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode).
- `UnsafeDownloadError`: (an OSError) When the plot is drawn, if a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) When the plot is drawn, if the manifest's sha256 or extension for a mark would put the file outside the cache directory.
- `OptionalDependencyError`: When the plot is drawn, if a mark is an SVG and the ``svg`` extra is not installed.

### Example

```python
import pandas as pd
from plotnine import aes, ggplot
from sdvplot.plotnine import geom_sdv_logos

df = pd.DataFrame({"team": ["KC", "BUF"], "epa": [0.2, 0.15], "sr": [0.48, 0.47]})
p = ggplot(df, aes("epa", "sr", team="team")) + geom_sdv_logos(league="nfl", height=0.12)
```

### See also

- [sdvplotR geom_nfl_logos()](https://sdvplotR.sportsdataverse.org/)
- sdvplot.plotnine.geom_sdv_wordmarks: the same with wordmarks

## geom_sdv_wordmarks

<div class="sdv-signature">

```python
geom_sdv_wordmarks(
    mapping: Any = None,
    data: Any = None,
    **kwargs: Any,
) -> None
```

</div>

Team wordmarks at (x, y), as a plotnine layer: the same aesthetics and parameters as ``geom_sdv_logos``.

### Arguments

| Name | Description |
|---|---|
| `mapping` | ``aes(x=..., y=..., team=...)``, plus optional ``season``. |
| `data` | The layer's data (pandas or polars), when not the plot's. |
| `**kwargs` | ``league`` (required, e.g. "nfl"), ``season``, ``height`` (a fraction of the panel height, in (0, 1], default 0.1), ``alpha`` (0 to 1), ``variant`` ("default", "dark" or a named variant), ``id_system`` and plotnine's layer arguments (``inherit_aes``, ...). |

### Returns

`geom` — A plotnine layer to add with ``+``. Marks that cannot be placed (an unknown team, a missing mark) are skipped with one SdvplotWarning when the plot is drawn.

### Raises

- `TypeError`: If ``league`` is missing.
- `InputError`: (a ValueError) If ``height`` or ``alpha`` is out of range (when the layer is built); when the plot is drawn, if ``league``, ``id_system`` or ``variant`` is unknown, or a season is not a year or is outside the seasons sdvplot knows for the league.
- `OfflineError`: When the plot is drawn, if the logo manifest or a mark's image is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode).
- `UnsafeDownloadError`: (an OSError) When the plot is drawn, if a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) When the plot is drawn, if the manifest's sha256 or extension for a mark would put the file outside the cache directory.
- `OptionalDependencyError`: When the plot is drawn, if a mark is an SVG and the ``svg`` extra is not installed.

### Example

```python
import pandas as pd
from plotnine import aes, ggplot
from sdvplot.plotnine import geom_sdv_wordmarks

df = pd.DataFrame({"team": ["KC", "BUF"], "epa": [0.2, 0.15], "sr": [0.48, 0.47]})
p = ggplot(df, aes("epa", "sr", team="team")) + geom_sdv_wordmarks(league="nfl", height=0.08)
```

### See also

- [sdvplotR geom_nfl_wordmarks()](https://sdvplotR.sportsdataverse.org/)
- sdvplot.plotnine.geom_sdv_logos: the same with logos

## scale_color_sdv

<div class="sdv-signature">

```python
scale_color_sdv(
    league: str,
    *,
    which: Literal['primary', 'secondary'] = 'primary',
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    na_value: str = 'grey',
    alpha: float | None = None,
    **kwargs: Any,
) -> Any
```

</div>

A discrete color scale that maps each team value (any id system) to its team color.

### Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary". |
| `season` | `Any` | One season for every value. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of the team values: ``"auto"`` (the default) tries them in order; pass ``"nhl_id"`` for NHL stats ids, which ``"auto"`` never tries. |
| `strict` | `bool` | Raise ``UnresolvedTeamError`` when the plot is drawn and a value does not resolve, instead of drawing it in ``na_value`` with one ``SdvplotWarning``. |
| `na_value` | `str` | The color of values that are not teams; drawn as given, ``alpha`` does not fade it. |
| `alpha` | `float \| None` | An opacity in [0, 1] applied to the team colors (sdvplotR's ``alpha``, ``scales::alpha()``); ``None`` (the default) leaves them opaque. |
| `**kwargs` | `Any` | Passed to plotnine's ``scale_color_manual`` (``name``, ``breaks``, ``guide``, ...). |

### Returns

`scale` — A plotnine color scale.

### Raises

- `InputError`: (a ValueError) If ``which`` is not "primary" or "secondary" or ``alpha`` is not in [0, 1]; when the plot is drawn, if ``league`` or ``id_system`` is unknown or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `UnresolvedTeamError`: (a ValueError) With ``strict=True``, when the plot is drawn and a value does not resolve.

### Example

```python
import pandas as pd
from plotnine import aes, geom_point, ggplot
from sdvplot.plotnine import scale_color_sdv

df = pd.DataFrame({"team": ["KC", "BUF"], "epa": [0.2, 0.15], "sr": [0.48, 0.47]})
p = ggplot(df, aes("epa", "sr", color="team")) + geom_point() + scale_color_sdv("nfl")
```

### See also

- [sdvplotR scale_color_sdv()](https://sdvplotR.sportsdataverse.org/)
- sdvplot.plotnine.scale_fill_sdv: the fill scale

## scale_colour_sdv

<div class="sdv-signature">

```python
scale_colour_sdv(
    league: str,
    *,
    which: Literal['primary', 'secondary'] = 'primary',
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    na_value: str = 'grey',
    alpha: float | None = None,
    **kwargs: Any,
) -> Any
```

</div>

A discrete color scale that maps each team value (any id system) to its team color.

### Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary". |
| `season` | `Any` | One season for every value. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of the team values: ``"auto"`` (the default) tries them in order; pass ``"nhl_id"`` for NHL stats ids, which ``"auto"`` never tries. |
| `strict` | `bool` | Raise ``UnresolvedTeamError`` when the plot is drawn and a value does not resolve, instead of drawing it in ``na_value`` with one ``SdvplotWarning``. |
| `na_value` | `str` | The color of values that are not teams; drawn as given, ``alpha`` does not fade it. |
| `alpha` | `float \| None` | An opacity in [0, 1] applied to the team colors (sdvplotR's ``alpha``, ``scales::alpha()``); ``None`` (the default) leaves them opaque. |
| `**kwargs` | `Any` | Passed to plotnine's ``scale_color_manual`` (``name``, ``breaks``, ``guide``, ...). |

### Returns

`scale` — A plotnine color scale.

### Raises

- `InputError`: (a ValueError) If ``which`` is not "primary" or "secondary" or ``alpha`` is not in [0, 1]; when the plot is drawn, if ``league`` or ``id_system`` is unknown or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `UnresolvedTeamError`: (a ValueError) With ``strict=True``, when the plot is drawn and a value does not resolve.

### Example

```python
import pandas as pd
from plotnine import aes, geom_point, ggplot
from sdvplot.plotnine import scale_color_sdv

df = pd.DataFrame({"team": ["KC", "BUF"], "epa": [0.2, 0.15], "sr": [0.48, 0.47]})
p = ggplot(df, aes("epa", "sr", color="team")) + geom_point() + scale_color_sdv("nfl")
```

### See also

- [sdvplotR scale_color_sdv()](https://sdvplotR.sportsdataverse.org/)
- sdvplot.plotnine.scale_fill_sdv: the fill scale

## scale_fill_sdv

<div class="sdv-signature">

```python
scale_fill_sdv(
    league: str,
    *,
    which: Literal['primary', 'secondary'] = 'primary',
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    na_value: str = 'grey',
    alpha: float | None = None,
    **kwargs: Any,
) -> Any
```

</div>

A discrete fill scale that maps each team value (any id system) to its team color.

### Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary". |
| `season` | `Any` | One season for every value. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of the team values: ``"auto"`` (the default) tries them in order; pass ``"nhl_id"`` for NHL stats ids, which ``"auto"`` never tries. |
| `strict` | `bool` | Raise ``UnresolvedTeamError`` when the plot is drawn and a value does not resolve, instead of drawing it in ``na_value`` with one ``SdvplotWarning``. |
| `na_value` | `str` | The color of values that are not teams; drawn as given, ``alpha`` does not fade it. |
| `alpha` | `float \| None` | An opacity in [0, 1] applied to the team colors (sdvplotR's ``alpha``, ``scales::alpha()``); ``None`` (the default) leaves them opaque. |
| `**kwargs` | `Any` | Passed to plotnine's ``scale_fill_manual``. |

### Returns

`scale` — A plotnine fill scale.

### Raises

- `InputError`: (a ValueError) If ``which`` is not "primary" or "secondary" or ``alpha`` is not in [0, 1]; when the plot is drawn, if ``league`` or ``id_system`` is unknown or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `UnresolvedTeamError`: (a ValueError) With ``strict=True``, when the plot is drawn and a value does not resolve.

### Example

```python
import pandas as pd
from plotnine import aes, geom_col, ggplot
from sdvplot.plotnine import scale_fill_sdv

df = pd.DataFrame({"team": ["KC", "BUF"], "epa": [0.2, 0.15]})
p = ggplot(df, aes("team", "epa", fill="team")) + geom_col() + scale_fill_sdv("nfl")
```

### See also

- [sdvplotR scale_fill_sdv()](https://sdvplotR.sportsdataverse.org/)
- sdvplot.plotnine.scale_color_sdv: the color scale

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
    variant: str = 'auto',
) -> plotnine.ggplot.ggplot
```

</div>

A tier list as a ggplot: each team's logo in its tier's row, tier 1 on top, on a dark (sdvplotR) or light theme.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | A pandas or polars DataFrame with ``tier_no`` (1 is the top tier) and ``team`` (any id system ``resolve()`` understands), and optionally ``tier_rank``, the position within the tier; without it, teams keep their order in ``data``. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `title` | `str \| None` | The title; None gives "{LEAGUE} Team Tiers", "" none. |
| `subtitle` | `str \| None` | The subtitle; None or "" for none. |
| `caption` | `str \| None` | The caption; None for none. |
| `tier_desc` | `dict[Any, str] \| None` | Each tier's label, keyed by tier number; None gives sdvplotR's (1 "Elite" ... 5 "What are they doing?"). Labels wrap at 15 characters; a tier without one gets none. |
| `presort` | `bool` | Sort teams alphabetically within each tier (ignores ``tier_rank``). |
| `alpha` | `float` | Logo opacity, 0 to 1. |
| `height` | `float \| None` | Logo height as a fraction of the panel height; None gives 0.1, about the largest height at which 32 logos in 5 tiers (7, 7, 6, 6, 6) neither overlap nor leave the panel at the default 6.4 x 4.8 in figure. |
| `no_line_below_tier` | `Any` | A tier number, or several, with no separator line below. |
| `devel` | `bool` | Draw each team as text instead of its logo (fast, and needs no download). |
| `theme` | `Literal['dark', 'light']` | "dark" (sdvplotR's: a near-black background) or "light" (white). |
| `variant` | `str` | The logo variant: "auto" (the default) draws the archive's "dark" variant, a mark made for dark backgrounds, on the dark theme and "default" on the light one; a team with no dark mark draws its default one, with no warning. Any other value ("default", "dark" or a named variant from ``marks()``) is drawn on either theme, as ``geom_sdv_logos`` draws it: ``variant="default"`` keeps the default logos on the dark theme, as sdvplotR and sdvplot 0.1.0 draw them. |

### Returns

`ggplot` — The plot; a team that does not resolve is skipped with one SdvplotWarning, keeping its slot.

### Raises

- `TypeError`: If ``data`` is not a DataFrame, or ``tier_no``/``tier_rank`` hold non-numbers.
- `InputError`: (a ValueError) If ``height``/``alpha`` is out of range, or ``league`` is unknown; unless ``devel=True``, when the plot is drawn, if ``variant`` is a name no mark in the archive has.
- `ValueError`: If ``data`` lacks ``tier_no`` or ``team``, has no row with a tier, or ``theme`` is not "dark" or "light".
- `OfflineError`: Unless ``devel=True``, when the plot is drawn, if the logo manifest or a logo is neither cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status; an IntegrityError for a file that does not match the manifest's sha256, or one PIL cannot decode).
- `UnsafeDownloadError`: (an OSError) Unless ``devel=True``, when the plot is drawn, if a download is refused.
- `UnsafeCachePathError`: (a ValueError) Unless ``devel=True``, when the plot is drawn, if the manifest's sha256 or extension for a logo would put the file outside the cache directory.
- `OptionalDependencyError`: Unless ``devel=True``, when the plot is drawn, if a logo is an SVG and the ``svg`` extra is not installed.

### Example

```python
import pandas as pd
from sdvplot.plotnine import team_tiers

df = pd.DataFrame({"tier_no": [1, 1, 2, 3], "team": ["KC", "BUF", "BAL", "NYJ"]})
p = team_tiers(df, "nfl", caption="data: nflverse")

# Draft it as text first:
p = team_tiers(df, "nfl", devel=True)

# A white background:
p = team_tiers(df, "cfb", theme="light")

# The default logos on the dark background, as sdvplotR draws them:
p = team_tiers(df, "nfl", variant="default")
```

### See also

- [sdvplotR sdv_team_tiers()](https://sdvplotR.sportsdataverse.org/reference/sdv_team_tiers.html)
- sdvplot.matplotlib.team_tiers: the same as a matplotlib Figure.

## title_image

<div class="sdv-signature">

```python
title_image(
    image: Any,
    title: str = '',
    *,
    league: str | None = None,
    season: Any = None,
    side: str = 'left',
    height: float = 15,
) -> Any
```

</div>

A plot title with an image (a team logo, or any image) beside it, added to a ggplot with ``+``.

The pair follows the theme's ``plot_title`` alignment, like the image inside sdvplotR's title: plotnine centres a
lone title and left-aligns one with a subtitle.

### Arguments

| Name | Type | Description |
|---|---|---|
| `image` | `Any` | A team, in any id system ``resolve()`` understands, when ``league`` is given; otherwise an image URL (https; http is refused) or a local file path. |
| `title` | `str` | The title text; it replaces ``labs(title=...)``, so add ``title_image`` after any ``labs``. |
| `league` | `str \| None` | The SDV league key, e.g. "nfl"; None reads ``image`` as a URL or path. |
| `season` | `Any` | One season, to pick the team's logo for that era. |
| `side` | `str` | "left" or "right" of the title text. |
| `height` | `float` | The image height in points (1/72 inch). The title keeps its own line height, so an image much taller than the text needs room: a ``plot_title`` margin in ``theme()``. |

### Returns

`object` — An object to add to a ggplot; the image is loaded now, and an unknown team, or an image by URL or path that cannot be read, gives one SdvplotWarning now (the title is drawn without the image). A second ``title_image`` added to the same plot replaces the first.

### Raises

- `TypeError`: If ``league`` is given and ``image`` is not one team.
- `InputError`: (a ValueError) If ``height`` is not a number of points of at least 1, or ``league`` is given and it is unknown or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If ``side`` is not "left"/"right".
- `OfflineError`: If ``league`` is given and the team's logo (or the logo manifest) is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode). An image by URL or path that cannot be read is skipped with a warning instead.
- `UnsafeDownloadError`: (an OSError) If ``league`` is given and a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``league`` is given and the manifest's sha256 or extension for the logo would put the file outside the cache directory.
- `OptionalDependencyError`: If ``league`` is given, the logo is an SVG and the ``svg`` extra is not installed.

### Example

```python
import pandas as pd
from plotnine import aes, geom_point, ggplot
from sdvplot.plotnine import title_image

df = pd.DataFrame({"epa": [0.2, 0.15], "sr": [0.48, 0.47]})
p = ggplot(df, aes("epa", "sr")) + geom_point() + title_image("KC", "Chiefs", league="nfl", height=20)
```

### See also

- [sdvplotR ggtitle_image()](https://sdvplotR.sportsdataverse.org/reference/ggtitle_image.html)
- sdvplot.matplotlib.title_image: the same for matplotlib.

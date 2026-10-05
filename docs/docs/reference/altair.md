---
title: sdvplot.altair
sidebar_label: sdvplot.altair
sidebar_position: 19
---

# sdvplot.altair

The Altair adapter: logos, wordmarks and headshots as a native Vega-Lite image layer.

| Name | What it is |
|---|---|
| [add_headshots](#add_headshots) | Layer each player's headshot, centred on its (x, y) point, onto an Altair chart. |
| [add_logos](#add_logos) | Layer each team's logo, centred on its (x, y) point, onto an Altair chart. |
| [add_wordmarks](#add_wordmarks) | Layer each team's wordmark, centred on its (x, y) point, onto an Altair chart. |
| [axis_logos](#axis_logos) | Replace a discrete axis' team labels with the teams' logos (or wordmarks). |
| [logo_layer](#logo_layer) | A Vega-Lite image layer of team logos, to layer onto a chart: ``alt.layer(chart, logo_layer(...))``. |

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
) -> altair.vegalite.v6.api.LayerChart
```

</div>

Layer each player's headshot, centred on its (x, y) point, onto an Altair chart.

### Arguments

| Name | Type | Description |
|---|---|---|
| `chart` | `Any` | An ``altair.Chart`` or ``LayerChart``. |
| `x` | `Any` | The points' x positions, in the chart's x values. |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `players` | `Any` | The player id for each point. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `float` | The headshot height as a fraction of the chart height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``. |

### Returns

`altair.LayerChart` — A new chart, ``chart`` plus the image layer.

### Raises

- `ValueError`: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or the chart cannot take a layer (see ``add_logos``).
- `TypeError`: If the target is not an Altair ``Chart`` or ``LayerChart``.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

### Example

```python
import altair as alt
import pandas as pd
import sdvplot

df = pd.DataFrame({"x": [0.3], "y": [0.5], "player": ["3139477"]})
chart = alt.Chart(df).mark_point().encode(x="x", y="y")
sdvplot.add_headshots(chart, df["x"], df["y"], df["player"], league="nfl", height=0.2)
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
) -> altair.vegalite.v6.api.LayerChart
```

</div>

Layer each team's logo, centred on its (x, y) point, onto an Altair chart.

The image layer reuses the chart's x/y field names, types, time units and sort, so a nominal axis stays nominal,
a logo on ``yearmonth(date)`` sits on its month, and the axis titles stay as they were. An aggregated or binned
axis is not copied: aggregate or bin in the data first.

### Arguments

| Name | Type | Description |
|---|---|---|
| `chart` | `Any` | An ``altair.Chart`` or ``LayerChart`` (facet, concat and repeat charts: pass one of their charts). |
| `x` | `Any` | The points' x positions, in the chart's x values. |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point, to pick each team's mark for that era. |
| `height` | `float` | The logo height as a fraction of the chart height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`altair.LayerChart` — A new chart, ``chart`` plus the image layer (``chart`` itself is unchanged).

### Raises

- `ValueError`: If ``height`` or ``alpha`` is out of range, the inputs differ in length, the chart is a facet, concat or repeat chart, its height is not a positive number of pixels where it must be, its x or y encoding aggregates or bins, or a discrete axis is sorted in a way Vega-Lite drops once layers share the axis.
- `TypeError`: If the target is not an Altair ``Chart`` or ``LayerChart``.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

### Example

```python
import altair as alt
import pandas as pd
import sdvplot

df = pd.DataFrame({"epa": [0.2, 0.1], "sr": [0.48, 0.45], "team": ["KC", "BUF"]})
chart = alt.Chart(df).mark_point().encode(x="epa", y="sr")
chart = sdvplot.add_logos(chart, df["epa"], df["sr"], df["team"], league="nfl", height=0.12)
```

### See also

- [sdvplotR geom_nfl_logos()](https://sdvplotR.sportsdataverse.org/)

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
) -> altair.vegalite.v6.api.LayerChart
```

</div>

Layer each team's wordmark, centred on its (x, y) point, onto an Altair chart.

### Arguments

| Name | Type | Description |
|---|---|---|
| `chart` | `Any` | An ``altair.Chart`` or ``LayerChart``. |
| `x` | `Any` | The points' x positions, in the chart's x values. |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point. |
| `height` | `float` | The wordmark height as a fraction of the chart height, in (0, 1]. |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`altair.LayerChart` — A new chart, ``chart`` plus the image layer.

### Raises

- `ValueError`: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or the chart cannot take a layer (see ``add_logos``).
- `TypeError`: If the target is not an Altair ``Chart`` or ``LayerChart``.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

### Example

```python
import altair as alt
import pandas as pd
import sdvplot

df = pd.DataFrame({"team": ["KC", "BUF"], "wins": [12, 10]})
bars = alt.Chart(df).mark_bar().encode(x=alt.X("team", sort=None), y="wins")
sdvplot.add_wordmarks(bars, df["team"], df["wins"], df["team"], league="nfl", height=0.06)
```

### See also

- [sdvplotR geom_nfl_wordmarks()](https://sdvplotR.sportsdataverse.org/)

## axis_logos

<div class="sdv-signature">

```python
axis_logos(
    chart: Any,
    axis: str,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    variant: str = 'default',
    mark_type: str = 'logo',
    embed: bool = False,
    id_system: str = 'auto',
) -> altair.vegalite.v6.api.LayerChart
```

</div>

Replace a discrete axis' team labels with the teams' logos (or wordmarks).

The images are a layer placed just outside the plot (under the x axis, left of the y axis), ``height`` of the chart
height tall; the axis' ``labelExpr`` blanks only the labels that became images and its ``labelPadding`` grows past
them, so labels that are not teams stay as text (with one SdvplotWarning). The categories come from an explicit
scale domain or sort list, or the chart's inline data.

### Arguments

| Name | Type | Description |
|---|---|---|
| `chart` | `Any` | An ``altair.Chart`` or ``LayerChart`` with a nominal or ordinal ``axis``. |
| `axis` | `str` | "x" or "y". |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season for every label. |
| `height` | `float` | The image height as a fraction of the chart height, in (0, 1]. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `mark_type` | `str` | "logo" or "wordmark". |
| `embed` | `bool` | Inline each image as a data URI instead of linking its URL. |
| `id_system` | `str` | The id system of the labels; "auto" tries each in order. |

### Returns

`altair.LayerChart` — A new chart: ``chart`` with the axis labels blanked, plus the image layer.

### Raises

- `ValueError`: If ``axis`` is not "x"/"y", ``height`` is out of range, the axis is not discrete or is hidden, the categories cannot be read, or the chart cannot take a layer (see ``add_logos``).
- `TypeError`: If the target is not an Altair ``Chart`` or ``LayerChart``.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

### Example

```python
import altair as alt
import pandas as pd
import sdvplot

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [12, 10, 9]})
bars = alt.Chart(df).mark_bar().encode(x=alt.X("team", sort=None), y="wins")
sdvplot.axis_logos(bars, "x", league="nfl", height=0.1)
```

### See also

- [sdvplotR element_sdv_logo()](https://sdvplotR.sportsdataverse.org/)

## logo_layer

<div class="sdv-signature">

```python
logo_layer(
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    chart_height: float | None = None,
    alpha: float = 1,
    variant: str = 'default',
    x_type: str = 'quantitative',
    y_type: str = 'quantitative',
    embed: bool = False,
    id_system: str = 'auto',
) -> altair.vegalite.v6.api.Chart
```

</div>

A Vega-Lite image layer of team logos, to layer onto a chart: ``alt.layer(chart, logo_layer(...))``.

The layer encodes its own columns named ``x`` and ``y``, so give your chart explicit axis titles (an explicit title
wins over the layer's), or use ``add_logos``, which reuses the chart's own field names, types and sort.

### Arguments

| Name | Type | Description |
|---|---|---|
| `x` | `Any` | The points' x positions, in the chart's x values (numbers, category names or dates). |
| `y` | `Any` | The points' y positions, the same length as ``x``. |
| `teams` | `Any` | The team for each point, in any id system ``resolve()`` understands. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | One season, or one per point, to pick each team's mark for that era. |
| `height` | `float` | The logo height as a fraction of the chart height, in (0, 1]. |
| `chart_height` | `float \| None` | The chart's height in pixels (a positive number); None means Vega-Lite's default (300). |
| `alpha` | `float` | Opacity, 0 to 1. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `x_type` | `str` | The Vega-Lite type of the chart's x axis ("quantitative", "nominal", "ordinal", "temporal"). |
| `y_type` | `str` | The Vega-Lite type of the chart's y axis. |
| `embed` | `bool` | Inline each image as a data URI (HTML that renders offline, and PNG export with vl-convert) instead of linking its URL. |
| `id_system` | `str` | The id system of ``teams``; "auto" tries each in order. |

### Returns

`altair.Chart` — The image layer.

### Raises

- `ValueError`: If ``height`` or ``alpha`` is out of range, ``chart_height`` is not a positive number of pixels, or the inputs differ in length.
- `OfflineError`: If ``embed=True`` and an image is neither cached nor downloadable.

### Example

```python
import altair as alt
import pandas as pd
import sdvplot.altair as salt

df = pd.DataFrame({"x": [10, 20], "y": [-3, -7], "team": ["KC", "BUF"]})
points = alt.Chart(df).mark_point().encode(x=alt.X("x", title="EPA"), y=alt.Y("y", title="Success"))
alt.layer(points, salt.logo_layer(df["x"], df["y"], df["team"], league="nfl", height=0.12))
```

### See also

- [sdvplotR geom_nfl_logos()](https://sdvplotR.sportsdataverse.org/)
- [Altair image marks](https://altair-viz.github.io/user_guide/marks/image.html)

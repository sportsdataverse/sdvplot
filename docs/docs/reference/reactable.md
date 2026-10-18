---
title: sdvplot.reactable
sidebar_label: sdvplot.reactable
sidebar_position: 26
---

# sdvplot.reactable

reactable-py columns (``pip install sdvplot[reactable]``), ported from sdvplotR's ``reactable_sdv_*`` functions.

| Name | What it is |
|---|---|
| [reactable_sdv_cols_label](#reactable_sdv_cols_label) | One reactable column per team-named column of ``data`` (a ``KC`` column, a ``BUF`` column, ...), its header |
| [reactable_sdv_gauge](#reactable_sdv_gauge) | A reactable column that draws each cell's number as a half-circle gauge (an inline SVG) with the value inside. |
| [reactable_sdv_headshots](#reactable_sdv_headshots) | A reactable column that shows each cell's player id as the player's headshot. |
| [reactable_sdv_logos](#reactable_sdv_logos) | A reactable column that shows each cell's team as its logo. |
| [reactable_sdv_sparkbar](#reactable_sdv_sparkbar) | A reactable column that draws each cell's list of numbers as a small bar chart (an inline SVG). |
| [reactable_sdv_sparkline](#reactable_sdv_sparkline) | A reactable column that draws each cell's list of numbers as a sparkline (an inline SVG). |
| [reactable_sdv_team_color_bar](#reactable_sdv_team_color_bar) | A reactable column whose cells hold a bar in the row's team color, as long as the value's share of the maximum. |
| [reactable_sdv_team_color_bg](#reactable_sdv_team_color_bg) | A reactable column whose cells are filled with the row's team color, mostly transparent. |
| [reactable_sdv_wordmarks](#reactable_sdv_wordmarks) | A reactable column that shows each cell's team as its wordmark. |

## reactable_sdv_cols_label

<div class="sdv-signature">

```python
reactable_sdv_cols_label(
    data: Any,
    *,
    league: str,
    variant: str = 'default',
    height: Any = 30,
    season: Any = None,
    mark_type: str = 'logo',
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    **column_kwargs: Any,
) -> list[reactable.models.Column]
```

</div>

One reactable column per team-named column of ``data`` (a ``KC`` column, a ``BUF`` column, ...), its header

the team's mark.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable``. Pass only the team-named columns (``df[["KC", "BUF"]]``) to avoid a warning for the others. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `height` | `Any` | The image height in pixels. |
| `season` | `Any` | One season whose marks to show; None for today's. |
| `mark_type` | `str` | "logo" or "wordmark". |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of the column names, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a column name does not resolve. |
| `**column_kwargs` | `Any` | Passed to every ``reactable.Column``. |

### Returns

`list[reactable.Column]` — A column (``id`` = the column name, an empty ``name``, the mark as ``header``) for each column whose name resolves; the others are left out, with one SdvplotWarning.

### Raises

- `InputError`: (a ValueError) If ``mark_type`` is not "logo"/"wordmark", ``height`` is not a number of pixels of at least 1, ``league``, ``id_system`` or ``variant`` is unknown, or ``season`` is not one year or is outside the seasons sdvplot knows for the league.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a column name does not resolve.
- `OfflineError`: If the logo manifest cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, when the CDN answers with an error status).
- `UnsafeDownloadError`: (an OSError) If the manifest download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_cols_label

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Reactable(df, columns=reactable_sdv_cols_label(df, league="nfl"))
```

### See also

- [Ported from sdvplotR ``reactable_sdv_cols_label()``](https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_cols_label.html)

## reactable_sdv_gauge

<div class="sdv-signature">

```python
reactable_sdv_gauge(
    data: Any,
    *,
    fill_color: str | collections.abc.Sequence[str] | None = None,
    background: str = '#EEEEEE',
    team_col: str | None = None,
    league: str | None = None,
    which: Literal['primary', 'secondary'] = 'primary',
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    na_color: str = '#b3b3b3',
    min_value: float | None = None,
    max_value: float | None = None,
    show_min_max: bool = False,
    number_fmt: collections.abc.Callable[[float], str] | str | None = None,
    size: float = 1,
    text_color: str | None = None,
    bold_text: bool = False,
    text_size: str | None = None,
    bias: float = 1,
    opacity: float = 1,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column that draws each cell's number as a half-circle gauge (an inline SVG) with the value inside.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable``: the gauged column's range (for the default scale and the color ramp) and ``team_col`` are read from it. |
| `fill_color` | `str \| collections.abc.Sequence[str] \| None` | The gauge's CSS color, or several hex colors to ramp through from the column's smallest value to its largest (as reactablefmtr); None for reactablefmtr's "#15607A" (or the row's team color). |
| `background` | `str` | The color of the gauge's unfilled track. |
| `team_col` | `str \| None` | A column of ``data`` holding each row's team: the gauge takes that team's color. |
| `league` | `str \| None` | The SDV league key of ``team_col``'s teams, e.g. "nhl"; required with ``team_col``. |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary" team color. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team_col``, as in ``resolve``. |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |
| `na_color` | `str` | The color for teams that do not resolve or have no color. |
| `min_value` | `float \| None` | The value of an empty gauge; None for 0. |
| `max_value` | `float \| None` | The value of a full gauge; None for the column's largest absolute value. |
| `show_min_max` | `bool` | Print the scale's two ends under the gauge. |
| `number_fmt` | `collections.abc.Callable[[float], str] \| str \| None` | How to print the value (and the ends): a function such as ``"{:.1%}".format``, or a format spec such as ``".3f"``; None prints the number as is. |
| `size` | `float` | The gauge's scale: 1 is 50 pixels wide (reactablefmtr's ``size = 1``), 2 is 100. |
| `text_color` | `str \| None` | The value's color; None for the cell's text color. |
| `bold_text` | `bool` | Print the value in bold. |
| `text_size` | `str \| None` | The value's CSS font size; None for the cell's. |
| `bias` | `float` | The ramp's spacing (grDevices::colorRamp's ``bias``): above 1 spreads the colors toward the high end. |
| `opacity` | `float` | The fill's opacity, 0 to 1. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column`` (``id`` is required by reactable). |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer; each gauge is an ``<svg role="img">`` whose ``aria-label`` gives the value and the scale. A missing value is left blank; text passes through.

### Raises

- `InputError`: (a ValueError) If ``size`` or ``bias`` is not a positive number, ``opacity`` is outside [0, 1], ``min_value``/``max_value`` is not a finite number, ``fill_color`` holds several colors that are not hex colors, or ``team_col`` is given without ``league``; if ``league``, ``id_system`` or ``which`` is unknown.
- `ValueError`: If ``team_col`` is not a column of ``data``.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

### Example

```python
import polars as pl
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_gauge

df = pl.DataFrame({"team": ["BOS", "TOR", "FLA"], "save_pct": [0.915, 0.902, 0.908]})
Reactable(df, columns=[reactable_sdv_gauge(df, id="save_pct", team_col="team", league="nhl",
                                           min_value=0.88, max_value=0.93, number_fmt=".3f")])
```

### See also

- Equivalent of reactablefmtr::gauge_chart (an SVG arc rather than nested divs, so the value sits on the cell's own background in any theme
- the "min" end reads the scale's real lower bound).

## reactable_sdv_headshots

<div class="sdv-signature">

```python
reactable_sdv_headshots(
    *,
    league: str,
    height: Any = 40,
    default_img: str | None = None,
    id_system: str = 'espn',
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column that shows each cell's player id as the player's headshot.

### Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `Any` | The image height in pixels. |
| `default_img` | `str \| None` | An image URL for ids without a headshot; None keeps their text. |
| `id_system` | `str` | "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column`` (``id`` is required by reactable). |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `InputError`: (a ValueError) If ``height`` is not a number of pixels of at least 1; when the ``Reactable`` is built, if ``league`` has no ESPN headshots or ``id_system`` is not valid for ``league``.
- `OfflineError`: When the ``Reactable`` is built, if ``id_system`` is "gsis" and the nflverse player table cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, for an HTTP error status).
- `UnsafeDownloadError`: (an OSError) When the ``Reactable`` is built, if ``id_system`` is "gsis" and the player table download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_headshots

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Reactable(df, columns=[reactable_sdv_headshots(league="nfl", id="espn_id", name="")])
```

### See also

- [Ported from sdvplotR ``reactable_sdv_headshots()``](https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_images.html)

## reactable_sdv_logos

<div class="sdv-signature">

```python
reactable_sdv_logos(
    *,
    league: str,
    variant: str = 'default',
    height: Any = 30,
    default_img: str | None = None,
    season: Any = None,
    include_name: bool = False,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column that shows each cell's team as its logo.

### Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `height` | `Any` | The image height in pixels. |
| `default_img` | `str \| None` | An image URL for values that do not resolve; None keeps their text. |
| `season` | `Any` | One season whose marks every cell shows; None for today's. |
| `include_name` | `bool` | Keep the cell's text after the logo. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of the column's values, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError (when the ``Reactable`` is built) instead of warning when a value does not resolve. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``: ``id`` (the data column, required by reactable), ``name``, ``width``, ... |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `InputError`: (a ValueError) If ``height`` is not a number of pixels of at least 1, or ``season`` is not one year or is outside the seasons sdvplot knows for the league; when the ``Reactable`` is built, if ``league``, ``id_system`` or ``variant`` is unknown.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a value does not resolve, when the ``Reactable`` is built.
- `OfflineError`: When the ``Reactable`` is built, if the logo manifest cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, when the CDN answers with an error status).
- `UnsafeDownloadError`: (an OSError) When the ``Reactable`` is built, if the manifest download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_logos
import pandas as pd

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Reactable(df, columns=[reactable_sdv_logos(league="nfl", id="team", name="")])
```

### See also

- [Ported from sdvplotR ``reactable_sdv_logos()``](https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_images.html)

## reactable_sdv_sparkbar

<div class="sdv-signature">

```python
reactable_sdv_sparkbar(
    data: Any,
    *,
    fill_color: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Literal['primary', 'secondary'] = 'primary',
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    na_color: str = '#b3b3b3',
    fill_opacity: float = 1,
    highlight_bars: collections.abc.Sequence[str] | collections.abc.Mapping[str, str] = (),
    statline: str | None = None,
    statline_color: str = 'red',
    statline_label_size: str = '0.8em',
    bandline: str | None = None,
    bandline_color: str = 'red',
    bandline_opacity: float = 0.2,
    labels: collections.abc.Sequence[str] | str = (),
    label_size: str = '0.8em',
    decimals: int = 0,
    min_value: float | None = None,
    max_value: float | None = None,
    height: float = 22,
    width: float | None = None,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column that draws each cell's list of numbers as a small bar chart (an inline SVG).

Bars stand on zero: positive values rise from it, negative ones hang below it.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable``; read only for ``team_col``. The column itself holds one list per row; a missing entry leaves a gap, an empty, missing or non-list cell is left blank. |
| `fill_color` | `str \| None` | The bars' CSS color; None for reactablefmtr's "slategray" (or the row's team color). |
| `team_col` | `str \| None` | A column of ``data`` holding each row's team: the bars take that team's color. |
| `league` | `str \| None` | The SDV league key of ``team_col``'s teams, e.g. "wnba"; required with ``team_col``. |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary" team color. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team_col``, as in ``resolve``. |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |
| `na_color` | `str` | The color for teams that do not resolve or have no color. |
| `fill_opacity` | `float` | The bars' opacity, 0 to 1. |
| `highlight_bars` | `collections.abc.Sequence[str] \| collections.abc.Mapping[str, str]` | Bars to recolor: a mapping such as ``{"max": "gold"}`` (reactablefmtr's ``highlight_bars(max = "gold")``), or a sequence of "first", "last", "min", "max" drawn in red. |
| `statline` | `str \| None` | A dashed reference line at the series' "mean", "median", "min" or "max", labeled at its right. |
| `statline_color` | `str` | The reference line's and its label's color. |
| `statline_label_size` | `str` | The reference line label's CSS font size. |
| `bandline` | `str \| None` | A shaded band across the series' "innerquartiles" or "range". |
| `bandline_color` | `str` | The band's color. |
| `bandline_opacity` | `float` | The band's opacity, 0 to 1. |
| `labels` | `collections.abc.Sequence[str] \| str` | Values to print above their bars: "first", "last", "min", "max" or "all". |
| `label_size` | `str` | The labels' CSS font size. |
| `decimals` | `int` | Decimal places of the labels and the statline label. |
| `min_value` | `float \| None` | The value at the bottom of every cell's chart; None for the lower of 0 and the series' minimum. |
| `max_value` | `float \| None` | The value at the top of every cell's chart; None for the higher of 0 and the series' maximum. |
| `height` | `float` | The chart's height in pixels. |
| `width` | `float \| None` | The chart's width in pixels; None for 100. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column`` (``id`` is required by reactable). |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer; each chart is an ``<svg role="img">`` whose ``aria-label`` gives the number of bars, the minimum, the maximum and the last value.

### Raises

- `InputError`: (a ValueError) As ``reactable_sdv_sparkline``: a bad pixel size, opacity, option name, decimals or bound, or ``team_col`` without ``league``; if ``league``, ``id_system`` or ``which`` is unknown.
- `ValueError`: If ``team_col`` is not a column of ``data``.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_sparkbar

df = pd.DataFrame({"team": ["LV", "NY"], "pts": [[88, 95, 79, 101], [92, 85, 99, 90]]})
Reactable(df, columns=[reactable_sdv_sparkbar(df, id="pts", team_col="team", league="wnba",
                                              highlight_bars={"max": "gold"})])
```

### See also

- Equivalent of reactablefmtr::react_sparkbar (drawn without dataui: no hover tooltips per bar, bars rooted at zero so the smallest bar still shows).

## reactable_sdv_sparkline

<div class="sdv-signature">

```python
reactable_sdv_sparkline(
    data: Any,
    *,
    line_color: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Literal['primary', 'secondary'] = 'primary',
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    na_color: str = '#b3b3b3',
    line_width: float = 1.5,
    show_area: bool = False,
    area_color: str | None = None,
    area_opacity: float = 0.1,
    highlight_points: collections.abc.Sequence[str] | collections.abc.Mapping[str, str] = (),
    point_size: float = 1.5,
    statline: str | None = None,
    statline_color: str = 'red',
    statline_label_size: str = '0.8em',
    bandline: str | None = None,
    bandline_color: str = 'red',
    bandline_opacity: float = 0.2,
    labels: collections.abc.Sequence[str] | str = (),
    label_size: str = '0.8em',
    decimals: int = 0,
    min_value: float | None = None,
    max_value: float | None = None,
    height: float = 22,
    width: float | None = None,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column that draws each cell's list of numbers as a sparkline (an inline SVG).

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable``; read only for ``team_col``. The column itself holds one list per row (a polars ``List`` column, or a pandas column of lists); a missing entry breaks the line, an empty, missing or non-list cell is left blank. |
| `line_color` | `str \| None` | The line's CSS color; None for reactablefmtr's "slategray" (or the row's team color). |
| `team_col` | `str \| None` | A column of ``data`` holding each row's team: the line (and area) take that team's color. |
| `league` | `str \| None` | The SDV league key of ``team_col``'s teams, e.g. "nba"; required with ``team_col``. |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary" team color. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team_col``, as in ``resolve``. |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |
| `na_color` | `str` | The color for teams that do not resolve or have no color. |
| `line_width` | `float` | The line's stroke width in pixels. |
| `show_area` | `bool` | Fill the area under the line. |
| `area_color` | `str \| None` | The area's color; None for the line's. |
| `area_opacity` | `float` | The area's opacity, 0 to 1. |
| `highlight_points` | `collections.abc.Sequence[str] \| collections.abc.Mapping[str, str]` | Points to mark: a mapping such as ``{"min": "red", "max": "blue"}`` (reactablefmtr's ``highlight_points(min = "red", max = "blue")``), or a sequence of names drawn in red. Names are "first", "last", "min", "max" and "all". |
| `point_size` | `float` | The radius of a highlighted point, in pixels. |
| `statline` | `str \| None` | A dashed reference line at the series' "mean", "median", "min" or "max", labeled at its right. |
| `statline_color` | `str` | The reference line's and its label's color. |
| `statline_label_size` | `str` | The reference line label's CSS font size. |
| `bandline` | `str \| None` | A shaded band across the series' "innerquartiles" (25th to 75th percentile) or "range". |
| `bandline_color` | `str` | The band's color. |
| `bandline_opacity` | `float` | The band's opacity, 0 to 1. |
| `labels` | `collections.abc.Sequence[str] \| str` | Values to print by their point: names as for ``highlight_points`` ("all" labels every point). |
| `label_size` | `str` | The labels' CSS font size. |
| `decimals` | `int` | Decimal places of the labels and the statline label. |
| `min_value` | `float \| None` | The value at the bottom of every cell's chart; None for each series' own minimum. |
| `max_value` | `float \| None` | The value at the top of every cell's chart; None for each series' own maximum. |
| `height` | `float` | The chart's height in pixels; the default 22 grows to 28 or 30 to make room for labels above the points, as in reactablefmtr. |
| `width` | `float \| None` | The chart's width in pixels; None for 100. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column`` (``id`` is required by reactable). |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer. Each chart is an ``<svg role="img">`` whose ``aria-label`` (and ``<title>`` tooltip) gives the number of points, the minimum, the maximum and the last value.

### Raises

- `InputError`: (a ValueError) If ``height``/``width`` is not a number of pixels of at least 1, an opacity is outside [0, 1], ``statline``/``bandline``/``labels``/``highlight_points`` names an unknown option, ``decimals`` is not a whole number, ``min_value``/``max_value`` is not a finite number, or ``team_col`` is given without ``league``; if ``league``, ``id_system`` or ``which`` is unknown.
- `ValueError`: If ``team_col`` is not a column of ``data``.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

### Example

```python
import polars as pl
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_sparkline

df = pl.DataFrame({"team": ["BOS", "NY"], "margin": [[12, -4, 8, 21], [3, 7, -10, 5]]})
Reactable(
    df,
    columns=[
        reactable_sdv_sparkline(df, id="margin", team_col="team", league="nba",
                                highlight_points={"min": "red", "max": "blue"}, statline="mean"),
    ],
)
```

### See also

- Equivalent of reactablefmtr::react_sparkline (drawn without dataui: no hover tooltips per point, a solid rather than hatched band, straight rather than cardinal-curve segments).

## reactable_sdv_team_color_bar

<div class="sdv-signature">

```python
reactable_sdv_team_color_bar(
    data: Any,
    team_col: str,
    *,
    league: str,
    which: Literal['primary', 'secondary'] = 'primary',
    max_value: float | None = None,
    na_color: str = '#b3b3b3',
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column whose cells hold a bar in the row's team color, as long as the value's share of the maximum.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable`` (each row's team is read from it). |
| `team_col` | `str` | The column of ``data`` holding the teams. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary" team color. |
| `max_value` | `float \| None` | The value that fills the whole cell; None for the column's maximum. |
| `na_color` | `str` | The CSS color for teams that do not resolve or have no color. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team_col``, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the styled column. |

### Returns

`reactable.Column` — The column, with a ``style`` function.

### Raises

- `InputError`: (a ValueError) If ``league`` or ``id_system`` is unknown, or ``which`` is not "primary"/"secondary".
- `ValueError`: If ``team_col`` is not a column of ``data``.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_team_color_bar

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Reactable(df, columns=[reactable_sdv_team_color_bar(df, "team", league="nfl", id="wins")])
```

### See also

- [Ported from sdvplotR ``reactable_sdv_team_color_bar()``](https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_team_color.html)

## reactable_sdv_team_color_bg

<div class="sdv-signature">

```python
reactable_sdv_team_color_bg(
    data: Any,
    team_col: str,
    *,
    league: str,
    which: Literal['primary', 'secondary'] = 'primary',
    alpha: float = 0.15,
    na_color: str = '#b3b3b3',
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column whose cells are filled with the row's team color, mostly transparent.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable`` (each row's team is read from it). |
| `team_col` | `str` | The column of ``data`` holding the teams. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary" team color. |
| `alpha` | `float` | The fill's opacity, 0 to 1. |
| `na_color` | `str` | The hex color for teams that do not resolve or have no color. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team_col``, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the styled column. |

### Returns

`reactable.Column` — The column, with a ``style`` function.

### Raises

- `InputError`: (a ValueError) If ``alpha`` is outside [0, 1], ``league`` or ``id_system`` is unknown, or ``which`` is not "primary"/"secondary".
- `ValueError`: If ``team_col`` is not a column of ``data``, or ``na_color`` is not a hex color.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_team_color_bg

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Reactable(df, columns=[reactable_sdv_team_color_bg(df, "team", league="nfl", id="team")])
```

### See also

- [Ported from sdvplotR ``reactable_sdv_team_color_bg()``](https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_team_color.html)

## reactable_sdv_wordmarks

<div class="sdv-signature">

```python
reactable_sdv_wordmarks(
    *,
    league: str,
    variant: str = 'default',
    height: Any = 30,
    default_img: str | None = None,
    season: Any = None,
    include_name: bool = False,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column that shows each cell's team as its wordmark.

### Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `height` | `Any` | The image height in pixels. |
| `default_img` | `str \| None` | An image URL for values that do not resolve; None keeps their text. |
| `season` | `Any` | One season whose marks every cell shows; None for today's. |
| `include_name` | `bool` | Keep the cell's text after the wordmark. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of the column's values, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError (when the ``Reactable`` is built) instead of warning when a value does not resolve. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column`` (``id`` is required by reactable). |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `InputError`: (a ValueError) If ``height`` is not a number of pixels of at least 1, or ``season`` is not one year or is outside the seasons sdvplot knows for the league; when the ``Reactable`` is built, if ``league``, ``id_system`` or ``variant`` is unknown.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a value does not resolve, when the ``Reactable`` is built.
- `OfflineError`: When the ``Reactable`` is built, if the logo manifest cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, when the CDN answers with an error status).
- `UnsafeDownloadError`: (an OSError) When the ``Reactable`` is built, if the manifest download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_wordmarks

df = pd.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

Reactable(df, columns=[reactable_sdv_wordmarks(league="nfl", id="team")])
```

### See also

- [Ported from sdvplotR ``reactable_sdv_wordmarks()``](https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_images.html)

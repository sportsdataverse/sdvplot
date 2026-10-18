---
title: sdvplot.reactable
sidebar_label: sdvplot.reactable
sidebar_position: 26
---

# sdvplot.reactable

reactable-py columns (``pip install sdvplot[reactable]``), ported from sdvplotR's ``reactable_sdv_*`` functions, plus reactablefmtr's cell formatters (data bars, color tiles and scales, pills, icons, merged columns, highlights, bubbles).

| Name | What it is |
|---|---|
| [reactable_sdv_bubble_grid](#reactable_sdv_bubble_grid) | A reactable column of circles (or squares) sized and colored by value, by a color column, or by team. |
| [reactable_sdv_color_scales](#reactable_sdv_color_scales) | A reactable column whose cell backgrounds are filled on a color scale, by a color column, or in team colors. |
| [reactable_sdv_color_tiles](#reactable_sdv_color_tiles) | A reactable column of rounded tiles filled on a color scale, by a color column, or in the row's team color. |
| [reactable_sdv_cols_label](#reactable_sdv_cols_label) | One reactable column per team-named column of ``data`` (a ``KC`` column, a ``BUF`` column, ...), its header |
| [reactable_sdv_data_bars](#reactable_sdv_data_bars) | A reactable column of horizontal bars sized by value, in a scale color, a color column or the team color. |
| [reactable_sdv_gauge](#reactable_sdv_gauge) | A reactable column that draws each cell's number as a half-circle gauge (an inline SVG) with the value inside. |
| [reactable_sdv_headshots](#reactable_sdv_headshots) | A reactable column that shows each cell's player id as the player's headshot. |
| [reactable_sdv_highlight](#reactable_sdv_highlight) | A reactable column whose highest (or lowest, or both) values are bold, in a color, optionally on a highlight. |
| [reactable_sdv_icon_assign](#reactable_sdv_icon_assign) | A reactable column that repeats an icon, filled up to the value: a rating in stars, a count in dots. |
| [reactable_sdv_icon_sets](#reactable_sdv_icon_sets) | A reactable column that puts an icon beside each number, chosen by the value's quantile bucket. |
| [reactable_sdv_icon_trend](#reactable_sdv_icon_trend) | A reactable column that marks each change with an up arrow, a down arrow or a dash, the value colored to match. |
| [reactable_sdv_logos](#reactable_sdv_logos) | A reactable column that shows each cell's team as its logo. |
| [reactable_sdv_merge_column](#reactable_sdv_merge_column) | A reactable column that shows a second column's value beside or below each value, after an optional mark. |
| [reactable_sdv_pill_buttons](#reactable_sdv_pill_buttons) | A reactable column whose values sit in rounded pills, in a scale color, a color column or the team color. |
| [reactable_sdv_sparkbar](#reactable_sdv_sparkbar) | A reactable column that draws each cell's list of numbers as a small bar chart (an inline SVG). |
| [reactable_sdv_sparkline](#reactable_sdv_sparkline) | A reactable column that draws each cell's list of numbers as a sparkline (an inline SVG). |
| [reactable_sdv_team_color_bar](#reactable_sdv_team_color_bar) | A reactable column whose cells hold a bar in the row's team color, as long as the value's share of the maximum. |
| [reactable_sdv_team_color_bg](#reactable_sdv_team_color_bg) | A reactable column whose cells are filled with the row's team color, mostly transparent. |
| [reactable_sdv_wordmarks](#reactable_sdv_wordmarks) | A reactable column that shows each cell's team as its wordmark. |

## reactable_sdv_bubble_grid

<div class="sdv-signature">

```python
reactable_sdv_bubble_grid(
    data: Any,
    *,
    shape: Literal['circles', 'squares'] = 'circles',
    colors: collections.abc.Sequence[str] = ('#15607A', '#FFFFFF', '#FA8C00'),
    color_ref: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Literal['primary', 'secondary'] = 'primary',
    color_by: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    opacity: float = 1,
    bias: float = 1,
    number_fmt: collections.abc.Callable[[Any], str] | str | None = None,
    text_color: str | None = None,
    brighten_text: bool = True,
    show_text: bool = True,
    bold_text: bool = False,
    box_shadow: bool = False,
    tooltip: bool = False,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column of circles (or squares) sized and colored by value, by a color column, or by team.

A bubble is the value's share of the column's largest magnitude, up to 100 pixels across.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable`` (ranges and per-row colors are read from it). |
| `shape` | `Literal['circles', 'squares']` | "circles" or "squares". |
| `colors` | `collections.abc.Sequence[str]` | Hex colors forming the scale from the column's minimum to its maximum. |
| `color_ref` | `str \| None` | A column of ``data`` holding each row's bubble color: hex, a CSS color name, or rgb()/hsl(); any other value is warned about once and that row keeps the scale color. |
| `team_col` | `str \| None` | A column of team values; each bubble takes that team's color (``which``). Teams that do not resolve keep the scale color. |
| `league` | `str \| None` | The SDV league key, e.g. "nfl"; needed by ``team_col``. |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary" team color. |
| `color_by` | `str \| None` | Another numeric column whose values set the colors and sizes. |
| `min_value` | `float \| None` | The value of an empty bubble; None measures from zero. |
| `max_value` | `float \| None` | The value of a 100-pixel bubble; None for the column's largest magnitude. Sizes are clamped to 0-100 pixels, as data bars are to their track. |
| `opacity` | `float` | The bubble's opacity, 0 to 1. |
| `bias` | `float` | Spacing of the scale's colors; above 1 spreads the high end (``grDevices::colorRamp``). |
| `number_fmt` | `collections.abc.Callable[[Any], str] \| str \| None` | A function of the value returning its text, or a format spec such as ",.1f". |
| `text_color` | `str \| None` | The text color; None for black, or white on a dark bubble. |
| `brighten_text` | `bool` | Switch the text to black or white when ``text_color`` is unreadable on the bubble. |
| `show_text` | `bool` | Show the value inside the bubble. |
| `bold_text` | `bool` | Bold text. |
| `box_shadow` | `bool` | A drop shadow under each bubble. |
| `tooltip` | `bool` | Give each cell a ``title`` (hover text) of its formatted value. |
| `season` | `Any` | One season whose team colors to use; None for today's. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team_col``, as in ``resolve``. |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the column drawn. |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `InputError`: (a ValueError) If ``shape`` is not "circles"/"squares", ``opacity`` is outside [0, 1], ``bias`` is not positive, ``team_col`` comes without ``league``, or ``color_ref`` and ``team_col`` are both given.
- `ValueError`: If ``colors`` are not hex colors, or a named column is not in ``data``.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_bubble_grid

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [15, 13, 12]})

Reactable(df, columns=[reactable_sdv_bubble_grid(df, team_col="team", league="nfl", id="wins")])
```

### See also

- [Equivalent of reactablefmtr::bubble_grid](https://kcuilla.github.io/reactablefmtr/reference/bubble_grid.html)

## reactable_sdv_color_scales

<div class="sdv-signature">

```python
reactable_sdv_color_scales(
    data: Any,
    *,
    colors: collections.abc.Sequence[str] = ('#15607A', '#FFFFFF', '#FA8C00'),
    color_ref: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Literal['primary', 'secondary'] = 'primary',
    color_by: str | None = None,
    opacity: float = 1,
    bias: float = 1,
    min_value: float | None = None,
    max_value: float | None = None,
    even_breaks: bool = False,
    number_fmt: collections.abc.Callable[[Any], str] | str | None = None,
    text_color: str | None = None,
    brighten_text: bool = True,
    show_text: bool = True,
    bold_text: bool = False,
    span: bool | str | collections.abc.Sequence[str] = False,
    tooltip: bool = False,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column whose cell backgrounds are filled on a color scale, by a color column, or in team colors.

``reactable_sdv_color_tiles`` without the tile; the text stays readable.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable`` (ranges and per-row colors are read from it). |
| `colors` | `collections.abc.Sequence[str]` | Hex colors forming the scale from the column's minimum to its maximum. |
| `color_ref` | `str \| None` | A column of ``data`` holding each row's fill color: hex, a CSS color name, or rgb()/hsl(); any other value is warned about once and that row keeps the scale color. |
| `team_col` | `str \| None` | A column of team values; each cell takes that team's color (``which``). Teams that do not resolve keep the scale color. |
| `league` | `str \| None` | The SDV league key, e.g. "nfl"; needed by ``team_col``. |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary" team color. |
| `color_by` | `str \| None` | Another numeric column whose values set the colors. |
| `opacity` | `float` | The fill's opacity, 0 to 1. |
| `bias` | `float` | Spacing of the scale's colors; above 1 spreads the high end (``grDevices::colorRamp``). |
| `min_value` | `float \| None` | The value at the scale's first color; at most the column's minimum. |
| `max_value` | `float \| None` | The value at the scale's last color; at least the column's maximum. |
| `even_breaks` | `bool` | Color by quantile bucket (as many as ``colors``) instead of by value. |
| `number_fmt` | `collections.abc.Callable[[Any], str] \| str \| None` | A function of the value returning its text, or a format spec such as ",.1f". |
| `text_color` | `str \| None` | The text color; None for black, or white on a dark fill. |
| `brighten_text` | `bool` | Switch the text to black or white when ``text_color`` is unreadable on the fill. |
| `show_text` | `bool` | Show the value; False hides it. |
| `bold_text` | `bool` | Bold text. |
| `span` | `bool \| str \| collections.abc.Sequence[str]` | True scales every numeric column of ``data`` on one shared range; a column name or list of names scales those columns together (cells of other columns are left unfilled). |
| `tooltip` | `bool` | Give each cell a ``title`` (hover text) of its formatted value. |
| `season` | `Any` | One season whose team colors to use; None for today's. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team_col``, as in ``resolve``. |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the column drawn. |

### Returns

`reactable.Column` — The column, with a ``style`` function (and a cell renderer when ``number_fmt`` or ``tooltip`` is given).

### Raises

- `InputError`: (a ValueError) If ``opacity`` is outside [0, 1], ``bias`` is not positive, ``min_value`` is above the column's minimum or ``max_value`` below its maximum (when the ``Reactable`` is built), ``span`` names a non-numeric column, ``team_col`` comes without ``league``, or ``color_ref`` and ``team_col`` are both given.
- `ValueError`: If ``colors`` are not hex colors, or a named column is not in ``data``.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_color_scales

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [15, 13, 12]})

Reactable(df, columns=[reactable_sdv_color_scales(df, team_col="team", league="nfl", id="wins")])
```

### See also

- [Equivalent of reactablefmtr::color_scales](https://kcuilla.github.io/reactablefmtr/reference/color_scales.html)

## reactable_sdv_color_tiles

<div class="sdv-signature">

```python
reactable_sdv_color_tiles(
    data: Any,
    *,
    colors: collections.abc.Sequence[str] = ('#15607A', '#FFFFFF', '#FA8C00'),
    color_ref: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Literal['primary', 'secondary'] = 'primary',
    color_by: str | None = None,
    opacity: float = 1,
    bias: float = 1,
    min_value: float | None = None,
    max_value: float | None = None,
    even_breaks: bool = False,
    number_fmt: collections.abc.Callable[[Any], str] | str | None = None,
    text_color: str | None = None,
    brighten_text: bool = True,
    show_text: bool = True,
    bold_text: bool = False,
    span: bool | str | collections.abc.Sequence[str] = False,
    box_shadow: bool = False,
    tooltip: bool = False,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column of rounded tiles filled on a color scale, by a color column, or in the row's team color.

The text on each tile stays readable.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable`` (ranges and per-row colors are read from it). |
| `colors` | `collections.abc.Sequence[str]` | Hex colors forming the scale from the column's minimum to its maximum. |
| `color_ref` | `str \| None` | A column of ``data`` holding each row's fill color: hex, a CSS color name, or rgb()/hsl(); any other value is warned about once and that row keeps the scale color. |
| `team_col` | `str \| None` | A column of team values; each tile takes that team's color (``which``). Teams that do not resolve keep the scale color. |
| `league` | `str \| None` | The SDV league key, e.g. "nfl"; needed by ``team_col``. |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary" team color. |
| `color_by` | `str \| None` | Another numeric column whose values set the colors. |
| `opacity` | `float` | The fill's opacity, 0 to 1. |
| `bias` | `float` | Spacing of the scale's colors; above 1 spreads the high end (``grDevices::colorRamp``). |
| `min_value` | `float \| None` | The value at the scale's first color; at most the column's minimum. |
| `max_value` | `float \| None` | The value at the scale's last color; at least the column's maximum. |
| `even_breaks` | `bool` | Color by quantile bucket (as many as ``colors``) instead of by value. |
| `number_fmt` | `collections.abc.Callable[[Any], str] \| str \| None` | A function of the value returning its text, or a format spec such as ",.1f". |
| `text_color` | `str \| None` | The text color; None for black, or white on a dark tile. |
| `brighten_text` | `bool` | Switch the text to black or white when ``text_color`` is unreadable on the tile. |
| `show_text` | `bool` | Show the value; False leaves a plain tile. |
| `bold_text` | `bool` | Bold text. |
| `span` | `bool \| str \| collections.abc.Sequence[str]` | True scales every numeric column of ``data`` on one shared range; a column name or list of names scales those columns together (cells of other columns are left unfilled). |
| `box_shadow` | `bool` | A drop shadow under each tile. |
| `tooltip` | `bool` | Give each cell a ``title`` (hover text) of its formatted value. |
| `season` | `Any` | One season whose team colors to use; None for today's. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team_col``, as in ``resolve``. |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the column drawn. |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `InputError`: (a ValueError) If ``opacity`` is outside [0, 1], ``bias`` is not positive, ``min_value`` is above the column's minimum or ``max_value`` below its maximum (when the ``Reactable`` is built), ``span`` names a non-numeric column, ``team_col`` comes without ``league``, or ``color_ref`` and ``team_col`` are both given.
- `ValueError`: If ``colors`` are not hex colors, or a named column is not in ``data``.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_color_tiles

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "epa": [0.12, 0.18, 0.21]})

Reactable(df, columns=[reactable_sdv_color_tiles(df, number_fmt=".2f", id="epa")])
```

### See also

- [Equivalent of reactablefmtr::color_tiles](https://kcuilla.github.io/reactablefmtr/reference/color_tiles.html)

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

## reactable_sdv_data_bars

<div class="sdv-signature">

```python
reactable_sdv_data_bars(
    data: Any,
    *,
    fill_color: str | collections.abc.Sequence[str] = '#15607A',
    fill_color_ref: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Literal['primary', 'secondary'] = 'primary',
    fill_by: str | None = None,
    fill_opacity: float = 1,
    bias: float = 1,
    min_value: float | None = None,
    max_value: float | None = None,
    align: Literal['left', 'right'] = 'left',
    text_position: Literal['inside-end', 'outside-end', 'inside-base', 'outside-base', 'center', 'above', 'none'] = 'inside-end',
    text_color: str | None = None,
    brighten_text: bool = True,
    bold_text: bool = False,
    number_fmt: collections.abc.Callable[[Any], str] | str | None = None,
    mark: Literal['logo', 'headshot', 'wordmark'] | None = None,
    mark_col: str | None = None,
    mark_height: float = 20,
    round_edges: bool = False,
    bar_height: float | None = None,
    background: str = '#EEEEEE',
    gradient: bool = False,
    pos_neg: bool = False,
    box_shadow: bool = False,
    tooltip: bool = False,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column of horizontal bars sized by value, in a scale color, a color column or the team color.

Each bar is the value's share of the column's largest magnitude, optionally with a logo, headshot or wordmark
on it.

Negative values (or ``pos_neg=True``) split the cell at zero: negative bars grow left from a center line, positive
bars right, colored by the first and last of two ``fill_color`` colors.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable`` (ranges and per-row colors are read from it). |
| `fill_color` | `str \| collections.abc.Sequence[str]` | One color, or several colors forming a scale from the column's minimum to its maximum. |
| `fill_color_ref` | `str \| None` | A column of ``data`` holding each row's bar color: hex, a CSS color name, or rgb()/hsl(); any other value is warned about once and that row keeps the scale color. |
| `team_col` | `str \| None` | A column of team values; each bar takes that team's color (``which``). Teams that do not resolve keep the scale color. |
| `league` | `str \| None` | The SDV league key, e.g. "nfl"; needed by ``team_col`` and ``mark``. |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary" team color. |
| `fill_by` | `str \| None` | Another numeric column whose values set the bar lengths and colors (a text column is an error). |
| `fill_opacity` | `float` | The bar's opacity, 0 to 1. |
| `bias` | `float` | Spacing of the scale's colors; above 1 spreads the high end (``grDevices::colorRamp``). |
| `min_value` | `float \| None` | The value of an empty bar; None measures from zero. |
| `max_value` | `float \| None` | The value of a full bar; None for the column's largest magnitude. Bars are clamped to 0-100% of the track, so a value beyond ``max_value`` draws a full bar. |
| `align` | `Literal['left', 'right']` | "left" or "right": the side bars grow from. |
| `text_position` | `Literal['inside-end', 'outside-end', 'inside-base', 'outside-base', 'center', 'above', 'none']` | "inside-end", "outside-end", "inside-base", "outside-base", "center", "above" or "none" ("none" keeps the value as visually hidden text for screen readers). |
| `text_color` | `str \| None` | The text color (hex, a CSS color name, or rgb()/hsl()); None for black, or white on a dark bar. |
| `brighten_text` | `bool` | Switch text inside a bar to black or white when ``text_color`` is unreadable on it. |
| `bold_text` | `bool` | Bold text. |
| `number_fmt` | `collections.abc.Callable[[Any], str] \| str \| None` | A function of the value returning its text, or a format spec such as ",.1f". |
| `mark` | `Literal['logo', 'headshot', 'wordmark'] \| None` | "logo", "headshot" or "wordmark": an image at the end of each bar. |
| `mark_col` | `str \| None` | The column the mark is read from; defaults to ``team_col``. Headshots need ESPN athlete ids. |
| `mark_height` | `float` | The mark's height in pixels. |
| `round_edges` | `bool` | Round the bar's ends. |
| `bar_height` | `float \| None` | The bar's height in pixels; None for 18 (5 with ``text_position="above"``). |
| `background` | `str` | The color of the empty track behind each bar (hex, a CSS color name, or rgb()/hsl()). |
| `gradient` | `bool` | Fill each bar with a left-to-right gradient of ``fill_color`` (two colors or more). |
| `pos_neg` | `bool` | Split every cell at zero even when no value is negative. |
| `box_shadow` | `bool` | A drop shadow under each bar. |
| `tooltip` | `bool` | Give each cell a ``title`` (hover text) of its formatted value. |
| `season` | `Any` | One season whose team colors and marks to use; None for today's. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team_col``/``mark_col``, as in ``resolve``. |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the column drawn. |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `InputError`: (a ValueError) If an option is not one of its choices, an opacity is outside [0, 1], ``fill_color`` is not hex colors, ``gradient`` has fewer than two colors, ``team_col`` or ``mark`` comes without ``league``, or ``fill_color_ref`` and ``team_col`` are both given.
- `ValueError`: If a named column is not in ``data``.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_data_bars

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [15, 13, 12]})

Reactable(df, columns=[reactable_sdv_data_bars(df, team_col="team", league="nfl", mark="logo", id="wins")])
```

### See also

- [Equivalent of reactablefmtr::data_bars](https://kcuilla.github.io/reactablefmtr/reference/data_bars.html)

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
    season: Any = None,
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
| `season` | `Any` | One season for every row's team color, for teams whose colors changed; None for today's. |
| `na_color` | `str` | The color for teams that do not resolve or have no color. |
| `min_value` | `float \| None` | The value of an empty gauge; None for 0. As in reactablefmtr, a cell's absolute value is what fills the gauge (-5 fills as 5); the printed value and the aria-label keep the sign. |
| `max_value` | `float \| None` | The value of a full gauge; None for the column's largest absolute value. Must be above ``min_value``. |
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

- `InputError`: (a ValueError) If ``size`` or ``bias`` is not a positive number, ``opacity`` is outside [0, 1], ``min_value``/``max_value`` is not a finite number or ``min_value`` is not below ``max_value``, ``fill_color`` holds several colors that are not hex colors, or ``team_col`` is given without ``league``; if ``league``, ``id_system``, ``which`` or ``season`` is unknown. When a cell is drawn: if ``min_value`` alone is above the column's largest absolute value, or (with ``team_col``) the table has more rows than ``data``.
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

## reactable_sdv_highlight

<div class="sdv-signature">

```python
reactable_sdv_highlight(
    data: Any,
    *,
    which: Literal['max', 'min', 'min_max'] = 'max',
    font_color: str | tuple[str, str] | None = None,
    highlighter: str | tuple[str | None, str | None] | None = None,
    tooltip: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column whose highest (or lowest, or both) values are bold, in a color, optionally on a highlight.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable`` (the column's extremes are read from it). |
| `which` | `Literal['max', 'min', 'min_max']` | "max", "min", or "min_max" for both: which extreme to highlight. (Unlike the team-color ``which`` of the other formatters, "primary"/"secondary", this is reactablefmtr's highlight_max/_min/_min_max.) |
| `font_color` | `str \| tuple[str, str] \| None` | The CSS text color; None for green on the maximum and red on the minimum. For "min_max", a ``(min, max)`` pair. |
| `highlighter` | `str \| tuple[str \| None, str \| None] \| None` | A CSS background color, or a ``(min, max)`` pair for "min_max"; None for no background. |
| `tooltip` | `bool` | Give each cell a ``title`` (hover text) of its value. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the column drawn. |

### Returns

`reactable.Column` — The column, with a ``style`` function (and a cell renderer when ``tooltip`` is on).

### Raises

- `InputError`: (a ValueError) If ``which`` is unknown, a pair is not two values, or a color is not a hex color, a CSS color name, or rgb()/hsl().

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_highlight

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [15, 13, 12]})

Reactable(df, columns=[reactable_sdv_highlight(df, which="min_max", id="wins")])
```

### See also

- [Equivalent of reactablefmtr::highlight_max, highlight_min and highlight_min_max](https://kcuilla.github.io/reactablefmtr/reference/highlight_min_max.html)

## reactable_sdv_icon_assign

<div class="sdv-signature">

```python
reactable_sdv_icon_assign(
    data: Any,
    *,
    icon: str = 'circle',
    fill_color: str = '#15607A',
    empty_color: str = '#EEEEEE',
    fill_opacity: float = 1,
    empty_opacity: float = 1,
    align_icons: Literal['left', 'right', 'center'] = 'left',
    icon_size: float = 16,
    buckets: int | None = None,
    number_fmt: collections.abc.Callable[[Any], str] | str | None = None,
    seq_by: float = 1,
    show_values: Literal['none', 'left', 'right', 'above', 'below'] = 'none',
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column that repeats an icon, filled up to the value: a rating in stars, a count in dots.

A value of 3 in a column whose largest value is 5 shows three filled icons and two empty ones (or, with
``buckets``, the value's quantile bucket out of ``buckets``).

The icons are inline SVG; see ``reactable_sdv_icon_sets`` for the names.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable`` (the column's maximum is read from it). |
| `icon` | `str` | The icon's name. |
| `fill_color` | `str` | The hex color of a filled icon. |
| `empty_color` | `str` | The hex color of an empty icon. |
| `fill_opacity` | `float` | The filled icons' opacity, 0 to 1. |
| `empty_opacity` | `float` | The empty icons' opacity, 0 to 1. |
| `align_icons` | `Literal['left', 'right', 'center']` | "left", "right" or "center". |
| `icon_size` | `float` | The icon's size in pixels. |
| `buckets` | `int \| None` | Cut the column into this many quantile buckets and fill one icon per bucket reached. |
| `number_fmt` | `collections.abc.Callable[[Any], str] \| str \| None` | A function of the value returning its text, or a format spec such as ",.1f". |
| `seq_by` | `float` | One icon per this many units of value (values are rounded half up first). A cell draws at most 100 icons (with a warning); a column that would need more than 1,000 is an error. |
| `show_values` | `Literal['none', 'left', 'right', 'above', 'below']` | "none", or where to show the value: "left", "right", "above" or "below". |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the column drawn. |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `InputError`: (a ValueError) If ``icon``, ``align_icons`` or ``show_values`` is unknown, an opacity is outside [0, 1], ``buckets`` is not a positive whole number, or ``seq_by`` is not positive.
- `ValueError`: If a color is not a hex color.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_icon_assign

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "titles": [4, 0, 2]})

Reactable(df, columns=[reactable_sdv_icon_assign(df, icon="star", show_values="right", id="titles")])
```

### See also

- [Equivalent of reactablefmtr::icon_assign](https://kcuilla.github.io/reactablefmtr/reference/icon_assign.html)

## reactable_sdv_icon_sets

<div class="sdv-signature">

```python
reactable_sdv_icon_sets(
    data: Any,
    *,
    icons: str | collections.abc.Sequence[str] = ('circle',),
    colors: collections.abc.Sequence[str] = ('#15607A', '#B0B0B0', '#FA8C00'),
    opacity: float = 1,
    icon_position: Literal['left', 'right', 'above', 'below', 'over'] = 'right',
    icon_ref: str | None = None,
    icon_size: float = 16,
    icon_color_ref: str | None = None,
    number_fmt: collections.abc.Callable[[Any], str] | str | None = None,
    tooltip: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column that puts an icon beside each number, chosen by the value's quantile bucket.

The column is cut into as many buckets as ``icons`` (and as ``colors``); each value takes its bucket's icon and
color.

The icons are inline SVG: circle, square, diamond, triangle (``triangle-up``), triangle-down, arrow
(``arrow-right``), arrow-up, arrow-down, arrow-left, chevron-up, chevron-down, star, check, x, flag, minus, plus,
heart and person.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable`` (buckets are read from it). |
| `icons` | `str \| collections.abc.Sequence[str]` | One icon name, or several from the lowest bucket to the highest. |
| `colors` | `collections.abc.Sequence[str]` | Hex colors from the lowest bucket to the highest. |
| `opacity` | `float` | The icons' opacity, 0 to 1. |
| `icon_position` | `Literal['left', 'right', 'above', 'below', 'over']` | "right", "left", "above", "below", or "over" (the icon replaces the value). |
| `icon_ref` | `str \| None` | A column of ``data`` holding each row's icon name (overrides ``icons``); a missing value draws no icon. |
| `icon_size` | `float` | The icon's size in pixels. |
| `icon_color_ref` | `str \| None` | A column of ``data`` holding each row's icon color (overrides ``colors``): hex, a CSS color name, or rgb()/hsl(); a missing value or any other value (warned about once) draws no icon. |
| `number_fmt` | `collections.abc.Callable[[Any], str] \| str \| None` | A function of the value returning its text, or a format spec such as ",.1f". |
| `tooltip` | `bool` | Give each cell a ``title`` (hover text) of its formatted value. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the column drawn. |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `InputError`: (a ValueError) If an icon or ``icon_position`` is unknown, or ``opacity`` is outside [0, 1].
- `ValueError`: If ``colors`` are not hex colors, or a named column is not in ``data``.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_icon_sets

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [15, 13, 12]})

Reactable(df, columns=[reactable_sdv_icon_sets(df, icons=("arrow-down", "minus", "arrow-up"), id="wins")])
```

### See also

- [Equivalent of reactablefmtr::icon_sets](https://kcuilla.github.io/reactablefmtr/reference/icon_sets.html)

## reactable_sdv_icon_trend

<div class="sdv-signature">

```python
reactable_sdv_icon_trend(
    data: Any,
    *,
    icons: Literal['arrow', 'chevron', 'triangle'] = 'arrow',
    colors: collections.abc.Sequence[str] = ('#15607A', '#767676', '#B35900'),
    icon_position: Literal['left', 'right', 'above', 'below', 'over'] = 'right',
    icon_size: float = 16,
    show_zero_label: bool = False,
    number_fmt: collections.abc.Callable[[Any], str] | str | None = None,
    opacity: float = 1,
    text_color: str | None = None,
    bold_text: bool = False,
    tooltip: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column that marks each change with an up arrow, a down arrow or a dash, the value colored to match.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable``. |
| `icons` | `Literal['arrow', 'chevron', 'triangle']` | "arrow", "chevron" or "triangle". |
| `colors` | `collections.abc.Sequence[str]` | Three hex colors: down, zero, up. The default is reactablefmtr's ``#15607A`` with ``#767676`` and ``#B35900``, both 4.5:1 or better on white, in place of reactablefmtr's ``#B2B2B2`` and ``#FA8C00`` (about 2.1:1 and 2.4:1, too faint for the text, which takes these colors). |
| `icon_position` | `Literal['left', 'right', 'above', 'below', 'over']` | "right", "left", "above", "below", or "over" (the icon replaces the value). |
| `icon_size` | `float` | The icon's size in pixels. |
| `show_zero_label` | `bool` | Show the value when it is zero (otherwise only the dash is drawn, and the zero is kept as visually hidden text for screen readers). |
| `number_fmt` | `collections.abc.Callable[[Any], str] \| str \| None` | A function of the value returning its text, or a format spec such as "+.1f". |
| `opacity` | `float` | The icons' opacity, 0 to 1. |
| `text_color` | `str \| None` | One color for every value's text; None colors it like its icon. |
| `bold_text` | `bool` | Bold text. |
| `tooltip` | `bool` | Give each cell a ``title`` (hover text) of its formatted value. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the column drawn. |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `InputError`: (a ValueError) If ``icons`` or ``icon_position`` is unknown, ``colors`` is not three colors, or ``opacity`` is outside [0, 1].
- `ValueError`: If ``colors`` are not hex colors.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_icon_trend

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "win_change": [4, 0, -3]})

Reactable(df, columns=[reactable_sdv_icon_trend(df, number_fmt="+d", id="win_change")])
```

### See also

- [Equivalent of reactablefmtr::icon_trend_indicator](https://kcuilla.github.io/reactablefmtr/reference/icon_trend_indicator.html)

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

## reactable_sdv_merge_column

<div class="sdv-signature">

```python
reactable_sdv_merge_column(
    data: Any,
    *,
    merged_name: str,
    merged_position: Literal['right', 'left', 'above', 'below'] = 'right',
    merged_size: float = 12,
    merged_color: str = '#777',
    merged_weight: Literal['normal', 'bold'] = 'normal',
    size: float = 14,
    color: str | None = None,
    weight: Literal['normal', 'bold'] = 'bold',
    spacing: float = 0,
    mark: Literal['logo', 'headshot', 'wordmark'] | None = None,
    mark_col: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    mark_height: float = 30,
    tooltip: bool = False,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column that shows a second column's value beside or below each value, after an optional mark.

A player and his team, a team and its record; the mark is the row's logo, headshot or wordmark.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable`` (the merged values are read from it). |
| `merged_name` | `str` | The column of ``data`` merged into this one (hide it with ``Column(show=False)`` if it is shown). |
| `merged_position` | `Literal['right', 'left', 'above', 'below']` | "right", "left", "above" or "below". |
| `merged_size` | `float` | The merged text's size in pixels. |
| `merged_color` | `str` | The merged text's color (hex, a CSS color name, or rgb()/hsl()). |
| `merged_weight` | `Literal['normal', 'bold']` | "normal" or "bold" for the merged text. |
| `size` | `float` | The main text's size in pixels. |
| `color` | `str \| None` | The main text's color (hex, a CSS color name, or rgb()/hsl()); None inherits the table's. |
| `weight` | `Literal['normal', 'bold']` | "normal" or "bold" for the main text. |
| `spacing` | `float` | Extra pixels between the two values. |
| `mark` | `Literal['logo', 'headshot', 'wordmark'] \| None` | "logo", "headshot" or "wordmark": an image before the text. |
| `mark_col` | `str \| None` | The column the mark is read from; defaults to ``team_col``, then this column. Headshots need ESPN athlete ids. |
| `team_col` | `str \| None` | A column of team values for the logo or wordmark. |
| `league` | `str \| None` | The SDV league key, e.g. "nfl"; needed by ``mark``. |
| `mark_height` | `float` | The mark's height in pixels. |
| `tooltip` | `bool` | Give each cell a ``title`` (hover text) of its value and the merged value. |
| `season` | `Any` | One season whose marks to use; None for today's. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of the mark's column, as in ``resolve``. |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the column drawn. |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `InputError`: (a ValueError) If ``merged_position``, a weight or ``mark`` is unknown, a color is not a color, or ``mark`` comes without ``league`` or a column to read it from.
- `ValueError`: If a named column is not in ``data``.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

### Example

```python
import pandas as pd
from reactable import Column, Reactable
from sdvplot.reactable import reactable_sdv_merge_column

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "record": ["15-2", "13-4", "12-5"]})

Reactable(
    df,
    columns=[
        reactable_sdv_merge_column(df, merged_name="record", merged_position="below", mark="logo",
                                   team_col="team", league="nfl", id="team"),
        Column(id="record", show=False),
    ],
)
```

### See also

- [Equivalent of reactablefmtr::merge_column](https://kcuilla.github.io/reactablefmtr/reference/merge_column.html)

## reactable_sdv_pill_buttons

<div class="sdv-signature">

```python
reactable_sdv_pill_buttons(
    data: Any,
    *,
    colors: str | collections.abc.Sequence[str] = '#15607A',
    color_ref: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Literal['primary', 'secondary'] = 'primary',
    opacity: float = 1,
    number_fmt: collections.abc.Callable[[Any], str] | str | None = None,
    text_color: str | None = None,
    brighten_text: bool = True,
    show_text: bool = True,
    bold_text: bool = False,
    box_shadow: bool = False,
    tooltip: bool = False,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
    **column_kwargs: Any,
) -> reactable.models.Column
```

</div>

A reactable column whose values sit in rounded pills, in a scale color, a color column or the team color.

Numbers are colored on the scale, text takes the first color.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | The pandas or polars DataFrame passed to ``Reactable`` (ranges and per-row colors are read from it). |
| `colors` | `str \| collections.abc.Sequence[str]` | One hex color, or several forming a scale from the column's minimum to its maximum (numbers only). |
| `color_ref` | `str \| None` | A column of ``data`` holding each row's pill color: hex, a CSS color name, or rgb()/hsl(); any other value is warned about once and that row keeps the scale color. |
| `team_col` | `str \| None` | A column of team values; each pill takes that team's color (``which``). |
| `league` | `str \| None` | The SDV league key, e.g. "nfl"; needed by ``team_col``. |
| `which` | `Literal['primary', 'secondary']` | "primary" or "secondary" team color. |
| `opacity` | `float` | The pill's opacity, 0 to 1. |
| `number_fmt` | `collections.abc.Callable[[Any], str] \| str \| None` | A function of the value returning its text, or a format spec such as ",.1f". |
| `text_color` | `str \| None` | The text color; None for black, or white on a dark pill. |
| `brighten_text` | `bool` | Switch the text to black or white when ``text_color`` is unreadable on the pill. |
| `show_text` | `bool` | Show the value; False leaves an empty pill. |
| `bold_text` | `bool` | Bold text. |
| `box_shadow` | `bool` | A drop shadow under each pill. |
| `tooltip` | `bool` | Give each cell a ``title`` (hover text) of its formatted value. |
| `season` | `Any` | One season whose team colors to use; None for today's. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team_col``, as in ``resolve``. |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |
| `**column_kwargs` | `Any` | Passed to ``reactable.Column``; ``id`` names the column drawn. |

### Returns

`reactable.Column` — The column, with ``html=True`` and a cell renderer.

### Raises

- `InputError`: (a ValueError) If ``opacity`` is outside [0, 1], ``team_col`` comes without ``league``, or ``color_ref`` and ``team_col`` are both given.
- `ValueError`: If ``colors`` are not hex colors, or a named column is not in ``data``.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_pill_buttons

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "conf": ["AFC West", "AFC East", "AFC North"]})

Reactable(df, columns=[reactable_sdv_pill_buttons(df, team_col="team", league="nfl", id="conf")])
```

### See also

- [Equivalent of reactablefmtr::pill_buttons](https://kcuilla.github.io/reactablefmtr/reference/pill_buttons.html)

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
    season: Any = None,
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
| `season` | `Any` | One season for every row's team color, for teams whose colors changed; None for today's. |
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

- `InputError`: (a ValueError) As ``reactable_sdv_sparkline``: a bad pixel size, opacity, option name, decimals or bounds, or ``team_col`` without ``league``; if ``league``, ``id_system``, ``which`` or ``season`` is unknown. When a cell is drawn: as ``reactable_sdv_sparkline``.
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
    season: Any = None,
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
| `season` | `Any` | One season for every row's team color, for teams whose colors changed; None for today's. |
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

- `InputError`: (a ValueError) If ``height``/``width`` is not a number of pixels of at least 1, an opacity is outside [0, 1], ``statline``/``bandline``/``labels``/``highlight_points`` names an unknown option, ``decimals`` is not a whole number, ``line_width``/``point_size`` is not a positive number, ``min_value``/``max_value`` is not a finite number or ``min_value`` is not below ``max_value``, or ``team_col`` is given without ``league``; if ``league``, ``id_system``, ``which`` or ``season`` is unknown. When a cell is drawn: if one bound crosses the row's data, or (with ``team_col``) the table has more rows than ``data``.
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

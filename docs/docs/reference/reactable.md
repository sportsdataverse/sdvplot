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
| [reactable_sdv_frame](#reactable_sdv_frame) | A ``Reactable`` with a title and subtitle above it and a legend and source line under it, in a Google font. |
| [reactable_sdv_headshots](#reactable_sdv_headshots) | A reactable column that shows each cell's player id as the player's headshot. |
| [reactable_sdv_icon_legend](#reactable_sdv_icon_legend) | An icon legend: each icon, in its color, before its label, for ``reactable_sdv_frame(legend=...)``. |
| [reactable_sdv_legend](#reactable_sdv_legend) | A color legend: a row of swatches with a label under each, for ``reactable_sdv_frame(legend=...)``. |
| [reactable_sdv_logos](#reactable_sdv_logos) | A reactable column that shows each cell's team as its logo. |
| [reactable_sdv_team_color_bar](#reactable_sdv_team_color_bar) | A reactable column whose cells hold a bar in the row's team color, as long as the value's share of the maximum. |
| [reactable_sdv_team_color_bg](#reactable_sdv_team_color_bg) | A reactable column whose cells are filled with the row's team color, mostly transparent. |
| [reactable_sdv_theme](#reactable_sdv_theme) | One of reactablefmtr's 27 table themes, with reactablefmtr's own colors, fonts, borders and paddings. |
| [reactable_sdv_theme_team](#reactable_sdv_theme_team) | A table theme in a team's colors: the header filled with the primary color over a rule in the secondary, |
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

## reactable_sdv_frame

<div class="sdv-signature">

```python
reactable_sdv_frame(
    table: Any,
    *,
    title: Any = None,
    subtitle: Any = None,
    source: Any = None,
    legend: Any = None,
    font: str | None = None,
    align: str = 'left',
) -> htmltools._core.TagList
```

</div>

A ``Reactable`` with a title and subtitle above it and a legend and source line under it, in a Google font.

The result shows in a notebook just as a ``Reactable`` does (call ``reactable.embed_css()`` once first). Its
sizes are reactablefmtr's: a 32 px bold title, a 24 px bold subtitle and a 16 px source line, no margins; the
text color is inherited from the page rather than reactablefmtr's black, so a dark page keeps it readable.

### Arguments

| Name | Type | Description |
|---|---|---|
| `table` | `Any` | The ``reactable.Reactable``. |
| `title` | `Any` | The title text (or an htmltools tag). |
| `subtitle` | `Any` | The subtitle text (or tag). |
| `source` | `Any` | The source line under the table, e.g. "Data: sportsdataverse-py". |
| `legend` | `Any` | A legend from ``reactable_sdv_legend`` or ``reactable_sdv_icon_legend`` (any htmltools tag), shown under the table. |
| `font` | `str \| None` | A Google Fonts family name, e.g. "Poppins" or "Roboto Condensed", for the title, table and source; None keeps the page's font. The font is loaded from fonts.googleapis.com when the page is shown. |
| `align` | `str` | "left", "center" or "right", for the title, subtitle, legend and source. |

### Returns

`htmltools.TagList` — The framed table.

### Raises

- `InputError`: (a ValueError) If ``align`` is not "left", "center" or "right", or ``font`` is not a font name.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_frame, reactable_sdv_legend

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [12, 10, 9]})
reactable_sdv_frame(
    Reactable(df),
    title="AFC leaders",
    subtitle="2025 regular season",
    source="Data: sportsdataverse-py",
    legend=reactable_sdv_legend(colors=["#ffffff", "#1a9641"], labels=["fewer", "more"]),
    font="Poppins",
)
```

### See also

- [Equivalent of reactablefmtr::add_title, add_subtitle, add_source and google_font](https://kcuilla.github.io/reactablefmtr/reference/add_title.html)

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

## reactable_sdv_icon_legend

<div class="sdv-signature">

```python
reactable_sdv_icon_legend(
    *,
    icons: Any,
    colors: Any,
    labels: Any,
    title: Any = None,
    footer: Any = None,
) -> htmltools._core.Tag
```

</div>

An icon legend: each icon, in its color, before its label, for ``reactable_sdv_frame(legend=...)``.

### Arguments

| Name | Description |
|---|---|
| `icons` | One shape per entry: "circle", "square", "triangle", "diamond" or "star" (drawn as inline SVG, no icon font), or a single shape for all. |
| `colors` | One hex color per entry, or a single color for all. |
| `labels` | One label per entry. |
| `title` | Text above the icons. |
| `footer` | Small grey text under them. |

### Returns

`htmltools.Tag` — The legend.

### Raises

- `InputError`: (a ValueError) If a shape is unknown, a color is not a hex color, or ``icons``/``colors`` do not have one entry per label.

### Example

```python
from sdvplot.reactable import reactable_sdv_icon_legend

reactable_sdv_icon_legend(icons="circle", colors=["#1a9641", "#d7191c"], labels=["won", "lost"])
```

### See also

- [Equivalent of reactablefmtr::add_icon_legend (inline SVG shapes instead of Font Awesome)](https://kcuilla.github.io/reactablefmtr/reference/add_icon_legend.html)

## reactable_sdv_legend

<div class="sdv-signature">

```python
reactable_sdv_legend(
    *,
    colors: Any,
    labels: Any = None,
    bins: int | None = None,
    title: Any = None,
    footer: Any = None,
) -> htmltools._core.Tag
```

</div>

A color legend: a row of swatches with a label under each, for ``reactable_sdv_frame(legend=...)``.

### Arguments

| Name | Type | Description |
|---|---|---|
| `colors` | `Any` | The legend's colors, low to high, as hex strings. |
| `labels` | `Any` | One label per swatch (numbers or text); None for swatches alone. |
| `bins` | `int \| None` | The number of swatches, spread evenly along ``colors`` as a ramp (reactablefmtr's ``bins``); None for one swatch per color. |
| `title` | `Any` | Text above the swatches. |
| `footer` | `Any` | Small grey text under them. |

### Returns

`htmltools.Tag` — The legend.

### Raises

- `InputError`: (a ValueError) If ``colors`` is empty or not hex colors, ``bins`` is not a whole number of at least 2, or ``labels`` does not have one entry per swatch.

### Example

```python
from sdvplot.reactable import reactable_sdv_legend

reactable_sdv_legend(colors=["#15607a", "#ffffff", "#fa8c00"], bins=5, labels=[-0.2, -0.1, 0, 0.1, 0.2],
                     title="EPA per play", footer="lower is better on defense")
```

### See also

- [Equivalent of reactablefmtr::add_legend (the swatches are given, not computed from a column)](https://kcuilla.github.io/reactablefmtr/reference/add_legend.html)

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

## reactable_sdv_theme

<div class="sdv-signature">

```python
reactable_sdv_theme(
    name: str,
    *,
    font_size: float | None = None,
    font_color: str | None = None,
    header_font_size: float | None = None,
    header_font_color: str | None = None,
    background_color: str | None = None,
    cell_padding: float | str | None = None,
    centered: bool = False,
    **theme_args: Any,
) -> reactable.models.Theme
```

</div>

One of reactablefmtr's 27 table themes, with reactablefmtr's own colors, fonts, borders and paddings.

Pass the result to ``Reactable(theme=...)``. (``reactable.options.theme`` would set it for every table in the
session, so the theme is returned rather than set.) The themes do not load a font: give
``reactable_sdv_frame(font=...)`` a Google font for that.

### Arguments

| Name | Type | Description |
|---|---|---|
| `name` | `str` | The theme: "cerulean", "clean", "cosmo", "cyborg", "dark", "darkly", "default", "espn", "fivethirtyeight", "flatly", "hoverdark", "hoverlight", "journal", "lux", "midnight", "midnightblue", "minty", "no_lines", "nytimes", "pff", "sandstone", "sanfran", "slate", "spacelab", "sunrise", "superhero" or "void". |
| `font_size` | `float \| None` | The body font size in pixels; None for the theme's. |
| `font_color` | `str \| None` | The body text color; None for the theme's. |
| `header_font_size` | `float \| None` | The header font size in pixels; None for the theme's. |
| `header_font_color` | `str \| None` | The header text color; None for the theme's. "hoverdark" and "hoverlight" have none. |
| `background_color` | `str \| None` | The table background; None for the theme's (most light themes have none: the page shows). |
| `cell_padding` | `float \| str \| None` | The cell padding, pixels or a CSS string; None for the theme's. |
| `centered` | `bool` | Center cell content vertically (useful with images). |
| `**theme_args` | `Any` | The theme's own extra arguments, by their reactablefmtr names: "nytimes" ``border_color``, ``border_width``; "sanfran" ``cell_color``, ``cell_border_width``, ``cell_border_color``, ``pagination_color``; "void" ``border_color``, ``border_width``, ``header_border_color``, ``header_border_width``. |

### Returns

`reactable.Theme` — The theme.

### Raises

- `InputError`: (a ValueError) If ``name`` is not one of the 27 themes (the message lists them), ``centered`` is not a bool, or an argument is not one the theme takes.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_theme

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [12, 10, 9]})
Reactable(df, theme=reactable_sdv_theme("espn"))
Reactable(df, theme=reactable_sdv_theme("midnight", font_size=13, centered=True))
```

### See also

- [Equivalent of reactablefmtr::espn, reactablefmtr::nytimes, reactablefmtr::fivethirtyeight and the other reactablefmtr themes](https://kcuilla.github.io/reactablefmtr/reference/index.html#themes)

## reactable_sdv_theme_team

<div class="sdv-signature">

```python
reactable_sdv_theme_team(
    team: Any,
    league: str,
    *,
    font_size: float | None = 15,
    font_color: str | None = None,
    header_font_size: float | None = 15,
    header_font_color: str | None = None,
    background_color: str | None = None,
    cell_padding: float | str | None = 6,
    centered: bool = False,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
) -> reactable.models.Theme
```

</div>

A table theme in a team's colors: the header filled with the primary color over a rule in the secondary,

stripes, hover and the current page button tinted with the primary, and every text color readable on its fill.

### Arguments

| Name | Type | Description |
|---|---|---|
| `team` | `Any` | The team, any value ``resolve`` accepts (an abbreviation, a name, an id). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `font_size` | `float \| None` | The body font size in pixels. |
| `font_color` | `str \| None` | The body text color as a hex color; None for black or white, whichever reads better on the background. |
| `header_font_size` | `float \| None` | The header font size in pixels. |
| `header_font_color` | `str \| None` | The header text color as a hex color; None for black or white, whichever reads better on the primary. |
| `background_color` | `str \| None` | The table background as a hex color; None for white (the page shows through). |
| `cell_padding` | `float \| str \| None` | The cell padding, pixels or a CSS string. |
| `centered` | `bool` | Center cell content vertically (useful with images). |
| `season` | `Any` | The season whose colors to use; None for today's. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team``, as in ``resolve``. |

### Returns

`reactable.Theme` — The theme.

### Raises

- `InputError`: (a ValueError) If ``league`` or ``id_system`` is unknown, ``centered`` is not a bool, or ``background_color``, ``font_color`` or ``header_font_color`` is not a hex color.
- `UnresolvedTeamError`: (a ValueError) If ``team`` does not resolve.

### Example

```python
import pandas as pd
from reactable import Reactable
from sdvplot.reactable import reactable_sdv_theme_team

df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [12, 10, 9]})
Reactable(df, theme=reactable_sdv_theme_team("KC", "nfl"))
```

### See also

- [sdvplot's addition to the reactablefmtr themes (reactablefmtr::espn and friends)](https://kcuilla.github.io/reactablefmtr/reference/index.html#themes)

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

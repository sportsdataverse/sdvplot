---
title: sdvplot.great_tables
sidebar_label: sdvplot.great_tables
sidebar_position: 24
---

# sdvplot.great_tables

great_tables helpers (``pip install sdvplot[tables]``), ported from sdvplotR's ``gt_*`` functions.

| Name | What it is |
|---|---|
| [add_headshots](#add_headshots) | Show each cell's player id as the player's headshot in a great_tables table. |
| [add_logos](#add_logos) | Show each cell's team as its logo in a great_tables table. |
| [add_wordmarks](#add_wordmarks) | Show each cell's team as its wordmark in a great_tables table. |
| [axis_logos](#axis_logos) | A table has no axes, so this always raises; ``gt_sdv_cols_label`` puts marks in the column labels instead. |
| [gt_538_caption](#gt_538_caption) | Add a FiveThirtyEight-style caption under the table: a top caption over a rule, then a bottom caption. |
| [gt_bold_rows](#gt_bold_rows) | Bold the body cells of chosen rows, optionally recoloring their text and filling them. |
| [gt_border_bars_bottom](#gt_border_bars_bottom) | Add a row of horizontal color bars below the table, optionally carrying text and an image. |
| [gt_border_bars_top](#gt_border_bars_top) | Add a row of horizontal color bars at the top of the table, optionally carrying text and an image. |
| [gt_border_grid](#gt_border_grid) | Draw borders between every column and every row, a full grid. |
| [gt_color_pills](#gt_color_pills) | Show values as rounded pills filled from a palette, by value or by rank. |
| [gt_color_ranks](#gt_color_ranks) | Fill the cells of columns that already hold ranks (1 is best), green to red by default. |
| [gt_color_results](#gt_color_results) | Fill and recolor each row by the win, loss or tie result in one column. |
| [gt_column_subheaders](#gt_column_subheaders) | Replace every column label with a two-line header: a heading over a smaller subtitle. |
| [gt_cutline](#gt_cutline) | Draw a rule across the table after a given row, with an optional label: the cut line of a ranked table. |
| [gt_delta](#gt_delta) | Add a column holding the change from one numeric column to another, signed and colored by direction. |
| [gt_fmt_rank](#gt_fmt_rank) | Format numbers as ordinals: 1 becomes 1st, 2 becomes 2nd, 23 becomes 23rd, 11-13 take "th". |
| [gt_fmt_tally](#gt_fmt_tally) | Combine two or more count columns into one ``"32-5"`` cell, optionally with one count's share of the total. |
| [gt_grid](#gt_grid) | Arrange several tables in a grid of rows and columns, as small multiples. |
| [gt_group_stripes](#gt_group_stripes) | Shade every other row group, so each group reads as a block. |
| [gt_highlight_cells](#gt_highlight_cells) | Fill the individual cells of a block of columns that meet a condition. |
| [gt_highlight_na](#gt_highlight_na) | Style, and optionally relabel, missing values. |
| [gt_indicator_boxes](#gt_indicator_boxes) | Replace values with colored boxes: filled when a value meets a rule, neutral otherwise. |
| [gt_legend_continuous](#gt_legend_continuous) | Add a color-scale legend that matches a column colored by ``gt_color_ranks``, ``gt_color_pills``, |
| [gt_legend_discrete](#gt_legend_discrete) | Add a key of labeled color swatches (home/away, tiers, conferences). |
| [gt_marginalia](#gt_marginalia) | Turn columns into margin notes: muted italic prose in a fixed-width column behind a hairline rule. |
| [gt_merge_stack_team_color](#gt_merge_stack_team_color) | Stack ``col1`` over ``col2`` in one cell: the top in bold small caps, the bottom in the team's color. |
| [gt_outliers](#gt_outliers) | Flag outlying values in numeric columns: colored (and bold) text, an optional fill, symbol and source note. |
| [gt_percentile_bar](#gt_percentile_bar) | Draw each percentile as a filled track with a round marker at its tip, the value printed in the marker. |
| [gt_row_accent](#gt_row_accent) | Draw a colored bar on the edge of each row, keyed to a column (a team color, a conference). |
| [gt_save_batch](#gt_save_batch) | Save a matched set of table images, one per group. |
| [gt_save_crop](#gt_save_crop) | Save a table to an image, trimmed to its content with an even border. |
| [gt_scale_note](#gt_scale_note) | Divide columns by a round number and say so: "Figures in thousands." or a "(000s)" label suffix. |
| [gt_sdv_cols_label](#gt_sdv_cols_label) | Replace the labels of team-named columns (a ``KC`` column, a ``BUF`` column, ...) with their marks. |
| [gt_sdv_headshots](#gt_sdv_headshots) | Show each cell's player id as the player's headshot in a great_tables table. |
| [gt_sdv_logos](#gt_sdv_logos) | Show each cell's team as its logo in a great_tables table. |
| [gt_sdv_wordmarks](#gt_sdv_wordmarks) | Show each cell's team as its wordmark in a great_tables table. |
| [gt_set_font](#gt_set_font) | Set one font family (and optionally a weight and style) on every part of the table. |
| [gt_significance](#gt_significance) | Append significance stars to estimates from paired p-value columns. |
| [gt_snake](#gt_snake) | Wrap a long table into side-by-side blocks (a top-50 list as two columns of 25). |
| [gt_snake_align](#gt_snake_align) | Reshape a frame the way ``gt_snake`` reshapes a table, so helper data (highlight masks, colors) lines up. |
| [gt_social_crop](#gt_social_crop) | Save a table centered on a canvas of a fixed aspect ratio, for social posts. |
| [gt_social_tag](#gt_social_tag) | Sign a table with social handles, each behind its platform's icon, under an optional caption. |
| [gt_spotlight](#gt_spotlight) | Light up some rows (bold, a fill, an accent bar) and dim everything else. |
| [gt_stack_tables](#gt_stack_tables) | Stack several tables vertically in one block, with an optional shared heading and footer. |
| [gt_theme_almanac](#gt_theme_almanac) | Record-book theme: a slab body, narrow condensed labels, tight rows and banded rows, like a statistical abstract. |
| [gt_theme_athletic](#gt_theme_athletic) | The Athletic's table look: a monospaced body, uppercase sans labels, dotted row rules and thin column rules. |
| [gt_theme_booktabs](#gt_theme_booktabs) | Academic booktabs theme: three horizontal rules and nothing else, the way LaTeX booktabs draws them. |
| [gt_theme_broadsheet](#gt_theme_broadsheet) | Newspaper theme: a serif body on warm paper, small letterspaced sans labels, hairlines between rows. |
| [gt_theme_brutalist](#gt_theme_brutalist) | Brutalist theme: heavy black frame, a knocked-out black label bar and one loud accent. |
| [gt_theme_drench](#gt_theme_drench) | Drenched theme: the whole table in one color, with rules, bands and muted text all derived from it. |
| [gt_theme_gtutils](#gt_theme_gtutils) | The gtUtils look: Almarai and Signika Negative on cream, taupe row rules and a taupe row-group band. |
| [gt_theme_kenpom](#gt_theme_kenpom) | KenPom's table look: blue-banded rows, a pale-blue label band with blue labels, black row rules. |
| [gt_theme_midnight](#gt_theme_midnight) | Dark theme: light type on a near-black ground, a raised label band and one cool accent. |
| [gt_theme_ncaa](#gt_theme_ncaa) | NCAA stats-site look: Open Sans, a black label band with white uppercase labels, striped rows, wide left inset. |
| [gt_theme_pl](#gt_theme_pl) | Premier League look: DM Sans in the league's deep purple, purple rules, a lilac row-group band. |
| [gt_theme_preview](#gt_theme_preview) | The same few rows in every table theme, one ``GT`` per theme, to compare them side by side. |
| [gt_theme_savant](#gt_theme_savant) | Baseball Savant's table look: Roboto Condensed, striped rows, a black row-group band, a centered heading. |
| [gt_theme_scoreboard](#gt_theme_scoreboard) | Scoreboard theme: condensed uppercase type under a solid header band, like a broadcast stat panel. |
| [gt_theme_sdv](#gt_theme_sdv) | The SportsDataverse house table: Chivo labels, a Lato body, and the SDV gradient under the column labels. |
| [gt_theme_sdv_team](#gt_theme_sdv_team) | ``gt_theme_sdv`` in one team's colors: a title block in the primary color, the line in the secondary. |
| [gt_theme_sofa](#gt_theme_sofa) | SofaScore's table look: Sofia Sans Condensed on a warm cream (or dark navy) ground, no rules between rows. |
| [gt_theme_swiss](#gt_theme_swiss) | International Typographic Style theme: a grotesque, generous space instead of rules, one accent rule. |
| [gt_theme_terminal](#gt_theme_terminal) | Terminal theme: a monospaced readout on a near-black ground, with a rule on every row. |
| [gt_theme_tier](#gt_theme_tier) | Tier-list look: Oswald on a near-black (or white) ground, centered columns, a rule under every row. |
| [gt_theme_tufte](#gt_theme_tufte) | Tufte theme: an old-style serif on cream, italic labels, one hairline under the labels and almost no ink. |
| [gt_tiers](#gt_tiers) | Build a tier list: a tier label column filled in each tier's color, the other columns rendered as images. |
| [gt_title_header](#gt_title_header) | Add a styled header: an optional kicker line, the title, the subtitle and a date line. |
| [gt_watermark](#gt_watermark) | Put a faint text or image watermark behind the table body. |
| [gt_wrap_labels](#gt_wrap_labels) | Wrap long column labels onto several lines, so narrow columns keep readable headers. |
| [pal_midnight](#pal_midnight) | A constant. |

## add_headshots

<div class="sdv-signature">

```python
add_headshots(
    gt: great_tables.gt.GT,
    columns: Any,
    *,
    league: str,
    height: Any = 30,
    locations: Any = None,
    id_system: str = 'espn',
) -> great_tables.gt.GT
```

</div>

Show each cell's player id as the player's headshot in a great_tables table.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | A great_tables ``GT``. |
| `columns` | `Any` | The columns of player ids. Ignored when ``locations`` is given (pass None). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `Any` | The image height in pixels. |
| `locations` | `Any` | Instead of the body of ``columns``: ``loc.body()``, ``loc.stub()`` or ``loc.row_groups()``, or a list of them (the locations great_tables' ``text_transform`` reaches). For marks in the column labels, use ``gt_sdv_cols_label``. |
| `id_system` | `str` | "espn" (ESPN athlete ids, any ESPN league) or "gsis" (NFL), as in ``headshot_url``. |

### Returns

`GT` — A new table; ids without a headshot keep their text, with one SdvplotWarning now.

### Raises

- `TypeError`: If ``gt`` is not a great_tables GT.
- `InputError`: (a ValueError) If ``height`` is not a number of pixels of at least 1, ``league`` has no ESPN headshots, or ``id_system`` is not valid for ``league``.
- `ValueError`: If ``columns`` names a column the table lacks, or ``locations`` holds another location.
- `OfflineError`: If ``id_system`` is "gsis" and the nflverse player table cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, when GitHub answers with an error status).
- `UnsafeDownloadError`: (an OSError) If ``id_system`` is "gsis" and the player table download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_sdv_headshots
import polars as pl

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_sdv_headshots(GT(df), "espn_id", league="nfl", height=40)
```

### See also

- [Ported from sdvplotR ``gt_sdv_headshots()``](https://sdvplotR.sportsdataverse.org/reference/gt_sdv_headshots.html)

## add_logos

<div class="sdv-signature">

```python
add_logos(
    gt: great_tables.gt.GT,
    columns: Any,
    *,
    league: str,
    height: Any = 30,
    locations: Any = None,
    include_name: bool = False,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
) -> great_tables.gt.GT
```

</div>

Show each cell's team as its logo in a great_tables table.

Values are resolved when you call this (team abbreviations, names and provider ids, as in ``resolve()``), so
unknown values warn once, now. They keep their text. The cell text is read as it renders now, so apply any
``fmt_*`` to the same column before this.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | A great_tables ``GT``. |
| `columns` | `Any` | The columns whose body cells become logos: a name, a list of names, or a polars selector. Ignored when ``locations`` is given (pass None). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `Any` | The image height in pixels. |
| `locations` | `Any` | Instead of the body of ``columns``: ``loc.body()``, ``loc.stub()`` or ``loc.row_groups()``, or a list of them (the locations great_tables' ``text_transform`` reaches). For marks in the column labels, use ``gt_sdv_cols_label``. |
| `include_name` | `bool` | Keep the cell's text after the logo. |
| `season` | `Any` | One season whose marks every cell shows (the ending year for the NHL, NBA, MBB and WBB); None for today's. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of the cell values, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a value does not resolve. |

### Returns

`GT` — A new table; ``gt`` is unchanged.

### Raises

- `TypeError`: If ``gt`` is not a great_tables GT.
- `InputError`: (a ValueError) If ``height`` is not a number of pixels of at least 1, ``league`` or ``id_system`` is unknown, or ``season`` is not one year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If ``columns`` names a column the table lacks, or ``locations`` holds another location.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a value does not resolve.
- `OfflineError`: If the logo manifest cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, when the CDN answers with an error status).
- `UnsafeDownloadError`: (an OSError) If the manifest download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_sdv_logos
import polars as pl

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_sdv_logos(GT(df), "team", league="nfl", height=24)
```

### See also

- [Ported from sdvplotR ``gt_sdv_logos()``](https://sdvplotR.sportsdataverse.org/reference/gt_sdv_logos.html)
- [great_tables](https://posit-dev.github.io/great-tables/)

## add_wordmarks

<div class="sdv-signature">

```python
add_wordmarks(
    gt: great_tables.gt.GT,
    columns: Any,
    *,
    league: str,
    height: Any = 30,
    locations: Any = None,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
) -> great_tables.gt.GT
```

</div>

Show each cell's team as its wordmark in a great_tables table.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | A great_tables ``GT``. |
| `columns` | `Any` | The columns whose body cells become wordmarks. Ignored when ``locations`` is given (pass None). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `Any` | The image height in pixels. |
| `locations` | `Any` | Instead of the body of ``columns``: ``loc.body()``, ``loc.stub()`` or ``loc.row_groups()``, or a list of them (the locations great_tables' ``text_transform`` reaches). For marks in the column labels, use ``gt_sdv_cols_label``. |
| `season` | `Any` | One season whose marks every cell shows; None for today's. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of the cell values, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a value does not resolve. |

### Returns

`GT` — A new table; unknown values keep their text, with one SdvplotWarning now.

### Raises

- `TypeError`: If ``gt`` is not a great_tables GT.
- `InputError`: (a ValueError) If ``height`` is not a number of pixels of at least 1, ``league`` or ``id_system`` is unknown, or ``season`` is not one year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If ``columns`` names a column the table lacks, or ``locations`` holds another location.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a value does not resolve.
- `OfflineError`: If the logo manifest cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, when the CDN answers with an error status).
- `UnsafeDownloadError`: (an OSError) If the manifest download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_sdv_wordmarks
import polars as pl

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_sdv_wordmarks(GT(df), "team", league="nfl")
```

### See also

- [Ported from sdvplotR ``gt_sdv_wordmarks()``](https://sdvplotR.sportsdataverse.org/reference/gt_sdv_wordmarks.html)

## axis_logos

<div class="sdv-signature">

```python
axis_logos(target: Any, *args: Any, **kwargs: Any) -> Any
```

</div>

A table has no axes, so this always raises; ``gt_sdv_cols_label`` puts marks in the column labels instead.

### Arguments

| Name | Description |
|---|---|
| `target` | A ``great_tables.GT``. |
| `*args` | Ignored. |
| `**kwargs` | Ignored. |

### Returns

`object` — Never returns.

### Raises

- `UnsupportedTargetError`: Always (a ``TypeError``).

### Example

```python
import polars as pl
from great_tables import GT
import sdvplot

gt = GT(pl.DataFrame({"team": ["KC", "BUF"], "wins": [12, 10]}))
try:
    sdvplot.axis_logos(gt, "team", league="nfl")
except TypeError:
    pass   # raised: a table has no axes
```

### See also

- [sdvplotR element_sdv_logo()](https://sdvplotR.sportsdataverse.org/)
- sdvplot.great_tables.gt_sdv_cols_label: marks in the column labels

## gt_538_caption

<div class="sdv-signature">

```python
gt_538_caption(
    gt: great_tables.gt.GT,
    *,
    top_caption: str | None = None,
    bottom_caption: str | None = None,
    rule_color: str | None = None,
    rule_width: float = 1,
    size: float = 12,
    align: str = 'right',
) -> great_tables.gt.GT
```

</div>

Add a FiveThirtyEight-style caption under the table: a top caption over a rule, then a bottom caption.

Both captions accept markdown (and raw HTML). great_tables renders source notes above footnotes, so both
captions are source notes (sdvplotR makes the top one a footnote): the top one carries the rule and ``size``,
the bottom one is aligned by ``align``. Apply the theme first: the rule color is read off the rendered table.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `top_caption` | `str \| None` | Text above the rule; ``None`` leaves out the rule too. |
| `bottom_caption` | `str \| None` | Text below the rule. |
| `rule_color` | `str \| None` | The rule's color; ``None`` takes the first text color in the rendered table (so it tracks a dark theme; a ``background-color`` or ``border-*-color`` is never taken), else a neutral gray. |
| `rule_width` | `float` | The rule width in pixels. |
| `size` | `float` | The top caption's font size in pixels. |
| `align` | `str` | The bottom caption's alignment: ``"left"``, ``"center"`` or ``"right"``. |

### Returns

`GT` — A new table with the captions.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: Neither caption was given, or ``align`` is unknown.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_538_caption

df = pl.DataFrame(
    {"car": ["Mazda", "Datsun", "Hornet"], "mpg": [21.0, 22.8, 18.7], "hp": [110, 93, 175],
     "disp": [160.0, 108.0, 360.0]}
)

gt_538_caption(GT(df), top_caption="Fuel economy and power", bottom_caption="Source: *Motor Trend*")
```

### See also

- Ported from sdvplotR ``gt_538_caption()``.

## gt_bold_rows

<div class="sdv-signature">

```python
gt_bold_rows(
    gt: great_tables.gt.GT,
    rows: Any = None,
    text_color: str = 'black',
    highlight_color: str | None = None,
) -> great_tables.gt.GT
```

</div>

Bold the body cells of chosen rows, optionally recoloring their text and filling them.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `rows` | `Any` | The rows to bold, as great_tables' ``loc.body(rows=)`` takes them: a 0-based position or list of positions, a polars expression (polars data) or a callable returning a boolean Series (pandas data). ``None`` bolds every row. |
| `text_color` | `str` | Text color of the bolded rows. |
| `highlight_color` | `str \| None` | Background fill of the bolded rows; ``None`` for no fill. |

### Returns

`GT` — A new table; ``gt`` is unchanged. When ``rows`` matches nothing, ``gt`` itself, with one SdvplotWarning.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_bold_rows

df = pl.DataFrame(
    {"car": ["Mazda", "Datsun", "Hornet"], "mpg": [21.0, 22.8, 18.7], "hp": [110, 93, 175],
     "disp": [160.0, 108.0, 360.0]}
)

gt_bold_rows(GT(df), rows=pl.col("mpg") > 20, highlight_color="#FFF3B0")
```

### See also

- Ported from sdvplotR ``gt_bold_rows()``.

## gt_border_bars_bottom

<div class="sdv-signature">

```python
gt_border_bars_bottom(
    gt: great_tables.gt.GT,
    colors: str | collections.abc.Sequence[str],
    *,
    bar_height: float = 10,
    bar_width: str = '100%',
    bar_align: str = 'center',
    img: str | None = None,
    img_width: float = 30,
    img_height: float = 30,
    img_padding: float = 10,
    img_align: str = 'right',
    text: str | None = None,
    text_weight: str = 'bold',
    text_color: str = '#FFFFFF',
    text_size: float = 18,
    text_align: str = 'left',
    text_padding: float = 10,
) -> great_tables.gt.GT
```

</div>

Add a row of horizontal color bars below the table, optionally carrying text and an image.

The bottom-edge counterpart of ``gt_border_bars_top``: the bars are a source note, and the source notes lose
their side and bottom padding so the bars reach the table's edges. The text uses the font set on the source
notes (imported from Google Fonts) or inherits.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `colors` | `str \| collections.abc.Sequence[str]` | One color per bar (only the first is used with ``text`` or ``img``). |
| `bar_height` | `float` | Bar height in pixels. |
| `bar_width` | `str` | Width of the bar block, as a CSS width. |
| `bar_align` | `str` | ``"left"``, ``"center"`` or ``"right"``, when ``bar_width`` is under 100%. |
| `img` | `str \| None` | URL of an image to show in the bar. |
| `img_width` | `float` | Image width in pixels. |
| `img_height` | `float` | Image height in pixels. |
| `img_padding` | `float` | Padding beside the image in pixels. |
| `img_align` | `str` | The side of the image the padding goes on (``"left"`` or ``"right"``). |
| `text` | `str \| None` | Text to show in the bar. |
| `text_weight` | `str` | Font weight of the text. |
| `text_color` | `str` | Text color. |
| `text_size` | `float` | Text size in pixels. |
| `text_align` | `str` | The side of the text the padding goes on (``"left"`` or ``"right"``). |
| `text_padding` | `float` | Padding beside the text in pixels. |

### Returns

`GT` — A new table with the bars below it.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: ``bar_align``, ``img_align`` or ``text_align`` is not one of its listed values.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_border_bars_bottom

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_border_bars_bottom(GT(df), "#22223B", text="Source: ESPN", bar_height=28)
```

### See also

- Ported from sdvplotR ``gt_border_bars_bottom()``.

## gt_border_bars_top

<div class="sdv-signature">

```python
gt_border_bars_top(
    gt: great_tables.gt.GT,
    colors: str | collections.abc.Sequence[str],
    *,
    bar_height: float = 10,
    bar_width: str = '100%',
    bar_align: str = 'center',
    img: str | None = None,
    img_width: float = 30,
    img_height: float = 30,
    img_padding: float = 10,
    img_align: str = 'right',
    text: str | None = None,
    text_weight: str = 'bold',
    text_color: str = '#FFFFFF',
    text_size: float = 18,
    text_align: str = 'left',
    text_padding: float = 10,
) -> great_tables.gt.GT
```

</div>

Add a row of horizontal color bars at the top of the table, optionally carrying text and an image.

With neither ``text`` nor ``img``, each color is its own full-width bar, stacked. With either, one bar in the
first color holds the text at one end and the image at the other; the text uses the font set on the title
(imported from Google Fonts) or inherits. great_tables has no ``tab_caption``, so the bars go at the top of
the heading, above the title: call this after ``tab_header``.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `colors` | `str \| collections.abc.Sequence[str]` | One color per bar (only the first is used with ``text`` or ``img``). |
| `bar_height` | `float` | Bar height in pixels. |
| `bar_width` | `str` | Width of the bar block, as a CSS width. |
| `bar_align` | `str` | ``"left"``, ``"center"`` or ``"right"``, when ``bar_width`` is under 100%. |
| `img` | `str \| None` | URL of an image to show in the bar. |
| `img_width` | `float` | Image width in pixels. |
| `img_height` | `float` | Image height in pixels. |
| `img_padding` | `float` | Padding beside the image in pixels. |
| `img_align` | `str` | The side of the image the padding goes on (``"left"`` or ``"right"``). |
| `text` | `str \| None` | Text to show in the bar. |
| `text_weight` | `str` | Font weight of the text. |
| `text_color` | `str` | Text color. |
| `text_size` | `float` | Text size in pixels. |
| `text_align` | `str` | The side of the text the padding goes on (``"left"`` or ``"right"``). |
| `text_padding` | `float` | Padding beside the text in pixels. |

### Returns

`GT` — A new table with the bars above its title.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: ``bar_align``, ``img_align`` or ``text_align`` is not one of its listed values.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_border_bars_top

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_border_bars_top(GT(df).tab_header("Standings"), ["#1B7837", "#FFFFFF", "#B2182B"])
```

### See also

- Ported from sdvplotR ``gt_border_bars_top()``.

## gt_border_grid

<div class="sdv-signature">

```python
gt_border_grid(
    gt: great_tables.gt.GT,
    color: str = 'black',
    weight: float = 1,
    include_labels: bool = False,
) -> great_tables.gt.GT
```

</div>

Draw borders between every column and every row, a full grid.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `color` | `str` | Border color. |
| `weight` | `float` | Border thickness in pixels. |
| `include_labels` | `bool` | Extend the column borders through the column labels. |

### Returns

`GT` — A new table with the grid.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_border_grid

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_border_grid(GT(df), color="#BBBBBB", weight=2, include_labels=True)
```

### See also

- Ported from sdvplotR ``gt_border_grid()`` (which uses gtExtras ``gt_add_divider``).

## gt_color_pills

<div class="sdv-signature">

```python
gt_color_pills(
    gt: great_tables.gt.GT,
    columns: Any,
    *,
    rows: Any = None,
    palette: collections.abc.Sequence[str] = ('#C84630', '#5DA271'),
    fill_type: str = 'continuous',
    rank_order: str = 'desc',
    digits: int | None = None,
    domain: collections.abc.Sequence[float] | None = None,
    format_type: str = 'number',
    scale_percent: bool = True,
    suffix: str = '',
    reverse: bool = False,
    outline_color: str | None = None,
    outline_width: float = 0.25,
    pal_type: str = 'discrete',
    pill_height: float = 25,
    text_color: str | None = None,
    na_color: str | None = None,
) -> great_tables.gt.GT
```

</div>

Show values as rounded pills filled from a palette, by value or by rank.

Several columns share one ``domain`` (taken from them all when unset, with a warning) so their colors compare;
pill width is set per column. With ``fill_type="rank"`` each column is ranked against itself (average ties).
The text is black or white, whichever reads better on the fill, unless ``text_color`` is set. A value outside
``domain`` is drawn grey (``#808080``) with one warning. The scale is recorded for ``gt_legend_continuous``.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The columns to fill. |
| `rows` | `Any` | The rows to fill, as great_tables' ``loc.body(rows=)`` takes them; the rest keep their value. ``None`` fills every row. |
| `palette` | `collections.abc.Sequence[str]` | Hex colors, low to high. |
| `fill_type` | `str` | ``"continuous"`` (by value) or ``"rank"``. |
| `rank_order` | `str` | ``"desc"`` (the largest value ranks 1) or ``"asc"``, for ``fill_type="rank"``. |
| `digits` | `int \| None` | Decimal places of the printed value; ``None`` prints it naturally. |
| `domain` | `collections.abc.Sequence[float] \| None` | ``(low, high)`` mapped onto the palette; ``None`` uses the observed range and warns. |
| `format_type` | `str` | ``"number"``, ``"comma"``, ``"currency"`` or ``"percent"``. |
| `scale_percent` | `bool` | Multiply by 100 for ``format_type="percent"``. |
| `suffix` | `str` | Appended to each printed value, such as ``"M"``. |
| `reverse` | `bool` | Reverse the palette. |
| `outline_color` | `str \| None` | A border color around each pill; ``None`` for none. |
| `outline_width` | `float` | The border width in pixels. |
| `pal_type` | `str` | ``"discrete"`` or ``"continuous"``; recorded for the legend only (sdvplotR uses it to look up paletteer palettes, which Python does not have). |
| `pill_height` | `float` | Pill height in pixels. |
| `text_color` | `str \| None` | The pill text color; ``None`` picks black or white per pill. |
| `na_color` | `str \| None` | A hex color for a pill over a missing value (a translucent ``#rrggbbaa`` is drawn as given); ``None`` leaves the cell blank. |

### Returns

`GT` — A new table with pills, recording ``_sdvplot_scale``; ``gt`` itself, with one SdvplotWarning, when ``rows`` matches nothing.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: ``columns`` matches nothing; the palette is not a list of hex colors; an option is not one of its listed values; or there is no ``domain`` and no numeric value to derive one from.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_color_pills

df = pl.DataFrame(
    {"car": ["Mazda", "Datsun", "Hornet"], "mpg": [21.0, 22.8, 18.7], "hp": [110, 93, 175],
     "disp": [160.0, 108.0, 360.0]}
)

gt_color_pills(GT(df), ["disp", "hp"], domain=(50, 500))
gt_color_pills(GT(df), "hp", fill_type="rank", domain=(1, 6), digits=0)
```

### See also

- Ported from sdvplotR ``gt_color_pills()``
- ``gt_color_ranks`` fills the whole cell.

## gt_color_ranks

<div class="sdv-signature">

```python
gt_color_ranks(
    gt: great_tables.gt.GT,
    columns: Any,
    *,
    rows: Any = None,
    palette: collections.abc.Sequence[str] = ('#3D8B6E', '#9DC5A7', '#EDE0CC', '#DB9070', '#BE4D3A'),
    domain: collections.abc.Sequence[float] | None = None,
    reverse: bool = False,
    na_color: str = 'white',
    autocolor_text: bool = True,
    pal_type: str = 'discrete',
    **data_color_kwargs: Any,
) -> great_tables.gt.GT
```

</div>

Fill the cells of columns that already hold ranks (1 is best), green to red by default.

A shorthand around great_tables' ``data_color``: the values are colored as they are, no ranking is computed.
The domain is shared across the columns (rank 1 and the largest rank present anchor the ends) unless given.
The scale is recorded for ``gt_legend_continuous``.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The columns to color. |
| `rows` | `Any` | The rows to color, as great_tables' ``loc.body(rows=)`` takes them; ``None`` colors every row. |
| `palette` | `collections.abc.Sequence[str]` | Hex colors, low to high. |
| `domain` | `collections.abc.Sequence[float] \| None` | ``(low, high)`` mapped onto the palette; ``None`` uses the selected columns' range. |
| `reverse` | `bool` | Reverse the palette. |
| `na_color` | `str` | The fill of missing values. |
| `autocolor_text` | `bool` | Set each cell's text to black or white for contrast. |
| `pal_type` | `str` | ``"discrete"`` or ``"continuous"``; recorded for the legend only. |
| `**data_color_kwargs` | `Any` | Passed to ``GT.data_color`` (``alpha``, ``truncate``). |

### Returns

`GT` — A new table, recording ``_sdvplot_scale``; ``gt`` itself, with one SdvplotWarning, when ``rows`` matches nothing.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: ``columns`` matches nothing, the palette is not a list of hex colors, or there is no ``domain`` and no numeric value to derive one from.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_color_ranks

ranked = pl.DataFrame({"team": ["KC", "BUF", "BAL"], "off_rank": [1, 3, 2], "def_rank": [5, 2, 1]})

gt_color_ranks(GT(ranked), ["off_rank", "def_rank"])
```

### See also

- Ported from sdvplotR ``gt_color_ranks()``
- ``gt_color_pills`` draws pills instead.

## gt_color_results

<div class="sdv-signature">

```python
gt_color_results(
    gt: great_tables.gt.GT,
    result_column: Any = 'result',
    *,
    win_color: str = '#5DA271',
    loss_color: str = '#C84630',
    tie_color: str | None = None,
    wins_text_color: str = 'white',
    loss_text_color: str = 'white',
    tie_text_color: str = 'white',
    tie_value: Any = 'T',
    result_type: str = 'wl',
) -> great_tables.gt.GT
```

</div>

Fill and recolor each row by the win, loss or tie result in one column.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `result_column` | `Any` | The column holding the results, as any great_tables selection of exactly one column. |
| `win_color` | `str` | Fill of winning rows. |
| `loss_color` | `str` | Fill of losing rows. |
| `tie_color` | `str \| None` | Fill of tie rows; ``None`` leaves ties alone. |
| `wins_text_color` | `str` | Text color of winning rows. |
| `loss_text_color` | `str` | Text color of losing rows. |
| `tie_text_color` | `str` | Text color of tie rows. |
| `tie_value` | `Any` | The value marking a tie (used when ``tie_color`` is set). |
| `result_type` | `str` | ``"wl"`` for ``"W"``/``"L"`` values, or ``"binary"`` for ``1``/``0``. |

### Returns

`GT` — A new table; rows matching no result keep their styling.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: ``result_column`` does not select exactly one column, or ``result_type`` is unknown.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_color_results

games = pl.DataFrame({"opp": ["BUF", "BAL", "SF"], "result": ["W", "L", "W"]})

gt_color_results(GT(games), result_column="result")
```

### See also

- Ported from sdvplotR ``gt_color_results()``.

## gt_column_subheaders

<div class="sdv-signature">

```python
gt_column_subheaders(
    gt: great_tables.gt.GT,
    *,
    heading_color: str = 'black',
    subtitle_color: str = '#808080',
    heading_weight: str = 'bold',
    subtitle_weight: str = 'normal',
    heading_size: float = 14,
    subtitle_size: float = 10,
    font: str | None = None,
    **subheaders: dict[str, str],
) -> great_tables.gt.GT
```

</div>

Replace every column label with a two-line header: a heading over a smaller subtitle.

Every column is relabeled. A column not named in ``subheaders`` keeps its name as the heading and gets a
non-breaking space as the subtitle, so the headers stay aligned. Call it after other label changes.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `heading_color` | `str` | Heading text color. |
| `subtitle_color` | `str` | Subtitle text color. |
| `heading_weight` | `str` | Heading font weight. |
| `subtitle_weight` | `str` | Subtitle font weight. |
| `heading_size` | `float` | Heading size in pixels. |
| `subtitle_size` | `float` | Subtitle size in pixels. |
| `font` | `str \| None` | A CSS font family for both lines (not imported: it must be installed or loaded by the theme). |
| `**subheaders` | `dict[str, str]` | ``column={"heading": ..., "subtitle": ...}`` per column (either key may be left out). A column named like one of this function's arguments cannot be given this way. |

### Returns

`GT` — A new table with stacked labels.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: A ``subheaders`` key is not a column of the table.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_column_subheaders

df = pl.DataFrame(
    {"car": ["Mazda", "Datsun", "Hornet"], "mpg": [21.0, 22.8, 18.7], "hp": [110, 93, 175],
     "disp": [160.0, 108.0, 360.0]}
)

gt_column_subheaders(GT(df), hp={"heading": "Horsepower", "subtitle": "HP"}, heading_color="blue")
```

### See also

- Ported from sdvplotR ``gt_column_subheaders()``.

## gt_cutline

<div class="sdv-signature">

```python
gt_cutline(
    gt: great_tables.gt.GT,
    after: int | collections.abc.Sequence[int],
    *,
    label: str | collections.abc.Sequence[str | None] | None = None,
    color: str = '#A6081A',
    weight: float = 2,
    style: str = 'dashed',
    label_color: str | None = None,
    label_size: float = 9,
    label_position: str = 'below',
    gap: float | collections.abc.Sequence[float] = 0,
) -> great_tables.gt.GT
```

</div>

Draw a rule across the table after a given row, with an optional label: the cut line of a ranked table.

The label is an inline SVG background on the row (CSS pseudo-elements do not survive inlining), so it renders
in a system sans-serif, and the labeled row's cell fills are cleared (its stripe is repainted on the row).
Labels assume the table has no row groups. Apply the theme first: the stripe color is read from its options.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `after` | `int \| collections.abc.Sequence[int]` | The number of rows above each line: ``4`` draws between the 4th and 5th rows, ``0`` above the first. One whole number or several (numpy integers included). |
| `label` | `str \| collections.abc.Sequence[str \| None] \| None` | A label per line, recycled against ``after``; ``None`` in a list leaves that line unlabeled. Drawn in uppercase. |
| `color` | `str` | The rule color. |
| `weight` | `float` | The rule thickness in pixels. |
| `style` | `str` | ``"dashed"``, ``"solid"`` or ``"dotted"``. |
| `label_color` | `str \| None` | The label color; ``None`` uses ``color``. |
| `label_size` | `float` | The label size in pixels. |
| `label_position` | `str` | ``"below"`` or ``"above"`` the line. |
| `gap` | `float \| collections.abc.Sequence[float]` | Extra space in pixels around each line: one number for both sides, or ``(above, below)``. |

### Returns

`GT` — A new table with the lines; ``gt`` itself, with one SdvplotWarning, when every line is out of range.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: ``after`` is not numeric or not a whole number, ``gap`` is not one or two non-negative numbers, or ``style`` or ``label_position`` is unknown.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_cutline

standings = pl.DataFrame(
    {
        "team": ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"],
        "wins": [14, 13, 12, 11, 10, 9, 8, 7],
    }
)

gt_cutline(GT(standings), after=6, label="Playoff line")
```

### See also

- Ported from sdvplotR ``gt_cutline()``.

## gt_delta

<div class="sdv-signature">

```python
gt_delta(
    gt: great_tables.gt.GT,
    from_: Any,
    to: Any,
    *,
    column_label: str = 'Change',
    percent: bool = False,
    decimals: int = 1,
    arrows: bool = False,
    color: bool = True,
    color_positive: str = '#1B7837',
    color_negative: str = '#B2182B',
    color_neutral: str | None = None,
    force_sign: bool = True,
    after: int | str | None = None,
) -> great_tables.gt.GT
```

</div>

Add a column holding the change from one numeric column to another, signed and colored by direction.

The change is ``to - from_`` (or that over ``from_`` with ``percent=True``). A row is blank where either value
is missing, or a percent change divides by zero. With ``arrows`` a triangle leads the magnitude in place of a
sign.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `from_` | `Any` | The starting column (``from`` is a Python keyword). |
| `to` | `Any` | The ending column. |
| `column_label` | `str` | The new column's label. |
| `percent` | `bool` | Show the change as a percent of ``from_``. |
| `decimals` | `int` | Decimal places. |
| `arrows` | `bool` | Lead each value with an up or down triangle instead of a sign. |
| `color` | `bool` | Color the values by direction. |
| `color_positive` | `str` | Color of an increase. |
| `color_negative` | `str` | Color of a decrease. |
| `color_neutral` | `str \| None` | Color of no change; ``None`` leaves it the table's text color. |
| `force_sign` | `bool` | Show a plus on an increase (ignored with ``arrows``). |
| `after` | `int \| str \| None` | The column the new one follows, a name or a 0-based position in the data; ``None`` places it after ``to``. |

### Returns

`GT` — A new table with the change column (right-aligned).

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: ``from_`` or ``to`` does not select a single column, or ``after`` names no column.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_delta

revenue = pl.DataFrame({"team": ["KC", "BUF"], "q1": [100.0, 80.0], "q2": [120.0, 70.0]})

gt_delta(GT(revenue), "q1", "q2")
gt_delta(GT(revenue), "q1", "q2", percent=True, arrows=True)
```

### See also

- Ported from sdvplotR ``gt_delta()``.

## gt_fmt_rank

<div class="sdv-signature">

```python
gt_fmt_rank(
    gt: great_tables.gt.GT,
    columns: Any,
    superscript: bool = True,
    suffix_size: str = '0.7em',
) -> great_tables.gt.GT
```

</div>

Format numbers as ordinals: 1 becomes 1st, 2 becomes 2nd, 23 becomes 23rd, 11-13 take "th".

Applied to the rendered cell text; a cell that does not read as a number is left alone.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The columns to format. |
| `superscript` | `bool` | Render the suffix as superscript. |
| `suffix_size` | `str` | The suffix size, as a CSS size. |

### Returns

`GT` — A new table with ordinal formatting.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_fmt_rank

standings = pl.DataFrame({"team": ["KC", "BUF", "BAL"], "place": [1, 2, 3]})

gt_fmt_rank(GT(standings), "place", superscript=False)
```

### See also

- Ported from sdvplotR ``gt_fmt_rank()``.

## gt_fmt_tally

<div class="sdv-signature">

```python
gt_fmt_tally(
    gt: great_tables.gt.GT,
    columns: Any,
    *,
    separator: str = '-',
    label: str | None = None,
    share: bool = False,
    share_of: int | str = 0,
    share_location: str = 'inline',
    share_decimals: int = 1,
    share_label: str = '%',
    share_prefix: str = ' (',
    share_suffix: str = ')',
    **fmt_percent_kwargs: Any,
) -> great_tables.gt.GT
```

</div>

Combine two or more count columns into one ``"32-5"`` cell, optionally with one count's share of the total.

The tally goes in the first column and the others are hidden (or the last one carries the share). A row with a
missing count is left alone, and the share is blank where the counts sum to zero.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The count columns, in reading order (two or more). |
| `separator` | `str` | Placed between the counts. |
| `label` | `str \| None` | A new label for the combined column; ``None`` keeps its label. |
| `share` | `bool` | Show one count as a share of the row total. |
| `share_of` | `int \| str` | The count the share is computed for: a 0-based position in ``columns`` or a column name. |
| `share_location` | `str` | ``"inline"`` (appended to the tally) or ``"column"`` (the last count column carries it). |
| `share_decimals` | `int` | Decimal places of the share. |
| `share_label` | `str` | The share column's label when ``share_location="column"``. |
| `share_prefix` | `str` | Placed before an inline share. |
| `share_suffix` | `str` | Placed after an inline share. |
| `**fmt_percent_kwargs` | `Any` | Passed to great_tables ``vals.fmt_percent``. |

### Returns

`GT` — A new table with the counts combined.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: Fewer than two columns, ``share_of`` is not one of them, or ``share_location`` is unknown.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_fmt_tally

suites = pl.DataFrame({"suite": ["unit", "live"], "passed": [142, 30], "failed": [8, 2]})
league = pl.DataFrame({"team": ["KC", "BUF"], "w": [12, 10], "d": [0, 1], "l": [5, 6]})

gt_fmt_tally(GT(suites), ["passed", "failed"], share=True)          # "142-8 (94.7%)"
gt_fmt_tally(GT(league), ["w", "d", "l"], label="W-D-L")
```

### See also

- Ported from sdvplotR ``gt_fmt_tally()``.

## gt_grid

<div class="sdv-signature">

```python
gt_grid(
    tables: collections.abc.Sequence[great_tables.gt.GT] | collections.abc.Mapping[Any, great_tables.gt.GT] | None = None,
    *,
    ncol: int = 2,
    labels: Any = None,
    label_style: collections.abc.Mapping[str, Any] | None = None,
    title: Any = None,
    subtitle: Any = None,
    caption: Any = None,
    source_note: Any = None,
    caption_rule: bool = False,
    title_style: collections.abc.Mapping[str, Any] | None = None,
    subtitle_style: collections.abc.Mapping[str, Any] | None = None,
    caption_style: collections.abc.Mapping[str, Any] | None = None,
    source_note_style: collections.abc.Mapping[str, Any] | None = None,
    gap: float = 24,
    align: str = 'top',
    file: str | os.PathLike[str] | None = None,
    bg: str = 'white',
    whitespace: int = 50,
    zoom: float = 2,
) -> Any
```

</div>

Arrange several tables in a grid of rows and columns, as small multiples.

The grid is HTML, not a ``GT``: each table keeps its own columns and header, so this is a last step after every
table is themed. Give ``file`` to write it straight to an image.

### Arguments

| Name | Type | Description |
|---|---|---|
| `tables` | `collections.abc.Sequence[great_tables.gt.GT] \| collections.abc.Mapping[Any, great_tables.gt.GT] \| None` | A list of ``GT`` objects (a dict's values are used in order, so ``gt_theme_preview()``'s dict works). |
| `ncol` | `int` | The number of tables across. |
| `labels` | `Any` | A caption above each table, recycled across ``tables``: a string, ``md()``/``html()`` text, or a non-empty list of them. Plain strings are escaped; use ``html()`` for markup. |
| `label_style` | `collections.abc.Mapping[str, Any] \| None` | Style for the labels (see ``title_style``). |
| `title` | `Any` | A heading above the whole grid: a string, ``md()`` or ``html()``. Plain strings are escaped (as in great_tables); use ``html()`` for markup. ``subtitle``, ``caption`` and ``source_note`` take the same. |
| `subtitle` | `Any` | A line below ``title``. |
| `caption` | `Any` | A note below the grid. |
| `source_note` | `Any` | A second line below ``caption``, right-aligned by default. |
| `caption_rule` | `bool` | Draw a hairline between ``caption`` and ``source_note``. |
| `title_style` | `collections.abc.Mapping[str, Any] \| None` | A dict of any of ``font`` (a Google font name), ``size``, ``color``, ``weight``, ``italic``, ``spacing``, ``transform``, ``align``, ``line_height``, ``margin_top``, ``margin_bottom``, ``padding_top``, ``padding_bottom``. Lengths take a number (pixels) or a CSS string; keys left out keep their defaults. |
| `subtitle_style` | `collections.abc.Mapping[str, Any] \| None` | As ``title_style``, for the subtitle. |
| `caption_style` | `collections.abc.Mapping[str, Any] \| None` | As ``title_style``, for the caption. |
| `source_note_style` | `collections.abc.Mapping[str, Any] \| None` | As ``title_style``, for the source note. |
| `gap` | `float` | The space between tables, a non-negative number of pixels. |
| `align` | `str` | How tables of differing height line up in a row: ``"top"``, ``"center"`` or ``"bottom"``. |
| `file` | `str \| os.PathLike[str] \| None` | A path to write an image to; ``None`` returns the HTML. |
| `bg` | `str` | The background color when saving. |
| `whitespace` | `int` | Padding, in pixels, around the grid when saving. |
| `zoom` | `float` | The rendering zoom when saving. |

### Returns

htmltools.Tag | str | os.PathLike: The grid as HTML (it displays in a notebook), or ``file`` after writing it.

### Raises

- `TypeError`: If ``tables`` holds anything but ``GT`` objects.
- `TypeError`: If ``labels`` is neither text nor a list of it.
- `ValueError`: If ``tables`` or ``labels`` is empty, ``ncol`` is below 1, ``gap`` is not a non-negative number, ``zoom`` is not a positive number, ``align`` or a style key is unknown, or (when saving) ``bg``, ``whitespace`` or the extension of ``file`` is invalid.
- `nokap.ChromeNotFoundError`: If saving and no Chrome or Chromium is installed.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_grid

east = GT(pl.DataFrame({"team": ["BUF", "MIA"], "wins": [11, 9]}))
west = GT(pl.DataFrame({"team": ["KC", "LV"], "wins": [12, 8]}))
north = GT(pl.DataFrame({"team": ["BAL", "CIN"], "wins": [10, 9]}))
south = GT(pl.DataFrame({"team": ["HOU", "IND"], "wins": [10, 8]}))

gt_grid([east, west, north, south], ncol=2, title="Division leaders", caption="Data: ESPN")
gt_grid([east, west], file="divisions.png", bg="#FBFAF7")
```

### See also

- [gt_stack_tables: a vertical stack. Ported from sdvplotR ``gt_grid()``](https://sdvplotR.sportsdataverse.org/reference/gt_grid.html)

## gt_group_stripes

<div class="sdv-signature">

```python
gt_group_stripes(
    gt: great_tables.gt.GT,
    color: str = '#F5F5F5',
    start: int = 2,
    include_stub: bool = True,
) -> great_tables.gt.GT
```

</div>

Shade every other row group, so each group reads as a block.

Groups are banded in the order they render (``GT.row_group_order``), not the order they appear in the data.
Group heading rows are left alone.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. It must have row groups (``GT(data, groupname_col=...)``). |
| `color` | `str` | Fill of the banded groups. |
| `start` | `int` | ``2`` leaves the first group unshaded, ``1`` shades it. |
| `include_stub` | `bool` | Band the stub column along with the body. |

### Returns

`GT` — A new table with alternate groups banded; ``gt`` itself, with one SdvplotWarning, when the table has no row groups.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: ``start`` is not 1 or 2.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_group_stripes

df = pl.DataFrame({"conference": ["AFC", "AFC", "NFC", "NFC"], "team": ["KC", "BUF", "SF", "DAL"]})

gt_group_stripes(GT(df, groupname_col="conference"), color="#FBF3E4", start=1)
```

### See also

- Ported from sdvplotR ``gt_group_stripes()``.

## gt_highlight_cells

<div class="sdv-signature">

```python
gt_highlight_cells(
    gt: great_tables.gt.GT,
    columns: Any,
    condition: collections.abc.Callable[[Any], Any] | Any,
    *,
    fill: str = '#FFF3B0',
    text_color: str | None = None,
    bold: bool = False,
    **text_kwargs: Any,
) -> great_tables.gt.GT
```

</div>

Fill the individual cells of a block of columns that meet a condition.

Each selected column is tested and filled on its own, so the filled cells can form a diagonal, a checker or
any scatter (one ``tab_style`` over ``loc.body`` would fill a whole rectangle).

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The block of columns to test. |
| `condition` | `collections.abc.Callable[[Any], Any] \| Any` | A callable applied to each column's data (a pandas or polars Series, as the table holds) that returns one boolean per row, such as ``lambda s: s > 0.7``; or a mask computed ahead of time with one column per selected column (a pandas or polars DataFrame, or a 2-D sequence or array of rows). Missing counts as not matched. |
| `fill` | `str` | Fill of the matching cells. |
| `text_color` | `str \| None` | Text color of the matching cells; ``None`` leaves it alone. |
| `bold` | `bool` | Bold the matching cells. |
| `**text_kwargs` | `Any` | Passed to great_tables ``style.text`` for the matching cells, such as ``style="italic"``. |

### Returns

`GT` — A new table with the matching cells filled.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: ``columns`` matches nothing, the mask has the wrong number of columns, or ``condition`` fails on a column or does not return one value per row.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_highlight_cells

cor_df = pl.DataFrame({"var": ["mpg", "hp"], "mpg": [1.0, -0.78], "hp": [-0.78, 1.0]})

gt_highlight_cells(GT(cor_df, rowname_col="var"), ["mpg", "hp"], lambda s: s > 0.7, fill="#FFD1A9")
```

### See also

- Ported from sdvplotR ``gt_highlight_cells()``.

## gt_highlight_na

<div class="sdv-signature">

```python
gt_highlight_na(
    gt: great_tables.gt.GT,
    columns: Any = None,
    *,
    fill: str | None = '#F0F0F0',
    text_color: str | None = None,
    bold: bool = False,
    italic: bool = False,
    missing_text: str | None = None,
    na_strings: str | collections.abc.Sequence[str] = 'NA',
    ignore_case: bool = False,
    **text_kwargs: Any,
) -> great_tables.gt.GT
```

</div>

Style, and optionally relabel, missing values.

Missing means a real null/NaN or a value whose trimmed text is one of ``na_strings`` (a CSV's ``"NA"``,
by default).

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The columns to check; ``None`` checks every body column. |
| `fill` | `str \| None` | Fill behind missing values; ``None`` for no fill. |
| `text_color` | `str \| None` | Text color of missing values. |
| `bold` | `bool` | Bold missing values. |
| `italic` | `bool` | Italicize missing values. |
| `missing_text` | `str \| None` | Replacement text for missing values, such as ``"--"``; ``None`` leaves the text alone. |
| `na_strings` | `str \| collections.abc.Sequence[str]` | Strings treated as missing alongside real nulls. |
| `ignore_case` | `bool` | Match ``na_strings`` case-insensitively. |
| `**text_kwargs` | `Any` | Passed to great_tables ``style.text``. |

### Returns

`GT` — A new table with missing values styled.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: ``columns`` names a column the table lacks.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_highlight_na

df = pl.DataFrame({"day": [1, 2, 3], "ozone": [41.0, None, 28.0], "solar": [190.0, 118.0, None]})

gt_highlight_na(GT(df), ["ozone", "solar"], missing_text="not recorded", italic=True)
```

### See also

- Ported from sdvplotR ``gt_highlight_na()``.

## gt_indicator_boxes

<div class="sdv-signature">

```python
gt_indicator_boxes(
    gt: great_tables.gt.GT,
    columns: Any = None,
    *,
    key_columns: Any = None,
    indicator_vals: collections.abc.Sequence[float] = (0, 1),
    indicator_rule: collections.abc.Callable[..., Any] | None = None,
    color_yes: str = '#FCCF10',
    color_no: str = '#EEEEEE',
    show_na_as_na: bool = False,
    show_text: bool = False,
    show_only: str | None = None,
    per_column_formats: dict[str, dict[str, Any]] | None = None,
    color_na: str | None = None,
    border_color: str | None = None,
    border_width: float = 0.25,
    box_width: float = 20,
    box_height: float = 20,
    text_size: float = 12,
    text_weight: str = 'bold',
) -> great_tables.gt.GT
```

</div>

Replace values with colored boxes: filled when a value meets a rule, neutral otherwise.

By default a box is filled when its value equals ``indicator_vals[1]``. Name the columns to convert with
``columns``, or the ones to leave alone with ``key_columns`` (not both); with neither, every body column is
converted. Values are read as numbers, so text becomes missing. Converted columns are centered.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The columns to convert. |
| `key_columns` | `Any` | The columns to leave alone (every other body column is converted). |
| `indicator_vals` | `collections.abc.Sequence[float]` | The ``(no, yes)`` values. |
| `indicator_rule` | `collections.abc.Callable[..., Any] \| None` | A function deciding when a box is filled, called with each cell's numeric value (and the column name, when it takes two arguments); ``None`` tests equality with ``indicator_vals[1]``. |
| `color_yes` | `str` | Fill of boxes meeting the rule (hex; a translucent ``#rrggbbaa`` is drawn as given, and the text color is read on what it shows over the table background). |
| `color_no` | `str` | Fill of the others (hex, as ``color_yes``). |
| `show_na_as_na` | `bool` | Print ``NA`` in a missing value's box instead of leaving it blank. |
| `show_text` | `bool` | Print the formatted value inside each box (boxes then widen to fit). |
| `show_only` | `str \| None` | Print text in only one class of box: ``"yes"``, ``"no"`` or ``"NA"``; ``None`` prints all. |
| `per_column_formats` | `dict[str, dict[str, Any]] \| None` | ``{column: {"digits": ..., "format_type": ..., "suffix": ...}}``. |
| `color_na` | `str \| None` | Fill of missing values' boxes (hex); ``None`` uses ``color_no``. |
| `border_color` | `str \| None` | A border color around each box; ``None`` for none. |
| `border_width` | `float` | The border width in pixels. |
| `box_width` | `float` | Box width in pixels when ``show_text`` is off. |
| `box_height` | `float` | Box height in pixels. |
| `text_size` | `float` | Box text size in pixels. |
| `text_weight` | `str` | Box text weight. |

### Returns

`GT` — A new table with the columns shown as boxes.

### Raises

- `TypeError`: ``gt`` is not a ``GT``.
- `ValueError`: Both ``columns`` and ``key_columns`` were given, no column is left to convert, or ``show_only`` is unknown.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_indicator_boxes

roster = pl.DataFrame({"player": ["A", "B", "C"], "starter": [True, False, True]})

gt_indicator_boxes(GT(roster), key_columns="player", show_text=True, border_color="#333333")
```

### See also

- Ported from sdvplotR ``gt_indicator_boxes()``.

## gt_legend_continuous

<div class="sdv-signature">

```python
gt_legend_continuous(
    gt: great_tables.gt.GT,
    columns: Any = None,
    *,
    palette: collections.abc.Sequence[str] | None = None,
    domain: collections.abc.Sequence[float] | None = None,
    reverse: bool | None = None,
    pal_type: str | None = None,
    type: str = 'continuous',
    n_bins: int = 5,
    labels: str | collections.abc.Sequence[str] | None = None,
    digits: int = 0,
    title: str | None = None,
    title_position: str = 'top',
    title_style: collections.abc.Mapping[str, Any] | None = None,
    labels_style: collections.abc.Mapping[str, Any] | None = None,
    labels_position: str = 'bottom',
    location: str = 'bottom',
    align: str = 'center',
    width: float = 200,
    height: float = 10,
    border_color: str | None = None,
    border_width: float = 1,
    radius: float = 2,
    gap: float = 3,
    title_gap: float = 4,
    block_gap: float = 2,
) -> great_tables.gt.GT
```

</div>

Add a color-scale legend that matches a column colored by ``gt_color_ranks``, ``gt_color_pills``,

``gt_percentile_bar`` or ``GT.data_color``.

Those three sdvplot functions record the scale they used on the table (``_sdvplot_scale``); every argument left
as ``None`` here is taken from that record, so ``gt_legend_continuous(gt)`` cannot disagree with the cells. The
bar is a row of solid segments (CSS gradients do not survive every renderer), colored by the same piecewise-linear
ramp great_tables' ``data_color`` uses. Style dicts take the keys listed in ``gt_title_header``.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The column selection the legend describes, used to derive ``domain``. Defaults to the recorded one. |
| `palette` | `collections.abc.Sequence[str] \| None` | Hex colors spread over ``domain``. Defaults to the recorded palette, else sdvplotR's five-color green-to-red ramp. |
| `domain` | `collections.abc.Sequence[float] \| None` | ``(low, high)``. Defaults to the recorded domain, else the range of ``columns``. |
| `reverse` | `bool \| None` | Reverse the palette. Defaults to the recorded value, else ``False``. |
| `pal_type` | `str \| None` | ``"discrete"`` or ``"continuous"``; kept for sdvplotR parity (it picks a paletteer registry in R). |
| `type` | `str` | ``"continuous"`` (a smooth ramp), ``"steps"`` (``n_bins`` touching steps) or ``"blocks"`` (separated). |
| `n_bins` | `int` | The number of steps or blocks. |
| `labels` | `str \| collections.abc.Sequence[str] \| None` | ``None`` labels the two ends of ``domain``; ``"edges"`` labels the ``n_bins + 1`` bin edges; a list of strings is spread evenly. |
| `digits` | `int` | Decimal places of derived labels. |
| `title` | `str \| None` | A caption for the legend. |
| `title_position` | `str` | ``"top"``, ``"bottom"``, ``"left"`` or ``"right"`` of the bar. |
| `title_style` | `collections.abc.Mapping[str, Any] \| None` | Styles the title (default 11px gray). |
| `labels_style` | `collections.abc.Mapping[str, Any] \| None` | Styles the labels (default 10px gray). |
| `labels_position` | `str` | ``"bottom"``, ``"top"`` or ``"none"``. |
| `location` | `str` | ``"bottom"`` adds the legend as a source note; ``"top"`` puts it in the header, under any title. |
| `align` | `str` | ``"center"``, ``"left"`` or ``"right"``. |
| `width` | `float` | The bar width in pixels. |
| `height` | `float` | The bar height in pixels. |
| `border_color` | `str \| None` | A border around the bar (each block, for ``"blocks"``). |
| `border_width` | `float` | The border width in pixels. |
| `radius` | `float` | The corner radius in pixels. |
| `gap` | `float` | Pixels between the bar and its labels. |
| `title_gap` | `float` | Pixels between the title and the bar. |
| `block_gap` | `float` | Pixels between blocks. |

### Returns

`GT` — A new table with the legend added.

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.
- `ValueError`: If neither a domain nor numeric ``columns`` can be found, an option is not one of its choices, ``n_bins`` is below 1, or a palette color is not hex.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_legend_continuous, gt_percentile_bar

gt = gt_percentile_bar(GT(pl.DataFrame({"pct": [94, 41, 72]})), "pct")
gt = gt_legend_continuous(gt, title="Percentile")   # palette and domain come from the bars
```

### See also

- [Ported from sdvplotR ``gt_legend_continuous()``](https://sdvplotR.sportsdataverse.org/reference/gt_legend_continuous.html)

## gt_legend_discrete

<div class="sdv-signature">

```python
gt_legend_discrete(
    gt: great_tables.gt.GT,
    key_info: Any = None,
    *,
    heading: str | None = None,
    subtitle: str | None = None,
    label_placement: str = 'outside',
    location: str = 'top',
    shape: str = 'square',
    swatch_size: float = 14,
    border: bool = True,
    border_color: str | None = None,
    border_width: float = 1,
    gap: float = 14,
    direction: str = 'horizontal',
    align: str = 'center',
    heading_style: collections.abc.Mapping[str, Any] | None = None,
    subtitle_style: collections.abc.Mapping[str, Any] | None = None,
    label_style: collections.abc.Mapping[str, Any] | None = None,
) -> great_tables.gt.GT
```

</div>

Add a key of labeled color swatches (home/away, tiers, conferences).

Text colors are read off the table background, so the key stays legible on a dark theme. Style dicts take the
keys listed in ``gt_title_header``.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `key_info` | `Any` | ``{label: hex color}``, or a pandas/polars frame with ``color`` and ``label`` columns (or color then label as its first two columns). Defaults to the key ``gt_tiers`` recorded on the table. |
| `heading` | `str \| None` | A heading above the key. |
| `subtitle` | `str \| None` | A subtitle under the heading. |
| `label_placement` | `str` | ``"outside"`` (label beside its swatch) or ``"inside"`` (label printed on the swatch). |
| `location` | `str` | ``"top"`` (the header) or ``"bottom"`` (a source note). |
| `shape` | `str` | ``"square"``, ``"rounded"`` or ``"circle"``. |
| `swatch_size` | `float` | The swatch size in pixels. |
| `border` | `bool` | Draw a hairline around each swatch. |
| `border_color` | `str \| None` | The hairline color; defaults to a darker shade of each swatch. |
| `border_width` | `float` | The hairline width in pixels. |
| `gap` | `float` | Pixels between keys. |
| `direction` | `str` | ``"horizontal"`` (a row) or ``"vertical"`` (a column). |
| `align` | `str` | ``"center"``, ``"left"`` or ``"right"``. |
| `heading_style` | `collections.abc.Mapping[str, Any] \| None` | Styles the heading (16px, weight 600, ink on the table background). |
| `subtitle_style` | `collections.abc.Mapping[str, Any] \| None` | Styles the subtitle (13px, a muted ink). |
| `label_style` | `collections.abc.Mapping[str, Any] \| None` | Styles the labels (12px). |

### Returns

`GT` — A new table with the key added. With ``location="top"`` and a heading or subtitle, the key replaces the header; a bare key goes under any existing title and subtitle.

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT`` or ``key_info`` is neither a mapping nor a data frame.
- `ValueError`: If there is no key, a color is not hex, or an option is not one of its choices.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_legend_discrete

gt = gt_legend_discrete(GT(pl.DataFrame({"game": ["@ KC"]})), {"Home": "#cce7f5", "Away": "#eeeeee"})
```

### See also

- [Ported from sdvplotR ``gt_legend_discrete()``](https://sdvplotR.sportsdataverse.org/reference/gt_legend_discrete.html)

## gt_marginalia

<div class="sdv-signature">

```python
gt_marginalia(
    gt: great_tables.gt.GT,
    columns: Any,
    *,
    width: float | str | None = 220,
    label: str | None = '',
    italic: bool = True,
    color: str | None = None,
    size: str = '0.92em',
    rule: bool = True,
    rule_color: str | None = None,
    align: str = 'left',
) -> great_tables.gt.GT
```

</div>

Turn columns into margin notes: muted italic prose in a fixed-width column behind a hairline rule.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The note columns (any great_tables selection). |
| `width` | `float \| str \| None` | The column width (a number is pixels); the fixed width is what makes the prose wrap. ``None`` leaves it alone. |
| `label` | `str \| None` | The column label (empty by default); ``None`` keeps the existing label. |
| `italic` | `bool` | Italicize the notes. |
| `color` | `str \| None` | The text color; defaults to a muted ink that clears 4.5:1 on the table background (dark themes too). |
| `size` | `str` | The CSS font size. |
| `rule` | `bool` | Draw a hairline on the left edge. |
| `rule_color` | `str \| None` | The hairline color; defaults to a faint tint of the ink. |
| `align` | `str` | The text alignment. |

### Returns

`GT` — A new table with the note columns styled.

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.
- `ValueError`: If ``columns`` selects nothing.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_marginalia

df = pl.DataFrame({"team": ["LV"], "note": ["Lost the starting QB in week 3."]})
gt = gt_marginalia(GT(df), "note")
```

### See also

- [Ported from sdvplotR ``gt_marginalia()``](https://sdvplotR.sportsdataverse.org/reference/gt_marginalia.html)

## gt_merge_stack_team_color

<div class="sdv-signature">

```python
gt_merge_stack_team_color(
    gt: great_tables.gt.GT,
    col1: str,
    col2: str,
    team_col: str,
    *,
    league: str,
    font_size_top: float = 14,
    font_size_bottom: float = 12,
    color: str = 'black',
    background: str | None = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
) -> great_tables.gt.GT
```

</div>

Stack ``col1`` over ``col2`` in one cell: the top in bold small caps, the bottom in the team's color.

The bottom line takes the team's primary color when it clears 4.5:1 contrast (WCAG AA) against the cell
background, else the secondary color, else the primary darkened (or lightened, on a dark table) until it does, so
a light primary such as Missouri's gold stays readable on a white table and keeps its gold on a dark one.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | A great_tables ``GT``. |
| `col1` | `str` | The column shown on top (bold small caps, in ``color``); it holds the merged cell. |
| `col2` | `str` | The column shown below, smaller and in the row's team color; it is hidden. |
| `team_col` | `str` | The column of teams whose primary colors color the bottom line. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `font_size_top` | `float` | The top line's font size in pixels. |
| `font_size_bottom` | `float` | The bottom line's font size in pixels. |
| `color` | `str` | The top line's CSS color. |
| `background` | `str \| None` | The cell background the bottom line is checked against, a hex color. ``None`` (the default) reads the table's background, so a theme such as ``gt_theme_midnight`` applied **before** this function is taken into account; a theme applied afterwards is not seen, so set ``background`` then. A table with no background set counts as white. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team_col``, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a team does not resolve. |

### Returns

`GT` — A new table. A team that does not resolve, or has no color, gets grey (sdvplotR's ``#bebebe``, made readable the same way), with one SdvplotWarning.

### Raises

- `TypeError`: If ``gt`` is not a great_tables GT.
- `InputError`: (a ValueError) If ``league`` or ``id_system`` is unknown.
- `ValueError`: If ``col1``, ``col2`` or ``team_col`` is not a column of the table's data, or ``background`` is not a hex color.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a team does not resolve.

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_merge_stack_team_color
import polars as pl

df = pl.DataFrame({"team": ["KC", "BUF"], "mascot": ["Chiefs", "Bills"]})

gt_merge_stack_team_color(GT(df), "team", "mascot", "team", league="nfl")
```

### See also

- [Ported from sdvplotR ``gt_merge_stack_team_color()``](https://sdvplotR.sportsdataverse.org/reference/gt_merge_stack_team_color.html)

## gt_outliers

<div class="sdv-signature">

```python
gt_outliers(
    gt: great_tables.gt.GT,
    columns: Any,
    *,
    method: str = 'iqr',
    threshold: float | None = None,
    bounds: collections.abc.Sequence[float | None] | None = None,
    side: str = 'both',
    fill: str | None = None,
    color: str | None = None,
    bold: bool = True,
    symbol: str | None = None,
    note: bool | str | None = None,
) -> great_tables.gt.GT
```

</div>

Flag outlying values in numeric columns: colored (and bold) text, an optional fill, symbol and source note.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The columns to test (any great_tables selection); non-numeric columns are skipped. |
| `method` | `str` | ``"iqr"`` (beyond ``threshold`` x IQR of the quartiles, R's type-7 quantiles), ``"sd"`` (more than ``threshold`` sample standard deviations from the mean) or ``"bounds"`` (outside ``bounds``). |
| `threshold` | `float \| None` | The cutoff for ``"iqr"`` (default 1.5) and ``"sd"`` (default 3). |
| `bounds` | `collections.abc.Sequence[float \| None] \| None` | ``(lower, upper)`` for ``"bounds"``; ``None`` on either side leaves it open. |
| `side` | `str` | ``"both"``, ``"high"`` or ``"low"``. |
| `fill` | `str \| None` | A hex fill behind flagged values (a translucent ``#rrggbbaa`` is drawn as given; the default text color is read on what it shows over the table background). |
| `color` | `str \| None` | The flagged text color; defaults to a warning red, or the readable ink when the red fails 4.5:1 on ``fill``. |
| `bold` | `bool` | Bold flagged values. |
| `symbol` | `str \| None` | A marker appended to flagged values, such as ``"†"``. |
| `note` | `bool \| str \| None` | ``True`` adds a source note describing the rule; a string adds that note; ``None``/``False`` none. |

### Returns

`GT` — A new table (unchanged, with an SdvplotWarning, when no selected column is numeric).

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.
- `ValueError`: If ``columns`` selects nothing, ``bounds`` is missing for ``"bounds"``, or an option is invalid.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_outliers

df = pl.DataFrame({"team": list("ABCDEFG"), "pts": [21, 24, 20, 23, 22, 25, 61]})
gt = gt_outliers(GT(df), "pts", symbol="†", note=True)
```

### See also

- [Ported from sdvplotR ``gt_outliers()``](https://sdvplotR.sportsdataverse.org/reference/gt_outliers.html)

## gt_percentile_bar

<div class="sdv-signature">

```python
gt_percentile_bar(
    gt: great_tables.gt.GT,
    columns: Any,
    *,
    rows: Any = None,
    domain: collections.abc.Sequence[float] = (0, 100),
    scale: str | float = 'auto',
    palette: collections.abc.Sequence[str] = ('#3661AD', '#C9C9C9', '#D22D49'),
    reverse: bool = False,
    pal_type: str = 'discrete',
    track_color: str = '#E9E9E9',
    track_height: float = 6,
    marker_size: float = 22,
    text_color: str = '#FFFFFF',
    font_size: float | None = None,
    ring_color: str | None = None,
    ring_width: float = 2,
    full_track: bool = True,
    na_label: str | None = '—',
    na_track_color: str | None = None,
    na_text_color: str = '#9A9A9A',
    decimals: int = 0,
    width: float | None = 220,
) -> great_tables.gt.GT
```

</div>

Draw each percentile as a filled track with a round marker at its tip, the value printed in the marker.

All CSS, so it stays sharp at any export scale. The fill and marker take the palette color mapped from the value.
The scale is recorded on the table (``_sdvplot_scale``), so ``gt_legend_continuous(gt)`` matches it.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The columns holding percentiles (any great_tables column selection). |
| `rows` | `Any` | The rows to draw bars in (any great_tables row selection: 0-based positions, a polars expression, or a function of the pandas frame); other rows keep their value. Defaults to every row. |
| `domain` | `collections.abc.Sequence[float]` | ``(low, high)`` of the percentile scale. |
| `scale` | `str \| float` | ``"auto"`` treats a column whose values all lie in [0, 1] as proportions of ``domain`` (0.72 is drawn and printed as 72); ``"none"`` leaves values alone; a number multiplies every value. |
| `palette` | `collections.abc.Sequence[str]` | Hex colors mapped across ``domain`` (blue, gray, red). |
| `reverse` | `bool` | Reverse the palette. |
| `pal_type` | `str` | ``"discrete"`` or ``"continuous"``; kept for sdvplotR parity and recorded with the scale. |
| `track_color` | `str` | The unfilled track color. |
| `track_height` | `float` | The track thickness in pixels. |
| `marker_size` | `float` | The marker diameter in pixels. |
| `text_color` | `str` | The number's color. |
| `font_size` | `float \| None` | The number's size in pixels; defaults to half of ``marker_size``. |
| `ring_color` | `str \| None` | A ring around the marker; ``None`` for none. |
| `ring_width` | `float` | The ring thickness in pixels. |
| `full_track` | `bool` | Run the track the full width (else it stops at the marker). |
| `na_label` | `str \| None` | What a missing percentile shows, centered in a broken track; ``None`` draws an unbroken empty track. |
| `na_track_color` | `str \| None` | The track color of missing rows; defaults to ``track_color``. |
| `na_text_color` | `str` | The color of ``na_label``. |
| `decimals` | `int` | Decimal places of the number. |
| `width` | `float \| None` | The column width in pixels; ``None`` leaves it alone. |

### Returns

`GT` — A new table with the bars (unchanged, with an SdvplotWarning, when ``rows`` selects no rows).

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.
- `ValueError`: If ``scale``, ``pal_type`` or ``domain`` is invalid, or a palette color is not hex.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_percentile_bar

df = pl.DataFrame({"metric": ["Barrel %", "Chase rate"], "pct": [94, None]})
gt = gt_percentile_bar(GT(df), "pct", na_label="Not qualified")
```

### See also

- [Ported from sdvplotR ``gt_percentile_bar()``](https://sdvplotR.sportsdataverse.org/reference/gt_percentile_bar.html)

## gt_row_accent

<div class="sdv-signature">

```python
gt_row_accent(
    gt: great_tables.gt.GT,
    column: Any,
    *,
    palette: collections.abc.Mapping[str, str] | collections.abc.Sequence[str] | None = None,
    rows: Any = None,
    width: float = 4,
    side: str = 'left',
    hide: bool = True,
    na_color: str = 'transparent',
) -> great_tables.gt.GT
```

</div>

Draw a colored bar on the edge of each row, keyed to a column (a team color, a conference).

The bar is a border on the stub, or on the leftmost rendered column when the table has no stub, so it lines up
with the row.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `column` | `Any` | The one column the color is keyed to: a column of colors, or values mapped through ``palette``. |
| `palette` | `collections.abc.Mapping[str, str] \| collections.abc.Sequence[str] \| None` | ``{value: color}``; or a list of colors assigned to the sorted distinct values and recycled. Defaults to reading ``column`` as colors. |
| `rows` | `Any` | The rows to accent (any great_tables row selection). Defaults to every row. |
| `width` | `float` | The bar width in pixels. |
| `side` | `str` | ``"left"`` or ``"right"``. |
| `hide` | `bool` | Hide ``column`` once the bars are drawn (what you want when it holds hex codes). |
| `na_color` | `str` | The color for a missing or unmapped key; ``"transparent"`` draws no bar. |

### Returns

`GT` — A new table with the bars (unchanged, with an SdvplotWarning, when ``rows`` selects no rows).

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.
- `ValueError`: If ``column`` does not select exactly one column, or ``side`` is not ``"left"``/``"right"``.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_row_accent

df = pl.DataFrame({"team": ["Clemson", "Georgia"], "conf": ["ACC", "SEC"], "wins": [10, 12]})
gt = gt_row_accent(GT(df), "conf", palette={"ACC": "#003366", "SEC": "#B8232F"})
```

### See also

- [Ported from sdvplotR ``gt_row_accent()``](https://sdvplotR.sportsdataverse.org/reference/gt_row_accent.html)

## gt_save_batch

<div class="sdv-signature">

```python
gt_save_batch(
    data: Any,
    group: str,
    fn: collections.abc.Callable[[Any, Any], great_tables.gt.GT],
    file: str,
    *,
    dir: str | os.PathLike[str],
    match_width: bool = True,
    bg: str = 'white',
    whitespace: int = 50,
    zoom: float = 2,
    quiet: bool = False,
) -> list[str]
```

</div>

Save a matched set of table images, one per group.

Splits ``data`` by a column, builds a table per group with ``fn`` and writes one image per group, padded to a
common width so a posted series is not ragged. A group whose table fails to build or render is skipped and named
in one warning at the end; the rest are still written.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | A pandas or polars DataFrame (any narwhals-supported eager frame). |
| `group` | `str` | The column to split on. Its missing values are skipped. |
| `fn` | `collections.abc.Callable[[Any, Any], great_tables.gt.GT]` | Builds one table, called as ``fn(df, value)`` with the group's rows (the same frame type as ``data``) and its value; it must return a ``GT``. |
| `file` | `str` | A file name containing ``{group}``, replaced by the group value with anything awkward turned into a dash and lower-cased, so ``"North / East"`` writes ``"net-north-east.png"`` for ``"net-{group}.png"``. |
| `dir` | `str \| os.PathLike[str]` | The directory to write into, created when missing. It has no default, so a batch never lands in the working directory unasked; pass ``"."`` for that. |
| `match_width` | `bool` | Pad every image to the widest one's width. |
| `bg` | `str` | The padding color. |
| `whitespace` | `int` | The border, in pixels, around each table. |
| `zoom` | `float` | The rendering zoom. |
| `quiet` | `bool` | Do not print the per-group progress lines (to stderr). |

### Returns

`list[str]` — The files written, in group order.

### Raises

- `TypeError`: If ``data`` is not a data frame or ``fn`` is not callable.
- `ValueError`: If ``group`` is not a column, has no non-missing values, two values would write the same file, ``file`` lacks ``{group}`` or an image extension, or ``bg``, ``whitespace`` or ``zoom`` is invalid (all before rendering).
- `RuntimeError`: If no group built.
- `nokap.ChromeNotFoundError`: If no browser can start (raised at the first group, not collected per group).

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_save_batch
import polars as pl

cars = pl.DataFrame({"cyl": [4, 4, 6], "mpg": [22.8, 24.4, 21.0]})

def build(df, value):
    return GT(df).tab_header(title=f"{value} cylinders")

gt_save_batch(cars, "cyl", build, "cars-{group}.png", dir="out")
```

### See also

- [gt_grid: the same split composed into one image. Ported from sdvplotR ``gt_save_batch()``](https://sdvplotR.sportsdataverse.org/reference/gt_save_batch.html)

## gt_save_crop

<div class="sdv-signature">

```python
gt_save_crop(
    data: great_tables.gt.GT,
    file: str | os.PathLike[str] | None = None,
    *,
    bg: str = 'white',
    whitespace: int = 50,
    zoom: float = 2,
    expand: int = 5,
    width: int | None = None,
) -> Any
```

</div>

Save a table to an image, trimmed to its content with an even border.

Renders the table in headless Chrome (great_tables' ``GT.gtsave``), trims the page around it and pads a
``whitespace`` border of ``bg`` back on.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `great_tables.gt.GT` | The great_tables ``GT`` to save. |
| `file` | `str \| os.PathLike[str] \| None` | A path ending in an image extension Pillow writes (``.png``, ``.jpg``, ``.jpeg``, ...). ``None`` returns the image instead of writing it. |
| `bg` | `str` | The border color: a CSS color name or hex code. |
| `whitespace` | `int` | The border, in pixels, left around the trimmed table. |
| `zoom` | `float` | The rendering zoom, a positive number; 2 gives a sharp (retina) image. |
| `expand` | `int` | Pixels of page captured around the table before trimming. |
| `width` | `int \| None` | A final width in pixels, the height following, so a series of tables shares one width. ``None`` keeps the rendered width. |

### Returns

str | os.PathLike | PIL.Image.Image: ``file`` after writing it, or the image when ``file`` is ``None``.

### Raises

- `TypeError`: If ``data`` is not a ``GT``.
- `ValueError`: If ``bg``, ``whitespace``, ``width``, ``zoom`` or the extension of ``file`` is invalid (checked before rendering).
- `nokap.ChromeNotFoundError`: If no Chrome or Chromium is installed (set ``CHROME_PATH`` to point at one).

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_save_crop
import polars as pl

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_save_crop(GT(df), "table.png", bg="#FBFAF7", width=900)
```

### See also

- [gt_social_crop: the same, padded onto a fixed-ratio canvas. Ported from sdvplotR ``gt_save_crop()``](https://sdvplotR.sportsdataverse.org/reference/gt_save_crop.html)

## gt_scale_note

<div class="sdv-signature">

```python
gt_scale_note(
    gt: great_tables.gt.GT,
    columns: Any,
    *,
    divisor: float = 1000,
    note: str | None = None,
    where: str = 'source_note',
    label_suffix: str | None = None,
    decimals: int = 0,
    **kwargs: Any,
) -> great_tables.gt.GT
```

</div>

Divide columns by a round number and say so: "Figures in thousands." or a "(000s)" label suffix.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The columns to scale (any great_tables selection). |
| `divisor` | `float` | The amount to divide by. |
| `note` | `str \| None` | The disclosure; defaults to "Figures in thousands." (millions, billions, trillions) or "Figures divided by 2,500." for other divisors. |
| `where` | `str` | ``"source_note"``, ``"label"`` (append ``label_suffix`` to the column labels) or ``"both"``. |
| `label_suffix` | `str \| None` | The label suffix; defaults to "(000s)", "(millions)", ... or "(÷2,500)". |
| `decimals` | `int` | Decimal places of the scaled values. |
| `**kwargs` | `Any` | Passed to great_tables ``fmt_number`` (``use_seps``, ``pattern``, ...). |

### Returns

`GT` — A new table with the columns formatted and the disclosure added.

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.
- `ValueError`: If ``divisor`` is not a non-zero number, ``columns`` selects nothing, or ``where`` is invalid.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_scale_note

df = pl.DataFrame({"team": ["LV", "KC"], "payroll": [254_000_000, 268_500_000]})
gt = gt_scale_note(GT(df), "payroll", divisor=1e6, decimals=1, where="both")
```

### See also

- [Ported from sdvplotR ``gt_scale_note()``](https://sdvplotR.sportsdataverse.org/reference/gt_scale_note.html)

## gt_sdv_cols_label

<div class="sdv-signature">

```python
gt_sdv_cols_label(
    gt: great_tables.gt.GT,
    columns: Any = None,
    *,
    league: str,
    height: Any = 30,
    season: Any = None,
    mark_type: str = 'logo',
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] | Literal['espn', 'gsis'] | NoneType = None,
    strict: bool = False,
) -> great_tables.gt.GT
```

</div>

Replace the labels of team-named columns (a ``KC`` column, a ``BUF`` column, ...) with their marks.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | A great_tables ``GT``. |
| `columns` | `Any` | The columns whose labels to replace: a name, a list, a polars selector, or None for every column. The column *names* are resolved (not labels set earlier with ``cols_label``). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `Any` | The image height in pixels. |
| `season` | `Any` | One season whose marks to show; None for today's. |
| `mark_type` | `str` | "logo", "wordmark", or "headshot" (the column names are player ids). |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] \| Literal['espn', 'gsis'] \| NoneType` | The id system of the column names: for logos and wordmarks one of ``resolve``'s (None means "auto"; NHL stats ids need "nhl_id"), for headshots "espn" or "gsis" as in ``headshot_url`` (None means "espn"). |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a column name does not resolve to a team. |

### Returns

`GT` — A new table; columns whose names do not resolve keep their labels, with one SdvplotWarning now.

### Raises

- `TypeError`: If ``gt`` is not a great_tables GT.
- `InputError`: (a ValueError) If ``mark_type`` is not "logo", "wordmark" or "headshot", ``height`` is not a number of pixels of at least 1, ``league`` or ``id_system`` is unknown (for headshots: ``league`` has no ESPN headshots, or ``id_system`` is not valid for it), or ``season`` is not one year or is outside the seasons sdvplot knows for the league.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a column name does not resolve.
- `OfflineError`: If the logo manifest (logos and wordmarks), or for "gsis" headshots the nflverse player table, cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, for an HTTP error status).
- `UnsafeDownloadError`: (an OSError) If that download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_sdv_cols_label
import polars as pl

df = pl.DataFrame({"KC": [12], "BUF": [10], "SF": [9]})

gt_sdv_cols_label(GT(df), ["KC", "BUF", "SF"], league="nfl")
```

### See also

- [Ported from sdvplotR ``gt_sdv_cols_label()``](https://sdvplotR.sportsdataverse.org/reference/gt_sdv_cols_label.html)

## gt_sdv_headshots

<div class="sdv-signature">

```python
gt_sdv_headshots(
    gt: great_tables.gt.GT,
    columns: Any,
    *,
    league: str,
    height: Any = 30,
    locations: Any = None,
    id_system: str = 'espn',
) -> great_tables.gt.GT
```

</div>

Show each cell's player id as the player's headshot in a great_tables table.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | A great_tables ``GT``. |
| `columns` | `Any` | The columns of player ids. Ignored when ``locations`` is given (pass None). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `Any` | The image height in pixels. |
| `locations` | `Any` | Instead of the body of ``columns``: ``loc.body()``, ``loc.stub()`` or ``loc.row_groups()``, or a list of them (the locations great_tables' ``text_transform`` reaches). For marks in the column labels, use ``gt_sdv_cols_label``. |
| `id_system` | `str` | "espn" (ESPN athlete ids, any ESPN league) or "gsis" (NFL), as in ``headshot_url``. |

### Returns

`GT` — A new table; ids without a headshot keep their text, with one SdvplotWarning now.

### Raises

- `TypeError`: If ``gt`` is not a great_tables GT.
- `InputError`: (a ValueError) If ``height`` is not a number of pixels of at least 1, ``league`` has no ESPN headshots, or ``id_system`` is not valid for ``league``.
- `ValueError`: If ``columns`` names a column the table lacks, or ``locations`` holds another location.
- `OfflineError`: If ``id_system`` is "gsis" and the nflverse player table cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, when GitHub answers with an error status).
- `UnsafeDownloadError`: (an OSError) If ``id_system`` is "gsis" and the player table download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_sdv_headshots
import polars as pl

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_sdv_headshots(GT(df), "espn_id", league="nfl", height=40)
```

### See also

- [Ported from sdvplotR ``gt_sdv_headshots()``](https://sdvplotR.sportsdataverse.org/reference/gt_sdv_headshots.html)

## gt_sdv_logos

<div class="sdv-signature">

```python
gt_sdv_logos(
    gt: great_tables.gt.GT,
    columns: Any,
    *,
    league: str,
    height: Any = 30,
    locations: Any = None,
    include_name: bool = False,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
) -> great_tables.gt.GT
```

</div>

Show each cell's team as its logo in a great_tables table.

Values are resolved when you call this (team abbreviations, names and provider ids, as in ``resolve()``), so
unknown values warn once, now. They keep their text. The cell text is read as it renders now, so apply any
``fmt_*`` to the same column before this.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | A great_tables ``GT``. |
| `columns` | `Any` | The columns whose body cells become logos: a name, a list of names, or a polars selector. Ignored when ``locations`` is given (pass None). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `Any` | The image height in pixels. |
| `locations` | `Any` | Instead of the body of ``columns``: ``loc.body()``, ``loc.stub()`` or ``loc.row_groups()``, or a list of them (the locations great_tables' ``text_transform`` reaches). For marks in the column labels, use ``gt_sdv_cols_label``. |
| `include_name` | `bool` | Keep the cell's text after the logo. |
| `season` | `Any` | One season whose marks every cell shows (the ending year for the NHL, NBA, MBB and WBB); None for today's. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of the cell values, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a value does not resolve. |

### Returns

`GT` — A new table; ``gt`` is unchanged.

### Raises

- `TypeError`: If ``gt`` is not a great_tables GT.
- `InputError`: (a ValueError) If ``height`` is not a number of pixels of at least 1, ``league`` or ``id_system`` is unknown, or ``season`` is not one year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If ``columns`` names a column the table lacks, or ``locations`` holds another location.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a value does not resolve.
- `OfflineError`: If the logo manifest cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, when the CDN answers with an error status).
- `UnsafeDownloadError`: (an OSError) If the manifest download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_sdv_logos
import polars as pl

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_sdv_logos(GT(df), "team", league="nfl", height=24)
```

### See also

- [Ported from sdvplotR ``gt_sdv_logos()``](https://sdvplotR.sportsdataverse.org/reference/gt_sdv_logos.html)
- [great_tables](https://posit-dev.github.io/great-tables/)

## gt_sdv_wordmarks

<div class="sdv-signature">

```python
gt_sdv_wordmarks(
    gt: great_tables.gt.GT,
    columns: Any,
    *,
    league: str,
    height: Any = 30,
    locations: Any = None,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
) -> great_tables.gt.GT
```

</div>

Show each cell's team as its wordmark in a great_tables table.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | A great_tables ``GT``. |
| `columns` | `Any` | The columns whose body cells become wordmarks. Ignored when ``locations`` is given (pass None). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `height` | `Any` | The image height in pixels. |
| `locations` | `Any` | Instead of the body of ``columns``: ``loc.body()``, ``loc.stub()`` or ``loc.row_groups()``, or a list of them (the locations great_tables' ``text_transform`` reaches). For marks in the column labels, use ``gt_sdv_cols_label``. |
| `season` | `Any` | One season whose marks every cell shows; None for today's. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of the cell values, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when a value does not resolve. |

### Returns

`GT` — A new table; unknown values keep their text, with one SdvplotWarning now.

### Raises

- `TypeError`: If ``gt`` is not a great_tables GT.
- `InputError`: (a ValueError) If ``height`` is not a number of pixels of at least 1, ``league`` or ``id_system`` is unknown, or ``season`` is not one year or is outside the seasons sdvplot knows for the league.
- `ValueError`: If ``columns`` names a column the table lacks, or ``locations`` holds another location.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and a value does not resolve.
- `OfflineError`: If the logo manifest cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, when the CDN answers with an error status).
- `UnsafeDownloadError`: (an OSError) If the manifest download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_sdv_wordmarks
import polars as pl

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_sdv_wordmarks(GT(df), "team", league="nfl")
```

### See also

- [Ported from sdvplotR ``gt_sdv_wordmarks()``](https://sdvplotR.sportsdataverse.org/reference/gt_sdv_wordmarks.html)

## gt_set_font

<div class="sdv-signature">

```python
gt_set_font(
    gt: great_tables.gt.GT,
    font_family: str,
    *,
    from_google_font: bool = True,
    weight: str | int | None = None,
    style: str | None = None,
) -> great_tables.gt.GT
```

</div>

Set one font family (and optionally a weight and style) on every part of the table.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `font_family` | `str` | The font family. |
| `from_google_font` | `bool` | Load ``font_family`` from Google Fonts; ``False`` uses a font the viewer has installed. |
| `weight` | `str \| int \| None` | A font weight for every part (``"bold"`` or a number such as 600); ``None`` leaves it alone. |
| `style` | `str \| None` | ``"normal"``, ``"italic"`` or ``"oblique"``; ``None`` leaves it alone. |

### Returns

`GT` — A new table with the font set on the title, stubhead, spanners, column labels, row groups, stub, body, footnotes and source notes (summary rows are left alone, as in sdvplotR).

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_set_font

gt = gt_set_font(GT(pl.DataFrame({"team": ["LV"]})), "Roboto Condensed", weight=600)
```

### See also

- [Ported from sdvplotR ``gt_set_font()``](https://sdvplotR.sportsdataverse.org/reference/gt_set_font.html)

## gt_significance

<div class="sdv-signature">

```python
gt_significance(
    gt: great_tables.gt.GT,
    columns: Any,
    p_columns: Any,
    *,
    levels: collections.abc.Sequence[float] = (0.01, 0.05, 0.1),
    symbols: collections.abc.Sequence[str] = ('***', '**', '*'),
    superscript: bool = True,
    size: str = '0.7em',
    legend: bool = True,
    legend_text: str | None = None,
    hide_p: bool = True,
) -> great_tables.gt.GT
```

</div>

Append significance stars to estimates from paired p-value columns.

Each value takes the symbol of the strictest level its p-value is below (0.004 gets ``***``, not ``*``); values
that meet no level, and missing p-values, are left alone. Stars follow the formatted text, so format first.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The estimate columns (any great_tables selection). |
| `p_columns` | `Any` | The p-value columns, paired with ``columns`` by position. |
| `levels` | `collections.abc.Sequence[float]` | Significance thresholds, ascending (strictest first). |
| `symbols` | `collections.abc.Sequence[str]` | The notation for each level. |
| `superscript` | `bool` | Render the stars as superscript. |
| `size` | `str` | The stars' CSS font size. |
| `legend` | `bool` | Add a legend as a source note. |
| `legend_text` | `str \| None` | A custom legend; defaults to ``"*** p < 0.01, ** p < 0.05, * p < 0.1"`` from the levels. |
| `hide_p` | `bool` | Hide the p-value columns. |

### Returns

`GT` — A new table with the stars.

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.
- `ValueError`: If ``levels`` and ``symbols`` differ in length, ``levels`` is not ascending, ``columns`` selects nothing, or the two selections do not pair up.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_significance

df = pl.DataFrame({"term": ["epa", "wpa"], "est": [0.42, 0.08], "p": [0.004, 0.2]})
gt = gt_significance(GT(df).fmt_number("est"), "est", "p")
```

### See also

- [Ported from sdvplotR ``gt_significance()``](https://sdvplotR.sportsdataverse.org/reference/gt_significance.html)

## gt_snake

<div class="sdv-signature">

```python
gt_snake(
    gt: great_tables.gt.GT,
    *,
    n_cols: int = 2,
    rows_per_col: int | None = None,
    gap: float = 20,
    fill: str | None = '',
    clean_gaps: bool = True,
) -> great_tables.gt.GT
```

</div>

Wrap a long table into side-by-side blocks (a top-50 list as two columns of 25).

The table is rebuilt from its data: each visible column appears once per block, suffixed ``_1``, ``_2``, ...
(``gt_snake_align`` reshapes helper data the same way). Labels, the header, source notes and body-cell styles
(``tab_style`` on ``loc.body``, moved to their block's column and row) carry over; formats, text transforms,
options and themes do not, so apply those after snaking. The recorded legend scale is dropped too.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table, from pandas or polars data. |
| `n_cols` | `int` | The number of blocks. |
| `rows_per_col` | `int \| None` | Rows per block; given this, the number of blocks follows from the data. |
| `gap` | `float` | Pixels of empty spacer column between blocks; 0 for none. |
| `fill` | `str \| None` | What the padding cells of the last block show; ``None`` leaves them missing. |
| `clean_gaps` | `bool` | Scrub borders, fills and rules off the spacer columns so the gap stays clean under any theme (set ``False`` when you style the gap yourself). |

### Returns

`GT` — A new, snaked table (``gt`` unchanged when there are fewer than two blocks or no rows).

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.
- `ValueError`: If ``n_cols`` or ``rows_per_col`` is below 1.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_snake

df = pl.DataFrame({"rank": range(1, 51), "team": [f"T{i}" for i in range(1, 51)]})
gt = gt_snake(GT(df), n_cols=2).fmt_integer(["rank_1", "rank_2"])
```

### See also

- [Ported from sdvplotR ``gt_snake()``](https://sdvplotR.sportsdataverse.org/reference/gt_snake.html)

## gt_snake_align

<div class="sdv-signature">

```python
gt_snake_align(
    x: Any,
    n_cols: int = 2,
    rows_per_col: int | None = None,
    fill: Any = None,
) -> Any
```

</div>

Reshape a frame the way ``gt_snake`` reshapes a table, so helper data (highlight masks, colors) lines up.

### Arguments

| Name | Type | Description |
|---|---|---|
| `x` | `Any` | A pandas or polars frame with one row per row of the un-snaked table. |
| `n_cols` | `int` | The number of blocks, as passed to ``gt_snake``. |
| `rows_per_col` | `int \| None` | Rows per block, as passed to ``gt_snake`` (then ``n_cols`` follows from the data). |
| `fill` | `Any` | The value of the trailing cells when the rows do not divide evenly (missing by default). |

### Returns

The same kind of frame, with each column once per block, suffixed ``_1``, ``_2``, ... (``x`` unchanged when there are fewer than two blocks or no rows).

### Raises

- `TypeError`: If ``x`` is not a pandas or polars frame.
- `ValueError`: If ``n_cols`` or ``rows_per_col`` is below 1.

### Example

```python
import polars as pl
from sdvplot.great_tables import gt_snake_align

wide = gt_snake_align(pl.DataFrame({"hot": [True, False, True]}), n_cols=2)   # hot_1, hot_2
```

### See also

- [Ported from sdvplotR ``gt_snake_align()``](https://sdvplotR.sportsdataverse.org/reference/gt_snake_align.html)

## gt_social_crop

<div class="sdv-signature">

```python
gt_social_crop(
    data: great_tables.gt.GT,
    file: str | os.PathLike[str] | None = None,
    *,
    aspect_ratio: str | float = '1:1',
    bg: str = 'white',
    whitespace: int = 60,
    gravity: str = 'center',
    zoom: float = 2,
    expand: int = 5,
    width: int | None = None,
) -> Any
```

</div>

Save a table centered on a canvas of a fixed aspect ratio, for social posts.

The trimmed table is never cropped: the canvas' short side grows until the ratio is met.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `great_tables.gt.GT` | The great_tables ``GT`` to save. |
| `file` | `str \| os.PathLike[str] \| None` | A path ending in an image extension (``.png``, ``.jpg``, ...). ``None`` returns the image. |
| `aspect_ratio` | `str \| float` | The canvas ratio, width to height: ``"1:1"``, ``"16:9"``, ``"4x5"`` or a number such as 1.91. |
| `bg` | `str` | The canvas color. |
| `whitespace` | `int` | Pixels left around the table before the canvas grows to the ratio. |
| `gravity` | `str` | Where the table sits on the canvas, as in magick: ``"center"``, ``"north"``, ``"south"``, ``"east"``, ``"west"``, ``"northwest"``, ``"northeast"``, ``"southwest"`` or ``"southeast"``. |
| `zoom` | `float` | The rendering zoom. |
| `expand` | `int` | Pixels of page captured around the table before trimming. |
| `width` | `int \| None` | A final width in pixels for the finished canvas, the ratio held. |

### Returns

str | os.PathLike | PIL.Image.Image: ``file`` after writing it, or the image when ``file`` is ``None``.

### Raises

- `TypeError`: If ``data`` is not a ``GT``.
- `ValueError`: If ``aspect_ratio`` is not a positive ratio, ``gravity`` is unknown, or ``bg``, ``whitespace``, ``width``, ``zoom`` or the extension of ``file`` is invalid (all checked before rendering).
- `nokap.ChromeNotFoundError`: If no Chrome or Chromium is installed.

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_social_crop
import polars as pl

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_social_crop(GT(df), "post.png", aspect_ratio="4:5", bg="#0C0D10")
```

### See also

- [gt_save_crop: a plain trimmed save. Ported from sdvplotR ``gt_social_crop()``](https://sdvplotR.sportsdataverse.org/reference/gt_social_crop.html)

## gt_social_tag

<div class="sdv-signature">

```python
gt_social_tag(
    gt: great_tables.gt.GT,
    accounts: collections.abc.Mapping[str, str],
    *,
    caption: str | None = None,
    stack: bool = False,
    separator: str = ' | ',
    align: str = 'right',
    icon_color: str | None = None,
    icon_height: str = '0.9em',
    text_size: str | None = None,
    text_weight: str | int | None = None,
    **kwargs: Any,
) -> great_tables.gt.GT
```

</div>

Sign a table with social handles, each behind its platform's icon, under an optional caption.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `accounts` | `collections.abc.Mapping[str, str]` | ``{platform: handle}``. Platforms are Font Awesome brand icon names or the aliases ``x``/``twitter``, ``ig``, ``bsky``, ``gh``, ``yt``, ``fb``, ``web``/``website``/``link`` and ``email``/``mail``. |
| `caption` | `str \| None` | A caption line above the handles, drawn by ``gt_538_caption``. |
| `stack` | `bool` | One account per line instead of a row. |
| `separator` | `str` | The string between accounts in a row. |
| `align` | `str` | The handle line's alignment: ``"left"``, ``"center"`` or ``"right"``. |
| `icon_color` | `str \| None` | The icons' color; defaults to the text color. |
| `icon_height` | `str` | The icons' CSS height (``em`` scales with ``text_size``). |
| `text_size` | `str \| None` | The handles' CSS font size; defaults to the source-note size. |
| `text_weight` | `str \| int \| None` | The handles' font weight. |
| `**kwargs` | `Any` | Passed to ``gt_538_caption`` (``rule_color``, ``rule_width``, ``size``) when ``caption`` is given. |

### Returns

`GT` — A new table with the handle line (and caption) as source notes.

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.
- `ValueError`: If ``accounts`` is not a non-empty mapping of platform to handle, an icon is not in the installed faicons, or ``align`` is not ``"left"``, ``"center"`` or ``"right"``.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_social_tag

gt = gt_social_tag(GT(pl.DataFrame({"team": ["LV"]})), {"gh": "sportsdataverse", "web": "sdv.org"})
```

### See also

- [Ported from sdvplotR ``gt_social_tag()``](https://sdvplotR.sportsdataverse.org/reference/gt_social_tag.html)

## gt_spotlight

<div class="sdv-signature">

```python
gt_spotlight(
    gt: great_tables.gt.GT,
    rows: Any,
    *,
    columns: Any = None,
    fill: str | None = None,
    text_color: str | None = None,
    bold: bool = True,
    accent_color: str | None = None,
    accent_width: float = 4,
    accent_column: Any = None,
    dim_color: str | None = 'auto',
    if_none: str = 'warn',
) -> great_tables.gt.GT
```

</div>

Light up some rows (bold, a fill, an accent bar) and dim everything else.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `rows` | `Any` | The rows to focus on: any great_tables row selection (0-based positions, a polars expression, or a function of the pandas frame). |
| `columns` | `Any` | The columns the spotlight covers; cells outside it are dimmed in the focused rows too. Defaults to every column. |
| `fill` | `str \| None` | A fill behind the focused cells. |
| `text_color` | `str \| None` | The focused cells' text color. |
| `bold` | `bool` | Bold the focused cells. |
| `accent_color` | `str \| None` | A bar on the left edge of the focused rows; giving a color turns it on. |
| `accent_width` | `float` | The bar width in pixels. |
| `accent_column` | `Any` | The column(s) the bar is drawn on; defaults to the leftmost rendered column. |
| `dim_color` | `str \| None` | The text color of everything else. ``"auto"`` (the default) blends the table's text toward its background until it sits just above 4.5:1 contrast against it (WCAG AA for text), so the rows read as muted rather than disabled, on a light or a dark theme; apply the theme first, the background is read from the table as set so far. Pass a color to choose it yourself, or ``None`` to emphasize without dimming. |
| `if_none` | `str` | When ``rows`` matches nothing: ``"warn"`` (unchanged, with an SdvplotWarning), ``"dim"`` (dim the whole table, for a spotlight that lives in another table of a grid) or ``"ignore"``. |

### Returns

`GT` — A new table with the spotlight.

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.
- `ValueError`: If ``if_none`` is not one of its choices.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_spotlight

df = pl.DataFrame({"team": ["LV", "KC", "BUF"], "wins": [10, 12, 11]})
gt = gt_spotlight(GT(df), pl.col("team") == "KC", accent_color="#E31837")
```

### See also

- [Ported from sdvplotR ``gt_spotlight()``](https://sdvplotR.sportsdataverse.org/reference/gt_spotlight.html)

## gt_stack_tables

<div class="sdv-signature">

```python
gt_stack_tables(
    tables: collections.abc.Sequence[great_tables.gt.GT] | collections.abc.Mapping[Any, great_tables.gt.GT] | None = None,
    *,
    gap: float = 16,
    align: str = 'center',
    title: Any = None,
    subtitle: Any = None,
    caption: Any = None,
    source_note: Any = None,
    caption_rule: bool = False,
    title_style: collections.abc.Mapping[str, Any] | None = None,
    subtitle_style: collections.abc.Mapping[str, Any] | None = None,
    caption_style: collections.abc.Mapping[str, Any] | None = None,
    source_note_style: collections.abc.Mapping[str, Any] | None = None,
    file: str | os.PathLike[str] | None = None,
    bg: str = 'white',
    whitespace: int = 50,
    zoom: float = 2,
) -> Any
```

</div>

Stack several tables vertically in one block, with an optional shared heading and footer.

The stack is HTML, not a ``GT``: each table keeps its own columns, widths and header. Give ``file`` to write it
straight to an image.

### Arguments

| Name | Type | Description |
|---|---|---|
| `tables` | `collections.abc.Sequence[great_tables.gt.GT] \| collections.abc.Mapping[Any, great_tables.gt.GT] \| None` | A list of ``GT`` objects (a dict's values are used in order). |
| `gap` | `float` | The space between tables, a non-negative number of pixels. |
| `align` | `str` | How tables of differing width line up: ``"center"``, ``"left"`` or ``"right"``. |
| `title` | `Any` | A heading above the stack: a string, ``md()`` or ``html()``. Plain strings are escaped (as in great_tables); use ``html()`` for markup. ``subtitle``, ``caption`` and ``source_note`` take the same. |
| `subtitle` | `Any` | A line below ``title``. |
| `caption` | `Any` | A note below the stack. |
| `source_note` | `Any` | A second line below ``caption``, right-aligned by default. |
| `caption_rule` | `bool` | Draw a hairline between ``caption`` and ``source_note``. |
| `title_style` | `collections.abc.Mapping[str, Any] \| None` | A style dict, with the keys of ``gt_grid``'s ``title_style``. |
| `subtitle_style` | `collections.abc.Mapping[str, Any] \| None` | As ``title_style``, for the subtitle. |
| `caption_style` | `collections.abc.Mapping[str, Any] \| None` | As ``title_style``, for the caption. |
| `source_note_style` | `collections.abc.Mapping[str, Any] \| None` | As ``title_style``, for the source note. |
| `file` | `str \| os.PathLike[str] \| None` | A path to write an image to; ``None`` returns the HTML. |
| `bg` | `str` | The background color when saving. |
| `whitespace` | `int` | Padding, in pixels, around the stack when saving. |
| `zoom` | `float` | The rendering zoom when saving. |

### Returns

htmltools.Tag | str | os.PathLike: The stack as HTML (it displays in a notebook), or ``file`` after writing it.

### Raises

- `TypeError`: If ``tables`` holds anything but ``GT`` objects.
- `ValueError`: If ``tables`` is empty, ``gap`` is not a non-negative number, ``zoom`` is not a positive number, ``align`` or a style key is unknown, or (when saving) ``bg``, ``whitespace`` or the extension of ``file`` is invalid.
- `nokap.ChromeNotFoundError`: If saving and no Chrome or Chromium is installed.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_stack_tables

offense = GT(pl.DataFrame({"team": ["KC", "BUF"], "epa": [0.2, 0.15]}))
defense = GT(pl.DataFrame({"team": ["BAL", "SF"], "epa": [-0.1, -0.08]}))

gt_stack_tables([offense, defense], title="Two tables", title_style={"font": "Oswald", "size": 30})
```

### See also

- [gt_grid: tables side by side. Ported from sdvplotR ``gt_stack_tables()``](https://sdvplotR.sportsdataverse.org/reference/gt_stack_tables.html)

## gt_theme_almanac

<div class="sdv-signature">

```python
gt_theme_almanac(
    gt: great_tables.gt.GT,
    accent: str = '#8C2F1E',
    density: str = 'compact',
    stripe: str | None = '#F1F1EF',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

Record-book theme: a slab body, narrow condensed labels, tight rows and banded rows, like a statistical abstract.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `accent` | `str` | Hex color of the row-group labels and the rule above the table. |
| `density` | `str` | The type and padding scale: "comfortable" (14px body), "compact" (12px) or "social" (17px, the scale saved images use). |
| `stripe` | `str \| None` | Hex color of the banded rows; None switches banding off and keeps the rest of the theme. |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme (great_tables names, e.g. ``table_font_size``). |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: A color is not hex, or ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_theme_almanac
import polars as pl

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_almanac(GT(df), stripe=None, accent="#1F3A5F")
```

### See also

- [Ported from sdvplotR ``gt_theme_almanac()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_almanac.html)

## gt_theme_athletic

<div class="sdv-signature">

```python
gt_theme_athletic(
    gt: great_tables.gt.GT,
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

The Athletic's table look: a monospaced body, uppercase sans labels, dotted row rules and thin column rules.

The row-group band is solid black with knocked-out white labels, and every column is centered. The theme sets its
sizes directly, so ``density`` rescales the finished table (as sdvplotR does).

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `density` | `str` | The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and "social" up. |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_athletic

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_athletic(GT(df), density="compact")
```

### See also

- [Ported from sdvplotR ``gt_theme_athletic()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_athletic.html)

## gt_theme_booktabs

<div class="sdv-signature">

```python
gt_theme_booktabs(
    gt: great_tables.gt.GT,
    accent: str = '#111111',
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

Academic booktabs theme: three horizontal rules and nothing else, the way LaTeX booktabs draws them.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `accent` | `str` | Hex color of the three rules and the row-group labels. |
| `density` | `str` | The type and padding scale: "comfortable", "compact" or "social". |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``accent`` is not hex, or ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_booktabs

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_booktabs(GT(df), density="compact")
```

### See also

- [Ported from sdvplotR ``gt_theme_booktabs()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_booktabs.html)

## gt_theme_broadsheet

<div class="sdv-signature">

```python
gt_theme_broadsheet(
    gt: great_tables.gt.GT,
    accent: str = '#A6081A',
    density: str = 'comfortable',
    paper: str = 'white',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

Newspaper theme: a serif body on warm paper, small letterspaced sans labels, hairlines between rows.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `accent` | `str` | Hex color of the rule above the table and the row-group labels. |
| `density` | `str` | The type and padding scale: "comfortable", "compact" or "social". |
| `paper` | `str` | The table background: "white" (a warm off-white), "salmon" (the financial-press pink) or any hex color, which keeps the neutral hairline. |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``accent`` or ``paper`` is not a hex color (or preset), or ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_broadsheet

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_broadsheet(GT(df), paper="salmon")
```

### See also

- [Ported from sdvplotR ``gt_theme_broadsheet()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_broadsheet.html)

## gt_theme_brutalist

<div class="sdv-signature">

```python
gt_theme_brutalist(
    gt: great_tables.gt.GT,
    accent: str = '#FF3B00',
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

Brutalist theme: heavy black frame, a knocked-out black label bar and one loud accent.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `accent` | `str` | The single accent color, on the row-group labels (hex). |
| `density` | `str` | The type and padding scale: "comfortable", "compact" or "social". |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``accent`` is not hex, or ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_brutalist

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_brutalist(GT(df), accent="#0047FF")
```

### See also

- [Ported from sdvplotR ``gt_theme_brutalist()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_brutalist.html)

## gt_theme_drench

<div class="sdv-signature">

```python
gt_theme_drench(
    gt: great_tables.gt.GT,
    color: str = '#123F5E',
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

Drenched theme: the whole table in one color, with rules, bands and muted text all derived from it.

The type is black or white, whichever reads better on ``color``; the muted text blends the type into the ground
until it clears 4.5:1 contrast; the rules and the row-group band shift the ground's luminance.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `color` | `str` | The hex color the table is drenched in, from near-black to a mid-saturation brand color. |
| `density` | `str` | The type and padding scale: "comfortable", "compact" or "social". |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``color`` is not hex, or ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_drench

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_drench(GT(df), color="#E31837")
```

### See also

- [Ported from sdvplotR ``gt_theme_drench()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_drench.html)

## gt_theme_gtutils

<div class="sdv-signature">

```python
gt_theme_gtutils(
    gt: great_tables.gt.GT,
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

The gtUtils look: Almarai and Signika Negative on cream, taupe row rules and a taupe row-group band.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `density` | `str` | The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and "social" up. |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_gtutils

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_gtutils(GT(df))
```

### See also

- [Ported from sdvplotR ``gt_theme_gtutils()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_gtutils.html)

## gt_theme_kenpom

<div class="sdv-signature">

```python
gt_theme_kenpom(
    gt: great_tables.gt.GT,
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

KenPom's table look: blue-banded rows, a pale-blue label band with blue labels, black row rules.

The bands are a stylesheet rule, so a cell fill (``data_color``, ``tab_style(style.fill(...))``,
``gt_color_results``, ...) shows over them whether it is applied before or after the theme. They alternate over
the data rows as drawn, so a grouped table bands by display order (sdvplotR bands by data row).

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `density` | `str` | The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and "social" up. |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_kenpom

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_kenpom(GT(df))
```

### See also

- [Ported from sdvplotR ``gt_theme_kenpom()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_kenpom.html)

## gt_theme_midnight

<div class="sdv-signature">

```python
gt_theme_midnight(
    gt: great_tables.gt.GT,
    accent: str = '#5B8DEF',
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

Dark theme: light type on a near-black ground, a raised label band and one cool accent.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `accent` | `str` | Hex color of the row-group labels and the rule above the table. |
| `density` | `str` | The type and padding scale: "comfortable", "compact" or "social". |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``accent`` is not hex, or ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_midnight

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_midnight(GT(df), accent="#3FBF87")
```

### See also

- [Ported from sdvplotR ``gt_theme_midnight()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_midnight.html)

## gt_theme_ncaa

<div class="sdv-signature">

```python
gt_theme_ncaa(
    gt: great_tables.gt.GT,
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

NCAA stats-site look: Open Sans, a black label band with white uppercase labels, striped rows, wide left inset.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `density` | `str` | The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and "social" up. |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_ncaa

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_ncaa(GT(df))
```

### See also

- [Ported from sdvplotR ``gt_theme_ncaa()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_ncaa.html)

## gt_theme_pl

<div class="sdv-signature">

```python
gt_theme_pl(
    gt: great_tables.gt.GT,
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

Premier League look: DM Sans in the league's deep purple, purple rules, a lilac row-group band.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `density` | `str` | The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and "social" up. |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_pl

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_pl(GT(df))
```

### See also

- [Ported from sdvplotR ``gt_theme_pl()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_pl.html)

## gt_theme_preview

<div class="sdv-signature">

```python
gt_theme_preview(
    data: Any,
    themes: str | list[str] | None = None,
    *,
    n: int = 5,
    density: str | None = 'compact',
) -> dict[str, great_tables.gt.GT]
```

</div>

The same few rows in every table theme, one ``GT`` per theme, to compare them side by side.

Each theme is called at its defaults, except ``density``. ``gt_theme_sdv_team`` is shown with ``league="nfl"``
and no team, i.e. the SportsDataverse colors, as R shows it.

### Arguments

| Name | Type | Description |
|---|---|---|
| `data` | `Any` | A pandas or polars DataFrame, or a ``GT`` (its data is used). |
| `themes` | `str \| list[str] \| None` | Theme function names (e.g. "gt_theme_kenpom"); None shows every ``gt_theme_*`` in ``sdvplot.great_tables``, sorted. |
| `n` | `int` | How many rows of ``data`` each table shows: a positive whole number (numpy integers count). |
| `density` | `str \| None` | The density passed to every theme that takes one, so the tables compare; None leaves each theme at its own default. |

### Returns

`dict[str, GT]` — ``{theme name: themed GT}``, in the order of ``themes``.

### Raises

- `TypeError`: ``data`` is not a DataFrame or a ``GT``.
- `ValueError`: ``data`` has no rows, a name in ``themes`` is not a theme, ``n`` is not a positive whole number, or ``density`` is not a scale.

### Example

```python
from sdvplot.great_tables import gt_theme_preview
import polars as pl
from sdvplot.great_tables import gt_theme_kenpom, gt_theme_athletic

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

tables = gt_theme_preview(df, themes=["gt_theme_kenpom", "gt_theme_athletic"])
tables["gt_theme_kenpom"]
```

### See also

- [Ported from sdvplotR ``gt_theme_preview()``, which lays the tables out with ``gt_grid()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_preview.html)

## gt_theme_savant

<div class="sdv-signature">

```python
gt_theme_savant(
    gt: great_tables.gt.GT,
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

Baseball Savant's table look: Roboto Condensed, striped rows, a black row-group band, a centered heading.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `density` | `str` | The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and "social" up. |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_savant

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_savant(GT(df))
```

### See also

- [Ported from sdvplotR ``gt_theme_savant()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_savant.html)

## gt_theme_scoreboard

<div class="sdv-signature">

```python
gt_theme_scoreboard(
    gt: great_tables.gt.GT,
    accent: str = '#0E1621',
    density: str = 'compact',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

Scoreboard theme: condensed uppercase type under a solid header band, like a broadcast stat panel.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `accent` | `str` | Hex color of the header band; the label color (black or white) adapts to it. |
| `density` | `str` | The type and padding scale: "comfortable", "compact" or "social". |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``accent`` is not hex, or ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_scoreboard

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_scoreboard(GT(df), accent="#FFC20E")
```

### See also

- [Ported from sdvplotR ``gt_theme_scoreboard()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_scoreboard.html)

## gt_theme_sdv

<div class="sdv-signature">

```python
gt_theme_sdv(
    gt: great_tables.gt.GT,
    style: str = 'light',
    density: str = 'comfortable',
    **tab_options: Any,
) -> great_tables.gt.GT
```

</div>

The SportsDataverse house table: Chivo labels, a Lato body, and the SDV gradient under the column labels.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | A great_tables ``GT``. |
| `style` | `str` | "light" (a white table) or "dark" (the SportsDataverse navy). |
| `density` | `str` | "comfortable" (as set), "compact" (smaller type and padding) or "social" (larger, for saved images). |
| `**tab_options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new, themed table. The gradient line is CSS (``thead::after``) scoped to the table's id; an id is assigned when the table has none.

### Raises

- `TypeError`: If ``gt`` is not a great_tables GT.
- `ValueError`: If ``style`` or ``density`` is unknown.

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_sdv_logos, gt_theme_sdv
import polars as pl

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_sdv(gt_sdv_logos(GT(df), "team", league="nfl").tab_header("AFC West"))
gt_theme_sdv(GT(df), style="dark", density="social")
```

### See also

- [Ported from sdvplotR ``gt_theme_sdv()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_sdv.html)

## gt_theme_sdv_team

<div class="sdv-signature">

```python
gt_theme_sdv_team(
    gt: great_tables.gt.GT,
    team: Any = None,
    *,
    league: str,
    density: str = 'comfortable',
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    **tab_options: Any,
) -> great_tables.gt.GT
```

</div>

``gt_theme_sdv`` in one team's colors: a title block in the primary color, the line in the secondary.

Ink on the title block is black or white, whichever reads better, and the subtitle is blended toward it while it
keeps 4.5:1 contrast. A secondary color too pale for a white table gives way to the primary for the line, and a
primary too light to read on white gives way to the SportsDataverse navy for the column labels.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | A great_tables ``GT``. |
| `team` | `Any` | One team (an abbreviation, name or provider id); None for the SportsDataverse navy and cyan. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `density` | `str` | "comfortable", "compact" or "social", as in ``gt_theme_sdv``. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team``, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `**tab_options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new, themed table. A team with no colors on file gets the SportsDataverse colors, with an SdvplotWarning.

### Raises

- `TypeError`: If ``gt`` is not a great_tables GT, or ``team`` is not one value.
- `InputError`: (a ValueError) If ``team`` is given and ``league`` or ``id_system`` is unknown.
- `UnresolvedTeamError`: (a ValueError) If ``team`` does not resolve to one team of ``league``.
- `ValueError`: If ``density`` is unknown.

### Example

```python
from great_tables import GT
from sdvplot.great_tables import gt_theme_sdv_team
import polars as pl

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_sdv_team(GT(df).tab_header("Chiefs leaders"), "KC", league="nfl")
```

### See also

- [Ported from sdvplotR ``gt_theme_sdv_team()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_sdv_team.html)

## gt_theme_sofa

<div class="sdv-signature">

```python
gt_theme_sofa(
    gt: great_tables.gt.GT,
    style: str = 'light',
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

SofaScore's table look: Sofia Sans Condensed on a warm cream (or dark navy) ground, no rules between rows.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `style` | `str` | "light" for the cream ground or "dark" for the navy one; on navy great_tables switches the text to white. |
| `density` | `str` | The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and "social" up. |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``style`` is not "light" or "dark", or ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_sofa

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_sofa(GT(df), style="dark")
```

### See also

- [Ported from sdvplotR ``gt_theme_sofa()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_sofa.html)

## gt_theme_swiss

<div class="sdv-signature">

```python
gt_theme_swiss(
    gt: great_tables.gt.GT,
    accent: str = '#111111',
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

International Typographic Style theme: a grotesque, generous space instead of rules, one accent rule.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `accent` | `str` | Hex color, used once, on the rule beneath the column labels. The default reads as no color at all. |
| `density` | `str` | The type and padding scale: "comfortable", "compact" or "social". |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``accent`` is not hex, or ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_swiss

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_swiss(GT(df), accent="#E30613")
```

### See also

- [Ported from sdvplotR ``gt_theme_swiss()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_swiss.html)

## gt_theme_terminal

<div class="sdv-signature">

```python
gt_theme_terminal(
    gt: great_tables.gt.GT,
    accent: str = '#FFB86C',
    density: str = 'compact',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

Terminal theme: a monospaced readout on a near-black ground, with a rule on every row.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `accent` | `str` | Hex color of the column labels, row groups and the top rule. The default is amber; "#7EE787" gives a green-phosphor variant. |
| `density` | `str` | The type and padding scale: "comfortable", "compact" or "social". |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``accent`` is not hex, or ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_terminal

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_terminal(GT(df), accent="#7EE787")
```

### See also

- [Ported from sdvplotR ``gt_theme_terminal()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_terminal.html)

## gt_theme_tier

<div class="sdv-signature">

```python
gt_theme_tier(
    gt: great_tables.gt.GT,
    style: str = 'dark',
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

Tier-list look: Oswald on a near-black (or white) ground, centered columns, a rule under every row.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `style` | `str` | "dark" for the near-black ground (great_tables switches the text to white) or "light" for white. |
| `density` | `str` | The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and "social" up. |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``style`` is not "light" or "dark", or ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_tier

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_tier(GT(df), style="light")
```

### See also

- [Ported from sdvplotR ``gt_theme_tier()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_tier.html)

## gt_theme_tufte

<div class="sdv-signature">

```python
gt_theme_tufte(
    gt: great_tables.gt.GT,
    accent: str = '#111111',
    density: str = 'comfortable',
    **options: Any,
) -> great_tables.gt.GT
```

</div>

Tufte theme: an old-style serif on cream, italic labels, one hairline under the labels and almost no ink.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The great_tables ``GT`` to theme. |
| `accent` | `str` | Hex color of the header hairline and the row-group labels; a muted red or rust gives Tufte's marginal accent. |
| `density` | `str` | The type and padding scale: "comfortable", "compact" or "social". |
| `**options` | `Any` | Passed to ``GT.tab_options`` last, so they override the theme. |

### Returns

`GT` — A new ``GT`` with the theme applied.

### Raises

- `TypeError`: ``gt`` is not a great_tables ``GT``.
- `ValueError`: ``accent`` is not hex, or ``density`` is not one of the three scales.

### Example

```python
from great_tables import GT
import polars as pl
from sdvplot.great_tables import gt_theme_tufte

df = pl.DataFrame(
    {
        "team": ["KC", "BUF", "BAL"],
        "espn_id": ["3139477", "3918298", "3916387"],
        "wins": [12, 10, 9],
    }
)

gt_theme_tufte(GT(df), accent="#A0522D")
```

### See also

- [Ported from sdvplotR ``gt_theme_tufte()``](https://sdvplotR.sportsdataverse.org/reference/gt_theme_tufte.html)

## gt_tiers

<div class="sdv-signature">

```python
gt_tiers(
    gt: great_tables.gt.GT,
    levels: collections.abc.Mapping[str, str] | collections.abc.Sequence[str],
    colors: collections.abc.Sequence[str] | None = None,
    *,
    style: str = 'dark',
    img_height: str = '55px',
    tier_column: str = 'tier',
    image_columns: Any = None,
    alt: collections.abc.Callable[[list[str]], collections.abc.Sequence[Any]] | None = None,
) -> great_tables.gt.GT
```

</div>

Build a tier list: a tier label column filled in each tier's color, the other columns rendered as images.

Applies ``gt_theme_tier(style=style)``, renders the image columns with ``fmt_image`` at ``img_height``, blanks
missing cells and every column label, then fills each tier's label cell with its color and readable bold ink. The
tier colors are recorded on the table (``_sdvplot_key``), so ``gt_legend_discrete(gt)`` draws the matching key.
Each image gets its own ``alt`` text, so a screen reader can tell the entries apart.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table: one row per tier, a tier column, and image paths or URLs in the other columns. |
| `levels` | `collections.abc.Mapping[str, str] \| collections.abc.Sequence[str]` | The tier values, in order; or one ``{level: hex color}`` mapping, leaving ``colors`` unset. |
| `colors` | `collections.abc.Sequence[str] \| None` | Hex colors paired with ``levels``. |
| `style` | `str` | ``"dark"`` or ``"light"``, passed to ``gt_theme_tier``. |
| `img_height` | `str` | The image height, as a CSS size. |
| `tier_column` | `str` | The column holding the tier values. |
| `image_columns` | `Any` | The columns to render as images (any great_tables selection); defaults to every other column. |
| `alt` | `collections.abc.Callable[[list[str]], collections.abc.Sequence[Any]] \| None` | A function from the image paths or URLs (one list of the distinct values, column by column) to their alt text, one string per image, such as ``lambda urls: [names[u] for u in urls]``. ``None`` (the default) names a mark the logo archive knows (any ``logo_url``) by its team, and any other image by its file name without the extension. The alt comes from the cell's value: a local file is embedded as a data URI, which names nothing. |

### Returns

`GT` — A new tier-list table.

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``, or ``alt`` is not a function.
- `ValueError`: If ``colors`` is missing without a mapping, the lengths differ, ``tier_column`` is not a column, a color is not hex, or ``alt`` returns the wrong number of strings.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_tiers

df = pl.DataFrame({"tier": ["S", "A"], "logo": ["https://.../kc.png", "https://.../buf.png"]})
gt = gt_tiers(GT(df), {"S": "#C84630", "A": "#5DA271"})
```

### See also

- [Ported from sdvplotR ``gt_tiers()``](https://sdvplotR.sportsdataverse.org/reference/gt_tiers.html)

## gt_title_header

<div class="sdv-signature">

```python
gt_title_header(
    gt: great_tables.gt.GT,
    title: str,
    *,
    subtitle: str | None = None,
    kicker: str | None = None,
    date: datetime.date | str | None = None,
    kicker_style: collections.abc.Mapping[str, Any] | None = None,
    title_style: collections.abc.Mapping[str, Any] | None = None,
    subtitle_style: collections.abc.Mapping[str, Any] | None = None,
    date_style: collections.abc.Mapping[str, Any] | None = None,
) -> great_tables.gt.GT
```

</div>

Add a styled header: an optional kicker line, the title, the subtitle and a date line.

Each element takes a style dict with the keys ``font`` (a Google font name), ``size``, ``color``, ``weight``,
``italic``, ``spacing`` (letter spacing), ``transform`` (e.g. ``"uppercase"``), ``align``, ``line_height``,
``margin_top``, ``margin_bottom``, ``padding_top`` and ``padding_bottom``. A number is read as pixels; a string is
any CSS length.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `title` | `str` | The title text (HTML allowed). |
| `subtitle` | `str \| None` | The subtitle text. |
| `kicker` | `str \| None` | A short line above the title, uppercase red by default. |
| `date` | `datetime.date \| str \| None` | A date under the subtitle; a ``datetime.date`` prints as "July 21, 2026", anything else as given. |
| `kicker_style` | `collections.abc.Mapping[str, Any] \| None` | Styles the kicker. |
| `title_style` | `collections.abc.Mapping[str, Any] \| None` | Styles the title. |
| `subtitle_style` | `collections.abc.Mapping[str, Any] \| None` | Styles the subtitle. |
| `date_style` | `collections.abc.Mapping[str, Any] \| None` | Styles the date (small gray by default). |

### Returns

`GT` — A new table whose header holds the styled block (it replaces any existing header).

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.
- `ValueError`: If a style dict has an unknown key.

### Example

```python
import datetime
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_title_header

gt = gt_title_header(GT(pl.DataFrame({"team": ["LV"]})), "Week 5", subtitle="Power ranking",
                     kicker="NFL", date=datetime.date(2026, 10, 4))
```

### See also

- [Ported from sdvplotR ``gt_title_header()``](https://sdvplotR.sportsdataverse.org/reference/gt_title_header.html)

## gt_watermark

<div class="sdv-signature">

```python
gt_watermark(
    gt: great_tables.gt.GT,
    text: str | None = None,
    *,
    image: str | pathlib.Path | None = None,
    opacity: float = 0.06,
    size: str = '60%',
    position: str = 'center',
    color: str = '#000000',
    angle: float = 0,
    font: str = 'Helvetica, Arial, sans-serif',
) -> great_tables.gt.GT
```

</div>

Put a faint text or image watermark behind the table body.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `text` | `str \| None` | Text to draw as the watermark (an inline SVG, so ``font`` must be a font the viewer has). |
| `image` | `str \| pathlib.Path \| None` | Instead of ``text``, a PNG, JPEG, SVG or GIF file, embedded as a ``data:`` URI. |
| `opacity` | `float` | How faint the watermark is, 0 to 1. |
| `size` | `str` | The watermark's size relative to the table body, as a CSS background size. |
| `position` | `str` | Where it sits, as a CSS background position (``"center"``, ``"right bottom"``). |
| `color` | `str` | The text color (``text`` only). |
| `angle` | `float` | Rotation in degrees (``text`` only). |
| `font` | `str` | The font family for ``text``. |

### Returns

`GT` — A new table with the watermark as the body's CSS background (the table gets an id if it had none).

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.
- `ValueError`: If neither or both of ``text`` and ``image`` are given, or ``image`` is not a supported type.
- `FileNotFoundError`: If ``image`` does not exist.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_watermark

gt = gt_watermark(GT(pl.DataFrame({"team": ["LV"]})), text="DRAFT", angle=-30)
```

### See also

- [Ported from sdvplotR ``gt_watermark()``](https://sdvplotR.sportsdataverse.org/reference/gt_watermark.html)

## gt_wrap_labels

<div class="sdv-signature">

```python
gt_wrap_labels(
    gt: great_tables.gt.GT,
    columns: Any = None,
    width: int = 12,
    balance: bool = True,
) -> great_tables.gt.GT
```

</div>

Wrap long column labels onto several lines, so narrow columns keep readable headers.

A one-word label, or one already shorter than ``width``, is left alone; a single long word is never split.

### Arguments

| Name | Type | Description |
|---|---|---|
| `gt` | `great_tables.gt.GT` | The table. |
| `columns` | `Any` | The columns whose labels wrap (any great_tables selection); defaults to every column. |
| `width` | `int` | The target line length in characters (lines stay shorter than this, as R's ``strwrap``). |
| `balance` | `bool` | Even the lines out instead of filling them greedily. |

### Returns

`GT` — A new table with the wrapped labels.

### Raises

- `TypeError`: If ``gt`` is not a great_tables ``GT``.
- `ValueError`: If ``columns`` names a column the table lacks.

### Example

```python
import polars as pl
from great_tables import GT
from sdvplot.great_tables import gt_wrap_labels

gt = gt_wrap_labels(GT(pl.DataFrame({"Expected points added per play": [0.12]})))
```

### See also

- [Ported from sdvplotR ``gt_wrap_labels()``](https://sdvplotR.sportsdataverse.org/reference/gt_wrap_labels.html)

## pal_midnight

<div class="sdv-signature">

```python
pal_midnight = ('#3FBF87', '#8FD9A8', '#D8D6A0', '#E8996B', '#E0645C')
```

</div>

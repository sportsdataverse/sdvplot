---
title: sdvplot.perspective
sidebar_label: sdvplot.perspective
sidebar_position: 29
---

# sdvplot.perspective

Perspective (``pip install sdvplot[perspective]``, Python 3.11+): team colors, registry fonts and a logo column for a Perspective viewer.

| Name | What it is |
|---|---|
| [perspective_logo_column](#perspective_logo_column) | The frame with a column of each team's logo URL, right after the team column. |
| [perspective_sdv_config](#perspective_sdv_config) | A Perspective viewer config that colors each team by its own colors, for the Datagrid or a chart. |

## perspective_logo_column

<div class="sdv-signature">

```python
perspective_logo_column(
    frame: Any,
    team_col: str,
    *,
    league: str,
    name: str | None = None,
    season: Any = None,
    variant: str = 'default',
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
) -> Any
```

</div>

The frame with a column of each team's logo URL, right after the team column.

Each distinct team is resolved once. A team that does not resolve, or has no archived logo, gets a null URL, with
one warning for each reason. Show the column as links with ``perspective_sdv_config(..., logo_col=...)``:
Perspective 5.5's Datagrid draws no images.

### Arguments

| Name | Type | Description |
|---|---|---|
| `frame` | `Any` | A polars or pandas DataFrame (anything narwhals reads eagerly); the result is of the same library, with the same rows (and pandas index). |
| `team_col` | `str` | The column holding team identifiers. |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `name` | `str \| None` | The new column's name. Default: ``f"{team_col}_logo"``. It must not be a column already. |
| `season` | `Any` | One season for every team: the logo of that season (relocations and rebrands). |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of the team values, as in ``resolve``. |
| `strict` | `bool` | Raise UnresolvedTeamError for a team that does not resolve, instead of warning. |

### Returns

The frame, with the logo URLs as a string column (null where there is none).

### Raises

- `InputError`: For a missing ``team_col``, a ``name`` the frame already has, or an unknown ``variant``, ``id_system`` or season.
- `UnresolvedTeamError`: With ``strict=True``, for a team that does not resolve.

### Example

```python
import polars as pl
from sdvplot.perspective import perspective_logo_column, perspective_sdv_config

epa = pl.DataFrame({"posteam": ["BAL", "BUF", "DET"], "epa_per_play": [0.218, 0.1885, 0.1592]})
out = perspective_logo_column(epa, "posteam", league="nfl")
print(out.columns)  # ['posteam', 'posteam_logo', 'epa_per_play']
cfg = perspective_sdv_config(out, team_col="posteam", league="nfl", logo_col="posteam_logo")
```

### See also

- perspective_sdv_config: the viewer config that shows the column as links
- logo_url: one team's logo URL

## perspective_sdv_config

<div class="sdv-signature">

```python
perspective_sdv_config(
    frame: Any,
    *,
    team_col: str,
    league: str,
    plugin: str = 'Datagrid',
    theme: str | None = None,
    mode: Literal['light', 'dark'] = 'light',
    logo_col: str | None = None,
    background: str | None = None,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
) -> dict[str, Any]
```

</div>

A Perspective viewer config that colors each team by its own colors, for the Datagrid or a chart.

The colors are the shared team palette (as the deck.gl and pydeck adapters use), taken over the teams in sorted
order: each team's color, made 3:1 against the background and ΔE 20 from every earlier team's, so a team keeps one
color whatever the frame's order. Perspective takes a palette, not a color per value, so each palette lists those
colors in the order Perspective hands colors out (checked in Chromium on Perspective 5.5.1):

- ``plugin="Datagrid"``: the team column's cells are filled (``bg_mode`` "series"; Perspective picks a readable
  text color). The grid gives the palette to the values in the order it first draws them, so it is in the frame's
  order of first appearance: keep the grid's rows in the frame's order (no ``sort``), and keep it to about one row
  per team. In a long grid, scrolling past a team the grid has not drawn yet shifts every later color. Only a
  string team column is filled: Perspective rejects a fill on a number column.
- a chart plugin: the view is yours. Split a bar, line or area chart by the team (``split_by=[team_col]``) and
  each team's series takes its color from every numeric column's ``palette``, in sorted order, because Perspective
  sorts split values. Put the team column in an "X/Y Scatter"'s Color slot (its third column) and each team's
  points take theirs from the team column's ``palette``, in the frame's order, the order Perspective meets them (a
  scatter's ``split_by`` draws one panel per team instead). Checked on "X Bar", "Y Bar", "Y Line" and
  "X/Y Scatter"; a Treemap or Sunburst hands colors out in drawing order, which this does not follow.

### Arguments

| Name | Type | Description |
|---|---|---|
| `frame` | `Any` | The data the viewer shows: a polars or pandas DataFrame (anything narwhals reads eagerly). |
| `team_col` | `str` | The column holding team identifiers (any id system ``resolve`` reads). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `plugin` | `str` | The Perspective plugin: "Datagrid" (the default) or a chart's name. |
| `theme` | `str \| None` | A registry table theme (``sdv_table_themes()``). On the Datagrid it sets the font family and size (``plugin_config``), each numeric column's sign colors (its ``neg`` and ``pos``) and, when the theme has a numeric face of its own, the numeric columns' font. Perspective quotes the value as one family name (no fallback stack), so the page must load the font itself (Google Fonts), or the browser draws its default font. Charts take no fonts from a config. |
| `mode` | `Literal['light', 'dark']` | "light" or "dark": the Perspective theme ("Pro Light" or "Pro Dark") and the registry theme's mode. |
| `logo_col` | `str \| None` | A logo URL column (``perspective_logo_column``) to show as links on the Datagrid. Perspective 5.5's Datagrid draws no images, so a link is the one format a URL column has. |
| `background` | `str \| None` | The color the teams must read against. Default: the Perspective theme's background (#ffffff for "Pro Light", #242526 for "Pro Dark"). |
| `season` | `Any` | One season for every team (the table rule). |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of the team values, as in ``resolve``. |
| `strict` | `bool` | Raise UnresolvedTeamError for a team that does not resolve, instead of warning once and giving it #808080. |

### Returns

`dict` — ``plugin``, ``theme`` and ``columns_config``, plus ``plugin_config`` for the Datagrid with a registry theme. Pass it as ``PerspectiveWidget(data, **config)`` or to ``viewer.restore()``; merge your own ``group_by``, ``split_by``, ``columns`` and the rest into it.

### Raises

- `InputError`: For a column the frame does not have, an unknown ``mode``, ``theme`` or ``id_system``, a season outside the league's, or a dark ``mode`` on a light-only theme.
- `UnresolvedTeamError`: With ``strict=True``, for a team that does not resolve.

### Example

```python
import polars as pl
from sdvplot.perspective import perspective_sdv_config

# 2024 regular season, offense: EPA per play (nflverse play-by-play)
epa = pl.DataFrame({"posteam": ["BAL", "BUF", "DET"], "epa_per_play": [0.218, 0.1885, 0.1592]})
cfg = perspective_sdv_config(epa, team_col="posteam", league="nfl", theme="datagolf")
print(cfg["columns_config"]["posteam"]["bg_color"])
bars = perspective_sdv_config(epa, team_col="posteam", league="nfl", plugin="Y Bar")
bars |= {"group_by": ["posteam"], "split_by": ["posteam"], "columns": ["epa_per_play"]}
# in a notebook: PerspectiveWidget(epa, **cfg)
```

### See also

- perspective_logo_column: a logo URL column to show beside the team
- table_theme_spec: the registry theme this reads
- [Perspective](https://perspective-dev.github.io/)

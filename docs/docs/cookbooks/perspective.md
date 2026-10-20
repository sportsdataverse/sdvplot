---
title: "Perspective cookbook"
sidebar_label: "Perspective"
sidebar_position: 17
description: "Six Perspective recipes: an NFL leaderboard with team fills and logo links, the same table in a registry theme, bars and a division race in team colors, offense against defense in the dark, and a season of play-by-play pivoted in the browser."
---

# Perspective

[Perspective](https://perspective-dev.github.io/) is an interactive data grid and chart viewer: a WebAssembly
engine that pivots, filters and aggregates in the browser, and a `<perspective-viewer>` element that shows the result
as a grid or a chart, which the reader can re-pivot. `sdvplot.perspective` builds two things for it:

- `perspective_sdv_config()`: a viewer config in team colors. On the Datagrid it fills each team's cells; on a chart it
  gives each team its color, for a view split by team or a scatter colored by team. A registry table theme adds its
  fonts and sign colors.
- `perspective_logo_column()`: each team's logo URL, as a column beside the team, which the Datagrid shows as a link
  (Perspective 5.5's grid draws no images).

The config is plain data: in Jupyter pass it to the widget as `PerspectiveWidget(frame, **config)`, and in a web page
to the viewer's `restore()`. The module needs `pip install "sdvplot[perspective]"` and Python 3.11+ (Perspective ships
wheels for 3.11 and later only).

Every number here comes from the 2024 NFL regular season's play-by-play (nflverse, through sportsdataverse-py), never
typed in. A docs page has no Jupyter kernel for the widget to talk to, so each recipe is drawn by the small `show()`
helper below: a standalone page that loads Perspective 5.5.1 from jsDelivr and restores the config, as the widget
does in a notebook.

```python
import html
import json

import polars as pl
import sportsdataverse.nfl as nfl
from IPython.display import HTML

import sdvplot
from sdvplot.perspective import perspective_logo_column, perspective_sdv_config

SEASON = 2024
PSP = "https://cdn.jsdelivr.net/npm/@perspective-dev"
PSP_VERSION = "5.5.1"  # the floor of the [perspective] extra, which the tests run against


def show(frame, config, *, height=440, theme=None):
    """``frame`` in a <perspective-viewer> restored to ``config``, as a standalone page (Perspective from jsDelivr).
    In Jupyter, ``PerspectiveWidget(frame.to_pandas(), **config)`` shows the same live, backed by the kernel."""
    fonts = ""
    if theme is not None:  # a registry theme names Google Fonts faces: the page loads them
        f = sdvplot.table_theme_spec(theme).fonts
        for family in sorted({x for x in (f.get("body"), f.get("numeric")) if x}):
            url = f"https://fonts.googleapis.com/css2?family={family.replace(' ', '+')}&display=swap"
            fonts += f'<link rel="stylesheet" href="{html.escape(url)}">\n'
    data = json.dumps(frame.to_dict(as_series=False)).replace("</", "<\\/")
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<link rel="stylesheet" crossorigin="anonymous" href="{PSP}/viewer@{PSP_VERSION}/dist/css/themes.css">
{fonts}<style>body{{margin:0}} perspective-viewer{{display:block;height:{height}px}}</style>
</head><body><perspective-viewer></perspective-viewer>
<script type="module">
import "{PSP}/viewer@{PSP_VERSION}/dist/cdn/perspective-viewer.js";
import "{PSP}/viewer-datagrid@{PSP_VERSION}/dist/cdn/perspective-viewer-datagrid.js";
import "{PSP}/viewer-charts@{PSP_VERSION}/dist/cdn/perspective-viewer-charts.js";
import perspective from "{PSP}/client@{PSP_VERSION}/dist/cdn/perspective.js";
const worker = await perspective.worker();
await worker.table({data}, {{name: "sdv"}});
const viewer = document.querySelector("perspective-viewer");
await viewer.load(worker);
await viewer.restore({{table: "sdv", settings: false, ...{json.dumps(config)}}});
</script></body></html>"""
    return HTML(page)
```

Each pass or run with an EPA, in the regular season, is one row. The team tables below sum them by offense
(`posteam`) and by defense (`defteam`); nflverse's team codes (`LA` for the Rams, `WAS`) resolve as they are.

```python
pbp = nfl.load_nfl_pbp([SEASON])
plays = pbp.filter(
    pl.col("season_type") == "REG",
    pl.col("play_type").is_in(["pass", "run"]),
    pl.col("epa").is_not_null(),
    pl.col("posteam").is_not_null(),
).select("week", "posteam", "defteam", "play_type", "epa", "success")
offense = plays.group_by("posteam").agg(
    plays=pl.len(), epa_per_play=pl.col("epa").mean().round(3), success_rate=pl.col("success").mean().round(3)
)
defense = plays.group_by("defteam").agg(def_epa_per_play=pl.col("epa").mean().round(3))
assert offense.schema["posteam"] == defense.schema["defteam"]  # one dtype for the team key on both sides
teams = offense.join(defense, left_on="posteam", right_on="defteam").sort("epa_per_play", descending=True)
print(plays.height, "plays;", teams.height, "teams")
teams.head(5)
```

<div class="sdv-output">

```text
33470 plays; 32 teams
```

| posteam | plays | epa_per_play | success_rate | def_epa_per_play |
|---------|-------|--------------|--------------|------------------|
| BAL     | 1039  | 0.218        | 0.5          | -0.051           |
| BUF     | 1005  | 0.188        | 0.475        | -0.009           |
| DET     | 1099  | 0.17         | 0.501        | -0.062           |
| WAS     | 1091  | 0.139        | 0.485        | 0.011            |
| TB      | 1084  | 0.13         | 0.494        | 0.015            |

</div>

## 1. A leaderboard with team fills and logo links

On the Datagrid, `perspective_sdv_config` fills the team column's cells with each team's color, and Perspective picks
a readable text color on each fill. The grid hands its palette out in the order it first draws each team, so the
palette is in the frame's order: the config sets no `sort`, and the frame is already sorted, one row per team.
`perspective_logo_column` puts each team's logo URL after the team, and `logo_col` shows it as a link; here the
`columns` list moves it to the end, where the long URLs do not push the numbers off the page. Each number column also
gets a format: a rate or EPA to 3 decimals, a percentage to 1, an integer plain (`formats=` overrides one).

```python
board = perspective_logo_column(teams, "posteam", league="nfl", season=SEASON)
config = perspective_sdv_config(board, team_col="posteam", league="nfl", logo_col="posteam_logo")
config["columns"] = ["posteam", "plays", "epa_per_play", "success_rate", "def_epa_per_play", "posteam_logo"]
print(config["columns_config"]["posteam"]["bg_color"][:80], "...")
show(board, config)
```

<div class="sdv-output">

```text
linear-gradient(to right, #241773, #c60c30, #8d9296, #5a1414, #b85149, #53575f,  ...
```

<iframe class="sdv-frame" src="/outputs/cookbooks/perspective/5_1.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 2. The same table in a registry theme

`theme=` takes any of the 122 registry table themes (`sdvplot.sdv_table_themes()`). On the Datagrid it sets the font
and size (`plugin_config`) and gives each number column the theme's negative and positive colors, so an offense or
defense below zero EPA per play reads in the theme's red. The page has to load the font: `show()` adds the Google
Fonts link. Perspective's own "Pro Light" theme still draws the grid lines and header.

```python
config = perspective_sdv_config(board.drop("posteam_logo"), team_col="posteam", league="nfl", theme="rbsdm")
print(config["plugin_config"], config["columns_config"]["epa_per_play"])
show(board.drop("posteam_logo"), config, theme="rbsdm")
```

<div class="sdv-output">

```text
{'font_family': 'Space Grotesk', 'font_size': 14} {'number_format': {'minimumFractionDigits': 3, 'maximumFractionDigits': 3}, 'fg_color': 'linear-gradient(to right, #a1231b 0%, #17692f 100%)'}
```

<iframe class="sdv-frame" src="/outputs/cookbooks/perspective/7_1.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 3. Success rate as bars in team colors

On a chart, the view is yours to set, and the config colors it. Split by the team (`split_by`) and each team's series
takes its color from the number column's `palette`, which lists the teams in ascending order of team code: Perspective
sorts the values it splits by, whatever the frame's order. Grouping by the team as well (`group_by`) puts one bar per
team, and the sort orders the bars. A team has one color in every recipe here: the palette is taken over the teams in
sorted order, then listed in whichever order Perspective needs.

```python
config = perspective_sdv_config(teams, team_col="posteam", league="nfl", plugin="X Bar")
config |= {
    "group_by": ["posteam"],
    "split_by": ["posteam"],
    "columns": ["success_rate"],
    "sort": [["success_rate", "desc"]],
}
show(teams, config, height=620)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/perspective/9_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 4. A division race, week by week

Cumulative EPA by week for the AFC North, summed in polars, then drawn as one line per team. Each team keeps its
color: the four are made readable on the white background and at least ΔE 20 apart, so Baltimore's purple and
Pittsburgh's black stay distinct from Cleveland's brown and Cincinnati's orange.

```python
north = (
    plays.filter(pl.col("posteam").is_in(["BAL", "PIT", "CIN", "CLE"]))
    .group_by("posteam", "week")
    .agg(epa=pl.col("epa").sum())
    .sort("week")
    .with_columns(cumulative_epa=pl.col("epa").cum_sum().over("posteam").round(1))
    .select("week", "posteam", "cumulative_epa")
)
config = perspective_sdv_config(north, team_col="posteam", league="nfl", plugin="Y Line")
config |= {"group_by": ["week"], "split_by": ["posteam"], "columns": ["cumulative_epa"]}
show(north, config)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/perspective/11_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 5. Offense against defense, in the dark

`mode="dark"` switches to Perspective's "Pro Dark" theme and builds the palette against its background (#242526), so
every team's color is at least 3:1 against it: a team whose colors are too dark there is lightened. One point per
team, offense EPA per play across and defense up (lower is better on defense). A scatter takes its colors from the
column in its third slot, Color: the team column. Perspective colors those categories in the order it meets them, the
rows' order, so the config lists the team column's `palette` in the frame's order. (Split by team, a scatter draws one
small panel per team instead.)

```python
config = perspective_sdv_config(teams, team_col="posteam", league="nfl", plugin="X/Y Scatter", mode="dark")
config |= {"columns": ["epa_per_play", "def_epa_per_play", "posteam"]}
show(teams.select("posteam", "epa_per_play", "def_epa_per_play"), config)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/perspective/13_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 6. A season of play-by-play, pivoted by Perspective

Here the page gets the plays themselves, about 33,000 rows (three columns, EPA rounded), and Perspective does the
pivot in the browser: passing plays only, grouped and split by offense, with the mean EPA per team. The reader can
change the filter to `run`, or the aggregate, and the bars keep their team colors, because the palette follows the
split values, not the numbers.

```python
season = plays.select("posteam", "play_type", pl.col("epa").round(3))
config = perspective_sdv_config(season, team_col="posteam", league="nfl", plugin="Y Bar")
config |= {
    "group_by": ["posteam"],
    "split_by": ["posteam"],
    "columns": ["epa"],
    "aggregates": {"epa": "avg"},
    "filter": [["play_type", "==", "pass"]],
    "sort": [["epa", "desc"]],
}
show(season, config)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/perspective/15_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## Run it yourself

<a href="pathname:///notebooks/cookbooks/perspective.ipynb" download>Download the notebook</a> (outputs cleared) or [open it on GitHub](https://github.com/sportsdataverse/sdvplot/blob/main/examples/notebooks/cookbooks/perspective.ipynb).

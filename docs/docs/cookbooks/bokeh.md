---
title: "Bokeh cookbook"
sidebar_label: "Bokeh"
sidebar_position: 10
description: "Four Bokeh recipes: team-colored bars with logos, headshots with hover, wordmarks on a horizontal bar chart, and linked panels sharing one data source."
---

# Bokeh

[Bokeh](https://bokeh.org/) builds interactive browser charts from Python: pan, zoom, hover and linked selection.
sdvplot's Bokeh adapter adds `add_logos`, `add_wordmarks` and `add_headshots`, each drawn as one `image_url` glyph
sized in screen pixels so the images keep their size when you zoom, and `sdvplot.team_colors()` gives the fill
colors. Bokeh glyphs cannot sit outside the plot frame, so there are no axis logos (see
[Interactive charts](interactive-web.md), which also covers a hover tool on NHL logos and logos in place of
axis labels).

The data is one completed season each from MLB (ESPN), the NBA (hoopR), the NFL (nflverse) and the WNBA (wehoop),
all through sportsdataverse-py.

```python
import polars as pl
import sportsdataverse.mlb as mlb
import sportsdataverse.nba as nba
import sportsdataverse.nfl as nfl
import sportsdataverse.wnba as wnba
from bokeh.io import output_notebook, show
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure

import sdvplot

output_notebook(hide_banner=True)
NFL_SEASON = 2025  # football names a season by the year it starts
SEASON = 2026  # the 2026 MLB and WNBA seasons, and the 2025-26 NBA season
```

## 1. Team-colored bars with a logo on top

`sdvplot.team_colors()` returns one hex color per team, in order, which Bokeh's `vbar` takes as `color`. The logos
go on a categorical x axis by passing the team names as x, and sit just above each bar. MLB runs per game, top 12:

```python
mlb_runs = (
    mlb.espn_mlb_standings(season=SEASON)
    .with_columns(rs=pl.col("points_for") / pl.col("games_played"))
    .sort(["rs", "team_abbreviation"], descending=[True, False])
    .head(12)
)
teams = mlb_runs["team_abbreviation"].to_list()
source = ColumnDataSource({"team": teams, "rs": mlb_runs["rs"].to_list(), "color": sdvplot.team_colors("mlb", teams)})

p = figure(
    x_range=teams, frame_width=700, frame_height=380, y_range=(0, mlb_runs["rs"].max() * 1.18),
    title=f"MLB runs scored per game, {SEASON} (top 12; data: ESPN via sportsdataverse-py)",
    y_axis_label="Runs per game", toolbar_location=None,
)  # fmt: skip
bars = p.vbar(x="team", top="rs", width=0.7, color="color", source=source)
p.add_tools(HoverTool(renderers=[bars], tooltips=[("Team", "@team"), ("Runs/game", "@rs{0.00}")]))
sdvplot.add_logos(p, teams, (mlb_runs["rs"] + mlb_runs["rs"].max() * 0.07).to_list(), teams, league="mlb", height=0.1)
p.xgrid.grid_line_color = None
show(p)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/bokeh/3_0.html" title="Interactive Bokeh figure" height="480" loading="lazy"></iframe>

</div>

## 2. Headshots with a hover tool

`add_headshots` takes ESPN athlete ids. As with logos, a transparent scatter under the images carries the
`HoverTool`, since an `image_url` glyph has no hit testing. NBA scoring leaders, points per game against true
shooting:

```python
fga, fta = pl.col("field_goals_attempted"), pl.col("free_throws_attempted")
nba_scorers = (
    nba.load_nba_player_boxscore(seasons=[SEASON])
    .filter((pl.col("season_type") == 2) & pl.col("did_not_play").not_() & pl.col("minutes").is_not_null())
    .group_by("athlete_id", "athlete_display_name", "team_abbreviation", maintain_order=True)
    .agg(games=pl.len(), ppg=pl.col("points").mean(), ts=pl.col("points").sum() / (2 * (fga.sum() + 0.44 * fta.sum())))
    .filter(pl.col("games") >= 40)
    .sort("ppg", descending=True)
    .head(15)
    .with_columns(pl.col("athlete_id").cast(pl.Int64).cast(pl.Utf8))
)

source = ColumnDataSource(nba_scorers.to_pandas())
p = figure(
    frame_width=640, frame_height=440, title=f"NBA scoring leaders, {SEASON - 1}-{SEASON % 100} (40+ games)",
    x_axis_label="True shooting %", y_axis_label="Points per game",
)  # fmt: skip
dots = p.scatter("ts", "ppg", source=source, size=40, alpha=0)
p.add_tools(
    HoverTool(
        renderers=[dots],
        tooltips=[
            ("Player", "@athlete_display_name"),
            ("Team", "@team_abbreviation"),
            ("PPG", "@ppg{0.0}"),
            ("TS%", "@ts{0.0%}"),
        ],
    )
)
p.x_range.range_padding = p.y_range.range_padding = 0.15
sdvplot.add_headshots(p, nba_scorers["ts"], nba_scorers["ppg"], nba_scorers["athlete_id"], league="nba", height=0.11)
show(p)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/bokeh/5_0.html" title="Interactive Bokeh figure" height="480" loading="lazy"></iframe>

</div>

## 3. Wordmarks on a horizontal bar chart

`add_wordmarks` works on a categorical y axis the same way: pass the team names as y. The wordmarks sit inside the
plot at the end of each bar, colored with each team's primary color and outlined in its secondary. The NFL's ten
best offenses by EPA per play:

```python
weeks = nfl.load_nfl_team_stats([NFL_SEASON]).filter(pl.col("season_type") == "REG")
plays = pl.col("attempts") + pl.col("sacks_suffered") + pl.col("carries")
nfl_off = (
    weeks.group_by("team", maintain_order=True)
    .agg(off_epa=(pl.col("passing_epa") + pl.col("rushing_epa")).sum() / plays.sum())
    .sort(["off_epa", "team"], descending=[True, False])
    .head(10)
    .reverse()  # Bokeh draws the first factor at the bottom
)
teams = nfl_off["team"].to_list()
top = nfl_off["off_epa"].max()

p = figure(
    y_range=teams, frame_width=640, frame_height=440, x_range=(0, top * 1.45), toolbar_location=None,
    title=f"NFL offense EPA per play, {NFL_SEASON} regular season (top 10)", x_axis_label="EPA per play",
)  # fmt: skip
p.hbar(
    y=teams, right=nfl_off["off_epa"].to_list(), height=0.7,
    fill_color=sdvplot.team_colors("nfl", teams), line_color=sdvplot.team_colors("nfl", teams, which="secondary"),
    line_width=3,
)  # fmt: skip
sdvplot.add_wordmarks(p, (nfl_off["off_epa"] + top * 0.2).to_list(), teams, teams, league="nfl", height=0.06)
p.yaxis.major_label_text_font_size = "0pt"  # the wordmarks name the teams
p.ygrid.grid_line_color = None
show(p)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/bokeh/7_0.html" title="Interactive Bokeh figure" height="480" loading="lazy"></iframe>

</div>

## 4. Linked panels that share one data source

Two figures that share a `ColumnDataSource` and an x range stay in step: pan or zoom one and the other follows, and
a box selection in either highlights the same teams in both. Call `add_logos` once per figure. WNBA points scored
against points allowed, and against three-point attempt rate:

```python
wnba_teams = (
    wnba.load_wnba_team_boxscore(seasons=[SEASON])
    .filter(pl.col("season_type") == 2)
    .group_by("team_abbreviation", maintain_order=True)
    .agg(
        games=pl.len(),
        scored=pl.col("team_score").mean(),
        allowed=pl.col("opponent_team_score").mean(),
        three_rate=pl.col("three_point_field_goals_attempted").sum() / pl.col("field_goals_attempted").sum(),
    )
    .filter(pl.col("games") > 10)  # drops the All-Star Game's teams
    .sort("team_abbreviation")
)
wnba_teams = wnba_teams.with_columns(color=pl.Series(sdvplot.team_colors("wnba", wnba_teams["team_abbreviation"])))
source = ColumnDataSource(wnba_teams.to_pandas())
tools = "pan,box_zoom,box_select,reset"
hover = [
    ("Team", "@team_abbreviation"),
    ("Scored", "@scored{0.0}"),
    ("Allowed", "@allowed{0.0}"),
    ("3PA rate", "@three_rate{0.0%}"),
]

left = figure(frame_width=330, frame_height=320, tools=tools, tooltips=hover, title="Scored vs allowed per game",
              x_axis_label="Points scored per game", y_axis_label="Points allowed per game")  # fmt: skip
right = figure(frame_width=330, frame_height=320, tools=tools, tooltips=hover, x_range=left.x_range,
               title="Scored vs three-point attempt rate", x_axis_label="Points scored per game",
               y_axis_label="3PA / FGA")  # fmt: skip
for fig, y in ((left, "allowed"), (right, "three_rate")):
    fig.scatter("scored", y, source=source, size=34, fill_color="color", fill_alpha=0.25, line_color="color",
                selection_fill_alpha=0.6, nonselection_fill_alpha=0.05)  # fmt: skip
    fig.y_range.range_padding = 0.15
    sdvplot.add_logos(
        fig, wnba_teams["scored"], wnba_teams[y], wnba_teams["team_abbreviation"], league="wnba", height=0.09
    )
left.x_range.range_padding = 0.12
show(gridplot([[left, right]], toolbar_location="right"))
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/bokeh/9_0.html" title="Interactive Bokeh figure" height="480" loading="lazy"></iframe>

</div>

## Run it yourself

<a href="pathname:///notebooks/cookbooks/bokeh.ipynb" download>Download the notebook</a> (outputs cleared) or [open it on GitHub](https://github.com/sportsdataverse/sdvplot/blob/main/examples/notebooks/cookbooks/bokeh.ipynb).

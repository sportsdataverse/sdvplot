---
title: "reactable formatters cookbook"
sidebar_label: "reactable formatters"
sidebar_position: 13
description: "reactablefmtr's cell formatters with sdvplot, one recipe each: NBA data bars with logos, NFL EPA color tiles, MLB color scales, WNBA pill buttons and headshots, NHL icon sets and bubbles, SEC win dots, NFL win trends and men's college basketball highlights."
---

# reactable formatters

[reactablefmtr](https://kcuilla.github.io/reactablefmtr/) is the R package that dresses up reactable cells: data bars,
color tiles and scales, pill buttons, icon sets, merged columns, highlights and bubble grids. `sdvplot.reactable`
ports its cell formatters to [reactable-py](https://machow.github.io/reactable-py/) as ordinary `reactable.Column`
objects, with reactablefmtr's semantics and defaults (the same color ramps, buckets and layouts), and adds the
SportsDataverse parts: any formatter that takes a color column also takes a team column and a league, filling each cell
in that team's color with text that stays readable, and data bars and merged columns can carry the row's logo,
headshot or wordmark. Icons are inline SVG and tooltips are the cell's `title`, so the tables need no Font Awesome and
no extra JavaScript.

Each formatter takes the frame you pass to `Reactable` (it reads ranges, buckets and team colors from it) and the
column's `id`. Every section below is one formatter on real data from sportsdataverse-py, across the NFL, NBA, WNBA,
NHL, MLB and college sports. The [reactable](reactable.md) cookbook covers the logo, headshot and team-color columns
these build on.

```python
import polars as pl
import sportsdataverse.cfb as cfb
import sportsdataverse.mbb as mbb
import sportsdataverse.mlb as mlb
import sportsdataverse.nba as nba
import sportsdataverse.nfl as nfl
import sportsdataverse.nhl as nhl
import sportsdataverse.wnba as wnba
from reactable import Column, Reactable, embed_css

import sdvplot
from sdvplot.reactable import (
    reactable_sdv_bubble_grid,
    reactable_sdv_color_scales,
    reactable_sdv_color_tiles,
    reactable_sdv_data_bars,
    reactable_sdv_highlight,
    reactable_sdv_icon_assign,
    reactable_sdv_icon_sets,
    reactable_sdv_icon_trend,
    reactable_sdv_logos,
    reactable_sdv_merge_column,
    reactable_sdv_pill_buttons,
)

NFL_SEASON = 2025  # nflverse and cfbfastR name a season by the year it starts
SEASON = 2026  # the 2026 MLB and WNBA seasons, and the 2025-26 NBA, NHL and college basketball seasons
embed_css()
```

## 1. Data bars in team colors: NBA wins

`reactable_sdv_data_bars` draws each value as a bar, its length the value's share of the column's largest. With
`team_col` and `league` every bar takes its team's primary color, the number inside switches to white on a dark bar,
and `mark="logo"` puts the team's logo at the end of the bar. `tooltip=True` gives each cell a hover title. The data is
the 2025-26 NBA regular season, summed from ESPN team box scores.

```python
nba_teams = (
    nba.load_nba_team_boxscore(seasons=[SEASON])
    .filter(pl.col("season_type") == 2)
    .group_by("team_abbreviation", "team_display_name", maintain_order=True)
    .agg(gp=pl.len(), wins=pl.col("team_winner").sum())
    .filter(pl.col("gp") > 10)
    .sort(["wins", "team_abbreviation"], descending=[True, False])
    .head(12)
    .drop("gp")
)
Reactable(
    nba_teams,
    columns=[
        Column(id="team_abbreviation", show=False),
        Column(id="team_display_name", name="Team", min_width=190),
        reactable_sdv_data_bars(
            nba_teams,
            team_col="team_abbreviation",
            league="nba",
            mark="logo",
            mark_height=22,
            bar_height=24,
            round_edges=True,
            tooltip=True,
            id="wins",
            name="Wins",
            min_width=320,
        ),
    ],
    default_page_size=12,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-formatters/3_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 2. Color tiles: NFL offense and defense by EPA

`reactable_sdv_color_tiles` fills each cell with a rounded tile on a color ramp: reactablefmtr's default
blue-white-orange, or any hex colors you give, here red to green. `number_fmt` takes a format spec (or a function);
the defensive column reverses the ramp because less allowed is better. The team column is tiled too, in each team's
own color. Expected points added per play come from nflverse's weekly team stats.

```python
weeks = nfl.load_nfl_team_stats([NFL_SEASON]).filter(pl.col("season_type") == "REG")
plays = pl.col("attempts") + pl.col("sacks_suffered") + pl.col("carries")


def epa_per_play(by):
    return weeks.group_by(team=by, maintain_order=True).agg(
        epa=(pl.col("passing_epa") + pl.col("rushing_epa")).sum() / plays.sum()
    )


nfl_epa = (
    epa_per_play(pl.col("team"))
    .join(epa_per_play(pl.col("opponent_team")), on="team", suffix="_allowed")
    .with_columns(net=pl.col("epa") - pl.col("epa_allowed"))
    .sort("net", descending=True)
    .head(16)
)
red_green = ["#d7301f", "#ffffbf", "#1a9850"]
Reactable(
    nfl_epa,
    columns=[
        reactable_sdv_color_tiles(nfl_epa, team_col="team", league="nfl", id="team", name="Team", width=80),
        reactable_sdv_color_tiles(nfl_epa, colors=red_green, number_fmt="+.3f", id="epa", name="Offense"),
        reactable_sdv_color_tiles(
            nfl_epa, colors=red_green[::-1], number_fmt="+.3f", id="epa_allowed", name="Defense allowed"
        ),
        reactable_sdv_color_tiles(nfl_epa, colors=red_green, number_fmt="+.3f", bold_text=True, id="net", name="Net"),
    ],
    default_page_size=16,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-formatters/5_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 3. Color scales: the MLB standings

`reactable_sdv_color_scales` is the same scale without the tile: it styles the whole cell, so the table keeps its
grid. Run differential is colored on reactablefmtr's default ramp (blue at the bottom, orange at the top), and the
team column carries each club's primary color at 85% opacity, its text still readable. The standings are ESPN's for
the 2026 season.

```python
mlb_table = (
    mlb.espn_mlb_standings(season=SEASON)
    .with_columns(pl.col("wins", "losses", "point_differential").cast(pl.Int64))
    .sort(["win_percent", "team_abbreviation"], descending=[True, False])
    .select(team="team_abbreviation", name="team_display_name", w="wins", l="losses", diff="point_differential")
    .head(15)
)
Reactable(
    mlb_table,
    columns=[
        reactable_sdv_color_scales(mlb_table, team_col="team", league="mlb", opacity=0.85, id="team", name=""),
        Column(id="name", name="Team", min_width=180),
        Column(id="w", name="W"),
        Column(id="l", name="L"),
        reactable_sdv_color_scales(mlb_table, number_fmt="+d", id="diff", name="Run diff."),
    ],
    default_page_size=15,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-formatters/7_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 4. Pill buttons: the WNBA's leading scorers

`reactable_sdv_pill_buttons` sets each value in a rounded pill. Numbers ramp across `colors`; text takes the first
color, or, with `team_col`, the row's team color. Here the team abbreviation sits in a team-colored pill and points
per game ramp from gray to orange. Per-game averages come from ESPN player box scores of the 2026 regular season.

```python
schedule = wnba.load_wnba_schedule(seasons=[SEASON]).filter(
    (pl.col("season_type") == 2) & (pl.col("type_abbreviation") == "STD")
)
wnba_players = wnba.load_wnba_player_boxscore(seasons=[SEASON]).filter(
    pl.col("game_id").is_in(schedule["game_id"].implode()) & ~pl.col("did_not_play")
)
scorers = (
    wnba_players.sort("game_date")
    .group_by("athlete_id", "athlete_display_name", maintain_order=True)
    .agg(team=pl.col("team_abbreviation").last(), gp=pl.len(), ppg=pl.col("points").mean().round(1))
    .filter(pl.col("gp") >= 20)
    .sort(["ppg", "athlete_display_name"], descending=[True, False])
    .head(12)
)
Reactable(
    scorers,
    columns=[
        Column(id="athlete_id", show=False),
        Column(id="athlete_display_name", name="Player", min_width=180),
        reactable_sdv_pill_buttons(scorers, team_col="team", league="wnba", bold_text=True, id="team", name="Team"),
        Column(id="gp", name="GP"),
        reactable_sdv_pill_buttons(scorers, colors=["#d9d9d9", "#fa4d00"], number_fmt=".1f", id="ppg", name="PPG"),
    ],
    default_page_size=12,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-formatters/9_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 5. Icon sets: NHL goal differential

`reactable_sdv_icon_sets` cuts the column into as many quantile buckets as `icons` (and as `colors`) and puts the
bucket's icon beside each value. Three buckets of goal differential in the final 2025-26 NHL standings get a down
arrow, a dash and an up arrow. The icons are inline SVG: circle, square, diamond, triangles, arrows, chevrons, star,
check, x, flag, minus, plus, heart and person.

```python
nhl_table = (
    nhl.nhl_standings("2026-04-16")
    .select(
        team="team_abbrev_default",
        name="team_name_default",
        pts="points",
        gf="goal_for",
        ga="goal_against",
        diff="goal_differential",
    )
    .sort(["pts", "team"], descending=[True, False])
)
Reactable(
    nhl_table,
    columns=[
        reactable_sdv_logos(league="nhl", id="team", name="", height=24, width=60),
        Column(id="name", name="Team", min_width=170),
        Column(id="pts", name="PTS"),
        Column(id="gf", name="GF"),
        Column(id="ga", name="GA"),
        reactable_sdv_icon_sets(
            nhl_table,
            icons=("arrow-down", "minus", "arrow-up"),
            colors=("#c0392b", "#9e9e9e", "#1e8449"),
            number_fmt="+d",
            id="diff",
            name="Goal diff.",
        ),
    ],
    default_page_size=10,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-formatters/11_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 6. Icon assign: SEC wins, one dot a win

`reactable_sdv_icon_assign` repeats an icon up to the column's largest value and fills as many as the row's value:
here each SEC team's 2025 wins as filled circles out of the most any team won, with the number to the right. With
`buckets=` it instead fills the row's quantile bucket out of that many icons. Each row reads to a screen reader as an
image labelled, for example, "10 out of 13". Wins are counted from cfbfastR's schedule of completed games.

```python
games = cfb.load_cfb_schedule(NFL_SEASON).filter(pl.col("completed"))
results = pl.concat(
    [
        games.select(team_id="home_id", team="home_team", conference="home_conference", won="home_winner"),
        games.select(team_id="away_id", team="away_team", conference="away_conference", won="away_winner"),
    ],
    how="vertical_relaxed",
)
sec = (
    results.filter(pl.col("conference") == "SEC")
    .group_by("team_id", "team")
    .agg(wins=pl.col("won").sum(), games=pl.len())
    .sort(["wins", "team"], descending=[True, False])
    .with_columns(logo=pl.col("team_id"))
    .select("logo", "team", "wins", "games")
)
Reactable(
    sec,
    columns=[
        reactable_sdv_logos(league="cfb", id="logo", name="", id_system="espn", height=24, width=60),
        Column(id="team", name="Team", min_width=140),
        reactable_sdv_icon_assign(
            sec, icon_size=11, fill_color="#461d7c", show_values="right", id="wins", name="Wins", min_width=260
        ),
        Column(id="games", name="Games"),
    ],
    default_page_size=16,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-formatters/13_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 7. Icon trend: NFL win changes, 2024 to 2025

`reactable_sdv_icon_trend` marks each change with an up icon, a down icon or a dash, and colors the number to match
(reactablefmtr's `icon_trend_indicator`). `icons` picks the shape: arrow, chevron or triangle. Regular-season wins
come from nflverse's schedules of both seasons.

```python
nfl_games = nfl.load_nfl_schedule([NFL_SEASON - 1, NFL_SEASON]).filter(
    (pl.col("game_type") == "REG") & pl.col("result").is_not_null()
)
team_wins = (
    pl.concat(
        [
            nfl_games.select("season", team="home_team", win=pl.col("result") > 0),
            nfl_games.select("season", team="away_team", win=pl.col("result") < 0),
        ]
    )
    .group_by("team", "season")
    .agg(wins=pl.col("win").sum())
    .pivot("season", index="team", values="wins")
    .rename({str(NFL_SEASON - 1): "before", str(NFL_SEASON): "after"})
    .with_columns(change=pl.col("after") - pl.col("before"))
    .sort(["change", "team"], descending=[True, False])
)
Reactable(
    team_wins,
    columns=[
        reactable_sdv_logos(league="nfl", id="team", name="", include_name=True, height=24, min_width=100),
        Column(id="before", name=str(NFL_SEASON - 1)),
        Column(id="after", name=str(NFL_SEASON)),
        reactable_sdv_icon_trend(
            team_wins, icons="triangle", number_fmt="+d", show_zero_label=True, id="change", name="Change"
        ),
    ],
    default_page_size=12,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-formatters/15_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 8. Merge column with headshots: the WNBA scorers again

`reactable_sdv_merge_column` shows a second column's value beside or below each value, so each player's team sits
under her name in small gray text. With `mark="headshot"` (and `mark_col` naming the ESPN athlete id) the player's
photo leads the cell. The merged and id columns are hidden.

```python
scorers_named = scorers.join(sdvplot.teams("wnba").select(team="abbr", team_name="name"), on="team", how="left")
Reactable(
    scorers_named,
    columns=[
        reactable_sdv_merge_column(
            scorers_named,
            merged_name="team_name",
            merged_position="below",
            mark="headshot",
            mark_col="athlete_id",
            league="wnba",
            mark_height=40,
            id="athlete_display_name",
            name="Player",
            min_width=260,
        ),
        Column(id="athlete_id", show=False),
        Column(id="team", show=False),
        Column(id="team_name", show=False),
        Column(id="gp", name="GP"),
        Column(id="ppg", name="PPG"),
    ],
    default_page_size=12,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-formatters/17_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 9. Highlights: men's college basketball's best and worst units

`reactable_sdv_highlight` bolds a column's maximum (green), minimum (red) or both, optionally on a highlighter. Among
the top 20 men's college basketball teams of 2025-26 by adjusted efficiency margin it marks the best and worst
adjusted offense; for defense, where lower is better, a `(min, max)` pair swaps the colors.

```python
names = mbb.load_mbb_team_boxscore(seasons=[SEASON]).select("team_id", "team_location").unique("team_id")
mbb_ratings = mbb.load_mbb_ratings(SEASON).with_columns(pl.col("team_id").cast(pl.Int32))  # ids ship as text here
assert names.schema["team_id"] == mbb_ratings.schema["team_id"]
top20 = (
    mbb_ratings.sort("rank")
    .head(20)
    .join(names, on="team_id", how="left")
    .with_columns(pl.col("adj_em", "adj_o", "adj_d").round(1), logo=pl.col("team_id"))
    .select("rank", "logo", "team_location", "adj_em", "adj_o", "adj_d")
)
Reactable(
    top20,
    columns=[
        Column(id="rank", name="#", width=50),
        reactable_sdv_logos(league="mbb", id="logo", name="", id_system="espn", height=24, width=60),
        Column(id="team_location", name="Team", min_width=150),
        Column(id="adj_em", name="Adj. margin"),
        reactable_sdv_highlight(
            top20, which="min_max", highlighter=("#fde0dd", "#e5f5e0"), id="adj_o", name="Adj. offense"
        ),
        reactable_sdv_highlight(
            top20,
            which="min_max",
            font_color=("green", "red"),
            highlighter=("#e5f5e0", "#fde0dd"),
            id="adj_d",
            name="Adj. defense",
        ),
    ],
    default_page_size=20,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-formatters/19_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 10. Bubble grid: NHL goals for and against, in team colors

`reactable_sdv_bubble_grid` draws each value as a circle (or a square, `shape="squares"`) whose width is its share of
the column's largest, up to 100 pixels, colored on a ramp or, with `team_col`, in the team's color. The Atlantic
Division's goals for (primary colors) and against (secondary colors, as squares) make a grid to scan for the big and
small numbers.

```python
atlantic = (
    nhl.nhl_standings("2026-04-16")
    .filter(pl.col("division_name") == "Atlantic")
    .sort("division_sequence")
    .select(team="team_abbrev_default", gf="goal_for", ga="goal_against")
)
Reactable(
    atlantic,
    columns=[
        reactable_sdv_logos(league="nhl", id="team", name="", include_name=True, height=24, min_width=100),
        reactable_sdv_bubble_grid(atlantic, team_col="team", league="nhl", id="gf", name="Goals for", min_width=120),
        reactable_sdv_bubble_grid(
            atlantic,
            team_col="team",
            league="nhl",
            which="secondary",
            shape="squares",
            id="ga",
            name="Goals against",
            min_width=120,
        ),
    ],
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-formatters/21_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## Run it yourself

<a href="pathname:///notebooks/cookbooks/reactable-formatters.ipynb" download>Download the notebook</a> (outputs cleared) or [open it on GitHub](https://github.com/sportsdataverse/sdvplot/blob/main/examples/notebooks/cookbooks/reactable-formatters.ipynb).

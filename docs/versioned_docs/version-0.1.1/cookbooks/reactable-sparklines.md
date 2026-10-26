---
title: "reactable sparklines and gauges cookbook"
sidebar_label: "reactable sparklines and gauges"
sidebar_position: 14
description: "In-cell charts with reactable: NBA point-margin sparklines, WNBA scoring sparkbars, NFL weekly EPA bars above and below zero, and gauges for NBA win percentage and NHL save percentage."
---

# reactable sparklines and gauges

reactablefmtr draws small charts inside table cells: `react_sparkline`, `react_sparkbar` and `gauge_chart`.
`sdvplot.reactable` ports the three as `reactable_sdv_sparkline`, `reactable_sdv_sparkbar` and `reactable_sdv_gauge`.
Each cell is a small inline SVG, so the table needs no extra JavaScript, and each SVG is an image with an
`aria-label` that a screen reader reads out (the number of points, the low, the high and the last value). Hovering a
chart shows the same summary.

A sparkline or sparkbar column holds one list of numbers per row: a polars `List` column or a pandas column of lists
both pass through reactable-py unchanged. Give `team_col` and `league` and each row's chart takes that team's color.
The recipes below use real 2025-26 NBA, 2026 WNBA, 2025 NFL and 2025-26 NHL data loaded through sportsdataverse-py.

```python
import polars as pl
import sportsdataverse.nba as nba
import sportsdataverse.nfl as nfl
import sportsdataverse.nhl as nhl
import sportsdataverse.wnba as wnba
from reactable import Column, Reactable, embed_css

from sdvplot.reactable import (
    reactable_sdv_gauge,
    reactable_sdv_logos,
    reactable_sdv_sparkbar,
    reactable_sdv_sparkline,
)

SEASON = 2026  # the 2025-26 NBA and NHL seasons and the 2026 WNBA season
NFL_SEASON = 2025  # nflverse names a season by the year it starts
embed_css()
```

## 1. Sparklines: every NBA team's game-by-game point margin

One row per team, one list per row: the team's point margin in each of its 82 regular-season games, in date
order (`standard_games` drops the All-Star Game and the NBA Cup final, which ESPN files under the regular season).
`highlight_points` marks the season's worst and best nights, and `statline="mean"` draws a dashed line at the team's
average margin with its value in the right margin. The line takes each team's primary color from `team_col`.

```python
def standard_games(schedule):
    # the regular season's standard games: ESPN also files the All-Star Game and the in-season cup final there
    games = schedule.filter((pl.col("season_type") == 2) & (pl.col("type_abbreviation") == "STD"))
    return pl.col("game_id").is_in(games["game_id"].implode())


nba_games = nba.load_nba_team_boxscore(seasons=[SEASON]).filter(standard_games(nba.load_nba_schedule(seasons=[SEASON])))
nba_margins = (
    nba_games.sort("game_date")
    .group_by("team_abbreviation", maintain_order=True)
    .agg(
        gp=pl.len(),
        w=(pl.col("team_winner") == True).sum(),  # noqa: E712
        margin=pl.col("team_score") - pl.col("opponent_team_score"),
    )
    .with_columns(avg=pl.col("margin").list.mean().round(1), logo=pl.col("team_abbreviation"))
    .sort("avg", descending=True)
    .select("logo", "team_abbreviation", "w", "gp", "avg", "margin")
)
assert nba_margins.height == 30 and nba_margins["gp"].min() == nba_margins["gp"].max() == 82
Reactable(
    nba_margins,
    columns=[
        reactable_sdv_logos(league="nba", id="logo", name="", width=50, height=26),
        Column(id="team_abbreviation", show=False),
        Column(id="w", name="W", width=55),
        Column(id="gp", name="GP", width=55),
        Column(id="avg", name="Avg. margin", width=95),
        reactable_sdv_sparkline(
            nba_margins,
            id="margin",
            name="Margin, game by game",
            team_col="team_abbreviation",
            league="nba",
            highlight_points={"min": "#d7191c", "max": "#1a9641"},
            statline="mean",
            decimals=1,
            line_width=1,
            width=260,
            height=34,
            min_width=280,
        ),
    ],
    default_page_size=10,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-sparklines/3_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 2. Sparkbars: WNBA scoring over each team's last 12 games

`reactable_sdv_sparkbar` draws the same kind of list as bars. Here each bar is a team's points in one of its last
12 regular-season games; `highlight_bars` colors the best game gold, and `labels="last"` prints the most recent
score above its bar. Bars stand on zero, so a 70-point night is visibly shorter than a 100-point one.

```python
wnba_games = wnba.load_wnba_team_boxscore(seasons=[SEASON]).filter(
    standard_games(wnba.load_wnba_schedule(seasons=[SEASON]))
)
wnba_last = (
    wnba_games.sort("game_date")
    .group_by("team_abbreviation", maintain_order=True)
    .agg(pts=pl.col("team_score").tail(12), ppg=pl.col("team_score").mean().round(1))
    .with_columns(last12=pl.col("pts").list.mean().round(1), logo=pl.col("team_abbreviation"))
    .sort("last12", descending=True)
    .select("logo", "team_abbreviation", "ppg", "last12", "pts")
)
assert wnba_last.height == 15 and wnba_last["pts"].list.len().min() == 12
Reactable(
    wnba_last,
    columns=[
        reactable_sdv_logos(league="wnba", id="logo", name="", width=50, height=26),
        Column(id="team_abbreviation", show=False),
        Column(id="ppg", name="Season PPG", width=100),
        Column(id="last12", name="Last 12 PPG", width=100),
        reactable_sdv_sparkbar(
            wnba_last,
            id="pts",
            name="Points, last 12 games",
            team_col="team_abbreviation",
            league="wnba",
            highlight_bars={"max": "#f2b705"},
            labels="last",
            width=200,
            height=34,
            min_width=220,
        ),
    ],
    pagination=False,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-sparklines/5_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 3. Bars above and below zero: NFL offensive EPA per play, week by week

Expected points added per play goes below zero, and a sparkbar hangs those weeks under the zero line. nflverse's
weekly team stats give each team's passing and rushing EPA and its dropbacks and carries; the list holds one rate per
game the team played. `bandline="innerquartiles"` shades the middle half of each team's weeks, so a steady offense
shows a thin band and an erratic one a wide band.

```python
weeks = nfl.load_nfl_team_stats([NFL_SEASON]).filter(pl.col("season_type") == "REG")
plays = pl.col("attempts") + pl.col("sacks_suffered") + pl.col("carries")
epa = pl.col("passing_epa") + pl.col("rushing_epa")
nfl_weekly = (
    weeks.sort("week")
    .group_by("team", maintain_order=True)
    .agg(season_epa=(epa.sum() / plays.sum()).round(3), weekly=(epa / plays).round(3))
    .with_columns(logo=pl.col("team"))
    .sort("season_epa", descending=True)
    .select("logo", "team", "season_epa", "weekly")
)
assert nfl_weekly.height == 32 and nfl_weekly["weekly"].list.len().min() == 17
Reactable(
    nfl_weekly,
    columns=[
        reactable_sdv_logos(league="nfl", id="logo", name="", width=50, height=26),
        Column(id="team", show=False),
        Column(id="season_epa", name="EPA / play", width=95),
        reactable_sdv_sparkbar(
            nfl_weekly,
            id="weekly",
            name="EPA / play by week",
            team_col="team",
            league="nfl",
            bandline="innerquartiles",
            bandline_color="#888888",
            width=260,
            height=34,
            min_width=280,
        ),
    ],
    default_page_size=8,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-sparklines/7_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 4. Gauges: NBA win percentage

`reactable_sdv_gauge` turns one number per row into a half-circle gauge with the value inside. With `min_value` and
`max_value` the scale is fixed (a win percentage runs from 0 to 1); without them it runs from 0 to the column's
largest absolute value (a negative value fills the gauge by its size, as in reactablefmtr). `team_col` fills each gauge in the team's color, and `number_fmt` takes a function or a format spec.
The ten best regular-season records:

```python
nba_pct = (
    nba_margins.with_columns(pct=(pl.col("w") / pl.col("gp")).round(3))
    .sort("pct", descending=True)
    .select("logo", "team_abbreviation", "w", "gp", "pct")
    .head(10)
)
Reactable(
    nba_pct,
    columns=[
        reactable_sdv_logos(league="nba", id="logo", name="", width=50, height=26),
        Column(id="team_abbreviation", show=False),
        Column(id="w", name="W", width=60),
        Column(id="gp", name="GP", width=60),
        reactable_sdv_gauge(
            nba_pct,
            id="pct",
            name="Win %",
            team_col="team_abbreviation",
            league="nba",
            min_value=0,
            max_value=1,
            number_fmt="{:.0%}".format,
            show_min_max=True,
            size=2,
            align="center",
            min_width=130,
        ),
    ],
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-sparklines/9_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 5. Gauges on a narrow scale: NHL save percentage

Save percentage lives in a narrow band, so a gauge from 0 to 1 would look full for every team. Fixing the scale to
.880-.920 spreads the 32 teams out, and a two-color `fill_color` ramps from red (the column's lowest) to green (its
highest). NHL regular-season game ids carry `02` after the season's year. The goalie box score counts the shots each
goaltender faced, so a team's save percentage is its goalies' saves over the shots against them, summed over the
season. An empty-net goal is not a shot any goalie faced, and an own goal is not a shot at all: neither is in the
denominator, as in the NHL's own goaltending figures.

```python
nhl_goalies = nhl.load_nhl_goalie_box(seasons=[SEASON]).filter(
    pl.col("game_id").cast(pl.String).str.slice(4, 2) == "02"
)
nhl_sv = (
    nhl_goalies.group_by("team_abbrev")
    .agg(
        gp=pl.col("game_id").n_unique(),
        sv_pct=(pl.col("saves").sum() / pl.col("shots_against").sum()).round(3),
    )
    .with_columns(logo=pl.col("team_abbrev"))
    .sort("sv_pct", descending=True)
    .select("logo", "team_abbrev", "gp", "sv_pct")
)
assert nhl_sv.height == 32 and nhl_sv["gp"].min() == 82
Reactable(
    nhl_sv,
    columns=[
        reactable_sdv_logos(league="nhl", id="logo", name="", width=50, height=26),
        Column(id="team_abbrev", show=False),
        Column(id="gp", name="GP", width=60),
        reactable_sdv_gauge(
            nhl_sv,
            id="sv_pct",
            name="Save %",
            fill_color=["#d7191c", "#1a9641"],
            min_value=0.88,
            max_value=0.92,
            number_fmt=".3f",
            show_min_max=True,
            size=2,
            align="center",
            min_width=130,
        ),
    ],
    default_page_size=8,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-sparklines/11_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## Run it yourself

<a href="pathname:///notebooks/cookbooks/reactable-sparklines.ipynb" download>Download the notebook</a> (outputs cleared) or [open it on GitHub](https://github.com/sportsdataverse/sdvplot/blob/main/examples/notebooks/cookbooks/reactable-sparklines.ipynb).

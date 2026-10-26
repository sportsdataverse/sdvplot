---
title: "reactable themes and titles cookbook"
sidebar_label: "reactable themes and titles"
sidebar_position: 15
description: "reactablefmtr's table furniture and themes in reactable-py: a title, subtitle, source line, legend and Google font around a table; ESPN, New York Times, FiveThirtyEight and PFF looks on NHL, WNBA, men's college basketball and NFL data; the other 23 themes side by side; and themes in the Chiefs' and Packers' colors."
---

# reactable themes and titles

reactablefmtr dresses an R reactable with a title, subtitle, source line, legend and Google font, and ships 27 table
themes, from ESPN's and The New York Times' to Bootswatch's. `sdvplot.reactable` ports both to reactable-py:
`reactable_sdv_frame` wraps a `Reactable` in that furniture (with `reactable_sdv_legend` or
`reactable_sdv_icon_legend` for the legend), `reactable_sdv_theme(name)` returns any of the 27 themes as a
`reactable.Theme` with reactablefmtr's own colors, fonts, borders and paddings, and `reactable_sdv_theme_team` builds a
theme from a team's colors. The data is the 2025 NFL season, the 2025-26 NHL and men's college basketball seasons and
the 2026 WNBA season, all loaded through sportsdataverse-py.

```python
import polars as pl
import sportsdataverse.mbb as mbb
import sportsdataverse.nfl as nfl
import sportsdataverse.nhl as nhl
import sportsdataverse.wnba as wnba
from htmltools import tags
from matplotlib.colors import LinearSegmentedColormap, to_hex
from reactable import Column, Reactable, embed_css
from reactable.tags import to_widget

from sdvplot.reactable import (
    reactable_sdv_frame,
    reactable_sdv_icon_legend,
    reactable_sdv_legend,
    reactable_sdv_logos,
    reactable_sdv_theme,
    reactable_sdv_theme_team,
)

NFL_SEASON = 2025  # nflverse names a season by the year it starts
SEASON = 2026  # the 2026 WNBA season and the 2025-26 NHL and men's college basketball seasons
SOURCE = "Data: sportsdataverse-py"
embed_css()

weeks = nfl.load_nfl_team_stats([NFL_SEASON]).filter(pl.col("season_type") == "REG")
dropbacks = pl.col("attempts") + pl.col("sacks_suffered")
nfl_epa = (
    weeks.group_by("team")
    .agg(
        epa=(pl.col("passing_epa") + pl.col("rushing_epa")).sum() / (dropbacks + pl.col("carries")).sum(),
        pass_epa=pl.col("passing_epa").sum() / dropbacks.sum(),
        rush_epa=pl.col("rushing_epa").sum() / pl.col("carries").sum(),
    )
    .with_columns(pl.selectors.float().round(3), logo=pl.col("team"))
    .sort("epa", descending=True)
    .select("logo", "team", "epa", "pass_epa", "rush_epa")
)
nfl_epa.head(3)
```

<div class="sdv-output">

| logo | team | epa   | pass_epa | rush_epa |
|------|------|-------|----------|----------|
| NE   | NE   | 0.143 | 0.298    | -0.029   |
| LA   | LA   | 0.135 | 0.242    | -0.009   |
| BUF  | BUF  | 0.128 | 0.181    | 0.075    |

</div>

## 1. Title, subtitle, source, legend and font

`reactable_sdv_frame` puts a title and subtitle over the table and a legend and source line under it, with
reactablefmtr's sizes (a 32 px title, a 24 px subtitle, a 16 px source). `font` names a Google font, loaded when the
page shows, for the whole frame, table included. The legend here is the one the cells are colored with: the EPA
cells sit on a three-color ramp over the column's range, and `reactable_sdv_legend(bins=5)` spreads the same three
colors over five swatches labelled with the values they stand for. The result displays like any `Reactable`.

```python
RAMP = ["#d7191c", "#ffffbf", "#1a9641"]
cmap = LinearSegmentedColormap.from_list("epa", RAMP)
lo, hi = nfl_epa["epa"].min(), nfl_epa["epa"].max()


def epa_fill(info):
    return {"background-color": to_hex(cmap((info.value - lo) / (hi - lo)))}


table = Reactable(
    nfl_epa,
    columns=[
        reactable_sdv_logos(league="nfl", id="logo", name="", width=50, height=26),
        Column(id="team", name="Team"),
        Column(id="epa", name="EPA/play", style=epa_fill),
        Column(id="pass_epa", name="Pass EPA"),
        Column(id="rush_epa", name="Rush EPA"),
    ],
    default_page_size=10,
    compact=True,
)
steps = [lo + i * (hi - lo) / 4 for i in range(5)]
reactable_sdv_frame(
    table,
    title="Who moved the ball in 2025",
    subtitle="Expected points added per play, NFL regular season",
    source=SOURCE,
    legend=reactable_sdv_legend(colors=RAMP, bins=5, labels=[f"{v:+.2f}" for v in steps], title="EPA/play"),
    font="Roboto Condensed",
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-themes/3_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

`reactable_sdv_icon_legend` explains icons rather than colors. Its shapes are inline SVG (no icon font to load), so a
cell can draw the same shape with the same color. Here a filled circle marks the teams with a winning record and EPA
above zero:

```python
games = nfl.load_nfl_schedule([NFL_SEASON]).filter(pl.col("game_type") == "REG")
sides = [("home_team", "home_score", "away_score"), ("away_team", "away_score", "home_score")]
records = (
    pl.concat(games.select(team=pl.col(t), win=(pl.col(us) > pl.col(them)).cast(pl.Int32)) for t, us, them in sides)
    .group_by("team")
    .agg(w=pl.col("win").sum(), gp=pl.len())
)
both = (
    nfl_epa.join(records, on="team")
    .with_columns(good=(pl.col("w") * 2 > pl.col("gp")) & (pl.col("epa") > 0))
    .sort("w", descending=True)
)


def dot(color):
    return f'<svg viewBox="0 0 16 16" width="12" height="12"><circle cx="8" cy="8" r="7" fill="{color}"/></svg>'


reactable_sdv_frame(
    Reactable(
        both.select("logo", "team", "w", "epa", "good"),
        columns=[
            reactable_sdv_logos(league="nfl", id="logo", name="", width=50, height=26),
            Column(id="team", name="Team"),
            Column(id="w", name="Wins"),
            Column(id="epa", name="EPA/play"),
            Column(id="good", name="", html=True, cell=lambda info: dot("#1a9641" if info.value else "#d9d9d9")),
        ],
        default_page_size=8,
        compact=True,
    ),
    title="Winning and efficient",
    source=SOURCE,
    legend=reactable_sdv_icon_legend(
        icons="circle", colors=["#1a9641", "#d9d9d9"], labels=["winning record and positive EPA", "the rest"]
    ),
    align="left",
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-themes/5_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 2. The sports-media themes

Four of reactablefmtr's themes copy a newsroom's tables: `espn`, `nytimes`, `fivethirtyeight` and `pff`. Each is a
`reactable.Theme` built from reactablefmtr's own values (its `espn()` gives a 12 px gray body, 11 px uppercase headers
between light rules and 7 px of padding, for one), so pass it to `Reactable(theme=...)`; every argument the R function takes, such
as `font_size` or `header_font_color`, can be overridden. First ESPN's look on the NHL's final 2025-26 standings:

```python
nhl_table = (
    nhl.nhl_standings("2026-04-16")
    .select(team="team_abbrev_default", gp="games_played", w="wins", l="losses", otl="ot_losses", pts="points")
    .with_columns(logo=pl.col("team"))
    .sort("pts", descending=True)
    .head(10)
    .select("logo", "team", "gp", "w", "l", "otl", "pts")
)
reactable_sdv_frame(
    Reactable(
        nhl_table,
        columns=[
            reactable_sdv_logos(league="nhl", id="logo", name="", width=46, height=24),
            Column(id="team", name="TEAM"),
            Column(id="gp", name="GP"),
            Column(id="w", name="W"),
            Column(id="l", name="L"),
            Column(id="otl", name="OTL"),
            Column(id="pts", name="PTS"),
        ],
        theme=reactable_sdv_theme("espn"),
    ),
    subtitle="NHL standings, 2025-26: the top ten",
    source=SOURCE,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-themes/7_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

`nytimes` on the WNBA's 2026 scoring leaders (20 or more games), its 13 px body and gray 11 px headers between thin
rules:

```python
schedule = wnba.load_wnba_schedule(seasons=[SEASON]).filter(
    (pl.col("season_type") == 2) & (pl.col("type_abbreviation") == "STD")
)
players = wnba.load_wnba_player_boxscore(seasons=[SEASON]).filter(
    pl.col("game_id").is_in(schedule["game_id"].implode()) & ~pl.col("did_not_play")
)
scorers = (
    players.group_by("athlete_display_name")
    .agg(team=pl.col("team_abbreviation").last(), gp=pl.len(), ppg=pl.col("points").mean().round(1))
    .filter(pl.col("gp") >= 20)
    .sort("ppg", descending=True)
    .head(10)
)
reactable_sdv_frame(
    Reactable(
        scorers,
        columns=[
            Column(id="athlete_display_name", name="Player", min_width=170),
            Column(id="team", name="Team"),
            Column(id="gp", name="Games"),
            Column(id="ppg", name="Points per game"),
        ],
        theme=reactable_sdv_theme("nytimes"),
    ),
    title="The WNBA's top scorers",
    source=SOURCE,
    font="Libre Franklin",
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-themes/9_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

`fivethirtyeight` on the top 15 of men's college basketball's 2025-26 adjusted efficiency ratings, and `pff` (its
slate-gray header bar) on the NFL's best passing offenses:

```python
names = mbb.load_mbb_team_boxscore(seasons=[SEASON]).select("team_id", "team_location").unique("team_id")
mbb_ratings = mbb.load_mbb_ratings(SEASON).with_columns(pl.col("team_id").cast(pl.Int32))  # ids ship as text here
assert names.schema["team_id"] == mbb_ratings.schema["team_id"]
top15 = (
    mbb_ratings.sort("rank")
    .head(15)
    .join(names, on="team_id", how="left")
    .with_columns(pl.col("adj_em", "adj_o", "adj_d").round(1))
    .select("rank", "team_location", "adj_em", "adj_o", "adj_d")
)
reactable_sdv_frame(
    Reactable(
        top15,
        columns=[
            Column(id="rank", name="RANK", width=60),
            Column(id="team_location", name="TEAM", min_width=150),
            Column(id="adj_em", name="ADJ. MARGIN"),
            Column(id="adj_o", name="ADJ. OFFENSE"),
            Column(id="adj_d", name="ADJ. DEFENSE"),
        ],
        theme=reactable_sdv_theme("fivethirtyeight"),
        default_page_size=15,
    ),
    title="College basketball's best, by adjusted margin",
    source=SOURCE,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-themes/11_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

```python
passing = nfl_epa.sort("pass_epa", descending=True).head(10)
Reactable(
    passing,
    columns=[
        reactable_sdv_logos(league="nfl", id="logo", name="", width=50, height=26),
        Column(id="team", name="TEAM"),
        Column(id="pass_epa", name="PASS EPA"),
        Column(id="rush_epa", name="RUSH EPA"),
        Column(id="epa", name="EPA"),
    ],
    theme=reactable_sdv_theme("pff", centered=True),
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-themes/12_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 3. The other 23 themes

The rest, each on the same five rows (the NFL's top offenses by EPA per play), titled with its name. A
`reactable_sdv_frame` is htmltools markup, so several fit in one grid: `reactable.tags.to_widget` shows the grid as one
widget. The dark themes (`cyborg`, `dark`, `darkly`, `hoverlight`, `midnight`, `midnightblue`, `slate`, `superhero`)
bring their own background; `hoverdark` and `hoverlight` restyle a row as the pointer passes over it.

```python
others = ["cerulean", "clean", "cosmo", "cyborg", "dark", "darkly", "default", "flatly", "hoverdark", "hoverlight",
          "journal", "lux", "midnight", "midnightblue", "minty", "no_lines", "sandstone", "sanfran", "slate",
          "spacelab", "sunrise", "superhero", "void"]  # fmt: skip
top5 = nfl_epa.head(5).select("team", "epa", "pass_epa", "rush_epa")
cards = [
    tags.div(
        reactable_sdv_frame(
            Reactable(top5, theme=reactable_sdv_theme(name, font_size=13, header_font_size=13), compact=True),
            subtitle=name,
        ),
        style="min-width:0",
    )
    for name in others
]
to_widget(tags.div(*cards, style="display:grid;grid-template-columns:repeat(auto-fill, minmax(300px, 1fr));gap:16px"))
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-themes/14_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 4. A team's own theme

`reactable_sdv_theme_team(team, league)` fills the header with the team's primary color over a rule in its
secondary, tints the stripes and hover with the primary, and picks black or white for every text by contrast, so the
same call works for a light primary and a dark one. The Chiefs' and the Packers' 2025 regular seasons, game by game:

```python
def game_log(team):
    home = games.filter(pl.col("home_team") == team).select(
        "week", opp="away_team", pf="home_score", pa="away_score", at=pl.lit("vs")
    )
    away = games.filter(pl.col("away_team") == team).select(
        "week", opp="home_team", pf="away_score", pa="home_score", at=pl.lit("@")
    )
    return (
        pl.concat([home, away])
        .sort("week")
        .with_columns(result=pl.when(pl.col("pf") > pl.col("pa")).then(pl.lit("W")).otherwise(pl.lit("L")))
        .select("week", "at", "opp", "result", "pf", "pa")
    )


def team_table(team, name):
    return reactable_sdv_frame(
        Reactable(
            game_log(team),
            columns=[
                Column(id="week", name="Week", width=70),
                Column(id="at", name="", width=40),
                reactable_sdv_logos(league="nfl", id="opp", name="Opponent", include_name=True, height=22),
                Column(id="result", name=""),
                Column(id="pf", name="PF"),
                Column(id="pa", name="PA"),
            ],
            theme=reactable_sdv_theme_team(team, "nfl", centered=True),
            striped=True,
            highlight=True,
            default_page_size=17,
            compact=True,
        ),
        subtitle=f"{name}, 2025",
        source=SOURCE,
    )


team_table("KC", "Kansas City Chiefs")
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-themes/16_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

```python
team_table("GB", "Green Bay Packers")
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable-themes/17_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## Run it yourself

<a href="pathname:///notebooks/cookbooks/reactable-themes.ipynb" download>Download the notebook</a> (outputs cleared) or [open it on GitHub](https://github.com/sportsdataverse/sdvplot/blob/main/examples/notebooks/cookbooks/reactable-themes.ipynb).

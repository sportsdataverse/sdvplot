---
title: "reactable cookbook"
sidebar_label: "reactable"
sidebar_position: 7
description: "Six reactable recipes with sdvplot: WNBA headshots, NFL wordmarks with column groups and heat cells, NHL standings grouped by division, logos in the headers of an NFC North matrix, expandable SEC game details, and a dark theme with dark logos."
---

# reactable

[reactable-py](https://machow.github.io/reactable-py/) is the Python port of R's reactable: an interactive HTML
table with sorting, searching, paging, grouped rows with aggregates, expandable row details, column groups and
themes. `sdvplot.reactable` adds the SportsDataverse marks to it as ordinary `reactable.Column` objects: team logos
and wordmarks, player headshots, logos in column headers, and cells tinted or barred in each row's team color.
These six recipes build on the [Tables](tables.md) cookbook's single example (logos and team-color bars on NBA
wins) with the parts it does not show, across the WNBA, NFL, NHL, college football and men's college basketball,
all loaded through sportsdataverse-py.

```python
import warnings

import polars as pl
import sportsdataverse.cfb as cfb
import sportsdataverse.mbb as mbb
import sportsdataverse.nfl as nfl
import sportsdataverse.nhl as nhl
import sportsdataverse.wnba as wnba
from matplotlib import colormaps
from reactable import ColGroup, Column, Reactable, Theme, embed_css

import sdvplot
from sdvplot.reactable import (
    reactable_sdv_cols_label,
    reactable_sdv_headshots,
    reactable_sdv_logos,
    reactable_sdv_team_color_bg,
    reactable_sdv_wordmarks,
)

NFL_SEASON = 2025  # nflverse and cfbfastR name a season by the year it starts
SEASON = 2026  # the 2026 WNBA season and the 2025-26 NHL and men's college basketball seasons
embed_css()


def heat(frame, column, cmap="RdYlGn", reverse=False, alpha=0.55):
    """A reactable ``style`` function: each cell's background on a color scale over the column's range."""
    lo, hi = frame[column].min(), frame[column].max()
    scale = colormaps[cmap].reversed() if reverse else colormaps[cmap]

    def style(info):
        r, g, b, _ = scale((info.value - lo) / (hi - lo))
        return {"background-color": f"rgba({r * 255:.0f}, {g * 255:.0f}, {b * 255:.0f}, {alpha})"}

    return style
```

## 1. Headshots: the WNBA's leading scorers

`reactable_sdv_headshots` turns a column of ESPN athlete ids into player photos, and `reactable_sdv_team_color_bg`
fills another column with each row's team color at low opacity, so the player's name sits on a tint of the team
they finished the season with. Both read the team from a column of the same frame: here `team`, which the table
hides once it has done that job. The 2026 regular season, 20 or more games:

```python
players = wnba.load_wnba_player_boxscore(seasons=[SEASON]).filter(
    (pl.col("season_type") == 2) & ~pl.col("did_not_play")
)
leaders = (
    players.sort("game_date")
    .group_by("athlete_id", "athlete_display_name", maintain_order=True)
    .agg(
        team=pl.col("team_abbreviation").last(),
        gp=pl.len(),
        ppg=pl.col("points").mean().round(1),
        rpg=pl.col("rebounds").mean().round(1),
        apg=pl.col("assists").mean().round(1),
    )
    .filter(pl.col("gp") >= 20)
    .sort("ppg", descending=True)
    .head(15)
    .with_columns(photo=pl.col("athlete_id"), logo=pl.col("team"))
    .select("photo", "athlete_display_name", "logo", "team", "gp", "ppg", "rpg", "apg")
)
Reactable(
    leaders,
    columns=[
        reactable_sdv_headshots(league="wnba", id="photo", name="", width=70, height=44),
        reactable_sdv_team_color_bg(
            leaders, "team", league="wnba", alpha=0.3, id="athlete_display_name", name="Player", min_width=190
        ),
        reactable_sdv_logos(league="wnba", id="logo", name="", width=50, height=26),
        Column(id="team", show=False),
        Column(id="gp", name="GP"),
        Column(id="ppg", name="PTS"),
        Column(id="rpg", name="REB"),
        Column(id="apg", name="AST"),
    ],
    default_page_size=15,
    default_col_def=Column(v_align="center"),
    highlight=True,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable/3_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 2. Wordmarks, column groups and heat cells: NFL EPA

`reactable_sdv_wordmarks` shows each team as its wordmark instead of its logo; NFL teams have one for every club.
Here it heads an offense-versus-defense table built from nflverse's weekly team stats: expected points added per
dropback and per carry, for each team's offense and for what its defense allowed. `ColGroup` puts a spanning
header over each side, and a small `heat` style function (defined above) colors every cell on the column's range:
green is good, so the defensive columns use the reversed scale. Click any header to re-sort.

```python
weeks = nfl.load_nfl_team_stats([NFL_SEASON]).filter(pl.col("season_type") == "REG")
dropbacks = pl.col("attempts") + pl.col("sacks_suffered")


def epa_rates(by):
    return weeks.group_by(team=by, maintain_order=True).agg(
        epa=(pl.col("passing_epa") + pl.col("rushing_epa")).sum() / (dropbacks + pl.col("carries")).sum(),
        pass_epa=pl.col("passing_epa").sum() / dropbacks.sum(),
        rush_epa=pl.col("rushing_epa").sum() / pl.col("carries").sum(),
    )


nfl_epa = (
    epa_rates(pl.col("team"))
    .join(epa_rates(pl.col("opponent_team")), on="team", suffix="_allowed")
    .with_columns(pl.selectors.float().round(3), mark=pl.col("team"))
    .sort("epa", descending=True)
    .select("mark", "team", "epa", "pass_epa", "rush_epa", "epa_allowed", "pass_epa_allowed", "rush_epa_allowed")
)
offense = ["epa", "pass_epa", "rush_epa"]
defense = [f"{c}_allowed" for c in offense]
labels = {"epa": "Per play", "pass_epa": "Per dropback", "rush_epa": "Per carry"}
Reactable(
    nfl_epa,
    columns=[
        reactable_sdv_wordmarks(league="nfl", id="mark", name="", height=22, width=150),
        Column(id="team", show=False),
        *[Column(id=c, name=labels[c], style=heat(nfl_epa, c), align="center") for c in offense],
        *[
            Column(id=c, name=labels[c.removesuffix("_allowed")], style=heat(nfl_epa, c, reverse=True), align="center")
            for c in defense
        ],
    ],
    column_groups=[
        ColGroup(name="Offense: EPA", columns=offense),
        ColGroup(name="Defense: EPA allowed", columns=defense),
    ],
    default_page_size=12,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable/5_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 3. Grouped rows with aggregates: NHL standings by division

reactable groups rows with `group_by` and fills each group's header row with the column's `aggregate`. With
`reactable_sdv_logos(include_name=True)` the team column keeps its abbreviation after the logo, so the four
division groups of the NHL's final 2025-26 standings read as one table: each group row sums its teams' wins,
losses, points and goal differential. Collapse a division by clicking its row.

```python
nhl_table = (
    nhl.nhl_standings("2026-04-16")
    .select(
        division="division_name",
        team="team_abbrev_default",
        gp="games_played",
        w="wins",
        l="losses",
        otl="ot_losses",
        pts="points",
        gd="goal_differential",
    )
    .sort(["division", "pts", "team"], descending=[False, True, False])
)
Reactable(
    nhl_table,
    group_by="division",
    columns=[
        Column(id="division", name="Division", min_width=150),
        reactable_sdv_logos(league="nhl", id="team", name="Team", include_name=True, height=24, min_width=110),
        Column(id="gp", name="GP", aggregate="sum"),
        Column(id="w", name="W", aggregate="sum"),
        Column(id="l", name="L", aggregate="sum"),
        Column(id="otl", name="OTL", aggregate="sum"),
        Column(id="pts", name="PTS", aggregate="sum"),
        Column(id="gd", name="Goal diff.", aggregate="sum"),
    ],
    default_expanded=True,
    pagination=False,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable/7_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 4. Logos in the column headers: an NFC North head-to-head

`reactable_sdv_cols_label` makes one column per team-named column of a frame, its header the team's logo. That fits
a matrix: one row and one column per team, each cell the row team's combined point margin over its two games
against the column team in the 2025 regular season. Pass it only the team-named columns; the extra keyword
arguments (a margin color and an empty-cell text) go to every column it makes.

```python
division = ["CHI", "DET", "GB", "MIN"]
games = nfl.load_nfl_schedule([NFL_SEASON]).filter(
    (pl.col("game_type") == "REG") & pl.col("home_team").is_in(division) & pl.col("away_team").is_in(division)
)
sides = [("home_team", "away_team", "home_score", "away_score"), ("away_team", "home_team", "away_score", "home_score")]
margins = pl.concat(games.select(team=pl.col(t), opp=pl.col(o), margin=pl.col(a) - pl.col(b)) for t, o, a, b in sides)
matrix = (
    margins.group_by("team", "opp")
    .agg(pl.col("margin").sum())
    .pivot(on="opp", index="team", values="margin")
    .select("team", *division)
    .sort("team")
)


def margin_color(info):
    if info.value is None:
        return {"background-color": "#f2f2f2"}
    return {"color": "#1a7f37" if info.value > 0 else "#c0392b", "font-weight": "600"}


Reactable(
    matrix,
    columns=[
        reactable_sdv_logos(league="nfl", id="team", name="", height=34, width=80),
        *reactable_sdv_cols_label(
            matrix.select(division),
            league="nfl",
            height=34,
            style=margin_color,
            align="center",
            v_align="center",
            na="",
            width=90,
        ),
    ],
    bordered=True,
    sortable=False,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable/9_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 5. Expandable row details: the SEC's games

A `details` column renders extra content under a row when you expand it. Each row here is an SEC team in
cfbfastR's 2025 adjusted ratings (net adjusted EPA per play, with its national rank), logo first; expanding it
lists the team's completed games, each opponent drawn by its logo from `sdvplot.logo_url`. The detail function runs
once per row when the table is built, so the page needs no Python to open a row.

```python
ratings = cfb.load_cfb_ratings(NFL_SEASON).select("team_id", "net_rank", "adj_off_epa", "adj_def_epa", "adj_net")
sec_teams = cfb.load_cfb_team_summaries(NFL_SEASON).filter(pl.col("conference") == "SEC").select("team_id", "pos_team")
assert sec_teams.schema["team_id"] == ratings.schema["team_id"]
sec = (
    sec_teams.join(ratings, on="team_id")
    .with_columns(pl.selectors.float().round(3), logo=pl.col("team_id"))
    .sort("adj_net", descending=True)
    .select("logo", "pos_team", "net_rank", "adj_off_epa", "adj_def_epa", "adj_net", "team_id")
)
schedule = cfb.load_cfb_schedule(NFL_SEASON).filter(pl.col("completed"))
results = pl.concat(
    schedule.select(
        "week",
        team_id=pl.col(f"{us}_id"),
        opp_id=pl.col(f"{them}_id"),
        opp=pl.col(f"{them}_team"),
        pts=pl.col(f"{us}_points"),
        opp_pts=pl.col(f"{them}_points"),
    )
    for us, them in [("home", "away"), ("away", "home")]
).sort("team_id", "week")
by_team = results.partition_by("team_id", as_dict=True)


def game_html(game):
    with warnings.catch_warnings():  # an opponent without a logo keeps its name instead
        warnings.simplefilter("ignore", sdvplot.SdvplotWarning)
        url = sdvplot.logo_url(game["opp_id"], "cfb", id_system="espn")
    mark = f'<img src="{url}" alt="{game["opp"]}" height="24">' if url else game["opp"]
    won = game["pts"] > game["opp_pts"]
    return (
        f'<span style="display:inline-flex;align-items:center;gap:4px;margin:4px 12px 4px 0">{mark}'
        f'<b style="color:{"#1a7f37" if won else "#c0392b"}">{"W" if won else "L"}</b>'
        f" {game['pts']}-{game['opp_pts']}</span>"
    )


def details(row):
    team_id = sec["team_id"][row.row_index]
    return "".join(game_html(g) for g in by_team[(team_id,)].iter_rows(named=True))


Reactable(
    sec,
    columns=[
        reactable_sdv_logos(league="cfb", id="logo", name="", id_system="espn", height=28, width=60),
        Column(id="pos_team", name="Team", min_width=140),
        Column(id="net_rank", name="Natl. rank"),
        Column(id="adj_off_epa", name="Off. EPA/play"),
        Column(id="adj_def_epa", name="Def. EPA/play"),
        Column(id="adj_net", name="Net"),
        Column(id="team_id", show=False),
    ],
    details=Column(details=details, html=True),
    default_page_size=16,
    highlight=True,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable/11_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## 6. A dark theme with the dark logo variant: men's college basketball

reactable's `Theme` restyles the whole table, and `reactable_sdv_logos(variant="dark")` swaps in the logo variant
drawn for dark backgrounds, so the marks stay readable on it. The table is the top 25 of the 2025-26 adjusted
efficiency ratings from hoopR's men's college basketball data: adjusted offense and defense (points per 100
possessions) carry heat cells, with the defensive scale reversed because fewer points allowed is better.

```python
names = mbb.load_mbb_team_boxscore(seasons=[SEASON]).select("team_id", "team_location").unique("team_id")
mbb_ratings = mbb.load_mbb_ratings(SEASON).with_columns(pl.col("team_id").cast(pl.Int32))  # ids ship as text here
assert names.schema["team_id"] == mbb_ratings.schema["team_id"]
top25 = (
    mbb_ratings.sort("rank")
    .head(25)
    .join(names, on="team_id", how="left")
    .with_columns(pl.col("adj_em", "adj_o", "adj_d", "adj_tempo").round(1), logo=pl.col("team_id"))
    .select("rank", "logo", "team_location", "adj_em", "adj_o", "adj_d", "adj_tempo")
)
dark = Theme(
    color="#e8e8e8",
    background_color="#14161a",
    border_color="#2c3038",
    striped_color="#1b1e23",
    highlight_color="#262a31",
    header_style={"color": "#a8adb7", "text-transform": "uppercase", "font-size": "0.8rem"},
    page_button_style={"color": "#e8e8e8"},
)
Reactable(
    top25,
    columns=[
        Column(id="rank", name="#", width=50),
        reactable_sdv_logos(league="mbb", id="logo", name="", variant="dark", id_system="espn", height=28, width=60),
        Column(id="team_location", name="Team", min_width=150),
        Column(id="adj_em", name="Adj. margin"),
        Column(id="adj_o", name="Adj. offense", style=heat(top25, "adj_o", alpha=0.45)),
        Column(id="adj_d", name="Adj. defense", style=heat(top25, "adj_d", reverse=True, alpha=0.45)),
        Column(id="adj_tempo", name="Tempo"),
    ],
    theme=dark,
    striped=True,
    default_page_size=25,
    compact=True,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/reactable/13_0.html" title="Interactive widget" height="480" loading="lazy"></iframe>

</div>

## Run it yourself

<a href="pathname:///notebooks/cookbooks/reactable.ipynb" download>Download the notebook</a> (outputs cleared) or [open it on GitHub](https://github.com/sportsdataverse/sdvplot/blob/main/examples/notebooks/cookbooks/reactable.ipynb).

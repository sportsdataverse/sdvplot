---
title: "pydeck cookbook"
sidebar_label: "pydeck"
sidebar_position: 16
description: "Seven pydeck recipes: shots as logos on an NHL rink, shots as arcs to the goal, a team's passes flat on the pitch, both finalists readable on the grass, upright arcs in 3D, logos on a map, and a box lacrosse rink."
---

# pydeck

[pydeck](https://deckgl.readthedocs.io/) draws [deck.gl](https://deck.gl/) layers from Python: WebGL maps and
charts that pan, zoom and tilt in the browser. `sdvplot.pydeck` builds three kinds of layer: team logos at points
(`logo_icon_layer`), arcs in team colors (`pass_arc_layer`), and a sportypy rink, pitch, court or field in its own
coordinates (`surface_layer`). Each returns `pydeck.Layer`'s keyword arguments as a plain dict, and `deck()` puts
them in a `pydeck.Deck` with its view fitted. The module needs pydeck: `pip install "sdvplot[pydeck]"`.
sdvplot-js builds the same layers for deck.gl in JavaScript, and the two are tested against one shared fixture.

Every point here comes from a data source, never typed in: game 7 of the 2024 Stanley Cup Final from NHL api-web
through sportsdataverse-py, the 2018 World Cup final from StatsBomb's open data, and MLB's ballparks from the MLB
Stats API through sportsdataverse-py. Drag to pan, scroll to zoom, and hover a mark for its team.

```python
import polars as pl
import pydeck as pdk
import requests
import sportsdataverse.mlb as mlb
import sportsdataverse.nhl as nhl

import sdvplot
import sdvplot.pydeck as sdeck

GAME = 2023030417  # game 7 of the 2024 Stanley Cup Final, Edmonton at Florida
WORLD_CUP_FINAL = 8658  # StatsBomb's match id: France 4-2 Croatia, 2018-07-15
ESPN_TEAM = {"France": "478", "Croatia": "477"}  # ESPN's soccer ids for the men's teams (2755 and 18889: the women's)
MLB_SEASON = 2026
```

NHL api-web's play-by-play gives each shot in feet from centre ice, the frame sportypy draws its rink in, so
the shots need no conversion. Its team ids are the NHL's own; the game's `homeTeam` and `awayTeam` name them.
StatsBomb's events are in its 120 x 80 frame, which `sdvplot.pitch_coords` converts to sportypy's 105 x 68 m pitch
(origin at the centre spot), flipping Croatia so the two teams attack opposite ends. StatsBomb open data is free for
non-commercial use; credit it as below.

```python
raw = nhl.nhl_web_pbp(GAME, return_parsed=False)
nhl_team = {t["id"]: t["abbrev"] for t in (raw["homeTeam"], raw["awayTeam"])}
shots = (
    nhl.parse_nhl_web_pbp(raw)
    .filter(
        pl.col("period_descriptor_number") == 1,
        pl.col("type_desc_key").is_in(["goal", "shot-on-goal", "missed-shot"]),
    )
    .select(
        team=pl.col("details_event_owner_team_id").cast(pl.Int64).replace_strict(nhl_team),
        type=pl.col("type_desc_key"),
        time=pl.col("time_in_period"),
        x=pl.col("details_x_coord"),
        y=pl.col("details_y_coord"),
    )
    # the goal each shot was aimed at: the goal line is 89 ft from centre, at the end the shot came from
    .with_columns(net_x=pl.col("x").sign() * 89, net_y=pl.lit(0.0))
)

events = requests.get(
    f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{WORLD_CUP_FINAL}.json", timeout=60
).json()
completed = [e for e in events if e["type"]["name"] == "Pass" and "outcome" not in e["pass"]]
passes = pl.DataFrame(
    {
        "team": [ESPN_TEAM[e["team"]["name"]] for e in completed],
        "half": [e["period"] for e in completed],
        "x": [e["location"][0] for e in completed],
        "y": [e["location"][1] for e in completed],
        "end_x": [e["pass"]["end_location"][0] for e in completed],
        "end_y": [e["pass"]["end_location"][1] for e in completed],
    }
).with_columns(croatia=pl.col("team") == ESPN_TEAM["Croatia"])
start = sdvplot.pitch_coords(passes, provider="statsbomb", flip="croatia")
end = sdvplot.pitch_coords(passes, provider="statsbomb", x="end_x", y="end_y", flip="croatia")
passes = start.with_columns(to_x=end["pitch_x"], to_y=end["pitch_y"])

teams = mlb.mlb_teams(season=MLB_SEASON, hydrate="venue(location)")["teams"]
parks = pl.DataFrame(
    [
        {
            "team": t["abbreviation"],
            "park": t["venue"]["name"],
            "longitude": t["venue"]["location"]["defaultCoordinates"]["longitude"],
            "latitude": t["venue"]["location"]["defaultCoordinates"]["latitude"],
        }
        for t in teams
    ]
).sort("team")
shots.height, passes.height, parks.height
```

<div class="sdv-output">

```text
(27, 650, 30)
```

</div>

## 1. Every shot of a Stanley Cup Final period, as logos on the rink

`surface_layer("hockey", "nhl")` is sportypy's NHL rink as a `PolygonLayer` in feet, the origin at centre ice, and
`logo_icon_layer` puts each shot's team logo at its (x, y) in the same feet. `deck()` sees the surface, draws it top
down (an OrthographicView, y up) fitted to the rink, and draws the logos in the rink's coordinates. `size` is the
logo's height on screen in pixels. In the first period Edmonton shot at the right-hand goal and Florida at the left.
pydeck writes every layer's data into the page, so `tolerance` (in feet here) thins sportypy's arcs further than
the default: at 0.25 ft the rink is about 9,200 points instead of 14,400 (123,000 unthinned). Each line keeps its
shape, because each loop caps the tolerance at its own width and keeps its corners.

```python
rink = sdeck.surface_layer("hockey", "nhl", tolerance=0.25)
logos = sdeck.logo_icon_layer(shots, x="x", y="y", team="team", league="nhl", size=26)
sdeck.deck(rink, logos, height=420, tooltip={"text": "{team}"})
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/pydeck/5_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 2. Each shot as an arc to the goal it was aimed at

`pass_arc_layer` draws one arc per row from (`x`, `y`) to (`xend`, `yend`), in the team's colors: its primary color
where the arc starts and its secondary where it ends, so each arc shows its direction (no `background` here,
so the colors are the teams' own). deck.gl's arcs stand upright
by default, which a top-down view sees as straight lines; `tilt=90` lays them flat on the ice, and `height=0.3`
keeps each curve low (deck.gl's default height, 1, swings a long arc well past the boards).

```python
arcs = sdeck.pass_arc_layer(
    shots, x="x", y="y", xend="net_x", yend="net_y", team="team", league="nhl", width=3, tilt=90, height=0.3
)
sdeck.deck(rink, arcs, height=420)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/pydeck/7_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 3. France's passes in the 2018 World Cup final, flat on the pitch

The pitch is `surface_layer("soccer", "fifa")` resized to the 105 x 68 m frame `pitch_coords` returns, through
sportypy's own `pitch_updates`. France's completed first-half passes, each from where it was played to where it was
received, attacking left to right. Without `background` the colors are the team's own: France's navy and its
secondary color.

```python
pitch = sdeck.surface_layer("soccer", "fifa", pitch_updates={"pitch_length": 105, "pitch_width": 68})
france = passes.filter(pl.col("team") == ESPN_TEAM["France"], pl.col("half") == 1)
arcs = sdeck.pass_arc_layer(
    france, x="pitch_x", y="pitch_y", xend="to_x", yend="to_y", team="team", league="soccer",
    id_system="team_id", tilt=90, height=0.3, width=2,
)  # fmt: skip
print(f"{france.height} passes")
sdeck.deck(pitch, arcs, height=440)
```

<div class="sdv-output">

```text
89 passes
```

<iframe class="sdv-frame" src="/outputs/cookbooks/pydeck/9_1.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 4. Both finalists, readable on the grass

The arcs are drawn on the pitch's green, so pass it as `background`: every color then keeps 3:1 contrast against
the grass (WCAG's minimum for graphics), a team color that would not read gives way to the team's other color or is
lightened until it does, and the two teams' colors stay distinct (a CIE76 ΔE of 20 or more). This is the same team
palette sdvplot-js uses for dark mode. Croatia's passes are flipped to attack right to left.

One caveat: a color that does not read gives way to the team's other color, so when only one of a team's two colors
reads on the background, both ends take it. France's navy does not read on this dark grass, so its passes are mint at
both ends (the printed colors show it) and their direction is lost, while Croatia's two colors both read (lightened)
and its arcs keep theirs. On a grass where both of a team's colors read, the ends differ: check `sourceColor` against
`targetColor`.

```python
grass = "#{:02x}{:02x}{:02x}".format(*pitch["data"][0]["fillColor"][:3])  # the pitch's own fill
first_half = passes.filter(pl.col("half") == 1)
arcs = sdeck.pass_arc_layer(
    first_half, x="pitch_x", y="pitch_y", xend="to_x", yend="to_y", team="team", league="soccer",
    id_system="team_id", tilt=90, height=0.3, background=grass,
)  # fmt: skip
print(grass, {d["team"]: (d["sourceColor"], d["targetColor"]) for d in arcs["data"]})
sdeck.deck(pitch, arcs, height=440)
```

<div class="sdv-output">

```text
#195f0c {'477': ([255, 127, 127, 255], [146, 161, 255, 255]), '478': ([200, 230, 216, 255], [200, 230, 216, 255])}
```

<iframe class="sdv-frame" src="/outputs/cookbooks/pydeck/11_1.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 5. Upright arcs in 3D

Without `tilt`, deck.gl's arcs rise off the surface, higher for longer passes, and a tilted view shows them. `deck()`
draws top down, so build the `pydeck.Deck` yourself with an OrbitView. The layers are `pydeck.Layer` keyword
arguments: a constant string is quoted (`"'cartesian'"`), because pydeck reads an unquoted string as an expression.
France's second-half passes:

```python
second = passes.filter(pl.col("team") == ESPN_TEAM["France"], pl.col("half") == 2)
arcs = sdeck.pass_arc_layer(
    second, x="pitch_x", y="pitch_y", xend="to_x", yend="to_y", team="team", league="soccer",
    id_system="team_id", background=grass,
)  # fmt: skip
pdk.Deck(
    layers=[pdk.Layer(**pitch), pdk.Layer(**arcs, coordinate_system="'cartesian'")],
    views=[pdk.View(type="OrbitView", controller=True)],
    initial_view_state=pdk.ViewState(target=[0, 0, 0], rotation_x=40, rotation_orbit=-20, zoom=2.4),
    map_provider=None,
    height=440,
)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/pydeck/13_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 6. Logos on a map

Without a surface, `deck()` draws a map fitted to the layers' positions, so `x` is a longitude and `y` a latitude.
Every MLB ballpark, from the MLB Stats API's venue coordinates; its abbreviations (`AZ`, `CWS`) resolve to the same
teams as ESPN's.

```python
logos = sdeck.logo_icon_layer(parks, x="longitude", y="latitude", team="team", league="mlb", size=34)
sdeck.deck(logos, height=440, map_style="light", tooltip={"text": "{team}"})
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/pydeck/15_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 7. A box lacrosse rink

`surface_layer` draws all ten of sportypy's sports, lacrosse, softball and volleyball included. The NLL plays box
lacrosse on a rink with boards, in feet with the origin at its centre, as the hockey rink above. With no other
layer, `deck()` fits the view to the surface.

```python
box = sdeck.surface_layer("lacrosse", "nll")
sdeck.deck(box, height=360)
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/pydeck/17_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

Data: NHL api-web; StatsBomb open data; the MLB Stats API.

## Run it yourself

<a href="pathname:///notebooks/cookbooks/pydeck.ipynb" download>Download the notebook</a> (outputs cleared) or [open it on GitHub](https://github.com/sportsdataverse/sdvplot/blob/main/examples/notebooks/cookbooks/pydeck.ipynb).

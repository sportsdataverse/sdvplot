---
title: "folium maps cookbook"
sidebar_label: "folium maps"
sidebar_position: 12
description: "Six Folium map recipes: MLB ballparks, team-colored circles with popups, division wordmarks, a layer per conference, dark tiles with dark logos, and a roster's hometowns in headshots."
---

# folium maps

[Folium](https://python-visualization.github.io/folium/) writes Leaflet web maps from Python: tiles,
markers, popups and layers, saved as one HTML page. sdvplot puts team logos, wordmarks and player
headshots on a map as image markers at each (longitude, latitude), with the team's name as the tooltip,
and gives you the team colors and image URLs for the rest of the map. Every location here comes from a
data source, never typed in: MLB ballparks from the MLB Stats API, college football stadiums and players'
hometowns from cfbfastR, both through sportsdataverse-py.

```python
import folium
import polars as pl
import sportsdataverse.cfb as cfb
import sportsdataverse.mlb as mlb

import sdvplot

MLB_SEASON = 2026
CFB_SEASON = 2025  # football names a season by the year it starts
```

The MLB Stats API's teams endpoint, hydrated with `venue(location)`, carries each home park's coordinates.
Its abbreviations (`AZ`, `CWS`) differ from ESPN's (`ARI`, `CHW`), so `sdvplot.resolve` maps both to one
team id before the standings join. cfbfastR's team info has every stadium's coordinates, capacity and
year built; its ESPN team ids are integers, cast once to the strings sdvplot uses. cfbfastR's rosters carry
each player's hometown coordinates.

```python
teams = mlb.mlb_teams(season=MLB_SEASON, hydrate="venue(location)")["teams"]
parks = pl.DataFrame(
    [
        {
            "abbr": t["abbreviation"],
            "team": t["name"],
            "division": t["division"]["name"],
            "park": t["venue"]["name"],
            "city": t["venue"]["location"]["city"],
            "elevation": t["venue"]["location"].get("elevation"),
            "latitude": t["venue"]["location"]["defaultCoordinates"]["latitude"],
            "longitude": t["venue"]["location"]["defaultCoordinates"]["longitude"],
        }
        for t in teams
    ]
)
parks = parks.with_columns(team_id=sdvplot.resolve(parks["abbr"], "mlb"))
standings = mlb.espn_mlb_standings(season=MLB_SEASON)
standings = standings.with_columns(team_id=sdvplot.resolve(standings["team_abbreviation"], "mlb")).select(
    "team_id", "wins", "losses", "point_differential"
)
assert parks.schema["team_id"] == standings.schema["team_id"]
parks = parks.join(standings, on="team_id").sort("abbr")

stadiums = (
    cfb.load_cfb_team_info([CFB_SEASON])
    .filter(pl.col("classification") == "fbs")
    .with_columns(pl.col("team_id").cast(pl.Int64).cast(pl.Utf8))
)
rosters = cfb.load_cfb_rosters_cfbd([CFB_SEASON])
parks.height, stadiums.height, rosters.height
```

<div class="sdv-output">

```text
(30, 136, 30072)
```

</div>

## 1. Every MLB ballpark

`add_logos` takes longitudes as x and latitudes as y. `height` is a fraction of the map's pixel height, so
give the map a height in pixels; the logos keep their size as you zoom. Each logo's tooltip is the team's
name.

```python
m = folium.Map(location=[38.5, -96], zoom_start=4, height=520, tiles="Esri.WorldGrayCanvas")
sdvplot.add_logos(m, parks["longitude"], parks["latitude"], parks["abbr"], league="mlb", height=0.07)
m
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/folium-maps/5_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 2. Team-colored circles sized by wins, with a popup

Draw your own Folium layers under the logos. `sdvplot.team_colors` gives each team's primary color for a
`CircleMarker`, sized here by regular-season wins, and `sdvplot.logo_url` puts the logo in the popup next to
the park, record and run differential. The circles are larger than the logos, so click a ring to open its
popup.

```python
lo, hi = parks["wins"].min(), parks["wins"].max()
m = folium.Map(location=[38.5, -96], zoom_start=4, height=520, tiles="Esri.WorldGrayCanvas")
colors = sdvplot.team_colors("mlb", parks["abbr"])
for row, color in zip(parks.iter_rows(named=True), colors, strict=True):
    popup = (
        f'<img src="{sdvplot.logo_url(row["abbr"], "mlb")}" width="48"><br>'
        f"<b>{row['team']}</b><br>{row['park']}, {row['city']}<br>"
        f"{row['wins']:.0f}-{row['losses']:.0f}, run differential {row['point_differential']:+.0f}"
    )
    folium.CircleMarker(
        [row["latitude"], row["longitude"]],
        radius=8 + 14 * (row["wins"] - lo) / (hi - lo),  # 8 px for the fewest wins, 22 px for the most
        color=color,
        weight=2,
        fill=True,
        fill_color=color,
        fill_opacity=0.45,
        popup=folium.Popup(popup, max_width=240),
    ).add_to(m)
sdvplot.add_logos(m, parks["longitude"], parks["latitude"], parks["abbr"], league="mlb", height=0.035)
m
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/folium-maps/7_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 3. A division in wordmarks

`add_wordmarks` draws the team's wordmark instead of its logo. MLB's wordmarks come in `on_light` and
`on_dark` variants (see `sdvplot.marks`), so name the one that suits the tiles. `fit_bounds` frames the
map on the parks themselves. The American League East:

```python
al_east = parks.filter(pl.col("division") == "American League East")
m = folium.Map(height=520, tiles="Esri.WorldGrayCanvas")
sdvplot.add_wordmarks(
    m, al_east["longitude"], al_east["latitude"], al_east["abbr"], league="mlb", variant="on_light", height=0.07
)
m.fit_bounds(al_east.select("latitude", "longitude").rows(), padding=(60, 60))
m
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/folium-maps/9_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 4. One layer per conference, with a layer control

sdvplot puts its markers in one `FeatureGroup` named "sdvplot logos", so a `LayerControl` lists them as
one layer. Add a group of your own per conference, here rings in each conference's color from
`sdvplot.teams("cfb", include_conferences=True)`, and the control turns the conferences on and off while
the logo layer stays one switch. The Power Four's stadiums, with each one's name and capacity on hover:

```python
power4 = ["SEC", "Big Ten", "Big 12", "ACC"]
conferences = sdvplot.teams("cfb", include_conferences=True).select("team_id", "color_primary")
conference_colors = dict(conferences.iter_rows())
p4 = stadiums.filter(pl.col("conference").is_in(power4))
m = folium.Map(location=[37.5, -92], zoom_start=4, height=560, tiles="Esri.WorldGrayCanvas")
for conference in power4:
    layer = folium.FeatureGroup(name=conference).add_to(m)
    for row in p4.filter(pl.col("conference") == conference).iter_rows(named=True):
        folium.CircleMarker(
            [row["latitude"], row["longitude"]],
            radius=16,
            color=conference_colors[conference],
            weight=4,
            fill=False,
            tooltip=f"{row['school']}: {row['venue_name']}, {row['capacity']:,} seats",
        ).add_to(layer)
sdvplot.add_logos(m, p4["longitude"], p4["latitude"], p4["team_id"], league="cfb", season=CFB_SEASON, height=0.04)
folium.LayerControl(collapsed=False).add_to(m)
m
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/folium-maps/11_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 5. Dark tiles and dark logos

On a dark basemap, ask for each team's `dark` variant: the version of the logo made for dark backgrounds.
The Big 12 on Esri's dark gray canvas:

```python
big12 = stadiums.filter(pl.col("conference") == "Big 12")
dark_gray = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer"
m = folium.Map(
    location=[36.5, -98],
    zoom_start=4,
    height=520,
    tiles=dark_gray + "/tile/{z}/{y}/{x}",
    attr="Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors",
)
sdvplot.add_logos(
    m, big12["longitude"], big12["latitude"], big12["team_id"], league="cfb", season=CFB_SEASON, variant="dark",
    height=0.07,
)  # fmt: skip
m
```

<div class="sdv-output">

<iframe class="sdv-frame" src="/outputs/cookbooks/folium-maps/13_0.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## 6. A roster's hometowns, in headshots

`add_headshots` places ESPN player headshots the same way; cfbfastR's roster ids are ESPN athlete ids,
and the tooltip is the id. Indiana's quarterbacks, running backs, receivers and tight ends at their
hometowns, with the Hoosiers' logo at their home stadium:

```python
hoosiers = rosters.filter(
    pl.col("team") == "Indiana",
    pl.col("position").is_in(["QB", "RB", "WR", "TE"]),
    pl.col("home_latitude").is_not_null(),
)
home = stadiums.filter(pl.col("school") == "Indiana")
m = folium.Map(location=[36, -86], zoom_start=5, height=560, tiles="Esri.WorldGrayCanvas")
sdvplot.add_headshots(
    m, hoosiers["home_longitude"], hoosiers["home_latitude"], hoosiers["athlete_id"], league="cfb", height=0.07
)
sdvplot.add_logos(m, home["longitude"], home["latitude"], home["team_id"], league="cfb", height=0.1)
print(f"{hoosiers.height} players")
m
```

<div class="sdv-output">

```text
32 players
```

<iframe class="sdv-frame" src="/outputs/cookbooks/folium-maps/15_1.html" title="HTML output" height="480" loading="lazy"></iframe>

</div>

## Run it yourself

<a href="pathname:///notebooks/cookbooks/folium-maps.ipynb" download>Download the notebook</a> (outputs cleared) or [open it on GitHub](https://github.com/sportsdataverse/sdvplot/blob/main/examples/notebooks/cookbooks/folium-maps.ipynb).

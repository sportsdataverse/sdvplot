---
title: "Quickstart tutorial"
sidebar_label: "Quickstart"
sidebar_position: 1
description: "Resolve team values, pick a season, and get team colors and logo urls with sdvplot."
---

# sdvplot quickstart

sdvplot gives every SportsDataverse team a canonical id, a color pair, and logos (with eras) so you can label and
color charts the same way in any plotting library. Lookups run against a bundled team index; logos and headshots are
fetched on demand and cached.

## Install

```bash
pip install "sdvplot[mpl,svg]"
```

The `mpl` extra installs matplotlib, used here to plot `logo_image` marks (the `add_logos` helpers arrive with the adapters), and the `svg` extra rasterizes SVG marks (many NHL logos are SVG).

```python
import sdvplot
```

## Resolve team values

`resolve` turns team values from any supported source (abbreviations, names, ESPN ids) into one canonical `team_id`. The league is always required.

```python
sdvplot.resolve(["LV", "OAK", "Las Vegas Raiders", 13], "nfl")
```

<div class="sdv-output">

```text
['13', '13', '13', '13']
```

</div>

## Seasons

`season=` is optional. It picks the right team when a code was reused, and it is how era-aware lookups such as logos choose a mark.

```python
sdvplot.resolve("OAK", "nfl", season=2010), sdvplot.resolve("OAK", "nfl", season=2024)
```

<div class="sdv-output">

```text
('13', '13')
```

</div>

Both seasons give the Raiders (`'13'`): in the shipped NFL index no code is shared by two franchises, so the season does not change
the answer here, and a unique code still resolves when the season is outside its dates. The era only changes *logos*, which
[the logos tutorial](03_logos_and_seasons.md) shows.

## Suggestions

When a value does not resolve, `suggest` lists close candidates.

```python
sdvplot.suggest("Las Vegas Raider", "nfl")
```

<div class="sdv-output">

```text
[('13', 'Las Vegas Raiders')]
```

</div>

## The team table

`teams` returns the team table for a league.

```python
sdvplot.teams("nfl").head()
```

<div class="sdv-output">

| league | team_id | abbr | name               | short_name | location     | program | conference_id | conference                   | color_primary | color_secondary | color_source |
|--------|---------|------|--------------------|------------|--------------|---------|---------------|------------------------------|---------------|-----------------|--------------|
| nfl    | 1       | ATL  | Atlanta Falcons    | Falcons    | Atlanta      | pro     | nfl:nfc       | National Football Conference | #a71930       | #000000         | nflverse     |
| nfl    | 10      | TEN  | Tennessee Titans   | Titans     | Tennessee    | pro     | nfl:afc       | American Football Conference | #4495d2       | #d50a0a         | nflverse     |
| nfl    | 11      | IND  | Indianapolis Colts | Colts      | Indianapolis | pro     | nfl:afc       | American Football Conference | #002c5f       | #a5acaf         | nflverse     |
| nfl    | 12      | KC   | Kansas City Chiefs | Chiefs     | Kansas City  | pro     | nfl:afc       | American Football Conference | #e31837       | #ffb612         | nflverse     |
| nfl    | 13      | LV   | Las Vegas Raiders  | Raiders    | Las Vegas    | pro     | nfl:afc       | American Football Conference | #000000       | #a5acaf         | nflverse     |

</div>

## Colors

`palette` maps team ids or abbreviations to primary colors, ready for a plotting library.

```python
sdvplot.palette("nfl", teams=["LV", "KC", "SF"])
```

<div class="sdv-output">

```text
{'LV': '#000000', 'KC': '#e31837', 'SF': '#aa0000'}
```

</div>

## Logos

`logo_url` returns a CDN url for a team's mark.

```python
sdvplot.logo_url("KC", "nfl")
```

<div class="sdv-output">

```text
'https://sdv.nyc3.cdn.digitaloceanspaces.com/assets/public/sha256/3d/3d77958dc6373768919bb2681cbe1b143f56c07a1f013460def665a5026a7f3d.png'
```

</div>

## Versions

`versions` reports the package, bundled index, and logo manifest versions in use.

```python
sdvplot.versions()
```

<div class="sdv-output">

```text
{'sdvplot': '0.1.0',
 'index': '1e20bbb90d63',
 'manifest_last_modified': 'Thu, 01 Oct 2026 07:44:07 GMT'}
```

</div>

## Run it yourself

<a href="pathname:///notebooks/01_quickstart.ipynb" download>Download the notebook</a> (outputs cleared) or [open it on GitHub](https://github.com/sportsdataverse/sdvplot/blob/main/examples/notebooks/01_quickstart.ipynb).

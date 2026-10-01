---
title: Quickstart tutorial
sidebar_label: Quickstart
sidebar_position: 1
---

# sdvplot quickstart

sdvplot gives every SportsDataverse team a canonical id, a color pair, and logos (with eras) so you can label and
color charts the same way in any plotting library. Lookups run against a bundled team index; logos and headshots are
fetched on demand and cached.

```bash
pip install "sdvplot[mpl,svg]"
```

The `mpl` extra adds matplotlib helpers and the `svg` extra rasterizes SVG marks (many NHL logos are SVG).


```python
import sdvplot
```

`resolve` turns team values from any supported source (abbreviations, names, ESPN ids) into one canonical `team_id`. The league is always required.


```python
sdvplot.resolve(["LV", "OAK", "Las Vegas Raiders", 13], "nfl")
```




    ['13', '13', '13', '13']



`season=` is optional. It picks the right team when a code was reused, and it is how era-aware lookups such as logos choose a mark.


```python
sdvplot.resolve("OAK", "nfl", season=2010), sdvplot.resolve("OAK", "nfl", season=2024)
```




    ('13', '13')



Both seasons give the Raiders (`'13'`): in the shipped NFL index no code is shared by two franchises, so the season does not change
the answer here, and a unique code still resolves when the season is outside its dates. The era only changes *logos*, which
[the logos tutorial](03_logos_and_seasons.md) shows.

When a value does not resolve, `suggest` lists close candidates.


```python
sdvplot.suggest("Las Vegas Raider", "nfl")
```




    [('13', 'Las Vegas Raiders')]



`teams` returns the team table for a league.


```python
sdvplot.teams("nfl").head()
```




    shape: (5, 12)
    ┌────────┬─────────┬──────┬─────────────┬───┬─────────────┬─────────────┬─────────────┬────────────┐
    │ league ┆ team_id ┆ abbr ┆ name        ┆ … ┆ conference  ┆ color_prima ┆ color_secon ┆ color_sour │
    │ ---    ┆ ---     ┆ ---  ┆ ---         ┆   ┆ ---         ┆ ry          ┆ dary        ┆ ce         │
    │ str    ┆ str     ┆ str  ┆ str         ┆   ┆ str         ┆ ---         ┆ ---         ┆ ---        │
    │        ┆         ┆      ┆             ┆   ┆             ┆ str         ┆ str         ┆ str        │
    ╞════════╪═════════╪══════╪═════════════╪═══╪═════════════╪═════════════╪═════════════╪════════════╡
    │ nfl    ┆ 1       ┆ ATL  ┆ Atlanta     ┆ … ┆ National    ┆ #a71930     ┆ #000000     ┆ nflverse   │
    │        ┆         ┆      ┆ Falcons     ┆   ┆ Football    ┆             ┆             ┆            │
    │        ┆         ┆      ┆             ┆   ┆ Conference  ┆             ┆             ┆            │
    │ nfl    ┆ 10      ┆ TEN  ┆ Tennessee   ┆ … ┆ American    ┆ #4495d2     ┆ #d50a0a     ┆ nflverse   │
    │        ┆         ┆      ┆ Titans      ┆   ┆ Football    ┆             ┆             ┆            │
    │        ┆         ┆      ┆             ┆   ┆ Conference  ┆             ┆             ┆            │
    │ nfl    ┆ 11      ┆ IND  ┆ Indianapoli ┆ … ┆ American    ┆ #002c5f     ┆ #a5acaf     ┆ nflverse   │
    │        ┆         ┆      ┆ s Colts     ┆   ┆ Football    ┆             ┆             ┆            │
    │        ┆         ┆      ┆             ┆   ┆ Conference  ┆             ┆             ┆            │
    │ nfl    ┆ 12      ┆ KC   ┆ Kansas City ┆ … ┆ American    ┆ #e31837     ┆ #ffb612     ┆ nflverse   │
    │        ┆         ┆      ┆ Chiefs      ┆   ┆ Football    ┆             ┆             ┆            │
    │        ┆         ┆      ┆             ┆   ┆ Conference  ┆             ┆             ┆            │
    │ nfl    ┆ 13      ┆ LV   ┆ Las Vegas   ┆ … ┆ American    ┆ #000000     ┆ #a5acaf     ┆ nflverse   │
    │        ┆         ┆      ┆ Raiders     ┆   ┆ Football    ┆             ┆             ┆            │
    │        ┆         ┆      ┆             ┆   ┆ Conference  ┆             ┆             ┆            │
    └────────┴─────────┴──────┴─────────────┴───┴─────────────┴─────────────┴─────────────┴────────────┘



`palette` maps team ids or abbreviations to primary colors, ready for a plotting library.


```python
sdvplot.palette("nfl", teams=["LV", "KC", "SF"])
```




    {'LV': '#000000', 'KC': '#e31837', 'SF': '#aa0000'}



`logo_url` returns a CDN url for a team's mark.


```python
sdvplot.logo_url("KC", "nfl")
```




    'https://sdv.nyc3.cdn.digitaloceanspaces.com/assets/public/sha256/3d/3d77958dc6373768919bb2681cbe1b143f56c07a1f013460def665a5026a7f3d.png'



`versions` reports the package, bundled index, and logo manifest versions in use.


```python
sdvplot.versions()
```




    {'sdvplot': '0.1.0',
     'index': '1e20bbb90d63',
     'manifest_last_modified': 'Thu, 01 Oct 2026 07:44:07 GMT'}

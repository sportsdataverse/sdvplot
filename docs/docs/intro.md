---
title: Getting started
sidebar_label: Getting started
sidebar_position: 1
description: Install sdvplot and its optional extras, and draw team logos, wordmarks, headshots and colors in Python plots and tables.
---

# sdvplot

sdvplot gives Python plots and tables team logos, wordmarks, player headshots and team colors. Logos come from the
SportsDataverse logo archive (sdv-assets), and team identity and colors come from an index bundled with the package.
It is the Python counterpart to [sdvplotR](https://sdvplotR.sportsdataverse.org/) and part of the
[SportsDataverse](https://sportsdataverse.org).

## Install

```bash
pip install sdvplot
```

The core needs only narwhals, numpy, polars, Pillow, platformdirs and requests (with urllib3 2.6 or later). Each extra adds the
libraries for one feature:

```bash
pip install "sdvplot[mpl]"
```

| Extra | Adds |
|---|---|
| `[svg]` | resvg-py, to rasterize SVG marks in `logo_image()` and the matplotlib-family adapters |
| `[mpl]` | matplotlib |
| `[plotnine]` | plotnine |
| `[plotly]` | plotly |
| `[altair]` | altair |
| `[bokeh]` | bokeh |
| `[holoviews]` | holoviews and bokeh (sdvplot draws through its Bokeh backend) |
| `[tables]` | great_tables, htmltools and nokap (which renders tables to PNG through a headless Chrome) |
| `[reactable]` | reactable |
| `[folium]` | folium |
| `[surfaces]` | sportypy (1.2 or newer) and mplsoccer |
| `[plottable]` | plottable |
| `[itables]` | itables, for `sdvplot.itables.itables_sdv_theme()` |
| `[pygal]` | pygal |
| `[pydeck]` | pydeck, for `sdvplot.pydeck`'s layers and `deck()` (`surface_layer` also needs `[surfaces]`) |
| `[perspective]` | perspective-python (with its Jupyter widget), for `sdvplot.perspective`; Python 3.11+ (its wheels are cp311-abi3 only) |
| `[all]` | every extra above (`[perspective]` only on Python 3.11+) |

`[svg]` lets `logo_image()`, and the adapters that draw decoded images, rasterize SVG marks. With `[mpl]`, `[plotnine]`, `[plotly]`, `[altair]`, `[bokeh]`,
`[holoviews]`, `[tables]`, `[folium]` or `[pygal]`, `add_logos()`, `add_wordmarks()` and `add_headshots()` draw on that
library's plots, tables and maps; `axis_logos()` works on matplotlib, seaborn, plotnine, Plotly and Altair. `[surfaces]`
is for `surface()` (the fields, courts, rinks and sheets of ten sports, from football to curling), `[reactable]` and `[plottable]` add column helpers (`sdvplot.reactable`, `sdvplot.plottable`), and
`[itables]` the surveyed table themes for itables (`sdvplot.itables`).
`sdvplot.pydeck` builds deck.gl layers (team logos, team-colored arcs, sportypy surfaces) for pydeck, and
`sdvplot.perspective` Perspective viewer configs in team colors and a logo column.

`surface()` and `surface_layer()` need sportypy 1.2 or newer. While PyPI has only sportypy 1.0, install it from GitHub:
`pip install -U "sportypy @ git+https://github.com/sportsdataverse/sportypy@v1.2.5"`.

## Quick example

```python
import sdvplot

sdvplot.resolve(["LV", "OAK", "Las Vegas Raiders"], "nfl")  # ['13', '13', '13']
sdvplot.palette("nfl", teams=["LV", "KC"])  # {'LV': '#000000', 'KC': '#e31837'}
sdvplot.logo_url("OAK", "nfl", season=2010)  # the CDN URL of the Oakland-era mark
img = sdvplot.logo_image("LV", "nfl", size=128)  # a 128x128 PIL image, cached after the first download
```

- `resolve()` turns any team identifier into the canonical `team_id` and never guesses.
- `palette()` returns a plain `{team: "#hex"}` dict, keyed by your own values.
- `logo_url()` returns the archive URL for a web library. `logo_image()` returns a decoded image for matplotlib-style
  libraries.

## Learn more

- Concepts:
  - [Team identity](concepts/identity.md): how identifiers resolve.
  - [Seasons and eras](concepts/seasons-and-eras.md): season conventions and relocated franchises.
  - [Logos](concepts/logos.md): the archive and how a mark is chosen.
  - [Colors](concepts/colors.md): palettes and color sources.
  - [The cache](concepts/cache.md): what is downloaded, where it lives, and working offline.
  - [Table themes](concepts/table-themes.md): the surveyed table themes the table helpers share.
- [API reference](reference/index.md): every public function.
- Tutorials: executed notebooks, starting with the [quickstart](tutorials/01_quickstart.md).
- [For adapter authors](adapters/contract.md): the contract every plotting adapter meets.

## Logos, trademarks and data

Team names, logos, wordmarks and player headshots are trademarks or copyrighted works of their respective leagues,
teams, schools and other rights holders. sdvplot is not affiliated with, sponsored by or endorsed by any of them, and
using sdvplot to draw a mark grants no right to use it. The package ships no logo files: the wheel carries only an
index of team names, ids and colors, and marks are fetched at runtime from the
[SportsDataverse logo archive](https://github.com/sportsdataverse/sdv-assets). Use of any mark in your own work is
governed by that owner's terms, and following them is your responsibility. The [MIT license](https://github.com/sportsdataverse/sdvplot/blob/main/LICENSE)
covers the sdvplot code only; team data belongs to its respective owners and sources.

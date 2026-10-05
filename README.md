# sdvplot <a href='https://sdvplot.sportsdataverse.org/'><img src='https://raw.githubusercontent.com/sportsdataverse/sdvplot/main/docs/static/img/sdvplot-logo.png' align="right" width="25%" min-width="120px" alt="sdvplot hex logo" /></a>

[![PyPI](https://img.shields.io/pypi/v/sdvplot)](https://pypi.org/project/sdvplot/)
[![Python](https://img.shields.io/pypi/pyversions/sdvplot)](https://pypi.org/project/sdvplot/)
[![Lifecycle: experimental](https://img.shields.io/badge/lifecycle-experimental-orange.svg)](https://lifecycle.r-lib.org/articles/stages.html#experimental)
[![Docs](https://img.shields.io/badge/docs-sdvplot.sportsdataverse.org-blue)](https://sdvplot.sportsdataverse.org)

Team logos, wordmarks, headshots and colors for Python plots and tables, from the SportsDataverse logo archive. It
resolves team abbreviations, names and provider ids across 28 leagues and picks the right era's mark for a season. Colors
and logos work with any library through `palette()`, `team_colors()`, `logo_url()` and `logo_image()`, and the
`add_logos()`, `add_wordmarks()` and `add_headshots()` adapters draw them on matplotlib (and seaborn), plotnine, plotly,
altair, bokeh, holoviews, great_tables, folium and pygal plots, tables and maps. `sdvplot.great_tables` also ports
sdvplotR's table themes, cell styling, legends and image export, and `surface()` draws a league's field, court or rink
in a team's colors. The Python counterpart to [sdvplotR](https://sdvplotR.sportsdataverse.org/). See
[CHANGELOG](https://github.com/sportsdataverse/sdvplot/blob/main/CHANGELOG.md).

## Installation

```bash
pip install sdvplot
# or
uv add sdvplot
```

Plotting libraries are optional extras, for example
`pip install "sdvplot[mpl]"`. Each extra adds the libraries for one feature: `[svg]` lets `logo_image()`
rasterize SVG marks. With `[mpl]`, `[plotnine]`, `[plotly]`, `[altair]`, `[bokeh]`, `[holoviews]`, `[tables]`,
`[folium]` or `[pygal]`, `add_logos()`, `add_wordmarks()` and `add_headshots()` draw on that library's plots, tables and
maps; `axis_logos()` works on matplotlib, seaborn, plotnine, Plotly and Altair. `[surfaces]` is for `surface()`, and
`[reactable]` and `[plottable]` add column helpers (`sdvplot.reactable`, `sdvplot.plottable`).

| Extra | Adds |
| --- | --- |
| `[mpl]` | matplotlib |
| `[plotnine]` | plotnine |
| `[plotly]` | plotly |
| `[altair]` | altair |
| `[bokeh]` | bokeh |
| `[holoviews]` | holoviews |
| `[tables]` | great_tables |
| `[reactable]` | reactable (reactable-py) |
| `[folium]` | folium |
| `[svg]` | resvg-py, for SVG marks |
| `[surfaces]` | sportypy and mplsoccer |
| `[plottable]` | plottable |
| `[pygal]` | pygal |
| `[all]` | everything above |

## Get started

```python
import sdvplot

sdvplot.resolve(["LV", "OAK", "Las Vegas Raiders"], "nfl")  # ['13', '13', '13']
sdvplot.palette("nfl", teams=["LV", "KC"])  # {'LV': '#000000', 'KC': '#e31837'}
sdvplot.logo_url("OAK", "nfl", season=2010)  # the Oakland-era mark
img = sdvplot.logo_image("LV", "nfl", size=128)  # a PIL image
```

Colors work in any library that takes a `{value: color}` mapping, for example seaborn:
`sns.barplot(data=df, x="team", y="epa", hue="team", palette=sdvplot.palette("nfl", teams=df["team"]))`.

`teams()` records where each team's colors come from in `color_source`: `nflverse` or `espn` when that source
publishes them, `logo` when they are derived from the team's archived logo because no source does, and `fallback` for
a placeholder that is not the team's colors.

## Environment variables

- `SDVPLOT_CACHE_DIR`: cache root.
- `SDVPLOT_CACHE_TTL`: cache lifetime in days (default 7).
- `SDVPLOT_LIVE_TESTS=1`: enable the network tests.

## Documentation

- [Docs site](https://sdvplot.sportsdataverse.org) with concepts, tutorials and the API reference.
- [Changelog](https://github.com/sportsdataverse/sdvplot/blob/main/CHANGELOG.md).
- [Contributing](https://github.com/sportsdataverse/sdvplot/blob/main/CONTRIBUTING.md).

## Logos, trademarks and data

Team names, logos, wordmarks and player headshots are trademarks or copyrighted works of their respective leagues,
teams, schools and other rights holders. sdvplot is not affiliated with, sponsored by or endorsed by any of them, and
using sdvplot to draw a mark grants no right to use it. The package ships no logo files: the wheel carries only an
index of team names, ids and colors, and marks are fetched at runtime from the
[SportsDataverse logo archive](https://github.com/sportsdataverse/sdv-assets), headshots from ESPN (or, for NFL gsis
ids, the URLs in nflverse's player table). Use of any mark in your own work is
governed by that owner's terms, and following them is your responsibility. The [MIT license](https://github.com/sportsdataverse/sdvplot/blob/main/LICENSE)
covers the sdvplot code only; team data belongs to its respective owners and sources.

## Companion packages

- [sdvplotR](https://sdvplotR.sportsdataverse.org/): the R package this one mirrors.
- [sdv-py](https://py.sportsdataverse.org/): SportsDataverse data for Python.
- [sportypy](https://sportypy.sportsdataverse.org/): sports surfaces for Python plots.

## Citations

To cite [**`sdvplot`**](https://sdvplot.sportsdataverse.org) in publications, use:

BibTex Citation

```bibtex
@misc{gilani_2026_sdvplot,
  author = {Gilani, Saiem},
  title = {sdvplot: Team logos, wordmarks, headshots and colors for Python plots and tables},
  url = {https://sdvplot.sportsdataverse.org},
  year = {2026}
}
```

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [sdvplot](#sdvplot)
  - [Installation](#installation)
  - [Get started](#get-started)
  - [Environment variables](#environment-variables)
  - [Documentation](#documentation)
  - [Companion packages](#companion-packages)
  - [Citations](#citations)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# sdvplot

[![Lifecycle: experimental](https://img.shields.io/badge/lifecycle-experimental-orange.svg)](https://lifecycle.r-lib.org/articles/stages.html#experimental)
[![PyPI](https://img.shields.io/pypi/v/sdvplot)](https://pypi.org/project/sdvplot/)
[![Downloads](https://img.shields.io/pypi/dm/sdvplot)](https://pypi.org/project/sdvplot/)
[![Docs](https://img.shields.io/badge/docs-sdvplot.sportsdataverse.org-blue)](https://sdvplot.sportsdataverse.org)

Team logos, wordmarks, headshots and colors for Python plots and tables, from the SportsDataverse logo archive. It
resolves team abbreviations, names and provider ids across 28 leagues and picks the right era's mark for a season. Colors
and logos work with any library today through `palette()`, `team_colors()`, `logo_url()` and `logo_image()`. The
`add_logos` adapters for matplotlib, plotnine, plotly, altair, bokeh, holoviews, great_tables and folium arrive in later
releases. The Python counterpart to [sdvplotR](https://sdvplotR.sportsdataverse.org/). See
[CHANGELOG.md](https://sdvplot.sportsdataverse.org/CHANGELOG).

## Installation

```bash
pip install sdvplot
# or
uv add sdvplot
```

Plotting libraries are optional extras, for example `pip install "sdvplot[mpl]"`. In this core release they only install
the library; the adapters that use it arrive in later releases:

| Extra | Adds |
| --- | --- |
| `[mpl]` | matplotlib |
| `[plotnine]` | plotnine |
| `[plotly]` | plotly |
| `[altair]` | altair |
| `[bokeh]` | bokeh |
| `[holoviews]` | holoviews |
| `[tables]` | great_tables |
| `[folium]` | folium |
| `[svg]` | resvg-py, for SVG marks |
| `[surfaces]` | sportypy and mplsoccer |
| `[all]` | everything above |

## Get started

```python
import sdvplot

sdvplot.resolve(["LV", "OAK", "Las Vegas Raiders"], "nfl")      # ['13', '13', '13']
sdvplot.palette("nfl", teams=["LV", "KC"])                     # {'LV': '#000000', 'KC': '#e31837'}
sdvplot.logo_url("OAK", "nfl", season=2010)                    # the Oakland-era mark
img = sdvplot.logo_image("LV", "nfl", size=128)                # a PIL image
```

Colors work in any library that takes a `{value: color}` mapping, for example seaborn:
`sns.barplot(data=df, x="team", y="epa", hue="team", palette=sdvplot.palette("nfl", teams=df["team"]))`.

Colors marked `color_source="fallback"` are placeholders, not team colors.

## Environment variables

- `SDVPLOT_CACHE_DIR`: cache root.
- `SDVPLOT_CACHE_TTL`: cache lifetime in days (default 7).
- `SDVPLOT_LIVE_TESTS=1`: enable the network tests.

## Documentation

- [Docs site](https://sdvplot.sportsdataverse.org) with concepts, tutorials and the API reference.
- [Changelog](https://sdvplot.sportsdataverse.org/CHANGELOG).
- [Contributing](CONTRIBUTING.md).

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

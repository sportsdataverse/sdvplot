---
title: Getting started
sidebar_label: Getting started
sidebar_position: 1
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

The core needs only narwhals, polars, Pillow, platformdirs and requests. Each extra adds the libraries for one feature:

```bash
pip install "sdvplot[mpl]"
```

| Extra | Adds |
|---|---|
| `[svg]` | resvg-py, to rasterize SVG marks in `logo_image()` |
| `[mpl]` | matplotlib |
| `[plotnine]` | plotnine |
| `[plotly]` | plotly |
| `[altair]` | altair |
| `[bokeh]` | bokeh |
| `[holoviews]` | holoviews |
| `[tables]` | great_tables |
| `[folium]` | folium |
| `[surfaces]` | sportypy and mplsoccer |
| `[all]` | every extra above |

In this core release only `[svg]` changes what sdvplot can do. The other extras install the library that its adapter
needs, and the adapters arrive in later releases (see [the roadmap](#roadmap)).

## Quick example

```python
import sdvplot

sdvplot.resolve(["LV", "OAK", "Las Vegas Raiders"], "nfl")   # ['13', '13', '13']
sdvplot.palette("nfl", teams=["LV", "KC"])                  # {'LV': '#000000', 'KC': '#e31837'}
sdvplot.logo_url("OAK", "nfl", season=2010)                 # the CDN URL of the Oakland-era mark
img = sdvplot.logo_image("LV", "nfl", size=128)             # a 128x128 PIL image, cached after the first download
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
- [API reference](reference/index.md): every public function.
- Tutorials: executed notebooks, starting with the [quickstart](tutorials/01_quickstart.md).
- [For adapter authors](adapters/contract.md): the contract every plotting adapter meets.

## Roadmap

sdvplot ships as five sub-projects:

1. **Core** (this release): team identity, colors, logo selection, headshot URLs, the cache and the bundled index.
2. **matplotlib family**: matplotlib, seaborn and plotnine layers, axis logos, and bridges to sportypy, mplsoccer and
   plottable.
3. **Web family**: Plotly, Altair, Bokeh, HoloViews and Folium.
4. **Tables**: great_tables helpers.
5. **Long tail**: pygal, and other libraries as they add image marks.

Until the adapters land, `add_logos()` and the other plotting verbs raise `UnsupportedTargetError`. The core functions
already work with any library: pass `palette()` to seaborn or Plotly, and `logo_url()` or `logo_image()` to whatever draws
the image.

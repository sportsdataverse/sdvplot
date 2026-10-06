---
title: API reference
sidebar_label: Overview
sidebar_position: 0
---

# API reference

Every public function, grouped by what it works with. Each top-level function has a page, and each public submodule (the library adapters, the table helpers, `sdvplot.testing` and `sdvplot.typing`) has one page with a section per name. Each gives the signature, the arguments and what the function returns and raises.

## Teams

| Function | What it does |
|---|---|
| [resolve](resolve.md) | Canonical team_id(s) for team values in one league. |
| [suggest](suggest.md) | Up to n (team_id, name) candidates for a value that did not resolve, best first. |
| [teams](teams.md) | The bundled team index: one row per (league, team_id), with names, abbreviation, conference and colors. |

## Colors

| Function | What it does |
|---|---|
| [palette](palette.md) | A ``{team: "#hex"}`` dict for a league, ready for seaborn, Plotly, Altair, Bokeh or PyPalettes. |
| [team_colors](team_colors.md) | One "#hex" (or None) per team value, in the same container the values came in. |

## Logos and headshots

| Function | What it does |
|---|---|
| [logo_url](logo_url.md) | The CDN URL of a team's logo or wordmark, chosen for the season. |
| [logo_image](logo_image.md) | The team's mark as a PIL image (downloaded once, then cached). |
| [marks](marks.md) | Every archived mark for one team, best first. |
| [headshot_url](headshot_url.md) | A headshot URL for one player. |

## Plots and tables

| Function | What it does |
|---|---|
| [add_logos](add_logos.md) | Add team logos to a plot or table of any supported library. |
| [add_wordmarks](add_wordmarks.md) | Add team wordmarks to a plot or table of any supported library. |
| [add_headshots](add_headshots.md) | Add player headshots to a plot or table of any supported library. |
| [axis_logos](axis_logos.md) | Replace an axis' team labels with team logos on a plot of any supported library. |
| [surface](surface.md) | Draw the league's playing surface with sportypy, in a team's colors. |
| [court_coords](court_coords.md) | Convert stats.nba.com / stats.wnba.com shot locations to the court frame sportypy draws. |
| [pitch_coords](pitch_coords.md) | Convert soccer event coordinates from any provider's frame to the pitch ``surface("soccer")`` draws. |

| Submodule | What it holds |
|---|---|
| [sdvplot.matplotlib](matplotlib.md) | The matplotlib adapter: logos, wordmarks and headshots on Axes, single-Axes Figures and seaborn grids. |
| [sdvplot.plotnine](plotnine.md) | The plotnine adapter: logo, wordmark, headshot and image geoms, axis logos, team color scales and reference lines. |
| [sdvplot.plotly](plotly.md) | The Plotly adapter: logos, wordmarks, headshots and axis logos as layout images on a Plotly Figure. |
| [sdvplot.altair](altair.md) | The Altair adapter: logos, wordmarks and headshots as a native Vega-Lite image layer. |
| [sdvplot.bokeh](bokeh.md) | The Bokeh adapter: logos, wordmarks and headshots as one ``image_url`` glyph per call on a Bokeh figure. |
| [sdvplot.holoviews](holoviews.md) | The HoloViews adapter: a Bokeh plot hook that draws the marks through the Bokeh adapter when the element renders. |
| [sdvplot.folium](folium.md) | The Folium adapter: logos, wordmarks and headshots as map markers with image icons. |
| [sdvplot.pygal](pygal.md) | The pygal adapter: logos, wordmarks and headshots on pygal XY charts, plus team colors as a pygal Style. |
| [sdvplot.great_tables](great_tables.md) | great_tables helpers (``pip install sdvplot[tables]``), ported from sdvplotR's ``gt_*`` functions. |
| [sdvplot.reactable](reactable.md) | reactable-py columns (``pip install sdvplot[reactable]``), ported from sdvplotR's ``reactable_sdv_*`` functions. |
| [sdvplot.plottable](plottable.md) | plottable columns of team logos, wordmarks and player headshots. |

## Housekeeping

| Function | What it does |
|---|---|
| [versions](versions.md) | What a bug report needs: the package version, the bundled-index version, and the cached manifest's date. |
| [clear_cache](clear_cache.md) | Delete everything sdvplot has cached (manifest, images, rasters, nflverse, URL images such as headshots). |

| Submodule | What it holds |
|---|---|
| [sdvplot.testing](testing.md) | Shared behaviour every adapter must have. Adapter test suites call check_adapter_contract(). |
| [sdvplot.typing](typing.md) | Types for annotating code that calls sdvplot: the ``Literal`` aliases of its closed argument vocabularies. |

## Errors and warnings

[Errors and warnings](errors.md): the warning sdvplot emits and the errors it raises, with what each means.

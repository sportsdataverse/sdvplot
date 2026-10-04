<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Changelog](#changelog)
  - [Unreleased](#unreleased)
    - [Added — core (team identity, colors, logos, cache, adapter contract)](#added--core-team-identity-colors-logos-cache-adapter-contract)
    - [Added — repository standards](#added--repository-standards)
    - [Added — matplotlib family](#added--matplotlib-family)
    - [Added — web family](#added--web-family)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Changelog

## Unreleased

### Added — core (team identity, colors, logos, cache, adapter contract)

- Team resolver and id systems: `resolve()` maps abbreviations, names and provider ids (ESPN, NHL, nflverse, MLB, NBA, HockeyTech, NCAA, PFF, Cricinfo, CFBD, Baseball-Reference, FanGraphs, sdvplotR) to a stable string `team_id`, with a documented `PRIORITY` order and `nhl_id` available only through an explicit `id_system`.
- `suggest()` for near-miss candidates when a value does not resolve.
- `palette()` and `team_colors()`: team colors as a `{team: "#hex"}` mapping or one hex per value, with `color_source="fallback"` marking placeholders.
- `logo_url()`, `logo_image()` and `marks()`, with era selection by season (relocated franchises get their era's mark), variant and source preference.
- `headshot_url()`: ESPN athlete ids for NFL, NBA, WNBA, MLB, NHL and college football and basketball, plus NFL gsis ids through the nflverse player table.
- A download cache (`SDVPLOT_CACHE_DIR`, `SDVPLOT_CACHE_TTL`) with `clear_cache()`.
- The adapter registry and contract harness (`add_logos`, `add_wordmarks`, `add_headshots`, `axis_logos`, `sdvplot.testing`).
- A bundled index of 5,876 teams across 28 leagues, rebuilt reproducibly from `data-raw/` by `tools/build_index.py`.
- sdvplotR parity: 99.8% of sdvplotR's `clean_team_abbrs()` keys resolve to the same team (4,232 of 4,241 checked).

### Added — repository standards

- A Docusaurus docs site at <https://sdvplot.sportsdataverse.org> with a generated API reference and rendered tutorials.
- Example notebooks, executed by `tools/render_notebooks.py` into the tutorials.
- CI, a release workflow, and pre-commit hooks, in sdv-py's layout.
- `CONTRIBUTING.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, issue and pull-request templates, and sdv-py's dotfiles.

### Added — matplotlib family

- `add_logos`, `add_wordmarks`, `add_headshots` and `axis_logos` work on matplotlib Axes, one-Axes Figures and seaborn
  grids (`sdvplot.matplotlib`); `height` is a fraction of the Axes height at any dpi or figure size.
- plotnine: `geom_sdv_logos`, `geom_sdv_wordmarks`, `geom_sdv_headshots`, `axis_logos` and the team color scales
  `scale_color_sdv` / `scale_fill_sdv` (`sdvplot.plotnine`).
- `surface()`: sportypy playing surfaces in team colors, the port of sdvplotR's `sdv_surface()`.
- plottable `logo_column` and `headshot_column` (`sdvplot.plottable`, new `[plottable]` extra).
- The adapter contract (`sdvplot.testing`) now covers wordmarks, headshots, axis logos and alpha (rules 0-8).

### Added — web family

- `add_logos`, `add_wordmarks`, `add_headshots` and `axis_logos` work on Plotly figures (`sdvplot.plotly`; sdvplot
  pins the axis ranges so `height` is a fraction of the plot area) and Altair charts (`sdvplot.altair`, plus the
  native `logo_layer`).
- `add_logos`, `add_wordmarks` and `add_headshots` on Bokeh figures (`sdvplot.bokeh`), HoloViews elements through a
  Bokeh plot hook (`sdvplot.holoviews`) and Folium maps (`sdvplot.folium`, `x` longitude and `y` latitude).
- `embed=True` inlines the images as data URIs, for HTML that renders offline and for static export.
- The `[holoviews]` extra now installs Bokeh 3 as well.

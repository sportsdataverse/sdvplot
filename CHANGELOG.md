<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Changelog](#changelog)
  - [Unreleased](#unreleased)
    - [Added — core (team identity, colors, logos, cache, adapter contract)](#added--core-team-identity-colors-logos-cache-adapter-contract)
    - [Added — repository standards](#added--repository-standards)
    - [Added — matplotlib family](#added--matplotlib-family)
    - [Added — tables, wave A (marks and team identity)](#added--tables-wave-a-marks-and-team-identity)
    - [Added — table themes](#added--table-themes)
    - [Added — tables wave C1 (cell styling and formatting)](#added--tables-wave-c1-cell-styling-and-formatting)
    - [Added — tables, wave D (image export and composition)](#added--tables-wave-d-image-export-and-composition)
    - [Added — web family](#added--web-family)
    - [Added — long tail (pygal, Cartopy, gallery compatibility)](#added--long-tail-pygal-cartopy-gallery-compatibility)
    - [Added — tables wave C2 (legends, layout and annotation)](#added--tables-wave-c2-legends-layout-and-annotation)

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

### Added — tables, wave A (marks and team identity)

- `sdvplot.great_tables`, ported from sdvplotR with `league=` for `sport=`:
  - `gt_sdv_logos`, `gt_sdv_wordmarks` and `gt_sdv_headshots` put marks in body, stub or row-group cells, and
    `gt_sdv_cols_label` puts them in column labels.
  - `gt_merge_stack_team_color` stacks two columns in one cell, the bottom line in the team color.
  - The themes `gt_theme_sdv` (light or dark, three densities) and `gt_theme_sdv_team`.
  - Heights are pixels. Unknown values keep their text and warn once, when the function is called.
- `sdvplot.add_logos(gt, "team", league="nfl")`, `add_wordmarks` and `add_headshots` route a great_tables `GT` to
  those functions.
- `sdvplot.reactable` (new `[reactable]` extra): `reactable_sdv_logos`, `reactable_sdv_wordmarks`,
  `reactable_sdv_headshots`, `reactable_sdv_cols_label`, `reactable_sdv_team_color_bar` and
  `reactable_sdv_team_color_bg`. Each returns `reactable.Column` objects.
- `sdvplot.testing.check_table_adapter_contract` (rules T0-T6) for table adapters.
- `docs/PARITY_TABLES.md`: how each sdvplotR table function maps to sdvplot.
- The `[tables]` extra now needs great_tables 1.0 or later.

### Added — table themes

- The 18 sdvplotR table themes for great_tables, with sdvplotR's names, arguments and defaults
  (`sdvplot.great_tables`): `gt_theme_almanac`, `gt_theme_athletic`, `gt_theme_booktabs`, `gt_theme_broadsheet`,
  `gt_theme_brutalist`, `gt_theme_drench`, `gt_theme_gtutils`, `gt_theme_kenpom`, `gt_theme_midnight`, `gt_theme_ncaa`,
  `gt_theme_pl`, `gt_theme_savant`, `gt_theme_scoreboard`, `gt_theme_sofa`, `gt_theme_swiss`, `gt_theme_terminal`,
  `gt_theme_tier` and `gt_theme_tufte`, each with `density="comfortable" | "compact" | "social"`.
- `pal_midnight`: sdvplotR's five-color rank palette for dark grounds (every step clears 4.5:1 on midnight and terminal).
- `gt_theme_preview()`: the same rows in every theme, as `{theme name: GT}`.
- Theme fonts load every weight from Google Fonts, over gt's fallback stack.

### Added — tables wave C1 (cell styling and formatting)

- 17 sdvplotR cell helpers in `sdvplot.great_tables`, with R's names and arguments: `gt_538_caption`,
  `gt_bold_rows`, `gt_border_bars_bottom`, `gt_border_bars_top`, `gt_border_grid`, `gt_color_pills`,
  `gt_color_ranks`, `gt_color_results`, `gt_column_subheaders`, `gt_cutline`, `gt_delta`, `gt_fmt_rank`,
  `gt_fmt_tally`, `gt_group_stripes`, `gt_highlight_cells`, `gt_highlight_na` and `gt_indicator_boxes`. They take
  tables built from pandas or polars data.
- `gt_color_pills` and `gt_color_ranks` record their color scale for `gt_legend_continuous`.
- `docs/PARITY_TABLES.md` lists where they differ from R.

### Added — tables, wave D (image export and composition)

- `sdvplot.great_tables`: `gt_save_crop`, `gt_social_crop` and `gt_save_batch` save tables as trimmed, padded images
  (great_tables' `GT.gtsave`, headless Chrome); `gt_grid` and `gt_stack_tables` compose several tables into one HTML
  block or image. Ports of the sdvplotR functions of the same names; differences are in `docs/PARITY_TABLES.md`.
- `[tables]` names `htmltools` and `nokap`, which great_tables 1.0 already installs. Saving needs Chrome or Chromium
  (set `CHROME_PATH` for a non-standard install); no selenium.

### Added — web family

- `add_logos`, `add_wordmarks`, `add_headshots` and `axis_logos` work on Plotly figures (`sdvplot.plotly`; sdvplot
  pins the axis ranges so `height` is a fraction of the plot area) and Altair charts (`sdvplot.altair`, plus the
  native `logo_layer`).
- `add_logos`, `add_wordmarks` and `add_headshots` on Bokeh figures (`sdvplot.bokeh`), HoloViews elements through a
  Bokeh plot hook (`sdvplot.holoviews`) and Folium maps (`sdvplot.folium`, `x` longitude and `y` latitude).
- `embed=True` inlines the images as data URIs, for HTML that renders offline and for static export.
- The `[holoviews]` extra now installs Bokeh 3 as well.

### Added — long tail (pygal, Cartopy, gallery compatibility)

- pygal: `add_logos`, `add_wordmarks` and `add_headshots` on XY-family charts (`XY`, `DateTimeLine`, `DateLine`,
  `TimeLine`, `TimeDeltaLine`), drawn in every render; `embed=True` makes SVG and PNG exports work offline;
  `team_style()` colors series by team (`sdvplot.pygal`, new `[pygal]` extra).
- pygal: a copy of a chart (`copy.copy` or `copy.deepcopy`) renders the marks it was copied with, and marks added to
  the copy or to the original afterwards stay on that chart.
- Cartopy: the matplotlib adapter's `add_logos`, `add_wordmarks` and `add_headshots` take `transform=` (e.g.
  `ccrs.PlateCarree()` for longitude/latitude, or any matplotlib transform); a `GeoAxes` without it raises
  `ValueError`. A mark whose point falls outside the Axes is not drawn, in any coordinate system.
- `docs/COMPATIBILITY.md`: every package on python-graph-gallery's best dataviz packages list, how it gets marks or
  colors, and the test that proves it (`tests/test_compat_*.py`, new `compat` dependency group); a watch item for
  Reflex XY image marks, re-checked at each release.

### Added — tables wave C2 (legends, layout and annotation)

- `sdvplot.great_tables` gains sdvplotR's legend, layout and annotation helpers, with sdvplotR's names and arguments
  on pandas or polars data: `gt_legend_continuous`, `gt_legend_discrete`, `gt_marginalia`, `gt_outliers`,
  `gt_percentile_bar`, `gt_row_accent`, `gt_scale_note`, `gt_set_font`, `gt_significance`, `gt_snake`,
  `gt_snake_align`, `gt_social_tag`, `gt_spotlight`, `gt_tiers`, `gt_title_header`, `gt_watermark`, `gt_wrap_labels`.
- `gt_legend_continuous()` with no arguments draws the scale that `gt_percentile_bar`, `gt_color_ranks` or
  `gt_color_pills` colored with; `gt_legend_discrete()` draws the key `gt_tiers` used.
- `docs/PARITY_TABLES.md` lists every difference from sdvplotR for these functions.

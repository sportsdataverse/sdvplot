<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Changelog](#changelog)
  - [[Unreleased]](#unreleased)
    - [Added](#added)
    - [Changed](#changed)
    - [Fixed](#fixed)
  - [[0.1.0] - Unreleased](#010---unreleased)
    - [Migrating from the git pre-release](#migrating-from-the-git-pre-release)
    - [Added](#added-1)
      - [Core (team identity, colors, logos, cache, adapter contract)](#core-team-identity-colors-logos-cache-adapter-contract)
      - [Repository standards](#repository-standards)
      - [Matplotlib family](#matplotlib-family)
      - [Tables, wave A (marks and team identity)](#tables-wave-a-marks-and-team-identity)
      - [Table themes](#table-themes)
      - [Tables wave C1 (cell styling and formatting)](#tables-wave-c1-cell-styling-and-formatting)
      - [Tables, wave D (image export and composition)](#tables-wave-d-image-export-and-composition)
      - [Web family](#web-family)
      - [Long tail (pygal, Cartopy, gallery compatibility)](#long-tail-pygal-cartopy-gallery-compatibility)
      - [Tables wave C2 (legends, layout and annotation)](#tables-wave-c2-legends-layout-and-annotation)
      - [Parity extras (court coordinates, images by path, reference lines)](#parity-extras-court-coordinates-images-by-path-reference-lines)
      - [Parity extras (title images, team tiers)](#parity-extras-title-images-team-tiers)
    - [Changed](#changed-1)
      - [Documentation](#documentation)
      - [Documentation — example notebooks by section, interactive outputs and the gallery](#documentation--example-notebooks-by-section-interactive-outputs-and-the-gallery)
    - [Fixed](#fixed-1)
      - [Adapter contract follow-ups](#adapter-contract-follow-ups)
      - [Tables follow-ups](#tables-follow-ups)
      - [Content findings (team index, team tiers, surface)](#content-findings-team-index-team-tiers-surface)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Changelog

All notable changes to sdvplot are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A deprecation helper, `sdvplot._deprecate` (`deprecate()` and `@deprecated_alias`), and its warning,
  `sdvplot.SdvplotDeprecationWarning` (a `FutureWarning` and a `SdvplotWarning`), with a deprecation policy in
  CONTRIBUTING.md: one minor release of warnings before a removal. Nothing is deprecated yet.
- `sdvplot.typing`: the `Literal` types of the closed argument vocabularies (`IdSystem`, `HeadshotIdSystem`, `Which`,
  `MarkType`), for annotating code that keeps an argument in a variable (`which: Which = "primary"`).

### Changed

- Documentation: an "Add an adapter" guide for contributors (`docs/docs/adapters/add-an-adapter.md`), a checklist from
  the adapter module to the changelog entry, with a worked example that passes `check_adapter_contract`.

### Fixed

- A season outside the seasons sdvplot knows for the league is an `InputError` (a `ValueError`) naming the bounds,
  wherever a season is taken. The first season is the league's earliest dated alias in the bundled index (1920 for the
  NFL, 1947 for the NBA, 1997 for the WNBA, 2020 for the XFL; 1871, MLB's, for a league whose history is not dated), the
  last is next year. `logo_url("OAK", "nfl", season=1900)` and `resolve(..., season=20)` used to resolve silently. A
  split season such as `"2020-21"` gets a hint (pass the ending year), and a season of the wrong type (a `pd.Timestamp`)
  is a `TypeError` that names `season` rather than the team values.
- A `variant` that no mark in the archive has (a typo, or not a string) is an `InputError` listing the league's
  variants; it used to fall back to the default mark without a word. A variant the team lacks still falls back, as
  before.
- Warnings point at the caller's line: they walk out of sdvplot's frames instead of using fixed `stacklevel`s, which
  named `_colors.py`, `_placement.py` and other sdvplot files whenever the call went through more than one function.
- A misspelled column name is the same `ValueError` on pandas and polars (`column(s) ['teamz'] not in the table; its
  columns are [...]`) in every great_tables helper that takes columns: the `gt_sdv_*` marks (their
  `locations=loc.body(...)` too), `gt_percentile_bar`, `gt_wrap_labels`, `gt_color_pills` and the rest, through the one
  column resolver they share. pandas used to match nothing silently and polars raised its own `ColumnNotFoundError`.

## [0.1.0] - Unreleased

First release. The date is set when v0.1.0 is tagged.

### Migrating from the git pre-release

0.1.0 freezes the public API. Code written against a git install from before it needs these changes; each old call now
fails loudly, with the message shown:

- `palette("nfl", "secondary")` is `palette("nfl", which="secondary")`: `palette` is `palette(league, teams=None, *,
  which="primary", season=None)`, as sdvplotR's `sdv_color_palette(sport, teams, type)`. The old call raises
  `InputError: 'secondary' is a color slot, not a team; pass it by keyword: palette(league, teams=...,
  which="secondary")`.
- `team_colors(teams, "nfl")` is `team_colors("nfl", teams)`: the league comes first, as in sdvplotR's
  `sdv_team_colors(sport, team, type)`. With a list or Series of teams the old order raises `InputError: league must be
  a league key such as 'nfl', got list; team_colors and palette take the league first: team_colors(league, teams)`;
  with one team, `InputError: unknown league 'KC'; known leagues: [...]`.
- Secondary arguments are keyword-only: `season`, `id_system` and `strict` on `resolve`; `season`, `variant`,
  `mark_type` and `size` on `logo_url` and `logo_image`; `season` on `marks`; `n` on `suggest`; `id_system` on
  `headshot_url`; `x` and `y` on `court_coords`. `resolve(v, "nfl", 2020)` raises `TypeError: resolve() takes 2
  positional arguments but 3 were given`; write `resolve(v, "nfl", season=2020)`.
- Each public submodule exports only its `__all__`, and `dir()` shows only that. Helpers and the adapter test hooks are
  underscored (`_drawn_marks`, `_drawn_axis_marks`, `_visible_axis_labels`, `_SUPPORTS_AXIS_LOGOS`,
  `_drawn_title_images`, great_tables' `_drawn_cells` and `_rendered_html`), so `sdvplot.matplotlib.draw_placements`
  raises `AttributeError: module 'sdvplot.matplotlib' has no attribute 'draw_placements'`.
- A table's `height` is pixels: `gt_sdv_logos(gt, "team", league="nfl", height=0.1)` (and the front door on a `GT`)
  raises `InputError: height is the image height in pixels for a table (such as 30), got 0.1; a fraction of the plot
  height is the unit for plots, not tables` instead of drawing a 0.1 px image.
- New errors, each still the builtin you may already catch: `SdvplotError` is the base of them all; `InputError` (a
  `ValueError`) is raised by the shared argument checks (league, `which`, `id_system`, `mark_type`, height, alpha);
  `UnsupportedTargetError` (a `TypeError`) by an adapter given the wrong kind of object or asked for axis logos it
  cannot draw; `UnsafeDownloadError` (an `OSError`) and `UnsafeCachePathError` (a `ValueError`) are exported.

### Added

#### Core (team identity, colors, logos, cache, adapter contract)

- Team resolver and id systems: `resolve()` maps abbreviations, names and provider ids (ESPN, NHL, nflverse, MLB, NBA, HockeyTech, NCAA, PFF, Cricinfo, CFBD, Baseball-Reference, FanGraphs, sdvplotR) to a stable string `team_id`, with a documented `PRIORITY` order and `nhl_id` available only through an explicit `id_system`.
- `suggest()` for near-miss candidates when a value does not resolve.
- `palette()` and `team_colors()`: team colors as a `{team: "#hex"}` mapping or one hex per value, with `color_source="fallback"` marking placeholders.
- `logo_url()`, `logo_image()` and `marks()`, with era selection by season (relocated franchises get their era's mark), variant and source preference.
- `headshot_url()`: ESPN athlete ids for NFL, NBA, WNBA, MLB, NHL and college football and basketball, plus NFL gsis ids through the nflverse player table.
- A download cache (`SDVPLOT_CACHE_DIR`, `SDVPLOT_CACHE_TTL`) with `clear_cache()`.
- The adapter registry and contract harness (`add_logos`, `add_wordmarks`, `add_headshots`, `axis_logos`, `sdvplot.testing`).
- A bundled index of 5,879 teams across 28 leagues, rebuilt reproducibly from `data-raw/` by `tools/build_index.py`.
- sdvplotR parity: 99.8% of sdvplotR's `clean_team_abbrs()` keys resolve to the same team (4,232 of 4,241 checked).

#### Repository standards

- A Docusaurus docs site at <https://sdvplot.sportsdataverse.org> with a generated API reference and rendered tutorials.
- Example notebooks, executed by `tools/render_notebooks.py` into the tutorials.
- CI, a release workflow, and pre-commit hooks, in sdv-py's layout.
- `CONTRIBUTING.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, issue and pull-request templates, and sdv-py's dotfiles.

#### Matplotlib family

- `add_logos`, `add_wordmarks`, `add_headshots` and `axis_logos` work on matplotlib Axes, one-Axes Figures and seaborn
  grids (`sdvplot.matplotlib`); `height` is a fraction of the Axes height at any dpi or figure size.
- plotnine: `geom_sdv_logos`, `geom_sdv_wordmarks`, `geom_sdv_headshots`, `axis_logos` and the team color scales
  `scale_color_sdv` / `scale_fill_sdv` (`sdvplot.plotnine`).
- `surface()`: sportypy playing surfaces in team colors, the port of sdvplotR's `sdv_surface()`.
- plottable `logo_column` and `headshot_column` (`sdvplot.plottable`, new `[plottable]` extra).
- The adapter contract (`sdvplot.testing`) now covers wordmarks, headshots, axis logos and alpha (rules 0-8).

#### Tables, wave A (marks and team identity)

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

#### Table themes

- The 18 sdvplotR table themes for great_tables, with sdvplotR's names, arguments and defaults
  (`sdvplot.great_tables`): `gt_theme_almanac`, `gt_theme_athletic`, `gt_theme_booktabs`, `gt_theme_broadsheet`,
  `gt_theme_brutalist`, `gt_theme_drench`, `gt_theme_gtutils`, `gt_theme_kenpom`, `gt_theme_midnight`, `gt_theme_ncaa`,
  `gt_theme_pl`, `gt_theme_savant`, `gt_theme_scoreboard`, `gt_theme_sofa`, `gt_theme_swiss`, `gt_theme_terminal`,
  `gt_theme_tier` and `gt_theme_tufte`, each with `density="comfortable" | "compact" | "social"`.
- `pal_midnight`: sdvplotR's five-color rank palette for dark grounds (every step clears 4.5:1 on midnight and terminal).
- `gt_theme_preview()`: the same rows in every theme, as `{theme name: GT}`.
- Theme fonts load every weight from Google Fonts, over gt's fallback stack.

#### Tables wave C1 (cell styling and formatting)

- 17 sdvplotR cell helpers in `sdvplot.great_tables`, with R's names and arguments: `gt_538_caption`,
  `gt_bold_rows`, `gt_border_bars_bottom`, `gt_border_bars_top`, `gt_border_grid`, `gt_color_pills`,
  `gt_color_ranks`, `gt_color_results`, `gt_column_subheaders`, `gt_cutline`, `gt_delta`, `gt_fmt_rank`,
  `gt_fmt_tally`, `gt_group_stripes`, `gt_highlight_cells`, `gt_highlight_na` and `gt_indicator_boxes`. They take
  tables built from pandas or polars data.
- `gt_color_pills` and `gt_color_ranks` record their color scale for `gt_legend_continuous`.
- `docs/PARITY_TABLES.md` lists where they differ from R.

#### Tables, wave D (image export and composition)

- `sdvplot.great_tables`: `gt_save_crop`, `gt_social_crop` and `gt_save_batch` save tables as trimmed, padded images
  (great_tables' `GT.gtsave`, headless Chrome); `gt_grid` and `gt_stack_tables` compose several tables into one HTML
  block or image. Ports of the sdvplotR functions of the same names; differences are in `docs/PARITY_TABLES.md`.
- `[tables]` names `htmltools` and `nokap`, which great_tables 1.0 already installs. Saving needs Chrome or Chromium
  (set `CHROME_PATH` for a non-standard install); no selenium.

#### Web family

- `add_logos`, `add_wordmarks`, `add_headshots` and `axis_logos` work on Plotly figures (`sdvplot.plotly`; sdvplot
  pins the axis ranges so `height` is a fraction of the plot area) and Altair charts (`sdvplot.altair`, plus the
  native `logo_layer`).
- `add_logos`, `add_wordmarks` and `add_headshots` on Bokeh figures (`sdvplot.bokeh`), HoloViews elements through a
  Bokeh plot hook (`sdvplot.holoviews`) and Folium maps (`sdvplot.folium`, `x` longitude and `y` latitude).
- `embed=True` inlines the images as data URIs, for HTML that renders offline and for static export.
- The `[holoviews]` extra now installs Bokeh 3 as well.

#### Long tail (pygal, Cartopy, gallery compatibility)

- pygal: `add_logos`, `add_wordmarks` and `add_headshots` on XY-family charts (`XY`, `DateTimeLine`, `DateLine`,
  `TimeLine`, `TimeDeltaLine`), drawn in every render; `embed=True` makes SVG and PNG exports work offline;
  `team_style()` colors series by team (`sdvplot.pygal`, new `[pygal]` extra).
- pygal: a deep copy of a chart (`copy.deepcopy`) renders the marks it was copied with, marks added to the copy or to
  the original afterwards stay on that chart, and a chart with marks pickles. Copy with `copy.deepcopy`; a shallow
  copy (`copy.copy`) shares pygal's own series and filters and is not supported.
- Cartopy: the matplotlib adapter's `add_logos`, `add_wordmarks` and `add_headshots` take `transform=` (e.g.
  `ccrs.PlateCarree()` for longitude/latitude, or any matplotlib transform); a `GeoAxes` without it raises
  `ValueError`. A mark whose point falls outside the Axes is not drawn, in any coordinate system.
- `docs/COMPATIBILITY.md`: every package on python-graph-gallery's best dataviz packages list, how it gets marks or
  colors, and the test that proves it (`tests/test_compat_*.py`, new `compat` dependency group); a watch item for
  Reflex XY image marks, re-checked at each release.

#### Tables wave C2 (legends, layout and annotation)

- `sdvplot.great_tables` gains sdvplotR's legend, layout and annotation helpers, with sdvplotR's names and arguments
  on pandas or polars data: `gt_legend_continuous`, `gt_legend_discrete`, `gt_marginalia`, `gt_outliers`,
  `gt_percentile_bar`, `gt_row_accent`, `gt_scale_note`, `gt_set_font`, `gt_significance`, `gt_snake`,
  `gt_snake_align`, `gt_social_tag`, `gt_spotlight`, `gt_tiers`, `gt_title_header`, `gt_watermark`, `gt_wrap_labels`.
- `gt_legend_continuous()` with no arguments draws the scale that `gt_percentile_bar`, `gt_color_ranks` or
  `gt_color_pills` colored with; `gt_legend_discrete()` draws the key `gt_tiers` used.
- `docs/PARITY_TABLES.md` lists every difference from sdvplotR for these functions.

#### Parity extras (court coordinates, images by path, reference lines)

- `sdvplot.court_coords()`: stats.nba.com / stats.wnba.com legacy shot locations (`LOC_X`/`LOC_Y`, `x_legacy`/`y_legacy`)
  to the court frame sportypy and `surface("nba")` draw, on pandas or polars, the port of sdvplotR's
  `sdv_court_coords()`; bit-identical to it on real `shotchartdetail` rows.
- `sdvplot.matplotlib.add_images()` and `sdvplot.plotnine.geom_from_path()`: any image by local path or URL at (x, y),
  sized like the logo verbs, the port of ggpath's `geom_from_path()`; unreadable images are skipped with one warning.
- `sdvplot.plotnine.geom_mean_lines()` and `geom_median_lines()`: per-panel reference lines, the ports of ggpath's,
  matching its values on real data.
- `docs/PARITY.md` maps the remaining sdvplotR exports to sdvplot functions or recipes; `tools/export_parity_extras.R`
  exports the sdvplotR and ggpath oracles the parity tests read.

#### Parity extras (title images, team tiers)

- `title_image()` in `sdvplot.matplotlib` (Axes title or Figure suptitle) and `sdvplot.plotnine` (added with `+`):
  sdvplotR's `ggtitle_image()`, an image beside the title. The image is a team's logo when `league=` is given (an
  unknown team warns once and keeps the title) or any image by URL or local path (one that cannot be read warns once
  and keeps the title); `height` is in points, `side` is `"left"` or `"right"`, and the image and title are aligned
  together as the title is, through later `set_title` calls. A second call on the same title replaces the image.
- `team_tiers()` in `sdvplot.matplotlib` (a Figure) and `sdvplot.plotnine` (a ggplot): sdvplotR's `sdv_team_tiers()`
  tier list on its dark theme, from a pandas or polars frame with `tier_no` and `team` (optional `tier_rank`), with
  `presort`, `tier_desc`, `no_line_below_tier` and `devel=True` (team text, no downloads). One shared preparation
  (`sdvplot._tiers`) ranks, wraps the tier labels and sets the limits for both. The default logo height, 0.1 of the
  panel, is about the largest at which 32 logos in 5 tiers neither overlap nor leave the panel at the default figure size.

### Changed

#### Documentation

- An automation example, `examples/automation/sdvplot_social.py`: social game-day graphics from live ESPN data through
  sportsdataverse-py, for the NFL, college football, NBA, WNBA, MLB and NHL. `leaderboard` makes a season's leaders as
  a great_tables table with headshots and logos; `gameday` makes final-score cards and a player-of-the-game card in
  matplotlib. Images are 1080 x 1080 or 1200 x 675, in team colors with readable ink. With no games or leaders yet it
  falls back to the most recent date or season and says so in the caption. Each run writes a manifest of images, alt
  text, captions and hashtags; `post` publishes it to Bluesky over plain `requests` (a dry-run unless `--post`),
  posting only fresh posts and each one once (a posted-ledger), retrying what is safe to retry.
  With it: a GitHub Actions template to copy (`examples/automation/workflows/sdvplot-social.yml`), a weekly dry-run in
  sdvplot's CI (`.github/workflows/automation-example.yml`, which never posts), offline tests
  (`tests/test_automation_example.py`) and the docs page *Social graphics* (`docs/docs/automation/index.md`).

#### Documentation — example notebooks by section, interactive outputs and the gallery

- `tools/render_notebooks.py` renders every notebook under `examples/notebooks/`, its folder picking the section: the
  top level is "Getting started", then `leagues/` (Tutorials by league), `cookbooks/`, `recipes/` and
  `leaderboards/`, each a sidebar category, beside the hand-written Automation guide. A notebook's
  `metadata["sdvplot"]` (`label`, `position`, `description`, optional per-cell `timeout`) replaces the renderer's
  hard-coded list, and `--only` takes a path such as `leagues/nfl`. A deleted notebook's page and outputs go with it.
- Interactive outputs (Plotly, Vega-Lite, Altair, great_tables, folium, Bokeh, HoloViews, reactable widgets) render
  as standalone pages under `docs/static/outputs/`, shown in iframes that a site client module sizes to their content.
- A gallery page shows every figure tagged `gallery` in a notebook as a thumbnail linked to its example; each render
  writes a per-notebook sidecar, so a partial render keeps the gallery whole (`--gallery-only` rebuilds it).
- The weekly `live-tests-cron` render executes every notebook and publishes every generated path.

### Fixed

#### Adapter contract follow-ups

- plotnine: a faceted plot warns once per render for each reason points are skipped (an unknown team, a missing
  mark), naming the values of every panel, instead of once per panel; `axis_logos` on a faceted plot likewise warns
  once.
- plotnine: `add_logos`/`add_wordmarks` with one season per team draw on a faceted plot (each panel's copy of a
  point keeps its season); the mark geoms take a per-row season as the `season` aesthetic.
- plotnine: the mark geoms leave missing and out-of-limits x/y to plotnine (`na_rm`, scale limits), so a row
  plotnine drops itself no longer also warns `skipped ... missing x or y`.
- plotnine: a point that plotnine copies into every panel (a layer without the facet column) counts once in the
  warning, not once per panel.
- plotnine: drawing no longer swaps the interpreter's warning filters (`warnings.catch_warnings`, not thread-safe)
  to keep the per-panel placement quiet; it uses a private quiet path instead.
- The adapters' test hooks report the height an image was drawn at, not the height they were asked for: matplotlib
  and plotnine measure each image's extent after a draw, pygal renders the chart and reads the SVG, and the axis-logo
  hooks of matplotlib, plotnine, Plotly and Altair report each image's height too.
- `sdvplot.testing.check_adapter_contract` is stricter: a call that skips nothing must not warn and each reason it
  skips points for gives exactly one `SdvplotWarning` (rules 1, 2, 6 and 7); `height` (including its out-of-range
  values) is checked on `add_headshots` and `axis_logos` as well as `add_logos` and `add_wordmarks`, and `alpha` on
  every verb that takes it; heights are compared within 1% of the requested value, as measured by the hooks.
  An out-of-range `height` must raise when the verb is called, not only when the marks are rendered.
  `drawn_axis_marks` now returns `(team_id, tick position, height)`. `check_table_adapter_contract` likewise requires
  no warning for known values and exactly one for all-unknown input.

#### Tables follow-ups

- Muted text (`gt_theme_sdv_team`'s subtitle, the `gt_legend_discrete` subtitle) blends at sdvplotR's exact weights,
  as the table themes already did; a few colors were one step off in a channel.
- A table whose id is the empty string gets a random id before a theme or cell, border or watermark helper scopes CSS
  to it; only `gt_theme_sdv` did this before, and elsewhere the CSS (`# td`) reached no cell.
- Every `sdvplot.great_tables` function refuses raw data with one message ("gt must be a great_tables GT, not
  DataFrame. It looks like raw data: wrap it in great_tables.GT() first."), as sdvplotR's `.check_gt` words it; an
  unknown `density` and an unknown `*_style` key are worded alike across the table modules too, and the style error
  names the argument.
- `gt_sdv_logos`, `gt_sdv_wordmarks` and `gt_sdv_headshots` document exactly which `locations` they take
  (`loc.body()`, `loc.stub()`, `loc.row_groups()`) and raise `ValueError` for any other: column labels used to come out
  as escaped `<img>` text, and a title or source note was silently left alone. `gt_sdv_cols_label` puts marks in the
  column labels.
- A headshot whose ESPN player id was read through a float (pandas stores `[3139477, None]` as floats, so the cell reads
  `3139477.0`) carries `3139477` in its alt text and team attribute, in every adapter; the URL was already right.
- `gt_theme_preview(n=...)` takes only a positive whole number of rows (numpy integers included); 0, negative numbers,
  booleans, floats and strings raise `ValueError` instead of showing no rows, all but the last, one row or a polars
  error.
- A table theme swaps out the fonts an earlier sdvplot theme put in front of the table's fonts instead of stacking on
  them: a table themed twice no longer lists every font twice, and a second theme no longer keeps the first one's font
  as its fallback (with `gt_theme_sdv`, directly behind Lato). Fonts you set with `opt_table_font()` stay, behind the
  theme's, as in sdvplotR. `gt_theme_sdv` and `gt_theme_sdv_team` fall back to gt's `default_fonts()`, as sdvplotR's
  do.
- A translucent `#rgba`/`#rrggbbaa` color is refused (`ValueError`) where sdvplot draws the color it computes (palette
  stops and ramps, legend and tier swatches, theme accents), instead of being drawn solid with its alpha silently
  dropped; an opaque alpha (`f`/`ff`) is accepted and `#rgba` is now read. A color sdvplot passes to CSS as given and
  only measures for its ink (`gt_color_pills(na_color=)`, `gt_indicator_boxes(color_yes=, color_no=, color_na=)`,
  `gt_outliers(fill=)`) is still drawn translucent, and its ink is now read on the color it shows over the table
  background rather than on the color with its alpha dropped. `reactable_sdv_team_color_bg` still replaces
  `na_color`'s alpha with its own `alpha`, as sdvplotR does; CSS-only color arguments take any CSS color.
- A translucent table background (`tab_options(table_background_color="#111111CC")`) is read as the color it shows
  over the page when `gt_legend_discrete` and `gt_marginalia` pick their ink, so a near-black one gets light text.

#### Content findings (team index, team tiers, surface)

- MLB historical codes are season-dated and reach their franchise. A new snapshot, `data-raw/mlbstats_history.csv`
  (the MLB Stats API's teams for every season since 1901; its team ids are franchise ids), dates each abbreviation
  and teamCode by the seasons the API used it. `KCA` is the Kansas City Athletics in 1955-67 and the Royals otherwise
  (the Royals' teamCode `kca` from 1968). `WAS` is the Twins' Senators to 1960, the Rangers' 1961-71 and otherwise the
  Nationals (teamCode `was` from 2005). `PHA`, `BSN`, `BRO`, `NYG`, `SLB`, `WS1`/`WS2`, `MON`, `CAL`, `ANA`, `FLA`
  and `OAK` reach today's team. A teamCode or fileCode is dropped only over seasons that overlap another franchise's
  run of the same abbreviation. Baseball-Reference/sportsipy MLB codes now go through that history instead of today's
  team names, which sent the 1901 Milwaukee Brewers (`MLA`) to today's Brewers and the 1872 Washington Nationals to
  today's Nationals; `PHA`, `KCA`, `MLN`, `SEP`, `WSH` (1901-60), `WSA` and the rest now resolve. An ESPN
  abbreviation or sdvplotR key another franchise held first starts the season after it (`MIL` from 1966, `SEA` from
  1970, `WSH` from 1961; sdvplotR's `KCA` from 1968), so `MIL` in 1960 is the Milwaukee Braves.
- `resolve()` without a season reads a reused code as its current holder: the team whose range covers the latest
  season in the index, then any. A season no alias covers falls back the same way before ranges are ignored.
  Measured over every alias of every league, undated and in each season 1870-2026, the only answers that change are
  the MLB eras above; a code only one team ever held, and every other league, answer as before.
- ESPN's college baseball and softball abbreviations resolve. ESPN's teams list gives NC State `NCST` and Missouri
  `MIZZ`, while its per-team endpoint, scoreboards and standings use `NCSU`, `MIZ`, `UCR`, `KENN` and about 120 others;
  a new snapshot, `data-raw/espn_abbrs.csv`, keeps the per-team abbreviations. One the list gives another team stays
  with that team (LSU Alexandria's per-team `LSU`), and one ESPN gives two teams (softball's `CEN`) is left out.
- UFL 2024-25 codes (`BIR`, `ARL`, `MEM`, `MIC`, `SA`, `HOU` for the Roughnecks) and every XFL code (2020, 2023)
  resolve, dated by the seasons ESPN's scoreboards show them (`data-raw/espn_abbrs.csv`), with the names of those
  seasons ("Houston Roughnecks", "Arlington Renegades"). Known gap: ESPN id 126075 was the Houston Roughnecks in
  2024-25, but the archive has only the 2026 Houston Gamblers marks for it, so `logo_url("HOU", "ufl", season=2024)`
  is the Gamblers logo. The archive's Roughnecks mark is the XFL team's (xfl 112648, 2020-23), another league's
  entity, and nothing establishes that the UFL team used it, so it is not wired (`docs/PARITY.md`).
- NHL Utah: `logo_url("UTA", "nhl", season=2025)` (2024-25; NHL seasons are end years) is the Utah Hockey Club's mark
  again, and 2026 on the Utah Mammoth's. The NHL's logo API dates the Mammoth's (team 68) logos from 2024-25, so they
  outranked the Hockey Club's (team 59) one-season marks. A curated range (`data-raw/curated/mark_ranges.csv`, each
  row with its reason) now starts team 68's marks in 2026, and a mark alias's range narrows a manifest row's own range
  instead of only filling an open one (no other archived mark changes).
- Women's college hockey: ESPN's scoreboards use team ids its teams list lacks. A new snapshot,
  `data-raw/espn_unlisted_teams.csv`, keeps them: one whose name and abbreviation are a listed team's is that team's
  second ESPN id (Minnesota State's `24059` resolves to `2364`, not only by name), and any other is a team of its own
  (Delaware, `48`, `DEL`). Men's college hockey adds the teams its scoreboards use that the archive lacks, listed by
  ESPN or not (SUNY Morrisville, `126813`; Maryville, `132633`); the scan reads one month at a time, since a year of
  men's games passes the scoreboard's 1,000-event cap. The archive has no mark for these teams, so their logos are
  `None` with a warning and their colors are flagged `color_source="fallback"`; none is made up.
- `team_tiers()` (matplotlib and plotnine) takes `theme="dark"` (the default, sdvplotR's) or `theme="light"`: dark
  logos such as Ohio State's, Texas A&M's and Penn State's vanished on the fixed dark background. The light theme's
  labels, lines, subtitle and caption meet WCAG contrast on white; sdvplotR has only the dark theme (`docs/PARITY.md`).
- `surface()` no longer floods stderr with "findfont: Font family 'Clarendon-Regular' not found". sportypy numbers
  football fields in Clarendon-Regular, a font it does not ship, so matplotlib logged a warning for every number it
  measured and drew its default font anyway. When Clarendon is not installed, `surface()` asks sportypy for that
  default (DejaVu Sans) by name, through `field_updates`, so the numbers look the same and nothing is logged; process
  logging is untouched, and a `number_font` the caller passes still wins.
- Borders and fills that sdvplot's great_tables helpers draw now show in a notebook too. great_tables' notebook repr
  marks its own cell rules `!important` (`td, th {border-style: none}`, the stub's and row groups' backgrounds), and
  a stylesheet `!important` beats a plain inline style, so `gt_row_accent`'s bars, for one, showed in saved images and
  vanished in Jupyter. Every border and fill the helpers set (`gt_row_accent`, `gt_spotlight`, `gt_border_grid`,
  `gt_cutline`, `gt_group_stripes`, `gt_marginalia`, `gt_snake`, `gt_tiers`, `gt_outliers`, `gt_bold_rows`,
  `gt_color_results`, `gt_highlight_cells`, the team-mark row groups and the themes) is now inline `!important`, through
  one helper.

[Unreleased]: https://github.com/sportsdataverse/sdvplot/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sportsdataverse/sdvplot/releases/tag/v0.1.0

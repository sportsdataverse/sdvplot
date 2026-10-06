<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Changelog](#changelog)
  - [[Unreleased]](#unreleased)
    - [Added](#added)
    - [Changed](#changed)
    - [Fixed](#fixed)
  - [[0.1.0] - 2026-10-05](#010---2026-10-05)
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
      - [Release hardening](#release-hardening)
    - [Changed](#changed-1)
      - [Documentation](#documentation)
      - [Documentation — example notebooks by section, interactive outputs and the gallery](#documentation--example-notebooks-by-section-interactive-outputs-and-the-gallery)
      - [Release hardening](#release-hardening-1)
    - [Fixed](#fixed-1)
      - [Adapter contract follow-ups](#adapter-contract-follow-ups)
      - [Tables follow-ups](#tables-follow-ups)
      - [Content findings (team index, team tiers, surface)](#content-findings-team-index-team-tiers-surface)
      - [Release hardening](#release-hardening-2)
    - [Security](#security)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Changelog

All notable changes to sdvplot are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `teams(league, include_conferences=True)` lists sdvplotR's conference and league rows (its `include_conferences`):
  the 89 college conferences of cfb, mbb and wbb and the AFC, NFC and NFL, with `program` `"conference"` or `"league"`,
  the conference's short name as `team_id` and `abbr`, cbbplotR's colors (`color_source` `"cbbplotR"`) and the
  `conference_id` the league's teams carry. The default lists teams only, and `resolve()` and `palette()` never
  answer a conference key, so no existing call changes. Index-only for now: the archive has no conference marks yet.
- Headshots by the league's own player id: `id_system="league"` (sdvplotR's `id_type = "league"`) on `headshot_url`
  and every headshot helper (`add_headshots` on every adapter, `geom_sdv_headshots`, `gt_sdv_headshots`,
  `gt_sdv_cols_label(mark_type="headshot")`, `reactable_sdv_headshots`, `plottable.headshot_column`) draws an NBA or
  WNBA Stats `PERSON_ID` (what nba_api, hoopR and wehoop return), an MLBAM id or an NHL API id from the league's CDN,
  with sdvplotR's URL templates; for the NFL it is the gsis id. `"espn"` stays the default. A league without them is
  an `InputError` naming the ones that have them, and a `DownloadError` from cdn.nba.com or cdn.wnba.com with a 403
  says that those CDNs block datacenter and cloud IPs.
- `surface("fiba")` draws a FIBA court (no team yet).
- `sdvplot.plotnine.scale_color_sdv` and `scale_fill_sdv` take `alpha=`, an opacity applied to the team colors
  (sdvplotR's `alpha`); `na_value` is drawn as given. `scale_colour_sdv` is the British alias sdvplotR and plotnine
  both ship.
- `gt_merge_stack_team_color` takes `background=`, the cell background the bottom line's color is checked against;
  the default reads the table's background, so a theme applied first is taken into account.
- `gt_tiers` takes `alt=`, a function from the image paths or URLs to their alt text. By default a logo the archive
  knows (any `logo_url`) is named by its team and any other image by its file name; the images had no alt text at
  all. The alt comes from the cell's value, so a local file (embedded as a data URI) gets a real name.
- `pitch_coords()` converts soccer event coordinates from Opta / Stats Perform, Wyscout, StatsBomb, UEFA, Impect,
  ESPN and the tracking providers (Tracab, SkillCorner, Second Spectrum, Metrica) to one regulation 105 x 68 m
  frame, piecewise-linearly between pitch landmarks, with `flip` for teams attacking opposite ends. The port of
  sdvplotR's `sdv_pitch_coords()`, matched to 1e-12 on every provider.
- `tools/espn_soccer_y_gate.py`, the measurement behind the ESPN frame's y direction.
- `axis_logos(..., mark_type="headshot")` draws player headshots as axis labels on matplotlib, plotnine, Plotly and
  Altair (the port of sdvplotR's `scale_x_sdv_headshots()` / `scale_y_sdv_headshots()` and `element_sdv_headshot()`):
  the tick labels are read as player ids (`id_system` `"espn"`, which `"auto"` means, `"gsis"` or `"league"`), each headshot
  keeps its own aspect, an unknown id stays as text with one warning, and the adapters without axis logos raise
  `UnsupportedTargetError` as before. `sdvplot.typing.AxisMarkType` is the `Literal` of the three mark types. The
  matplotlib y-axis label pad now grows by the widest image's width, so wordmarks and headshots no longer overlap
  their tick labels' room. The adapter contract (`check_adapter_contract`, rule 7) checks the headshot axis too.

### Changed

- `surface("soccer")` draws a regulation 105 x 68 m pitch by default (it drew sportypy's 120 x 90 m maximum), the
  frame `pitch_coords()` returns; `pitch_updates` still overrides it key by key.
- `gt_merge_stack_team_color` keeps the bottom line readable (sdvplotR #55): the team's primary color when it clears
  4.5:1 contrast (WCAG AA) on the cell background, else the secondary, else the primary darkened (or lightened, on a
  dark table) until it does, so Missouri's gold (1.8:1 on white) reads on a white table and stays gold on a dark one.
  An unknown team's grey goes through the same rule.
- `gt_spotlight(dim_color=)` defaults to `"auto"` (sdvplotR #61): the other rows are dimmed to the table's text
  blended toward its background until it clears 4.5:1 (`#737373` on white), instead of the fixed `#BBBBBB`, which is
  1.9:1 on white and barely dimmer than the text on a dark theme. Pass a color to choose it, or `None` not to dim.
- `team_tiers` (matplotlib and plotnine) takes `variant=`, default `"auto"`: the dark theme now draws the archive's
  dark-background logos (the `"dark"` variant), so dark marks such as the Capitals', the Giants', Penn State's or
  Iowa's no longer fade into the near-black background. A team with no dark mark draws its default one, with no
  warning; the light theme still draws the default logos. Pass `variant="default"` for the old look (sdvplotR's), or
  any variant `add_logos` takes.

### Fixed

- The surfaces cookbook's soccer shot map (§9) placed ESPN shots at twice their distance from goal (ESPN's
  `field_position_x` is a fraction of half the pitch, not of the whole), mirrored the home team's wings, and kept
  ESPN's `(0, 0)` "no location" events. It now scales by 52.5 m, turns the away team half a turn, and drops them.
- Coordinates, teams and seasons accept a `range`: `add_logos(ax, range(1, 8), ...)` raised a `TypeError` that named
  `resolve()` though the bad value was `x`. A container sdvplot cannot read now raises a `TypeError` that names no one
  function: `expected a scalar, list, tuple, range, numpy array or a pandas/polars Series, got dict`.
- NHL `WIN` is season-aware: `resolve("WIN", "nhl", season=1990)` (and NHL team id 33, and the archive's logos of
  those seasons) gives the original Jets' line, today's Utah Mammoth, for the seasons ending 1980-1996, as sdvplotR's
  `resolve_historical_abbr()` does; any other season, or none, gives today's Winnipeg Jets, the relocated Thrashers.
  Every season used to give today's Jets, because the NHL stats API files the 1979-96 team under their franchise.
- `UTRGV`, `TEXAS-RIO GRANDE VALLEY` and `RGV` resolve in college football (ESPN's teams list omits UT Rio Grande
  Valley, 292; its per-team endpoint's `RGV` is now in `data-raw/espn_abbrs.csv`).

## [0.1.0] - 2026-10-05

First release.

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

#### Release hardening

- A deprecation helper, `sdvplot._deprecate` (`deprecate()` and `@deprecated_alias`), and its warning,
  `sdvplot.SdvplotDeprecationWarning` (a `FutureWarning` and a `SdvplotWarning`), with a deprecation policy in
  CONTRIBUTING.md: one minor release of warnings before a removal. Nothing is deprecated yet.
- `id_system` and `strict` wherever a team is resolved, passed to the resolver as `resolve()` takes them:
  `team_colors`, `palette`, `logo_url`, `logo_image`, the great_tables helpers `gt_sdv_logos`, `gt_sdv_wordmarks`,
  `gt_sdv_cols_label` and `gt_merge_stack_team_color` (`gt_theme_sdv_team` takes `id_system`; it is always strict),
  and the reactable helpers `reactable_sdv_logos`, `reactable_sdv_wordmarks`, `reactable_sdv_cols_label`,
  `reactable_sdv_team_color_bar` and `reactable_sdv_team_color_bg`. NHL stats ids need it:
  `team_colors("nhl", [1, 6, 10])` reads them as ESPN ids and returns the Bruins, Oilers and Canadiens without a
  warning, while `team_colors("nhl", [1, 6, 10], id_system="nhl_id")` gives the Devils, Bruins and Leafs.
  `gt_sdv_cols_label`'s `id_system` now defaults to None: "auto" for logos and wordmarks, "espn" for headshots.
  `team_colors`'s `which` is typed `Which`, so `which="secondry"` is a type error, as it is for `palette`.
- `sdvplot.typing`: the `Literal` types of the closed argument vocabularies (`IdSystem`, `HeadshotIdSystem`, `Which`,
  `MarkType`), for annotating code that keeps an argument in a variable (`which: Which = "primary"`).

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

#### Release hardening

- `sdvplot.plotnine.scale_color_sdv` / `scale_fill_sdv` take `which`, `season` and `na_value` by keyword only (as
  `palette()` and `team_colors()` do), and they and `sdvplot.pygal.team_style` take `id_system` and `strict`:
  `scale_color_sdv("nhl", id_system="nhl_id")` reads NHL stats ids, which `"auto"` reads as ESPN ids and colored as
  other teams without a word. A season before the league's first is reported with the league's own range in the first
  error (`season 1850 ... for nfl (1920 to ...)`), not the index's and then the league's on a retry.

- Team colors for the 3,636 teams that had only placeholder colors: all of soccer, MiLB, cricket, the HockeyTech
  leagues, college hockey, the PHF, AAF, USFL and XFL, and the college teams ESPN's lists give none. 2,270 now carry
  ESPN's colors (`color_source="espn"`): its per-team endpoint by ESPN id, and for a college team its school's colors in
  another ESPN sport, through the same school id at the same location or, for college baseball and softball (which
  number their teams apart from the school), a unique exact name and location. The other 1,364 carry the two dominant
  colors of their archived logo, flagged `color_source="logo"` because no source publishes them (`teamcolors` was
  surveyed and not used: GPL data from 2020 that adds 5 teams). Two scoreboard-only men's college hockey teams, with no
  logo and no ESPN color, keep a fallback. ESPN's stand-in colors (black alone, or black with its stock red) no longer
  count as a team's: 417 college teams that showed them now show their school's ESPN colors (119) or their logo's
  (298). A secondary equal to its primary is dropped (5 teams). `tools/fetch_sources.py --colors-only` refreshes the
  two new snapshots, `data-raw/espn_colors.csv` and `data-raw/logo_colors.csv`.

- The `sdvplot.great_tables` helpers take their options by keyword only: past the table and the columns (or the
  other leading "what" arguments: `gt_delta(gt, from_, to)`, `gt_highlight_cells(gt, columns, condition)`,
  `gt_significance(gt, columns, p_columns)`, `gt_tiers(gt, levels, colors)`, `gt_save_batch(data, group, fn, file)`,
  `gt_save_crop(data, file)`, `gt_title_header(gt, title)` and so on) every argument is keyword-only, so a later
  release can add an option without rebinding a positional value. No public function of sdvplot or its submodules
  takes more than four arguments by position (a test keeps it so). Migrate by naming the option:
  `gt_color_pills(gt, "pts", palette=...)`, `gt_save_batch(df, "conf", build, "{group}.png", dir="out")`.
- Documentation: an "Add an adapter" guide for contributors (`docs/docs/adapters/add-an-adapter.md`), a checklist from
  the adapter module to the changelog entry, with a worked example that passes `check_adapter_contract`.
- Documentation: the MBB, WBB and college-hockey tutorials draw their tier lists on `team_tiers(theme="light")`, where
  dark logos (Iowa, West Virginia, Penn State) no longer vanish into the dark background.
- Documentation: the tables cookbook's stripes gotcha says theme order no longer matters (`gt_theme_kenpom` bands
  with a CSS rule) and that stripes cover plain fills only in VS Code and Positron notebooks, and the college softball
  World Series table turns row striping off after `gt_theme_ncaa` (`gt_color_results` fills every row).
- Documentation: every example notebook is re-rendered against the 0.1.0 API. The pages that called a league's
  colors fallbacks (the colors tutorial and cookbook; cricket, MLB, NBA, PWHL, soccer, spring football, college
  hockey; the rank bump chart) now say where the index's colors come from (`color_source` `espn` or `logo`); the WNBA
  tier list ranks teams within each tier, so its logos no longer overlap; the cache page lists `urlimages/` and the
  current `versions()` output. The docs pages' Python examples run offline in the test suite, which checks every
  output their comments show. The social-graphics workflow template pins a current sdvplot commit.
- The social-graphics example (`examples/automation/sdvplot_social.py`) covers men's and women's college basketball
  (`--league mbb` / `wbb`, hashtags CBB and WCBB). Both keep NCAA Division I only, as ESPN's group 50 (checked by
  name): leaderboards read that group's own leaders, since ESPN's league-wide college leaders are mostly Division II,
  III and NAIA players on teams the index does not hold, and score cards keep games between two of its teams.
- Documentation: "The adapter contract" page follows `sdvplot.testing` again: rules 0 to 8 (exactly one warning per
  skip reason, `height` and `alpha` checked on every verb when called, drawn heights measured within 1%), the axis
  hooks `_drawn_axis_marks` (`(team_id, tick, height)`) and `_visible_axis_labels`, the table harness's rules T0 to T6,
  and a minimal adapter that passes the current harness.
- API reference: one page per public submodule (`sdvplot.matplotlib`, `sdvplot.plotnine`, `sdvplot.plotly`,
  `sdvplot.altair`, `sdvplot.bokeh`, `sdvplot.holoviews`, `sdvplot.folium`, `sdvplot.pygal`, `sdvplot.great_tables`,
  `sdvplot.reactable`, `sdvplot.plottable`, `sdvplot.testing`, `sdvplot.typing`), with a section per public name in the
  top-level pages' format (signature, arguments, returns, raises, example, see also). Only the 17 top-level functions
  had pages, so `gt_theme_athletic` or any adapter-only function was on none.
- The docstring gate (`tools/gen_docs.py --check`) finds the public submodules itself, as `tests/test_api.py` does,
  instead of reading a list a new submodule could be left off; a new one also fails until it has a reference page.
- The submodule examples run on a seeded cache (a logo and wordmark for every NFL team, the examples' headshots and
  images) instead of an empty one, so the 32 that stopped at their first download now run to the end: an error after
  the first mark lookup no longer passes. Only the four that render through a headless browser stay tolerated.
- Release: a release run refuses a README without a PyPI install line (it becomes the version's PyPI page), a
  CHANGELOG without a dated heading for the tag, or entries left under `[Unreleased]`
  (`tests/test_repo_files.py::test_the_tagged_release_is_ready`). The dist is built in its own job from a fresh
  checkout after the tests pass, with no uv cache from other workflows, a pinned uv and no persisted credentials; the
  docs deploy (which holds `contents: write`) pins its actions by commit SHA.
- CI: the built wheel is installed with no extras and its core is exercised (3.10 and 3.14), then every public
  submodule is imported with `[all]`; the offline suite runs on 3.10 through 3.13; pytest runs with `--strict-markers`
  and `--strict-config`. Python 3.14 is a declared classifier. A run on `main` is never cancelled by a later push (only
  a PR's is), and the live network tests run on manual dispatch and weekly in `live-tests-cron`, not on every push.
- Repeated lookups are faster: with everything cached, `logo_url` takes about 0.1 ms per call instead of 2.5 ms, and
  `logo_image` about 1 ms instead of 4 ms (most of it the copy of the image the caller gets). A cached file within
  its TTL is remembered for the session instead of having its metadata re-read on every call, the bundled index's
  directory is looked up once, and each team's marks are taken from the manifest once per manifest load.
- The matplotlib-family adapters (matplotlib, seaborn, plotnine, plottable, `title_image`) keep a mark in memory no
  bigger than they draw it, 512 px tall. Half of the logo archive is 4096 px: each such mark held 64 MiB, a quarter of
  the decoded-image cache, so a few of them pushed out everything else and every plot decoded them again (about 0.5 s
  each). Now a repeated `add_logos` with a 4096 px mark takes about 0.02 s instead of 0.5 s; the first one still pays
  the decode.
- Documentation: `sdvplot.matplotlib.add_images` and `title_image`, and `sdvplot.plotnine.geom_from_path` and
  `title_image`, say an image URL must be https. They said "http or https", but an http URL is refused with
  `UnsafeDownloadError`.
- Documentation: every public function's docstring names the error classes the code can raise since the API freeze:
  `InputError` for the shared checks (heights, alpha, league, id system, season, variant; it said `ValueError`),
  `UnsupportedTargetError` for a target an adapter cannot draw on (it said `TypeError`), and each download error a
  function can meet (`OfflineError`, `DownloadError`, `IntegrityError`, `UnsafeDownloadError`, `UnsafeCachePathError`,
  and `OptionalDependencyError` for an SVG mark without the `svg` extra), with the ones a plotnine layer, a reactable
  column or a plottable column raises when it is drawn marked as such. The 17 top-level functions' examples now run
  offline in `tests/test_submodule_examples.py`, as the submodules' do. The concept and adapter pages say what the code
  does: the cache's `urlimages/` directory, shared downloads and `UnsafeDownloadError` (not an `OfflineError`);
  `id_system` and `strict` on `palette()`, `team_colors()` and `logo_url()`; the MLB Stats API codes whose team a
  season does change (`KCA`, `WAS`, `SEA`, `MIL`), where the page said no code's did; the libraries each extra installs.
- Issue templates: the bug report asks for the plotting or table library and the league, and takes the whole
  `sdvplot.versions()` output; the feature request lists every top-level function, the submodule helpers, new
  adapters and new leagues; the wrong-team template, now also for wrong colors, picks the league from a list and asks
  for the team id returned and expected, the season and the team's `color_source`. A test keeps those lists equal to
  the leagues, adapters, functions and color sources sdvplot has. The issue chooser links the docs and private
  security reporting.

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

#### Release hardening

- `surface()` draws a rink or court in well under a second instead of 16-19 s: matplotlib's `add_patch` walked every
  segment of sportypy's 10,000-point circle polygons as a Bezier curve to find the data limits (~1.3 M segments per
  rink); for a polygon those limits are its vertices, so they now come from the vertices in one call. The drawn PNG
  and the Axes' data limits are byte-for-byte the same.
- `gt_theme_kenpom` no longer wipes cell fills. Its row bands were `!important` cell fills, so theming a table after
  `data_color`, `tab_style(style.fill(...))` or `gt_color_results` replaced their fills, and a plain fill applied after
  the theme lost to them. The bands are now a table-scoped stylesheet rule on the data rows as drawn (row group
  headings and summary rows are neither counted nor painted), which every cell fill shows over, in either order and in
  the notebook repr (`docs/PARITY_TABLES.md` records the divergence).
- Row striping no longer covers the text color sdvplot's fill helpers draw in VS Code and Positron notebooks. There,
  great_tables' repr marks its whole stylesheet `!important` (Jupyter, Quarto, Databricks and saved files do not), and
  on every other row the stripe's text color beat the plain inline ink that `gt_color_results`, `gt_bold_rows`,
  `gt_tiers`, `gt_spotlight`, `gt_outliers`, `gt_highlight_cells` and `gt_highlight_na` pair with their `!important`
  fills: white text on a dark fill turned the stripe's dark gray. That ink is now `!important` too. `gt_color_ranks`
  fills through great_tables' `data_color`, whose plain fills sdvplot cannot mark, so on a striped table in VS Code or
  Positron it warns once (`SdvplotWarning`) and says to turn striping off with `opt_row_striping(row_striping=False)`.
- A failed logo download raises sdvplot's own errors, never a `requests` exception or a bare `OSError`: an HTTP error
  status (4xx or 5xx) with no cached copy is the new `sdvplot.DownloadError` (an `OfflineError` and an `OSError`), and
  a download whose sha256 does not match the manifest, or an archived file that is not an image, is the new
  `sdvplot.IntegrityError` (a `DownloadError`). A 404 used to escape as `requests.HTTPError`, which
  `except sdvplot.SdvplotError` did not catch. `except OSError` still catches both.
- Every shared input check raises `InputError`, so `except sdvplot.SdvplotError` catches bad input:
  `logo_image(size=...)` takes an int from 1 to 4096 (`size=0` was a `ZeroDivisionError`, `size=-5` a Pillow
  `ValueError`, and `size=2.5` or `size=True` drew a 2x2 or 1x1 image; a size far past 4096 could abort the process in
  the SVG renderer), `suggest(n=...)` an int of at least 1 (`n=-1` was difflib's `ValueError` naming `-3`), a season
  that is not a year (`"2020-21"`, a `pd.Timestamp`) or a season list of the wrong length is an `InputError`, and so
  is an unknown `mark_type` in `reactable_sdv_cols_label` and `gt_sdv_cols_label`.
- `matplotlib.title_image` and `plotnine.title_image` take `height` in points of at least 1: `height=0.1` (a plot
  fraction, as `add_logos` takes) drew a 0.1 pt image without a word, and now raises an `InputError` naming points.
- Importing an adapter submodule without its library (`import sdvplot.plotly` without plotly) raises
  `OptionalDependencyError` naming the extra (`pip install "sdvplot[plotly]"`) rather than a bare
  `ModuleNotFoundError`; the front door had the hint, a direct import did not. `OptionalDependencyError` is now a
  `ModuleNotFoundError` (and still an `ImportError`), so `except ModuleNotFoundError` around the import keeps working.
- The warning (or, with `strict=True`, the error) for an ambiguous team value lists the teams it could mean and what
  picks one: `'Charlotte' (ambiguous: 2429 Charlotte 49ers or 3253 Charlotte Saints); pass season= for a code reused
  across eras, or id_system= for the id system of the values`. It used to say only "ambiguous".
- Docstrings: `matplotlib.add_logos`, `add_wordmarks`, `add_headshots` and `axis_logos` list the
  `UnsupportedTargetError` and `OfflineError` they raise (`add_images` the former), and plotnine's `add_logos` and
  `add_wordmarks` say `season` takes one season or one per point, as they always did.
- A season outside the seasons sdvplot knows for the league is an `InputError` (a `ValueError`) naming the bounds,
  wherever a season is taken. The first season is the league's earliest dated alias in the bundled index (1920 for the
  NFL, 1947 for the NBA, 1997 for the WNBA, 2020 for the XFL; 1871, MLB's, for a league whose history is not dated), the
  last is next year. `logo_url("OAK", "nfl", season=1900)` and `resolve(..., season=20)` used to resolve silently. A
  split season such as `"2020-21"` gets a hint (pass the ending year), and a season of the wrong type (a `pd.Timestamp`)
  is an `InputError` that names `season` rather than the team values.
- A `variant` that no mark in the archive has (a typo, or not a string) is an `InputError` listing the league's
  variants; it used to fall back to the default mark without a word. A variant the team lacks still falls back, as
  before.
- Warnings point at the caller's line: they walk out of sdvplot's frames instead of using fixed `stacklevel`s, which
  named `_colors.py`, `_placement.py` and other sdvplot files whenever the call went through more than one function.
- A misspelled column name is the same `ValueError` on pandas and polars (`column(s) ['teamz'] not in the table; its
  columns are [...]`) in every great_tables helper that takes columns: the `gt_sdv_*` marks (their
  `locations=loc.body(...)` too), `gt_percentile_bar`, `gt_wrap_labels`, `gt_color_pills` and the rest, through the one
  column resolver they share. pandas used to match nothing silently and polars raised its own `ColumnNotFoundError`.
- Threads that ask for the same uncached mark at once (`logo_image()` from a thread pool) download and decode it once:
  the cache runs one fetch per file and the others wait for it, and the decoded-image cache decodes each key once. On
  Windows every thread used to download its own copy, and replacing the file while another thread had it open raised
  `PermissionError: [WinError 5] Access is denied`; the logo manifest's first load warned `could not refresh ...`
  the same way. A replace that another process refuses, over the same content-addressed file it already wrote, is
  no longer an error.
- A long-running session no longer keeps every logo manifest (about 17 MiB parsed) or nflverse player table it has read:
  when the cached file is refreshed, the previous one is freed. `clear_cache()` now also frees the parsed manifest, the
  player table and the per-league tables built from the manifest, as it already freed the decoded images.
- `clear_cache()` unlinks a cache subdirectory that is a symlink in the default cache directory (what it points to is
  untouched) and leaves one alone with a warning in a directory you chose. It used to raise `OSError` from
  `shutil.rmtree` after deleting `manifest/`, leaving the later subdirectories and the in-memory caches as they were;
  the in-memory caches are now emptied even when a removal fails.
- The in-memory cache of decoded images counts bytes per sample: a 16-bit image (mode `I;16`) is two bytes a pixel and
  a 32-bit one (`I`, `F`) four. They were counted at one byte a sample, so they could hold two to four times the
  256 MB budget.

### Security

- Image URLs from the logo manifest (`archive_url`) and from nflverse's player table (`headshot`) must be plain https
  URLs: a host, then only RFC 3986 characters, with no quote, `<`, `>`, whitespace, backslash or control character. A
  manifest row that fails is dropped and a headshot that fails is treated as missing (the player gets their ESPN
  headshot when nflverse has their ESPN id), each with one `SdvplotWarning`. Such a URL used to reach the web adapters
  unchanged, and Altair's HTML export wrote it into a `<script>` block unescaped, so a poisoned manifest or player table
  could run script in an exported page. The web adapters also percent-encode any such character left in an image URL.
- SVG rendering is bounded. An SVG mark is rendered inside a `size` x `size` box (its longest side `size` pixels, at
  most `sdvplot._images.MAX_SIZE`, 4096) after a small probe render measures its aspect ratio. An SVG more than 64 times
  longer than it is wide, or a `size` over 4096, is an `InputError` before anything is rendered. resvg used to render
  at `width=size` first, so a tall SVG or a large `size` asked for gigabytes and could abort the Python process.
- `urllib3>=2.6` is a dependency. `requests>=2.33` still allowed urllib3 1.26 and 2.0 to 2.5, which decompress a
  whole received chunk at once: a 275-byte gzip body cost 4 GB of memory before the download byte cap saw it
  (CVE-2025-66471). The download loop's fallback for urllib3 below 2 is removed.
- A download's 120 s deadline covers the TLS handshake and the response headers, not only the body: a watchdog shuts
  the connection's socket down at the deadline, across every redirect hop, and no single read waits past it. Each read
  had a 60 s timeout of its own, so a server sending a header byte every 59 s held the call open almost indefinitely.
  Through a proxy, the watchdog covers the body only.

[Unreleased]: https://github.com/sportsdataverse/sdvplot/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sportsdataverse/sdvplot/releases/tag/v0.1.0

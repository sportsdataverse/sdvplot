<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Changelog](#changelog)
  - [Unreleased](#unreleased)
    - [Added — core (team identity, colors, logos, cache, adapter contract)](#added--core-team-identity-colors-logos-cache-adapter-contract)
    - [Added — repository standards](#added--repository-standards)
    - [Added — matplotlib family](#added--matplotlib-family)
    - [Added — tables, wave A (marks and team identity)](#added--tables-wave-a-marks-and-team-identity)

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

### Added — tables wave C1 (cell styling and formatting)

- 17 sdvplotR cell helpers in `sdvplot.great_tables`, with R's names and arguments: `gt_538_caption`,
  `gt_bold_rows`, `gt_border_bars_bottom`, `gt_border_bars_top`, `gt_border_grid`, `gt_color_pills`,
  `gt_color_ranks`, `gt_color_results`, `gt_column_subheaders`, `gt_cutline`, `gt_delta`, `gt_fmt_rank`,
  `gt_fmt_tally`, `gt_group_stripes`, `gt_highlight_cells`, `gt_highlight_na` and `gt_indicator_boxes`. They take
  tables built from pandas or polars data.
- `gt_color_pills` and `gt_color_ranks` record their color scale for `gt_legend_continuous`.
- `docs/PARITY_TABLES.md` lists where they differ from R.

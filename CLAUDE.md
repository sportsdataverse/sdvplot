<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [CLAUDE.md — sdvplot Development Guide](#claudemd--sdvplot-development-guide)
  - [Purpose](#purpose)
  - [Layout (`src/sdvplot/`)](#layout-srcsdvplot)
  - [Commands](#commands)
  - [Generated files — never hand-edit](#generated-files--never-hand-edit)
  - [Public API (frozen for 0.1)](#public-api-frozen-for-01)
  - [Identity rules](#identity-rules)
  - [Colors](#colors)
  - [Marks](#marks)
  - [Cache](#cache)
  - [Test gates](#test-gates)
  - [Docstring standard](#docstring-standard)
  - [Release](#release)
  - [Commits](#commits)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# CLAUDE.md — sdvplot Development Guide

## Purpose

`sdvplot` is the Python package of team logos, wordmarks, headshots and colors for plots and tables, from the
SportsDataverse logo archive. It is the counterpart to the R package sdvplotR, and companion to sdv-py. When this
guide differs from `CONTRIBUTING.md` or the tests under `tests/`, those win.

## Layout (`src/sdvplot/`)

| Module | Owns |
| --- | --- |
| `_resolve.py` | `resolve`, `suggest`, the `PRIORITY` id-system order and `EXPLICIT_ONLY` |
| `_index.py`, `_normalize.py` | the bundled team index (`teams()`), value/season normalization |
| `_lazy.py` | `pl`, a stand-in for polars that imports it on first use. Core modules take `pl` from it (`import polars as pl` only under `TYPE_CHECKING`) and import PIL and requests inside the functions that need them, so `import sdvplot` loads none of the three; `tests/test_import_time.py` fails if a module-level import brings one back |
| `_colors.py` | `palette`, `team_colors` |
| `_marks.py`, `_manifest.py` | `marks`, `logo_url`, `select_mark`; the cached logo manifest |
| `_images.py` | `logo_image` (PIL; SVG needs `[svg]`) and the decoded-image cache |
| `_headshots.py` | `headshot_url` (ESPN athlete ids, NFL gsis through nflverse) |
| `_cache.py` | the download cache, `clear_cache`, `key_lock`, and `MEMORY_CACHES`: every in-memory cache of what the cache holds (parsed manifest, decoded images) registers its clear there, so `clear_cache()` frees it |
| `_dispatch.py` | `add_logos`, `add_wordmarks`, `add_headshots`, `axis_logos` and the adapter registry (`register_adapter`) |
| `testing.py` | `check_adapter_contract` and `check_table_adapter_contract`, the shared adapter harnesses |
| `_placement.py` | `Placement`, `place`, `check_height`, `check_alpha`: the step every adapter shares |
| `_tiers.py` | `prepare` and `Tiers`: `team_tiers`' ranking, tier lines, labels and limits, which the matplotlib and plotnine adapters only draw |
| `_contrast.py` | WCAG contrast and readable ink (surfaces, table themes) |
| `matplotlib.py`, `plotnine.py`, `plottable.py` | the adapters (public submodules, named after their library; seaborn goes through `matplotlib.py`) |
| `_web.py` | `HEADSHOT_ASPECT`, `aspect`, `axis_letter`, `image_src`, `image_sources`: what the web adapters share |
| `plotly.py`, `altair.py`, `bokeh.py`, `holoviews.py`, `folium.py` | the web adapters (public submodules) |
| `pygal.py` | the pygal adapter (an xml filter draws the marks at each render) and `team_style` |
| `_surface.py` | `surface` (sportypy) |
| `_court.py` | `court_coords`: stats.nba.com legacy shot coordinates onto sportypy's court (narwhals, so any dataframe) |
| `_tables.py` | `check_px`, `img_tag`, `mark_html`: what the table adapters share (pixel heights, `<img>` markup) |
| `great_tables/` | `sdvplot.great_tables`: `__init__.py` (public names, front-door verbs, test hooks) and one module per table wave: `_marks.py` (marks and team identity, `important()`), `_themes.py`, `_cells.py`, `_layout.py`, `_export.py`; `docs/PARITY_TABLES.md` records each R function's port |
| `great_tables/_themes.py` | the `gt_theme_*` ports and `gt_theme_preview`; reads `GT._options`, `_tbl_data`, `_spanners`, `_styles` (pinned by tests) |
| `great_tables/_cells.py` | the cell styling and formatting helpers (wave C1); the `_sdvplot_scale` record legends read |
| `great_tables/_layout.py` | wave C2: legends (`gt_legend_*`), `gt_percentile_bar`, `gt_tiers`, row emphasis, notes, `gt_snake`; reads the `_sdvplot_scale` / `_sdvplot_key` records |
| `great_tables/_export.py` | `gt_save_crop`, `gt_social_crop`, `gt_save_batch`, `gt_grid`, `gt_stack_tables`: rendering through `GT.gtsave` / nokap, Pillow ports of sdvplotR's magick trim and pad |
| `reactable.py` | the `reactable_sdv_*` column helpers |
| `_errors.py` | `SdvplotWarning`, `SdvplotDeprecationWarning`, `warn` (at the caller's line), the error types and `requires_extra` |
| `_versions.py` | `versions()` |
| `_deprecate.py` | `deprecate` and `@deprecated_alias`: the one way to warn about a rename (CONTRIBUTING's deprecation policy) |
| `_types.py` | the `Literal` aliases of the closed argument vocabularies (`IdSystem`, `HeadshotIdSystem`, `Which`, `MarkType`); `tests/test_types.py` keeps them equal to the runtime sets and is in mypy's `files` |
| `typing.py` | `sdvplot.typing`, the public re-export of those aliases for user annotations (the `numpy.typing` precedent) |

`tools/` holds the generators (`build_index.py`, `fetch_sources.py`, `gen_docs.py`, `render_notebooks.py`,
`home_figures.py`, `hex_logo.py`), the R exports (`export_sdvplotr.R`, `export_parity_extras.R`) and the commit-msg
hook (`hooks/check_commit_msg.py`). `docs/` is the Docusaurus site; outside its pages, `docs/COMPATIBILITY.md` is the
gallery compatibility matrix (kept true by `tests/test_compat_matrix.py`) and `docs/PARITY.md` /
`docs/PARITY_TABLES.md` map sdvplotR's exports. `data-raw/` is the committed input to the index. `examples/` holds the
notebooks and the automation example.

## Commands

The gates, as CI runs them (`quality`, `drift`, `tests`; `docs-build` for the site):

```sh
uv sync --all-extras --all-groups --frozen       # a plain `uv sync` drops the extras: mypy and gen_docs then fail
uv run --frozen ruff check . && uv run --frozen ruff format --check .
uv run --frozen mypy                             # needs the extras; the pre-push hook runs `uv run --all-extras mypy`
uv run --frozen pre-commit run --all-files       # `pre-commit install` refuses when core.hooksPath is set
uv run --frozen python tools/build_index.py --check
uv run --frozen python tools/gen_docs.py --check
uv run --frozen pytest -q --mpl                  # offline, with the image baselines (several minutes)
SDVPLOT_LIVE_TESTS=1 uv run --frozen pytest -q   # plus the network tests
cd docs && npx yarn@1.22.22 install --frozen-lockfile && npx yarn@1.22.22 build   # when a change reaches the site
```

A `uv run` without `--frozen` can re-lock `uv.lock`: check `git diff --quiet origin/main -- uv.lock` before committing,
and never let a lock bump ride into an unrelated commit.

## Generated files — never hand-edit

| File | Regenerate | Check |
| --- | --- | --- |
| `src/sdvplot/data/*` | `uv run python tools/build_index.py` (after `tools/fetch_sources.py` for new sources) | `--check` |
| `data-raw/espn_colors.csv`, `data-raw/logo_colors.csv` | `uv run python tools/fetch_sources.py --colors-only` (network), then rebuild the index | `--check` |
| `docs/docs/reference/**`, `docs/src/data/reference_sidebar.json`, `docs/src/data/home.json` | `uv run python tools/gen_docs.py` | `--check` |
| `docs/docs/{tutorials,cookbooks,recipes,leaderboards}/**` (pages, figures, `_category_.json`), `docs/docs/gallery.md`, `docs/static/outputs/**`, `docs/static/img/gallery/**`, `docs/src/data/gallery/*.json`, `docs/static/notebooks/**` | `uv run python tools/render_notebooks.py` (network; `--only leagues/nfl`; `--gallery-only` after a merge) | `tests/test_notebooks.py` (copies, metadata, gallery) |
| `docs/static/img/home/*.png`, `docs/src/data/home_figures.json` | `uv run python tools/home_figures.py` (network) | `tests/test_home_figures.py` |
| `docs/static/img/sdvplot-logo.png` (the hex, 1036 x 1200), `docs/static/img/favicon.ico` | `uv run python tools/hex_logo.py` (network: the eight logos; starfield and Russo One in `tools/brand/`) | the script asserts the size |
| `docs/src/pages/CHANGELOG.md` | copy of `CHANGELOG.md` (the `sync-docs-changelog` pre-commit hook) | `tests/test_repo_files.py` |
| `data-raw/sdvplotr_*.csv` | `R_ENVIRON_USER=/dev/null Rscript tools/export_sdvplotr.R [path/to/sdvplotR]` | rebuild the index |

Regenerate after changing any source, including a public function's docstring or `__all__`; stale generated files
fail the drift gates. doctoc rewrites a TOC after the changelog hook copies `CHANGELOG.md`: run the hooks until they
pass (sync, doctoc, sync), or `test_docs_changelog_mirrors_the_root_changelog` fails.

Rendering notebooks: `render_notebooks.py` runs each kernel without `VSCODE_PID`, `POSITRON_VERSION`,
`QUARTO_BIN_PATH` and `DATABRICKS_RUNTIME_VERSION` (great_tables picks its notebook CSS by them), so a render from a
VS Code terminal matches the CI cron's. On Windows, run renders with `PYTHONIOENCODING=utf-8`. Never commit a
`--no-execute` render: it replaces the pages with output-free ones.

## Public API (frozen for 0.1)

- `sdvplot.__all__` is the spec in `tests/test_api.py` (`PUBLIC`); each public submodule shows only its `__all__`.
  Adding or removing a public name means changing both, and the reference docs.
- Past the leading "what" arguments (the target and data, a table and its columns, a team and league) every argument
  is keyword-only: put a bare `*` after them. No public function takes more than four positional arguments
  (`test_public_functions_take_at_most_four_positional_arguments`; `POSITIONAL_ALLOWLIST` is empty), and the core
  verbs' positional names are pinned (`POSITIONAL`). The leading arguments are league-first for colors
  (`palette(league, teams)`, `team_colors(league, teams)`, as sdvplotR) and team-first for marks
  (`logo_url(team, league)`).
- Every function that resolves a team takes `id_system` and `strict` and passes them to the resolver
  (`TEAM_RESOLVERS` in `tests/test_api.py`).
- Errors subclass `SdvplotError` and the builtin a caller already catches: `InputError` (ValueError) for the shared
  argument checks (league, id system, color slot, mark type, variant, season, height, alpha, size, counts),
  `UnresolvedTeamError` (with `strict=True`), `OfflineError` / `DownloadError` (an HTTP error status, also an OSError)
  / `IntegrityError` (a sha256 mismatch or an undecodable image), `UnsafeDownloadError`, `UnsafeCachePathError`,
  `OptionalDependencyError` (ModuleNotFoundError, naming the extra; wrap an adapter's library imports in
  `requires_extra`) and `UnsupportedTargetError` (TypeError). A check specific to one helper raises a plain ValueError
  or TypeError. A new error class goes in `_errors.py`, `__all__` and `ERRORS` in `tests/test_api.py`.
- Warn through `sdvplot._errors.warn` (it names the caller's line); a rename goes through `_deprecate`.
- Adapter test hooks stay private (`_drawn_marks`, `_SUPPORTS_AXIS_LOGOS`, `_drawn_cells`, `_rendered_html`).

## Identity rules

- `team_id` is always a string. Never cast a float id to a string, and assert dtypes before joining.
- Never guess: an unknown or ambiguous team gives `None` plus one `SdvplotWarning` (or raises with `strict=True`).
- `"auto"` tries the id systems in `PRIORITY` order (`_resolve.py`); the first system with a candidate decides.
- `nhl_id` is explicit-only (`EXPLICIT_ONLY`): NHL stats ids 1-28 collide with other teams' ESPN ids, so it is
  never tried under `"auto"`.
- A season disambiguates a reused code through the alias ranges; use OAK, SD or STL for relocations. Season bounds are
  the league's own.

## Colors

Each index row carries a `color_source`, by precedence: `nflverse` (nflverse's team table, the NFL), `espn` (ESPN's
teams lists, else `data-raw/espn_colors.csv`, its per-team endpoint, including a college team's school colors from
another ESPN sport), `logo` (the two dominant colors of the team's archived logo, `data-raw/logo_colors.csv`) and
`fallback` (a placeholder from a fixed palette). One source gives both colors (`COLOR_SOURCES` in
`tools/build_index.py`); ESPN's stand-in colors (black alone, black with its stock red) count as none.
`docs/docs/concepts/colors.md` documents the rules.

## Marks

The manifest `entity_id` is per-source, so it never equals a team id. Map through the `mark` id-system aliases (keys
`source:entity_id`, built by `mark_aliases` in `tools/build_index.py`) and never match raw ids. `select_mark` chooses
by variant first, then season within each variant, then source rank.

## Cache

- `key_lock(key)` is the single-flight lock: threads after the same file (`fetch_cached`, `fetch_immutable`) or the
  same decoded image (`_images._decoded_mark`) do the work once, and the rest wait and find it done. Take it around
  any new download or decode that threads can share.
- `fetch_cached` keeps a warm-path memo, `_fresh`: a file found fresh is a dict lookup until its TTL runs out, trusted
  only while `_intact` vouches for it and it still exists. `clear_cache()` empties `_intact` and every
  `MEMORY_CACHES` entry, so a new in-memory cache must register its clear there.

## Test gates

- `SDVPLOT_LIVE_TESTS=1` enables network tests; the default run is offline.
- The `real_index` marker runs a test against the shipped index instead of the hand-written fixture
  (`tests/conftest.py`).
- `pytest_configure` in `tests/conftest.py` turns `SdvplotWarning` into errors; assert expected warnings with
  `pytest.warns`.
- The `render` marker: tests that render through a headless Chrome (Plotly kaleido, great_tables `gtsave`, nokap) or
  vl-convert (Altair) and measure the output. They skip when no browser can start (`SDVPLOT_RENDER_TESTS=1` makes a
  missing Chrome fail the web render tests instead); `-m "not render"` deselects them.
- Repo-only tests: CI also runs the suite from the unpacked sdist, which has no `tools/`, `docs/`, `examples/`,
  `data-raw/`, `.github/` or `CLAUDE.md`. A test module that reads one of them at import goes in `_NEEDS_AT_IMPORT`,
  a test that reads one when it runs in `_NEEDS_AT_RUN` (`tests/conftest.py`); it then skips only where the path is
  absent.
- `_daemon_pipe_readers` in `tests/conftest.py` makes logistro's pipe readers (kaleido's Chrome stderr, through
  choreographer) daemon threads, so a Chrome that will not close cannot hang pytest after its summary. Drop it once
  choreographer closes the pipe in a `finally` (its `browser_async.close` / `browser_sync.close`; 1.4.0 does not).
- great_tables' notebook repr marks every rule of its stylesheet `!important` only under VS Code and Positron
  (`VSCODE_PID`, `POSITRON_VERSION`: `infer_render_env_defaults()["all_important"]`); Jupyter, Quarto, Databricks,
  `as_raw_html()` and the docs pages have none. Agent shells inherit `VSCODE_PID`, so state the env when you measure
  CSS precedence. The `sdvplot.great_tables` helpers write their inline borders and fills (and the text color paired
  with a fill) through `important()`, which wins in every env, and `gt_color_ranks` warns where VS Code or Positron
  stripes would cover its fills (`tests/test_gt_repr_important.py`).

## Docstring standard

Google-style (napoleon) with `Args`, `Returns`, `Raises`, `Example` and `See Also`, linking the reference page.
`uv run python tools/gen_docs.py --check` enforces it for the top level and for every public submodule's `__all__`
functions (the submodules are found with pkgutil; a new one also needs a `MODULE_SECTIONS` group for its reference
page), and checks each submodule Example statically (syntax, undefined names). `tests/test_submodule_examples.py` runs
them offline against a cache seeded with what they draw (`seeded_cache`: every NFL team's logo and wordmark, the
examples' headshots and URL images), with a 20 s limit each; an example that needs more gets it seeded there, and one
that needs a browser is listed in `TOLERATED` with a reason, which never excuses an `AssertionError` or `NameError`.
Polars 1.x API only; ruff line length 120.

## Release

1. PR #50 (first release only) switches the install lines to `pip install sdvplot` and cuts the CHANGELOG: it merges
   just before tagging, because the README is the PyPI page and cannot change for a version once uploaded.
2. Publishing a GitHub Release `vX.Y.Z` runs `release.yml`: the tag must equal the project version; the tests run
   with `SDVPLOT_RELEASE_VERSION` set, so `test_the_tagged_release_is_ready` refuses a README that does not install
   from PyPI, a CHANGELOG without a dated `## [X.Y.Z] - YYYY-MM-DD` heading, or entries left under `[Unreleased]`;
   then the index drift check, a fresh-checkout build, and a smoke test of the bare wheel.
3. `publish-pypi` uploads with Trusted Publishing (OIDC, no stored token) from the `pypi` environment; it is the only
   job with `id-token: write`. `test_the_release_workflow_keeps_its_hardening` pins these guards (SHA-pinned actions,
   no uv cache, a pinned uv, no persisted credentials).

CONTRIBUTING's Release section has the full checklist.

## Commits

Conventional Commits. Never add AI co-author trailers or "Generated with" footers (the commit-msg hook rejects them).
Stage explicit paths (`git add <paths>`), never `git add -A`. Branch and open a PR; do not push to `main`. A
user-visible change gets a bullet under `## [Unreleased]` in `CHANGELOG.md`; never move or date its sections outside a
release.

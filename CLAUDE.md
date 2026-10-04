<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [CLAUDE.md — sdvplot Development Guide](#claudemd--sdvplot-development-guide)
  - [Purpose](#purpose)
  - [Layout (`src/sdvplot/`)](#layout-srcsdvplot)
  - [Commands](#commands)
  - [Generated files — never hand-edit](#generated-files--never-hand-edit)
  - [Identity rules](#identity-rules)
  - [Marks](#marks)
  - [Test gates](#test-gates)
  - [Docstring standard](#docstring-standard)
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
| `_resolve.py` | `resolve`, `suggest`, the `PRIORITY` id-system order |
| `_index.py`, `_normalize.py` | the bundled team index (`teams()`), value/season normalization |
| `_colors.py` | `palette`, `team_colors` |
| `_marks.py`, `_manifest.py` | `marks`, `logo_url`, `select_mark`; the cached logo manifest |
| `_images.py` | `logo_image` (PIL; SVG needs `[svg]`) |
| `_headshots.py` | `headshot_url` (ESPN athlete ids, NFL gsis through nflverse) |
| `_cache.py` | the download cache, `clear_cache` |
| `_dispatch.py` | `add_logos`, `add_wordmarks`, `add_headshots`, `axis_logos` and the adapter registry |
| `testing.py` | `check_adapter_contract` and `check_table_adapter_contract`, the shared adapter harnesses |
| `_placement.py` | `Placement`, `place`, `check_height`, `check_alpha`: the step every adapter shares |
| `_contrast.py` | WCAG contrast and readable ink (surfaces, table themes) |
| `matplotlib.py`, `plotnine.py`, `plottable.py` | the adapters (public submodules, named after their library) |
| `_web.py` | `HEADSHOT_ASPECT`, `aspect`, `image_src`, `image_sources`: what the web adapters share |
| `plotly.py`, `altair.py`, `bokeh.py`, `holoviews.py`, `folium.py` | the web adapters (public submodules) |
| `_surface.py` | `surface` (sportypy) |
| `_tables.py` | `check_px`, `img_tag`, `mark_html`: what the table adapters share (pixel heights, `<img>` markup) |
| `great_tables/` | `sdvplot.great_tables`: `__init__.py` (public names, front-door verbs, test hooks) plus one module per table wave (`_marks.py`; later `_themes.py`, `_cells.py`, `_layout.py`, `_export.py`); `docs/PARITY_TABLES.md` records each R function's port |
| `great_tables/_themes.py` | the `gt_theme_*` ports and `gt_theme_preview`; reads `GT._options`, `_tbl_data`, `_spanners`, `_styles` (pinned by tests) |
| `great_tables/_cells.py` | the cell styling and formatting helpers (tables wave C1); the `_sdvplot_scale` record legends read |
| `great_tables/_export.py` | `gt_save_crop`, `gt_social_crop`, `gt_save_batch`, `gt_grid`, `gt_stack_tables`: rendering through `GT.gtsave` / nokap, Pillow ports of sdvplotR's magick trim and pad |
| `reactable.py` | the `reactable_sdv_*` column helpers |
| `_errors.py`, `_versions.py` | `SdvplotWarning` and the error types; `versions()` |

`tools/` holds the generators (`build_index.py`, `fetch_sources.py`, `gen_docs.py`, `render_notebooks.py`,
`export_sdvplotr.R`). `docs/` is the Docusaurus site. `data-raw/` is the committed input to the index.

## Commands

```sh
uv sync                                     # install with the dev groups
uv run pytest -q                            # offline tests
SDVPLOT_LIVE_TESTS=1 uv run pytest -q       # plus network tests
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pre-commit run --all-files           # `pre-commit install` refuses when core.hooksPath is set
```

`uv run` can re-lock `uv.lock`: check `git status` and never let a lock bump ride into an unrelated commit.

## Generated files — never hand-edit

| File | Regenerate | Check |
| --- | --- | --- |
| `src/sdvplot/data/*` | `uv run python tools/build_index.py` (after `tools/fetch_sources.py` for new sources) | `--check` |
| `docs/docs/reference/**` | `uv run python tools/gen_docs.py` | `--check` |
| `docs/docs/tutorials/**` | `uv run python tools/render_notebooks.py` | none |
| `docs/src/pages/CHANGELOG.md` | copy of `CHANGELOG.md` (pre-commit hook) | tests |
| `data-raw/sdvplotr_*.csv` | `Rscript tools/export_sdvplotr.R` | rebuild the index |

Regenerate after changing any source, including a public function's docstring or `__all__`; stale generated files
fail the drift gates.

## Identity rules

- `team_id` is always a string. Never cast a float id to a string, and assert dtypes before joining.
- Never guess: an unknown or ambiguous team gives `None` plus one `SdvplotWarning` (or raises with `strict=True`).
- `"auto"` tries the id systems in `PRIORITY` order (`_resolve.py`); the first system with a candidate decides.
- `nhl_id` is explicit-only (`EXPLICIT_ONLY`): NHL stats ids 1-28 collide with other teams' ESPN ids, so it is
  never tried under `"auto"`.
- A season disambiguates a reused code through the alias ranges; use OAK, SD or STL for relocations.

## Marks

The manifest `entity_id` is per-source, so it never equals a team id. Map through the `mark` id-system aliases (keys
`source:entity_id`, built by `mark_aliases` in `tools/build_index.py`) and never match raw ids. `select_mark` chooses by variant first, then season within each variant, then source rank.

## Test gates

- `SDVPLOT_LIVE_TESTS=1` enables network tests; the default run is offline.
- The `real_index` marker runs a test against the shipped index instead of the hand-written fixture
  (`tests/conftest.py`).
- `filterwarnings` turns `SdvplotWarning` into errors in tests; assert expected warnings with `pytest.warns`.
- The `render` marker: tests that render through a headless Chrome (Plotly kaleido, great_tables `gtsave`, nokap) or
  vl-convert (Altair) and measure the output. They skip when no browser can start (`SDVPLOT_RENDER_TESTS=1` makes a
  missing Chrome fail the web render tests instead); `-m "not render"` deselects them.

## Docstring standard

Google-style (napoleon) with `Args`, `Returns`, `Raises`, `Example` and `See Also`, linking the reference page.
`uv run python tools/gen_docs.py --check` enforces it. Polars 1.x API only; ruff line length 120.

## Commits

Conventional Commits. Never add AI co-author trailers or "Generated with" footers. Stage explicit paths
(`git add <paths>`), never `git add -A`. Branch and open a PR; do not push to `main`.

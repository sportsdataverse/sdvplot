<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Contributing to sdvplot](#contributing-to-sdvplot)
  - [Development setup](#development-setup)
    - [pre-commit](#pre-commit)
  - [Tests](#tests)
    - [Image baselines](#image-baselines)
    - [Render tests](#render-tests)
  - [Generated files](#generated-files)
  - [Code standards for new modules](#code-standards-for-new-modules)
  - [Notebooks](#notebooks)
  - [Changelog](#changelog)
  - [Deprecation policy](#deprecation-policy)
  - [Commits](#commits)
  - [Documentation and the docs site](#documentation-and-the-docs-site)
  - [Release](#release)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Contributing to sdvplot

`sdvplot` is the Python package of team logos, wordmarks, headshots and colors for the SportsDataverse, the
counterpart to the R package [sdvplotR](https://sdvplotR.sportsdataverse.org/). See the [README](README.md) for an
overview. This document captures the conventions to follow when changing this repository; it mirrors
[sdv-py's](https://github.com/sportsdataverse/sportsdataverse-py/blob/main/CONTRIBUTING.md).

Participation follows the [Code of Conduct](CODE_OF_CONDUCT.md). Report a vulnerability privately, as
[SECURITY.md](SECURITY.md) describes, not in a public issue.

## Development setup

The project uses [uv](https://docs.astral.sh/uv/). Dependencies live in `pyproject.toml` (PEP 621 and PEP 735
dependency groups) and `uv.lock` is committed.

```sh
uv sync --all-extras --all-groups --frozen   # every plotting extra and every dependency group, as CI installs them
```

The groups are `test`, `compat` (the gallery packages `tests/test_compat_*.py` check), `lint`, `docs`, `examples`
(sdv-py, for the notebooks) and `dev`, which includes them all plus pre-commit and nbstripout. Install the extras too:
without the plotting libraries the adapters' types collapse to `Any`, so mypy reports errors CI never sees, and
`tools/gen_docs.py --check` cannot import the adapter submodules.

Commit a regenerated `uv.lock` together with the `pyproject.toml` change that caused it, and nothing else with it: a
`uv run` without `--frozen` can re-lock, so check `git diff --quiet origin/main -- uv.lock` before you commit.

### pre-commit

```sh
uv run pre-commit run --all-files
```

Run `uv run pre-commit install` to run the hooks on every commit; it also installs the commit-msg hook (Conventional
Commits, no AI co-author trailers) and the pre-push mypy hook. It refuses when a global `core.hooksPath` is set (git
then ignores `.git/hooks`); in that case run the command above before you push.
On git older than 2.31, which lacks `ls-files --deduplicate`, run `uv run pre-commit run --files $(git ls-files)`
instead.

## Tests

The gates, as CI runs them (the `quality`, `drift` and `tests` workflows):

```sh
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy                                  # src/sdvplot and tests/test_types.py, against every extra
uv run --frozen pre-commit run --all-files
uv run --frozen python tools/build_index.py --check
uv run --frozen python tools/gen_docs.py --check
uv run --frozen pytest -q --mpl                       # offline, with the image comparisons
SDVPLOT_LIVE_TESTS=1 uv run --frozen pytest -q        # adds the network tests (manual and weekly in CI)
```

The offline suite takes several minutes; `-m "not render"` leaves out the browser render tests. Tests run against a
small hand-written index fixture. A test that needs the shipped index carries the `real_index` marker
(`tests/test_real_index.py`). `SdvplotWarning` is an error in the tests: assert an expected one with `pytest.warns`.

CI also runs the suite on Windows and macOS, at the lowest allowed version of every direct dependency, and from the
unpacked sdist, which ships `src/` and `tests/` but not `tools/`, `docs/`, `examples/`, `data-raw/`, `.github/` or
`CLAUDE.md`. A test that reads one of those must be registered in `tests/conftest.py`: in `_NEEDS_AT_IMPORT` if its
module reads the path while importing, otherwise in `_NEEDS_AT_RUN` by test id. It then skips only where the path is
absent, so the repository still runs it.

### Image baselines

`tests/test_images_baseline.py` compares figures against `tests/baseline/*.png` (pytest-mpl). Only CI's py3.13 offline
job runs `pytest --mpl`; the others skip the comparison, because py3.10 resolves an older matplotlib (3.10.x) whose
image-edge antialiasing differs. The figures carry no text, so the newest matplotlib renders them the same on Linux,
macOS and Windows. After an intended visual change, regenerate with the newest locked matplotlib (any Python 3.11+
environment from the sync above) and look at every changed PNG before committing; a failing CI comparison uploads the
baseline, result and diff images as the `mpl-results-py3.13` artifact:

```sh
uv run pytest tests/test_images_baseline.py --mpl-generate-path=tests/baseline
```

### Render tests

Tests marked `render` draw through a real renderer and measure the output in pixels: `tests/test_web_render.py`
(Plotly through kaleido, Altair through vl-convert), `tests/test_gt_export_render.py` (great_tables `gtsave` and
nokap) and the automation example. kaleido and nokap drive a local Chrome; without one, those tests skip. CI sets
`SDVPLOT_RENDER_TESTS=1`, which turns a missing Chrome in the web render tests into a failure. Run only these with
`uv run pytest -m render`.

`tests/conftest.py` makes the pipe readers kaleido's browser driver starts (logistro threads) daemon threads, so a
Chrome that will not close cannot keep pytest alive after its summary. Remove that patch once choreographer closes the
pipe in a `finally` (its `browser_async.close` / `browser_sync.close`; 1.4.0 does not).

## Generated files

Generated files are never hand-edited. Change the source, regenerate, and commit both.

| Generated file | Regenerate with | Drift check |
| --- | --- | --- |
| `src/sdvplot/data/*` (the bundled index) | `uv run python tools/fetch_sources.py`, then `uv run python tools/build_index.py` | `uv run python tools/build_index.py --check` |
| `data-raw/espn_colors.csv`, `data-raw/logo_colors.csv` (the ESPN per-team and logo-derived colors) | `uv run python tools/fetch_sources.py --colors-only` (network), then rebuild the index | `uv run python tools/build_index.py --check` |
| `docs/docs/reference/**` (API reference), `docs/src/data/reference_sidebar.json`, `docs/src/data/home.json` | `uv run python tools/gen_docs.py` | `uv run python tools/gen_docs.py --check` |
| `docs/docs/{tutorials,cookbooks,recipes,leaderboards}/**` (pages, figures, `_category_.json`), `docs/docs/gallery.md`, `docs/static/outputs/**`, `docs/static/img/gallery/**`, `docs/src/data/gallery/*.json`, `docs/static/notebooks/**` | `uv run python tools/render_notebooks.py` (`--only leagues/nfl` for one notebook; `--gallery-only` rebuilds `gallery.md` after a merge) | `tests/test_notebooks.py` (refreshed weekly by `live-tests-cron`) |
| `docs/static/img/home/*.png`, `docs/src/data/home_figures.json` | `uv run python tools/home_figures.py` (network) | `tests/test_home_figures.py` (refreshed weekly by `live-tests-cron`) |
| `docs/static/img/sdvplot-logo.png` (the hex logo), `docs/static/img/favicon.ico` | `uv run python tools/hex_logo.py` (network) | the script asserts the logo's size |
| `docs/src/pages/CHANGELOG.md` | the `sync-docs-changelog` pre-commit hook copies `CHANGELOG.md` | `uv run pre-commit run --all-files` |
| `data-raw/sdvplotr_*.csv` (sdvplotR export) | `R_ENVIRON_USER=/dev/null Rscript tools/export_sdvplotr.R [path/to/sdvplotR]` | rebuild the index afterwards |

After a `CHANGELOG.md` edit, doctoc can rewrite its TOC after the hook has copied it: run the hooks again until they
pass, or `test_docs_changelog_mirrors_the_root_changelog` fails.

Do not commit a `render_notebooks.py --no-execute` render: it overwrites the rendered pages with output-free ones. The
renderer starts each kernel without `VSCODE_PID`, `POSITRON_VERSION`, `QUARTO_BIN_PATH` and
`DATABRICKS_RUNTIME_VERSION`, which change the CSS great_tables writes, so a render from an IDE terminal matches CI's.
On Windows, set `PYTHONIOENCODING=utf-8` for a render.

## Code standards for new modules

- Python 3.10+, full type hints (`mypy` runs with `disallow_untyped_defs`), ruff with a 120-column limit.
- Team ids are strings. Never cast a float id to a string; fix the dtype at the boundary.
- A new public function lands in `__all__`, in `src/sdvplot/__init__.py` and in the reference docs; a new top-level
  name also goes in `PUBLIC` in `tests/test_api.py`, the spec the public API is checked against. A new public
  submodule gets a reference page by being placed in a `MODULE_SECTIONS` group in `tools/gen_docs.py`.
- Keep the leading "what" arguments positional (the target and data, a table and its columns, a team and league) and
  make every other argument keyword-only with a bare `*`: no public function takes more than four positional
  arguments (`tests/test_api.py` checks every function in every `__all__`). A function that resolves teams takes
  `id_system` and `strict` and passes them to the resolver.
- Give every public function a Google-style docstring with `Args`, `Returns`, `Raises`, `Example` and `See Also`
  sections, and link its reference page. The `uv run python tools/gen_docs.py --check` gate enforces the standard
  and fails when the committed reference differs from the docstrings.
- Warn instead of raising for an unresolved team (`SdvplotWarning`), unless the caller passed `strict=True`. Warn
  through `sdvplot._errors.warn`, which names the caller's line.
- Raise sdvplot's errors, each a `SdvplotError` and the builtin a caller already catches: `InputError` (a ValueError)
  for the shared argument checks (league, id system, color slot, mark type, variant, season, height, alpha, size),
  `UnresolvedTeamError` for `strict=True`, `OfflineError`, `DownloadError` and `IntegrityError` for downloads,
  `UnsafeDownloadError` and `UnsafeCachePathError` for refused ones, `OptionalDependencyError` for a missing extra and
  `UnsupportedTargetError` for an object no adapter takes. A check specific to one helper raises a plain ValueError
  or TypeError.
- New adapters satisfy the contract in `sdvplot.testing` (`check_adapter_contract`). The step-by-step checklist, from
  the module to the changelog entry, is the docs page
  [Add an adapter](https://sdvplot.sportsdataverse.org/docs/adapters/add-an-adapter)
  (`docs/docs/adapters/add-an-adapter.md`).

## Notebooks

Commit notebooks under `examples/notebooks/` without outputs. The `nbstripout` pre-commit hook enforces this; the rendered
pages come from `tools/render_notebooks.py`.

- The folder picks the docs section: the top level is "Getting started", then `leagues/`, `cookbooks/`, `recipes/` and
  `leaderboards/`.
- Each notebook carries `metadata["sdvplot"] = {"label": ..., "position": ..., "description": ...}` (optional
  `"timeout"`, seconds per cell, default 600): its sidebar label, order and page description.
- Tag a figure cell `gallery` (`cell.metadata.tags`, optional `cell.metadata.sdvplot_gallery = {"title", "alt"}`) to put
  its first PNG in the gallery.
- Interactive outputs (Plotly, Altair, great_tables, folium, Bokeh, HoloViews, reactable) render as framed standalone
  pages.

## Changelog

Every user-visible change gets an entry under `## [Unreleased]` in `CHANGELOG.md`, in
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) form: an `### Added`, `### Changed`, `### Deprecated`,
`### Removed`, `### Fixed` or `### Security` group, with a `####` topic heading when the entry needs one. Only a
release moves or dates the sections.

## Deprecation policy

From 0.1.0, a public name, argument or behaviour is not removed or renamed without a deprecation first:

- Keep the old form working and have it warn through `sdvplot._deprecate`: `deprecate(old, replacement=...,
  removal=...)` from inside the old function or branch, or `@deprecated_alias(removal="0.4.0", old="new")` for a renamed
  keyword argument. Both raise `SdvplotDeprecationWarning`, a `FutureWarning` (shown by default) and a
  `SdvplotWarning`, at the caller's line, naming the replacement and the release that removes the old form.
- Warn for at least one minor release before removing: deprecated in 0.3.0, removed no earlier than 0.4.0. From 1.0,
  removals wait for the next major release.
- Each deprecation gets a test that the old form still works and warns once, a `### Deprecated` changelog entry when it
  starts, and a `### Removed` entry when it goes.
- Before 1.0, a change that cannot keep the old form working (a security fix, say) may break without a deprecation; its
  changelog entry says how to migrate.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:` ...). Do not add
AI co-author trailers or "Generated with" footers; the commit-msg hook rejects them. Stage explicit paths, not
`git add -A`.

## Documentation and the docs site

The site is Docusaurus 3 under `docs/` and is published at <https://sdvplot.sportsdataverse.org> by the
`docs-deploy` workflow on each push to `main`; `docs-build` builds it on every pull request that touches `docs/`,
`src/sdvplot/` or `CHANGELOG.md`. Preview it locally, and build it before you push a change the site shows:

```sh
cd docs && npx yarn@1.22.22 install --frozen-lockfile
npx yarn@1.22.22 start    # live preview
npx yarn@1.22.22 build    # what CI runs: it must finish with no new broken links or anchors
```

`docs/docs/intro.md`, `concepts/`, `adapters/` and `automation/` are hand-written; `reference/`, `tutorials/`,
`cookbooks/`, `recipes/`, `leaderboards/` and `gallery.md` are generated.

## Release

1. Re-check the watch list in `docs/COMPATIBILITY.md`: if a newer reflex-xy release documents an image mark or a
   custom glyph, open an issue for a Reflex XY adapter; either way, update the version and date checked there.
2. Bump `version` in `pyproject.toml`, run `uv lock`, and commit `uv.lock` with it (the `drift` workflow fails on a
   stale lock).
3. In `CHANGELOG.md`, move the `## [Unreleased]` entries under a new `## [X.Y.Z] - <date>` heading (and add its link reference) directly below
   an emptied `## [Unreleased]`, which always stays at the top (a test asserts it).
4. Run `cd docs && npx yarn@1.22.22 version:docs X.Y.Z`.
5. First release only: merge the install-line PR (#50: README, intro and quickstart switch to `pip install sdvplot`)
   just before tagging. The README is the PyPI page and cannot be changed for a version once it is uploaded. For 0.1.0,
   step 3 means folding the `[Unreleased]` entries into the existing `## [0.1.0]` section and replacing its
   `Unreleased` with the date; #50 carries that cut too.
6. Publish a GitHub Release `vX.Y.Z`. `release.yml` checks that the tag equals the project version, runs the tests
   with `SDVPLOT_RELEASE_VERSION` set from the tag (so `tests/test_repo_files.py::test_the_tagged_release_is_ready`
   refuses a README that still installs from GitHub, a CHANGELOG without a dated `## [X.Y.Z] - YYYY-MM-DD` heading, or
   entries left under `[Unreleased]`) and the index drift check, builds the sdist and wheel from a fresh checkout, and
   installs the wheel bare to run its core. Then `publish-pypi` uploads with Trusted Publishing (OIDC, no stored
   token) from the `pypi` environment, the only job holding `id-token: write`. A manual run of the workflow builds and
   keeps the artifacts but never publishes. The one-time setup is a pending Trusted Publisher on pypi.org for project
   `sdvplot` (owner `sportsdataverse`, repo `sdvplot`, workflow `release.yml`, environment `pypi`).

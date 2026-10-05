<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [sdvplot Copilot Instructions](#sdvplot-copilot-instructions)
  - [Project Context](#project-context)
  - [Repository Workflow](#repository-workflow)
  - [Commit Convention](#commit-convention)
  - [Public API](#public-api)
  - [Code Style](#code-style)
  - [Tests](#tests)
  - [Generated Files](#generated-files)
  - [Release](#release)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# sdvplot Copilot Instructions

## Project Context

`sdvplot` is the Python package of team logos, wordmarks, headshots and colors for plots and tables
(SportsDataverse), the counterpart to sdvplotR. Source is `src/sdvplot/`; follow `CONTRIBUTING.md`, `CLAUDE.md` and
`tests/` when they differ from this file.

## Repository Workflow

- Use feature branches and pull requests; do not push to `main`.
- Set up with `uv sync --all-extras --all-groups --frozen` (a plain `uv sync` drops the plotting extras, and mypy and
  `tools/gen_docs.py` then fail).
- The gates, as CI runs them: `uv run --frozen ruff check .`, `uv run --frozen ruff format --check .`,
  `uv run --frozen mypy`, `uv run --frozen pre-commit run --all-files`,
  `uv run --frozen python tools/build_index.py --check`, `uv run --frozen python tools/gen_docs.py --check` and
  `uv run --frozen pytest -q --mpl`. A change that reaches the docs site also needs
  `cd docs && npx yarn@1.22.22 install --frozen-lockfile && npx yarn@1.22.22 build`.
- Never let a `uv.lock` change ride into an unrelated commit.

## Commit Convention

Conventional Commits. No AI co-author trailers or "Generated with" footers. Stage explicit paths. A user-visible
change gets a bullet under `## [Unreleased]` in `CHANGELOG.md`.

## Public API

- `sdvplot.__all__` equals `PUBLIC` in `tests/test_api.py`; each public submodule shows only its `__all__`.
- Past the leading arguments (target, data, table, columns, team, league) every argument is keyword-only, and no
  public function takes more than four positional arguments (a test enforces it).
- A function that resolves teams takes `id_system` and `strict` and passes them to the resolver.
- Errors subclass `SdvplotError` and a builtin: `InputError` (ValueError) for the shared argument checks,
  `UnresolvedTeamError`, `OfflineError`, `DownloadError`, `IntegrityError`, `UnsafeDownloadError`,
  `UnsafeCachePathError`, `OptionalDependencyError`, `UnsupportedTargetError`. A helper-specific check raises a plain
  ValueError or TypeError. Warn through `sdvplot._errors.warn`; deprecate through `sdvplot._deprecate`.

## Code Style

- Python 3.10+, full type hints, ruff (120 columns), polars 1.x only.
- Team ids are strings; never cast a float id to a string. Never guess an unresolved team: warn and return `None`.
- Google-style docstrings with `Args`, `Returns`, `Raises`, `Example`, `See Also`; `tools/gen_docs.py --check` enforces
  them for the top level and every public submodule.
- A team's `color_source` is `nflverse`, `espn`, `logo` (derived from its logo, `data-raw/logo_colors.csv`) or
  `fallback` (a placeholder); ESPN's per-team colors are snapshotted in `data-raw/espn_colors.csv`.
- Threads after the same download or decode share it through `sdvplot._cache.key_lock`; a new in-memory cache
  registers its clear in `MEMORY_CACHES`.

## Tests

- Offline by default; `SDVPLOT_LIVE_TESTS=1` enables network tests and the `real_index` marker runs a test against
  the shipped index. `SdvplotWarning` is an error in tests: assert it with `pytest.warns`.
- CI also runs the suite from the unpacked sdist (no `tools/`, `docs/`, `examples/`, `data-raw/`, `.github/`,
  `CLAUDE.md`): register a test that reads one of them in `_NEEDS_AT_IMPORT` or `_NEEDS_AT_RUN` in
  `tests/conftest.py`.

## Generated Files

Never hand-edit `src/sdvplot/data/*` (`tools/build_index.py`), `docs/docs/reference/**`,
`docs/src/data/reference_sidebar.json` and `docs/src/data/home.json` (`tools/gen_docs.py`),
the notebook pages `docs/docs/{tutorials,cookbooks,recipes,leaderboards}/**`, `docs/docs/gallery.md`,
`docs/static/outputs/**`, `docs/static/img/gallery/**`, `docs/src/data/gallery/*.json` and `docs/static/notebooks/**`
(`tools/render_notebooks.py`), `docs/static/img/home/*.png` and `docs/src/data/home_figures.json`
(`tools/home_figures.py`), the hex logo and favicon (`tools/hex_logo.py`) or `docs/src/pages/CHANGELOG.md` (a copy
of `CHANGELOG.md`). Regenerate after changing their sources, including a public docstring or `__all__`.

## Release

A GitHub Release `vX.Y.Z` runs `release.yml`: the tag must match the project version, the tests refuse a README that
does not install from PyPI or an undated CHANGELOG, and `publish-pypi` uploads through Trusted Publishing from the
`pypi` environment. See CONTRIBUTING's Release section.

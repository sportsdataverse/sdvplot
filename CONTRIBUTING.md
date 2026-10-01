<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Contributing to sdvplot](#contributing-to-sdvplot)
  - [Development setup](#development-setup)
    - [pre-commit](#pre-commit)
  - [Tests](#tests)
  - [Generated files](#generated-files)
  - [Code standards for new modules](#code-standards-for-new-modules)
  - [Notebooks](#notebooks)
  - [Changelog](#changelog)
  - [Commits](#commits)
  - [Documentation and the docs site](#documentation-and-the-docs-site)
  - [Release](#release)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Contributing to sdvplot

`sdvplot` is the Python package of team logos, wordmarks, headshots and colors for the SportsDataverse, the
counterpart to the R package [sdvplotR](https://sdvplotR.sportsdataverse.org/). See the [README](README.md) for an
overview. This document captures the conventions to follow when changing this repository; it mirrors
[sdv-py's](https://github.com/sportsdataverse/sportsdataverse-py/blob/main/CONTRIBUTING.md).

## Development setup

The project uses [uv](https://docs.astral.sh/uv/). Dependencies live in `pyproject.toml` (PEP 621 and PEP 735
dependency groups) and `uv.lock` is committed.

```sh
uv sync                       # runtime + the dev groups (test, lint, docs, pre-commit, nbstripout)
uv sync --all-extras          # also install every plotting extra
```

Commit a regenerated `uv.lock` together with the `pyproject.toml` change that caused it.

### pre-commit

```sh
uv run pre-commit run --all-files
```

Run `uv run pre-commit install` to run the hooks on every commit. It refuses when a global `core.hooksPath` is set
(git then ignores `.git/hooks`); in that case run the command above before you push.

## Tests

```sh
uv run pytest -q                           # offline, the default
SDVPLOT_LIVE_TESTS=1 uv run pytest -q      # adds the network tests
uv run ruff check . && uv run ruff format --check .
uv run mypy
```

Tests run against a small hand-written index fixture. A test that needs the shipped index carries the `real_index`
marker (`tests/test_real_index.py`).

## Generated files

Generated files are never hand-edited. Change the source, regenerate, and commit both.

| Generated file | Regenerate with | Drift check |
| --- | --- | --- |
| `src/sdvplot/data/*` (the bundled index) | `uv run python tools/fetch_sources.py`, then `uv run python tools/build_index.py` | `uv run python tools/build_index.py --check` |
| `docs/docs/reference/**` (API reference) | `uv run python tools/gen_docs.py` | `uv run python tools/gen_docs.py --check` |
| `docs/docs/tutorials/**` | `uv run python tools/render_notebooks.py` | none (refreshed weekly by `live-tests-cron`) |
| `docs/src/pages/CHANGELOG.md` | the pre-commit hook copies `CHANGELOG.md` | `uv run pre-commit run --all-files` |
| `data-raw/sdvplotr_*.csv` (sdvplotR export) | `Rscript tools/export_sdvplotr.R [path/to/sdvplotR]` | rebuild the index afterwards |

Do not commit a `render_notebooks.py --no-execute` render: it overwrites the rendered tutorials with output-free pages.

## Code standards for new modules

- Python 3.10+, full type hints (`mypy` runs with `disallow_untyped_defs`), ruff with a 120-column limit.
- Team ids are strings. Never cast a float id to a string; fix the dtype at the boundary.
- A new public function lands in `__all__`, in `src/sdvplot/__init__.py` and in the reference docs.
- Give every public function a Google-style docstring with `Args`, `Returns`, `Raises`, `Example` and `See Also`
  sections, and link its reference page. The `uv run python tools/gen_docs.py --check` gate enforces the standard
  and fails when the committed reference differs from the docstrings.
- Warn instead of raising for an unresolved team (`SdvplotWarning`), unless the caller passed `strict=True`.
- New adapters satisfy the contract in `sdvplot.testing` (`check_adapter_contract`).

## Notebooks

Commit notebooks under `examples/notebooks/` without outputs. The `nbstripout` pre-commit hook enforces this; the rendered
tutorials come from `tools/render_notebooks.py`.

## Changelog

Every user-visible change gets an entry under `## Unreleased` in `CHANGELOG.md`, in sdv-py's
`### Added|Changed|Fixed — <what>` format.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:` ...). Do not add
AI co-author trailers or "Generated with" footers; the commit-msg hook rejects them. Stage explicit paths, not
`git add -A`.

## Documentation and the docs site

The site is Docusaurus 3 under `docs/` and is published at <https://sdvplot.sportsdataverse.org>. Preview it locally:

```sh
cd docs && npx yarn@1.22.22 install && npx yarn@1.22.22 start
```

`docs/docs/intro.md`, `concepts/` and `adapters/` are hand-written; `reference/` and `tutorials/` are generated.

## Release

1. Bump `version` in `pyproject.toml`.
2. In `CHANGELOG.md`, move the `## Unreleased` entries under a new `## X.Y.Z Release: <date>` heading directly below
   an emptied `## Unreleased`, which always stays at the top (a test asserts it).
3. Run `cd docs && npx yarn@1.22.22 version:docs X.Y.Z`.
4. Publish a GitHub Release `vX.Y.Z`; `release.yml` publishes to PyPI after its gates.

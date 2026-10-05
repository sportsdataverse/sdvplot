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
On git older than 2.31, which lacks `ls-files --deduplicate`, run `uv run pre-commit run --files $(git ls-files)`
instead.

## Tests

```sh
uv run pytest -q                           # offline, the default
SDVPLOT_LIVE_TESTS=1 uv run pytest -q      # adds the network tests
uv run ruff check . && uv run ruff format --check .
uv run mypy
```

Tests run against a small hand-written index fixture. A test that needs the shipped index carries the `real_index`
marker (`tests/test_real_index.py`).

### Image baselines

`tests/test_images_baseline.py` compares figures against `tests/baseline/*.png` (pytest-mpl). CI's py3.13 job runs
`pytest --mpl`; the py3.10 job skips the comparison, because py3.10 resolves an older matplotlib (3.10.x) whose
image-edge antialiasing differs. The figures carry no text, so the newest matplotlib renders them the same on Linux,
macOS and Windows. After an intended visual change, regenerate with the newest locked matplotlib (any Python 3.11+
environment from `uv sync`) and look at every changed PNG before committing; a failing CI comparison uploads the
baseline, result and diff images as the `mpl-results-py3.13` artifact:

```sh
uv run pytest tests/test_images_baseline.py --mpl-generate-path=tests/baseline
```

### Render tests

`tests/test_web_render.py` (marker `render`) renders Plotly figures with kaleido and Altair charts with vl-convert, and
measures the logos in pixels. kaleido drives a local Chrome; without one, the Plotly render tests skip. CI sets
`SDVPLOT_RENDER_TESTS=1`, which turns a missing Chrome into a failure. Run only these with `uv run pytest -m render`.

## Generated files

Generated files are never hand-edited. Change the source, regenerate, and commit both.

| Generated file | Regenerate with | Drift check |
| --- | --- | --- |
| `src/sdvplot/data/*` (the bundled index) | `uv run python tools/fetch_sources.py`, then `uv run python tools/build_index.py` | `uv run python tools/build_index.py --check` |
| `docs/docs/reference/**` (API reference), `docs/src/data/reference_sidebar.json`, `docs/src/data/home.json` | `uv run python tools/gen_docs.py` | `uv run python tools/gen_docs.py --check` |
| `docs/docs/tutorials/**`, `docs/static/notebooks/*.ipynb` | `uv run python tools/render_notebooks.py` | `tests/test_notebooks.py` (refreshed weekly by `live-tests-cron`) |
| `docs/static/img/home/*.png`, `docs/src/data/home_figures.json` | `uv run python tools/home_figures.py` (network) | `tests/test_home_figures.py` (refreshed weekly by `live-tests-cron`) |
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

1. Re-check the watch list in `docs/COMPATIBILITY.md`: if a newer reflex-xy release documents an image mark or a
   custom glyph, open an issue for a Reflex XY adapter; either way, update the version and date checked there.
2. Bump `version` in `pyproject.toml`, run `uv lock`, and commit `uv.lock` with it (the `drift` workflow fails on a
   stale lock).
3. In `CHANGELOG.md`, move the `## Unreleased` entries under a new `## X.Y.Z Release: <date>` heading directly below
   an emptied `## Unreleased`, which always stays at the top (a test asserts it).
4. Run `cd docs && npx yarn@1.22.22 version:docs X.Y.Z`.
5. Publish a GitHub Release `vX.Y.Z`; `release.yml` publishes to PyPI after its gates.

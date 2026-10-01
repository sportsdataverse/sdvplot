<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# sdvplot Copilot Instructions

## Project Context

`sdvplot` is the Python package of team logos, wordmarks, headshots and colors for plots and tables
(SportsDataverse), the counterpart to sdvplotR. Source is `src/sdvplot/`; follow `CONTRIBUTING.md`, `CLAUDE.md` and
`tests/` when they differ from this file.

## Repository Workflow

- Use feature branches and pull requests; do not push to `main`.
- Use uv: `uv sync`, `uv run pytest -q`, `uv run ruff check .`, `uv run mypy`.
- Run `uv run pre-commit run --all-files` before pushing.

## Commit Convention

Conventional Commits. No AI co-author trailers or "Generated with" footers. Stage explicit paths.

## Code Style

- Python 3.10+, full type hints, ruff (120 columns), polars 1.x only.
- Team ids are strings; never cast a float id to a string. Never guess an unresolved team: warn and return `None`.
- Google-style docstrings with `Args`, `Returns`, `Raises`, `Example`, `See Also`; `tools/gen_docs.py --check` enforces them.
- Tests are offline by default; `SDVPLOT_LIVE_TESTS=1` enables network tests and the `real_index` marker runs a test
  against the shipped index.

## Generated Files

Never hand-edit `src/sdvplot/data/*` (`tools/build_index.py`), `docs/docs/reference/**` (`tools/gen_docs.py`),
`docs/docs/tutorials/**` (`tools/render_notebooks.py`) or `docs/src/pages/CHANGELOG.md` (copy of `CHANGELOG.md`).
Regenerate after changing their sources.

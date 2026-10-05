## Summary

<!--
Brief explanation of WHAT this PR changes and WHY. Aim for 1-3 sentences in
plain English. Avoid implementation details — those live in the diff.
-->

## Changes

<!-- Bullet list of the substantive changes. -->

-

## Type of change

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change (existing API surface changes)
- [ ] Documentation only
- [ ] Test only
- [ ] Refactor (no behavior change)
- [ ] Tooling / CI / packaging

## Test plan

<!--
How did you verify this works? The gates below are the ones CI runs, after
`uv sync --all-extras --all-groups --frozen`. Live tests are gated by
SDVPLOT_LIVE_TESTS=1; the offline suite passes without it.
-->

- [ ] `uv run --frozen ruff check .` and `uv run --frozen ruff format --check .` clean
- [ ] `uv run --frozen mypy` clean
- [ ] `uv run --frozen pre-commit run --all-files` clean
- [ ] `uv run --frozen python tools/build_index.py --check` reports the index is current
- [ ] `uv run --frozen python tools/gen_docs.py --check` reports the reference is current
- [ ] `uv run --frozen pytest -q --mpl` (offline) passes
- [ ] `SDVPLOT_LIVE_TESTS=1 uv run --frozen pytest -q` passes (if the change touches the manifest, marks, headshots or images)
- [ ] `cd docs && npx yarn@1.22.22 install --frozen-lockfile && npx yarn@1.22.22 build` passes with no new broken links (if the site shows the change)
- [ ] A new test that reads `docs/`, `tools/`, `examples/`, `data-raw/` or `.github/` is registered in `tests/conftest.py` (`_NEEDS_AT_IMPORT` / `_NEEDS_AT_RUN`)
- [ ] `uv.lock` is unchanged, or changed only with the `pyproject.toml` edit that caused it

## Breaking changes

<!-- If "Breaking change" is checked above, describe the migration path. Otherwise: "None." -->

## Documentation

- [ ] `CHANGELOG.md` entry under `## [Unreleased]` (a user-visible change)
- [ ] Docstring(s) updated, and generated files regenerated (`tools/gen_docs.py`, `tools/render_notebooks.py`, `tools/build_index.py`)
- [ ] CLAUDE.md / copilot-instructions.md updated (only if a convention or pattern changes)

## Checklist

- [ ] My code follows the project's [code standards](https://github.com/sportsdataverse/sdvplot/blob/main/CONTRIBUTING.md#code-standards-for-new-modules): options past the leading arguments are keyword-only (at most four positional), errors subclass `SdvplotError`.
- [ ] I have NOT included AI agents (Claude, Copilot, GPT, etc.) as commit co-authors.
- [ ] I have searched existing PRs to confirm this isn't a duplicate.

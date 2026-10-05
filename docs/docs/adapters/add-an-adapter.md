---
title: Add an adapter
sidebar_label: Add an adapter
---

# Add an adapter

This is the checklist for putting sdvplot's marks on a new plotting library. Work through it top to bottom. You do not
need to read `sdvplot/testing.py`: the rules the harness checks are listed in step 5, and
[The adapter contract](contract.md) says what each verb means. The examples use a made-up library called `newlib`,
whose `Canvas` has a `draw_image` method. Swap in your library's names.

The pygal adapter (`src/sdvplot/pygal.py`) is a small real example to read next to this page. For a table library,
read `src/sdvplot/great_tables/` instead and see [Tables](#tables) at the end.

## 1. Write the module

Create `src/sdvplot/<library>.py`, named after the library. It is a public submodule. Import the library at the top of
the module: that import is what tells sdvplot the extra is missing (step 4).

The module exposes these names. The four verbs are its public API: list them in `__all__`, and add
`def __dir__(): return list(__all__)` so `dir()` and tab completion show only them. Everything else (helpers, the
test hooks, constants) starts with an underscore.

| Name | What it is |
| --- | --- |
| `add_logos`, `add_wordmarks` | `(target, x, y, teams, *, league, season=None, height=0.1, alpha=1, variant="default", embed=False, id_system="auto")` |
| `add_headshots` | `(target, x, y, players, *, league, height=0.1, alpha=1, embed=False, id_system="espn")`: no `season`, no `variant` |
| `axis_logos` | `(target, axis, *, league, season=None, height=0.1, variant="default", mark_type="logo", id_system="auto")`: draw logos in place of tick labels; or `(target, axis, **kwargs)` that raises `UnsupportedTargetError` (a `TypeError`), with `_SUPPORTS_AXIS_LOGOS = False` |
| `_drawn_marks` | the test hook (private): `(target) -> list[tuple]` |
| `_SUPPORTS_AXIS_LOGOS` | (private) `False` when `axis_logos` is not supported. The default, when absent, is `True` |

Every `add_*` verb returns the object that was drawn on: the target itself when the library mutates in place, a new
object when it builds one. Give every public function a Google-style docstring with `Args`, `Returns`, `Raises`,
`Example` and `See Also`, as in the other adapters.

## 2. Use `place()` for everything but drawing

`sdvplot._placement` does the work every adapter shares, so the adapter only draws:

- `check_height(height)` returns the height as a float, or raises `ValueError` unless it is in (0, 1]. It is a fraction
  of the plot height.
- `check_alpha(alpha)` returns the opacity as a float, or raises `ValueError` unless it is in [0, 1].
- `place(x, y, teams, *, league, season=None, kind="logo", variant="default", id_system="auto")` returns one
  `Placement` per mark to draw, in input order. It reads `x`, `y` and `teams` by position (a pandas index is ignored),
  resolves the teams, and drops unknown teams and missing `x` or `y` with one `SdvplotWarning` per reason.
  `kind` is `"logo"`, `"wordmark"` or `"headshot"`; for a headshot, `teams` holds player ids.
- A `Placement` has `team_id` (the canonical id), `x`, `y`, `url` (the image), `aspect` (width over height, `None` for
  a headshot) and `mark` (the manifest row, `None` for a headshot).

Call `check_height` and `check_alpha` first, in the verb, so a bad value raises when the verb is called and not later
at render time. The web adapters also share three helpers from `sdvplot._web`: `axis_letter(axis)` (the "x"/"y" check an `axis_logos` verb starts with), `aspect(placement)` (the image's width over
height, with the headshot ratio filled in) and `image_src(placement, embed=False)` (the URL, or a data URI with
`embed=True`).

Here is a complete adapter for `newlib`. One `_add` does the work for the three `add_*` verbs:

```python
"""The newlib adapter: logos, wordmarks and headshots at (x, y) points of a newlib Canvas."""

from __future__ import annotations

from typing import Any

import newlib

from sdvplot._errors import UnsupportedTargetError
from sdvplot._placement import check_alpha, check_height, place
from sdvplot._web import aspect, image_src

_SUPPORTS_AXIS_LOGOS = False

__all__ = ["add_logos", "add_wordmarks", "add_headshots", "axis_logos"]


def __dir__() -> list[str]:
    return list(__all__)


def _add(
    canvas: Any, x: Any, y: Any, teams: Any, *, kind: str, league: str, season: Any, height: float, alpha: float,
    variant: str, embed: bool, id_system: str,
) -> Any:
    if not isinstance(canvas, newlib.Canvas):
        raise UnsupportedTargetError(f"sdvplot.newlib draws on a newlib.Canvas, got {type(canvas).__name__}")
    h, a = check_height(height), check_alpha(alpha)  # raise when the verb is called, not at render time
    placements = place(x, y, teams, league=league, season=season, kind=kind, variant=variant, id_system=id_system)
    for p in placements:  # unknown teams and missing x/y are already gone, with one warning per reason
        canvas.draw_image(p.x, p.y, name=p.team_id, src=image_src(p, embed=embed), height=h, ratio=aspect(p), opacity=a)
    return canvas


def add_logos(
    canvas: Any, x: Any, y: Any, teams: Any, *, league: str, season: Any = None, height: float = 0.1,
    alpha: float = 1, variant: str = "default", embed: bool = False, id_system: str = "auto",
) -> Any:
    """Draw each team's logo at its (x, y) point of a newlib Canvas."""
    return _add(
        canvas, x, y, teams, kind="logo", league=league, season=season, height=height, alpha=alpha,
        variant=variant, embed=embed, id_system=id_system,
    )


def add_wordmarks(
    canvas: Any, x: Any, y: Any, teams: Any, *, league: str, season: Any = None, height: float = 0.1,
    alpha: float = 1, variant: str = "default", embed: bool = False, id_system: str = "auto",
) -> Any:
    """Draw each team's wordmark at its (x, y) point of a newlib Canvas."""
    return _add(
        canvas, x, y, teams, kind="wordmark", league=league, season=season, height=height, alpha=alpha,
        variant=variant, embed=embed, id_system=id_system,
    )


def add_headshots(
    canvas: Any, x: Any, y: Any, players: Any, *, league: str, height: float = 0.1, alpha: float = 1,
    embed: bool = False, id_system: str = "espn",
) -> Any:
    """Draw each player's headshot at its (x, y) point of a newlib Canvas."""
    return _add(
        canvas, x, y, players, kind="headshot", league=league, season=None, height=height, alpha=alpha,
        variant="default", embed=embed, id_system=id_system,
    )


def axis_logos(canvas: Any, axis: str, **kwargs: Any) -> Any:
    """Not supported: newlib has no axis tick labels to replace."""
    raise UnsupportedTargetError("sdvplot.newlib does not draw axis logos")


def _drawn_marks(canvas: Any) -> list[tuple[Any, ...]]:
    """Test hook: (team_id, x, y, height, url) per image on the canvas, in draw order."""
    return [(i["name"], i["x"], i["y"], i["height"], i["src"]) for i in canvas.images]
```

The `_drawn_marks` hook returns one `(team_id, x, y, height)` or `(team_id, x, y, height, url)` tuple per image drawn, in
draw order. Measure `height` from what the library actually holds after the draw (an image's extent, a size in the
emitted spec, the rendered SVG), never from the value you were asked for or stored: the harness exists to catch an
ignored `height`. When the tuple carries a `url`, the harness also checks that it drew the right mark. The harness compares
heights within 1% (relative), which absorbs rounding.

If the library can draw axis logos, set `_SUPPORTS_AXIS_LOGOS = True` (or leave it out), implement `axis_logos`, and add
two more hooks: `_drawn_axis_marks(target, axis) -> list[tuple[str, Any, float]]` (team id, tick position, height, in
tick order) and `_visible_axis_labels(target, axis) -> list[str]` (the tick labels still shown as text). See
`src/sdvplot/matplotlib.py` for a full implementation.

## 3. Register it

Add one line to the end of `src/sdvplot/_dispatch.py`, with the others:

```python
register_adapter(Adapter("newlib", "newlib", "sdvplot.newlib", "newlib"))
```

The four fields are `name` (the display name, for error messages), `package` (the top-level package of the target
object's class: `type(target).__module__.split(".")[0]`), `module` (your adapter module) and `extra` (the pip extra).
`package` is the registry key and the extra can be shared: seaborn registers `package="seaborn"` against
`sdvplot.matplotlib` and the `mpl` extra.

Registering imports nothing. The adapter module loads on the first `sdvplot.add_logos(target, ...)` call whose target
is a `newlib` object, found by walking `type(target).__mro__`, so a subclass of a `newlib` class reaches it too.

## 4. Add the extra and its error

Add the extra to `pyproject.toml`, under `[project.optional-dependencies]`, and add it to the `all` list:

```toml
newlib = ["newlib>=1.0"]
all = ["sdvplot[svg,mpl,...,pygal,newlib]"]
```

Set the floor to a version you tested: CI also installs the lowest allowed versions (`--resolution lowest-direct`).
Then run `uv lock`, and commit `uv.lock` with the change, because the `drift` workflow fails on a stale lock. Check
`git status` after any `uv run`: it can re-lock `uv.lock` on its own.

You do not raise the missing-extra error yourself. Because the adapter imports the library at the top of its module,
the front door catches the `ModuleNotFoundError` and raises `OptionalDependencyError`:

```text
newlib support needs the newlib extra: pip install sdvplot[newlib]
```

It does so only when the missing module is your adapter module, your `package`, or one of its submodules. Any other
`ImportError` inside the adapter is a real bug and propagates unchanged. So keep `import newlib` at module level and
leave other imports to fail loudly.

## 5. Test it with the contract harness

Write `tests/test_<library>.py`. Skip it when the library is not installed, and ask for the cached-image fixtures from
`tests/conftest.py` so the test never touches the network:

```python
import pytest

newlib = pytest.importorskip("newlib")

import sdvplot.newlib as snl  # noqa: E402
from sdvplot.testing import check_adapter_contract  # noqa: E402


def test_the_adapter_passes_the_contract(mark_images, headshot_images):
    check_adapter_contract(snl, make_target=newlib.Canvas)
```

`make_target` builds a fresh, empty target. If the library's empty target renders nothing, make one that holds a point
at the contract's coordinates (as `tests/test_pygal.py` does). If `axis_logos` is supported, also pass
`make_axis_target=lambda categories: ...`, which builds a target whose x axis shows those categories, in order.

`check_adapter_contract(adapter, make_target, *, league="nfl", known=("LV", "LAR"), known_wordmarks=("LV", "LAC"),
players=("3139477", "4241479"), make_axis_target=None)` needs pandas and polars. A broken rule raises an
`AssertionError` whose message starts with `rule N`:

| Rule | What it checks |
| --- | --- |
| 0 | Registration: the front door routes `make_target()` to your module |
| 1 | Resolution: each team is drawn once, as its canonical id, at its own x/y (and its own mark, when you report `url`) |
| 2 | Warn and skip: an unknown team is dropped with its own x/y, with exactly one `SdvplotWarning` per call, never a raise |
| 3 | pandas and polars inputs draw the same marks, even with a non-default pandas index |
| 4 | `height` is the fraction of the plot height actually drawn; `0` and `1.5` raise `ValueError` when the verb is called |
| 5 | Wordmarks follow rules 1, 2 and 4 |
| 6 | Headshots draw player ids at their own x/y, warn once for an unknown id, and follow rule 4 |
| 7 | Axis logos replace known categories in tick order (an unknown one warns once and stays text), or `axis_logos` raises `TypeError` |
| 8 | `alpha` outside [0, 1] raises `ValueError` on every verb that takes it |

The harness uses coordinates that are not row positions (`x=[10, 20]`, `y=[-3, -7]`), so swapped, shared or positional
x and y values fail. Using `place()` passes rules 1, 2, 3 and most of 4 for free; what the harness really tests is
your `_drawn_marks` and your drawing. Add tests of your own for what is specific to the library (units, date axes, a
copy of the target, `embed=True`).

`tests/test_api.py` finds every public submodule itself (`pkgutil`) and checks that `dir()` shows only `__all__` and
that nothing the module defines is public outside it.

## 6. Add the compatibility row

`docs/COMPATIBILITY.md` has a matrix of every library sdvplot works with, and each row names the test that proves it.
Add a row, or for a library that is not on the gallery list, name it in the "also supported" paragraph below the table:

```markdown
| Interactivity | newlib | adapter `sdvplot.newlib` | `tests/test_newlib.py::test_the_adapter_passes_the_contract` |
```

`tests/test_compat_matrix.py` fails when any `tests/test_*.py` file or `::test_name` that the page names does not exist,
so write the test first and copy its name exactly.

Then list the library wherever the others are listed: the extras table and library list in `README.md` and
`docs/docs/intro.md`, the adapter row in `CLAUDE.md`'s layout table, and the list of registered adapters at the top of
[The adapter contract](contract.md).

## 7. Reference docs

The API reference under `docs/docs/reference/` is generated from the public docstrings of the front door
(`add_logos`, `add_wordmarks`, `add_headshots`, `axis_logos` and the rest of `SECTIONS` in `tools/gen_docs.py`). Adapter
modules have no pages of their own, so a new adapter changes nothing there unless you edit one of those docstrings or
`__all__`. Never edit a generated page by hand. Run the generator, then the check, before you push:

```bash
uv run python tools/gen_docs.py
uv run python tools/gen_docs.py --check
```

Only names in `sdvplot.__all__` get a reference page, and the check fails for one that is not placed in a `SECTIONS`
group. Helpers that live in an adapter module, like `team_style` in the pygal adapter, are documented by their
docstrings alone.

## 8. Changelog

Add a line under `## [Unreleased]` at the top of `CHANGELOG.md`, in an `### Added` list:

```markdown
## [Unreleased]

### Added

- newlib: `add_logos`, `add_wordmarks` and `add_headshots` on `newlib.Canvas` (`sdvplot.newlib`, new `[newlib]`
  extra).
```

`## [Unreleased]` must stay the first section (a test asserts it). The pre-commit hook copies `CHANGELOG.md` to
`docs/src/pages/CHANGELOG.md`; commit both.

## Before you open the pull request

```bash
uv run pytest -q
uv run python tools/gen_docs.py --check
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pre-commit run --all-files
```

Use a Conventional Commit message such as `feat(newlib): add the newlib adapter`.

## Tables

A table library has rows, columns and pixel heights instead of points and plot fractions, so it has its own harness,
`check_table_adapter_contract`, with rules T0 to T6. A table adapter's `add_*` verbs take `(table, columns, *, league,
height=<pixels>)` and return the new table. It exposes the hooks `_drawn_cells(table)` (a `(team_id, row, column,
height_px[, src])` tuple per image, in display order) and `_rendered_html(table)`. Steps 3 to 8 are the same. Read
`src/sdvplot/great_tables/` and its tests for a worked example.

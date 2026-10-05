---
title: The adapter contract
sidebar_label: The adapter contract
---

# The adapter contract

An adapter draws sdvplot's marks with one plotting or table library. sdvplot registers adapters for matplotlib,
seaborn, plotnine, great_tables, Plotly, Altair, Bokeh, HoloViews, Folium and pygal, and each meets the contract on
this page. This page is for the people writing a new one; [Add an adapter](add-an-adapter.md) is the step-by-step
checklist. The source of truth is the docstring of `sdvplot.testing`, which holds the harnesses that check it.

## The verbs

Every plot adapter module exposes the same four verbs. Their shared arguments come first; an adapter may add
keyword arguments of its own after them (`embed` for the web adapters, `zorder` and `transform` for matplotlib, `xref`,
`yref` and `layer` for Plotly):

```python
add_logos(target, x, y, teams, *, league, season=None, height=0.1, alpha=1, variant="default", id_system="auto")
add_wordmarks(target, x, y, teams, *, league, season=None, height=0.1, alpha=1, variant="default", id_system="auto")
add_headshots(target, x, y, players, *, league, height=0.1, alpha=1, id_system="espn")
axis_logos(target, axis, *, league, season=None, height=0.1, variant="default", mark_type="logo", id_system="auto")
```

An adapter whose library cannot draw axis logos (Bokeh, HoloViews, folium, pygal) sets `_SUPPORTS_AXIS_LOGOS = False`
and defines `axis_logos(target, axis, **kwargs)`, which always raises `UnsupportedTargetError` (a `TypeError`). A table
adapter (great_tables) takes `(table, columns, *, league, height=30, ...)` instead, with `height` in pixels: see
[Table adapters](#table-adapters).

- `target` is the plot object.
- `x` and `y` are positions in the target's own coordinates. `teams` holds the values to draw. For `add_headshots`,
  `players` holds player ids, `league` picks the ESPN league, and there is no `season` or `variant`.
- `x`, `y` and `teams` can be lists, numpy arrays, or pandas or polars Series. Read them by **position**, never by
  pandas index label.
- `league` and `season` mean what they mean in `resolve()`. `variant` means what it means in `logo_url()`.
- **`height` is a fraction of the plot height**, the same as sdvplotR's `height`. So `0.1` means a tenth of the plot,
  whatever the library or the data range. Every verb raises `ValueError` for `0` and for values above `1`, when it is
  called, not later when the marks are rendered.
- `alpha` is the opacity. Every verb that takes it raises `ValueError` for a value outside 0 to 1.
- `axis_logos` puts images in place of an axis' tick labels, like sdvplotR's `element_sdv_logo`.

Users call the front door, `sdvplot.add_logos(target, ...)` and its siblings. It finds the adapter for `target`'s
library, passes every argument through, and returns what the adapter returns.

## Return the drawn-on object

`add_logos` (and the other verbs) **return the object that was drawn on**:

- the target itself, when the library mutates in place (matplotlib);
- the new object, when the library builds one (plotnine, Altair, great_tables).

The harness reads the test hooks from the returned object when it is not `None`, and from the target otherwise.

## Registering an adapter

The front door keeps a registry keyed by the target library's top-level package name. An entry is an `Adapter` from
`sdvplot._dispatch`:

```python
from sdvplot._dispatch import Adapter, register_adapter

register_adapter(Adapter(name="Plotly", package="plotly", module="sdvplot.plotly", extra="plotly"))
```

| Field | Meaning |
|---|---|
| `name` | the display name, used in error messages |
| `package` | the top-level package of the target's type, such as `"plotly"` |
| `module` | the adapter module, imported on first use |
| `extra` | the pip extra that installs the library |

Dispatch walks `type(target).__mro__` and uses the first class whose top-level package is registered. A user's
subclass of a library class, even one defined in `__main__`, still reaches that library's adapter. For any other
target, the front door raises `UnsupportedTargetError` (a `TypeError`) listing what is supported. The adapter module is
imported lazily:

- If the adapter module or the target library is missing (`ModuleNotFoundError`), the front door raises
  `OptionalDependencyError` naming the extra, for example `pip install sdvplot[plotly]`.
- Any other `ImportError` inside the adapter is a real bug, so it propagates unchanged.

## The test hooks

Every adapter module also exposes test hooks. Their names start with an underscore: an adapter module's public API
is its `__all__` (the verbs and any documented extras), and hooks and helpers stay out of it.

```python
_drawn_marks(target) -> list[tuple]  # (team_id, x, y, height) or (team_id, x, y, height, url)
```

It returns one `(team_id, x, y, height)` or `(team_id, x, y, height, url)` tuple per image the adapter drew, in draw
order:

- `team_id` is the canonical string id (the player id for headshots).
- `x` and `y` are the caller's position values for that image.
- `height` is the fraction of the plot height the image was drawn at, **measured from what was drawn**, never the
  value the adapter was asked for or stored: the image's extent after a draw (matplotlib, plotnine), the size in the
  emitted spec or document (Plotly layout images, Vega-Lite marks, Bokeh and folium sizes), or the rendered SVG
  (pygal). The harness compares heights within 1% (relative), which absorbs pixel and attribute rounding (pygal
  writes three decimals) but not an ignored height or a wrong reference height.
- `url`, when present, is the image source the adapter drew, so the harness can check that it drew the right mark.

An adapter that draws axis logos sets `_SUPPORTS_AXIS_LOGOS = True` (the default when the attribute is absent) and
exposes two more hooks:

```python
_drawn_axis_marks(target, axis) -> list[tuple]   # (team_id, tick position, height), in tick order
_visible_axis_labels(target, axis) -> list[str]  # the tick labels still shown as text
```

`height` is measured as for `_drawn_marks`.

## The contract check

`sdvplot.testing.check_adapter_contract(adapter, make_target, *, league="nfl", known=("LV", "LAR"),
known_wordmarks=("LV", "LAC"), players=("3139477", "4241479"), make_axis_target=None)` runs the shared rules against an
adapter module. `make_target` builds a fresh, empty target; `make_axis_target(categories)` builds a target whose x axis
shows those categories, in order, and is required when the adapter supports axis logos. Every adapter's test suite
calls it, and an adapter must pass it to merge. It needs pandas and polars installed. It uses coordinates that are not
row positions (`x=[10, 20]`, `y=[-3, -7]`), so swapped, shared or positional x/y values fail.

**Warnings are counted per skip reason.** The harness counts the `SdvplotWarning`s of one call plus one read of the
drawn marks (an adapter that resolves at render time, such as plotnine, warns there). A call that skips nothing gives
no warning, and each reason it skips for (unknown teams, unknown player ids, ...) gives **exactly one**, however many
values, layers or marks that reason covers.

A broken rule raises an `AssertionError` whose message starts with `rule N`:

| Rule | What it checks |
| --- | --- |
| 0 | Registration: sdvplot's front door routes `make_target()` to this adapter |
| 1 | Resolution: the canonical ids of the teams passed, at their own x/y (and each team's own mark, when `url` is reported), with no warning |
| 2 | Warn and skip: an unknown team is dropped together with its own x/y, with exactly one `SdvplotWarning` per call (one unknown or several), never a raise |
| 3 | pandas/polars parity: a pandas Series with a non-default index draws the same marks as a polars Series |
| 4 | Height: on every verb (`add_logos` here; rules 5 to 7 for the others), `height` is the fraction of the plot height drawn, measured by the hooks within 1%; `0` and values above `1` raise `ValueError` when the verb is called |
| 5 | Wordmarks: `add_wordmarks` follows rules 1, 2 and 4 |
| 6 | Headshots: `add_headshots` draws player ids at their own x/y, skips an unknown id with exactly one warning, and follows rule 4 |
| 7 | Axis logos: known team categories become images in tick order, an unknown one gives exactly one warning and stays readable text, and the images follow rule 4; without axis support, `axis_logos` raises `TypeError` |
| 8 | Alpha: on every verb that takes `alpha` (`add_logos`, `add_wordmarks`, `add_headshots`, and `axis_logos` when its signature has it), `alpha` outside 0 to 1 raises `ValueError` |

## Table adapters

A table library has rows, columns and pixel heights instead of points and plot fractions, so it gets its own harness,
`sdvplot.testing.check_table_adapter_contract(adapter, make_table, *, league="nfl", known=("LV", "LAR"),
known_wordmarks=("LV", "LAC"), players=("3139477", "4241479"))`, where `make_table(frame)` builds the adapter's table
from a pandas or polars DataFrame (for great_tables, `GT`). A table adapter's `add_*` verbs take
`(table, columns, *, league, height=<pixels>)` and return the new table. It exposes two hooks:

```python
_drawn_cells(table) -> list[tuple]  # (team_id, row, column, height_px[, src]) per image, in display order
_rendered_html(table) -> str        # the table as it renders
```

In `_drawn_cells`, `row` is the 0-based display row of a body cell and `-1` for a column label. A broken rule raises an
`AssertionError` whose message starts with `rule T<n>`:

| Rule | What it checks |
| --- | --- |
| T0 | Registration: the front door routes the table to this adapter |
| T1 | Resolution: a column `["LV", "LAR"]` renders both teams' canonical ids at rows 0 and 1 (and their own marks), with no warning |
| T2 | Warn and keep: `["XXX", "LV"]` renders LV at row 1, keeps `"XXX"` as text, and warns exactly once when called and never when rendered; all-unknown input renders no image and also warns exactly once |
| T3 | pandas/polars parity: a pandas frame with a non-default index renders the same cells as a polars frame |
| T4 | Height: `height=24` is 24 px on every image (`_drawn_cells` reads it from the rendered HTML); `0`, negative, fractional (below 1 px: a plot's unit, not a table's) and non-numeric heights raise `ValueError` |
| T5 | Wordmarks: `add_wordmarks` satisfies T1 to T4 |
| T6 | Headshots: `add_headshots` satisfies T1 to T4 for player ids |

## A minimal adapter

This is the dummy adapter from sdvplot's own tests (`tests/test_dispatch.py`). Its "plot" is a list, drawing appends a
tuple to it, so `_drawn_marks` is just `list`, and it draws no axis logos:

```python
import sys
import types
import warnings

import sdvplot
from sdvplot import SdvplotWarning
from sdvplot._dispatch import Adapter, register_adapter
from sdvplot.testing import check_adapter_contract


class Canvas(list):
    """A pretend plot object from a pretend library called 'fakeplot'."""


Canvas.__module__ = "fakeplot.canvas"


def _check(height, alpha):
    if not 0 < height <= 1:
        raise ValueError("height is a fraction of the plot height")
    if not 0 <= alpha <= 1:
        raise ValueError("alpha is an opacity")


def add_logos(target, x, y, teams, *, league, season=None, height=0.1, alpha=1.0, variant="default"):
    _check(height, alpha)
    # positional values, never index labels; x, y and teams are filtered together
    ids = sdvplot.resolve(list(teams), league, season=season)
    for xi, yi, team_id in zip(list(x), list(y), ids, strict=True):
        if team_id is not None:
            target.append((team_id, xi, yi, height))
    return target


def add_headshots(target, x, y, players, *, league, height=0.1, alpha=1.0):
    _check(height, alpha)
    bad = [p for p in players if not str(p).isdigit()]
    if bad:  # one warning for the whole call, however many ids it skips
        warnings.warn(f"no headshot for {bad}", SdvplotWarning, stacklevel=2)
    for xi, yi, pid in zip(list(x), list(y), list(players), strict=True):
        if str(pid).isdigit():
            target.append((str(pid), xi, yi, height))
    return target


def axis_logos(target, axis, **kwargs):
    raise TypeError("fakeplot draws no axis logos")


adapter = types.ModuleType("fakeplot_adapter")
adapter.add_logos = add_logos
adapter.add_wordmarks = add_logos  # the dummy resolves only, so a wordmark is drawn like a logo
adapter.add_headshots = add_headshots
adapter.axis_logos = axis_logos
adapter._SUPPORTS_AXIS_LOGOS = False
adapter._drawn_marks = list
sys.modules["fakeplot_adapter"] = adapter
register_adapter(Adapter(name="fakeplot", package="fakeplot", module="fakeplot_adapter", extra="fakeplot"))

sdvplot.add_logos(Canvas(), [0], [0], ["LV"], league="nfl")   # [('13', 0, 0, 0.1)]
check_adapter_contract(adapter, make_target=Canvas)           # passes: no AssertionError
```

`resolve()` already warns once about the unknown teams of a call, so the adapter gets rule 2 for free: it must only
keep each surviving team's own x/y. A real adapter measures `height` from what it drew; the dummy can report the value
it was given because appending the tuple is its drawing.

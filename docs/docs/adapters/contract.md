---
title: The adapter contract
sidebar_label: The adapter contract
---

# The adapter contract

An adapter draws sdvplot's marks with one plotting or table library. sdvplot registers adapters for matplotlib,
seaborn, plotnine, great_tables, Plotly, Altair, Bokeh, HoloViews, Folium and pygal, and each meets the contract on
this page. This page is for the people writing a new one.

## The verbs

Every adapter module exposes the same verbs, with the same arguments in every library:

```python
add_logos(target, x, y, teams, *, league, season=None, height=0.1, alpha=1.0, variant="default")
add_wordmarks(target, x, y, teams, *, league, season=None, height=0.1, alpha=1.0, variant="default")
add_headshots(target, x, y, teams, *, league, season=None, height=0.1, alpha=1.0, variant="default")
axis_logos(target, axis, league, ...)
```

- `target` is the plot or table object.
- `x` and `y` are positions in the target's own coordinates. `teams` holds the values to draw. For `add_headshots`, it
  holds player ids, and `league` picks the ESPN league.
- `x`, `y` and `teams` can be lists, numpy arrays, or pandas or polars Series. Read them by **position**, never by
  pandas index label.
- `league` and `season` mean what they mean in `resolve()`. `variant` means what it means in `logo_url()`.
- `alpha` is the opacity, from 0 to 1.
- **`height` is a fraction of the plot height**, the same as sdvplotR's `height`. So `0.1` means a tenth of the plot,
  whatever the library or the data range. Raise `ValueError` for `0` and for values above `1`.
- `axis_logos` puts images in place of an axis' tick labels, like sdvplotR's `element_sdv_logo`. Its remaining
  arguments are settled with the first adapter.

Users call the front door, `sdvplot.add_logos(target, ...)` and its siblings. It finds the adapter for `target`'s
library, passes every argument through, and returns what the adapter returns.

## Return the drawn-on object

`add_logos` (and the other verbs) **return the object that was drawn on**:

- the target itself, when the library mutates in place (matplotlib);
- the new object, when the library builds one (plotnine, Altair, great_tables).

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

## The `drawn_marks` test hook

Every adapter module also exposes a test hook:

```python
drawn_marks(target) -> list[tuple[str, float, float, float]]
```

It returns one `(team_id, x, y, height)` tuple per image the adapter drew, in draw order:

- `team_id` is the canonical string id.
- `x` and `y` are the caller's position values for that image.
- `height` is the fraction of the plot height the adapter **actually** used, not the value it was asked for.

The harness reads `drawn_marks` from the object `add_logos` returned when that is not `None`, and from the target
otherwise.

## The contract check

`sdvplot.testing.check_adapter_contract(adapter, make_target, *, league="nfl", known=("LV", "LAR"))` runs the shared
rules against an adapter module. `make_target` builds a fresh, empty target. Every adapter's test suite calls it, and an
adapter must pass it to merge. It needs pandas and polars installed. It uses coordinates that are not row positions
(`x=[10, 20]`, `y=[-3, -7]`), so swapped, shared or positional x/y values fail.

A broken rule raises an `AssertionError` whose message starts with `rule N`:

1. **Resolution.** Each team is drawn once, as its canonical id, at its own x/y.
2. **Warn and skip.** An unknown team is dropped together with its own x/y, with an `SdvplotWarning`, and never raises.
   All-unknown input draws nothing and still warns.
3. **pandas/polars parity.** pandas Series with a non-default index draw the same marks as polars Series.
4. **Height semantics.** With `height=0.1` and `height=0.25`, every drawn mark has that height. `height=0` and
   `height=1.5` raise `ValueError`.

## A minimal adapter

This is the dummy adapter from sdvplot's own tests (`tests/test_dispatch.py`). Its "plot" is a list, and drawing appends
a tuple to it, so `drawn_marks` is just `list`:

```python
import sys
import types

import sdvplot
from sdvplot._dispatch import Adapter, register_adapter
from sdvplot.testing import check_adapter_contract


class Canvas(list):
    """A pretend plot object from a pretend library called 'fakeplot'."""


Canvas.__module__ = "fakeplot.canvas"


def add_logos(target, x, y, teams, *, league, season=None, height=0.1, alpha=1.0, variant="default"):
    if not 0 < height <= 1:
        raise ValueError("height is a fraction of the plot height")
    # positional values, never index labels; x, y and teams are filtered together
    ids = sdvplot.resolve(list(teams), league, season=season)
    for xi, yi, team_id in zip(list(x), list(y), ids, strict=True):
        if team_id is not None:
            target.append((team_id, xi, yi, height))
    return target


adapter = types.ModuleType("fakeplot_adapter")
adapter.add_logos = add_logos
adapter.drawn_marks = list
sys.modules["fakeplot_adapter"] = adapter
register_adapter(Adapter(name="fakeplot", package="fakeplot", module="fakeplot_adapter", extra="fakeplot"))

sdvplot.add_logos(Canvas(), [0], [0], ["LV"], league="nfl")   # [('13', 0, 0, 0.1)]
check_adapter_contract(adapter, make_target=Canvas)           # passes: no AssertionError
```

`resolve()` already warns about unknown teams, so the adapter gets rule 2 for free. It must only keep each surviving
team's own x/y.

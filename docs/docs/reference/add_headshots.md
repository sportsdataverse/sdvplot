---
title: add_headshots
sidebar_label: add_headshots
sidebar_position: 12
---

# `add_headshots`

```python
add_headshots(target: Any, *args: Any, **kwargs: Any) -> Any
```

Add player headshots to a plot or table of any supported library.

Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. Every
adapter takes the same arguments. For headshots, ``teams`` holds player ids and ``league`` picks the ESPN league.

## Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | The plot or table object. Its type picks the adapter. |
| `*args` | `Any` | Passed to the adapter. By convention ``x``, ``y`` (positions in the target's own coordinates) and ``teams`` (the team values to draw), in that order. |
| `**kwargs` | `Any` | Passed to the adapter: ``league`` (the SDV league key), ``height`` (the headshot's height as a fraction of the plot height), ``alpha`` (opacity, 0 to 1) and ``id_system`` (``"espn"`` or ``"gsis"``, as in ``headshot_url``). Headshots take no ``season`` or ``variant``. |

## Returns

`object` — The drawn-on plot or table: ``target`` itself, or the new object the adapter built.

## Raises

- `UnsupportedTargetError`: If no adapter is registered for ``target``'s library.
- `OptionalDependencyError`: If the adapter's optional extra is not installed.

## Example

```python
import sdvplot

try:
    sdvplot.add_headshots(object(), [0.5], [0.5], ["KC"], league="nfl")
except sdvplot.UnsupportedTargetError:
    pass   # raised: object() is not a plot or table
```

## See also

sdvplotR: https://sdvplotR.sportsdataverse.org/ ; sdv-py: https://py.sportsdataverse.org/

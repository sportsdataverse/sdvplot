---
title: axis_logos
sidebar_label: axis_logos
sidebar_position: 13
---

# `axis_logos`

```python
axis_logos(target: Any, *args: Any, **kwargs: Any) -> Any
```

Replace an axis' team labels with team logos on a plot of any supported library.

Routes to the adapter for ``target``'s library (matplotlib, plotnine, Plotly, Altair, great_tables, ...) and returns
the object that was drawn on: ``target`` itself when the library mutates in place, a new object otherwise. Every
adapter takes the same arguments.

## Arguments

| Name | Type | Description |
|---|---|---|
| `target` | `Any` | The plot or table object. Its type picks the adapter. |
| `*args` | `Any` | Passed to the adapter. By convention ``x``, ``y`` (positions in the target's own coordinates) and ``teams`` (the team values to draw), in that order. |
| `**kwargs` | `Any` | Passed to the adapter: ``league`` (the SDV league key), ``season`` (one season or one per team), ``height`` (the mark's height as a fraction of the plot height), ``alpha`` (opacity, 0 to 1) and ``variant`` (a mark variant, as in ``logo_url``). |

## Returns

`object` — The drawn-on plot or table: ``target`` itself, or the new object the adapter built.

## Raises

- `UnsupportedTargetError`: If no adapter is registered for ``target``'s library.
- `OptionalDependencyError`: If the adapter's optional extra is not installed.

## Example

```python
import sdvplot

try:
    sdvplot.axis_logos(object(), [0.5], [0.5], ["KC"], league="nfl")
except sdvplot.UnsupportedTargetError:
    pass   # raised: this core release has no adapters registered
```

## See also

sdvplotR: https://sdvplotR.sportsdataverse.org/ ; sdv-py: https://py.sportsdataverse.org/

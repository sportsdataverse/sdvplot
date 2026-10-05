"""The Plotly adapter: logos, wordmarks, headshots and axis logos as layout images on a Plotly Figure.

A layout image takes one reference for both its position and its size, so an image placed in data coordinates is sized
in data units: its height is ``height`` times the y axis span. sdvplot pins the axis ranges (with room for the images,
which Plotly clips at the plot edge) so each image is exactly ``height`` of the plot area tall. Axis logos are placed in
paper coordinates, where ``height`` is exact as is.
"""

from __future__ import annotations

import datetime as dt
import math
import re
import warnings
from typing import Any

import plotly.graph_objects as go

from sdvplot._errors import SdvplotWarning, UnsupportedTargetError
from sdvplot._placement import check_alpha, check_height, place
from sdvplot._web import aspect, axis_letter, image_sources

_SUPPORTS_AXIS_LOGOS = True
_PLOTLY_DEFAULT_WIDTH, _PLOTLY_DEFAULT_HEIGHT = 700, 450  # plotly.js's figure size when layout.width/height are unset
_PLOTLY_DEFAULT_MARGIN = {"t": 100, "b": 80, "l": 80, "r": 80}  # plotly.js's margins when unset
_REF = re.compile(r"^([xy])(\d*)$")
_READABLE = ("scatter", "scattergl", "bar")  # trace types whose extent sdvplot can work out

__all__ = ["add_logos", "add_wordmarks", "add_headshots", "axis_logos"]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)


def _figure(target: Any) -> go.Figure:
    if not isinstance(target, go.Figure):  # FigureWidget subclasses Figure
        raise UnsupportedTargetError(
            f"sdvplot.plotly draws on a plotly.graph_objects.Figure, got {type(target).__name__}"
        )
    return target


def _margin(fig: go.Figure, side: str) -> float:
    m = fig.layout.margin[side]
    return float(_PLOTLY_DEFAULT_MARGIN[side] if m is None else m)


def _key(ref: str, letter: str) -> str:
    """'y' -> 'yaxis', 'y2' -> 'yaxis2'."""
    m = _REF.match(ref)
    if m is None or m.group(1) != letter:
        raise ValueError(f"{letter}ref must name a {letter} axis such as {letter!r} or '{letter}2', got {ref!r}")
    return f"{letter}axis{m.group(2)}"


def _traces(fig: go.Figure, letter: str, ref: str) -> list[Any]:
    return [t for t in fig.data if hasattr(t, f"{letter}axis") and (getattr(t, f"{letter}axis") or letter) == ref]


def _vals(trace: Any, letter: str) -> list[Any]:
    """A trace's x or y values as a list (Plotly keeps numpy arrays as they are)."""
    values = getattr(trace, letter)
    return [] if values is None else [v for v in values if v is not None]


def _column(trace: Any, letter: str) -> list[Any]:
    """A trace's x or y values point by point; without them, where Plotly draws it: x0 + i * dx (y0 + i * dy)."""
    values = getattr(trace, letter)
    if values is not None:
        return list(values)
    other = getattr(trace, "y" if letter == "x" else "x")
    start, step = getattr(trace, f"{letter}0"), getattr(trace, f"d{letter}")
    return [(start or 0) + i * (1 if step is None else step) for i in range(0 if other is None else len(other))]


def _unmeasurable(what: str, ref: str, letter: str) -> ValueError:
    return ValueError(
        f"cannot work out the {ref} range of {what}; set it first, "
        f"e.g. fig.update_{letter}axes(range=[lo, hi]), then add the marks"
    )


def _value_kind(v: Any) -> str:
    if isinstance(v, str):
        try:
            float(v)
            return "linear"
        except ValueError:
            pass
        try:
            dt.datetime.fromisoformat(v)
            return "date"
        except ValueError:
            return "category"
    if isinstance(v, dt.date) or type(v).__name__ in ("Timestamp", "datetime64"):
        return "date"
    return "linear"


def _axis_type(fig: go.Figure, letter: str, ref: str, values: list[Any]) -> str:
    """The axis type: set explicitly, or inferred from the traces on the axis and the new values, as Plotly does."""
    declared = fig.layout[_key(ref, letter)].type
    if declared not in (None, "-"):
        kind = str(declared)
    else:
        seen = [v for t in _traces(fig, letter, ref) for v in _vals(t, letter)]
        kinds = {_value_kind(v) for v in [*seen, *values] if v is not None}
        kind = "date" if "date" in kinds else "category" if "category" in kinds else "linear"
    if kind not in ("linear", "category"):
        raise ValueError(f"sdvplot does not support {kind} axes yet ({ref}); use a linear or category axis")
    return kind


def _categories(fig: go.Figure, letter: str, ref: str) -> list[Any]:
    """A category axis' categories in display order: categoryarray, or first appearance across the traces."""
    axis = fig.layout[_key(ref, letter)]
    order = axis.categoryorder or ("array" if axis.categoryarray is not None else "trace")
    from_traces = list(dict.fromkeys(v for t in _traces(fig, letter, ref) for v in _vals(t, letter)))
    if order == "array":
        listed = list(axis.categoryarray or ())
        return listed + [c for c in from_traces if c not in listed]
    if order == "trace":
        return from_traces
    if order in ("category ascending", "category descending"):
        return sorted(from_traces, reverse=order == "category descending")
    raise ValueError(f"sdvplot does not support categoryorder={order!r} yet ({ref}); use 'trace' or 'array'")


def _extent(fig: go.Figure, letter: str, ref: str, coords: list[float], index: dict[Any, int] | None) -> list[float]:
    """Every coordinate the axis' traces span, plus the new marks: the data Plotly's autorange would fit."""
    out = list(coords)
    across = "y" if letter == "x" else "x"
    stacked = fig.layout.barmode in ("stack", "relative")
    ends: dict[tuple[Any, ...], float] = {}  # where each bar stack ends so far: Plotly stacks bars in trace order
    filled: set[tuple[str, str]] = set()  # subplots that already have a scatter trace, for fill="tonext..."
    for t in _traces(fig, letter, ref):
        if t.type not in _READABLE:
            raise _unmeasurable(f"a {t.type} trace", ref, letter)
        subplot = (t.xaxis or "x", t.yaxis or "y")
        along = letter == ("x" if getattr(t, "orientation", None) == "h" else "y")  # bar lengths and stacks run along
        nums: list[float | None]
        if index is not None and getattr(t, letter) is not None:
            nums = [index.get(v) for v in _column(t, letter)]
        else:  # numbers; a trace without values sits at Plotly's default positions (on a category axis, as indices)
            nums = [None if v is None else float(v) for v in _column(t, letter)]
        if t.type == "bar" and along:
            if t.base is not None or fig.layout.barnorm or (stacked and t.offsetgroup):
                raise _unmeasurable("bars with a base, barnorm or stacked offsetgroups", ref, letter)
            out.append(0.0)  # bars start at zero
            if stacked:  # a bar starts where the stack at its position ends ("relative": one stack per sign)
                for p, v in zip(_column(t, across), nums, strict=False):
                    if v is not None and not math.isnan(v):
                        key = (subplot, p, fig.layout.barmode == "relative" and v < 0)
                        ends[key] = ends.get(key, 0.0) + v
                        out.append(ends[key])
                continue
        out += [v for v in nums if v is not None]
        if t.type == "bar" and index is None and not along:  # a bar is as wide as the gap between bars
            spots = sorted({v for v in nums if v is not None})
            half = min((b - a for a, b in zip(spots, spots[1:], strict=False)), default=1.0) / 2
            out += [spots[0] - half, spots[-1] + half] if spots else []
        elif t.type != "bar":
            if getattr(t, "stackgroup", None) and along:
                raise _unmeasurable("stacked scatter traces (stackgroup)", ref, letter)
            if t.fill == f"tozero{letter}" or (t.fill == f"tonext{letter}" and subplot not in filled):
                out.append(0.0)  # a filled area from zero; "tonext" fills to zero when no trace comes before it
            filled.add(subplot)
    if index is not None:
        out += [-0.5, len(index) - 0.5]  # a category axis shows every category's band
    return [v for v in out if not math.isnan(v)]


def _range(fig: go.Figure, letter: str, ref: str, coords: list[float], index: dict[Any, int] | None, *,
           mark: float) -> tuple[float, float]:  # fmt: skip
    """The axis range: as set, or the extent of the data with half a mark of room at each end, then pinned.

    ``mark`` is the fraction of the axis length one mark covers.
    """
    axis = fig.layout[_key(ref, letter)]
    if axis.range is not None and None not in axis.range and axis.autorange in (None, False):
        return float(axis.range[0]), float(axis.range[1])
    data = _extent(fig, letter, ref, coords, index)
    lo, hi = (min(data), max(data)) if data else (0.0, 1.0)
    span = (hi - lo or 1.0) / max(1 - mark, 0.5)
    mid = (lo + hi) / 2
    rng = (mid - span / 2, mid + span / 2)
    if isinstance(axis.autorange, str) and "reversed" in axis.autorange:
        rng = rng[::-1]
    axis.update(range=list(rng), autorange=False)
    return rng


def _plot_size(fig: go.Figure, xref: str, yref: str) -> tuple[float, float]:
    """The subplot's size in pixels at the layout's width and height (plotly.js's defaults when unset)."""
    w = (fig.layout.width or _PLOTLY_DEFAULT_WIDTH) - _margin(fig, "l") - _margin(fig, "r")
    h = (fig.layout.height or _PLOTLY_DEFAULT_HEIGHT) - _margin(fig, "t") - _margin(fig, "b")
    xd = fig.layout[_key(xref, "x")].domain or (0, 1)
    yd = fig.layout[_key(yref, "y")].domain or (0, 1)
    return w * (xd[1] - xd[0]), h * (yd[1] - yd[0])


def _coords(fig: go.Figure, letter: str, ref: str, values: list[Any]) -> tuple[list[Any], dict[Any, int] | None]:
    """Values as axis coordinates: numbers as they are, category names as their index (None when not a category)."""
    if _axis_type(fig, letter, ref, values) == "linear":
        return list(values), None
    index = {c: i for i, c in enumerate(_categories(fig, letter, ref))}
    return [index.get(v) for v in values], index


def _add(
    target: Any,
    x: Any,
    y: Any,
    teams: Any,
    *,
    kind: str,
    league: str,
    season: Any,
    height: float,
    alpha: float,
    variant: str,
    xref: str,
    yref: str,
    layer: str,
    embed: bool,
    id_system: str,
) -> Any:
    h, a = check_height(height), check_alpha(alpha)
    fig = _figure(target)
    _key(xref, "x")
    _key(yref, "y")
    placements = place(x, y, teams, league=league, season=season, kind=kind, variant=variant, id_system=id_system)
    xs, x_index = _coords(fig, "x", xref, [p.x for p in placements])
    ys, y_index = _coords(fig, "y", yref, [p.y for p in placements])
    keep = [i for i, (cx, cy) in enumerate(zip(xs, ys, strict=True)) if cx is not None and cy is not None]
    if len(keep) < len(placements):
        off = [p.team_id for i, p in enumerate(placements) if i not in keep]
        warnings.warn(f"skipped {len(off)} point(s) whose category is not on the axis: {off}", SdvplotWarning,
                      stacklevel=3)  # fmt: skip
    placements, xs, ys = [placements[i] for i in keep], [xs[i] for i in keep], [ys[i] for i in keep]
    if not placements:
        return fig
    plot_w, plot_h = _plot_size(fig, xref, yref)
    x_lo, x_hi = _range(fig, "x", xref, xs, x_index, mark=h * max(aspect(p) for p in placements) * plot_h / plot_w)
    y_lo, y_hi = _range(fig, "y", yref, ys, y_index, mark=h)
    sizex = 2 * abs(x_hi - x_lo)  # only bounds the width: "contain" fits each image by height
    for p, src, cx, cy in zip(placements, image_sources(placements, embed=embed), xs, ys, strict=True):
        fig.add_layout_image(
            source=src, x=cx, y=cy, xref=xref, yref=yref, sizex=sizex, sizey=h * abs(y_hi - y_lo),
            sizing="contain", xanchor="center", yanchor="middle", opacity=a, layer=layer,
            name=f"sdvplot:{kind}:{p.team_id}",
        )  # fmt: skip
    return fig


def add_logos(
    target: Any,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = "default",
    xref: str = "x",
    yref: str = "y",
    layer: str = "above",
    embed: bool = False,
    id_system: str = "auto",
) -> Any:
    """Draw each team's logo centred on its (x, y) point of a Plotly figure, as layout images.

    Call it after adding the traces: an axis range that is not set is worked out from the scatter and bar traces
    (stacked bars included) and the new points, with half a logo of room at each end (Plotly clips images at the plot
    edge), and pinned, because a data-placed image is sized in axis units. The logos then zoom with the data. Linear
    and category axes are supported (a category is placed at its index).

    Args:
        target: A ``plotly.graph_objects.Figure`` (or ``FigureWidget``).
        x: The points' x positions in the axis' own values (numbers, or category names).
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point, to pick each team's mark for that era.
        height: The logo height as a fraction of the plot area's height, in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        xref: The x axis to place on ("x", "x2", ...), for subplots.
        yref: The y axis to place on ("y", "y2", ...).
        layer: "above" or "below" the traces.
        embed: Inline each image as a data URI (HTML that renders offline, and static export with kaleido) instead
            of linking its URL.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        object: ``target`` itself, with the images added (like Plotly's own ``add_*`` methods).

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, the inputs differ in length, an axis is a log or date
            axis, or the range must be worked out from a trace type other than scatter or bar, stacked scatter traces
            (``stackgroup``), or bars with a ``base``, ``barnorm`` or stacked ``offsetgroup`` (set the range first).
        TypeError: If the target is not a Plotly ``Figure``.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

    Example:
        ::

            import plotly.graph_objects as go
            import sdvplot

            fig = go.Figure(go.Scatter(x=[10, 20], y=[-3, -7], mode="markers"))
            sdvplot.add_logos(fig, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)

    See Also:
        sdvplotR geom_nfl_logos(): https://sdvplotR.sportsdataverse.org/ ;
        Plotly layout images: https://plotly.com/python/images/
    """
    return _add(
        target, x, y, teams, kind="logo", league=league, season=season, height=height, alpha=alpha,
        variant=variant, xref=xref, yref=yref, layer=layer, embed=embed, id_system=id_system,
    )  # fmt: skip


def add_wordmarks(
    target: Any,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = "default",
    xref: str = "x",
    yref: str = "y",
    layer: str = "above",
    embed: bool = False,
    id_system: str = "auto",
) -> Any:
    """Draw each team's wordmark centred on its (x, y) point of a Plotly figure.

    Args:
        target: A ``plotly.graph_objects.Figure``.
        x: The points' x positions in the axis' own values.
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point.
        height: The wordmark height as a fraction of the plot area's height, in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        xref: The x axis to place on.
        yref: The y axis to place on.
        layer: "above" or "below" the traces.
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        object: ``target`` itself, with the images added.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or an axis is not
            supported (see ``add_logos``).
        TypeError: If the target is not a Plotly ``Figure``.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

    Example:
        ::

            import plotly.graph_objects as go
            import sdvplot

            fig = go.Figure(go.Bar(x=["KC", "BUF"], y=[12, 10]))
            sdvplot.add_wordmarks(fig, ["KC", "BUF"], [12, 10], ["KC", "BUF"], league="nfl", height=0.08)

    See Also:
        sdvplotR geom_nfl_wordmarks(): https://sdvplotR.sportsdataverse.org/
    """
    return _add(
        target, x, y, teams, kind="wordmark", league=league, season=season, height=height, alpha=alpha,
        variant=variant, xref=xref, yref=yref, layer=layer, embed=embed, id_system=id_system,
    )  # fmt: skip


def add_headshots(
    target: Any,
    x: Any,
    y: Any,
    players: Any,
    *,
    league: str,
    height: float = 0.1,
    alpha: float = 1,
    xref: str = "x",
    yref: str = "y",
    layer: str = "above",
    embed: bool = False,
    id_system: str = "espn",
) -> Any:
    """Draw each player's headshot centred on its (x, y) point of a Plotly figure.

    Args:
        target: A ``plotly.graph_objects.Figure``.
        x: The points' x positions in the axis' own values.
        y: The points' y positions, the same length as ``x``.
        players: The player id for each point.
        league: The SDV league key, e.g. "nfl".
        height: The headshot height as a fraction of the plot area's height, in (0, 1].
        alpha: Opacity, 0 to 1.
        xref: The x axis to place on.
        yref: The y axis to place on.
        layer: "above" or "below" the traces.
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``.

    Returns:
        object: ``target`` itself, with the images added.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or an axis is not
            supported (see ``add_logos``).
        TypeError: If the target is not a Plotly ``Figure``.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

    Example:
        ::

            import plotly.graph_objects as go
            import sdvplot

            fig = go.Figure(go.Scatter(x=[0.3, 0.7], y=[0.5, 0.5], mode="markers"))
            sdvplot.add_headshots(fig, [0.3], [0.5], ["3139477"], league="nfl", height=0.2)

    See Also:
        sdvplotR geom_nfl_headshots(): https://sdvplotR.sportsdataverse.org/
    """
    return _add(
        target, x, y, players, kind="headshot", league=league, season=None, height=height, alpha=alpha,
        variant="default", xref=xref, yref=yref, layer=layer, embed=embed, id_system=id_system,
    )  # fmt: skip


def axis_logos(
    target: Any,
    axis: str,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    variant: str = "default",
    mark_type: str = "logo",
    embed: bool = False,
    id_system: str = "auto",
) -> Any:
    """Replace a category axis' team labels with the teams' logos (or wordmarks).

    The images sit in paper coordinates just outside the plot (under the x axis, left of the y axis), ``height`` of
    the plot area tall; labels that are not teams stay as text, with one SdvplotWarning. The bottom (left) margin grows
    to make room. Call it after adding the traces, so the axis has its categories.

    Args:
        target: A ``plotly.graph_objects.Figure`` whose ``axis`` is a category axis.
        axis: "x" or "y" (the first x or y axis).
        league: The SDV league key, e.g. "nfl".
        season: One season for every label.
        height: The image height as a fraction of the plot area's height, in (0, 1].
        variant: "default", "dark", or a named variant from ``marks()``.
        mark_type: "logo" or "wordmark".
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: The id system of the labels; "auto" tries each in order.

    Returns:
        object: ``target`` itself, with the images added and the resolved labels blanked.

    Raises:
        ValueError: If ``axis`` is not "x"/"y", ``height`` is out of range, or the axis is not a category axis.
        TypeError: If the target is not a Plotly ``Figure``.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

    Example:
        ::

            import plotly.graph_objects as go
            import sdvplot

            fig = go.Figure(go.Bar(x=["KC", "BUF", "BAL"], y=[12, 10, 9]))
            sdvplot.axis_logos(fig, "x", league="nfl", height=0.1)

    See Also:
        sdvplotR element_sdv_logo(): https://sdvplotR.sportsdataverse.org/
    """
    letter = axis_letter(axis)
    h = check_height(height)
    fig = _figure(target)
    if _axis_type(fig, letter, letter, []) != "category":
        raise ValueError(f"axis_logos needs a category {letter} axis (team names on the axis)")
    cats = _categories(fig, letter, letter)
    labels = [str(c) for c in cats]
    index: list[Any] = list(range(len(cats)))
    across: list[Any] = [0.0] * len(cats)
    xs, ys = (index, across) if letter == "x" else (across, index)
    placements = place(xs, ys, labels, league=league, season=season, kind=mark_type, variant=variant,
                       id_system=id_system)  # fmt: skip
    ax = fig.layout[_key(letter, letter)]
    drawn = {int(p.x if letter == "x" else p.y) for p in placements}
    ax.update(tickmode="array", tickvals=cats, ticktext=["" if i in drawn else lab for i, lab in enumerate(labels)])
    if not placements:
        return fig
    plot_h = _plot_size(fig, "x", "y")[1]
    if letter == "x":
        # make room under the plot; the plot area shrinks by what the margin grows, so the images do too
        fig.layout.margin.b = _margin(fig, "b") + math.ceil(h * plot_h / (1 + h))
        lo, hi = 0.0, 1.0
    else:
        lo, hi = _range(fig, "y", "y", [], {c: i for i, c in enumerate(cats)}, mark=0)
        fig.layout.margin.l = _margin(fig, "l") + math.ceil(h * plot_h * max(aspect(p) for p in placements))
    for p, src in zip(placements, image_sources(placements, embed=embed), strict=True):
        loc = int(p.x if letter == "x" else p.y)
        if letter == "x":
            spec = {"x": loc, "y": 0, "xref": "x", "yref": "paper", "sizex": 2 * len(cats), "sizey": h,
                    "xanchor": "center", "yanchor": "top"}  # fmt: skip
        else:
            spec = {"x": 0, "y": loc, "xref": "paper", "yref": "y", "sizex": 1, "sizey": h * abs(hi - lo),
                    "xanchor": "right", "yanchor": "middle"}  # fmt: skip
        fig.add_layout_image(source=src, sizing="contain", layer="above", name=f"sdvplot:axis:{letter}:{p.team_id}",
                             **spec)  # fmt: skip
    return fig


def _span(fig: go.Figure, ref: str) -> float:
    rng = fig.layout[_key(ref, ref[0])].range
    return abs(float(rng[1]) - float(rng[0]))


def _height(fig: go.Figure, im: Any) -> float:
    """A layout image's emitted height as a fraction of the plot height: sizey over its y reference's span."""
    return float(im.sizey) / (1.0 if im.yref == "paper" else _span(fig, im.yref))


def _drawn_marks(target: Any) -> list[tuple[Any, ...]]:
    """Test hook: (team_id, x, y, height, source) for each image add_logos/add_wordmarks/add_headshots drew."""
    out = []
    for im in _figure(target).layout.images:
        parts = (im.name or "").split(":", 2)
        if parts[0] == "sdvplot" and parts[1] != "axis":
            out.append((parts[2], im.x, im.y, _height(target, im), im.source))
    return out


def _drawn_axis_marks(target: Any, axis: str) -> list[tuple[str, float, float]]:
    """Test hook: (team_id, category index, height) for each image on ``axis``, in tick order."""
    letter = axis_letter(axis)
    marks = []
    for im in _figure(target).layout.images:
        parts = (im.name or "").split(":", 3)
        if parts[:3] == ["sdvplot", "axis", letter]:
            marks.append((parts[3], float(im.x if letter == "x" else im.y), _height(target, im)))
    return sorted(marks, key=lambda m: m[1])


def _visible_axis_labels(target: Any, axis: str) -> list[str]:
    """Test hook: the tick labels on ``axis`` still shown as text."""
    return [t for t in (_figure(target).layout[_key(axis_letter(axis), axis)].ticktext or ()) if t]

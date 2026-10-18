"""In-cell charts for reactable-py: sparklines, sparkbars and gauges as inline SVG (reactablefmtr's Tier 2).

reactablefmtr draws these with the dataui htmlwidget (sparklines, sparkbars) and nested ``<div>``s (gauges); here each
cell is a self-contained ``<svg role="img">`` with an ``aria-label`` summarizing it, so a table needs no extra JS. List
cells pass through reactable-py unchanged: a polars ``List`` column or a pandas column of lists both reach the cell
function as a Python ``list``.
"""

from __future__ import annotations

import html
import math
import numbers
import statistics
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from sdvplot._errors import InputError, requires_extra

with requires_extra("reactable"):
    import narwhals as nw
    from reactable import Column
    from reactable.models import CellInfo

from sdvplot._colors import team_colors
from sdvplot._contrast import hex6, mix
from sdvplot._placement import _missing, check_alpha
from sdvplot._tables import check_px
from sdvplot._types import IdSystem, Which

__all__ = ["reactable_sdv_gauge", "reactable_sdv_sparkbar", "reactable_sdv_sparkline"]

_POINTS = ("first", "last", "min", "max")
_STATLINES = ("mean", "median", "min", "max")
_BANDLINES = ("innerquartiles", "range")
_STAT: dict[str, Callable[[list[float]], float]] = {
    "mean": statistics.fmean,
    "median": statistics.median,
    "min": min,
    "max": max,
}
_HIGHLIGHT = "red"  # a highlight given by name only: reactablefmtr's statline/bandline default color
_WIDTH = 100  # px, when width=None


def _a(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _n(value: float) -> str:
    """A coordinate, short: two decimals at most, no trailing zeros."""
    return f"{round(value, 2):g}"


def _plain(value: float) -> str:
    """A number as people write it: 12, 0.523, 1234567.5 (never 1.23e+06)."""
    if float(value).is_integer():
        return str(int(value))
    return f"{round(float(value), 4):f}".rstrip("0").rstrip(".")


def _real(value: Any) -> bool:
    return isinstance(value, numbers.Real) and not isinstance(value, bool) and not _missing(value)


def _series(value: Any) -> list[float | None] | None:
    """A cell's list of numbers (None for each missing entry), or None if the cell holds no list."""
    if hasattr(value, "tolist") and not isinstance(value, (str, bytes)):
        value = value.tolist()
    if not isinstance(value, (list, tuple)):
        return None
    return [float(v) if _real(v) else None for v in value]


def _choice(name: str, value: Any, allowed: Sequence[str]) -> None:
    if value is not None and value not in allowed:
        raise InputError(f"{name} must be None or one of {', '.join(map(repr, allowed))}, got {value!r}")


def _names(name: str, value: Any) -> tuple[str, ...]:
    """``labels`` / a sequence of highlight names: a subset of first/last/min/max, or "all"."""
    names = (value,) if isinstance(value, str) else tuple(value)
    if "all" in names:
        names = ("all", *_POINTS)
    bad = [n for n in names if n not in ("all", *_POINTS)]
    if bad:
        raise InputError(f"{name} takes 'first', 'last', 'min', 'max' or 'all', got {bad[0]!r}")
    return names


def _highlights(name: str, value: Any) -> dict[str, str]:
    """``highlight_points`` / ``highlight_bars`` as {point: color}: a mapping as reactablefmtr's
    ``highlight_points(max = "red")``, or a sequence of names, each drawn in red."""
    if isinstance(value, Mapping):
        _names(name, list(value))
        if "all" in value:
            return {"all": str(value["all"]), **{k: str(v) for k, v in value.items() if k != "all"}}
        return {str(k): str(v) for k, v in value.items()}
    return {n: _HIGHLIGHT for n in _names(name, value)}


def _decimals(decimals: Any) -> int:
    if isinstance(decimals, bool) or not isinstance(decimals, numbers.Integral) or decimals < 0:
        raise InputError(f"decimals is a whole number of decimal places, at least 0, got {decimals!r}")
    return int(decimals)


def _bound(name: str, value: Any) -> float | None:
    if value is None:
        return None
    if not _real(value) or not math.isfinite(value):
        raise InputError(f"{name} must be None or a finite number, got {value!r}")
    return float(value)


def _team_fills(
    data: Any, team_col: str | None, league: str | None, which: Which, na_color: str, id_system: IdSystem, strict: bool
) -> list[str] | None:
    """Each row's team color (``na_color`` where a team has none), or None without ``team_col``."""
    if team_col is None:
        return None
    if league is None:
        raise InputError("team_col needs league, the SDV league key of its teams (e.g. league='nba')")
    frame = nw.from_native(data, eager_only=True)
    if team_col not in frame.columns:
        raise ValueError(f"column {team_col!r} not found in data; columns are {frame.columns}")
    colors = team_colors(league, frame[team_col].to_list(), which=which, id_system=id_system, strict=strict)
    return [c or na_color for c in colors]


def _margins(labels: tuple[str, ...], statline: str | None, bars: bool) -> tuple[float, float, float, float, float]:
    """reactablefmtr's default margins (top, right, bottom, left) and the height a default 22 px chart grows to."""
    ends_only = bool(labels) and not set(labels) & {"min", "max", "all"}
    if bars:
        if statline:
            return (4, 28, 3, 13, 22) if not labels else (12, 26, 3, 26, 22)
        return (3, 13, 0, 13, 22) if not labels else (12, 26, 0, 26, 22)
    if statline:
        if not labels:
            return 4, 28, 3, 13, 22
        return (5, 28, 3, 24, 22) if ends_only else (14, 28, 10, 13, 28)
    if not labels:
        return 3, 13, 2, 13, 22
    return (5, 24, 3, 24, 22) if ends_only else (14, 13, 10, 13, 30)


class _Chart:
    """The shared geometry of a sparkline / sparkbar cell: the drawable box and its y scale."""

    def __init__(
        self, values: list[float], labels: tuple[str, ...], statline: str | None, bars: bool, height: float,
        width: float, lo: float | None, hi: float | None,
    ) -> None:  # fmt: skip
        t, r, b, left, grown = _margins(labels, statline, bars)
        self.h = grown if height == 22 else height
        self.w = width
        self.top, self.right, self.bottom, self.left = t, width - r, self.h - b, left
        vmin, vmax = min(values), max(values)
        if bars:  # bars stand on zero, so the scale holds it (reactablefmtr's smallest bar would have no height)
            vmin, vmax = min(vmin, 0.0), max(vmax, 0.0)
        self.lo = vmin if lo is None else lo
        self.hi = vmax if hi is None else hi

    def y(self, v: float) -> float:
        if self.hi == self.lo:
            return (self.top + self.bottom) / 2
        frac = (self.hi - v) / (self.hi - self.lo)
        return self.top + min(max(frac, 0.0), 1.0) * (self.bottom - self.top)

    def statline(self, kind: str | None, values: list[float], color: str, size: str, decimals: int) -> str:
        if kind is None:
            return ""
        v = _STAT[kind](values)
        y = _n(self.y(v))
        return (
            f'<line class="sdv-statline" x1="{_n(self.left)}" x2="{_n(self.right)}" y1="{y}" y2="{y}" '
            f'stroke="{_a(color)}" stroke-width="1" stroke-dasharray="2,2" stroke-opacity="0.75"/>'
            f'<text class="sdv-statline-label" x="{_n(self.right + 5)}" y="{y}" dominant-baseline="middle" '
            f'fill="{_a(color)}" font-weight="bold" font-size="{_a(size)}">{v:.{decimals}f}</text>'
        )

    def bandline(self, kind: str | None, values: list[float], color: str, opacity: float) -> str:
        if kind is None:
            return ""
        if kind == "range" or len(values) < 2:
            lo, hi = min(values), max(values)
        else:  # R type 7 / d3.quantile, as dataui's innerquartiles band
            q = statistics.quantiles(values, n=4, method="inclusive")
            lo, hi = q[0], q[2]
        y1, y2 = self.y(hi), self.y(lo)
        return (
            f'<rect class="sdv-bandline" x="{_n(self.left)}" y="{_n(y1)}" width="{_n(self.right - self.left)}" '
            f'height="{_n(y2 - y1)}" fill="{_a(color)}" fill-opacity="{opacity:g}"/>'
        )


def _which_points(values: list[float | None]) -> dict[str, int]:
    """The index of the first, last, min and max present value (the first of ties)."""
    present = [i for i, v in enumerate(values) if v is not None]
    vals = [(values[i], i) for i in present]
    return {
        "first": present[0],
        "last": present[-1],
        "min": min(vals, key=lambda p: (p[0], p[1]))[1],
        "max": max(vals, key=lambda p: (p[0], -p[1]))[1],
    }


def _svg(kind: str, w: float, h: float, label: str, body: str) -> str:
    return (
        f'<svg class="sdv-{kind}" xmlns="http://www.w3.org/2000/svg" width="{_n(w)}" height="{_n(h)}" '
        f'viewBox="0 0 {_n(w)} {_n(h)}" role="img" aria-label="{_a(label)}" style="display:block;overflow:visible">'
        f"<title>{html.escape(label)}</title>{body}</svg>"
    )


def _summary(name: str, values: list[float]) -> str:
    return (
        f"{name} of {len(values)} value{'s' * (len(values) != 1)}: min {_plain(min(values))}, "
        f"max {_plain(max(values))}, last {_plain(values[-1])}"
    )


def _area(pts: dict[int, tuple[float, float]], n: int, bottom: float) -> str:
    """The area under a sparkline: one closed shape per unbroken run of points, down to the chart's bottom."""
    runs: list[list[tuple[float, float]]] = []
    run: list[tuple[float, float]] = []
    for i in range(n + 1):
        if i < n and i in pts:
            run.append(pts[i])
        elif run:
            runs.append(run)
            run = []
    b = _n(bottom)
    return " ".join(
        f"M{_n(r[0][0])},{b} " + " ".join(f"L{_n(x)},{_n(y)}" for x, y in r) + f" L{_n(r[-1][0])},{b} Z" for r in runs
    )


def _point_labels(
    values: list[float | None], pts: dict[int, tuple[float, float]], at: dict[str, int], names: tuple[str, ...],
    color: str, size: str, places: int,
) -> str:  # fmt: skip
    """The value labels of a sparkline: first/last alone sit beside their points (as reactablefmtr), others above."""
    labeled = set(pts) if "all" in names else {at[name] for name in names}
    ends_only = bool(names) and not set(names) & {"min", "max", "all"}
    out = ""
    for i in sorted(labeled):
        x, y = pts[i]
        if ends_only and i == at["first"]:
            pos = f'x="{_n(x - 6)}" y="{_n(y)}" text-anchor="end" dominant-baseline="middle"'
        elif ends_only and i == at["last"]:
            pos = f'x="{_n(x + 6)}" y="{_n(y)}" text-anchor="start" dominant-baseline="middle"'
        else:
            pos = f'x="{_n(x)}" y="{_n(y - 7)}" text-anchor="middle"'
        out += f'<text class="sdv-label" {pos} fill="{_a(color)}" font-size="{_a(size)}">{values[i]:.{places}f}</text>'
    return out


def reactable_sdv_sparkline(
    data: Any,
    *,
    line_color: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Which = "primary",
    id_system: IdSystem = "auto",
    strict: bool = False,
    na_color: str = "#b3b3b3",
    line_width: float = 1.5,
    show_area: bool = False,
    area_color: str | None = None,
    area_opacity: float = 0.1,
    highlight_points: Sequence[str] | Mapping[str, str] = (),
    point_size: float = 1.5,
    statline: str | None = None,
    statline_color: str = "red",
    statline_label_size: str = "0.8em",
    bandline: str | None = None,
    bandline_color: str = "red",
    bandline_opacity: float = 0.2,
    labels: Sequence[str] | str = (),
    label_size: str = "0.8em",
    decimals: int = 0,
    min_value: float | None = None,
    max_value: float | None = None,
    height: float = 22,
    width: float | None = None,
    **column_kwargs: Any,
) -> Column:
    """A reactable column that draws each cell's list of numbers as a sparkline (an inline SVG).

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable``; read only for ``team_col``. The column itself
            holds one list per row (a polars ``List`` column, or a pandas column of lists); a missing entry breaks the
            line, an empty, missing or non-list cell is left blank.
        line_color: The line's CSS color; None for reactablefmtr's "slategray" (or the row's team color).
        team_col: A column of ``data`` holding each row's team: the line (and area) take that team's color.
        league: The SDV league key of ``team_col``'s teams, e.g. "nba"; required with ``team_col``.
        which: "primary" or "secondary" team color.
        id_system: The id system of ``team_col``, as in ``resolve``.
        strict: Raise UnresolvedTeamError instead of warning when a team does not resolve.
        na_color: The color for teams that do not resolve or have no color.
        line_width: The line's stroke width in pixels.
        show_area: Fill the area under the line.
        area_color: The area's color; None for the line's.
        area_opacity: The area's opacity, 0 to 1.
        highlight_points: Points to mark: a mapping such as ``{"min": "red", "max": "blue"}`` (reactablefmtr's
            ``highlight_points(min = "red", max = "blue")``), or a sequence of names drawn in red. Names are "first",
            "last", "min", "max" and "all".
        point_size: The radius of a highlighted point, in pixels.
        statline: A dashed reference line at the series' "mean", "median", "min" or "max", labeled at its right.
        statline_color: The reference line's and its label's color.
        statline_label_size: The reference line label's CSS font size.
        bandline: A shaded band across the series' "innerquartiles" (25th to 75th percentile) or "range".
        bandline_color: The band's color.
        bandline_opacity: The band's opacity, 0 to 1.
        labels: Values to print by their point: names as for ``highlight_points`` ("all" labels every point).
        label_size: The labels' CSS font size.
        decimals: Decimal places of the labels and the statline label.
        min_value: The value at the bottom of every cell's chart; None for each series' own minimum.
        max_value: The value at the top of every cell's chart; None for each series' own maximum.
        height: The chart's height in pixels; the default 22 grows to 28 or 30 to make room for labels above the
            points, as in reactablefmtr.
        width: The chart's width in pixels; None for 100.
        **column_kwargs: Passed to ``reactable.Column`` (``id`` is required by reactable).

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer. Each chart is an
        ``<svg role="img">`` whose ``aria-label`` (and ``<title>`` tooltip) gives the number of points, the minimum,
        the maximum and the last value.

    Raises:
        InputError: (a ValueError) If ``height``/``width`` is not a number of pixels of at least 1, an opacity is
            outside [0, 1], ``statline``/``bandline``/``labels``/``highlight_points`` names an unknown option,
            ``decimals`` is not a whole number, ``min_value``/``max_value`` is not a finite number, or ``team_col`` is
            given without ``league``; if ``league``, ``id_system`` or ``which`` is unknown.
        ValueError: If ``team_col`` is not a column of ``data``.
        UnresolvedTeamError: (a ValueError) If ``strict=True`` and a team does not resolve.

    Example:
        ::

            import polars as pl
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_sparkline

            df = pl.DataFrame({"team": ["BOS", "NY"], "margin": [[12, -4, 8, 21], [3, 7, -10, 5]]})
            Reactable(
                df,
                columns=[
                    reactable_sdv_sparkline(df, id="margin", team_col="team", league="nba",
                                            highlight_points={"min": "red", "max": "blue"}, statline="mean"),
                ],
            )

    See Also:
        Equivalent of reactablefmtr::react_sparkline (drawn without dataui: no hover tooltips per point, a solid
        rather than hatched band, straight rather than cardinal-curve segments).
    """
    h, w = check_px(height), check_px(_WIDTH if width is None else width)
    _choice("statline", statline, _STATLINES)
    _choice("bandline", bandline, _BANDLINES)
    marks, label_names = _highlights("highlight_points", highlight_points), _names("labels", labels)
    a_opacity, b_opacity, places = check_alpha(area_opacity), check_alpha(bandline_opacity), _decimals(decimals)
    lo, hi = _bound("min_value", min_value), _bound("max_value", max_value)
    fills = _team_fills(data, team_col, league, which, na_color, id_system, strict)

    def cell(info: CellInfo) -> str:
        values = _series(info.value)
        present = [v for v in values or [] if v is not None]
        if not values or not present:
            return ""
        color = fills[info.row_index] if fills is not None else line_color or "slategray"
        chart = _Chart(present, label_names, statline, False, h, w, lo, hi)
        n = len(values)
        step = (chart.right - chart.left) / (n - 1) if n > 1 else 0.0
        xs = [chart.left + i * step if n > 1 else (chart.left + chart.right) / 2 for i in range(n)]
        pts = {i: (xs[i], chart.y(v)) for i, v in enumerate(values) if v is not None}
        path, pen_down = [], False
        for i in range(n):
            if i in pts:
                path.append(f"{'L' if pen_down else 'M'}{_n(pts[i][0])},{_n(pts[i][1])}")
            pen_down = i in pts
        line = " ".join(path)
        body = chart.bandline(bandline, present, bandline_color, b_opacity)
        if show_area:
            area = _area(pts, n, chart.bottom)
            body += f'<path class="sdv-area" d="{area}" fill="{_a(area_color or color)}" fill-opacity="{a_opacity:g}"/>'
        body += (
            f'<path class="sdv-line" d="{line}" fill="none" stroke="{_a(color)}" stroke-width="{line_width:g}" '
            'stroke-linejoin="round" stroke-linecap="round"/>'
        )
        body += chart.statline(statline, present, statline_color, statline_label_size, places)
        at = _which_points(values)
        point_color: dict[int, str] = {}
        if "all" in marks:
            point_color.update({i: marks["all"] for i in pts})
        for name in _POINTS:  # later names win where points coincide, as reactablefmtr layers them
            if name in marks:
                point_color[at[name]] = marks[name]
        for i, c in sorted(point_color.items()):
            body += (
                f'<circle class="sdv-point" cx="{_n(pts[i][0])}" cy="{_n(pts[i][1])}" r="{point_size:g}" '
                f'fill="{_a(c)}" stroke="{_a(c)}"/>'
            )
        body += _point_labels(values, pts, at, label_names, color, label_size, places)
        return _svg("sparkline", w, chart.h, _summary("Sparkline", present), body)

    return Column(**{"html": True, **column_kwargs, "cell": cell})


def reactable_sdv_sparkbar(
    data: Any,
    *,
    fill_color: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Which = "primary",
    id_system: IdSystem = "auto",
    strict: bool = False,
    na_color: str = "#b3b3b3",
    fill_opacity: float = 1,
    highlight_bars: Sequence[str] | Mapping[str, str] = (),
    statline: str | None = None,
    statline_color: str = "red",
    statline_label_size: str = "0.8em",
    bandline: str | None = None,
    bandline_color: str = "red",
    bandline_opacity: float = 0.2,
    labels: Sequence[str] | str = (),
    label_size: str = "0.8em",
    decimals: int = 0,
    min_value: float | None = None,
    max_value: float | None = None,
    height: float = 22,
    width: float | None = None,
    **column_kwargs: Any,
) -> Column:
    """A reactable column that draws each cell's list of numbers as a small bar chart (an inline SVG).

    Bars stand on zero: positive values rise from it, negative ones hang below it.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable``; read only for ``team_col``. The column itself
            holds one list per row; a missing entry leaves a gap, an empty, missing or non-list cell is left blank.
        fill_color: The bars' CSS color; None for reactablefmtr's "slategray" (or the row's team color).
        team_col: A column of ``data`` holding each row's team: the bars take that team's color.
        league: The SDV league key of ``team_col``'s teams, e.g. "wnba"; required with ``team_col``.
        which: "primary" or "secondary" team color.
        id_system: The id system of ``team_col``, as in ``resolve``.
        strict: Raise UnresolvedTeamError instead of warning when a team does not resolve.
        na_color: The color for teams that do not resolve or have no color.
        fill_opacity: The bars' opacity, 0 to 1.
        highlight_bars: Bars to recolor: a mapping such as ``{"max": "gold"}`` (reactablefmtr's
            ``highlight_bars(max = "gold")``), or a sequence of "first", "last", "min", "max" drawn in red.
        statline: A dashed reference line at the series' "mean", "median", "min" or "max", labeled at its right.
        statline_color: The reference line's and its label's color.
        statline_label_size: The reference line label's CSS font size.
        bandline: A shaded band across the series' "innerquartiles" or "range".
        bandline_color: The band's color.
        bandline_opacity: The band's opacity, 0 to 1.
        labels: Values to print above their bars: "first", "last", "min", "max" or "all".
        label_size: The labels' CSS font size.
        decimals: Decimal places of the labels and the statline label.
        min_value: The value at the bottom of every cell's chart; None for the lower of 0 and the series' minimum.
        max_value: The value at the top of every cell's chart; None for the higher of 0 and the series' maximum.
        height: The chart's height in pixels.
        width: The chart's width in pixels; None for 100.
        **column_kwargs: Passed to ``reactable.Column`` (``id`` is required by reactable).

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer; each chart is an ``<svg role="img">``
        whose ``aria-label`` gives the number of bars, the minimum, the maximum and the last value.

    Raises:
        InputError: (a ValueError) As ``reactable_sdv_sparkline``: a bad pixel size, opacity, option name, decimals
            or bound, or ``team_col`` without ``league``; if ``league``, ``id_system`` or ``which`` is unknown.
        ValueError: If ``team_col`` is not a column of ``data``.
        UnresolvedTeamError: (a ValueError) If ``strict=True`` and a team does not resolve.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_sparkbar

            df = pd.DataFrame({"team": ["LV", "NY"], "pts": [[88, 95, 79, 101], [92, 85, 99, 90]]})
            Reactable(df, columns=[reactable_sdv_sparkbar(df, id="pts", team_col="team", league="wnba",
                                                          highlight_bars={"max": "gold"})])

    See Also:
        Equivalent of reactablefmtr::react_sparkbar (drawn without dataui: no hover tooltips per bar, bars rooted at
        zero so the smallest bar still shows).
    """
    h, w = check_px(height), check_px(_WIDTH if width is None else width)
    _choice("statline", statline, _STATLINES)
    _choice("bandline", bandline, _BANDLINES)
    marks, label_names = _highlights("highlight_bars", highlight_bars), _names("labels", labels)
    f_opacity, b_opacity, places = check_alpha(fill_opacity), check_alpha(bandline_opacity), _decimals(decimals)
    lo, hi = _bound("min_value", min_value), _bound("max_value", max_value)
    fills = _team_fills(data, team_col, league, which, na_color, id_system, strict)

    def cell(info: CellInfo) -> str:
        values = _series(info.value)
        present = [v for v in values or [] if v is not None]
        if not values or not present:
            return ""
        color = fills[info.row_index] if fills is not None else fill_color or "slategray"
        chart = _Chart(present, label_names, statline, True, h, w, lo, hi)
        n = len(values)
        band = (chart.right - chart.left) / n
        bar_w, base = band * 0.8, chart.y(min(max(0.0, chart.lo), chart.hi))
        at = _which_points(values)
        bar_color = {i: marks["all"] for i, v in enumerate(values) if v is not None} if "all" in marks else {}
        for name in _POINTS:
            if name in marks:
                bar_color[at[name]] = marks[name]
        body = chart.bandline(bandline, present, bandline_color, b_opacity)
        tops: dict[int, tuple[float, float]] = {}
        for i, v in enumerate(values):
            if v is None:
                continue
            x, y = chart.left + i * band + (band - bar_w) / 2, chart.y(v)
            tops[i] = (x + bar_w / 2, min(y, base))
            body += (
                f'<rect class="sdv-bar" x="{_n(x)}" y="{_n(min(y, base))}" width="{_n(bar_w)}" '
                f'height="{_n(abs(base - y))}" fill="{_a(bar_color.get(i, color))}" fill-opacity="{f_opacity:g}"/>'
            )
        body += chart.statline(statline, present, statline_color, statline_label_size, places)
        labeled = set(tops) if "all" in label_names else {at[name] for name in label_names}
        for i in sorted(labeled):
            value = values[i]
            assert value is not None
            body += (
                f'<text class="sdv-label" x="{_n(tops[i][0])}" y="{_n(tops[i][1] - 3)}" text-anchor="middle" '
                f'fill="{_a(color)}" font-size="{_a(label_size)}">{value:.{places}f}</text>'
            )
        return _svg("sparkbar", w, chart.h, _summary("Bar chart", present), body)

    return Column(**{"html": True, **column_kwargs, "cell": cell})


def _ramp(colors: Sequence[str], x: float, bias: float) -> str:
    """grDevices::colorRamp(colors, bias = bias)(x): stops at ((i / (n - 1)) ^ bias), linear in sRGB between them."""
    if len(colors) == 1:
        return colors[0]
    stops = [(i / (len(colors) - 1)) ** bias for i in range(len(colors))]
    for (s0, c0), (s1, c1) in zip(
        zip(stops, colors, strict=True), zip(stops[1:], colors[1:], strict=True), strict=False
    ):
        if x <= s1:
            return mix(c0, c1, 0.0 if s1 == s0 else min(max((x - s0) / (s1 - s0), 0.0), 1.0))
    return colors[-1]


def _arc(cx: float, cy: float, outer: float, inner: float, frac: float) -> str:
    """The annulus path from the gauge's left end, ``frac`` of the way round the top to its right end."""
    t = math.pi * (1 - frac)
    ox, oy, ix, iy = (
        cx + outer * math.cos(t),
        cy - outer * math.sin(t),
        cx + inner * math.cos(t),
        cy - inner * math.sin(t),
    )
    return (
        f"M{_n(cx - outer)},{_n(cy)} A{_n(outer)},{_n(outer)} 0 0 1 {_n(ox)},{_n(oy)} "
        f"L{_n(ix)},{_n(iy)} A{_n(inner)},{_n(inner)} 0 0 0 {_n(cx - inner)},{_n(cy)} Z"
    )


def _ramp_colors(fill_color: str | Sequence[str] | None) -> list[str]:
    if fill_color is None or isinstance(fill_color, str):
        return [fill_color or "#15607A"]
    try:
        ramp = [hex6(c) for c in fill_color]
    except ValueError as e:
        raise InputError(f"fill_color with several colors takes hex colors: {e}") from None
    if not ramp:
        raise InputError("fill_color is empty")
    return ramp


def _formatter(number_fmt: Callable[[float], str] | str | None) -> Callable[[float], str]:
    if number_fmt is None:
        return _plain
    if isinstance(number_fmt, str):
        spec = number_fmt
        return lambda v: format(v, spec)
    return number_fmt


def reactable_sdv_gauge(
    data: Any,
    *,
    fill_color: str | Sequence[str] | None = None,
    background: str = "#EEEEEE",
    team_col: str | None = None,
    league: str | None = None,
    which: Which = "primary",
    id_system: IdSystem = "auto",
    strict: bool = False,
    na_color: str = "#b3b3b3",
    min_value: float | None = None,
    max_value: float | None = None,
    show_min_max: bool = False,
    number_fmt: Callable[[float], str] | str | None = None,
    size: float = 1,
    text_color: str | None = None,
    bold_text: bool = False,
    text_size: str | None = None,
    bias: float = 1,
    opacity: float = 1,
    **column_kwargs: Any,
) -> Column:
    """A reactable column that draws each cell's number as a half-circle gauge (an inline SVG) with the value inside.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable``: the gauged column's range (for the default scale
            and the color ramp) and ``team_col`` are read from it.
        fill_color: The gauge's CSS color, or several hex colors to ramp through from the column's smallest value to
            its largest (as reactablefmtr); None for reactablefmtr's "#15607A" (or the row's team color).
        background: The color of the gauge's unfilled track.
        team_col: A column of ``data`` holding each row's team: the gauge takes that team's color.
        league: The SDV league key of ``team_col``'s teams, e.g. "nhl"; required with ``team_col``.
        which: "primary" or "secondary" team color.
        id_system: The id system of ``team_col``, as in ``resolve``.
        strict: Raise UnresolvedTeamError instead of warning when a team does not resolve.
        na_color: The color for teams that do not resolve or have no color.
        min_value: The value of an empty gauge; None for 0.
        max_value: The value of a full gauge; None for the column's largest absolute value.
        show_min_max: Print the scale's two ends under the gauge.
        number_fmt: How to print the value (and the ends): a function such as ``"{:.1%}".format``, or a format spec
            such as ``".3f"``; None prints the number as is.
        size: The gauge's scale: 1 is 50 pixels wide (reactablefmtr's ``size = 1``), 2 is 100.
        text_color: The value's color; None for the cell's text color.
        bold_text: Print the value in bold.
        text_size: The value's CSS font size; None for the cell's.
        bias: The ramp's spacing (grDevices::colorRamp's ``bias``): above 1 spreads the colors toward the high end.
        opacity: The fill's opacity, 0 to 1.
        **column_kwargs: Passed to ``reactable.Column`` (``id`` is required by reactable).

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer; each gauge is an ``<svg role="img">``
        whose ``aria-label`` gives the value and the scale. A missing value is left blank; text passes through.

    Raises:
        InputError: (a ValueError) If ``size`` or ``bias`` is not a positive number, ``opacity`` is outside [0, 1],
            ``min_value``/``max_value`` is not a finite number, ``fill_color`` holds several colors that are not hex
            colors, or ``team_col`` is given without ``league``; if ``league``, ``id_system`` or ``which`` is unknown.
        ValueError: If ``team_col`` is not a column of ``data``.
        UnresolvedTeamError: (a ValueError) If ``strict=True`` and a team does not resolve.

    Example:
        ::

            import polars as pl
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_gauge

            df = pl.DataFrame({"team": ["BOS", "TOR", "FLA"], "save_pct": [0.915, 0.902, 0.908]})
            Reactable(df, columns=[reactable_sdv_gauge(df, id="save_pct", team_col="team", league="nhl",
                                                       min_value=0.88, max_value=0.93, number_fmt=".3f")])

    See Also:
        Equivalent of reactablefmtr::gauge_chart (an SVG arc rather than nested divs, so the value sits on the cell's
        own background in any theme; the "min" end reads the scale's real lower bound).
    """
    for name, v in (("size", size), ("bias", bias)):
        if not _real(v) or not math.isfinite(v) or v <= 0:
            raise InputError(f"{name} must be a positive number, got {v!r}")
    alpha = check_alpha(opacity)
    lo_arg, hi_arg = _bound("min_value", min_value), _bound("max_value", max_value)
    ramp, fmt = _ramp_colors(fill_color), _formatter(number_fmt)
    fills = _team_fills(data, team_col, league, which, na_color, id_system, strict)
    frame = nw.from_native(data, eager_only=True)
    ranges: dict[str, tuple[float, float, float]] = {}

    def column_range(column: str) -> tuple[float, float, float]:
        """The column's min, max and largest absolute value."""
        if column not in ranges:
            vals = [float(v) for v in frame[column].to_list() if _real(v)] if column in frame.columns else []
            ranges[column] = (min(vals), max(vals), max(map(abs, vals))) if vals else (0.0, 0.0, 0.0)
        return ranges[column]

    w = 50 * size
    r_out, r_in = w / 2, w / 2 * 0.75  # reactablefmtr's cover is 75% of the gauge's width
    weight = ' font-weight="bold"' if bold_text else ""
    font = f' font-size="{_a(text_size)}"' if text_size else ""
    ink = _a(text_color or "currentColor")

    def cell(info: CellInfo) -> str:
        value = info.value
        if _missing(value):
            return ""
        if not _real(value):
            return html.escape(str(value))
        v = float(value)
        cmin, cmax, cabs = column_range(info.column_name)
        lo = 0.0 if lo_arg is None else lo_arg
        hi = cabs if hi_arg is None else hi_arg
        frac = 0.0 if hi == lo else min(max((abs(v) - lo) / (hi - lo), 0.0), 1.0)
        if fills is not None:
            color = fills[info.row_index]
        else:
            color = _ramp(ramp, 1.0 if cmax == cmin else (v - cmin) / (cmax - cmin), bias)
        label = html.escape(fmt(v))
        h = r_out + (12 * size if show_min_max else 0)
        body = f'<path class="sdv-track" d="{_arc(r_out, r_out, r_out, r_in, 1.0)}" fill="{_a(background)}"/>'
        if frac > 0:
            body += (
                f'<path class="sdv-fill" d="{_arc(r_out, r_out, r_out, r_in, frac)}" fill="{_a(color)}" '
                f'fill-opacity="{alpha:g}"/>'
            )
        body += (
            f'<text class="sdv-value" x="{_n(r_out)}" y="{_n(r_out - 2)}" text-anchor="middle" fill="{ink}"'
            f"{weight}{font}>{label}</text>"
        )
        if show_min_max:
            y = _n(r_out + 10 * size)
            body += (
                f'<text class="sdv-min" x="0" y="{y}" text-anchor="start" fill="{ink}" font-size="0.7em">'
                f"{html.escape(fmt(lo))}</text>"
                f'<text class="sdv-max" x="{_n(w)}" y="{y}" text-anchor="end" fill="{ink}" font-size="0.7em">'
                f"{html.escape(fmt(hi))}</text>"
            )
        aria = f"Gauge: {fmt(v)} on a scale from {fmt(lo)} to {fmt(hi)}"
        return _svg("gauge", w, h, aria, body)

    return Column(**{"html": True, **column_kwargs, "cell": cell})

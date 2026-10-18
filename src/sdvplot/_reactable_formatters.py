"""reactablefmtr's cell formatters for reactable-py: data bars, color tiles and scales, pills, icons, merged columns,
highlights and bubbles, re-exported from ``sdvplot.reactable``.

Each function reads the frame passed to ``Reactable`` (its ranges, buckets and per-row colors) and returns a
``reactable.Column``; the column's ``id`` and any other ``Column`` argument pass through as keywords. The semantics and
defaults are reactablefmtr 2.1.0's, read from its R source; where reactablefmtr takes a color column (``color_ref``)
these also take a team column (``team_col`` + ``league``) and fill with each row's team color, with readable ink. Icons
are inline SVG (no Font Awesome) and tooltips are the ``title`` attribute (no tippy).
"""

from __future__ import annotations

import html
import math
import numbers
from collections.abc import Callable, Sequence
from typing import Any, Literal

import narwhals as nw
from reactable import Column
from reactable.models import CellInfo

from sdvplot._colors import team_colors
from sdvplot._contrast import contrast, hex6, on_color, solid
from sdvplot._errors import InputError, warn
from sdvplot._normalize import norm_season
from sdvplot._placement import _missing
from sdvplot._tables import check_px, mark_html
from sdvplot._types import IdSystem, Which

NumberFmt = Callable[[Any], str] | str | None
TextPosition = Literal["inside-end", "outside-end", "inside-base", "outside-base", "center", "above", "none"]
Mark = Literal["logo", "headshot", "wordmark"]

_RAMP = ("#15607A", "#FFFFFF", "#FA8C00")  # reactablefmtr's default color_tiles/color_scales/bubble_grid colors
_FILL = "#15607A"  # reactablefmtr's default single fill
_ICON_COLORS = ("#15607A", "#B0B0B0", "#FA8C00")  # icon_sets
_TREND_COLORS = ("#15607A", "#B2B2B2", "#FA8C00")  # icon_trend_indicator: down, zero, up
_SHADOW = "0 6px 6px -4px #888888"

# 16x16 inline SVG bodies. ponytail: a small fixed set; add a path here when a recipe needs another shape.
_ICONS = {
    "circle": '<circle cx="8" cy="8" r="7"/>',
    "square": '<rect x="1" y="1" width="14" height="14" rx="1.5"/>',
    "diamond": '<path d="M8 .5 15.5 8 8 15.5.5 8z"/>',
    "triangle-up": '<path d="M8 1.5 15 14.5H1z"/>',
    "triangle-down": '<path d="M1 1.5h14L8 14.5z"/>',
    "arrow-up": '<path d="M8 1 2 7.5h4V15h4V7.5h4z"/>',
    "arrow-down": '<path d="M8 15 2 8.5h4V1h4v7.5h4z"/>',
    "arrow-right": '<path d="M15 8 8.5 2v4H1v4h7.5v4z"/>',
    "arrow-left": '<path d="M1 8 7.5 2v4H15v4H7.5v4z"/>',
    "chevron-up": '<path d="M8 3.5 15 10.5 13 12.5 8 7.5 3 12.5 1 10.5z"/>',
    "chevron-down": '<path d="M8 12.5 1 5.5 3 3.5 8 8.5 13 3.5 15 5.5z"/>',
    "star": '<path d="M8 .8l2.2 4.6 5 .7-3.6 3.5.9 5L8 12.2l-4.5 2.4.9-5L.8 6.1l5-.7z"/>',
    "check": '<path d="M6.2 13.6.6 8l2-2 3.6 3.6 7.2-7.2 2 2z"/>',
    "x": '<path d="M3 1l5 5 5-5 2 2-5 5 5 5-2 2-5-5-5 5-2-2 5-5-5-5z"/>',
    "flag": '<path d="M2 1h1.6v14H2zM4.4 1.6H14l-2.6 3.6L14 8.8H4.4z"/>',
    "minus": '<rect x="1" y="6.5" width="14" height="3" rx="1"/>',
    "plus": '<path d="M6.5 1h3v5.5H15v3H9.5V15h-3V9.5H1v-3h5.5z"/>',
    "heart": '<path d="M8 14.5S1 10 1 5.3C1 3 2.7 1.5 4.6 1.5c1.4 0 2.6.8 3.4 2 .8-1.2 2-2 3.4-2 1.9 0 3.6 1.5 '
    '3.6 3.8C15 10 8 14.5 8 14.5z"/>',
    "person": '<circle cx="8" cy="4.5" r="3.5"/><path d="M1 15.5c0-4 3-6.5 7-6.5s7 2.5 7 6.5z"/>',
}
_ICONS["triangle"] = _ICONS["triangle-up"]
_ICONS["arrow"] = _ICONS["arrow-right"]
_TRENDS = ("arrow", "chevron", "triangle")


# --- shared helpers ---------------------------------------------------------------------------------------------


def _real(value: Any) -> bool:
    return isinstance(value, numbers.Real) and not isinstance(value, bool) and not _missing(value)


def _frame(data: Any) -> Any:
    return nw.from_native(data, eager_only=True)


def _column(frame: Any, name: str, what: str = "column") -> list[Any]:
    if name not in frame.columns:
        raise ValueError(f"{what} {name!r} not found in data; columns are {frame.columns}")
    return list(frame[name].to_list())


def _numbers(values: list[Any]) -> list[float | None]:
    return [float(v) if _real(v) else None for v in values]


def _fmt(value: Any, number_fmt: NumberFmt) -> str:
    """The cell's text: ``number_fmt(value)``, ``format(value, number_fmt)``, or R's 7 significant digits."""
    if callable(number_fmt):
        return html.escape(str(number_fmt(value)))
    if isinstance(number_fmt, str) and _real(value):
        try:
            return html.escape(format(value, number_fmt))
        except ValueError:  # an integer spec on a whole float (pandas makes an int column with a gap float)
            if not float(value).is_integer():
                raise
            return html.escape(format(int(value), number_fmt))
    if _real(value):
        v = float(value)
        return str(int(v)) if v.is_integer() and abs(v) < 1e15 else f"{v:.7g}"
    return html.escape(str(value))


def _check_fmt(number_fmt: Any) -> NumberFmt:
    if number_fmt is None or callable(number_fmt):
        return number_fmt
    if isinstance(number_fmt, str):
        try:  # a bad spec fails now, not inside reactable ("d" takes whole numbers only)
            format(1, number_fmt)
        except ValueError:
            format(1.5, number_fmt)
        return number_fmt
    raise InputError(f"number_fmt is a function of the value or a format spec such as ',.1f', got {number_fmt!r}")


def _css(**rules: Any) -> str:
    """An inline style: snake_case keys become CSS properties, None values are left out."""
    return ";".join(f"{k.replace('_', '-')}:{html.escape(str(v))}" for k, v in rules.items() if v is not None)


def _title(text: str, tooltip: bool) -> str:
    return f' title="{text}"' if tooltip else ""


def _check_opacity(opacity: Any, name: str = "opacity") -> float:
    if not _real(opacity) or not 0 <= opacity <= 1:
        raise InputError(f"{name} is an opacity in [0, 1], got {opacity!r}")
    return float(opacity)


def _choice(value: Any, name: str, options: Sequence[str]) -> str:
    if value not in options:
        raise InputError(f"{name} must be one of {', '.join(map(repr, options))}, got {value!r}")
    return str(value)


def _hexes(colors: Any, name: str) -> list[str]:
    seq = [colors] if isinstance(colors, str) else list(colors)
    if not seq:
        raise InputError(f"{name} needs at least one color")
    return [hex6(c) for c in seq]


def _alpha(color: str, opacity: float) -> str:
    """A hex color at ``opacity`` (grDevices::adjustcolor); a CSS color that is not hex passes through."""
    try:
        c = hex6(color, drop_alpha=True)
    except ValueError:
        return color
    return c if opacity >= 1 else f"{c}{round(opacity * 255):02x}"


def _ramp(colors: list[str], x: float, bias: float = 1.0) -> str:
    """grDevices::colorRamp(colors, bias)(x) as hex: linear in RGB between stops at ``(i / (n - 1)) ** bias``, each
    channel truncated as ``rgb(..., maxColorValue = 255)`` does."""
    rgb = [[int(c[i : i + 2], 16) for i in (1, 3, 5)] for c in colors]
    if len(rgb) == 1:
        return colors[0]
    x = min(max(x, 0.0), 1.0)
    stops = [(i / (len(rgb) - 1)) ** bias for i in range(len(rgb))]
    i = next(k for k in range(len(rgb) - 1) if x <= stops[k + 1])
    t = (x - stops[i]) / (stops[i + 1] - stops[i]) if stops[i + 1] > stops[i] else 0.0
    return "#" + "".join(f"{int(a + (b - a) * t + 1e-9):02x}" for a, b in zip(rgb[i], rgb[i + 1], strict=True))


def _ntile(values: list[float | None], n: int) -> list[int | None]:
    """dplyr::ntile(): rank (ties by position) into ``n`` buckets as even as possible, the larger ones first."""
    order = sorted((v, i) for i, v in enumerate(values) if v is not None)
    rank = {i: r + 1 for r, (_, i) in enumerate(order)}
    length = len(order)
    larger, smaller = math.ceil(length / n), length // n
    threshold = larger * (length % n)
    out: list[int | None] = []
    for i in range(len(values)):
        if i not in rank:
            out.append(None)
            continue
        x = rank[i]
        bins = (x + larger - 1) / larger if x <= threshold else (x - threshold + smaller - 1) / smaller + length % n
        out.append(math.floor(bins))
    return out


def _ink(fill: str, text_color: str | None, brighten: bool) -> str:
    """The text color on ``fill``: ``text_color`` unless it is unreadable there and ``brighten_text`` is on, in which
    case black or white (reactablefmtr switches to its brighten color on dark fills)."""
    try:
        bg = solid(fill)
    except ValueError:  # a CSS color name from a color column: nothing to measure
        return text_color or "#000000"
    if not brighten:
        return text_color or "#000000"
    if text_color is not None:
        try:
            if contrast(hex6(text_color), bg) >= 4.5:
                return text_color
        except ValueError:
            return text_color
    return on_color(bg)


def _norm(value: float, lo: float, hi: float) -> float:
    return 1.0 if hi == lo else (value - lo) / (hi - lo)  # a constant column is 1, as in reactablefmtr


def _row_refs(
    frame: Any,
    *,
    color_ref: str | None,
    team_col: str | None,
    league: str | None,
    which: Which,
    season: Any,
    id_system: IdSystem,
    strict: bool,
) -> list[str | None] | None:
    """Each row's own fill: the ``color_ref`` column's color, or the ``team_col`` team's color (None where a team does
    not resolve, so the cell falls back to its scale color); None when neither is given."""
    if color_ref is not None and team_col is not None:
        raise InputError("give color_ref or team_col, not both")
    if color_ref is not None:
        return [None if _missing(c) else str(c) for c in _column(frame, color_ref, "color_ref")]
    if team_col is None:
        return None
    if league is None:
        raise InputError("team_col needs league, the SDV league key such as 'nfl'")
    norm_season(season, league=league)
    teams = _column(frame, team_col, "team_col")
    return team_colors(league, teams, which=which, season=season, id_system=id_system, strict=strict)


def _row_marks(
    frame: Any,
    *,
    mark: Mark | None,
    mark_col: str | None,
    league: str | None,
    height: float,
    season: Any,
    id_system: IdSystem,
    strict: bool,
) -> list[str | None] | None:
    """Each row's mark ``<img>`` (None where it has none); None when ``mark`` is None."""
    if mark is None:
        return None
    _choice(mark, "mark", ("logo", "headshot", "wordmark"))
    if league is None or mark_col is None:
        raise InputError("mark needs league and a column to read it from (mark_col, or team_col for logos)")
    values = _column(frame, mark_col, "mark_col")
    ids = "espn" if mark == "headshot" else id_system
    return mark_html(values, league=league, kind=mark, height=height, season=None if mark == "headshot" else season,
                     id_system=ids, strict=strict)  # fmt: skip


class _Scale:
    """A column's value range and buckets, computed once per column of the frame (the cell sees its column's name)."""

    def __init__(self, frame: Any, *, by: str | None, min_value: Any, max_value: Any, span: Any, check: bool) -> None:
        for name, v in (("min_value", min_value), ("max_value", max_value)):
            if v is not None and not _real(v):
                raise InputError(f"{name} must be a number, got {v!r}")
        self.frame, self.by, self.min, self.max, self.check = frame, by, min_value, max_value, check
        if by is not None:
            _column(frame, by, "color_by")
        numeric = [c for c in frame.columns if any(_real(v) for v in frame[c].to_list())]
        if span is True:
            self.span: list[str] | None = numeric
        elif span is False or span is None:
            self.span = None
        else:
            self.span = [span] if isinstance(span, str) else list(span)
            if not set(self.span) <= set(numeric):
                raise InputError(f"span names numeric columns of data; numeric columns are {numeric}")
        self._cache: dict[str, tuple[list[float | None], float, float]] = {}

    def values(self, name: str) -> list[float | None]:
        return self._get(name)[0]

    def _get(self, name: str) -> tuple[list[float | None], float, float]:
        if name not in self._cache:
            col = self.by or name
            vals = _numbers(_column(self.frame, col))
            pool = [v for c in self.span for v in _numbers(_column(self.frame, c))] if self.span else vals
            seen = [v for v in pool if v is not None]
            lo, hi = (min(seen), max(seen)) if seen else (math.nan, math.nan)
            if self.check and self.min is not None and seen and self.min > lo:
                raise InputError(f"min_value must be at most the column's minimum ({lo:g}), got {self.min!r}")
            if self.check and self.max is not None and seen and self.max < hi:
                raise InputError(f"max_value must be at least the column's maximum ({hi:g}), got {self.max!r}")
            self._cache[name] = (vals, float(self.min if self.min is not None else lo),
                                 float(self.max if self.max is not None else hi))  # fmt: skip
        return self._cache[name]

    def x(self, name: str, row: int) -> float | None:
        """The row's position on the column's range, 0 to 1 (None if it has no number, or is outside ``span``)."""
        if self.span is not None and name not in self.span:
            return None
        vals, lo, hi = self._get(name)
        v = vals[row]
        return None if v is None else _norm(v, lo, hi)


def _icon(name: str, color: str, size: float, *, style: str = "") -> str:
    extra = f";{style}" if style else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="{size:g}" height="{size:g}" '
            f'fill="{html.escape(color)}" aria-hidden="true" style="vertical-align:middle{extra}">'
            f"{_ICONS[name]}</svg>")  # fmt: skip


def _check_icon(name: Any) -> str:
    if name not in _ICONS:
        raise InputError(f"unknown icon {name!r}; the icons are {', '.join(sorted(_ICONS))}")
    return str(name)


def _place(label: str, icon: str, position: str) -> str:
    """reactablefmtr's icon_position layouts."""
    if position == "right":
        return f'{label}<div style="display:inline-block;margin-left:8px">{icon}</div>'
    if position == "left":
        return f'<div style="display:inline-block;margin-right:8px">{icon}</div>{label}'
    if position == "below":
        return (
            f'<div style="display:grid;position:relative">{label}</div><div style="display:inline-block">{icon}</div>'
        )
    if position == "above":
        return (
            f'<div style="display:inline-block">{icon}</div><div style="display:grid;position:relative">{label}</div>'
        )
    return (f'<div style="position:absolute;display:inline-block">{icon}</div>'
            f'<div style="color:transparent;display:grid;z-index:100;position:relative">{label}</div>')  # fmt: skip


_POSITIONS = ("left", "right", "above", "below", "over")


# --- data bars ----------------------------------------------------------------------------------------------------


def reactable_sdv_data_bars(
    data: Any,
    *,
    fill_color: str | Sequence[str] = _FILL,
    fill_color_ref: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Which = "primary",
    fill_by: str | None = None,
    fill_opacity: float = 1,
    bias: float = 1,
    min_value: float | None = None,
    max_value: float | None = None,
    align: Literal["left", "right"] = "left",
    text_position: TextPosition = "inside-end",
    text_color: str | None = None,
    brighten_text: bool = True,
    bold_text: bool = False,
    number_fmt: NumberFmt = None,
    mark: Mark | None = None,
    mark_col: str | None = None,
    mark_height: float = 20,
    round_edges: bool = False,
    bar_height: float | None = None,
    background: str = "#EEEEEE",
    gradient: bool = False,
    pos_neg: bool = False,
    box_shadow: bool = False,
    tooltip: bool = False,
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
    **column_kwargs: Any,
) -> Column:
    """A reactable column of horizontal bars sized by value, in a scale color, a color column or the team color.

    Each bar is the value's share of the column's largest magnitude, optionally with a logo, headshot or wordmark
    on it.

    Negative values (or ``pos_neg=True``) split the cell at zero: negative bars grow left from a center line, positive
    bars right, colored by the first and last of two ``fill_color`` colors.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable`` (ranges and per-row colors are read from it).
        fill_color: One color, or several colors forming a scale from the column's minimum to its maximum.
        fill_color_ref: A column of ``data`` holding each row's bar color.
        team_col: A column of team values; each bar takes that team's color (``which``). Teams that do not resolve keep
            the scale color.
        league: The SDV league key, e.g. "nfl"; needed by ``team_col`` and ``mark``.
        which: "primary" or "secondary" team color.
        fill_by: Another numeric column whose values set the bar lengths and colors.
        fill_opacity: The bar's opacity, 0 to 1.
        bias: Spacing of the scale's colors; above 1 spreads the high end (``grDevices::colorRamp``).
        min_value: The value of an empty bar; None measures from zero.
        max_value: The value of a full bar; None for the column's largest magnitude.
        align: "left" or "right": the side bars grow from.
        text_position: "inside-end", "outside-end", "inside-base", "outside-base", "center", "above" or "none".
        text_color: The text color; None for black, or white on a dark bar.
        brighten_text: Switch text inside a bar to black or white when ``text_color`` is unreadable on it.
        bold_text: Bold text.
        number_fmt: A function of the value returning its text, or a format spec such as ",.1f".
        mark: "logo", "headshot" or "wordmark": an image at the end of each bar.
        mark_col: The column the mark is read from; defaults to ``team_col``. Headshots need ESPN athlete ids.
        mark_height: The mark's height in pixels.
        round_edges: Round the bar's ends.
        bar_height: The bar's height in pixels; None for 18 (5 with ``text_position="above"``).
        background: The CSS color of the empty track behind each bar.
        gradient: Fill each bar with a left-to-right gradient of ``fill_color`` (two colors or more).
        pos_neg: Split every cell at zero even when no value is negative.
        box_shadow: A drop shadow under each bar.
        tooltip: Give each cell a ``title`` (hover text) of its formatted value.
        season: One season whose team colors and marks to use; None for today's.
        id_system: The id system of ``team_col``/``mark_col``, as in ``resolve``.
        strict: Raise UnresolvedTeamError instead of warning when a team does not resolve.
        **column_kwargs: Passed to ``reactable.Column``; ``id`` names the column drawn.

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer.

    Raises:
        InputError: (a ValueError) If an option is not one of its choices, an opacity is outside [0, 1], ``fill_color``
            is not hex colors, ``gradient`` has fewer than two colors, ``team_col`` or ``mark`` comes without
            ``league``, or ``fill_color_ref`` and ``team_col`` are both given.
        ValueError: If a named column is not in ``data``.
        UnresolvedTeamError: (a ValueError) If ``strict=True`` and a team does not resolve.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_data_bars

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [15, 13, 12]})

            Reactable(df, columns=[reactable_sdv_data_bars(df, team_col="team", league="nfl", mark="logo", id="wins")])

    See Also:
        Equivalent of reactablefmtr::data_bars:
        https://kcuilla.github.io/reactablefmtr/reference/data_bars.html
    """
    frame = _frame(data)
    fills = _hexes(fill_color, "fill_color")
    op = _check_opacity(fill_opacity, "fill_opacity")
    _choice(align, "align", ("left", "right"))
    _choice(text_position, "text_position", ("inside-end", "outside-end", "inside-base", "outside-base", "center",
                                             "above", "none"))  # fmt: skip
    if gradient and len(fills) < 2:
        raise InputError("gradient needs at least two colors in fill_color")
    fmt = _check_fmt(number_fmt)
    h = check_px(bar_height) if bar_height is not None else (5.0 if text_position == "above" else 18.0)
    refs = _row_refs(frame, color_ref=fill_color_ref, team_col=team_col, league=league, which=which, season=season,
                     id_system=id_system, strict=strict)  # fmt: skip
    marks = _row_marks(frame, mark=mark, mark_col=mark_col or team_col, league=league, height=check_px(mark_height),
                       season=season, id_system=id_system, strict=strict)  # fmt: skip
    scale = _Scale(frame, by=fill_by, min_value=None, max_value=None, span=False, check=False)
    radius = f"{h / 2:g}px" if round_edges else "0px"
    shadow = _SHADOW if box_shadow else None
    weight = "bold" if bold_text else "normal"
    grad = f"linear-gradient(to right, {', '.join(_alpha(c, op) for c in fills)})" if gradient else None

    def length(name: str, v: float) -> float:
        vals = [abs(x) for x in scale.values(name) if x is not None]
        top = max_value if max_value is not None else max(vals, default=0.0)
        lo = min_value or 0.0
        pct = 0.0 if top == lo else 100 * (abs(v) - lo) / (top - lo)
        return min(max(pct, 0.0), 100.0)

    def cell(info: CellInfo) -> str:
        name, row = info.column_name, info.row_index
        v = scale.values(name)[row]
        if v is None:
            return "" if _missing(info.value) else html.escape(str(info.value))
        label = _fmt(info.value, fmt)
        two_sided = pos_neg or min((x for x in scale.values(name) if x is not None), default=0.0) < 0
        ref = refs[row] if refs is not None else None
        if ref is not None:
            fill = _alpha(ref, op)
        elif two_sided and len(fills) == 2:
            fill = _alpha(fills[0] if v < 0 else fills[1], op)
        else:
            fill = _alpha(_ramp(fills, scale.x(name, row) or 0.0, bias), op)
        inside = text_position in ("inside-end", "inside-base", "center")
        ink = _ink(fill, text_color, brighten_text) if inside else (text_color or "#000000")
        img = marks[row] if marks is not None else None
        img_html = f'<span style="margin:0 4px;display:inline-flex">{img}</span>' if img else ""
        pct = length(name, v)
        end = "flex-end"
        if align == "right" or (two_sided and v < 0):
            end = "flex-start"
        just = {"inside-end": end, "inside-base": "flex-start" if end == "flex-end" else "flex-end"}.get(
            text_position, "center"
        )
        inner = (img_html if end == "flex-start" else "") + (label if inside else "")
        inner += img_html if end == "flex-end" else ""
        bar_css = _css(display="flex", align_items="center", justify_content=just, width=f"{pct:.4g}%",
                       height=f"{h:g}px", background=fill, background_image=grad, border_radius=radius,
                       box_shadow=shadow, color=ink, white_space="nowrap", transition="width 1s ease")  # fmt: skip
        bar = f'<div style="{bar_css}">{inner}</div>'
        if text_position == "outside-end":  # the label just past the bar's end, inside the track (row-reversed: after)
            bar += f'<span style="margin:0 6px;white-space:nowrap">{label}</span>'
        track_css = _css(display="flex", flex_direction="row-reverse" if end == "flex-start" else "row",
                         align_items="center", flex_grow=1, background=None if two_sided else background,
                         border_radius=radius)  # fmt: skip
        track = f'<div style="{track_css}">{bar}</div>'
        if two_sided:
            half = f'<div style="flex:1 1 0;display:flex">{track}</div>'
            empty = '<div style="flex:1 1 0"></div>'
            axis = '<div style="width:1px;align-self:stretch;background:#666666"></div>'
            body = f'<div style="display:flex;align-items:center">{half if v < 0 else empty}{axis}' + (
                f"{empty if v < 0 else half}</div>"
            )
        elif text_position == "outside-base":
            base = f'<span style="margin-right:6px;white-space:nowrap">{label}</span>'
            body = f'<div style="display:flex;align-items:center">{base}{track}</div>'
        elif text_position == "above":
            body = f'<div style="{_css(text_align=align)}">{label}</div>{track}'
        else:
            body = track
        style = _css(font_weight=weight, color=None if inside else text_color)
        return f'<div style="{style}"{_title(label, tooltip)}>{body}</div>'

    return Column(**{"html": True, **column_kwargs, "cell": cell})


# --- color tiles, scales, pills, bubbles --------------------------------------------------------------------------


class _Colorer:
    """A cell's fill and ink, reactablefmtr's way: a row color (color_ref / team), else even_breaks buckets, else the
    color scale at the value's place on its range."""

    def __init__(self, frame: Any, *, colors: Any, refs: list[str | None] | None, scale: _Scale, bias: float,
                 opacity: float, even_breaks: bool, text_color: str | None, brighten: bool) -> None:  # fmt: skip
        if not _real(bias) or bias <= 0:
            raise InputError(f"bias must be a positive number, got {bias!r}")
        self.colors, self.refs, self.scale, self.bias = _hexes(colors, "colors"), refs, scale, float(bias)
        self.opacity, self.even, self.text, self.brighten = opacity, even_breaks, text_color, brighten
        self._buckets: dict[str, list[int | None]] = {}

    def __call__(self, name: str, row: int) -> tuple[str, str] | None:
        ref = self.refs[row] if self.refs is not None else None
        if ref is not None:
            fill = _alpha(ref, self.opacity)
        elif self.even:
            if name not in self._buckets:
                self._buckets[name] = _ntile(self.scale.values(name), len(self.colors))
            b = self._buckets[name][row]
            if b is None:
                return None
            fill = _alpha(self.colors[b - 1], self.opacity)
        else:
            x = self.scale.x(name, row)
            if x is None:
                return None
            fill = _alpha(_ramp(self.colors, x, self.bias), self.opacity)
        return fill, _ink(fill, self.text, self.brighten)


def _color_setup(
    data: Any, colors: Any, color_ref: str | None, team_col: str | None, league: str | None, which: Which,
    color_by: str | None, bias: float, opacity: float, min_value: Any, max_value: Any, even_breaks: bool, span: Any,
    text_color: str | None, brighten_text: bool, season: Any, id_system: IdSystem, strict: bool,
) -> tuple[Any, _Colorer]:  # fmt: skip
    frame = _frame(data)
    op = _check_opacity(opacity)
    refs = _row_refs(frame, color_ref=color_ref, team_col=team_col, league=league, which=which, season=season,
                     id_system=id_system, strict=strict)  # fmt: skip
    scale = _Scale(frame, by=color_by, min_value=min_value, max_value=max_value, span=span, check=True)
    return frame, _Colorer(frame, colors=colors, refs=refs, scale=scale, bias=bias, opacity=op,
                           even_breaks=even_breaks, text_color=text_color, brighten=brighten_text)  # fmt: skip


def _passthrough(value: Any) -> str:
    return "" if _missing(value) else html.escape(str(value))


def reactable_sdv_color_tiles(
    data: Any,
    *,
    colors: Sequence[str] = _RAMP,
    color_ref: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Which = "primary",
    color_by: str | None = None,
    opacity: float = 1,
    bias: float = 1,
    min_value: float | None = None,
    max_value: float | None = None,
    even_breaks: bool = False,
    number_fmt: NumberFmt = None,
    text_color: str | None = None,
    brighten_text: bool = True,
    show_text: bool = True,
    bold_text: bool = False,
    span: bool | str | Sequence[str] = False,
    box_shadow: bool = False,
    tooltip: bool = False,
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
    **column_kwargs: Any,
) -> Column:
    """A reactable column of rounded tiles filled on a color scale, by a color column, or in the row's team color.

    The text on each tile stays readable.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable`` (ranges and per-row colors are read from it).
        colors: Hex colors forming the scale from the column's minimum to its maximum.
        color_ref: A column of ``data`` holding each row's fill color.
        team_col: A column of team values; each tile takes that team's color (``which``). Teams that do not resolve
            keep the scale color.
        league: The SDV league key, e.g. "nfl"; needed by ``team_col``.
        which: "primary" or "secondary" team color.
        color_by: Another numeric column whose values set the colors.
        opacity: The fill's opacity, 0 to 1.
        bias: Spacing of the scale's colors; above 1 spreads the high end (``grDevices::colorRamp``).
        min_value: The value at the scale's first color; at most the column's minimum.
        max_value: The value at the scale's last color; at least the column's maximum.
        even_breaks: Color by quantile bucket (as many as ``colors``) instead of by value.
        number_fmt: A function of the value returning its text, or a format spec such as ",.1f".
        text_color: The text color; None for black, or white on a dark tile.
        brighten_text: Switch the text to black or white when ``text_color`` is unreadable on the tile.
        show_text: Show the value; False leaves a plain tile.
        bold_text: Bold text.
        span: True scales every numeric column of ``data`` on one shared range; a column name or list of names
            scales those columns together (cells of other columns are left unfilled).
        box_shadow: A drop shadow under each tile.
        tooltip: Give each cell a ``title`` (hover text) of its formatted value.
        season: One season whose team colors to use; None for today's.
        id_system: The id system of ``team_col``, as in ``resolve``.
        strict: Raise UnresolvedTeamError instead of warning when a team does not resolve.
        **column_kwargs: Passed to ``reactable.Column``; ``id`` names the column drawn.

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer.

    Raises:
        InputError: (a ValueError) If ``opacity`` is outside [0, 1], ``bias`` is not positive, ``min_value`` is above
            the column's minimum or ``max_value`` below its maximum (when the ``Reactable`` is built), ``span`` names a
            non-numeric column, ``team_col`` comes without ``league``, or ``color_ref`` and ``team_col`` are both given.
        ValueError: If ``colors`` are not hex colors, or a named column is not in ``data``.
        UnresolvedTeamError: (a ValueError) If ``strict=True`` and a team does not resolve.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_color_tiles

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "epa": [0.12, 0.18, 0.21]})

            Reactable(df, columns=[reactable_sdv_color_tiles(df, number_fmt=".2f", id="epa")])

    See Also:
        Equivalent of reactablefmtr::color_tiles:
        https://kcuilla.github.io/reactablefmtr/reference/color_tiles.html
    """
    _, colorer = _color_setup(data, colors, color_ref, team_col, league, which, color_by, bias, opacity, min_value,
                              max_value, even_breaks, span, text_color, brighten_text, season, id_system,
                              strict)  # fmt: skip
    fmt = _check_fmt(number_fmt)
    shadow = _SHADOW if box_shadow else None

    def cell(info: CellInfo) -> str:
        if colorer.refs is None and color_by is None and not _real(info.value):
            return _passthrough(info.value)
        got = colorer(info.column_name, info.row_index)
        label = _fmt(info.value, fmt)
        if got is None:
            return label if not _missing(info.value) else ""
        fill, ink = got
        style = _css(background=fill, color=ink if show_text else "transparent", display="flex",
                     flex_direction="column", justify_content="center", align_items="center", border_radius="6px",
                     font_weight="bold" if bold_text else "normal", box_shadow=shadow,
                     transition="background 1s ease")  # fmt: skip
        return f'<div style="{style}"{_title(label, tooltip)}>{label}</div>'

    return Column(**{"html": True, **column_kwargs, "cell": cell})


def reactable_sdv_color_scales(
    data: Any,
    *,
    colors: Sequence[str] = _RAMP,
    color_ref: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Which = "primary",
    color_by: str | None = None,
    opacity: float = 1,
    bias: float = 1,
    min_value: float | None = None,
    max_value: float | None = None,
    even_breaks: bool = False,
    number_fmt: NumberFmt = None,
    text_color: str | None = None,
    brighten_text: bool = True,
    show_text: bool = True,
    bold_text: bool = False,
    span: bool | str | Sequence[str] = False,
    tooltip: bool = False,
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
    **column_kwargs: Any,
) -> Column:
    """A reactable column whose cell backgrounds are filled on a color scale, by a color column, or in team colors.

    ``reactable_sdv_color_tiles`` without the tile; the text stays readable.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable`` (ranges and per-row colors are read from it).
        colors: Hex colors forming the scale from the column's minimum to its maximum.
        color_ref: A column of ``data`` holding each row's fill color.
        team_col: A column of team values; each cell takes that team's color (``which``). Teams that do not resolve
            keep the scale color.
        league: The SDV league key, e.g. "nfl"; needed by ``team_col``.
        which: "primary" or "secondary" team color.
        color_by: Another numeric column whose values set the colors.
        opacity: The fill's opacity, 0 to 1.
        bias: Spacing of the scale's colors; above 1 spreads the high end (``grDevices::colorRamp``).
        min_value: The value at the scale's first color; at most the column's minimum.
        max_value: The value at the scale's last color; at least the column's maximum.
        even_breaks: Color by quantile bucket (as many as ``colors``) instead of by value.
        number_fmt: A function of the value returning its text, or a format spec such as ",.1f".
        text_color: The text color; None for black, or white on a dark fill.
        brighten_text: Switch the text to black or white when ``text_color`` is unreadable on the fill.
        show_text: Show the value; False hides it.
        bold_text: Bold text.
        span: True scales every numeric column of ``data`` on one shared range; a column name or list of names
            scales those columns together (cells of other columns are left unfilled).
        tooltip: Give each cell a ``title`` (hover text) of its formatted value.
        season: One season whose team colors to use; None for today's.
        id_system: The id system of ``team_col``, as in ``resolve``.
        strict: Raise UnresolvedTeamError instead of warning when a team does not resolve.
        **column_kwargs: Passed to ``reactable.Column``; ``id`` names the column drawn.

    Returns:
        reactable.Column: The column, with a ``style`` function (and a cell renderer when ``number_fmt`` or
        ``tooltip`` is given).

    Raises:
        InputError: (a ValueError) If ``opacity`` is outside [0, 1], ``bias`` is not positive, ``min_value`` is above
            the column's minimum or ``max_value`` below its maximum (when the ``Reactable`` is built), ``span`` names a
            non-numeric column, ``team_col`` comes without ``league``, or ``color_ref`` and ``team_col`` are both given.
        ValueError: If ``colors`` are not hex colors, or a named column is not in ``data``.
        UnresolvedTeamError: (a ValueError) If ``strict=True`` and a team does not resolve.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_color_scales

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [15, 13, 12]})

            Reactable(df, columns=[reactable_sdv_color_scales(df, team_col="team", league="nfl", id="wins")])

    See Also:
        Equivalent of reactablefmtr::color_scales:
        https://kcuilla.github.io/reactablefmtr/reference/color_scales.html
    """
    _, colorer = _color_setup(data, colors, color_ref, team_col, league, which, color_by, bias, opacity, min_value,
                              max_value, even_breaks, span, text_color, brighten_text, season, id_system,
                              strict)  # fmt: skip
    fmt = _check_fmt(number_fmt)

    def style(info: CellInfo) -> dict[str, str]:
        if colorer.refs is None and color_by is None and not _real(info.value):
            return {}
        got = colorer(info.column_name, info.row_index)
        if got is None:
            return {}
        fill, ink = got
        return {"background": fill, "color": ink if show_text else "transparent",
                "font-weight": "bold" if bold_text else "normal", "transition": "background 1s ease"}  # fmt: skip

    def cell(info: CellInfo) -> str:
        if _missing(info.value):
            return ""
        label = _fmt(info.value, fmt)
        return f"<span{_title(label, tooltip)}>{label}</span>"

    shown = {"html": True, "cell": cell} if fmt is not None or tooltip else {}
    return Column(**{**shown, **column_kwargs, "style": style})


def reactable_sdv_pill_buttons(
    data: Any,
    *,
    colors: str | Sequence[str] = _FILL,
    color_ref: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Which = "primary",
    opacity: float = 1,
    number_fmt: NumberFmt = None,
    text_color: str | None = None,
    brighten_text: bool = True,
    show_text: bool = True,
    bold_text: bool = False,
    box_shadow: bool = False,
    tooltip: bool = False,
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
    **column_kwargs: Any,
) -> Column:
    """A reactable column whose values sit in rounded pills, in a scale color, a color column or the team color.

    Numbers are colored on the scale, text takes the first color.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable`` (ranges and per-row colors are read from it).
        colors: One hex color, or several forming a scale from the column's minimum to its maximum (numbers only).
        color_ref: A column of ``data`` holding each row's pill color.
        team_col: A column of team values; each pill takes that team's color (``which``).
        league: The SDV league key, e.g. "nfl"; needed by ``team_col``.
        which: "primary" or "secondary" team color.
        opacity: The pill's opacity, 0 to 1.
        number_fmt: A function of the value returning its text, or a format spec such as ",.1f".
        text_color: The text color; None for black, or white on a dark pill.
        brighten_text: Switch the text to black or white when ``text_color`` is unreadable on the pill.
        show_text: Show the value; False leaves an empty pill.
        bold_text: Bold text.
        box_shadow: A drop shadow under each pill.
        tooltip: Give each cell a ``title`` (hover text) of its formatted value.
        season: One season whose team colors to use; None for today's.
        id_system: The id system of ``team_col``, as in ``resolve``.
        strict: Raise UnresolvedTeamError instead of warning when a team does not resolve.
        **column_kwargs: Passed to ``reactable.Column``; ``id`` names the column drawn.

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer.

    Raises:
        InputError: (a ValueError) If ``opacity`` is outside [0, 1], ``team_col`` comes without ``league``, or
            ``color_ref`` and ``team_col`` are both given.
        ValueError: If ``colors`` are not hex colors, or a named column is not in ``data``.
        UnresolvedTeamError: (a ValueError) If ``strict=True`` and a team does not resolve.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_pill_buttons

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "conf": ["AFC West", "AFC East", "AFC North"]})

            Reactable(df, columns=[reactable_sdv_pill_buttons(df, team_col="team", league="nfl", id="conf")])

    See Also:
        Equivalent of reactablefmtr::pill_buttons:
        https://kcuilla.github.io/reactablefmtr/reference/pill_buttons.html
    """
    _, colorer = _color_setup(data, colors, color_ref, team_col, league, which, None, 1, opacity, None, None,
                                  False, False, text_color, brighten_text, season, id_system, strict)  # fmt: skip
    fmt = _check_fmt(number_fmt)
    shadow = _SHADOW if box_shadow else None

    def cell(info: CellInfo) -> str:
        if _missing(info.value):
            return ""
        ref = colorer.refs[info.row_index] if colorer.refs is not None else None
        if ref is None and not _real(info.value):  # text: the first color
            fill = _alpha(colorer.colors[0], colorer.opacity)
            got: tuple[str, str] | None = (fill, _ink(fill, text_color, brighten_text))
        else:
            got = colorer(info.column_name, info.row_index)
        label = _fmt(info.value, fmt)
        if got is None:
            return label
        fill, ink = got
        style = _css(background=fill, color=ink if show_text else "transparent", box_shadow=shadow,
                     display="inline-block", padding="2px 12px", border_radius="15px",
                     font_weight="bold" if bold_text else "normal", transition="background 1s ease")  # fmt: skip
        return f'<div style="{style}"{_title(label, tooltip)}>{label}</div>'

    return Column(**{"html": True, **column_kwargs, "cell": cell})


def reactable_sdv_bubble_grid(
    data: Any,
    *,
    shape: Literal["circles", "squares"] = "circles",
    colors: Sequence[str] = _RAMP,
    color_ref: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    which: Which = "primary",
    color_by: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    opacity: float = 1,
    bias: float = 1,
    number_fmt: NumberFmt = None,
    text_color: str | None = None,
    brighten_text: bool = True,
    show_text: bool = True,
    bold_text: bool = False,
    box_shadow: bool = False,
    tooltip: bool = False,
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
    **column_kwargs: Any,
) -> Column:
    """A reactable column of circles (or squares) sized and colored by value, by a color column, or by team.

    A bubble is the value's share of the column's largest magnitude, up to 100 pixels across.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable`` (ranges and per-row colors are read from it).
        shape: "circles" or "squares".
        colors: Hex colors forming the scale from the column's minimum to its maximum.
        color_ref: A column of ``data`` holding each row's bubble color.
        team_col: A column of team values; each bubble takes that team's color (``which``). Teams that do not resolve
            keep the scale color.
        league: The SDV league key, e.g. "nfl"; needed by ``team_col``.
        which: "primary" or "secondary" team color.
        color_by: Another numeric column whose values set the colors and sizes.
        min_value: The value of an empty bubble; None measures from zero.
        max_value: The value of a 100-pixel bubble; None for the column's largest magnitude.
        opacity: The bubble's opacity, 0 to 1.
        bias: Spacing of the scale's colors; above 1 spreads the high end (``grDevices::colorRamp``).
        number_fmt: A function of the value returning its text, or a format spec such as ",.1f".
        text_color: The text color; None for black, or white on a dark bubble.
        brighten_text: Switch the text to black or white when ``text_color`` is unreadable on the bubble.
        show_text: Show the value inside the bubble.
        bold_text: Bold text.
        box_shadow: A drop shadow under each bubble.
        tooltip: Give each cell a ``title`` (hover text) of its formatted value.
        season: One season whose team colors to use; None for today's.
        id_system: The id system of ``team_col``, as in ``resolve``.
        strict: Raise UnresolvedTeamError instead of warning when a team does not resolve.
        **column_kwargs: Passed to ``reactable.Column``; ``id`` names the column drawn.

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer.

    Raises:
        InputError: (a ValueError) If ``shape`` is not "circles"/"squares", ``opacity`` is outside [0, 1], ``bias`` is
            not positive, ``team_col`` comes without ``league``, or ``color_ref`` and ``team_col`` are both given.
        ValueError: If ``colors`` are not hex colors, or a named column is not in ``data``.
        UnresolvedTeamError: (a ValueError) If ``strict=True`` and a team does not resolve.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_bubble_grid

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [15, 13, 12]})

            Reactable(df, columns=[reactable_sdv_bubble_grid(df, team_col="team", league="nfl", id="wins")])

    See Also:
        Equivalent of reactablefmtr::bubble_grid:
        https://kcuilla.github.io/reactablefmtr/reference/bubble_grid.html
    """
    _choice(shape, "shape", ("circles", "squares"))
    _, colorer = _color_setup(data, colors, color_ref, team_col, league, which, color_by, bias, opacity, None, None,
                              False, False, text_color, brighten_text, season, id_system, strict)  # fmt: skip
    for name, v in (("min_value", min_value), ("max_value", max_value)):
        if v is not None and not _real(v):
            raise InputError(f"{name} must be a number, got {v!r}")
    fmt = _check_fmt(number_fmt)
    shadow = _SHADOW if box_shadow else None

    def cell(info: CellInfo) -> str:
        if colorer.refs is None and color_by is None and not _real(info.value):
            return _passthrough(info.value)
        vals = colorer.scale.values(info.column_name)
        v = vals[info.row_index]
        got = colorer(info.column_name, info.row_index)
        label = _fmt(info.value, fmt)
        if v is None or got is None:
            return "" if _missing(info.value) else label
        top = max_value if max_value is not None else max(abs(x) for x in vals if x is not None)
        lo = min_value or 0.0
        size = 0.0 if top == lo else max(0.0, 100 * (abs(v) - lo) / (top - lo))
        fill, ink = got
        style = _css(background=fill, color=ink if show_text else "transparent", display="inline-flex",
                     justify_content="center", align_items="center", text_align="center", height=f"{size:.4g}px",
                     width=f"{size:.4g}px", border_radius="50%" if shape == "circles" else None,
                     font_weight="bold" if bold_text else "normal", box_shadow=shadow,
                     transition="background 1s ease")  # fmt: skip
        return f'<div style="{style}"{_title(label, tooltip)}>{label}</div>'

    return Column(**{"html": True, **column_kwargs, "cell": cell})


# --- icons --------------------------------------------------------------------------------------------------------


def reactable_sdv_icon_sets(
    data: Any,
    *,
    icons: str | Sequence[str] = ("circle",),
    colors: Sequence[str] = _ICON_COLORS,
    opacity: float = 1,
    icon_position: Literal["left", "right", "above", "below", "over"] = "right",
    icon_ref: str | None = None,
    icon_size: float = 16,
    icon_color_ref: str | None = None,
    number_fmt: NumberFmt = None,
    tooltip: bool = False,
    **column_kwargs: Any,
) -> Column:
    """A reactable column that puts an icon beside each number, chosen by the value's quantile bucket.

    The column is cut into as many buckets as ``icons`` (and as ``colors``); each value takes its bucket's icon and
    color.

    The icons are inline SVG: circle, square, diamond, triangle (``triangle-up``), triangle-down, arrow
    (``arrow-right``), arrow-up, arrow-down, arrow-left, chevron-up, chevron-down, star, check, x, flag, minus, plus,
    heart and person.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable`` (buckets are read from it).
        icons: One icon name, or several from the lowest bucket to the highest.
        colors: Hex colors from the lowest bucket to the highest.
        opacity: The icons' opacity, 0 to 1.
        icon_position: "right", "left", "above", "below", or "over" (the icon replaces the value).
        icon_ref: A column of ``data`` holding each row's icon name (overrides ``icons``).
        icon_size: The icon's size in pixels.
        icon_color_ref: A column of ``data`` holding each row's icon color (overrides ``colors``).
        number_fmt: A function of the value returning its text, or a format spec such as ",.1f".
        tooltip: Give each cell a ``title`` (hover text) of its formatted value.
        **column_kwargs: Passed to ``reactable.Column``; ``id`` names the column drawn.

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer.

    Raises:
        InputError: (a ValueError) If an icon or ``icon_position`` is unknown, or ``opacity`` is outside [0, 1].
        ValueError: If ``colors`` are not hex colors, or a named column is not in ``data``.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_icon_sets

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [15, 13, 12]})

            Reactable(df, columns=[reactable_sdv_icon_sets(df, icons=("arrow-down", "minus", "arrow-up"), id="wins")])

    See Also:
        Equivalent of reactablefmtr::icon_sets:
        https://kcuilla.github.io/reactablefmtr/reference/icon_sets.html
    """
    frame = _frame(data)
    names = [_check_icon(i) for i in ([icons] if isinstance(icons, str) else icons)]
    if not names:
        raise InputError("icons needs at least one icon")
    hexes = [_alpha(c, _check_opacity(opacity)) for c in _hexes(colors, "colors")]
    _choice(icon_position, "icon_position", _POSITIONS)
    size = check_px(icon_size)
    fmt = _check_fmt(number_fmt)
    row_icons = _column(frame, icon_ref, "icon_ref") if icon_ref is not None else None
    row_colors = _column(frame, icon_color_ref, "icon_color_ref") if icon_color_ref is not None else None
    buckets: dict[str, tuple[list[int | None], list[int | None]]] = {}
    unknown: set[str] = set()

    def cell(info: CellInfo) -> str:
        if row_icons is None and not _real(info.value):
            return _passthrough(info.value)
        name, row = info.column_name, info.row_index
        if name not in buckets:
            vals = _numbers(_column(frame, name))
            buckets[name] = (_ntile(vals, len(names)), _ntile(vals, len(hexes)))
        ib, cb = buckets[name][0][row], buckets[name][1][row]
        icon_name = str(row_icons[row]) if row_icons is not None else (names[ib - 1] if ib else None)
        color = str(row_colors[row]) if row_colors is not None else (hexes[cb - 1] if cb else None)
        label = _fmt(info.value, fmt) if not _missing(info.value) else ""
        if icon_name is None or color is None:
            return label
        if icon_name not in _ICONS:
            if icon_name not in unknown:
                unknown.add(icon_name)
                warn(f"unknown icon {icon_name!r} in icon_ref; the icons are {', '.join(sorted(_ICONS))}")
            return label
        icon = _icon(icon_name, color, size, style="transition:1s ease")
        return f"<div{_title(label, tooltip)}>{_place(label, icon, icon_position)}</div>"

    return Column(**{"html": True, **column_kwargs, "cell": cell})


def reactable_sdv_icon_assign(
    data: Any,
    *,
    icon: str = "circle",
    fill_color: str = _FILL,
    empty_color: str = "#EEEEEE",
    fill_opacity: float = 1,
    empty_opacity: float = 1,
    align_icons: Literal["left", "right", "center"] = "left",
    icon_size: float = 16,
    buckets: int | None = None,
    number_fmt: NumberFmt = None,
    seq_by: float = 1,
    show_values: Literal["none", "left", "right", "above", "below"] = "none",
    **column_kwargs: Any,
) -> Column:
    """A reactable column that repeats an icon, filled up to the value: a rating in stars, a count in dots.

    A value of 3 in a column whose largest value is 5 shows three filled icons and two empty ones (or, with
    ``buckets``, the value's quantile bucket out of ``buckets``).

    The icons are inline SVG; see ``reactable_sdv_icon_sets`` for the names.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable`` (the column's maximum is read from it).
        icon: The icon's name.
        fill_color: The hex color of a filled icon.
        empty_color: The hex color of an empty icon.
        fill_opacity: The filled icons' opacity, 0 to 1.
        empty_opacity: The empty icons' opacity, 0 to 1.
        align_icons: "left", "right" or "center".
        icon_size: The icon's size in pixels.
        buckets: Cut the column into this many quantile buckets and fill one icon per bucket reached.
        number_fmt: A function of the value returning its text, or a format spec such as ",.1f".
        seq_by: One icon per this many units of value (values are rounded half up first).
        show_values: "none", or where to show the value: "left", "right", "above" or "below".
        **column_kwargs: Passed to ``reactable.Column``; ``id`` names the column drawn.

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer.

    Raises:
        InputError: (a ValueError) If ``icon``, ``align_icons`` or ``show_values`` is unknown, an opacity is outside
            [0, 1], ``buckets`` is not a positive whole number, or ``seq_by`` is not positive.
        ValueError: If a color is not a hex color.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_icon_assign

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "titles": [4, 0, 2]})

            Reactable(df, columns=[reactable_sdv_icon_assign(df, icon="star", show_values="right", id="titles")])

    See Also:
        Equivalent of reactablefmtr::icon_assign:
        https://kcuilla.github.io/reactablefmtr/reference/icon_assign.html
    """
    frame = _frame(data)
    _check_icon(icon)
    full = _alpha(hex6(fill_color), _check_opacity(fill_opacity, "fill_opacity"))
    empty = _alpha(hex6(empty_color), _check_opacity(empty_opacity, "empty_opacity"))
    _choice(align_icons, "align_icons", ("left", "right", "center"))
    _choice(show_values, "show_values", ("none", "left", "right", "above", "below"))
    if buckets is not None and (not isinstance(buckets, numbers.Integral) or isinstance(buckets, bool) or buckets < 1):
        raise InputError(f"buckets must be a whole number of at least 1, got {buckets!r}")
    if not _real(seq_by) or seq_by <= 0:
        raise InputError(f"seq_by must be a positive number, got {seq_by!r}")
    size = check_px(icon_size)
    fmt = _check_fmt(number_fmt)
    on, off = _icon(icon, full, size), _icon(icon, empty, size)
    cache: dict[str, tuple[list[float | None], list[int | None] | None, float]] = {}

    def cell(info: CellInfo) -> str:
        if _missing(info.value):
            return ""
        if not _real(info.value):
            return _passthrough(info.value)
        name, row = info.column_name, info.row_index
        if name not in cache:
            vals = _numbers(_column(frame, name))
            peak = max((math.floor(v + 0.5) for v in vals if v is not None), default=0)
            cache[name] = (vals, _ntile(vals, buckets) if buckets else None, float(peak))
        _, bins, top = cache[name]
        value = float(info.value)
        if bins is not None and buckets is not None:  # reactablefmtr: one icon per bucket, the value's bucket filled
            filled = bins[row] or 0
            steps = [float(i) for i in range(1, buckets + 1)]
            text = f"{filled} out of {buckets}"
        else:  # one icon per seq_by units up to the column's (rounded) maximum
            filled = math.floor(value + 0.5)
            start = 1.0 if top != 0 else 0.0
            steps = [start + k * seq_by for k in range(int((top - start) / seq_by) + 1)] if top >= start else []
            text = f"{_fmt(value, None)} out of {top:g}"
        lit = (lambda i: i <= filled) if top != 0 or bins is not None else (lambda i: i < filled)
        seq = "".join(on if lit(i) else off for i in steps)
        label = _fmt(value, fmt)
        icons = f'<div title="{text}" aria-label="{text}" role="img" style="text-align:{align_icons}">'
        if show_values == "right":
            return f"{icons}{seq} {label}</div>"
        if show_values == "left":
            return f"{icons}{label} {seq}</div>"
        if show_values == "above":
            return f'<div style="text-align:{align_icons}">{label}</div>{icons}{seq}</div>'
        if show_values == "below":
            return f'{icons}{seq}</div><div style="text-align:{align_icons}">{label}</div>'
        return f"{icons}{seq}</div>"

    return Column(**{"html": True, **column_kwargs, "cell": cell})


def reactable_sdv_icon_trend(
    data: Any,
    *,
    icons: Literal["arrow", "chevron", "triangle"] = "arrow",
    colors: Sequence[str] = _TREND_COLORS,
    icon_position: Literal["left", "right", "above", "below", "over"] = "right",
    icon_size: float = 16,
    show_zero_label: bool = False,
    number_fmt: NumberFmt = None,
    opacity: float = 1,
    text_color: str | None = None,
    bold_text: bool = False,
    tooltip: bool = False,
    **column_kwargs: Any,
) -> Column:
    """A reactable column that marks each change with an up arrow, a down arrow or a dash, the value colored to match.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable``.
        icons: "arrow", "chevron" or "triangle".
        colors: Three hex colors: down, zero, up.
        icon_position: "right", "left", "above", "below", or "over" (the icon replaces the value).
        icon_size: The icon's size in pixels.
        show_zero_label: Show the value when it is zero (otherwise only the dash).
        number_fmt: A function of the value returning its text, or a format spec such as "+.1f".
        opacity: The icons' opacity, 0 to 1.
        text_color: One color for every value's text; None colors it like its icon.
        bold_text: Bold text.
        tooltip: Give each cell a ``title`` (hover text) of its formatted value.
        **column_kwargs: Passed to ``reactable.Column``; ``id`` names the column drawn.

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer.

    Raises:
        InputError: (a ValueError) If ``icons`` or ``icon_position`` is unknown, ``colors`` is not three colors, or
            ``opacity`` is outside [0, 1].
        ValueError: If ``colors`` are not hex colors.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_icon_trend

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "win_change": [4, 0, -3]})

            Reactable(df, columns=[reactable_sdv_icon_trend(df, number_fmt="+d", id="win_change")])

    See Also:
        Equivalent of reactablefmtr::icon_trend_indicator:
        https://kcuilla.github.io/reactablefmtr/reference/icon_trend_indicator.html
    """
    _choice(icons, "icons", _TRENDS)
    _choice(icon_position, "icon_position", _POSITIONS)
    hexes = [_alpha(c, _check_opacity(opacity)) for c in _hexes(colors, "colors")]
    if len(hexes) != 3:
        raise InputError(f"colors must be three colors (down, zero, up), got {len(hexes)}")
    size = check_px(icon_size)
    fmt = _check_fmt(number_fmt)
    del data  # the trend needs no range; data is taken for the same call shape as the other formatters
    weight = "bold" if bold_text else "normal"

    def cell(info: CellInfo) -> str:
        if not _real(info.value):
            return _passthrough(info.value)
        v = float(info.value)
        k, name = (0, f"{icons}-down") if v < 0 else (2, f"{icons}-up") if v > 0 else (1, "minus")
        if icons == "arrow" and v != 0:
            name = "arrow-up" if v > 0 else "arrow-down"
        label = _fmt(info.value, fmt)
        shown = "" if v == 0 and not show_zero_label else label
        text = f'<span style="{_css(color=text_color or hexes[k], font_weight=weight)}">{shown}</span>'
        icon = _icon(name, hexes[k], size, style="transition:1s ease")
        return f"<div{_title(label, tooltip)}>{_place(text, icon, icon_position)}</div>"

    return Column(**{"html": True, **column_kwargs, "cell": cell})


# --- merge column and highlights ----------------------------------------------------------------------------------


def reactable_sdv_merge_column(
    data: Any,
    *,
    merged_name: str,
    merged_position: Literal["right", "left", "above", "below"] = "right",
    merged_size: float = 12,
    merged_color: str = "#777",
    merged_weight: Literal["normal", "bold"] = "normal",
    size: float = 14,
    color: str | None = None,
    weight: Literal["normal", "bold"] = "bold",
    spacing: float = 0,
    mark: Mark | None = None,
    mark_col: str | None = None,
    team_col: str | None = None,
    league: str | None = None,
    mark_height: float = 30,
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
    **column_kwargs: Any,
) -> Column:
    """A reactable column that shows a second column's value beside or below each value, after an optional mark.

    A player and his team, a team and its record; the mark is the row's logo, headshot or wordmark.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable`` (the merged values are read from it).
        merged_name: The column of ``data`` merged into this one (hide it with ``Column(show=False)`` if it is shown).
        merged_position: "right", "left", "above" or "below".
        merged_size: The merged text's size in pixels.
        merged_color: The merged text's CSS color.
        merged_weight: "normal" or "bold" for the merged text.
        size: The main text's size in pixels.
        color: The main text's CSS color; None inherits the table's.
        weight: "normal" or "bold" for the main text.
        spacing: Extra pixels between the two values.
        mark: "logo", "headshot" or "wordmark": an image before the text.
        mark_col: The column the mark is read from; defaults to ``team_col``, then this column. Headshots need ESPN
            athlete ids.
        team_col: A column of team values for the logo or wordmark.
        league: The SDV league key, e.g. "nfl"; needed by ``mark``.
        mark_height: The mark's height in pixels.
        season: One season whose marks to use; None for today's.
        id_system: The id system of the mark's column, as in ``resolve``.
        strict: Raise UnresolvedTeamError instead of warning when a team does not resolve.
        **column_kwargs: Passed to ``reactable.Column``; ``id`` names the column drawn.

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer.

    Raises:
        InputError: (a ValueError) If ``merged_position``, a weight or ``mark`` is unknown, or ``mark`` comes without
            ``league`` or a column to read it from.
        ValueError: If a named column is not in ``data``.
        UnresolvedTeamError: (a ValueError) If ``strict=True`` and a team does not resolve.

    Example:
        ::

            import pandas as pd
            from reactable import Column, Reactable
            from sdvplot.reactable import reactable_sdv_merge_column

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "record": ["15-2", "13-4", "12-5"]})

            Reactable(
                df,
                columns=[
                    reactable_sdv_merge_column(df, merged_name="record", merged_position="below", mark="logo",
                                               team_col="team", league="nfl", id="team"),
                    Column(id="record", show=False),
                ],
            )

    See Also:
        Equivalent of reactablefmtr::merge_column:
        https://kcuilla.github.io/reactablefmtr/reference/merge_column.html
    """
    frame = _frame(data)
    merged = _column(frame, merged_name, "merged_name")
    _choice(merged_position, "merged_position", ("right", "left", "above", "below"))
    _choice(weight, "weight", ("normal", "bold"))
    _choice(merged_weight, "merged_weight", ("normal", "bold"))
    for name, v in (("size", size), ("merged_size", merged_size), ("spacing", spacing)):
        if not _real(v) or v < 0:
            raise InputError(f"{name} must be a number of pixels, got {v!r}")
    main_css = _css(font_size=f"{size:g}px", color=color, font_weight=weight)
    sub_css = _css(font_size=f"{merged_size:g}px", color=merged_color, font_weight=merged_weight)
    gap = f"{spacing + 3:g}px"
    source = mark_col or team_col or column_kwargs.get("id")
    marks = _row_marks(frame, mark=mark, mark_col=source, league=league, height=check_px(mark_height), season=season,
                       id_system=id_system, strict=strict)  # fmt: skip

    def cell(info: CellInfo) -> str:
        value, other = _passthrough(info.value), _passthrough(merged[info.row_index])
        if merged_position == "below":
            text = f'<div style="{main_css};margin-bottom:{gap}">{value}</div><div style="{sub_css}">{other}</div>'
        elif merged_position == "above":
            text = f'<div style="{sub_css};margin-bottom:{gap}">{other}</div><div style="{main_css}">{value}</div>'
        elif merged_position == "left":
            text = f'<span style="{sub_css};margin-right:{gap}">{other}</span><span style="{main_css}">{value}</span>'
        else:
            text = f'<span style="{main_css};margin-right:{gap}">{value}</span><span style="{sub_css}">{other}</span>'
        img = marks[info.row_index] if marks is not None else None
        if img is None:
            return f"<div>{text}</div>"
        return f'<div style="display:flex;align-items:center;gap:8px">{img}<div>{text}</div></div>'

    return Column(**{"html": True, **column_kwargs, "cell": cell})


def reactable_sdv_highlight(
    data: Any,
    *,
    which: Literal["max", "min", "min_max"] = "max",
    font_color: str | tuple[str, str] | None = None,
    highlighter: str | tuple[str | None, str | None] | None = None,
    **column_kwargs: Any,
) -> Column:
    """A reactable column whose highest (or lowest, or both) values are bold, in a color, optionally on a highlight.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable`` (the column's extremes are read from it).
        which: "max", "min", or "min_max" for both.
        font_color: The CSS text color; None for green on the maximum and red on the minimum. For "min_max", a
            ``(min, max)`` pair.
        highlighter: A CSS background color, or a ``(min, max)`` pair for "min_max"; None for no background.
        **column_kwargs: Passed to ``reactable.Column``; ``id`` names the column drawn.

    Returns:
        reactable.Column: The column, with a ``style`` function.

    Raises:
        InputError: (a ValueError) If ``which`` is unknown, or a pair is not two values.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_highlight

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [15, 13, 12]})

            Reactable(df, columns=[reactable_sdv_highlight(df, which="min_max", id="wins")])

    See Also:
        Equivalent of reactablefmtr::highlight_max, highlight_min and highlight_min_max:
        https://kcuilla.github.io/reactablefmtr/reference/highlight_min_max.html
    """
    _choice(which, "which", ("max", "min", "min_max"))

    def pair(value: Any, default: tuple[Any, Any], name: str) -> tuple[Any, Any]:
        if value is None:
            return default
        if which == "min_max":
            if isinstance(value, str) or len(value) != 2:
                raise InputError(f"{name} for which='min_max' is a (min, max) pair, got {value!r}")
            return value[0], value[1]
        return (value, value)

    lo_color, hi_color = pair(font_color, ("red", "green"), "font_color")
    lo_bg, hi_bg = pair(highlighter, (None, None), "highlighter")
    frame = _frame(data)
    extremes: dict[str, tuple[float, float]] = {}

    def style(info: CellInfo) -> dict[str, str]:
        if not _real(info.value):
            return {}
        name = info.column_name
        if name not in extremes:
            seen = [v for v in _numbers(_column(frame, name)) if v is not None]
            extremes[name] = (min(seen), max(seen))
        lo, hi = extremes[name]
        v = float(info.value)
        if which in ("min", "min_max") and v == lo:
            color, bg = lo_color, lo_bg
        elif which in ("max", "min_max") and v == hi:
            color, bg = hi_color, hi_bg
        else:
            return {}
        return {"font-weight": "bold", "color": color, **({"background": bg} if bg is not None else {})}

    return Column(**{**column_kwargs, "style": style})

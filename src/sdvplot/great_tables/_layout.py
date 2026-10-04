"""Legends, layout and annotation helpers for great_tables, ported from sdvplotR's ``gt_*`` functions (wave C2)."""

from __future__ import annotations

import base64
import copy
import dataclasses
import datetime
import functools
import importlib.metadata
import math
import random
import string
import textwrap
import warnings
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

import faicons
import narwhals as nw
import polars as pl
from great_tables import GT, google_font, html, loc
from great_tables import style as gst

# private great_tables API: the column/row resolvers its own methods use (pinned by test_private_great_tables_api)
from great_tables._locations import resolve_cols_c, resolve_rows_i

from sdvplot._contrast import contrast, hex6, mix, on_color
from sdvplot._errors import SdvplotWarning

_STYLE_KEYS = (
    "font",
    "size",
    "color",
    "weight",
    "italic",
    "spacing",
    "transform",
    "align",
    "line_height",
    "margin_top",
    "margin_bottom",
    "padding_top",
    "padding_bottom",
)
_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".gif": "image/gif"}


def _check_gt(gt: object) -> None:
    """sdvplotR's ``.check_gt``: every public function takes a GT, never raw data."""
    if not isinstance(gt, GT):
        raise TypeError(f"gt must be a great_tables.GT, not {type(gt).__name__}; wrap a data frame with GT(df) first")


def _style(default: Mapping[str, Any], user: Mapping[str, Any] | None) -> dict[str, Any]:
    """A style dict (sdvplotR's ``*_style`` lists): the defaults with the caller's keys on top."""
    user = dict(user or {})
    unknown = sorted(set(user) - set(_STYLE_KEYS))
    if unknown:
        raise ValueError(f"unknown style key(s) {unknown}; the keys are {', '.join(_STYLE_KEYS)}")
    return {**default, **user}


def _css_len(value: Any) -> str:
    """A number reads as pixels; anything else is a CSS length already."""
    return f"{value}px" if isinstance(value, int | float) and not isinstance(value, bool) else str(value)


def _style_css(s: Mapping[str, Any]) -> str:
    """Inline CSS for a style dict (sdvplotR's ``.style_css`` with no font fallback, so text inherits the theme's)."""
    out = []
    if s.get("font") is not None:
        out.append(f"font-family:'{s['font']}', sans-serif;")
    plain = {"color": "color", "weight": "font-weight", "transform": "text-transform", "align": "text-align"}
    lengths = {
        "size": "font-size",
        "spacing": "letter-spacing",
        "margin_top": "margin-top",
        "margin_bottom": "margin-bottom",
        "padding_top": "padding-top",
        "padding_bottom": "padding-bottom",
    }
    for key in _STYLE_KEYS:
        value = s.get(key)
        if value is None:
            continue
        if key in plain:
            out.append(f"{plain[key]}:{value};")
        elif key in lengths:
            out.append(f"{lengths[key]}:{_css_len(value)};")
        elif key == "italic" and value is True:
            out.append("font-style:italic;")
        elif key == "line_height":
            out.append(f"line-height:{value};")
    return "".join(out)


def _fonts(*styles: Mapping[str, Any]) -> list[str]:
    """The distinct Google font names across style dicts, in order."""
    return list(dict.fromkeys(s["font"] for s in styles if s.get("font") is not None))


def _with_fonts(gt: GT, fonts: list[str], location: Any) -> GT:
    """Load Google fonts through great_tables, so the inline ``font-family`` references resolve."""
    for font in fonts:
        gt = gt.tab_style(gst.text(font=google_font(font)), location)
    return gt


def _choice(name: str, value: str, options: tuple[str, ...]) -> str:
    """R's ``match.arg``: ``value`` must be one of ``options``."""
    if value not in options:
        raise ValueError(f"{name} must be one of {', '.join(map(repr, options))}, got {value!r}")
    return value


def _columns(gt: GT, columns: Any) -> list[str]:
    """The data columns a great_tables column selection names (``None`` selects every column)."""
    return resolve_cols_c(data=gt, expr=columns)


def _rows(gt: GT, rows: Any) -> list[int]:
    """The 0-based row positions a great_tables row selection names (``None`` selects every row)."""
    return [i for _, i in resolve_rows_i(gt, rows)]


def _frame(gt: GT) -> nw.DataFrame[Any]:
    """The table's data (pandas or polars) as a narwhals frame."""
    return nw.from_native(gt._tbl_data, eager_only=True)


def _number(value: Any) -> float | None:
    """R's ``as.numeric``: a float, or ``None`` for missing and non-numeric values (None, NaN, pd.NA, "abc")."""
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else x


def _numbers(gt: GT, column: str) -> list[float | None]:
    return [_number(v) for v in _frame(gt)[column].to_list()]


def _strings(gt: GT, column: str) -> list[str | None]:
    """A column's values as strings, ``None`` where missing (None, NaN in pandas, pd.NA)."""
    series = _frame(gt)[column]
    return [None if null else str(v) for v, null in zip(series.to_list(), series.is_null().to_list(), strict=True)]


def _palette(palette: Any) -> list[str]:
    """A palette as a list of ``#rrggbb`` colors (sdvplotR also takes paletteer names, which are R-only)."""
    if isinstance(palette, str):
        raise ValueError(f"palette must be a list of hex colors, not the string {palette!r}")
    colors = [hex6(c) for c in palette]
    if not colors:
        raise ValueError("palette is empty")
    return colors


def _ramp(palette: list[str], t: float) -> str:
    """The color ``t`` (0-1) of the way along ``palette``: piecewise-linear sRGB between evenly spaced stops, the
    ramp great_tables' ``data_color`` draws."""
    if len(palette) == 1:
        return palette[0]
    pos = min(max(t, 0.0), 1.0) * (len(palette) - 1)
    i = min(int(pos), len(palette) - 2)
    return mix(palette[i], palette[i + 1], pos - i)


def _record(gt: GT, name: str, value: Any) -> GT:
    """A copy of ``gt`` carrying ``value`` as attribute ``name`` (``_sdvplot_scale``, ``_sdvplot_key``)."""
    out = copy.copy(gt)
    out.__dict__[name] = value
    return out


def _background(gt: GT) -> str:
    """The table background as ``#rrggbb``; white when it is unset or not a hex color."""
    try:
        return hex6(str(gt._options.table_background_color.value))
    except ValueError:
        return "#ffffff"


def _secondary_on(bg: str, fg: str, target: float = 4.5) -> str:
    """Muted but legible text: ``fg`` blended into ``bg`` until it clears ``target`` contrast."""
    for step in range(12):
        candidate = mix(bg, fg, (45 + 5 * step) / 100)
        if contrast(candidate, bg) >= target:
            return candidate
    return fg


def _text(value: Any) -> str | None:
    """A heading part (``str``, great_tables ``Html``/``Md`` or ``None``) as its text; ``None`` when empty."""
    text = getattr(value, "text", value)
    return str(text) if text is not None and str(text) else None


def _in_header(gt: GT, block: str, fonts: list[str]) -> GT:
    """Put ``block`` at the top: as the title if the table has none, else under the title and subtitle."""
    heading = gt._heading
    old_title, old_subtitle = _text(heading.title), _text(heading.subtitle)
    if old_title is None:
        return _with_fonts(gt.tab_header(title=html(block), preheader=heading.preheader), fonts, loc.title())
    spacer = "" if old_subtitle is None else '<div style="height:4px;"></div>'
    out = gt.tab_header(
        title=html(old_title), subtitle=html((old_subtitle or "") + spacer + block), preheader=heading.preheader
    )
    return _with_fonts(out, fonts, loc.subtitle())


_JUSTIFY = {"left": "flex-start", "right": "flex-end", "center": "center"}
_RANK_PALETTE = ("#3D8B6E", "#9DC5A7", "#EDE0CC", "#DB9070", "#BE4D3A")


def _table_id(gt: GT) -> tuple[GT, str]:
    """The table's id, assigning a random one when it has none (scoped CSS needs it)."""
    table_id = gt._options.table_id.value
    if table_id is None:
        table_id = "".join(random.choices(string.ascii_lowercase, k=10))
        gt = gt.with_id(table_id)
    return gt, table_id


def gt_title_header(
    gt: GT,
    title: str,
    subtitle: str | None = None,
    kicker: str | None = None,
    date: datetime.date | str | None = None,
    kicker_style: Mapping[str, Any] | None = None,
    title_style: Mapping[str, Any] | None = None,
    subtitle_style: Mapping[str, Any] | None = None,
    date_style: Mapping[str, Any] | None = None,
) -> GT:
    """Add a styled header: an optional kicker line, the title, the subtitle and a date line.

    Each element takes a style dict with the keys ``font`` (a Google font name), ``size``, ``color``, ``weight``,
    ``italic``, ``spacing`` (letter spacing), ``transform`` (e.g. ``"uppercase"``), ``align``, ``line_height``,
    ``margin_top``, ``margin_bottom``, ``padding_top`` and ``padding_bottom``. A number is read as pixels; a string is
    any CSS length.

    Args:
        gt: The table.
        title: The title text (HTML allowed).
        subtitle: The subtitle text.
        kicker: A short line above the title, uppercase red by default.
        date: A date under the subtitle; a ``datetime.date`` prints as "July 21, 2026", anything else as given.
        kicker_style: Styles the kicker.
        title_style: Styles the title.
        subtitle_style: Styles the subtitle.
        date_style: Styles the date (small gray by default).

    Returns:
        GT: A new table whose header holds the styled block (it replaces any existing header).

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.
        ValueError: If a style dict has an unknown key.

    Example:
        ::

            import datetime
            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_title_header

            gt = gt_title_header(GT(pl.DataFrame({"team": ["LV"]})), "Week 5", subtitle="Power ranking",
                                 kicker="NFL", date=datetime.date(2026, 10, 4))

    See Also:
        Ported from sdvplotR ``gt_title_header()``: https://sdvplotR.sportsdataverse.org/reference/gt_title_header.html
    """
    _check_gt(gt)
    s_kicker = _style(
        {"size": "0.75em", "weight": 700, "color": "#C84630", "transform": "uppercase", "spacing": "0.08em"},
        kicker_style,
    )
    s_title = _style({}, title_style)
    s_subtitle = _style({}, subtitle_style)
    s_date = _style({"size": "0.85em", "weight": 400, "color": "#8A8A8A"}, date_style)

    kicker_html = "" if kicker is None else f'<div style="{_style_css(s_kicker)}margin-bottom:0.15em;">{kicker}</div>'
    title_full = f'{kicker_html}<div style="{_style_css(s_title)}">{title}</div>'
    subtitle_html = "" if subtitle is None else f'<div style="{_style_css(s_subtitle)}">{subtitle}</div>'
    date_html = ""
    if date is not None:
        shown = date.strftime("%B %d, %Y") if isinstance(date, datetime.date) else str(date)
        date_html = f'<div style="{_style_css(s_date)}margin-top:0.15em;">{shown}</div>'
    subtitle_full = subtitle_html + date_html

    out = gt.tab_header(title=html(title_full), subtitle=html(subtitle_full) if subtitle_full else None)
    return _with_fonts(out, _fonts(s_kicker, s_title, s_subtitle, s_date), loc.title())


def gt_set_font(
    gt: GT,
    font_family: str,
    from_google_font: bool = True,
    weight: str | int | None = None,
    style: str | None = None,
) -> GT:
    """Set one font family (and optionally a weight and style) on every part of the table.

    Args:
        gt: The table.
        font_family: The font family.
        from_google_font: Load ``font_family`` from Google Fonts; ``False`` uses a font the viewer has installed.
        weight: A font weight for every part (``"bold"`` or a number such as 600); ``None`` leaves it alone.
        style: ``"normal"``, ``"italic"`` or ``"oblique"``; ``None`` leaves it alone.

    Returns:
        GT: A new table with the font set on the title, stubhead, spanners, column labels, row groups, stub, body,
        footnotes and source notes (summary rows are left alone, as in sdvplotR).

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_set_font

            gt = gt_set_font(GT(pl.DataFrame({"team": ["LV"]})), "Roboto Condensed", weight=600)

    See Also:
        Ported from sdvplotR ``gt_set_font()``: https://sdvplotR.sportsdataverse.org/reference/gt_set_font.html
    """
    _check_gt(gt)
    family = google_font(font_family) if from_google_font else font_family
    locations = [
        loc.title(),
        loc.subtitle(),
        loc.stubhead(),
        loc.spanner_labels(ids=[s.spanner_id for s in gt._spanners]),
        loc.column_labels(),
        loc.row_groups(),
        loc.stub(),
        loc.body(),
        loc.footnotes(),
        loc.source_notes(),
    ]
    # great_tables types weight as a keyword Literal, but writes any value into font-weight (600 verified)
    return gt.tab_style(gst.text(font=family, weight=weight, style=style), locations)  # type: ignore[arg-type]


def _watermark_svg(text: str, color: str, opacity: float, angle: float, font: str) -> tuple[str, bool]:
    """An inline SVG text mark as a ``data:`` URI, and whether the rotated box is taller than wide."""
    label = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    size = 100
    text_w = max(len(label) * size * 0.62, size)
    text_h = size * 1.3
    rad = abs(angle) * math.pi / 180
    w = math.ceil(text_w * math.cos(rad) + text_h * math.sin(rad)) + 4
    h = math.ceil(text_w * math.sin(rad) + text_h * math.cos(rad)) + 4
    rot = f' transform="rotate({angle:g} {w / 2:g} {h / 2:g})"' if angle != 0 else ""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
        f'<text x="50%" y="50%" text-anchor="middle" dominant-baseline="central" font-family="{font}" '
        f'font-size="{size}" font-weight="700" fill="{color}" fill-opacity="{opacity:g}"{rot}>{label}</text></svg>'
    )
    return "data:image/svg+xml," + quote(svg, safe=""), h > w


def gt_watermark(
    gt: GT,
    text: str | None = None,
    image: str | Path | None = None,
    opacity: float = 0.06,
    size: str = "60%",
    position: str = "center",
    color: str = "#000000",
    angle: float = 0,
    font: str = "Helvetica, Arial, sans-serif",
) -> GT:
    """Put a faint text or image watermark behind the table body.

    Args:
        gt: The table.
        text: Text to draw as the watermark (an inline SVG, so ``font`` must be a font the viewer has).
        image: Instead of ``text``, a PNG, JPEG, SVG or GIF file, embedded as a ``data:`` URI.
        opacity: How faint the watermark is, 0 to 1.
        size: The watermark's size relative to the table body, as a CSS background size.
        position: Where it sits, as a CSS background position (``"center"``, ``"right bottom"``).
        color: The text color (``text`` only).
        angle: Rotation in degrees (``text`` only).
        font: The font family for ``text``.

    Returns:
        GT: A new table with the watermark as the body's CSS background (the table gets an id if it had none).

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.
        ValueError: If neither or both of ``text`` and ``image`` are given, or ``image`` is not a supported type.
        FileNotFoundError: If ``image`` does not exist.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_watermark

            gt = gt_watermark(GT(pl.DataFrame({"team": ["LV"]})), text="DRAFT", angle=-30)

    See Also:
        Ported from sdvplotR ``gt_watermark()``: https://sdvplotR.sportsdataverse.org/reference/gt_watermark.html
    """
    _check_gt(gt)
    if (text is None) == (image is None):
        raise ValueError("supply exactly one of text or image")
    gt, table_id = _table_id(gt)
    tall = False
    extra = ""
    if image is None:
        uri, tall = _watermark_svg(str(text), color, opacity, angle, font)
    else:
        path = Path(image)
        if not path.exists():
            raise FileNotFoundError(f"can't find the watermark image {path}")
        mime = _MIME.get(path.suffix.lower())
        if mime is None:
            raise ValueError(f"image must be a PNG, JPEG, SVG or GIF, not {path.name}")
        uri = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")
        extra = f" opacity: {opacity:g};"
    fit = f"auto {size}" if tall else f"{size} auto"
    return gt.opt_css(
        f"#{table_id} .gt_table_body {{ background-image: url('{uri}'); background-repeat: no-repeat;"
        f" background-position: {position}; background-size: {fit};{extra} }}"
    )


def gt_legend_continuous(
    gt: GT,
    columns: Any = None,
    palette: Sequence[str] | None = None,
    domain: Sequence[float] | None = None,
    reverse: bool | None = None,
    pal_type: str | None = None,
    type: str = "continuous",
    n_bins: int = 5,
    labels: str | Sequence[str] | None = None,
    digits: int = 0,
    title: str | None = None,
    title_position: str = "top",
    title_style: Mapping[str, Any] | None = None,
    labels_style: Mapping[str, Any] | None = None,
    labels_position: str = "bottom",
    location: str = "bottom",
    align: str = "center",
    width: float = 200,
    height: float = 10,
    border_color: str | None = None,
    border_width: float = 1,
    radius: float = 2,
    gap: float = 3,
    title_gap: float = 4,
    block_gap: float = 2,
) -> GT:
    """Add a color-scale legend that matches a column colored by ``gt_color_ranks``, ``gt_color_pills``,
    ``gt_percentile_bar`` or ``GT.data_color``.

    Those three sdvplot functions record the scale they used on the table (``_sdvplot_scale``); every argument left
    as ``None`` here is taken from that record, so ``gt_legend_continuous(gt)`` cannot disagree with the cells. The
    bar is a row of solid segments (CSS gradients do not survive every renderer), colored by the same piecewise-linear
    ramp great_tables' ``data_color`` uses. Style dicts take the keys listed in ``gt_title_header``.

    Args:
        gt: The table.
        columns: The column selection the legend describes, used to derive ``domain``. Defaults to the recorded one.
        palette: Hex colors spread over ``domain``. Defaults to the recorded palette, else sdvplotR's five-color
            green-to-red ramp.
        domain: ``(low, high)``. Defaults to the recorded domain, else the range of ``columns``.
        reverse: Reverse the palette. Defaults to the recorded value, else ``False``.
        pal_type: ``"discrete"`` or ``"continuous"``; kept for sdvplotR parity (it picks a paletteer registry in R).
        type: ``"continuous"`` (a smooth ramp), ``"steps"`` (``n_bins`` touching steps) or ``"blocks"`` (separated).
        n_bins: The number of steps or blocks.
        labels: ``None`` labels the two ends of ``domain``; ``"edges"`` labels the ``n_bins + 1`` bin edges; a list
            of strings is spread evenly.
        digits: Decimal places of derived labels.
        title: A caption for the legend.
        title_position: ``"top"``, ``"bottom"``, ``"left"`` or ``"right"`` of the bar.
        title_style: Styles the title (default 11px gray).
        labels_style: Styles the labels (default 10px gray).
        labels_position: ``"bottom"``, ``"top"`` or ``"none"``.
        location: ``"bottom"`` adds the legend as a source note; ``"top"`` puts it in the header, under any title.
        align: ``"center"``, ``"left"`` or ``"right"``.
        width: The bar width in pixels.
        height: The bar height in pixels.
        border_color: A border around the bar (each block, for ``"blocks"``).
        border_width: The border width in pixels.
        radius: The corner radius in pixels.
        gap: Pixels between the bar and its labels.
        title_gap: Pixels between the title and the bar.
        block_gap: Pixels between blocks.

    Returns:
        GT: A new table with the legend added.

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.
        ValueError: If neither a domain nor numeric ``columns`` can be found, an option is not one of its choices,
            ``n_bins`` is below 1, or a palette color is not hex.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_legend_continuous, gt_percentile_bar

            gt = gt_percentile_bar(GT(pl.DataFrame({"pct": [94, 41, 72]})), "pct")
            gt = gt_legend_continuous(gt, title="Percentile")   # palette and domain come from the bars

    See Also:
        Ported from sdvplotR ``gt_legend_continuous()``:
        https://sdvplotR.sportsdataverse.org/reference/gt_legend_continuous.html
    """
    _check_gt(gt)
    _choice("type", type, ("continuous", "steps", "blocks"))
    _choice("title_position", title_position, ("top", "bottom", "left", "right"))
    _choice("labels_position", labels_position, ("bottom", "top", "none"))
    _choice("location", location, ("bottom", "top"))
    _choice("align", align, ("center", "left", "right"))
    if n_bins < 1:
        raise ValueError("n_bins must be at least 1")

    rec = gt.__dict__.get("_sdvplot_scale") or {}
    columns = rec.get("columns") if columns is None else columns
    palette = rec.get("palette", _RANK_PALETTE) if palette is None else palette
    domain = rec.get("domain") if domain is None else domain
    reverse = rec.get("reverse", False) if reverse is None else reverse
    pal = _palette(palette)[:: -1 if reverse else 1]

    if domain is None:
        if columns is None:
            raise ValueError(
                "need columns or domain to know what the legend spans; color the table with gt_color_ranks, "
                "gt_color_pills or gt_percentile_bar first and the legend picks the scale up"
            )
        values = [v for c in _columns(gt, columns) for v in _numbers(gt, c) if v is not None]
        if not values:
            raise ValueError("no numeric values found in columns; pass domain directly")
        domain = (min(values), max(values))
    if len(domain) != 2:
        raise ValueError(f"domain must be (low, high), got {domain!r}")
    lo, hi = float(domain[0]), float(domain[1])

    s_title = _style({"size": "11px", "color": "#666666"}, title_style)
    s_labels = _style({"size": "10px", "color": "#666666"}, labels_style)

    if labels is None:
        texts = [f"{v:,.{digits}f}" for v in (lo, hi)]
    elif isinstance(labels, str) and labels == "edges":
        texts = [f"{lo + (hi - lo) * k / n_bins:,.{digits}f}" for k in range(n_bins + 1)]
    else:
        texts = [str(x) for x in ([labels] if isinstance(labels, str) else labels)]

    border = "" if border_color is None else f"border:{border_width:g}px solid {border_color};"
    if type == "continuous":
        colors = [_ramp(pal, k / 59) for k in range(60)]
    else:
        colors = [_ramp(pal, (k + 0.5) / n_bins) for k in range(n_bins)]
    if type == "blocks":
        segments = "".join(
            f'<span style="flex:1 0 auto; height:{height:g}px; background-color:{c}; border-radius:{radius:g}px; '
            f'{border}"></span>'
            for c in colors
        )
        bar = f'<div style="display:flex; width:{width:g}px; gap:{block_gap:g}px;">{segments}</div>'
    else:
        segments = "".join(f'<span style="flex:1 0 auto; background-color:{c};"></span>' for c in colors)
        bar = (
            f'<div style="display:flex; width:{width:g}px; height:{height:g}px; border-radius:{radius:g}px; '
            f'overflow:hidden; {border}">{segments}</div>'
        )

    labels_html = ""
    if labels_position != "none" and len(texts) == 1:
        labels_html = f'<div style="width:{width:g}px; {_style_css(s_labels)} text-align:center;">{texts[0]}</div>'
    elif labels_position != "none" and texts:
        spans = "".join(f"<span>{t}</span>" for t in texts)
        labels_html = (
            f'<div style="display:flex; width:{width:g}px; justify-content:space-between; {_style_css(s_labels)}">'
            f"{spans}</div>"
        )
    stacked = labels_html + bar if labels_position == "top" else bar + labels_html
    legend = f'<div style="display:flex; flex-direction:column; gap:{gap:g}px;">{stacked}</div>'

    if title is not None:
        title_html = f'<div style="{_style_css(s_title)}">{title}</div>'
        if title_position in ("top", "bottom"):
            inner = title_html + legend if title_position == "top" else legend + title_html
            legend = (
                f'<div style="display:flex; flex-direction:column; align-items:{_JUSTIFY[align]}; '
                f'gap:{title_gap:g}px;">{inner}</div>'
            )
        else:
            inner = title_html + legend if title_position == "left" else legend + title_html
            legend = (
                f'<div style="display:flex; flex-direction:row; align-items:center; gap:{title_gap:g}px;">{inner}</div>'
            )
    legend = f'<div style="display:flex; justify-content:{_JUSTIFY[align]};">{legend}</div>'

    fonts = _fonts(s_title, s_labels)
    if location == "bottom":
        return _with_fonts(gt.tab_source_note(html(legend)), fonts, loc.source_notes())
    return _in_header(gt, legend, fonts)


def gt_legend_discrete(
    gt: GT,
    key_info: Any = None,
    heading: str | None = None,
    subtitle: str | None = None,
    label_placement: str = "outside",
    location: str = "top",
    shape: str = "square",
    swatch_size: float = 14,
    border: bool = True,
    border_color: str | None = None,
    border_width: float = 1,
    gap: float = 14,
    direction: str = "horizontal",
    align: str = "center",
    heading_style: Mapping[str, Any] | None = None,
    subtitle_style: Mapping[str, Any] | None = None,
    label_style: Mapping[str, Any] | None = None,
) -> GT:
    """Add a key of labeled color swatches (home/away, tiers, conferences).

    Text colors are read off the table background, so the key stays legible on a dark theme. Style dicts take the
    keys listed in ``gt_title_header``.

    Args:
        gt: The table.
        key_info: ``{label: hex color}``, or a pandas/polars frame with ``color`` and ``label`` columns (or color then
            label as its first two columns). Defaults to the key ``gt_tiers`` recorded on the table.
        heading: A heading above the key.
        subtitle: A subtitle under the heading.
        label_placement: ``"outside"`` (label beside its swatch) or ``"inside"`` (label printed on the swatch).
        location: ``"top"`` (the header) or ``"bottom"`` (a source note).
        shape: ``"square"``, ``"rounded"`` or ``"circle"``.
        swatch_size: The swatch size in pixels.
        border: Draw a hairline around each swatch.
        border_color: The hairline color; defaults to a darker shade of each swatch.
        border_width: The hairline width in pixels.
        gap: Pixels between keys.
        direction: ``"horizontal"`` (a row) or ``"vertical"`` (a column).
        align: ``"center"``, ``"left"`` or ``"right"``.
        heading_style: Styles the heading (16px, weight 600, ink on the table background).
        subtitle_style: Styles the subtitle (13px, a muted ink).
        label_style: Styles the labels (12px).

    Returns:
        GT: A new table with the key added. With ``location="top"`` and a heading or subtitle, the key replaces the
        header; a bare key goes under any existing title and subtitle.

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT`` or ``key_info`` is neither a mapping nor a data frame.
        ValueError: If there is no key, a color is not hex, or an option is not one of its choices.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_legend_discrete

            gt = gt_legend_discrete(GT(pl.DataFrame({"game": ["@ KC"]})), {"Home": "#cce7f5", "Away": "#eeeeee"})

    See Also:
        Ported from sdvplotR ``gt_legend_discrete()``:
        https://sdvplotR.sportsdataverse.org/reference/gt_legend_discrete.html
    """
    _check_gt(gt)
    _choice("label_placement", label_placement, ("outside", "inside"))
    _choice("location", location, ("top", "bottom"))
    _choice("shape", shape, ("square", "rounded", "circle"))
    _choice("direction", direction, ("horizontal", "vertical"))
    _choice("align", align, ("center", "left", "right"))

    if key_info is None:
        key_info = gt.__dict__.get("_sdvplot_key")
    if key_info is None:
        raise ValueError("key_info is missing and no key is recorded on the table; pass {'Home': '#cce7f5'} or call "
                         "gt_tiers first")  # fmt: skip
    if isinstance(key_info, Mapping):
        labels, colors = [str(k) for k in key_info], [str(v) for v in key_info.values()]
    else:
        try:
            key = nw.from_native(key_info, eager_only=True)
        except TypeError:
            raise TypeError("key_info must be a mapping of label to color or a data frame") from None
        names = key.columns
        if {"color", "label"} <= set(names):
            colors, labels = key["color"].to_list(), key["label"].to_list()
        elif len(names) >= 2:
            colors, labels = key[names[0]].to_list(), key[names[1]].to_list()
        else:
            raise ValueError("a data frame key_info needs a color and a label column")
        colors, labels = [str(c) for c in colors], [str(x) for x in labels]
    colors = [hex6(c) for c in colors]

    bg = _background(gt)
    ink = on_color(bg)
    s_heading = _style({"size": 16, "weight": 600, "color": ink}, heading_style)
    s_subtitle = _style({"size": 13, "weight": 400, "color": _secondary_on(bg, ink)}, subtitle_style)
    s_label = _style({"size": 12, "color": ink}, label_style)

    edges = [mix(c, "#000000", 0.18) if border_color is None else border_color for c in colors]
    rims = [f"border:{border_width:g}px solid {e};" if border else "" for e in edges]
    radius = {"square": 0, "rounded": round(swatch_size / 4), "circle": round(swatch_size / 2)}[shape]

    if label_placement == "inside":
        items = [
            f'<span style="display:inline-block; padding:2px 9px; background-color:{c}; border-radius:{radius}px; '
            f'{rim} {_style_css({**s_label, "color": on_color(c)})}">{label}</span>'
            for c, rim, label in zip(colors, rims, labels, strict=True)
        ]
    else:
        items = [
            '<span style="display:inline-flex; align-items:center; gap:6px;">'
            f'<span style="display:inline-block; width:{swatch_size:g}px; height:{swatch_size:g}px; '
            f'background-color:{c}; border-radius:{radius}px; {rim}"></span>'
            f'<span style="{_style_css(s_label)}">{label}</span></span>'
            for c, rim, label in zip(colors, rims, labels, strict=True)
        ]
    justify = _JUSTIFY[align]
    flow = (
        f"column; align-items:{justify};"
        if direction == "vertical"
        else f"row; justify-content:{justify}; align-items:center;"
    )
    key_html = f'<div style="display:flex; flex-wrap:wrap; gap:{gap:g}px; flex-direction:{flow}">{"".join(items)}</div>'
    head = ""
    if heading is not None:
        head += f'<div style="{_style_css(s_heading)}">{heading}</div>'
    if subtitle is not None:
        head += f'<div style="{_style_css(s_subtitle)}">{subtitle}</div>'
    content = (
        f'<div style="display:flex; flex-direction:column; align-items:{justify}; gap:6px;">{head}{key_html}</div>'
    )

    fonts = _fonts(s_heading, s_subtitle, s_label)
    if location == "bottom":
        return _with_fonts(gt.tab_source_note(html(content)), fonts, loc.source_notes())
    if heading is not None or subtitle is not None:
        return _with_fonts(gt.tab_header(title=html(content)), fonts, loc.title())
    return _in_header(gt, content, fonts)


def gt_percentile_bar(
    gt: GT,
    columns: Any,
    rows: Any = None,
    domain: Sequence[float] = (0, 100),
    scale: str | float = "auto",
    palette: Sequence[str] = ("#3661AD", "#C9C9C9", "#D22D49"),
    reverse: bool = False,
    pal_type: str = "discrete",
    track_color: str = "#E9E9E9",
    track_height: float = 6,
    marker_size: float = 22,
    text_color: str = "#FFFFFF",
    font_size: float | None = None,
    ring_color: str | None = None,
    ring_width: float = 2,
    full_track: bool = True,
    na_label: str | None = "—",
    na_track_color: str | None = None,
    na_text_color: str = "#9A9A9A",
    decimals: int = 0,
    width: float | None = 220,
) -> GT:
    """Draw each percentile as a filled track with a round marker at its tip, the value printed in the marker.

    All CSS, so it stays sharp at any export scale. The fill and marker take the palette color mapped from the value.
    The scale is recorded on the table (``_sdvplot_scale``), so ``gt_legend_continuous(gt)`` matches it.

    Args:
        gt: The table.
        columns: The columns holding percentiles (any great_tables column selection).
        rows: The rows to draw bars in (any great_tables row selection: 0-based positions, a polars expression, or a
            function of the pandas frame); other rows keep their value. Defaults to every row.
        domain: ``(low, high)`` of the percentile scale.
        scale: ``"auto"`` treats a column whose values all lie in [0, 1] as proportions of ``domain`` (0.72 is drawn
            and printed as 72); ``"none"`` leaves values alone; a number multiplies every value.
        palette: Hex colors mapped across ``domain`` (blue, gray, red).
        reverse: Reverse the palette.
        pal_type: ``"discrete"`` or ``"continuous"``; kept for sdvplotR parity and recorded with the scale.
        track_color: The unfilled track color.
        track_height: The track thickness in pixels.
        marker_size: The marker diameter in pixels.
        text_color: The number's color.
        font_size: The number's size in pixels; defaults to half of ``marker_size``.
        ring_color: A ring around the marker; ``None`` for none.
        ring_width: The ring thickness in pixels.
        full_track: Run the track the full width (else it stops at the marker).
        na_label: What a missing percentile shows, centered in a broken track; ``None`` draws an unbroken empty track.
        na_track_color: The track color of missing rows; defaults to ``track_color``.
        na_text_color: The color of ``na_label``.
        decimals: Decimal places of the number.
        width: The column width in pixels; ``None`` leaves it alone.

    Returns:
        GT: A new table with the bars (unchanged, with an SdvplotWarning, when ``rows`` selects no rows).

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.
        ValueError: If ``scale``, ``pal_type`` or ``domain`` is invalid, or a palette color is not hex.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_percentile_bar

            df = pl.DataFrame({"metric": ["Barrel %", "Chase rate"], "pct": [94, None]})
            gt = gt_percentile_bar(GT(df), "pct", na_label="Not qualified")

    See Also:
        Ported from sdvplotR ``gt_percentile_bar()``: https://sdvplotR.sportsdataverse.org/reference/gt_percentile_bar.html
    """
    _check_gt(gt)
    _choice("pal_type", pal_type, ("discrete", "continuous"))
    if isinstance(scale, str):
        _choice("scale", scale, ("auto", "none"))
    if len(domain) != 2 or domain[1] == domain[0]:
        raise ValueError(f"domain must be (low, high) with low != high, got {domain!r}")
    cols = _columns(gt, columns)
    if not cols:
        return gt
    keep = _rows(gt, rows)
    if not keep:
        warnings.warn("rows matched no rows; the table is unchanged", SdvplotWarning, stacklevel=2)
        return gt

    lo, hi = float(domain[0]), float(domain[1])
    pal = _palette(palette)[:: -1 if reverse else 1]
    size = round(marker_size * 0.5, 1) if font_size is None else font_size
    half, r, row_h = marker_size / 2, track_height / 2, marker_size + 4
    na_track = track_color if na_track_color is None else na_track_color

    def na_cell() -> str:
        seg = (
            f'<div style="flex:1; height:{track_height:.2f}px; border-radius:{r:.2f}px; background:{na_track};"></div>'
        )
        inner = seg
        if na_label is not None:
            label = (
                f'<span style="font-size:{size:.1f}px; color:{na_text_color}; letter-spacing:0.06em; '
                f'white-space:nowrap; line-height:1;">{na_label}</span>'
            )
            inner = seg + label + seg
        return (
            f'<div style="display:flex; align-items:center; gap:8px; height:{row_h:.2f}px; padding:0 {half:.2f}px;">'
            f"{inner}</div>"
        )

    def bar(value: Any, proportion: bool) -> str:
        v = _number(value)
        if v is None:
            return na_cell()
        if not isinstance(scale, str):
            v *= scale
        elif proportion:
            v = lo + v * (hi - lo)
        frac = min(1.0, max(0.0, (v - lo) / (hi - lo)))
        color = _ramp(pal, frac)
        at = f"calc({half:.2f}px + {frac:.4f} * (100% - {marker_size:.2f}px))"
        centered = "position:absolute; top:50%; transform:translateY(-50%);"
        track = (
            f'<div style="{centered} left:{half:.2f}px; right:{half:.2f}px; height:{track_height:.2f}px; '
            f'border-radius:{r:.2f}px; background:{track_color};"></div>'
        )
        fill = (
            f'<div style="{centered} left:{half:.2f}px; width:calc({at} - {half:.2f}px); height:{track_height:.2f}px; '
            f'border-radius:{r:.2f}px; background:{color};"></div>'
        )
        ring = "" if ring_color is None else f" box-shadow:0 0 0 {ring_width:.2f}px {ring_color};"
        marker = (
            f'<div style="position:absolute; top:50%; left:{at}; transform:translate(-50%,-50%); '
            f"width:{marker_size:.2f}px; height:{marker_size:.2f}px; border-radius:50%; background:{color}; "
            f"color:{text_color}; font-size:{size:.1f}px; font-weight:700; line-height:{marker_size:.2f}px; "
            f'text-align:center;{ring}">{v:.{decimals}f}</div>'
        )
        return (
            f'<div style="position:relative; width:100%; height:{row_h:g}px;">'
            f"{track if full_track else ''}{fill}{marker}</div>"
        )

    for col in cols:
        present = [v for v in _numbers(gt, col) if v is not None]
        proportion = scale == "auto" and bool(present) and all(0 <= v <= 1 for v in present) and hi > 1
        # partial binds this column's proportion now; a closure would see the last column's by render time
        gt = gt.fmt(functools.partial(bar, proportion=proportion), columns=col, rows=keep)
    if width is not None:
        gt = gt.cols_width(cases={c: f"{width:g}px" for c in cols})
    scale_record = {"columns": cols, "palette": list(palette), "domain": (lo, hi), "reverse": reverse}
    return _record(gt, "_sdvplot_scale", {**scale_record, "pal_type": pal_type})


def gt_tiers(
    gt: GT,
    levels: Mapping[str, str] | Sequence[str],
    colors: Sequence[str] | None = None,
    style: str = "dark",
    img_height: str = "55px",
    tier_column: str = "tier",
    image_columns: Any = None,
) -> GT:
    """Build a tier list: a tier label column filled in each tier's color, the other columns rendered as images.

    Applies ``gt_theme_tier(style=style)``, renders the image columns with ``fmt_image`` at ``img_height``, blanks
    missing cells and every column label, then fills each tier's label cell with its color and readable bold ink. The
    tier colors are recorded on the table (``_sdvplot_key``), so ``gt_legend_discrete(gt)`` draws the matching key.

    Args:
        gt: The table: one row per tier, a tier column, and image paths or URLs in the other columns.
        levels: The tier values, in order; or one ``{level: hex color}`` mapping, leaving ``colors`` unset.
        colors: Hex colors paired with ``levels``.
        style: ``"dark"`` or ``"light"``, passed to ``gt_theme_tier``.
        img_height: The image height, as a CSS size.
        tier_column: The column holding the tier values.
        image_columns: The columns to render as images (any great_tables selection); defaults to every other column.

    Returns:
        GT: A new tier-list table.

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.
        ValueError: If ``colors`` is missing without a mapping, the lengths differ, ``tier_column`` is not a column,
            or a color is not hex.

    Warns:
        SdvplotWarning: When a level has no rows in ``tier_column``.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_tiers

            df = pl.DataFrame({"tier": ["S", "A"], "logo": ["https://.../kc.png", "https://.../buf.png"]})
            gt = gt_tiers(GT(df), {"S": "#C84630", "A": "#5DA271"})

    See Also:
        Ported from sdvplotR ``gt_tiers()``: https://sdvplotR.sportsdataverse.org/reference/gt_tiers.html
    """
    from sdvplot.great_tables._themes import gt_theme_tier  # wave B

    _check_gt(gt)
    if colors is None:
        if not isinstance(levels, Mapping):
            raise ValueError("colors is missing; pass levels and colors as two lists, or one mapping such as "
                             "{'A': '#C84630', 'B': '#5DA271'}")  # fmt: skip
        colors = list(levels.values())
    names = [str(x) for x in levels]
    if len(names) != len(colors):
        raise ValueError(f"levels and colors must be the same length: got {len(names)} levels and {len(colors)} colors")
    fills = [hex6(c) for c in colors]

    data = _frame(gt)
    if tier_column not in data.columns:
        raise ValueError(f"tier_column {tier_column!r} is not a column in the table; it has {data.columns}")
    tiers = _strings(gt, tier_column)
    missing = [x for x in names if x not in tiers]
    if missing:
        held = list(dict.fromkeys(t for t in tiers if t is not None))
        warnings.warn(
            f"tier(s) {missing} are not in {tier_column!r}, so they get no rows; it holds {held}",
            SdvplotWarning,
            stacklevel=2,
        )

    chosen = data.columns if image_columns is None else _columns(gt, image_columns)
    images = [c for c in chosen if c != tier_column]
    gt = (
        gt_theme_tier(gt, style=style)
        .fmt_image(columns=images, height=img_height)
        .sub_missing(missing_text="")
        .cols_label(cases={c: "" for c in data.columns})
    )
    for level, fill in zip(names, fills, strict=True):
        rows = [i for i, t in enumerate(tiers) if t == level]
        if rows:
            look = [gst.fill(color=fill), gst.text(weight="bold", color=on_color(fill))]
            gt = gt.tab_style(look, loc.body(columns=tier_column, rows=rows))
    return _record(gt, "_sdvplot_key", dict(zip(names, fills, strict=True)))


def _rendered(gt: GT) -> list[str]:
    """The visible body columns, in display order (not the stub, row groups or hidden columns)."""
    return [c.var for c in gt._boxhead if c.type.name == "default"]


def _append(text: str, suffix: str) -> str:
    """A ``text_transform`` function: the cell's rendered text plus ``suffix`` (bound with ``functools.partial``)."""
    return f"{text}{suffix}"


def gt_spotlight(
    gt: GT,
    rows: Any,
    columns: Any = None,
    fill: str | None = None,
    text_color: str | None = None,
    bold: bool = True,
    accent_color: str | None = None,
    accent_width: float = 4,
    accent_column: Any = None,
    dim_color: str | None = "#BBBBBB",
    if_none: str = "warn",
) -> GT:
    """Light up some rows (bold, a fill, an accent bar) and dim everything else.

    Args:
        gt: The table.
        rows: The rows to focus on: any great_tables row selection (0-based positions, a polars expression, or a
            function of the pandas frame).
        columns: The columns the spotlight covers; cells outside it are dimmed in the focused rows too. Defaults to
            every column.
        fill: A fill behind the focused cells.
        text_color: The focused cells' text color.
        bold: Bold the focused cells.
        accent_color: A bar on the left edge of the focused rows; giving a color turns it on.
        accent_width: The bar width in pixels.
        accent_column: The column(s) the bar is drawn on; defaults to the leftmost rendered column.
        dim_color: The text color of everything else; ``None`` emphasizes without dimming.
        if_none: When ``rows`` matches nothing: ``"warn"`` (unchanged, with an SdvplotWarning), ``"dim"`` (dim the
            whole table, for a spotlight that lives in another table of a grid) or ``"ignore"``.

    Returns:
        GT: A new table with the spotlight.

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.
        ValueError: If ``if_none`` is not one of its choices.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_spotlight

            df = pl.DataFrame({"team": ["LV", "KC", "BUF"], "wins": [10, 12, 11]})
            gt = gt_spotlight(GT(df), pl.col("team") == "KC", accent_color="#E31837")

    See Also:
        Ported from sdvplotR ``gt_spotlight()``: https://sdvplotR.sportsdataverse.org/reference/gt_spotlight.html
    """
    _check_gt(gt)
    _choice("if_none", if_none, ("warn", "dim", "ignore"))
    focus = _rows(gt, rows)
    if not focus:
        if if_none == "dim" and dim_color is not None:
            return gt.tab_style(gst.text(color=dim_color), loc.body())
        if if_none == "warn":
            msg = "rows matched no rows, so the table is unchanged; set if_none='dim' to dim the whole table instead"
            warnings.warn(msg, SdvplotWarning, stacklevel=2)
        return gt

    chosen = _columns(gt, columns)
    rendered = _rendered(gt)
    others = [i for i in range(len(_frame(gt))) if i not in set(focus)]
    rest = [c for c in rendered if c not in chosen]
    if dim_color is not None:
        if others:
            gt = gt.tab_style(gst.text(color=dim_color), loc.body(rows=others))
        if rest:
            gt = gt.tab_style(gst.text(color=dim_color), loc.body(columns=rest, rows=focus))

    looks: list[Any] = [] if fill is None else [gst.fill(color=fill)]
    if text_color is not None or bold:
        looks.append(gst.text(color=text_color, weight="bold" if bold else None))
    if looks:
        gt = gt.tab_style(looks, loc.body(columns=chosen, rows=focus))

    if accent_color is not None:
        edge = rendered[:1] if accent_column is None else [c for c in _columns(gt, accent_column) if c in rendered]
        if not edge:
            warnings.warn("accent_column matched no rendered column; no accent drawn", SdvplotWarning, stacklevel=2)
        else:
            bar = gst.borders(sides="left", color=accent_color, weight=f"{accent_width:g}px")
            gt = gt.tab_style(bar, loc.body(columns=edge, rows=focus))
    return gt


def gt_row_accent(
    gt: GT,
    column: Any,
    palette: Mapping[str, str] | Sequence[str] | None = None,
    rows: Any = None,
    width: float = 4,
    side: str = "left",
    hide: bool = True,
    na_color: str = "transparent",
) -> GT:
    """Draw a colored bar on the edge of each row, keyed to a column (a team color, a conference).

    The bar is a border on the stub, or on the leftmost rendered column when the table has no stub, so it lines up
    with the row.

    Args:
        gt: The table.
        column: The one column the color is keyed to: a column of colors, or values mapped through ``palette``.
        palette: ``{value: color}``; or a list of colors assigned to the sorted distinct values and recycled.
            Defaults to reading ``column`` as colors.
        rows: The rows to accent (any great_tables row selection). Defaults to every row.
        width: The bar width in pixels.
        side: ``"left"`` or ``"right"``.
        hide: Hide ``column`` once the bars are drawn (what you want when it holds hex codes).
        na_color: The color for a missing or unmapped key; ``"transparent"`` draws no bar.

    Returns:
        GT: A new table with the bars (unchanged, with an SdvplotWarning, when ``rows`` selects no rows).

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.
        ValueError: If ``column`` does not select exactly one column, or ``side`` is not ``"left"``/``"right"``.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_row_accent

            df = pl.DataFrame({"team": ["Clemson", "Georgia"], "conf": ["ACC", "SEC"], "wins": [10, 12]})
            gt = gt_row_accent(GT(df), "conf", palette={"ACC": "#003366", "SEC": "#B8232F"})

    See Also:
        Ported from sdvplotR ``gt_row_accent()``: https://sdvplotR.sportsdataverse.org/reference/gt_row_accent.html
    """
    _check_gt(gt)
    _choice("side", side, ("left", "right"))
    selected = _columns(gt, column)
    if len(selected) != 1:
        raise ValueError(f"column must select exactly one column, got {selected}")
    keys = _strings(gt, selected[0])
    if palette is None:
        colors = list(keys)
    elif isinstance(palette, Mapping):
        colors = [None if k is None else palette.get(k) for k in keys]
    else:
        levels = sorted({k for k in keys if k is not None})
        lookup = {level: palette[i % len(palette)] for i, level in enumerate(levels)}
        colors = [None if k is None else lookup[k] for k in keys]
    fills = [na_color if c is None else c for c in colors]

    keep = set(_rows(gt, rows))
    if not keep:
        warnings.warn("rows matched no rows; the table is unchanged", SdvplotWarning, stacklevel=2)
        return gt
    if hide:
        gt = gt.cols_hide(columns=selected)
    has_stub = any(c.type.name == "stub" for c in gt._boxhead)
    rendered = _rendered(gt)
    if not rendered and not has_stub:
        return gt
    edge_side: Literal["left", "right"] = "left" if side == "left" else "right"
    for color in dict.fromkeys(fills):
        at = [i for i, c in enumerate(fills) if c == color and i in keep]
        if color == "transparent" or not at:
            continue
        where = loc.stub(rows=at) if has_stub else loc.body(columns=rendered[0], rows=at)
        gt = gt.tab_style(gst.borders(sides=edge_side, color=color, weight=f"{width:g}px"), where)
    return gt


def _quantile(ordered: list[float], p: float) -> float:
    """R's default (type 7) quantile of sorted values."""
    h = (len(ordered) - 1) * p
    i = math.floor(h)
    return ordered[i] if i + 1 >= len(ordered) else ordered[i] + (h - i) * (ordered[i + 1] - ordered[i])


def _limits(method: str, values: list[float], threshold: float, bounds: Sequence[Any]) -> list[float]:
    """The (low, high) outside which a value is an outlier; infinite when the spread is zero or undefined."""
    wide = [-math.inf, math.inf]
    if method == "bounds":
        lo, hi = (_number(b) for b in bounds)
        return [-math.inf if lo is None else lo, math.inf if hi is None else hi]
    if len(values) < 2:
        return wide
    if method == "sd":
        mean = sum(values) / len(values)
        sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
        return wide if sd == 0 else [mean - threshold * sd, mean + threshold * sd]
    ordered = sorted(values)
    q1, q3 = _quantile(ordered, 0.25), _quantile(ordered, 0.75)
    return wide if q3 == q1 else [q1 - threshold * (q3 - q1), q3 + threshold * (q3 - q1)]


def gt_outliers(
    gt: GT,
    columns: Any,
    method: str = "iqr",
    threshold: float | None = None,
    bounds: Sequence[float | None] | None = None,
    side: str = "both",
    fill: str | None = None,
    color: str | None = None,
    bold: bool = True,
    symbol: str | None = None,
    note: bool | str | None = None,
) -> GT:
    """Flag outlying values in numeric columns: colored (and bold) text, an optional fill, symbol and source note.

    Args:
        gt: The table.
        columns: The columns to test (any great_tables selection); non-numeric columns are skipped.
        method: ``"iqr"`` (beyond ``threshold`` x IQR of the quartiles, R's type-7 quantiles), ``"sd"`` (more than
            ``threshold`` sample standard deviations from the mean) or ``"bounds"`` (outside ``bounds``).
        threshold: The cutoff for ``"iqr"`` (default 1.5) and ``"sd"`` (default 3).
        bounds: ``(lower, upper)`` for ``"bounds"``; ``None`` on either side leaves it open.
        side: ``"both"``, ``"high"`` or ``"low"``.
        fill: A fill behind flagged values.
        color: The flagged text color; defaults to a warning red, or the readable ink when the red fails 4.5:1 on
            ``fill``.
        bold: Bold flagged values.
        symbol: A marker appended to flagged values, such as ``"†"``.
        note: ``True`` adds a source note describing the rule; a string adds that note; ``None``/``False`` none.

    Returns:
        GT: A new table (unchanged, with an SdvplotWarning, when no selected column is numeric).

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.
        ValueError: If ``columns`` selects nothing, ``bounds`` is missing for ``"bounds"``, or an option is invalid.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_outliers

            df = pl.DataFrame({"team": list("ABCDEFG"), "pts": [21, 24, 20, 23, 22, 25, 61]})
            gt = gt_outliers(GT(df), "pts", symbol="†", note=True)

    See Also:
        Ported from sdvplotR ``gt_outliers()``: https://sdvplotR.sportsdataverse.org/reference/gt_outliers.html
    """
    _check_gt(gt)
    _choice("method", method, ("iqr", "sd", "bounds"))
    _choice("side", side, ("both", "high", "low"))
    if threshold is None:
        threshold = 3 if method == "sd" else 1.5
    if method == "bounds" and (bounds is None or len(bounds) != 2):
        raise ValueError("bounds must be (lower, upper) when method is 'bounds'")
    cols = _columns(gt, columns)
    if not cols:
        raise ValueError("columns matched no columns")
    data = _frame(gt)
    numeric = [c for c in cols if data[c].dtype.is_numeric()]
    if not numeric:
        warnings.warn("no numeric columns among columns; nothing to flag", SdvplotWarning, stacklevel=2)
        return gt
    if color is None:
        color = "#B3261E" if fill is None or contrast("#B3261E", fill) >= 4.5 else on_color(fill)

    flagged = False
    for col in numeric:
        values = _numbers(gt, col)
        low, high = _limits(method, [v for v in values if v is not None], threshold, bounds or ())
        hit = [
            i
            for i, v in enumerate(values)
            if v is not None and ((v < low and side != "high") or (v > high and side != "low"))
        ]
        if not hit:
            continue
        flagged = True
        looks: list[Any] = [gst.text(color=color, weight="bold" if bold else None)]
        if fill is not None:
            looks.append(gst.fill(color=fill))
        gt = gt.tab_style(looks, loc.body(columns=col, rows=hit))
        if symbol is not None:
            gt = gt.text_transform(loc.body(columns=col, rows=hit), functools.partial(_append, suffix=symbol))

    if not flagged or note is None or note is False:
        return gt
    if note is True:
        tail = {"both": "", "high": " (high side only)", "low": " (low side only)"}[side]
        if method == "sd":
            plural = "" if threshold == 1 else "s"
            text = f"Marked values fall more than {threshold:g} standard deviation{plural} from the column mean{tail}."
        elif method == "iqr":
            text = f"Marked values fall outside {threshold:g} × IQR of the column quartiles{tail}."
        else:
            lo, hi = ("NA" if x is None else f"{x:g}" for x in map(_number, bounds or ()))
            text = f"Marked values fall outside {lo}–{hi}{tail}."
    else:
        text = str(note)
    return gt.tab_source_note(text)


def gt_significance(
    gt: GT,
    columns: Any,
    p_columns: Any,
    levels: Sequence[float] = (0.01, 0.05, 0.1),
    symbols: Sequence[str] = ("***", "**", "*"),
    superscript: bool = True,
    size: str = "0.7em",
    legend: bool = True,
    legend_text: str | None = None,
    hide_p: bool = True,
) -> GT:
    """Append significance stars to estimates from paired p-value columns.

    Each value takes the symbol of the strictest level its p-value is below (0.004 gets ``***``, not ``*``); values
    that meet no level, and missing p-values, are left alone. Stars follow the formatted text, so format first.

    Args:
        gt: The table.
        columns: The estimate columns (any great_tables selection).
        p_columns: The p-value columns, paired with ``columns`` by position.
        levels: Significance thresholds, ascending (strictest first).
        symbols: The notation for each level.
        superscript: Render the stars as superscript.
        size: The stars' CSS font size.
        legend: Add a legend as a source note.
        legend_text: A custom legend; defaults to ``"*** p < 0.01, ** p < 0.05, * p < 0.1"`` from the levels.
        hide_p: Hide the p-value columns.

    Returns:
        GT: A new table with the stars.

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.
        ValueError: If ``levels`` and ``symbols`` differ in length, ``levels`` is not ascending, ``columns`` selects
            nothing, or the two selections do not pair up.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_significance

            df = pl.DataFrame({"term": ["epa", "wpa"], "est": [0.42, 0.08], "p": [0.004, 0.2]})
            gt = gt_significance(GT(df).fmt_number("est"), "est", "p")

    See Also:
        Ported from sdvplotR ``gt_significance()``: https://sdvplotR.sportsdataverse.org/reference/gt_significance.html
    """
    _check_gt(gt)
    if len(levels) != len(symbols):
        raise ValueError("levels and symbols must be the same length")
    if list(levels) != sorted(levels):
        raise ValueError("levels must be in ascending order, strictest first")
    estimates, p_cols = _columns(gt, columns), _columns(gt, p_columns)
    if not estimates:
        raise ValueError("columns matched no columns")
    if len(p_cols) != len(estimates):
        raise ValueError(
            f"p_columns must pair with columns: got {len(estimates)} estimate column(s) and {len(p_cols)} p-value "
            "column(s)"
        )
    for estimate, p_col in zip(estimates, p_cols, strict=True):
        marks = []
        for p in _numbers(gt, p_col):
            mark = next((s for level, s in zip(levels, symbols, strict=True) if p is not None and p < level), "")
            marks.append(f"<sup style='font-size:{size};'>{mark}</sup>" if superscript and mark else mark)
        for mark in dict.fromkeys(m for m in marks if m):
            rows = [i for i, m in enumerate(marks) if m == mark]
            gt = gt.text_transform(loc.body(columns=estimate, rows=rows), functools.partial(_append, suffix=mark))
    if hide_p:
        gt = gt.cols_hide(columns=p_cols)
    if legend:
        text = ", ".join(f"{s} p < {level:g}" for level, s in zip(levels, symbols, strict=True))
        gt = gt.tab_source_note(html(text if legend_text is None else legend_text))
    return gt


def gt_marginalia(
    gt: GT,
    columns: Any,
    width: float | str | None = 220,
    label: str | None = "",
    italic: bool = True,
    color: str | None = None,
    size: str = "0.92em",
    rule: bool = True,
    rule_color: str | None = None,
    align: str = "left",
) -> GT:
    """Turn columns into margin notes: muted italic prose in a fixed-width column behind a hairline rule.

    Args:
        gt: The table.
        columns: The note columns (any great_tables selection).
        width: The column width (a number is pixels); the fixed width is what makes the prose wrap. ``None`` leaves
            it alone.
        label: The column label (empty by default); ``None`` keeps the existing label.
        italic: Italicize the notes.
        color: The text color; defaults to a muted ink that clears 4.5:1 on the table background (dark themes too).
        size: The CSS font size.
        rule: Draw a hairline on the left edge.
        rule_color: The hairline color; defaults to a faint tint of the ink.
        align: The text alignment.

    Returns:
        GT: A new table with the note columns styled.

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.
        ValueError: If ``columns`` selects nothing.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_marginalia

            df = pl.DataFrame({"team": ["LV"], "note": ["Lost the starting QB in week 3."]})
            gt = gt_marginalia(GT(df), "note")

    See Also:
        Ported from sdvplotR ``gt_marginalia()``: https://sdvplotR.sportsdataverse.org/reference/gt_marginalia.html
    """
    _check_gt(gt)
    cols = _columns(gt, columns)
    if not cols:
        raise ValueError("columns matched no columns")
    bg = _background(gt)
    ink = on_color(bg)
    color = _secondary_on(bg, ink) if color is None else color
    rule_color = mix(bg, ink, 0.18) if rule_color is None else rule_color
    out = gt.cols_align(align=align, columns=cols).tab_style(
        gst.text(color=color, size=size, style="italic" if italic else "normal"), loc.body(columns=cols)
    )
    if width is not None:
        out = out.cols_width(cases={c: _css_len(width) for c in cols})
    if label is not None:
        out = out.cols_label(cases={c: label for c in cols})
    if rule:
        out = out.tab_style(gst.borders(sides="left", color=rule_color, weight="1px"), loc.body(columns=cols))
    return out


_SCALE_NAMES = {
    1e3: ("thousands", "(000s)"),
    1e6: ("millions", "(millions)"),
    1e9: ("billions", "(billions)"),
    1e12: ("trillions", "(trillions)"),
}


def gt_scale_note(
    gt: GT,
    columns: Any,
    divisor: float = 1000,
    note: str | None = None,
    where: str = "source_note",
    label_suffix: str | None = None,
    decimals: int = 0,
    **kwargs: Any,
) -> GT:
    """Divide columns by a round number and say so: "Figures in thousands." or a "(000s)" label suffix.

    Args:
        gt: The table.
        columns: The columns to scale (any great_tables selection).
        divisor: The amount to divide by.
        note: The disclosure; defaults to "Figures in thousands." (millions, billions, trillions) or "Figures divided
            by 2,500." for other divisors.
        where: ``"source_note"``, ``"label"`` (append ``label_suffix`` to the column labels) or ``"both"``.
        label_suffix: The label suffix; defaults to "(000s)", "(millions)", ... or "(÷2,500)".
        decimals: Decimal places of the scaled values.
        **kwargs: Passed to great_tables ``fmt_number`` (``use_seps``, ``pattern``, ...).

    Returns:
        GT: A new table with the columns formatted and the disclosure added.

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.
        ValueError: If ``divisor`` is not a non-zero number, ``columns`` selects nothing, or ``where`` is invalid.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_scale_note

            df = pl.DataFrame({"team": ["LV", "KC"], "payroll": [254_000_000, 268_500_000]})
            gt = gt_scale_note(GT(df), "payroll", divisor=1e6, decimals=1, where="both")

    See Also:
        Ported from sdvplotR ``gt_scale_note()``: https://sdvplotR.sportsdataverse.org/reference/gt_scale_note.html
    """
    _check_gt(gt)
    _choice("where", where, ("source_note", "label", "both"))
    if isinstance(divisor, bool) or not isinstance(divisor, int | float) or divisor == 0:
        raise ValueError(f"divisor must be a single non-zero number, got {divisor!r}")
    cols = _columns(gt, columns)
    if not cols:
        raise ValueError("columns matched no columns")
    named = _SCALE_NAMES.get(float(divisor))
    shown = f"{int(divisor):,}" if float(divisor).is_integer() else f"{divisor:,}"
    if note is None:
        note = f"Figures in {named[0]}." if named else f"Figures divided by {shown}."
    if label_suffix is None:
        label_suffix = named[1] if named else f"(÷{shown})"

    out = gt.fmt_number(columns=cols, scale_by=1 / divisor, decimals=decimals, **kwargs)
    if where in ("source_note", "both"):
        out = out.tab_source_note(note)
    if where in ("label", "both"):
        current = {c.var: c.column_label for c in gt._boxhead}
        out = out.cols_label(cases={c: _suffixed(current[c], label_suffix) for c in cols})
    return out


def _suffixed(label: Any, suffix: str) -> Any:
    """A column label with ``suffix`` appended, keeping an HTML label HTML."""
    text = f"{getattr(label, 'text', label)} {suffix}"
    return html(text) if hasattr(label, "text") else text


# sdvplotR's friendly names -> Font Awesome icon names, tried in order. faicons (a great_tables dependency) 0.2.2
# predates Font Awesome's x-twitter, bluesky, threads and substack icons, so X falls back to the Twitter bird.
_SOCIAL = {
    "x": ("x-twitter", "twitter"),
    "twitter": ("x-twitter", "twitter"),
    "ig": ("instagram",),
    "bsky": ("bluesky",),
    "gh": ("github",),
    "yt": ("youtube",),
    "fb": ("facebook",),
    "web": ("globe",),
    "website": ("globe",),
    "link": ("globe",),
    "email": ("envelope",),
    "mail": ("envelope",),
}


def _social_icon(key: str, fill: str, height: str) -> str:
    """The Font Awesome SVG for a platform name or alias, or a ValueError naming the installed faicons version."""
    names = _SOCIAL.get(key.lower(), (key.lower(),))
    for name in names:
        try:
            return str(faicons.icon_svg(name, fill=fill, height=height))
        except ValueError:
            continue
    version = importlib.metadata.version("faicons")
    raise ValueError(
        f"icon {names[0]!r} was not found in your installed faicons ({version}); update faicons or use a "
        "different icon or alias"
    )


def gt_social_tag(
    gt: GT,
    accounts: Mapping[str, str],
    caption: str | None = None,
    stack: bool = False,
    separator: str = " | ",
    align: str = "right",
    icon_color: str | None = None,
    icon_height: str = "0.9em",
    text_size: str | None = None,
    text_weight: str | int | None = None,
    **kwargs: Any,
) -> GT:
    """Sign a table with social handles, each behind its platform's icon, under an optional caption.

    Args:
        gt: The table.
        accounts: ``{platform: handle}``. Platforms are Font Awesome brand icon names or the aliases ``x``/``twitter``,
            ``ig``, ``bsky``, ``gh``, ``yt``, ``fb``, ``web``/``website``/``link`` and ``email``/``mail``.
        caption: A caption line above the handles, drawn by ``gt_538_caption``.
        stack: One account per line instead of a row.
        separator: The string between accounts in a row.
        align: The handle line's alignment.
        icon_color: The icons' color; defaults to the text color.
        icon_height: The icons' CSS height (``em`` scales with ``text_size``).
        text_size: The handles' CSS font size; defaults to the source-note size.
        text_weight: The handles' font weight.
        **kwargs: Passed to ``gt_538_caption`` (``rule_color``, ``rule_width``, ``size``) when ``caption`` is given.

    Returns:
        GT: A new table with the handle line (and caption) as source notes.

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.
        ValueError: If ``accounts`` is not a non-empty mapping of platform to handle, or an icon is not in the
            installed faicons.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_social_tag

            gt = gt_social_tag(GT(pl.DataFrame({"team": ["LV"]})), {"gh": "sportsdataverse", "web": "sdv.org"})

    See Also:
        Ported from sdvplotR ``gt_social_tag()``: https://sdvplotR.sportsdataverse.org/reference/gt_social_tag.html
    """
    _check_gt(gt)
    if not isinstance(accounts, Mapping) or not accounts or not all(isinstance(k, str) and k for k in accounts):
        raise ValueError("accounts must be a mapping of platform to handle, such as {'x': '@you', 'gh': 'you'}")
    fill = "currentColor" if icon_color is None else icon_color
    items = [
        "<span style='display:inline-flex; align-items:center; gap:0.3em; white-space:nowrap;'>"
        f"{_social_icon(key, fill, icon_height)}{handle}</span>"
        for key, handle in accounts.items()
    ]
    joined = "<br>".join(items) if stack else separator.join(items)
    box = f"text-align:{align};"
    if text_size is not None:
        box += f" font-size:{text_size};"
    if text_weight is not None:
        box += f" font-weight:{text_weight};"
    social = f"<div style='{box}'>{joined}</div>"
    if caption is not None:
        from sdvplot.great_tables._cells import gt_538_caption  # wave C1

        return gt_538_caption(gt, top_caption=caption, bottom_caption=social, **kwargs)
    return gt.tab_source_note(html(social))


def _snake_shape(n: int, n_cols: int, rows_per_col: int | None) -> tuple[int, int]:
    """(blocks, rows per block) for ``n`` rows, from ``n_cols`` or, when given, ``rows_per_col``."""
    if rows_per_col is not None:
        per = int(rows_per_col)
        if per < 1:
            raise ValueError("rows_per_col must be at least 1")
        return math.ceil(n / per), per
    blocks = int(n_cols)
    if blocks < 1:
        raise ValueError("n_cols must be at least 1")
    return blocks, math.ceil(n / blocks)


def _block(data: Any, cols: list[str], i: int, per: int, fill: Any) -> Any:
    """Rows ``i*per`` to ``(i+1)*per`` of ``cols`` (a pandas or polars frame), padded with ``fill`` to ``per`` rows
    and suffixed ``_{i+1}``."""
    names = {c: f"{c}_{i + 1}" for c in cols}
    if isinstance(data, pl.DataFrame):
        part = data.select(cols).slice(i * per, per)
        short = per - part.height
        if short:
            pad = pl.DataFrame({c: [fill] * short for c in cols})
            part = pl.concat([part, pad], how="vertical_relaxed")
        return part.rename(names)
    part = data[cols].iloc[i * per : (i + 1) * per].reset_index(drop=True)
    short = per - len(part)
    if short:
        # object dtype keeps integers as integers next to the padding (a float column would print 3 as 3.0)
        part = part.astype(object).reindex(range(per))
        part.iloc[per - short :] = fill
    return part.rename(columns=names)


def _side_by_side(parts: list[Any]) -> Any:
    return nw.concat([nw.from_native(p, eager_only=True) for p in parts], how="horizontal").to_native()


def gt_snake(
    gt: GT,
    n_cols: int = 2,
    rows_per_col: int | None = None,
    gap: float = 20,
    fill: str | None = "",
    clean_gaps: bool = True,
) -> GT:
    """Wrap a long table into side-by-side blocks (a top-50 list as two columns of 25).

    The table is rebuilt from its data: each visible column appears once per block, suffixed ``_1``, ``_2``, ...
    (``gt_snake_align`` reshapes helper data the same way). Labels, the header, source notes and body-cell styles
    (``tab_style`` on ``loc.body``, moved to their block's column and row) carry over; formats, text transforms,
    options and themes do not, so apply those after snaking. The recorded legend scale is dropped too.

    Args:
        gt: The table, from pandas or polars data.
        n_cols: The number of blocks.
        rows_per_col: Rows per block; given this, the number of blocks follows from the data.
        gap: Pixels of empty spacer column between blocks; 0 for none.
        fill: What the padding cells of the last block show; ``None`` leaves them missing.
        clean_gaps: Scrub borders, fills and rules off the spacer columns so the gap stays clean under any theme
            (set ``False`` when you style the gap yourself).

    Returns:
        GT: A new, snaked table (``gt`` unchanged when there are fewer than two blocks or no rows).

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.
        ValueError: If ``n_cols`` or ``rows_per_col`` is below 1.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_snake

            df = pl.DataFrame({"rank": range(1, 51), "team": [f"T{i}" for i in range(1, 51)]})
            gt = gt_snake(GT(df), n_cols=2).fmt_integer(["rank_1", "rank_2"])

    See Also:
        Ported from sdvplotR ``gt_snake()``: https://sdvplotR.sportsdataverse.org/reference/gt_snake.html
    """
    _check_gt(gt)
    data = gt._tbl_data
    n = len(_frame(gt))
    blocks, per = _snake_shape(n, n_cols, rows_per_col)
    if blocks < 2 or n == 0:
        return gt

    cols = [c.var for c in gt._boxhead if c.type.name in ("default", "stub")]
    labels: dict[str, Any] = {c.var: c.var if c.column_label is None else c.column_label for c in gt._boxhead}
    parts: list[Any] = []
    spacers: list[str] = []
    for i in range(blocks):
        parts.append(_block(data, cols, i, per, None))
        if gap > 0 and i < blocks - 1:
            spacers.append(f".gap{i + 1}")
            parts.append(type(data)({spacers[-1]: [""] * per}))
    out = _side_by_side(parts)

    table_id = gt._options.table_id.value
    do_clean = clean_gaps and bool(spacers)
    if table_id is None and do_clean:
        table_id = "".join(random.choices(string.ascii_lowercase, k=10))
    res = GT(out, id=table_id)
    res = res.cols_label(
        cases={f"{c}_{i + 1}": labels[c] for i in range(blocks) for c in cols} | {s: "" for s in spacers}
    )
    padded = blocks * per - n
    if padded and fill is not None:
        last = [f"{c}_{blocks}" for c in cols]
        res = res.sub_missing(columns=last, rows=list(range(per - padded, per)), missing_text=fill)
    if spacers:
        res = res.cols_width(cases={s: f"{gap:g}px" for s in spacers})

    # body-cell styles move to their block's column and row; other column styles repeat in every block
    moved = []
    for s in gt._styles:
        if s.colname is not None and s.colname not in cols:
            continue
        if type(s.locname).__name__ == "LocBody" and s.rownum is not None:
            block, row = divmod(s.rownum, per)
            moved.append(dataclasses.replace(s, colname=f"{s.colname}_{block + 1}", rownum=row))
        elif s.colname is not None:
            moved.extend(dataclasses.replace(s, colname=f"{s.colname}_{i + 1}") for i in range(blocks))
        else:
            moved.append(s)
    # what belongs to the table rather than its cells carries over as is
    res = res._replace(_heading=gt._heading, _source_notes=gt._source_notes, _styles=[*res._styles, *moved])

    if do_clean:
        names = nw.from_native(out, eager_only=True).columns
        css = []
        for k in (names.index(s) + 1 for s in spacers):
            cell = f"#{table_id} td:nth-child"
            css += [
                f"{cell}({k}) {{border: 1px solid transparent !important; background: transparent !important;"
                " box-shadow: none !important;}",
                f"{cell}({k - 1}) {{border-right: 1px solid transparent !important;}}",
                f"{cell}({k + 1}) {{border-left: 1px solid transparent !important;}}",
            ]
        res = res.opt_css("\n".join(css)).tab_style(
            gst.borders(sides="all", color="transparent", weight="1px"), loc.column_labels(columns=spacers)
        )
    return res


def gt_snake_align(x: Any, n_cols: int = 2, rows_per_col: int | None = None, fill: Any = None) -> Any:
    """Reshape a frame the way ``gt_snake`` reshapes a table, so helper data (highlight masks, colors) lines up.

    Args:
        x: A pandas or polars frame with one row per row of the un-snaked table.
        n_cols: The number of blocks, as passed to ``gt_snake``.
        rows_per_col: Rows per block, as passed to ``gt_snake`` (then ``n_cols`` follows from the data).
        fill: The value of the trailing cells when the rows do not divide evenly (missing by default).

    Returns:
        The same kind of frame, with each column once per block, suffixed ``_1``, ``_2``, ... (``x`` unchanged when
        there are fewer than two blocks or no rows).

    Raises:
        TypeError: If ``x`` is not a pandas or polars frame.
        ValueError: If ``n_cols`` or ``rows_per_col`` is below 1.

    Example:
        ::

            import polars as pl
            from sdvplot.great_tables import gt_snake_align

            wide = gt_snake_align(pl.DataFrame({"hot": [True, False, True]}), n_cols=2)   # hot_1, hot_2

    See Also:
        Ported from sdvplotR ``gt_snake_align()``: https://sdvplotR.sportsdataverse.org/reference/gt_snake_align.html
    """
    frame = nw.from_native(x, eager_only=True)
    n = len(frame)
    blocks, per = _snake_shape(n, n_cols, rows_per_col)
    if blocks < 2 or n == 0:
        return x
    return _side_by_side([_block(x, frame.columns, i, per, fill) for i in range(blocks)])


def _strwrap(text: str, width: int) -> list[str]:
    """R's ``strwrap``: greedy lines shorter than ``width``, split on whitespace only."""
    return textwrap.wrap(text, max(width - 1, 1), break_long_words=False, break_on_hyphens=False)


def _balanced(words: list[str], width: int) -> list[str]:
    """As many lines as ``strwrap`` needs, filled toward the mean length instead of the maximum."""
    greedy = _strwrap(" ".join(words), width)
    if len(greedy) <= 1:
        return [" ".join(words)]
    target = math.ceil(sum(len(w) + 1 for w in words) / len(greedy))
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}" if current else word
        if len(candidate) > target and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    return [*lines, current] if current else lines


def gt_wrap_labels(gt: GT, columns: Any = None, width: int = 12, balance: bool = True) -> GT:
    """Wrap long column labels onto several lines, so narrow columns keep readable headers.

    A one-word label, or one already shorter than ``width``, is left alone; a single long word is never split.

    Args:
        gt: The table.
        columns: The columns whose labels wrap (any great_tables selection); defaults to every column.
        width: The target line length in characters (lines stay shorter than this, as R's ``strwrap``).
        balance: Even the lines out instead of filling them greedily.

    Returns:
        GT: A new table with the wrapped labels.

    Raises:
        TypeError: If ``gt`` is not a great_tables ``GT``.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_wrap_labels

            gt = gt_wrap_labels(GT(pl.DataFrame({"Expected points added per play": [0.12]})))

    See Also:
        Ported from sdvplotR ``gt_wrap_labels()``: https://sdvplotR.sportsdataverse.org/reference/gt_wrap_labels.html
    """
    _check_gt(gt)
    labels = {c.var: c.column_label for c in gt._boxhead}
    wrapped: dict[str, Any] = {}
    for col in _columns(gt, columns):
        label = labels.get(col)
        text = col if label is None else str(getattr(label, "text", label))
        words = text.split()
        if len(words) <= 1:
            continue
        lines = _balanced(words, width) if balance else _strwrap(text, width)
        if len(lines) > 1:
            wrapped[col] = html("<br>".join(lines))
    return gt.cols_label(cases=wrapped) if wrapped else gt

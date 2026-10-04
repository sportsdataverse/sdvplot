"""Legends, layout and annotation helpers for great_tables, ported from sdvplotR's ``gt_*`` functions (wave C2)."""

from __future__ import annotations

import base64
import copy
import datetime
import functools
import math
import random
import string
import warnings
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import quote

import narwhals as nw
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

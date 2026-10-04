"""Legends, layout and annotation helpers for great_tables, ported from sdvplotR's ``gt_*`` functions (wave C2)."""

from __future__ import annotations

import base64
import datetime
import math
import random
import string
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import quote

from great_tables import GT, google_font, html, loc
from great_tables import style as gst

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

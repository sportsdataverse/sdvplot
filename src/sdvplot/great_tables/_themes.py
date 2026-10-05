"""Table themes for great_tables: the port of sdvplotR's ``gt_theme_*`` functions.

Each theme ports its R file's ``opt_table_font``, ``tab_style``, ``tab_options`` and ``opt_css`` calls one to one, with
the same arguments and defaults (``docs/PARITY_TABLES.md`` lists where great_tables differs).

great_tables has no public way to read a table back, so this module reads four private attributes, each pinned by a
test: ``GT._options`` (the table id and option values), ``GT._tbl_data`` (columns and row count), ``GT._spanners``
(spanner ids) and ``GT._styles`` (rescaled by ``density``). It also subclasses the private ``GoogleFont`` (``_Font``).
"""

from __future__ import annotations

import dataclasses
import inspect
import math
import numbers
import re
from typing import Any

import narwhals as nw
from great_tables import GT, html, loc, px, style
from great_tables._helpers import GoogleFont

from sdvplot._contrast import hex6, on_color
from sdvplot.great_tables._marks import (
    DENSITY,
    _check_gt,
    _density,
    _secondary_on,
    _table_font,
    _table_id,
)

# sdvplotR's .theme_scale_output(): which density role each styled location and size option scales with
_STYLE_ROLE: dict[type, str] = {
    loc.title: "title",
    loc.subtitle: "subtitle",
    loc.column_labels: "label",
    loc.spanner_labels: "label",
    loc.row_groups: "group",
    loc.stubhead: "label",
    loc.body: "body",
    loc.stub: "body",
    loc.source_notes: "source",
    loc.footnotes: "source",
}
_OPTION_ROLE = {
    "table_font_size": "body",
    "stub_font_size": "body",
    "heading_title_font_size": "title",
    "heading_subtitle_font_size": "subtitle",
    "column_labels_font_size": "label",
    "row_group_font_size": "group",
    "source_notes_font_size": "source",
    "data_row_padding": "pad",
    "row_group_padding": "pad",
    "column_labels_padding": "pad",
    "heading_padding": "pad",
    "source_notes_padding": "pad",
    "summary_row_padding": "pad",
    "grand_summary_row_padding": "pad",
}
_PX = re.compile(r"-?[0-9.]+px")


class _Font(GoogleFont):
    """A Google font that loads every weight. great_tables' import asks for the regular face only, so a theme's 600 or
    700 would be synthesized; a discrete weight list (not a ``100..900`` range) returns the faces a family has."""

    def make_import_stmt(self) -> str:
        axes = ";".join(f"{i},{w}" for i in (0, 1) for w in range(100, 1000, 100))
        family = self.font.replace(" ", "+")
        return f"@import url('https://fonts.googleapis.com/css2?family={family}:ital,wght@{axes}&display=swap');"


def _font(name: str) -> GoogleFont:
    return _Font(name)


def _text(**kwargs: Any) -> Any:
    """``style.text`` taking sdvplotR's numeric weights (typed as keywords in great_tables; any weight renders)."""
    return style.text(**kwargs)


def _color(value: str, arg: str) -> str:
    try:
        return hex6(value)
    except ValueError:
        raise ValueError(f"{arg} must be a hex color with no transparency, such as '#8C2F1E', not {value!r}") from None


def _shape(gt: GT) -> tuple[list[str], int]:
    """The data's column names and row count."""
    data = nw.from_native(gt._tbl_data, eager_only=True)
    return list(data.columns), len(data)


def _on_spanners(gt: GT, *styles: Any) -> GT:
    """R's ``cells_column_spanners()``: every spanner the table has now (great_tables needs their ids)."""
    ids = [s.spanner_id for s in gt._spanners]
    return gt.tab_style(list(styles), loc.spanner_labels(ids=ids)) if ids else gt


def _row_rules(gt: GT, color: str) -> GT:
    """A rule under every body row but the last: R's ``cells_body(rows = 1:(nrow(data) - 1))`` bottom border.

    A one-row table gets none; R's ``1:0`` drew one under its only row.
    """
    n = _shape(gt)[1]
    return gt.tab_style(style.borders(sides="bottom", color=color), loc.body(rows=list(range(n - 1)))) if n > 1 else gt


def _hide_spanner_row(gt: GT, table_id: str) -> GT:
    """sdvplotR's spanner over every column, hidden by CSS.

    R hides it by element id; great_tables gives a spanner stacked over another no id, so the label carries a class
    and the CSS hides the cell holding it. A table themed twice already has the spanner (great_tables refuses a second
    one with the same id).
    """
    if "toss_out_spanner_dev" not in [s.spanner_id for s in gt._spanners]:
        label = html('<span class="sdvplot-hidden-spanner"></span>')
        gt = gt.tab_spanner(label, columns=_shape(gt)[0], id="toss_out_spanner_dev")
    return gt.opt_css(_css(table_id, "th:has(.sdvplot-hidden-spanner)", "display: none;"))


def _css(table_id: str, selectors: str | list[str], body: str) -> str:
    """One CSS rule scoped to the table: ``#id sel1, #id sel2 { body }``."""
    sel = [selectors] if isinstance(selectors, str) else selectors
    return ", ".join(f"#{table_id} {s}" for s in sel) + " { " + body + " }"


def _tabular_nums(table_id: str) -> str:
    # not font-feature-settings: 'tnum', which also spaces out commas in some faces
    return _css(table_id, "td", "font-variant-numeric: tabular-nums;")


def _last_row_border(table_id: str, background: str) -> str:
    # gt's hline under the last row doubles up with the table's closing rule
    return _css(table_id, "tbody tr:last-child", f"border-bottom: 2px solid {background};")


def _scale_len(value: Any, k: float) -> Any:
    """A ``"12px"`` length times ``k``, rounded to 0.1 px as R does; any other value (``"90%"``, None) unchanged."""
    if isinstance(value, str) and _PX.fullmatch(value):
        return f"{round(float(value[:-2]) * k, 1):g}px"
    return value


def _scale_output(gt: GT, density: str) -> GT:
    """sdvplotR's ``.theme_scale_output()``: rescale the px sizes a finished table holds by ``density``.

    For the themes that hard-code their sizes. Every text size set through ``tab_style`` and every size and padding
    option (great_tables' defaults included) scales by its role's ratio to ``"comfortable"``, as in R.
    """
    d, base = _density(density), DENSITY["comfortable"]
    k = {role: d[role] / base[role] for role in d}
    if all(v == 1 for v in k.values()):
        return gt
    styles = []
    for info in gt._styles:
        role = _STYLE_ROLE.get(type(info.locname))
        cells = [
            dataclasses.replace(s, size=_scale_len(s.size, k[role]))
            if role is not None and isinstance(s, style.text) and s.size is not None
            else s
            for s in info.styles
        ]
        styles.append(dataclasses.replace(info, styles=cells))
    gt = gt._replace(_styles=styles)
    options = {name: _scale_len(getattr(gt._options, name).value, k[role]) for name, role in _OPTION_ROLE.items()}
    return gt.tab_options(**options)


def _adjust_luminance(color: str, steps: float) -> str:
    """``gt::adjust_luminance()``: shift a color's HCL luminance ``steps`` along a logistic curve (R's grDevices math).

    Matches R on 426 of 432 sampled colors and steps (2026-10-04); the other six are pure white, where R returns NA
    and this returns white.
    """

    def c2to3(x: float, y: float) -> list[float]:
        return [x / y, 1.0, (1 - x - y) / y]

    # grDevices make.rgb(): sRGB primaries and R's own D65 white point (0.3137, 0.3291)
    p = [c2to3(0.64, 0.33), c2to3(0.30, 0.60), c2to3(0.15, 0.06)]
    white = c2to3(0.3137, 0.3291)
    det = (
        p[0][0] * (p[1][1] * p[2][2] - p[1][2] * p[2][1])
        - p[0][1] * (p[1][0] * p[2][2] - p[1][2] * p[2][0])
        + p[0][2] * (p[1][0] * p[2][1] - p[1][1] * p[2][0])
    )
    inv = [
        [
            (p[(j + 1) % 3][(i + 1) % 3] * p[(j + 2) % 3][(i + 2) % 3]
             - p[(j + 1) % 3][(i + 2) % 3] * p[(j + 2) % 3][(i + 1) % 3]) / det
            for j in range(3)
        ]
        for i in range(3)
    ]  # fmt: skip
    s = [sum(white[k] * inv[k][j] for k in range(3)) for j in range(3)]
    m = [[s[r] * p[r][j] for j in range(3)] for r in range(3)]

    c = hex6(color)
    rgb = [int(c[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [v / 12.92 if v < 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    x, y, z = (sum(lin[k] * m[k][j] for k in range(3)) for j in range(3))
    # convertColor(, "sRGB", "Luv")
    denom, wdenom = x + 15 * y + 3 * z, white[0] + 15 * white[1] + 3 * white[2]
    u1, v1 = (4 * x / denom, 9 * y / denom) if denom else (1.0, 1.0)
    yr = y / white[1]
    lum = 24389 / 27 * yr if yr <= 216 / 24389 else 116 * yr ** (1 / 3) - 16
    u, v = 13 * lum * (u1 - 4 * white[0] / wdenom), 13 * lum * (v1 - 9 * white[1] / wdenom)
    hue, chroma = math.atan2(v, u), math.hypot(u, v)
    frac = lum / 100
    if frac <= 0:
        return "#000000"
    lum = 100.0 if frac >= 1 else 100 / (1 + math.exp(-(math.log(frac / (1 - frac)) + steps)))
    # grDevices hcl(h, c, l): polar Luv back to sRGB, clamped into gamut
    yy = 100 * (((lum + 16) / 116) ** 3 if lum > 7.999592 else lum / 903.3)
    uu = chroma * math.cos(hue) / (13 * lum) + 0.1978398
    vv = chroma * math.sin(hue) / (13 * lum) + 0.4683363
    xx = 9.0 * yy * uu / (4 * vv)
    zz = -xx / 3 - 5 * yy + 3 * yy / vv

    def gamma(t: float) -> float:
        return 1.055 * t ** (1 / 2.4) - 0.055 if t > 0.00304 else 12.92 * t

    out = [
        gamma((3.240479 * xx - 1.537150 * yy - 0.498535 * zz) / 100),
        gamma((-0.969256 * xx + 1.875992 * yy + 0.041556 * zz) / 100),
        gamma((0.055648 * xx - 0.204043 * yy + 1.057311 * zz) / 100),
    ]
    return "#" + "".join(f"{min(255, max(0, int(255 * t + 0.5))):02x}" for t in out)


def gt_theme_almanac(
    gt: GT, accent: str = "#8C2F1E", density: str = "compact", stripe: str | None = "#F1F1EF", **options: Any
) -> GT:
    """Record-book theme: a slab body, narrow condensed labels, tight rows and banded rows, like a statistical abstract.

    Args:
        gt: The great_tables ``GT`` to theme.
        accent: Hex color of the row-group labels and the rule above the table.
        density: The type and padding scale: "comfortable" (14px body), "compact" (12px) or "social" (17px, the
            scale saved images use).
        stripe: Hex color of the banded rows; None switches banding off and keeps the rest of the theme.
        **options: Passed to ``GT.tab_options`` last, so they override the theme (great_tables names, e.g.
            ``table_font_size``).

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: A color is not hex, or ``density`` is not one of the three scales.

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_theme_almanac

            gt_theme_almanac(GT(df), stripe=None, accent="#1F3A5F")

    See Also:
        Ported from sdvplotR ``gt_theme_almanac()``: https://sdvplotR.sportsdataverse.org/reference/gt_theme_almanac.html
    """
    d = _density(density)
    accent = _color(accent, "accent")
    stripe = None if stripe is None else _color(stripe, "stripe")
    ink, secondary, rule = "#1A1A1A", "#6B6B68", "#D8D8D4"
    gt, tid = _table_id(_check_gt(gt))
    narrow = _font("Archivo Narrow")
    label = _text(font=narrow, weight=700, size=px(d["label"] + 1), color=ink, transform="uppercase")
    gt = (
        _table_font(gt, _font("Zilla Slab"))
        .opt_row_striping(row_striping=stripe is not None)
        .tab_style(_text(color=ink, size=px(d["body"])), loc.body())
        .tab_style(_text(weight=700, size=px(d["title"]), color=ink), loc.title())
        .tab_style(_text(weight=400, size=px(d["subtitle"]), color=secondary), loc.subtitle())
        .tab_style(label, loc.column_labels())
        .pipe(_on_spanners, label)
        .tab_style(
            _text(font=narrow, weight=700, size=px(d["group"] + 1), color=accent, transform="uppercase"),
            loc.row_groups(),
        )
        .tab_style(_text(font=narrow, size=px(d["source"] + 1), color=secondary), [loc.source_notes(), loc.footnotes()])
        .tab_options(
            table_background_color="#FFFFFF",
            row_striping_background_color=stripe or "#FFFFFF",
            table_font_size=px(d["body"]),
            data_row_padding=px(d["pad"]),
            table_border_top_style="solid",
            table_border_top_width=px(2),
            table_border_top_color=accent,
            table_border_bottom_style="none",
            heading_align="left",
            heading_border_bottom_style="none",
            heading_padding=px(d["pad"] + 2),
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="solid",
            column_labels_border_bottom_width=px(1.5),
            column_labels_border_bottom_color=ink,
            column_labels_padding=px(d["pad"] + 1),
            # banding does the work, so no row rules
            table_body_border_top_style="none",
            table_body_hlines_style="none",
            table_body_border_bottom_style="solid",
            table_body_border_bottom_width=px(1),
            table_body_border_bottom_color=ink,
            row_group_border_top_style="solid",
            row_group_border_top_width=px(1),
            row_group_border_top_color=rule,
            row_group_border_bottom_style="none",
            row_group_padding=px(max(d["pad"], 3)),
            source_notes_border_lr_style="none",
            source_notes_border_bottom_style="none",
            source_notes_padding=px(d["pad"] + 2),
        )
        .opt_css(
            "\n".join(
                [
                    _tabular_nums(tid),
                    _last_row_border(tid, "#FFFFFF"),
                    _css(tid, [".gt_col_heading", ".gt_column_spanner"], "letter-spacing: 0.05em;"),
                    _css(tid, ".gt_group_heading", "letter-spacing: 0.05em;"),
                    _css(tid, ".gt_subtitle", f"padding-bottom: {d['pad'] + 6}px !important;"),
                    _css(tid, ".gt_title", f"padding-bottom: {math.ceil(d['pad'] / 2)}px !important;"),
                ]
            )
        )
    )
    # the caller's options last, so they win
    return gt.tab_options(**options)


def gt_theme_booktabs(gt: GT, accent: str = "#111111", density: str = "comfortable", **options: Any) -> GT:
    """Academic booktabs theme: three horizontal rules and nothing else, the way LaTeX booktabs draws them.

    Args:
        gt: The great_tables ``GT`` to theme.
        accent: Hex color of the three rules and the row-group labels.
        density: The type and padding scale: "comfortable", "compact" or "social".
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``accent`` is not hex, or ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_booktabs(GT(df), density="compact")

    See Also:
        Ported from sdvplotR ``gt_theme_booktabs()``: https://sdvplotR.sportsdataverse.org/reference/gt_theme_booktabs.html
    """
    d = _density(density)
    accent = _color(accent, "accent")
    ink, secondary, bg = "#111111", "#5A5A5A", "#FFFFFF"
    gt, tid = _table_id(_check_gt(gt))
    serif = _font("Tinos")
    label = _text(font=serif, weight=700, size=px(d["label"] + 1), color=ink)
    gt = (
        _table_font(gt, _font("Tinos"))
        .tab_style(_text(color=ink, size=px(d["body"])), loc.body())
        .tab_style(_text(font=serif, weight=700, size=px(d["title"]), color=ink), loc.title())
        .tab_style(
            _text(font=serif, weight=400, style="italic", size=px(d["subtitle"]), color=secondary), loc.subtitle()
        )
        # column labels, same serif, no caps
        .tab_style(label, loc.column_labels())
        .pipe(_on_spanners, label)
        # row groups as a bold italic subheading
        .tab_style(
            _text(font=serif, weight=700, style="italic", size=px(d["group"] + 1), color=accent), loc.row_groups()
        )
        .tab_style(_text(font=serif, size=px(d["source"]), color=secondary), [loc.source_notes(), loc.footnotes()])
        .tab_options(
            table_background_color=bg,
            table_font_size=px(d["body"]),
            data_row_padding=px(d["pad"]),
            heading_align="left",
            heading_border_bottom_style="none",
            heading_padding=px(d["pad"]),
            # top rule, above the column labels
            table_border_top_style="none",
            column_labels_border_top_style="solid",
            column_labels_border_top_width=px(2),
            column_labels_border_top_color=accent,
            # mid rule, under the column labels
            column_labels_border_bottom_style="solid",
            column_labels_border_bottom_width=px(1),
            column_labels_border_bottom_color=accent,
            column_labels_padding=px(max(d["pad"] - 1, 2)),
            # nothing between the data rows
            table_body_border_top_style="none",
            table_body_hlines_style="none",
            # bottom rule, closing the body
            table_body_border_bottom_style="solid",
            table_body_border_bottom_width=px(2),
            table_body_border_bottom_color=accent,
            table_border_bottom_style="none",
            column_labels_vlines_style="none",
            table_body_vlines_style="none",
            stub_border_style="none",
            # a midrule above each row group
            row_group_border_top_style="solid",
            row_group_border_top_width=px(1),
            row_group_border_top_color=accent,
            row_group_border_bottom_style="none",
            row_group_padding=px(max(d["pad"] - 2, 2)),
            source_notes_border_lr_style="none",
            source_notes_border_bottom_style="none",
            source_notes_padding=px(d["pad"]),
        )
        .opt_css("\n".join([_tabular_nums(tid), _css(tid, ".gt_sourcenote", f"padding-top: {d['pad'] + 4}px;")]))
    )
    return gt.tab_options(**options)


def gt_theme_broadsheet(
    gt: GT, accent: str = "#A6081A", density: str = "comfortable", paper: str = "white", **options: Any
) -> GT:
    """Newspaper theme: a serif body on warm paper, small letterspaced sans labels, hairlines between rows.

    Args:
        gt: The great_tables ``GT`` to theme.
        accent: Hex color of the rule above the table and the row-group labels.
        density: The type and padding scale: "comfortable", "compact" or "social".
        paper: The table background: "white" (a warm off-white), "salmon" (the financial-press pink) or any hex
            color, which keeps the neutral hairline.
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``accent`` or ``paper`` is not a hex color (or preset), or ``density`` is not one of the three
            scales.

    Example:
        ::

            gt_theme_broadsheet(GT(df), paper="salmon")

    See Also:
        Ported from sdvplotR ``gt_theme_broadsheet()``:
        https://sdvplotR.sportsdataverse.org/reference/gt_theme_broadsheet.html
    """
    d = _density(density)
    accent = _color(accent, "accent")
    # each paper preset carries a rule color matched to its ground
    presets = {"white": ("#FBFAF7", "#DEDAD2"), "salmon": ("#FFF1E5", "#EAD9C7")}
    bg, rule = presets.get(paper) or (_color(paper, "paper"), "#DEDAD2")
    ink, secondary = "#16130F", "#5C574F"
    gt, tid = _table_id(_check_gt(gt))
    headline, sans = _font("Newsreader"), _font("Public Sans")
    label = _text(font=sans, weight=600, size=px(d["label"]), color=secondary, transform="uppercase")
    gt = (
        _table_font(gt, _font("Source Serif 4"))
        .tab_style(_text(color=ink, size=px(d["body"])), loc.body())
        .tab_style(_text(font=headline, weight=600, size=px(d["title"]), color=ink), loc.title())
        .tab_style(
            _text(font=headline, weight=400, style="italic", size=px(d["subtitle"]), color=secondary),
            loc.subtitle(),
        )
        # small letterspaced sans labels
        .tab_style(label, loc.column_labels())
        .pipe(_on_spanners, label)
        # row groups get a label over a rule, not a filled band
        .tab_style(
            _text(font=sans, weight=700, size=px(d["group"]), color=accent, transform="uppercase"), loc.row_groups()
        )
        .tab_style(_text(font=sans, size=px(d["source"]), color=secondary), [loc.source_notes(), loc.footnotes()])
        .tab_options(
            table_background_color=bg,
            table_font_size=px(d["body"]),
            data_row_padding=px(d["pad"]),
            # thin accent rule across the top
            table_border_top_style="solid",
            table_border_top_width=px(2),
            table_border_top_color=accent,
            table_border_bottom_style="none",
            heading_align="left",
            heading_border_bottom_style="none",
            heading_padding=px(d["pad"]),
            # the one heavy rule, under the column labels
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="solid",
            column_labels_border_bottom_width=px(1.5),
            column_labels_border_bottom_color=ink,
            column_labels_padding=px(max(d["pad"] - 2, 2)),
            # hairlines between rows, firmer rule to close the body
            table_body_border_top_style="none",
            table_body_hlines_color=rule,
            table_body_hlines_width=px(1),
            table_body_border_bottom_style="solid",
            table_body_border_bottom_width=px(1),
            table_body_border_bottom_color=ink,
            row_group_border_top_style="solid",
            row_group_border_top_width=px(1),
            row_group_border_top_color=ink,
            row_group_border_bottom_style="none",
            row_group_padding=px(max(d["pad"] - 3, 2)),
            source_notes_border_lr_style="none",
            source_notes_border_bottom_style="none",
            source_notes_padding=px(d["pad"]),
        )
        .opt_css(
            "\n".join(
                [
                    _tabular_nums(tid),
                    _last_row_border(tid, bg),
                    # no tab_options equivalent for letter-spacing
                    _css(tid, [".gt_col_heading", ".gt_column_spanner"], "letter-spacing: 0.09em;"),
                    # gt's .gt_row_group_first: great_tables has no such class, so the row after a group heading
                    _css(tid, ".gt_group_heading_row + tr td", f"padding-top: {max(d['pad'] - 2, 2)}px;"),
                    _css(tid, ".gt_group_heading", "letter-spacing: 0.08em;"),
                    # the heading needs more air under it than the rows have between them
                    _css(tid, ".gt_subtitle", f"padding-bottom: {d['pad'] + 8}px !important;"),
                    _css(tid, ".gt_title", f"padding-bottom: {math.ceil(d['pad'] / 2)}px !important;"),
                    # keep the source note off the closing rule
                    _css(tid, ".gt_sourcenote", f"padding-top: {d['pad'] + 4}px;"),
                ]
            )
        )
    )
    return gt.tab_options(**options)


def gt_theme_swiss(gt: GT, accent: str = "#111111", density: str = "comfortable", **options: Any) -> GT:
    """International Typographic Style theme: a grotesque, generous space instead of rules, one accent rule.

    Args:
        gt: The great_tables ``GT`` to theme.
        accent: Hex color, used once, on the rule beneath the column labels. The default reads as no color at all.
        density: The type and padding scale: "comfortable", "compact" or "social".
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``accent`` is not hex, or ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_swiss(GT(df), accent="#E30613")

    See Also:
        Ported from sdvplotR ``gt_theme_swiss()``: https://sdvplotR.sportsdataverse.org/reference/gt_theme_swiss.html
    """
    d = _density(density)
    accent = _color(accent, "accent")
    ink, secondary = "#111111", "#6B6B6B"  # 5.28:1 on white; #7A7A7A missed 4.5
    gt, tid = _table_id(_check_gt(gt))
    label = _text(weight=500, size=px(d["label"]), color=ink, transform="uppercase")
    gt = (
        _table_font(gt, _font("Archivo"))
        .tab_style(_text(color=ink, size=px(d["body"]), weight=400), loc.body())
        .tab_style(_text(weight=700, size=px(d["title"] + 4), color=ink), loc.title())
        .tab_style(_text(weight=400, size=px(d["subtitle"]), color=secondary), loc.subtitle())
        .tab_style(label, loc.column_labels())
        .pipe(_on_spanners, label)
        .tab_style(_text(weight=500, size=px(d["group"]), color=secondary, transform="uppercase"), loc.row_groups())
        .tab_style(_text(size=px(d["source"]), color=secondary), [loc.source_notes(), loc.footnotes()])
        .tab_options(
            table_background_color="#FFFFFF",
            table_font_size=px(d["body"]),
            # padding is the design here
            data_row_padding=px(d["pad"] + 5),
            table_border_top_style="none",
            table_border_bottom_style="none",
            heading_align="left",
            heading_border_bottom_style="none",
            heading_padding=px(d["pad"] + 4),
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="solid",
            column_labels_border_bottom_width=px(1),
            column_labels_border_bottom_color=accent,
            column_labels_padding=px(d["pad"] + 2),
            # no row rules, space does the separating
            table_body_border_top_style="none",
            table_body_hlines_style="none",
            table_body_border_bottom_style="solid",
            table_body_border_bottom_width=px(1),
            table_body_border_bottom_color=ink,
            row_group_border_top_style="none",
            row_group_border_bottom_style="none",
            row_group_padding=px(d["pad"] + 6),
            source_notes_border_lr_style="none",
            source_notes_border_bottom_style="none",
            source_notes_padding=px(d["pad"] + 4),
        )
        .opt_css(
            "\n".join(
                [
                    _tabular_nums(tid),
                    _last_row_border(tid, "#FFFFFF"),
                    _css(tid, [".gt_col_heading", ".gt_column_spanner"], "letter-spacing: 0.12em;"),
                    _css(tid, ".gt_group_heading", "letter-spacing: 0.12em;"),
                    _css(
                        tid,
                        ".gt_title",
                        f"letter-spacing: -0.02em; padding-bottom: {math.ceil(d['pad'] / 2)}px !important;",
                    ),
                    _css(tid, ".gt_subtitle", f"padding-bottom: {d['pad'] + 14}px !important;"),
                ]
            )
        )
    )
    return gt.tab_options(**options)


def gt_theme_tufte(gt: GT, accent: str = "#111111", density: str = "comfortable", **options: Any) -> GT:
    """Tufte theme: an old-style serif on cream, italic labels, one hairline under the labels and almost no ink.

    Args:
        gt: The great_tables ``GT`` to theme.
        accent: Hex color of the header hairline and the row-group labels; a muted red or rust gives Tufte's marginal
            accent.
        density: The type and padding scale: "comfortable", "compact" or "social".
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``accent`` is not hex, or ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_tufte(GT(df), accent="#A0522D")

    See Also:
        Ported from sdvplotR ``gt_theme_tufte()``: https://sdvplotR.sportsdataverse.org/reference/gt_theme_tufte.html
    """
    d = _density(density)
    accent = _color(accent, "accent")
    ink, secondary, hair, bg = "#111111", "#6F6A60", "#C9C4B8", "#FFFFF8"
    gt, tid = _table_id(_check_gt(gt))
    serif = _font("EB Garamond")
    label = _text(font=serif, weight=400, style="italic", size=px(d["label"] + 2), color=secondary)
    gt = (
        _table_font(gt, _font("EB Garamond"))
        .tab_style(_text(color=ink, size=px(d["body"] + 1)), loc.body())
        .tab_style(_text(font=serif, weight=500, size=px(d["title"]), color=ink), loc.title())
        .tab_style(
            _text(font=serif, weight=400, style="italic", size=px(d["subtitle"]), color=secondary), loc.subtitle()
        )
        # italic labels, de-emphasized
        .tab_style(label, loc.column_labels())
        .pipe(_on_spanners, label)
        .tab_style(
            _text(font=serif, weight=600, style="italic", size=px(d["group"] + 2), color=accent), loc.row_groups()
        )
        .tab_style(
            _text(font=serif, style="italic", size=px(d["source"] + 1), color=secondary),
            [loc.source_notes(), loc.footnotes()],
        )
        .tab_options(
            table_background_color=bg,
            table_font_size=px(d["body"] + 1),
            data_row_padding=px(d["pad"]),
            heading_align="left",
            heading_border_bottom_style="none",
            heading_padding=px(d["pad"]),
            # no top rule
            table_border_top_style="none",
            table_border_bottom_style="none",
            column_labels_border_top_style="none",
            # the one rule, a hairline under the labels
            column_labels_border_bottom_style="solid",
            column_labels_border_bottom_width=px(1),
            column_labels_border_bottom_color=accent,
            column_labels_padding=px(max(d["pad"] - 1, 2)),
            # nothing between the rows, a faint hairline to close the body
            table_body_border_top_style="none",
            table_body_hlines_style="none",
            table_body_border_bottom_style="solid",
            table_body_border_bottom_width=px(1),
            table_body_border_bottom_color=hair,
            column_labels_vlines_style="none",
            table_body_vlines_style="none",
            stub_border_style="none",
            # row groups get a label, no band and no rule
            row_group_border_top_style="none",
            row_group_border_bottom_style="none",
            row_group_padding=px(max(d["pad"] - 1, 2)),
            source_notes_border_lr_style="none",
            source_notes_border_bottom_style="none",
            source_notes_padding=px(d["pad"]),
        )
        .opt_css("\n".join([_tabular_nums(tid), _css(tid, ".gt_sourcenote", f"padding-top: {d['pad'] + 4}px;")]))
    )
    return gt.tab_options(**options)


def gt_theme_brutalist(gt: GT, accent: str = "#FF3B00", density: str = "comfortable", **options: Any) -> GT:
    """Brutalist theme: heavy black frame, a knocked-out black label bar and one loud accent.

    Args:
        gt: The great_tables ``GT`` to theme.
        accent: The single accent color, on the row-group labels (hex).
        density: The type and padding scale: "comfortable", "compact" or "social".
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``accent`` is not hex, or ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_brutalist(GT(df), accent="#0047FF")

    See Also:
        Ported from sdvplotR ``gt_theme_brutalist()``:
        https://sdvplotR.sportsdataverse.org/reference/gt_theme_brutalist.html
    """
    d = _density(density)
    accent = _color(accent, "accent")
    ink = "#000000"
    gt, tid = _table_id(_check_gt(gt))
    gt = (
        _table_font(gt, _font("Archivo"), weight=500)
        .tab_style(_text(color=ink, size=px(d["body"]), weight=500), loc.body())
        .tab_style(
            _text(font=_font("Archivo Black"), size=px(d["title"] + 6), color=ink, transform="uppercase"), loc.title()
        )
        .tab_style(_text(weight=600, size=px(d["subtitle"]), color=ink), loc.subtitle())
        # label row is a solid black bar, knocked out white
        .tab_style(
            _text(weight=700, size=px(d["label"] + 1), color="#FFFFFF", transform="uppercase"), loc.column_labels()
        )
        .pipe(_on_spanners, _text(weight=700, size=px(d["label"] + 1), color=ink, transform="uppercase"))
        .tab_style(_text(weight=700, size=px(d["group"] + 1), color=accent, transform="uppercase"), loc.row_groups())
        .tab_style(_text(size=px(d["source"]), color=ink, weight=500), [loc.source_notes(), loc.footnotes()])
        .tab_options(
            table_background_color="#FFFFFF",
            column_labels_background_color=ink,
            table_font_size=px(d["body"]),
            data_row_padding=px(d["pad"]),
            table_border_top_style="solid",
            table_border_top_width=px(3),
            table_border_top_color=ink,
            table_border_bottom_style="solid",
            table_border_bottom_width=px(3),
            table_border_bottom_color=ink,
            table_border_left_style="solid",
            table_border_left_width=px(3),
            table_border_left_color=ink,
            table_border_right_style="solid",
            table_border_right_width=px(3),
            table_border_right_color=ink,
            heading_align="left",
            heading_border_bottom_style="solid",
            heading_border_bottom_width=px(3),
            heading_border_bottom_color=ink,
            heading_padding=px(d["pad"] + 2),
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="none",
            column_labels_padding=px(d["pad"]),
            table_body_border_top_style="none",
            table_body_hlines_color=ink,
            table_body_hlines_width=px(1),
            table_body_border_bottom_style="none",
            row_group_border_top_style="solid",
            row_group_border_top_width=px(2),
            row_group_border_top_color=ink,
            row_group_border_bottom_style="none",
            row_group_padding=px(max(d["pad"] - 1, 3)),
            source_notes_border_lr_style="none",
            source_notes_border_bottom_style="none",
            source_notes_padding=px(d["pad"] + 2),
        )
        .opt_css(
            "\n".join(
                [
                    _tabular_nums(tid),
                    _last_row_border(tid, "#FFFFFF"),
                    _css(tid, ".gt_col_heading", "letter-spacing: 0.04em;"),
                    _css(tid, ".gt_group_heading", "letter-spacing: 0.06em;"),
                    _css(
                        tid,
                        ".gt_title",
                        "letter-spacing: -0.02em; line-height: 1.05; "
                        f"padding-bottom: {math.ceil(d['pad'] / 2)}px !important;",
                    ),
                    _css(tid, ".gt_subtitle", f"padding-bottom: {d['pad'] + 2}px !important;"),
                ]
            )
        )
    )
    return gt.tab_options(**options)


def gt_theme_drench(gt: GT, color: str = "#123F5E", density: str = "comfortable", **options: Any) -> GT:
    """Drenched theme: the whole table in one color, with rules, bands and muted text all derived from it.

    The type is black or white, whichever reads better on ``color``; the muted text blends the type into the ground
    until it clears 4.5:1 contrast; the rules and the row-group band shift the ground's luminance.

    Args:
        gt: The great_tables ``GT`` to theme.
        color: The hex color the table is drenched in, from near-black to a mid-saturation brand color.
        density: The type and padding scale: "comfortable", "compact" or "social".
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``color`` is not hex, or ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_drench(GT(df), color="#E31837")

    See Also:
        Ported from sdvplotR ``gt_theme_drench()``: https://sdvplotR.sportsdataverse.org/reference/gt_theme_drench.html
    """
    d = _density(density)
    color = _color(color, "color")
    # everything derives from the ground so any hue holds together
    ink = on_color(color)
    dark_type = ink == "#000000"
    # shift the ground rather than laying gray over it
    rule = _adjust_luminance(color, -0.6 if dark_type else 0.9)
    surface = _adjust_luminance(color, 0.5 if dark_type else -0.7)
    # a fixed luminance step fails on some hues, so blend until it clears 4.5:1
    secondary = _secondary_on(color, ink, 4.5)
    gt, tid = _table_id(_check_gt(gt))
    label = _text(weight=700, size=px(d["label"]), color=secondary, transform="uppercase")
    gt = (
        _table_font(gt, _font("Gabarito"))
        .tab_style(_text(color=ink, size=px(d["body"]), weight=500), loc.body())
        .tab_style(_text(weight=700, size=px(d["title"] + 2), color=ink), loc.title())
        .tab_style(_text(weight=400, size=px(d["subtitle"]), color=secondary), loc.subtitle())
        .tab_style(label, loc.column_labels())
        .pipe(_on_spanners, label)
        .tab_style(
            [_text(weight=700, size=px(d["group"]), color=ink, transform="uppercase"), style.fill(color=surface)],
            loc.row_groups(),
        )
        .tab_style(_text(size=px(d["source"]), color=secondary), [loc.source_notes(), loc.footnotes()])
        .tab_options(
            table_background_color=color,
            heading_background_color=color,
            column_labels_background_color=color,
            row_group_background_color=color,
            stub_background_color=color,
            source_notes_background_color=color,
            table_font_size=px(d["body"]),
            data_row_padding=px(d["pad"] + 1),
            table_border_top_style="none",
            table_border_bottom_style="none",
            heading_align="left",
            heading_border_bottom_style="none",
            heading_padding=px(d["pad"] + 2),
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="solid",
            column_labels_border_bottom_width=px(1),
            column_labels_border_bottom_color=rule,
            column_labels_padding=px(d["pad"] + 1),
            table_body_border_top_style="none",
            table_body_hlines_color=rule,
            table_body_hlines_width=px(1),
            table_body_border_bottom_style="none",
            row_group_border_top_style="none",
            row_group_border_bottom_style="none",
            row_group_padding=px(max(d["pad"] - 1, 3)),
            source_notes_border_lr_style="none",
            source_notes_border_bottom_style="none",
            source_notes_padding=px(d["pad"] + 2),
        )
        .opt_css(
            "\n".join(
                [
                    _tabular_nums(tid),
                    _last_row_border(tid, color),
                    # light type on a saturated ground reads lighter than it is
                    *([] if dark_type else [_css(tid, ["td", "th"], "line-height: 1.55;")]),
                    _css(tid, [".gt_col_heading", ".gt_column_spanner"], "letter-spacing: 0.08em;"),
                    _css(tid, ".gt_group_heading", "letter-spacing: 0.06em;"),
                    _css(tid, ".gt_subtitle", f"padding-bottom: {d['pad'] + 8}px !important;"),
                    _css(tid, ".gt_title", f"padding-bottom: {math.ceil(d['pad'] / 2)}px !important;"),
                ]
            )
        )
    )
    return gt.tab_options(**options)


def gt_theme_midnight(gt: GT, accent: str = "#5B8DEF", density: str = "comfortable", **options: Any) -> GT:
    """Dark theme: light type on a near-black ground, a raised label band and one cool accent.

    Args:
        gt: The great_tables ``GT`` to theme.
        accent: Hex color of the row-group labels and the rule above the table.
        density: The type and padding scale: "comfortable", "compact" or "social".
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``accent`` is not hex, or ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_midnight(GT(df), accent="#3FBF87")

    See Also:
        Ported from sdvplotR ``gt_theme_midnight()``:
        https://sdvplotR.sportsdataverse.org/reference/gt_theme_midnight.html
    """
    d = _density(density)
    accent = _color(accent, "accent")
    ground, surface, primary, secondary, rule = "#0C0D10", "#16181D", "#E8E9ED", "#9498A3", "#24272E"
    gt, tid = _table_id(_check_gt(gt))
    # sentence case; uppercase tracking is too loud on this ground
    label = _text(weight=600, size=px(d["label"] + 1), color=secondary)
    gt = (
        _table_font(gt, _font("Chivo"))
        .tab_style(_text(color=primary, size=px(d["body"])), loc.body())
        .tab_style(_text(weight=700, size=px(d["title"]), color=primary), loc.title())
        .tab_style(_text(weight=400, size=px(d["subtitle"]), color=secondary), loc.subtitle())
        .tab_style(label, loc.column_labels())
        .pipe(_on_spanners, label)
        .tab_style(_text(weight=700, size=px(d["group"]), color=accent), loc.row_groups())
        .tab_style(_text(size=px(d["source"]), color=secondary), [loc.source_notes(), loc.footnotes()])
        .tab_options(
            table_background_color=ground,
            heading_background_color=ground,
            column_labels_background_color=surface,
            row_group_background_color=ground,
            stub_background_color=ground,
            source_notes_background_color=ground,
            table_font_size=px(d["body"]),
            data_row_padding=px(d["pad"]),
            table_border_top_style="solid",
            table_border_top_width=px(2),
            table_border_top_color=accent,
            table_border_bottom_style="none",
            heading_align="left",
            heading_border_bottom_style="none",
            heading_padding=px(d["pad"]),
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="solid",
            column_labels_border_bottom_width=px(1),
            column_labels_border_bottom_color=rule,
            column_labels_padding=px(max(d["pad"] - 1, 3)),
            table_body_border_top_style="none",
            table_body_hlines_color=rule,
            table_body_hlines_width=px(1),
            table_body_border_bottom_style="solid",
            table_body_border_bottom_width=px(1),
            table_body_border_bottom_color=rule,
            row_group_border_top_style="solid",
            row_group_border_top_width=px(1),
            row_group_border_top_color=rule,
            row_group_border_bottom_style="none",
            row_group_padding=px(max(d["pad"] - 2, 2)),
            source_notes_border_lr_style="none",
            source_notes_border_bottom_style="none",
            source_notes_padding=px(d["pad"]),
        )
        .opt_css(
            "\n".join(
                [
                    _tabular_nums(tid),
                    _last_row_border(tid, ground),
                    # light on dark reads lighter than it is, so open the leading
                    _css(tid, ["td", "th"], "line-height: 1.55;"),
                    _css(tid, ".gt_subtitle", f"padding-bottom: {d['pad'] + 8}px !important;"),
                    _css(tid, ".gt_title", f"padding-bottom: {math.ceil(d['pad'] / 2)}px !important;"),
                ]
            )
        )
    )
    return gt.tab_options(**options)


# sdvplotR's pal_midnight: a rank palette for dark backgrounds, five colors running best (green) to worst (red), its
# luminance lifted so every step clears 4.5:1 on gt_theme_midnight's #0C0D10 ground (and gt_theme_terminal's). The
# usual green-to-red ramp is built for white paper; its mid-tones sink into a near-black ground.
pal_midnight: tuple[str, ...] = ("#3FBF87", "#8FD9A8", "#D8D6A0", "#E8996B", "#E0645C")


def gt_theme_scoreboard(gt: GT, accent: str = "#0E1621", density: str = "compact", **options: Any) -> GT:
    """Scoreboard theme: condensed uppercase type under a solid header band, like a broadcast stat panel.

    Args:
        gt: The great_tables ``GT`` to theme.
        accent: Hex color of the header band; the label color (black or white) adapts to it.
        density: The type and padding scale: "comfortable", "compact" or "social".
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``accent`` is not hex, or ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_scoreboard(GT(df), accent="#FFC20E")

    See Also:
        Ported from sdvplotR ``gt_theme_scoreboard()``:
        https://sdvplotR.sportsdataverse.org/reference/gt_theme_scoreboard.html
    """
    d = _density(density)
    accent = _color(accent, "accent")
    ink, rule, muted = "#141719", "#E6E9ED", "#5A6069"
    # a pale accent needs dark labels, so measure it
    on_accent = on_color(accent)
    gt, tid = _table_id(_check_gt(gt))
    condensed = _font("Barlow Condensed")
    label = _text(font=condensed, weight=700, size=px(d["label"] + 2), color=on_accent, transform="uppercase")
    gt = (
        _table_font(gt, _font("Barlow"))
        .tab_style(_text(color=ink, size=px(d["body"]), weight=500), loc.body())
        .tab_style(
            _text(font=condensed, weight=700, size=px(d["title"] + 4), color=ink, transform="uppercase"), loc.title()
        )
        .tab_style(_text(font=condensed, weight=500, size=px(d["subtitle"] + 1), color=muted), loc.subtitle())
        .tab_style(label, loc.column_labels())
        .pipe(_on_spanners, label)
        .tab_style(
            [
                _text(font=condensed, weight=700, size=px(d["group"] + 1), color=accent, transform="uppercase"),
                style.fill(color="#F2F4F6"),
            ],
            loc.row_groups(),
        )
        .tab_style(_text(size=px(d["source"]), color=muted), [loc.source_notes(), loc.footnotes()])
        .tab_options(
            table_background_color="#FFFFFF",
            column_labels_background_color=accent,
            table_font_size=px(d["body"]),
            data_row_padding=px(d["pad"]),
            table_border_top_style="none",
            table_border_bottom_style="none",
            heading_align="left",
            heading_border_bottom_style="none",
            heading_padding=px(d["pad"] + 1),
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="none",
            column_labels_padding=px(d["pad"] + 2),
            table_body_border_top_style="none",
            table_body_hlines_color=rule,
            table_body_hlines_width=px(1),
            table_body_border_bottom_style="solid",
            table_body_border_bottom_width=px(2),
            table_body_border_bottom_color=accent,
            row_group_border_top_style="none",
            row_group_border_bottom_style="none",
            row_group_padding=px(max(d["pad"], 3)),
            source_notes_border_lr_style="none",
            source_notes_border_bottom_style="none",
            source_notes_padding=px(d["pad"] + 2),
        )
        .opt_css(
            "\n".join(
                [
                    _tabular_nums(tid),
                    _last_row_border(tid, "#FFFFFF"),
                    _css(tid, [".gt_col_heading", ".gt_column_spanner"], "letter-spacing: 0.06em;"),
                    _css(tid, ".gt_group_heading", "letter-spacing: 0.06em;"),
                    _css(tid, ".gt_heading", "letter-spacing: 0.01em;"),
                    _css(tid, ".gt_subtitle", f"padding-bottom: {d['pad'] + 6}px !important;"),
                ]
            )
        )
    )
    return gt.tab_options(**options)


def gt_theme_terminal(gt: GT, accent: str = "#FFB86C", density: str = "compact", **options: Any) -> GT:
    """Terminal theme: a monospaced readout on a near-black ground, with a rule on every row.

    Args:
        gt: The great_tables ``GT`` to theme.
        accent: Hex color of the column labels, row groups and the top rule. The default is amber; "#7EE787" gives a
            green-phosphor variant.
        density: The type and padding scale: "comfortable", "compact" or "social".
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``accent`` is not hex, or ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_terminal(GT(df), accent="#7EE787")

    See Also:
        Ported from sdvplotR ``gt_theme_terminal()``:
        https://sdvplotR.sportsdataverse.org/reference/gt_theme_terminal.html
    """
    d = _density(density)
    accent = _color(accent, "accent")
    ground, primary, secondary, rule = "#0F1115", "#C9D1D9", "#7D8590", "#262B33"
    gt, tid = _table_id(_check_gt(gt))
    label = _text(weight=700, size=px(d["label"]), color=accent, transform="uppercase")
    gt = (
        _table_font(gt, _font("JetBrains Mono"))
        .tab_style(_text(color=primary, size=px(d["body"])), loc.body())
        .tab_style(_text(weight=700, size=px(d["title"] - 2), color=primary, transform="uppercase"), loc.title())
        .tab_style(_text(weight=400, size=px(d["subtitle"] - 1), color=secondary), loc.subtitle())
        .tab_style(label, loc.column_labels())
        .pipe(_on_spanners, label)
        .tab_style(_text(weight=700, size=px(d["group"]), color=accent, transform="uppercase"), loc.row_groups())
        .tab_style(_text(size=px(d["source"]), color=secondary), [loc.source_notes(), loc.footnotes()])
        .tab_options(
            table_background_color=ground,
            heading_background_color=ground,
            column_labels_background_color=ground,
            row_group_background_color=ground,
            stub_background_color=ground,
            source_notes_background_color=ground,
            table_font_size=px(d["body"]),
            data_row_padding=px(d["pad"]),
            table_border_top_style="solid",
            table_border_top_width=px(1),
            table_border_top_color=accent,
            table_border_bottom_style="solid",
            table_border_bottom_width=px(1),
            table_border_bottom_color=rule,
            heading_align="left",
            heading_border_bottom_style="none",
            heading_padding=px(d["pad"] + 2),
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="solid",
            column_labels_border_bottom_width=px(1),
            column_labels_border_bottom_color=accent,
            column_labels_padding=px(d["pad"] + 1),
            # rule on every row, it's a readout
            table_body_border_top_style="none",
            table_body_hlines_color=rule,
            table_body_hlines_width=px(1),
            table_body_border_bottom_style="none",
            row_group_border_top_style="solid",
            row_group_border_top_width=px(1),
            row_group_border_top_color=rule,
            row_group_border_bottom_style="none",
            row_group_padding=px(max(d["pad"], 3)),
            source_notes_border_lr_style="none",
            source_notes_border_bottom_style="none",
            source_notes_padding=px(d["pad"] + 2),
        )
        .opt_css(
            "\n".join(
                [
                    _tabular_nums(tid),
                    _last_row_border(tid, ground),
                    _css(tid, ["td", "th"], "line-height: 1.5;"),
                    _css(tid, ".gt_col_heading", "letter-spacing: 0.08em;"),
                    _css(tid, ".gt_title", "letter-spacing: 0.04em; padding-bottom: 2px !important;"),
                    _css(tid, ".gt_subtitle", f"padding-bottom: {d['pad'] + 6}px !important;"),
                ]
            )
        )
    )
    return gt.tab_options(**options)


def gt_theme_athletic(gt: GT, density: str = "comfortable", **options: Any) -> GT:
    """The Athletic's table look: a monospaced body, uppercase sans labels, dotted row rules and thin column rules.

    The row-group band is solid black with knocked-out white labels, and every column is centered. The theme sets its
    sizes directly, so ``density`` rescales the finished table (as sdvplotR does).

    Args:
        gt: The great_tables ``GT`` to theme.
        density: The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and
            "social" up.
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_athletic(GT(df), density="compact")

    See Also:
        Ported from sdvplotR ``gt_theme_athletic()``:
        https://sdvplotR.sportsdataverse.org/reference/gt_theme_athletic.html
    """
    _density(density)
    gt, tid = _table_id(_check_gt(gt))
    columns = _shape(gt)[0]
    work = _font("Work Sans")
    table = (
        _table_font(gt, _font("Spline Sans Mono"), weight=500)
        .tab_style(_text(font=work, weight=650, size=px(12), transform="uppercase"), loc.column_labels())
        .tab_style(_text(font=work, weight=650, size=px(22)), loc.title())
        .tab_style(_text(font=work, weight=500, size=px(14)), loc.subtitle())
        .tab_style([_text(weight=650, size=px(12), color="white"), style.fill(color="black")], loc.row_groups())
        # column rules: a left border on every column but the first, so the stub reads without a leading rule
        .tab_style(style.borders(sides="left", weight=px(0.5), color="black"), loc.body(columns=columns[1:]))
        .tab_style(style.borders(sides="top", color="black", weight=px(1.5), style="dotted"), loc.body())
        .cols_align("center")
        .tab_options(
            table_font_size=px(12),
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="solid",
            column_labels_border_bottom_width=px(1),
            column_labels_border_bottom_color="black",
            table_border_top_style="none",
            table_border_bottom_style="none",
            table_body_border_top_style="none",
            heading_border_bottom_style="none",
            heading_align="left",
            heading_title_font_size=px(26),
            source_notes_border_lr_style="none",
            source_notes_font_size=px(10),
            row_group_border_top_style="none",
            row_group_border_top_color="black",
            row_group_border_bottom_width=px(1),
            row_group_border_bottom_color="black",
            row_group_border_bottom_style="solid",
            row_group_padding=px(1.5),
        )
        .opt_css(
            "\n".join(
                [
                    _last_row_border(tid, "#FFFFFF"),
                    _css(tid, ".gt_subtitle", "padding-top: 0px !important; padding-bottom: 4px !important;"),
                    _css(tid, ".gt_sourcenote", "border-bottom-color: #FFFDF5 !important;"),
                    _css(tid, ".gt_heading", "padding-bottom: 0px; padding-top: 6px;"),
                ]
            )
        )
    )
    return _scale_output(table, density).tab_options(**options)


def gt_theme_gtutils(gt: GT, density: str = "comfortable", **options: Any) -> GT:
    """The gtUtils look: Almarai and Signika Negative on cream, taupe row rules and a taupe row-group band.

    Args:
        gt: The great_tables ``GT`` to theme.
        density: The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and
            "social" up.
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_gtutils(GT(df))

    See Also:
        Ported from sdvplotR ``gt_theme_gtutils()``: https://sdvplotR.sportsdataverse.org/reference/gt_theme_gtutils.html
    """
    _density(density)
    gt, tid = _table_id(_check_gt(gt))
    signika, almarai = _font("Signika Negative"), _font("Almarai")
    table = (
        _table_font(gt, _font("Almarai"), weight=500)
        .tab_style(_text(font=signika, weight=650), loc.title())
        .tab_style(_text(font=signika, weight=500), loc.subtitle())
        .tab_style(_text(font=signika, weight=650, size=px(14)), loc.column_labels())
        .pipe(_on_spanners, _text(font=signika, weight=650, size=px(13)))
        .tab_style(
            [_text(font=signika, weight=650, size=px(14), color="#FFFDF5"), style.fill(color="#8A817C")],
            loc.row_groups(),
        )
        .tab_style(_text(font=almarai, size=px(12)), [loc.source_notes(), loc.footnotes()])
        .pipe(_row_rules, "#8A817C")
        .cols_align("center")
        .tab_options(
            data_row_padding=px(1),
            table_body_hlines_color="transparent",
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="solid",
            column_labels_border_bottom_width=px(1),
            column_labels_border_bottom_color="black",
            row_group_border_top_style="none",
            row_group_border_top_color="black",
            row_group_border_bottom_width=px(1),
            row_group_border_bottom_color="black",
            row_group_border_bottom_style="solid",
            row_group_padding=px(1.5),
            heading_align="left",
            heading_border_bottom_style="none",
            table_body_border_top_style="none",
            table_border_bottom_style="none",
            table_border_top_style="none",
            source_notes_border_lr_style="none",
            table_background_color="#FFFDF5",
            table_border_top_color="#FFFDF5",
            table_border_right_color="#FFFDF5",
            table_border_bottom_color="#FFFDF5",
            table_border_left_color="#FFFDF5",
        )
        .opt_css(
            "\n".join(
                [
                    _last_row_border(tid, "#FFFDF5"),
                    _css(tid, ".gt_col_heading", "padding-bottom: 2px; padding-top: 2px;"),
                    _css(tid, ".gt_subtitle", "padding-top: 0px !important; padding-bottom: 4px !important;"),
                    _css(tid, ".gt_sourcenote", "border-bottom-color: #FFFDF5 !important;"),
                    _css(tid, ".gt_heading", "padding-bottom: 0px; padding-top: 6px;"),
                    _css(tid, ".gt_column_spanner", "padding-bottom: 2px;"),
                ]
            )
        )
    )
    return _scale_output(table, density).tab_options(**options)


def gt_theme_kenpom(gt: GT, density: str = "comfortable", **options: Any) -> GT:
    """KenPom's table look: blue-banded rows, a pale-blue label band with blue labels, black row rules.

    Args:
        gt: The great_tables ``GT`` to theme.
        density: The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and
            "social" up.
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_kenpom(GT(df))

    See Also:
        Ported from sdvplotR ``gt_theme_kenpom()``: https://sdvplotR.sportsdataverse.org/reference/gt_theme_kenpom.html
    """
    _density(density)
    gt, tid = _table_id(_check_gt(gt))
    n = _shape(gt)[1]
    helvetica = _font("Helvetica Neue")
    band = [_text(font=helvetica, weight=650, size=px(14), color="#02b"), style.fill(color="#c3d9ff")]
    table = (
        _table_font(gt, _font("Helvetica Neue"), weight=500)
        # R's odd and even rows (1-based), banded
        .tab_style(style.fill(color="#F2FAFD"), loc.body(rows=list(range(0, n, 2))))
        .tab_style(style.fill(color="#e5ecf9"), loc.body(rows=list(range(1, n, 2))))
        .tab_style(band, loc.column_labels())
        .tab_style(_text(font=helvetica, weight=650, size=px(18), align="left"), loc.title())
        .tab_style(_text(font=helvetica, weight=500, size=px(14), align="left"), loc.subtitle())
        .pipe(_on_spanners, _text(font=helvetica, weight=650, size=px(12)))
        .tab_style(band, loc.row_groups())
        .tab_style(_text(font=helvetica, size=px(12)), loc.source_notes())
        .tab_style(_text(weight="bold", font=helvetica, size=px(14)), loc.row_groups())
        .tab_style(_text(font=helvetica, size=px(12)), loc.footnotes())
        .pipe(_row_rules, "#000000")
        # uh this is kinda hacky but it works
        .pipe(_hide_spanner_row, tid)
        .tab_options(
            data_row_padding=px(2),
            table_body_hlines_color="transparent",
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="none",
            row_group_border_top_style="none",
            row_group_border_top_color="black",
            row_group_border_bottom_width=px(1),
            row_group_border_bottom_color="black",
            row_group_border_bottom_style="solid",
            row_group_padding=px(1.5),
            heading_align="center",
            heading_border_bottom_style="none",
            table_body_border_top_style="none",
            table_body_border_bottom_color="white",
            table_border_bottom_style="none",
            table_border_top_style="none",
            source_notes_border_lr_style="none",
        )
        .opt_css(
            "\n".join(
                [
                    _last_row_border(tid, "#FFFFFF"),
                    _css(tid, ".gt_col_heading", "padding-bottom: 2px; padding-top: 2px;"),
                    _css(tid, ".gt_subtitle", "padding-top: 0px !important; padding-bottom: 4px !important;"),
                    _css(tid, ".gt_heading", "padding-bottom: 0px; padding-top: 6px;"),
                    _css(tid, ".gt_column_spanner", "text-decoration: underline;"),
                ]
            )
        )
    )
    return _scale_output(table, density).tab_options(**options)


def gt_theme_ncaa(gt: GT, density: str = "comfortable", **options: Any) -> GT:
    """NCAA stats-site look: Open Sans, a black label band with white uppercase labels, striped rows, wide left inset.

    Args:
        gt: The great_tables ``GT`` to theme.
        density: The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and
            "social" up.
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_ncaa(GT(df))

    See Also:
        Ported from sdvplotR ``gt_theme_ncaa()``: https://sdvplotR.sportsdataverse.org/reference/gt_theme_ncaa.html
    """
    _density(density)
    gt, tid = _table_id(_check_gt(gt))
    sans, almarai = _font("Open Sans"), _font("Almarai")
    table = (
        gt.tab_style(_text(font=sans, size=px(14)), loc.body())
        .tab_style(
            [
                _text(font=sans, size=px(14), transform="uppercase", color="white", align="left"),
                style.fill(color="#000000"),
            ],
            loc.column_labels(),
        )
        .tab_style(_text(weight="bold", font=sans, size=px(14)), loc.row_groups())
        .tab_style(_text(font=sans, size=px(12)), loc.footnotes())
        .tab_style(_text(weight="bold", font=sans, size=px(18)), loc.title())
        .tab_style(_text(font=sans, size=px(14)), loc.subtitle())
        .tab_style(_text(font=sans, size=px(10)), loc.source_notes())
        .cols_align("left")
        .pipe(_on_spanners, _text(font=sans, weight=650, size=px(13)))
        .tab_style(
            [_text(font=sans, weight=650, size=px(14), color="#ffffff"), style.fill(color="#3C3A40")], loc.row_groups()
        )
        .tab_style(_text(font=almarai, size=px(12)), [loc.source_notes(), loc.footnotes()])
        .pipe(_hide_spanner_row, tid)
        .tab_options(
            data_row_padding=px(2),
            table_body_hlines_color="transparent",
            column_labels_border_top_color="black",
            column_labels_border_top_width=px(1),
            column_labels_border_bottom_style="none",
            row_group_border_top_style="none",
            row_group_border_top_color="black",
            row_group_border_bottom_width=px(1),
            row_group_border_bottom_color="black",
            row_group_border_bottom_style="solid",
            row_group_padding=px(1.5),
            heading_align="left",
            heading_border_bottom_style="none",
            table_body_border_top_style="none",
            table_body_border_bottom_color="white",
            table_border_bottom_style="none",
            table_border_top_style="none",
            source_notes_border_lr_style="none",
        )
        .opt_row_striping()
        .opt_css(
            "\n".join(
                [
                    _last_row_border(tid, "#FFFFFF"),
                    _css(tid, ".gt_col_heading", "padding: 5px 5px 5px 25px;"),
                    _css(tid, ".gt_row", "padding: 5px 5px 5px 25px;"),
                    _css(tid, ".gt_subtitle", "padding-top: 0px !important; padding-bottom: 4px !important;"),
                    _css(tid, ".gt_heading", "padding-bottom: 0px; padding-top: 6px;"),
                    _css(tid, ".gt_column_spanner", "text-decoration: underline;"),
                ]
            )
        )
    )
    return _scale_output(table, density).tab_options(**options)


def gt_theme_pl(gt: GT, density: str = "comfortable", **options: Any) -> GT:
    """Premier League look: DM Sans in the league's deep purple, purple rules, a lilac row-group band.

    Args:
        gt: The great_tables ``GT`` to theme.
        density: The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and
            "social" up.
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_pl(GT(df))

    See Also:
        Ported from sdvplotR ``gt_theme_pl()``: https://sdvplotR.sportsdataverse.org/reference/gt_theme_pl.html
    """
    _density(density)
    gt, tid = _table_id(_check_gt(gt))
    n = _shape(gt)[1]
    dm = _font("DM Sans")
    purple = "#37003c"
    table = (
        gt.tab_style(_text(font=dm, color=purple, size=px(14)), loc.body())
        .tab_style(_text(font=dm, color="#87668a", weight=650, size=px(13)), loc.column_labels())
        .tab_style(_text(font=dm, weight=650), loc.title())
        .tab_style(_text(font=dm, weight=500), loc.subtitle())
        .pipe(_on_spanners, _text(font=dm, weight=650, size=px(12), color=purple))
        .tab_style(
            [_text(font=dm, weight=650, size=px(12), color="#ffffff"), style.fill(color="#C0BACA")], loc.row_groups()
        )
        .tab_style(_text(font=dm, size=px(12)), [loc.footnotes(), loc.source_notes()])
        .pipe(_row_rules, purple)
    )
    if n:
        table = table.tab_style(style.borders(sides="top", color=purple), loc.body(rows=[0]))
    table = table.tab_options(
        heading_align="left",
        column_labels_border_top_style="none",
        table_border_top_style="none",
        table_body_border_top_style="solid",
        table_body_border_top_width=px(1),
        table_body_border_top_color=purple,
        table_body_border_bottom_color="white",
        heading_border_bottom_style="none",
        data_row_padding=px(2),
        row_group_padding=px(1.5),
        row_group_border_top_style="none",
        row_group_border_bottom_width=px(1),
        row_group_border_bottom_color=purple,
        row_group_border_bottom_style="solid",
        table_border_bottom_style="none",
        source_notes_border_lr_style="none",
        column_labels_border_bottom_style="solid",
        column_labels_border_bottom_width=px(1),
        column_labels_border_bottom_color=purple,
    ).opt_css(
        "\n".join(
            [
                _last_row_border(tid, "#FFFFFF"),
                _css(tid, ".gt_col_heading", "padding-bottom: 3px;"),
                _css(tid, ".gt_heading", "padding-bottom: 0px; padding-top: 6px;"),
                _css(tid, ".gt_subtitle", "padding-top: 2px; padding-bottom: 6px;"),
                _css(tid, ".gt_column_spanner", "font-size: 13px; font-weight: bold; padding-bottom: 2px;"),
                _css(tid, ".gt_sourcenote", "line-height: 1.2;"),
            ]
        )
    )
    return _scale_output(table, density).tab_options(**options)


def gt_theme_savant(gt: GT, density: str = "comfortable", **options: Any) -> GT:
    """Baseball Savant's table look: Roboto Condensed, striped rows, a black row-group band, a centered heading.

    Args:
        gt: The great_tables ``GT`` to theme.
        density: The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and
            "social" up.
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_savant(GT(df))

    See Also:
        Ported from sdvplotR ``gt_theme_savant()``: https://sdvplotR.sportsdataverse.org/reference/gt_theme_savant.html
    """
    _density(density)
    gt, tid = _table_id(_check_gt(gt))
    roboto = _font("Roboto Condensed")
    table = (
        gt.tab_style(_text(font=roboto, size=px(14)), loc.body())
        .tab_style(_text(weight="bold", font=roboto, size=px(14)), loc.column_labels())
        .tab_style(
            [_text(font=roboto, weight=650, size=px(14), color="#FFFDF5"), style.fill(color="#000000")],
            loc.row_groups(),
        )
        .tab_style(_text(font=roboto, size=px(12)), [loc.footnotes(), loc.source_notes()])
        .tab_style(_text(weight="bold", font=roboto, size=px(18)), loc.title())
        .tab_style(_text(font=roboto, size=px(14)), loc.subtitle())
        .pipe(_on_spanners, _text(font=roboto, weight=650, size=px(8)))
        .tab_options(
            data_row_padding=px(1),
            table_body_hlines_color="transparent",
            column_labels_border_top_color="black",
            column_labels_border_top_width=px(1),
            column_labels_border_bottom_style="none",
            row_group_border_top_style="none",
            row_group_border_top_color="black",
            row_group_border_bottom_width=px(1),
            row_group_border_bottom_color="black",
            row_group_border_bottom_style="solid",
            row_group_padding=px(1.5),
            heading_align="center",
            heading_border_bottom_style="none",
            table_body_border_top_style="none",
            table_body_border_bottom_color="white",
            table_border_bottom_style="none",
            table_border_top_style="none",
            source_notes_border_lr_style="none",
        )
        .opt_row_striping()
        .opt_css(
            "\n".join(
                [
                    _last_row_border(tid, "#FFFFFF"),
                    _css(tid, ".gt_col_heading", "padding-bottom: 2px; padding-top: 2px;"),
                    _css(tid, ".gt_subtitle", "padding-top: 0px !important; padding-bottom: 4px !important;"),
                    _css(tid, ".gt_heading", "padding-bottom: 0px; padding-top: 6px;"),
                    _css(tid, ".gt_column_spanner", "font-size: 12px; font-weight: bold; text-decoration: underline;"),
                ]
            )
        )
    )
    return _scale_output(table, density).tab_options(**options)


def gt_theme_sofa(gt: GT, style: str = "light", density: str = "comfortable", **options: Any) -> GT:
    """SofaScore's table look: Sofia Sans Condensed on a warm cream (or dark navy) ground, no rules between rows.

    Args:
        gt: The great_tables ``GT`` to theme.
        style: "light" for the cream ground or "dark" for the navy one; on navy great_tables switches the text to
            white.
        density: The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and
            "social" up.
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``style`` is not "light" or "dark", or ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_sofa(GT(df), style="dark")

    See Also:
        Ported from sdvplotR ``gt_theme_sofa()``: https://sdvplotR.sportsdataverse.org/reference/gt_theme_sofa.html
    """
    _density(density)
    if style not in ("light", "dark"):
        raise ValueError(f"style must be 'light' or 'dark', not {style!r}")
    base = "#F0EAD6" if style == "light" else "#1c2632"
    gt, tid = _table_id(_check_gt(gt))
    sofia = _font("Sofia Sans Condensed")
    table = (
        gt.tab_style(_text(font=sofia, size=px(14)), loc.body())
        .tab_style(_text(weight="bold", font=sofia, size=px(14)), [loc.column_labels(), loc.row_groups()])
        .tab_style(_text(font=sofia, size=px(12)), loc.footnotes())
        .tab_style(_text(weight="bold", font=sofia, size=px(22)), loc.title())
        .tab_style(_text(font=sofia, size=px(14)), loc.subtitle())
        .pipe(_on_spanners, _text(font=sofia, weight=650, size=px(12)))
        .tab_style(_text(font=sofia, size=px(10)), loc.source_notes())
        .tab_options(
            data_row_padding=px(1),
            table_body_hlines_color="transparent",
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="none",
            row_group_border_top_style="none",
            row_group_border_top_color="black",
            row_group_border_bottom_width=px(1),
            row_group_border_bottom_color="black",
            row_group_border_bottom_style="solid",
            row_group_padding=px(1.5),
            heading_align="left",
            heading_border_bottom_style="none",
            table_body_border_top_style="none",
            table_border_bottom_style="none",
            table_border_top_style="none",
            source_notes_border_lr_style="none",
            table_background_color=base,
            table_border_top_color=base,
            table_border_right_color=base,
            table_border_bottom_color=base,
            table_border_left_color=base,
        )
        .opt_css(
            "\n".join(
                [
                    _last_row_border(tid, base),
                    _css(tid, ".gt_col_heading", "padding-bottom: 2px; padding-top: 2px;"),
                    _css(tid, ".gt_subtitle", "padding-top: 0px !important; padding-bottom: 4px !important;"),
                    _css(tid, ".gt_sourcenote", f"border-bottom-color: {base} !important;"),
                    _css(tid, ".gt_heading", "padding-bottom: 0px; padding-top: 6px;"),
                    _css(tid, ".gt_column_spanner", "font-size: 12px; font-weight: bold; text-decoration: underline;"),
                ]
            )
        )
    )
    return _scale_output(table, density).tab_options(**options)


def gt_theme_tier(gt: GT, style: str = "dark", density: str = "comfortable", **options: Any) -> GT:
    """Tier-list look: Oswald on a near-black (or white) ground, centered columns, a rule under every row.

    Args:
        gt: The great_tables ``GT`` to theme.
        style: "dark" for the near-black ground (great_tables switches the text to white) or "light" for white.
        density: The type and padding scale: "comfortable" keeps the theme's sizes, "compact" scales them down and
            "social" up.
        **options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        ValueError: ``style`` is not "light" or "dark", or ``density`` is not one of the three scales.

    Example:
        ::

            gt_theme_tier(GT(df), style="light")

    See Also:
        Ported from sdvplotR ``gt_theme_tier()``: https://sdvplotR.sportsdataverse.org/reference/gt_theme_tier.html
    """
    _density(density)
    if style not in ("light", "dark"):
        raise ValueError(f"style must be 'light' or 'dark', not {style!r}")
    base = "#1a1a17" if style == "dark" else "#ffffff"
    gt, tid = _table_id(_check_gt(gt))
    oswald = _font("Oswald")
    table = (
        _table_font(gt, _font("Oswald"), weight=500)
        .tab_style(_text(font=oswald, weight=650), loc.title())
        .tab_style(_text(font=oswald, weight=500), loc.subtitle())
        .pipe(_row_rules, "black")
        .cols_align("center")
        .tab_options(
            data_row_padding=px(1),
            table_body_hlines_color="transparent",
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="none",
            row_group_border_top_style="none",
            row_group_border_top_color="black",
            row_group_border_bottom_width=px(1),
            row_group_border_bottom_color="black",
            row_group_border_bottom_style="solid",
            row_group_padding=px(1.5),
            heading_align="left",
            heading_border_bottom_style="none",
            table_body_border_top_style="none",
            table_border_bottom_style="none",
            table_border_top_style="none",
            source_notes_border_lr_style="none",
            table_background_color=base,
            table_border_top_color=base,
            table_border_right_color=base,
            table_border_bottom_color=base,
            table_border_left_color=base,
        )
        .opt_css(
            "\n".join(
                [
                    _last_row_border(tid, base),
                    _css(tid, ".gt_col_heading", "padding-bottom: 2px; padding-top: 2px;"),
                    _css(tid, ".gt_subtitle", "padding-top: 0px !important; padding-bottom: 4px !important;"),
                    _css(tid, ".gt_sourcenote", f"border-bottom-color: {base} !important;"),
                    _css(tid, ".gt_heading", "padding-bottom: 0px; padding-top: 6px;"),
                ]
            )
        )
    )
    return _scale_output(table, density).tab_options(**options)


def gt_theme_preview(
    data: Any, themes: str | list[str] | None = None, *, n: int = 5, density: str | None = "compact"
) -> dict[str, GT]:
    """The same few rows in every table theme, one ``GT`` per theme, to compare them side by side.

    Each theme is called at its defaults, except ``density``. ``gt_theme_sdv_team`` is shown with ``league="nfl"``
    and no team, i.e. the SportsDataverse colors, as R shows it.

    Args:
        data: A pandas or polars DataFrame, or a ``GT`` (its data is used).
        themes: Theme function names (e.g. "gt_theme_kenpom"); None shows every ``gt_theme_*`` in
            ``sdvplot.great_tables``, sorted.
        n: How many rows of ``data`` each table shows: a positive whole number (numpy integers count).
        density: The density passed to every theme that takes one, so the tables compare; None leaves each theme at
            its own default.

    Returns:
        dict[str, GT]: ``{theme name: themed GT}``, in the order of ``themes``.

    Raises:
        TypeError: ``data`` is not a DataFrame or a ``GT``.
        ValueError: ``data`` has no rows, a name in ``themes`` is not a theme, ``n`` is not a positive whole number,
            or ``density`` is not a scale.

    Example:
        ::

            from sdvplot.great_tables import gt_theme_preview

            tables = gt_theme_preview(df, themes=["gt_theme_kenpom", "gt_theme_athletic"])
            tables["gt_theme_kenpom"]

    See Also:
        Ported from sdvplotR ``gt_theme_preview()``, which lays the tables out with ``gt_grid()``:
        https://sdvplotR.sportsdataverse.org/reference/gt_theme_preview.html
    """
    import sdvplot.great_tables as sgt  # the package imports this module, so import it at call time

    if isinstance(data, GT):
        data = data._tbl_data
    try:
        frame = nw.from_native(data, eager_only=True)
    except TypeError:
        raise TypeError(f"data must be a pandas or polars DataFrame or a GT, not {type(data).__name__}") from None
    if len(frame) == 0:
        raise ValueError("data has no rows")
    if isinstance(n, bool) or not isinstance(n, numbers.Integral) or n < 1:
        raise ValueError(f"n must be a positive whole number of rows, got {n!r}")
    if density is not None:
        _density(density)
    available = sorted(name for name in sgt.__all__ if name.startswith("gt_theme_") and name != "gt_theme_preview")
    names = available if themes is None else [themes] if isinstance(themes, str) else list(themes)
    missing = [name for name in names if name not in available]
    if missing:
        raise ValueError(f"No such theme: {', '.join(missing)}. Themes: {', '.join(available)}")
    rows = frame.head(int(n)).to_native()
    out = {}
    for name in names:
        fn = getattr(sgt, name)
        params = inspect.signature(fn).parameters
        kwargs: dict[str, Any] = {}
        if density is not None and "density" in params:
            kwargs["density"] = density
        if "league" in params and params["league"].default is inspect.Parameter.empty:
            kwargs["league"] = "nfl"
        out[name] = fn(GT(rows), **kwargs)
    return out

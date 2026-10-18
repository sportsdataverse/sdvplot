"""``gt_theme_source``: any surveyed registry theme (``sdv_table_themes()``) as a great_tables theme.

Built like the house themes in ``_themes.py`` (``tab_style`` for type, ``tab_options`` for ground and padding,
``opt_css`` for the borders, stripes and tracking great_tables has no option for), from the resolved
``table_theme_spec``. The spec's sizes are the ``"comfortable"`` baseline; other densities rescale them by the
house density ratios.
"""

from __future__ import annotations

from typing import Any

from great_tables import GT, loc, px

from sdvplot._table_themes import _font_stack, table_theme_spec
from sdvplot.great_tables._marks import DENSITY, R_FONTS, _check_gt, _density, _table_font, _table_id
from sdvplot.great_tables._themes import _css, _Font, _on_spanners, _tabular_nums, _text

__all__ = ["gt_theme_source"]


class _Face(_Font):
    """A Google face written into CSS with its generic fallback (``"Lora", serif``), so a face that fails to load
    degrades to the right kind of font."""

    def get_font_name(self) -> str:
        return _font_stack(self.font)


def _font(family: str) -> _Face:
    return _Face(family)


def _quote(name: str) -> str:
    return f'"{name}"' if " " in name else name


def _tr(size: float, k: float) -> float:
    return round(size * k, 1)


def gt_theme_source(gt: GT, name: str, mode: str = "light", density: str = "comfortable") -> GT:
    """Style a table like one of the 122 surveyed sources (``"datagolf"``, ``"wikipedia"``, ``"economist"``, ...).

    Fonts, ground, text and rule colors, row rules, column rules, striping, label case and tracking, and padding
    come from the theme's spec (``table_theme_spec(name, mode)``); ``density`` rescales its sizes.

    Args:
        gt: The great_tables ``GT`` to theme.
        name: A registry theme id, as listed by ``sdv_table_themes()``.
        mode: ``"light"`` or ``"dark"``; ``"dark"`` raises for a light-only theme.
        density: The type and padding scale: "comfortable" (the spec's own sizes), "compact" or "social".

    Returns:
        GT: A new ``GT`` with the theme applied.

    Raises:
        TypeError: ``gt`` is not a great_tables ``GT``.
        InputError: (a ValueError) ``name`` is unknown, or ``mode`` is invalid or unavailable for the theme.
        ValueError: ``density`` is not one of the three scales.

    Example:
        ::

            from great_tables import GT
            import polars as pl
            from sdvplot.great_tables import gt_theme_source

            df = pl.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [12, 10, 9]})

            gt_theme_source(GT(df), "datagolf", mode="dark")

    See Also:
        sdvplot.table_theme_spec: the resolved fonts, palette and structure ;
        sdvplot.sdv_table_themes: the available ids
    """
    gt = _check_gt(gt)
    sp = table_theme_spec(name, mode)  # type: ignore[arg-type]  # a bad mode raises there
    d, base = _density(density), DENSITY["comfortable"]
    k = {role: d[role] / base[role] for role in d}
    pal, fonts, sizes, st = sp.palette, sp.fonts, sp.sizes, sp.structure
    pad_y, pad_x = _tr(sizes["padY"], k["pad"]), _tr(sizes["padX"], k["pad"])
    gt, tid = _table_id(gt)

    def type_(role: str, family: str, weight: Any, color: str, **extra: Any) -> Any:
        return _text(font=_font(family), weight=weight, size=px(_tr(sizes[role], k[role])), color=color, **extra)

    def case(transform: str) -> dict[str, Any]:
        return {"transform": transform} if transform in ("uppercase", "lowercase", "capitalize") else {}

    label = type_("label", fonts["label"], fonts["labelWeight"], pal["labelColor"], **case(st["labelTransform"]))
    gt = (
        _table_font(gt, _Font(fonts["body"]))  # plain: great_tables quotes a table font as one name
        .tab_style(type_("body", fonts["body"], fonts["bodyWeight"], pal["text"]), loc.body())
        .tab_style(
            type_("title", fonts["title"], fonts["titleWeight"], pal["text"], **case(st["titleTransform"])),
            loc.title(),
        )
        .tab_style(
            type_(
                "subtitle",
                fonts["subtitle"],
                400,
                pal["muted"],
                **({"style": "italic"} if fonts.get("subtitleItalic") else {}),
            ),
            loc.subtitle(),
        )
        .tab_style(label, loc.column_labels())
        .pipe(_on_spanners, label)
        .tab_style(type_("label", fonts["label"], fonts["labelWeight"], pal["text"]), loc.row_groups())
        .tab_style(type_("source", fonts["body"], 400, pal["muted"]), [loc.source_notes(), loc.footnotes()])
        .tab_options(
            table_background_color=pal["bg"],
            table_font_color=pal["text"],
            table_font_size=px(_tr(sizes["body"], k["body"])),
            heading_background_color=pal["bg"],
            heading_align=st["headingAlign"],
            heading_border_bottom_style="none",
            heading_padding=px(pad_y),
            column_labels_background_color=pal["labelBg"],
            column_labels_padding=px(pad_y),
            column_labels_padding_horizontal=px(pad_x),
            row_group_background_color=pal["summaryBg"],
            row_group_padding=px(pad_y),
            data_row_padding=px(pad_y),
            data_row_padding_horizontal=px(pad_x),
            source_notes_background_color=pal["bg"],
            source_notes_padding=px(pad_y),
            table_border_top_style="none",
            table_border_bottom_style="none",
            table_body_border_top_style="none",
            table_body_border_bottom_style="none",
            column_labels_border_top_style="none",
            column_labels_border_bottom_style="none",
            source_notes_border_bottom_style="none",
            source_notes_border_lr_style="none",
        )
    )
    heads = [".gt_col_heading", ".gt_column_spanner"]
    css = [
        _tabular_nums(tid),
        # the table font with its generic family in front of gt's system fallbacks (opt_table_font cannot spell it)
        _css(tid, ".gt_table", "font-family: " + ", ".join([_font_stack(fonts["body"]), *map(_quote, R_FONTS)]) + ";"),
        _css(tid, ".gt_table", f"border-top: {st['tableBorderTop']}; border-bottom: {st['tableBorderBottom']};"),
        _css(tid, ".gt_col_headings", f"border-top: {st['labelBorderTop']}; border-bottom: {st['labelBorderBottom']};"),
        _css(tid, "td.gt_row", f"border-top: none; border-bottom: {st['rowRule']};"),
        _css(tid, heads, f"text-align: {st['labelAlign']}; letter-spacing: {st['labelTracking']};"),
    ]
    if st["frame"] != "none":
        css.append(_css(tid, ".gt_table", f"outline: {st['frame']}; outline-offset: -1px;"))
    if st["colRule"] != "none":
        css.append(
            _css(
                tid,
                [".gt_col_heading:not(:first-child)", "td.gt_row:not(:first-child)"],
                f"border-left: {st['colRule']};",
            )
        )
    if st["stripe"]:
        css.append(_css(tid, "tbody tr:nth-child(even) td.gt_row", f"background-color: {pal['stripe']};"))
    return gt.opt_css("\n".join(css))

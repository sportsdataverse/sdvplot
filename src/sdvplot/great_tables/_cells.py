"""sdvplotR's cell styling and formatting helpers for great_tables (wave C1).

Each function ports the sdvplotR function of the same name. Rows are great_tables row selections: 0-based
positions, a polars expression (polars data) or a callable that takes the data and returns a boolean Series
(pandas data). Columns are anything great_tables accepts as a column selection. Divergences from R are listed in
``docs/PARITY_TABLES.md``.
"""

from __future__ import annotations

import copy
import inspect
import math
import re
import warnings
from collections.abc import Callable, Sequence
from decimal import Decimal
from html import escape
from numbers import Real
from typing import Any, cast
from urllib.parse import quote

import narwhals as nw
from great_tables import GT, google_font, html, loc, md, random_id, style, vals
from great_tables._gt_data import Body, Boxhead, ColInfo
from great_tables._locations import resolve_cols_c, resolve_rows_i
from great_tables._text import _process_text

from sdvplot._contrast import hex6, mix, on_color
from sdvplot._errors import SdvplotWarning

# ---------------------------------------------------------------------------------------------------------------------
# shared helpers (sdvplotR R/utils-theme.R and the per-function row/column handling)


def _check_gt(gt: Any) -> None:
    """Raise unless ``gt`` is a great_tables ``GT`` (sdvplotR's ``.check_gt``)."""
    if isinstance(gt, GT):
        return
    hint = "it looks like raw data: wrap it in GT(...) first" if hasattr(gt, "columns") else "build one with GT(data)"
    raise TypeError(f"gt must be a great_tables.GT, not {type(gt).__name__}; {hint}")


def _warn(message: str) -> None:
    warnings.warn(message, SdvplotWarning, stacklevel=3)


def _one_of(name: str, value: Any, allowed: tuple[str, ...]) -> None:
    """Raise unless ``value`` is one of ``allowed`` (the strings it is interpolated into CSS as)."""
    if value not in allowed:
        raise ValueError(f"{name} must be one of {allowed}, got {value!r}")


def _frame(gt: GT) -> Any:
    """The GT's data as a narwhals DataFrame (pandas or polars); positions, never index labels."""
    return nw.from_native(gt._tbl_data, eager_only=True)


def _columns(gt: GT, columns: Any) -> list[str]:
    """The body columns a great_tables column selection names (``None`` means every body column)."""
    return resolve_cols_c(data=gt, expr=columns)


def _values(gt: GT, column: str) -> list[Any]:
    return list(_frame(gt)[column].to_list())


def _row_indices(gt: GT, rows: Any) -> list[int]:
    """0-based row positions for a great_tables row selection (``None`` means every row)."""
    return [i for _, i in resolve_rows_i(gt, rows)]


def _kept_rows(gt: GT, rows: Any) -> list[int] | None:
    """Rows to style, or ``None`` (after one warning) when ``rows`` was given and matched nothing."""
    idx = _row_indices(gt, rows)
    if rows is not None and not idx:
        _warn("rows matched no rows; returning the table unchanged")
        return None
    return idx


def _is_na(v: Any) -> bool:
    """R's ``is.na``: None, NaN, NaT and pandas.NA."""
    if v is None:
        return True
    try:
        return bool(v != v)
    except TypeError:  # pandas.NA refuses bool()
        return True


def _flags(values: Any) -> list[bool]:
    """A boolean vector with R's ``!is.na(x) & as.logical(x)``: missing counts as not matched."""
    out = []
    for v in list(values):
        try:
            out.append(not _is_na(v) and bool(v))
        except (TypeError, ValueError):
            out.append(False)
    return out


def _constant(value: str) -> Callable[[Any], str]:
    """A great_tables ``fmt`` function that ignores the cell and returns ``value`` (sdvplotR's ``.constant``)."""

    def fn(_x: Any) -> str:
        return value

    return fn


# ---------------------------------------------------------------------------------------------------------------------
# rows and cells


def gt_bold_rows(gt: GT, rows: Any = None, text_color: str = "black", highlight_color: str | None = None) -> GT:
    """Bold the body cells of chosen rows, optionally recoloring their text and filling them.

    Args:
        gt: The table.
        rows: The rows to bold, as great_tables' ``loc.body(rows=)`` takes them: a 0-based position or list of
            positions, a polars expression (polars data) or a callable returning a boolean Series (pandas data).
            ``None`` bolds every row.
        text_color: Text color of the bolded rows.
        highlight_color: Background fill of the bolded rows; ``None`` for no fill.

    Returns:
        GT: A new table; ``gt`` is unchanged. When ``rows`` matches nothing, ``gt`` itself, with one
        SdvplotWarning.

    Raises:
        TypeError: ``gt`` is not a ``GT``.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_bold_rows

            gt_bold_rows(GT(df), rows=pl.col("mpg") > 20, highlight_color="#FFF3B0")

    See Also:
        Ported from sdvplotR ``gt_bold_rows()``.
    """
    _check_gt(gt)
    idx = _kept_rows(gt, rows)
    if idx is None:
        return gt
    styles: list[Any] = [style.text(color=text_color, weight="bold")]
    if highlight_color is not None:
        styles.insert(0, style.fill(color=highlight_color))
    return gt.tab_style(style=styles, locations=loc.body(rows=idx))


def gt_color_results(
    gt: GT,
    result_column: Any = "result",
    win_color: str = "#5DA271",
    loss_color: str = "#C84630",
    tie_color: str | None = None,
    wins_text_color: str = "white",
    loss_text_color: str = "white",
    tie_text_color: str = "white",
    tie_value: Any = "T",
    result_type: str = "wl",
) -> GT:
    """Fill and recolor each row by the win, loss or tie result in one column.

    Args:
        gt: The table.
        result_column: The column holding the results, as any great_tables selection of exactly one column.
        win_color: Fill of winning rows.
        loss_color: Fill of losing rows.
        tie_color: Fill of tie rows; ``None`` leaves ties alone.
        wins_text_color: Text color of winning rows.
        loss_text_color: Text color of losing rows.
        tie_text_color: Text color of tie rows.
        tie_value: The value marking a tie (used when ``tie_color`` is set).
        result_type: ``"wl"`` for ``"W"``/``"L"`` values, or ``"binary"`` for ``1``/``0``.

    Returns:
        GT: A new table; rows matching no result keep their styling.

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: ``result_column`` does not select exactly one column, or ``result_type`` is unknown.

    Example:
        ::

            gt_color_results(GT(games), result_column="result")

    See Also:
        Ported from sdvplotR ``gt_color_results()``.
    """
    _check_gt(gt)
    if result_type not in ("wl", "binary"):
        raise ValueError(f'result_type must be "wl" or "binary", got {result_type!r}')
    cols = _columns(gt, result_column)
    if len(cols) != 1:
        raise ValueError(f"result_column must select exactly one column; it selected {len(cols)}")
    col = _values(gt, cols[0])
    win, loss = (1, 0) if result_type == "binary" else ("W", "L")
    out = gt
    passes = [(win, win_color, wins_text_color), (loss, loss_color, loss_text_color)]
    if tie_color is not None:
        passes.append((tie_value, tie_color, tie_text_color))
    for value, fill, ink in passes:
        rows = [i for i, v in enumerate(col) if not _is_na(v) and v == value]
        if rows:
            out = out.tab_style(style=[style.fill(color=fill), style.text(color=ink)], locations=loc.body(rows=rows))
    return out


def gt_highlight_cells(
    gt: GT,
    columns: Any,
    condition: Callable[[Any], Any] | Any,
    fill: str = "#FFF3B0",
    text_color: str | None = None,
    bold: bool = False,
    **text_kwargs: Any,
) -> GT:
    """Fill the individual cells of a block of columns that meet a condition.

    Each selected column is tested and filled on its own, so the filled cells can form a diagonal, a checker or
    any scatter (one ``tab_style`` over ``loc.body`` would fill a whole rectangle).

    Args:
        gt: The table.
        columns: The block of columns to test.
        condition: A callable applied to each column's data (a pandas or polars Series, as the table holds) that
            returns one boolean per row, such as ``lambda s: s > 0.7``; or a mask computed ahead of time with one
            column per selected column (a pandas or polars DataFrame, or a 2-D sequence or array of rows).
            Missing counts as not matched.
        fill: Fill of the matching cells.
        text_color: Text color of the matching cells; ``None`` leaves it alone.
        bold: Bold the matching cells.
        **text_kwargs: Passed to great_tables ``style.text`` for the matching cells, such as ``style="italic"``.

    Returns:
        GT: A new table with the matching cells filled.

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: ``columns`` matches nothing, the mask has the wrong number of columns, or ``condition`` fails
            on a column or does not return one value per row.

    Example:
        ::

            gt_highlight_cells(GT(cor_df, rowname_col="var"), ["mpg", "hp"], lambda s: s > 0.7, fill="#FFD1A9")

    See Also:
        Ported from sdvplotR ``gt_highlight_cells()``.
    """
    _check_gt(gt)
    cols = _columns(gt, columns)
    if not cols:
        raise ValueError("columns matched no columns")
    masks = _condition_masks(gt, cols, condition)
    text_args = dict(text_kwargs)
    if text_color is not None:
        text_args["color"] = text_color
    if bold:
        text_args["weight"] = "bold"
    styles: list[Any] = [style.fill(color=fill)]
    if text_args:
        styles.append(style.text(**text_args))
    out = gt
    for c in cols:
        rows = [i for i, hit in enumerate(masks[c]) if hit]
        if rows:
            out = out.tab_style(style=styles, locations=loc.body(columns=c, rows=rows))
    return out


def _condition_masks(gt: GT, cols: list[str], condition: Any) -> dict[str, list[bool]]:
    frame = _frame(gt)
    if callable(condition):
        masks = {}
        for c in cols:
            try:
                out = condition(frame[c].to_native())
            except Exception as e:
                raise ValueError(
                    f"condition could not be applied to column {c!r} ({e}); select only the columns it fits"
                ) from e
            flags = _flags(out)
            if len(flags) != len(frame):
                raise ValueError("condition must return one value per row")
            masks[c] = flags
        return masks
    try:
        mask = nw.from_native(condition, eager_only=True)
        by_column = [list(mask[name].to_list()) for name in mask.columns]
    except TypeError:
        rows = [list(r) for r in condition]
        width = len(rows[0]) if rows else 0
        if any(len(r) != width for r in rows):
            raise ValueError("a mask condition must have the same number of values in every row") from None
        by_column = [[r[j] for r in rows] for j in range(width)]
    if len(by_column) != len(cols):
        raise ValueError(
            f"a mask condition must have one column per selected column: got {len(by_column)} for {len(cols)}"
        )
    return {c: _flags(v) for c, v in zip(cols, by_column, strict=True)}


def gt_highlight_na(
    gt: GT,
    columns: Any = None,
    fill: str | None = "#F0F0F0",
    text_color: str | None = None,
    bold: bool = False,
    italic: bool = False,
    missing_text: str | None = None,
    na_strings: str | Sequence[str] = "NA",
    ignore_case: bool = False,
    **text_kwargs: Any,
) -> GT:
    """Style, and optionally relabel, missing values.

    Missing means a real null/NaN or a value whose trimmed text is one of ``na_strings`` (a CSV's ``"NA"``,
    by default).

    Args:
        gt: The table.
        columns: The columns to check; ``None`` checks every body column.
        fill: Fill behind missing values; ``None`` for no fill.
        text_color: Text color of missing values.
        bold: Bold missing values.
        italic: Italicize missing values.
        missing_text: Replacement text for missing values, such as ``"--"``; ``None`` leaves the text alone.
        na_strings: Strings treated as missing alongside real nulls.
        ignore_case: Match ``na_strings`` case-insensitively.
        **text_kwargs: Passed to great_tables ``style.text``.

    Returns:
        GT: A new table with missing values styled.

    Raises:
        TypeError: ``gt`` is not a ``GT``.

    Example:
        ::

            gt_highlight_na(GT(df), ["ozone", "solar"], missing_text="not recorded", italic=True)

    See Also:
        Ported from sdvplotR ``gt_highlight_na()``.
    """
    _check_gt(gt)
    wanted = [na_strings] if isinstance(na_strings, str) else list(na_strings)
    if ignore_case:
        wanted = [s.lower() for s in wanted]

    def missing(v: Any) -> bool:
        if _is_na(v):
            return True
        text = str(v).strip()
        return (text.lower() if ignore_case else text) in wanted

    text_args = {
        k: v
        for k, v in {
            "color": text_color,
            "weight": "bold" if bold else None,
            "style": "italic" if italic else None,
        }.items()
        if v is not None
    } | text_kwargs
    styles: list[Any] = []
    if fill is not None:
        styles.append(style.fill(color=fill))
    if text_args:
        styles.append(style.text(**text_args))

    out = gt
    for col in _columns(gt, columns):
        rows = [i for i, v in enumerate(_values(gt, col)) if missing(v)]
        if not rows:
            continue
        if styles:
            out = out.tab_style(style=styles, locations=loc.body(columns=col, rows=rows))
        if missing_text is not None:
            # fmt, not text_transform: great_tables skips null cells in text_transform
            out = out.fmt(_constant(missing_text), columns=col, rows=rows)
    return out


def gt_group_stripes(gt: GT, color: str = "#F5F5F5", start: int = 2, include_stub: bool = True) -> GT:
    """Shade every other row group, so each group reads as a block.

    Groups are banded in the order they render (``GT.row_group_order``), not the order they appear in the data.
    Group heading rows are left alone.

    Args:
        gt: The table. It must have row groups (``GT(data, groupname_col=...)``).
        color: Fill of the banded groups.
        start: ``2`` leaves the first group unshaded, ``1`` shades it.
        include_stub: Band the stub column along with the body.

    Returns:
        GT: A new table with alternate groups banded; ``gt`` itself, with one SdvplotWarning, when the table has
        no row groups.

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: ``start`` is not 1 or 2.

    Example:
        ::

            gt_group_stripes(GT(df, groupname_col="conference"), color="#FBF3E4", start=1)

    See Also:
        Ported from sdvplotR ``gt_group_stripes()``.
    """
    _check_gt(gt)
    groups = list(gt._stub.group_rows)
    if not groups:
        _warn("gt_group_stripes needs a table with row groups: build it with GT(data, groupname_col=...)")
        return gt
    if start not in (1, 2):
        raise ValueError(f"start must be 1 or 2, got {start!r}")
    rows = sorted(int(i) for group in groups[start - 1 :: 2] for i in group.indices)  # pandas gives numpy ints
    if not rows:
        return gt
    out = gt.tab_style(style=style.fill(color=color), locations=loc.body(rows=rows))
    if include_stub and any(c.type.name == "stub" for c in gt._boxhead):
        out = out.tab_style(style=style.fill(color=color), locations=loc.stub(rows=rows))
    return out


# ---------------------------------------------------------------------------------------------------------------------
# borders, bars, rules and captions: scoped CSS keyed on the table id

_borders = style.borders  # gt_cutline's ``style`` argument shadows the great_tables module


def _table_id(gt: GT) -> tuple[GT, str]:
    """The table's id, assigning a random one when it has none, so CSS can be scoped to ``#id`` (``.table_id``)."""
    table_id = gt._options.table_id.value
    if table_id is None:
        table_id = random_id()
        gt = gt.with_id(table_id)
    return gt, table_id


def _md(text: str) -> str:
    """Markdown to HTML, as great_tables renders ``md()`` (raw HTML passes through)."""
    return _process_text(md(text)).strip()


def gt_538_caption(
    gt: GT,
    top_caption: str | None = None,
    bottom_caption: str | None = None,
    rule_color: str | None = None,
    rule_width: float = 1,
    size: float = 12,
    align: str = "right",
) -> GT:
    """Add a FiveThirtyEight-style caption under the table: a top caption over a rule, then a bottom caption.

    Both captions accept markdown (and raw HTML). great_tables renders source notes above footnotes, so both
    captions are source notes (sdvplotR makes the top one a footnote): the top one carries the rule and ``size``,
    the bottom one is aligned by ``align``. Apply the theme first: the rule color is read off the rendered table.

    Args:
        gt: The table.
        top_caption: Text above the rule; ``None`` leaves out the rule too.
        bottom_caption: Text below the rule.
        rule_color: The rule's color; ``None`` takes the first text color in the rendered table (so it tracks a
            dark theme; a ``background-color`` or ``border-*-color`` is never taken), else a neutral gray.
        rule_width: The rule width in pixels.
        size: The top caption's font size in pixels.
        align: The bottom caption's alignment: ``"left"``, ``"center"`` or ``"right"``.

    Returns:
        GT: A new table with the captions.

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: Neither caption was given, or ``align`` is unknown.

    Example:
        ::

            gt_538_caption(GT(df), top_caption="Fuel economy and power", bottom_caption="Source: *Motor Trend*")

    See Also:
        Ported from sdvplotR ``gt_538_caption()``.
    """
    _check_gt(gt)
    if top_caption is None and bottom_caption is None:
        raise ValueError("nothing to caption: pass top_caption (above the rule), bottom_caption (below it), or both")
    _one_of("align", align, ("left", "center", "right"))
    if rule_color is None:  # a bare `color:` declaration, not the tail of `background-color:` or `border-*-color:`
        found = re.search(r"(?<![\w-])color:\s(#[0-9A-Fa-f]{6})", gt.as_raw_html())
        rule_color = found.group(1) if found else "#8A8A8A"
    out = gt
    if top_caption is not None:
        rule = f"border-bottom: {rule_width}px solid {rule_color}; font-size: {size}px;"
        out = out.tab_source_note(html(f'<div style="{rule}">{_md(top_caption)}</div>'))
    if bottom_caption is not None:
        out = out.tab_source_note(html(f'<div style="text-align: {align};">{_md(bottom_caption)}</div>'))
    return out


_BAR_ALIGN = {
    "left": "margin-left: 0; margin-right: auto;",
    "center": "margin-left: auto; margin-right: auto;",
    "right": "margin-left: auto; margin-right: 0;",
}


def _style_font(gt: GT, where: type) -> str | None:
    """The first font set with ``tab_style(style.text(font=...))`` on a location of type ``where``."""
    for info in gt._styles:
        if isinstance(info.locname, where):
            for s in info.styles:
                font = getattr(s, "font", None)
                if isinstance(font, str) and font:
                    return font
    return None


def _bars(gt: GT, where: type, colors: str | Sequence[str], **a: Any) -> str:
    """The bar block sdvplotR's ``gt_border_bars_top``/``_bottom`` build, as one HTML string."""
    _one_of("bar_align", a["bar_align"], tuple(_BAR_ALIGN))
    _one_of("img_align", a["img_align"], ("left", "right"))  # each becomes a `padding-<side>` property
    _one_of("text_align", a["text_align"], ("left", "right"))
    colors = [colors] if isinstance(colors, str) else list(colors)
    align = _BAR_ALIGN[a["bar_align"]]
    if a["text"] is None and a["img"] is None:
        stack = "".join(f'<div style="height: {a["bar_height"]}px; background-color: {c};"></div>' for c in colors)
        return f'<div style="background-color: transparent; width: {a["bar_width"]}; {align}">{stack}</div>'
    font = _style_font(gt, where)
    head = f"<style>{google_font(font).make_import_stmt()}</style>" if font else ""
    text = (
        f'<span style="font-weight:{a["text_weight"]}; color:{a["text_color"]}; font-size:{a["text_size"]}px; '
        f'padding-{a["text_align"]}: {a["text_padding"]}px; font-family: {font or "inherit"};">{a["text"]}</span>'
        if a["text"] is not None
        else "<span></span>"
    )
    img = (
        f'<img src="{a["img"]}" width="{a["img_width"]}px" height="{a["img_height"]}px" '
        f'style="padding-{a["img_align"]}:{a["img_padding"]}px;" />'
        if a["img"] is not None
        else ""
    )
    return (
        f'{head}<div style="display: flex; justify-content: space-between; align-items: center; '
        f'height: {a["bar_height"]}px; background-color: {colors[0]}; width: {a["bar_width"]}; {align}">'
        f"{text}{img}</div>"
    )


def gt_border_bars_top(
    gt: GT,
    colors: str | Sequence[str],
    bar_height: float = 10,
    bar_width: str = "100%",
    bar_align: str = "center",
    img: str | None = None,
    img_width: float = 30,
    img_height: float = 30,
    img_padding: float = 10,
    img_align: str = "right",
    text: str | None = None,
    text_weight: str = "bold",
    text_color: str = "#FFFFFF",
    text_size: float = 18,
    text_align: str = "left",
    text_padding: float = 10,
) -> GT:
    """Add a row of horizontal color bars at the top of the table, optionally carrying text and an image.

    With neither ``text`` nor ``img``, each color is its own full-width bar, stacked. With either, one bar in the
    first color holds the text at one end and the image at the other; the text uses the font set on the title
    (imported from Google Fonts) or inherits. great_tables has no ``tab_caption``, so the bars go at the top of
    the heading, above the title: call this after ``tab_header``.

    Args:
        gt: The table.
        colors: One color per bar (only the first is used with ``text`` or ``img``).
        bar_height: Bar height in pixels.
        bar_width: Width of the bar block, as a CSS width.
        bar_align: ``"left"``, ``"center"`` or ``"right"``, when ``bar_width`` is under 100%.
        img: URL of an image to show in the bar.
        img_width: Image width in pixels.
        img_height: Image height in pixels.
        img_padding: Padding beside the image in pixels.
        img_align: The side of the image the padding goes on (``"left"`` or ``"right"``).
        text: Text to show in the bar.
        text_weight: Font weight of the text.
        text_color: Text color.
        text_size: Text size in pixels.
        text_align: The side of the text the padding goes on (``"left"`` or ``"right"``).
        text_padding: Padding beside the text in pixels.

    Returns:
        GT: A new table with the bars above its title.

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: ``bar_align``, ``img_align`` or ``text_align`` is not one of its listed values.

    Example:
        ::

            gt_border_bars_top(GT(df).tab_header("Standings"), ["#1B7837", "#FFFFFF", "#B2182B"])

    See Also:
        Ported from sdvplotR ``gt_border_bars_top()``.
    """
    _check_gt(gt)
    bar_args = {k: v for k, v in locals().items() if k not in ("gt", "colors")}  # every styling argument
    gt, table_id = _table_id(gt)
    bars = _bars(gt, loc.title, colors, **bar_args)
    heading = gt._heading
    title = "" if heading.title is None else f'<div style="padding: 4px 5px;">{_process_text(heading.title)}</div>'
    subtitle = cast(Any, heading.subtitle)  # GTData annotates it BaseText; tab_header stores Text
    return gt.tab_header(title=html(bars + title), subtitle=subtitle, preheader=heading.preheader).opt_css(
        f"#{table_id} .gt_title {{padding: 0px !important;}}"
    )


def gt_border_bars_bottom(
    gt: GT,
    colors: str | Sequence[str],
    bar_height: float = 10,
    bar_width: str = "100%",
    bar_align: str = "center",
    img: str | None = None,
    img_width: float = 30,
    img_height: float = 30,
    img_padding: float = 10,
    img_align: str = "right",
    text: str | None = None,
    text_weight: str = "bold",
    text_color: str = "#FFFFFF",
    text_size: float = 18,
    text_align: str = "left",
    text_padding: float = 10,
) -> GT:
    """Add a row of horizontal color bars below the table, optionally carrying text and an image.

    The bottom-edge counterpart of ``gt_border_bars_top``: the bars are a source note, and the source notes lose
    their side and bottom padding so the bars reach the table's edges. The text uses the font set on the source
    notes (imported from Google Fonts) or inherits.

    Args:
        gt: The table.
        colors: One color per bar (only the first is used with ``text`` or ``img``).
        bar_height: Bar height in pixels.
        bar_width: Width of the bar block, as a CSS width.
        bar_align: ``"left"``, ``"center"`` or ``"right"``, when ``bar_width`` is under 100%.
        img: URL of an image to show in the bar.
        img_width: Image width in pixels.
        img_height: Image height in pixels.
        img_padding: Padding beside the image in pixels.
        img_align: The side of the image the padding goes on (``"left"`` or ``"right"``).
        text: Text to show in the bar.
        text_weight: Font weight of the text.
        text_color: Text color.
        text_size: Text size in pixels.
        text_align: The side of the text the padding goes on (``"left"`` or ``"right"``).
        text_padding: Padding beside the text in pixels.

    Returns:
        GT: A new table with the bars below it.

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: ``bar_align``, ``img_align`` or ``text_align`` is not one of its listed values.

    Example:
        ::

            gt_border_bars_bottom(GT(df), "#22223B", text="Source: ESPN", bar_height=28)

    See Also:
        Ported from sdvplotR ``gt_border_bars_bottom()``.
    """
    _check_gt(gt)
    bar_args = {k: v for k, v in locals().items() if k not in ("gt", "colors")}  # every styling argument
    gt, table_id = _table_id(gt)
    bars = _bars(gt, loc.source_notes, colors, **bar_args)
    unpad = "padding-right: 0px !important; padding-left: 0px !important; padding-bottom: 0px;"
    return gt.tab_source_note(html(bars)).opt_css(f"#{table_id} .gt_sourcenote {{{unpad}}}")


def gt_border_grid(gt: GT, color: str = "black", weight: float = 1, include_labels: bool = False) -> GT:
    """Draw borders between every column and every row, a full grid.

    Args:
        gt: The table.
        color: Border color.
        weight: Border thickness in pixels.
        include_labels: Extend the column borders through the column labels.

    Returns:
        GT: A new table with the grid.

    Raises:
        TypeError: ``gt`` is not a ``GT``.

    Example:
        ::

            gt_border_grid(GT(df), color="#BBBBBB", weight=2, include_labels=True)

    See Also:
        Ported from sdvplotR ``gt_border_grid()`` (which uses gtExtras ``gt_add_divider``).
    """
    _check_gt(gt)
    gt, table_id = _table_id(gt)
    visible = [c.var for c in gt._boxhead if c.type.name == "default"]
    out = gt
    if len(visible) > 1:  # every column but the last gets a right border (gt_add_divider(columns = -last_col()))
        divider = _borders(sides="right", color=color, style="solid", weight=f"{weight}px")
        where: list[Any] = [loc.body(columns=visible[:-1])]
        if include_labels:
            where.append(loc.column_labels(columns=visible[:-1]))
        out = out.tab_style(style=divider, locations=where)
    return out.opt_css(f"#{table_id} .gt_row {{ border-top-color: {color};}}")


def _cutline_svg(text: str, color: str, size: float) -> str:
    """The label as a URL-encoded inline SVG (sdvplotR's ``.cutline_svg``, byte for byte)."""
    text = str(text).upper()
    esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    tracking = 1.1
    width = len(text) * (size * 0.80 + tracking) + 4
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{size + 4:.0f}">'
        f'<text x="0" y="{size + 0.5:.1f}" font-family="Helvetica,Arial,sans-serif" '
        f'font-size="{size:g}" font-weight="700" letter-spacing="{tracking:g}" fill="{color}">{esc}</text></svg>'
    )
    return "data:image/svg+xml;charset=utf-8," + quote(svg, safe="")


def gt_cutline(
    gt: GT,
    after: int | Sequence[int],
    label: str | Sequence[str | None] | None = None,
    color: str = "#A6081A",
    weight: float = 2,
    style: str = "dashed",
    label_color: str | None = None,
    label_size: float = 9,
    label_position: str = "below",
    gap: float | Sequence[float] = 0,
) -> GT:
    """Draw a rule across the table after a given row, with an optional label: the cut line of a ranked table.

    The label is an inline SVG background on the row (CSS pseudo-elements do not survive inlining), so it renders
    in a system sans-serif, and the labeled row's cell fills are cleared (its stripe is repainted on the row).
    Labels assume the table has no row groups. Apply the theme first: the stripe color is read from its options.

    Args:
        gt: The table.
        after: The number of rows above each line: ``4`` draws between the 4th and 5th rows, ``0`` above the
            first. One whole number or several (numpy integers included).
        label: A label per line, recycled against ``after``; ``None`` in a list leaves that line unlabeled. Drawn
            in uppercase.
        color: The rule color.
        weight: The rule thickness in pixels.
        style: ``"dashed"``, ``"solid"`` or ``"dotted"``.
        label_color: The label color; ``None`` uses ``color``.
        label_size: The label size in pixels.
        label_position: ``"below"`` or ``"above"`` the line.
        gap: Extra space in pixels around each line: one number for both sides, or ``(above, below)``.

    Returns:
        GT: A new table with the lines; ``gt`` itself, with one SdvplotWarning, when every line is out of range.

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: ``after`` is not numeric or not a whole number, ``gap`` is not one or two non-negative
            numbers, or ``style`` or ``label_position`` is unknown.

    Example:
        ::

            gt_cutline(GT(standings), after=6, label="Playoff line")

    See Also:
        Ported from sdvplotR ``gt_cutline()``.
    """
    _check_gt(gt)
    if label_position not in ("below", "above"):
        raise ValueError(f'label_position must be "below" or "above", got {label_position!r}')
    _one_of("style", style, ("dashed", "solid", "dotted"))
    # numbers.Real, not int | float: numpy integers are neither, and list() of one raises a TypeError
    afters: list[Any] = [after] if isinstance(after, Real) else list(cast(Sequence[Any], after))
    if not afters:
        return gt
    if not all(isinstance(a, Real) and not isinstance(a, bool) for a in afters):
        raise ValueError("after must be numeric row numbers")
    if not all(float(a).is_integer() for a in afters):
        raise ValueError(f"after must be whole row numbers, got {[float(a) for a in afters]}")
    afters = [int(a) for a in afters]
    gaps: list[Any] = [gap] if isinstance(gap, Real) else list(cast(Sequence[Any], gap))
    if not 1 <= len(gaps) <= 2 or any(not isinstance(g, Real) or g < 0 for g in gaps):
        raise ValueError("gap must be one or two non-negative numbers")
    above_gap, below_gap = gaps[0], gaps[-1]

    labels: list[str | None] | None = None
    if label is not None:
        given = [label] if isinstance(label, str) else list(label)
        labels = [given[i % len(given)] for i in range(len(afters))]
    n_rows = len(_frame(gt))
    keep = [0 <= a < n_rows for a in afters]
    if not all(keep):
        dropped = [a for a, k in zip(afters, keep, strict=True) if not k]
        _warn(
            f"dropped {len(dropped)} cut line(s) at {dropped}: after must be between 0 and {n_rows - 1}; "
            "a line after the last row is just the table border"
        )
        afters = [a for a, k in zip(afters, keep, strict=True) if k]
        labels = None if labels is None else [x for x, k in zip(labels, keep, strict=True) if k]
        if not afters:
            return gt
    label_color = label_color or color
    gt, table_id = _table_id(gt)

    # the rule is a top border on the row below the cut (0-based row `a` is R's row a + 1)
    out = gt
    for a in afters:
        rule = _borders(sides="top", weight=f"{weight}px", color=color, style=style)
        out = out.tab_style(style=rule, locations=loc.body(rows=[int(a)]))

    below = label_position == "below"
    css: list[str] = []
    # room around each rule on the flanking rows (CSS nth-child is 1-based); a labeled side folds its share into
    # the label's padding instead
    for i, a in enumerate(afters):
        labeled = labels is not None and bool(labels[i])
        label_row = 1 if a == 0 else (a + 1 if below else a)
        for r, side, value in ((a, "bottom", above_gap), (a + 1, "top", below_gap)):
            if value <= 0 or r < 1 or r > n_rows or (labeled and r == label_row):
                continue
            css.append(f"#{table_id} tbody tr:nth-child({r:g}) td {{ padding-{side}: {value:g}px !important; }}")

    if labels is not None:
        opts = out._options
        striping = bool(opts.row_striping_include_table_body.value)
        stripe = opts.row_striping_background_color.value
        for a, lab in zip(afters, labels, strict=True):
            if not lab:
                continue
            row, side, pos = (a + 1, "top", "left 5px") if below else (a, "bottom", "left bottom 5px")
            if row < 1:  # nothing above row 1 to sit under, so the label drops into its top
                row, side, pos = 1, "top", "left 5px"
            pad = label_size + 13 + (below_gap if side == "top" else above_gap)
            row_bg = f"background-color: {stripe}; " if striping and row % 2 == 0 and stripe else ""
            css.append(
                f"#{table_id} tbody tr:nth-child({row:g}) td {{ padding-{side}: {pad:g}px !important; "
                "background-color: transparent !important; }"
            )
            css.append(
                f'#{table_id} tbody tr:nth-child({row:g}) {{ {row_bg}background-image: url("'
                f'{_cutline_svg(lab, label_color, label_size)}"); '
                f"background-repeat: no-repeat; background-position: {pos}; }}"
            )
    return out.opt_css("\n".join(css)) if css else out


# ---------------------------------------------------------------------------------------------------------------------
# color scales, pills and boxes


def _number(v: Any) -> float | None:
    """R's ``as.numeric`` without the warning: numbers, booleans and numeric strings; anything else is None."""
    if _is_na(v) or (isinstance(v, str) and not v.strip()):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _natural(v: float, big: bool = False) -> str:
    """R's ``format(v, trim = TRUE, scientific = FALSE)``: up to 7 significant digits, never scientific."""
    if math.isinf(v):
        return "Inf" if v > 0 else "-Inf"
    exponent = Decimal(f"{v:.7g}").normalize().as_tuple().exponent
    decimals = max(0, -exponent) if isinstance(exponent, int) else 0
    return f"{v:{',' if big else ''}.{decimals}f}"


def _format_value(value: float | None, digits: int | None, format_type: str, suffix: str) -> str:
    """sdvplotR's pill and box label for an already-scaled value: ``number``, ``comma``, ``currency`` or ``percent``.

    A missing value prints as ``NA``, as R's ``format(NA)`` does.
    """
    big = format_type in ("comma", "currency")
    if value is None:
        core = "NA"
    elif digits is None:
        core = _natural(value, big)
    else:
        core = f"{value:{',' if big else ''}.{digits}f}"
    if format_type == "currency":
        core = "$" + core
    elif format_type == "percent":
        core += "%"
    return core + suffix


_FORMAT_TYPES = ("number", "comma", "currency", "percent")


def _fmt_rows(gt: GT, column: str, cells: dict[int, str]) -> GT:
    """Put per-row HTML into a column (sdvplotR's ``.fmt_rows``).

    great_tables formatters see a cell's value, not its row, so this adds one ``fmt`` per distinct string, over the
    rows that carry it. Formatting by data row keeps row groups and sorting from scrambling the cells.
    """
    by_html: dict[str, list[int]] = {}
    for row, text in cells.items():
        by_html.setdefault(text, []).append(row)
    for text, rows in by_html.items():
        gt = gt.fmt(_constant(text), columns=column, rows=rows)
    return gt


def _palette(palette: Sequence[str], pal_type: str) -> list[str]:
    """The palette as ``#rrggbb`` strings; a ``str`` (a named or paletteer palette) is refused."""
    if pal_type not in ("discrete", "continuous"):
        raise ValueError(f'pal_type must be "discrete" or "continuous", got {pal_type!r}')
    if isinstance(palette, str):
        raise ValueError(f"palette must be a list of hex colors; named palettes like {palette!r} are not supported")
    colors = [hex6(c) for c in palette]
    if not colors:
        raise ValueError("palette needs at least one color")
    return colors


def _ramp(palette: list[str], domain: tuple[float, float]) -> Callable[[float], str | None]:
    """Piecewise-linear sRGB between evenly spaced stops over ``domain``, as great_tables' ``data_color``.

    Returns ``None`` for a value outside the domain.
    """
    lo, hi = domain
    k = len(palette) - 1

    def color(v: float) -> str | None:
        if not lo <= v <= hi:
            return None
        if k == 0:
            return palette[0]
        t = 0.5 if hi == lo else (v - lo) / (hi - lo)
        i = min(int(t * k), k - 1)
        return mix(palette[i], palette[i + 1], t * k - i)

    return color


def _ranks(values: list[float | None], descending: bool) -> list[float | None]:
    """R's ``rank(ties.method = "average", na.last = "keep")``, flipped so the largest value ranks 1 when descending."""
    order = sorted((v, i) for i, v in enumerate(values) if v is not None)
    ranks: list[float | None] = [None] * len(values)
    j = 0
    while j < len(order):
        k = j
        while k + 1 < len(order) and order[k + 1][0] == order[j][0]:
            k += 1
        for t in range(j, k + 1):
            ranks[order[t][1]] = (j + k) / 2 + 1
        j = k + 1
    if descending and order:
        top = max(r for r in ranks if r is not None)
        ranks = [None if r is None else top - r + 1 for r in ranks]
    return ranks


def _domain(columns: dict[str, list[float | None]], domain: Sequence[float] | None) -> tuple[float, float]:
    if domain is not None:
        return float(domain[0]), float(domain[1])
    present = [v for values in columns.values() for v in values if v is not None]
    if not present:
        raise ValueError("the columns hold no numeric values to color; pass domain")
    return min(present), max(present)


def _record_scale(
    gt: GT, columns: list[str], palette: Sequence[str], domain: tuple[float, float], reverse: bool, pal_type: str
) -> GT:
    """Leave the scale on a copy of the table for ``gt_legend_continuous`` (the shared ``_sdvplot_scale`` record)."""
    out = copy.copy(gt)
    out.__dict__["_sdvplot_scale"] = {
        "columns": list(columns),
        "palette": list(palette),
        "domain": domain,
        "reverse": reverse,
        "pal_type": pal_type,
    }
    return out


def gt_color_pills(
    gt: GT,
    columns: Any,
    rows: Any = None,
    palette: Sequence[str] = ("#C84630", "#5DA271"),
    fill_type: str = "continuous",
    rank_order: str = "desc",
    digits: int | None = None,
    domain: Sequence[float] | None = None,
    format_type: str = "number",
    scale_percent: bool = True,
    suffix: str = "",
    reverse: bool = False,
    outline_color: str | None = None,
    outline_width: float = 0.25,
    pal_type: str = "discrete",
    pill_height: float = 25,
    text_color: str | None = None,
    na_color: str | None = None,
) -> GT:
    """Show values as rounded pills filled from a palette, by value or by rank.

    Several columns share one ``domain`` (taken from them all when unset, with a warning) so their colors compare;
    pill width is set per column. With ``fill_type="rank"`` each column is ranked against itself (average ties).
    The text is black or white, whichever reads better on the fill, unless ``text_color`` is set. A value outside
    ``domain`` is drawn grey (``#808080``) with one warning. The scale is recorded for ``gt_legend_continuous``.

    Args:
        gt: The table.
        columns: The columns to fill.
        rows: The rows to fill, as great_tables' ``loc.body(rows=)`` takes them; the rest keep their value.
            ``None`` fills every row.
        palette: Hex colors, low to high.
        fill_type: ``"continuous"`` (by value) or ``"rank"``.
        rank_order: ``"desc"`` (the largest value ranks 1) or ``"asc"``, for ``fill_type="rank"``.
        digits: Decimal places of the printed value; ``None`` prints it naturally.
        domain: ``(low, high)`` mapped onto the palette; ``None`` uses the observed range and warns.
        format_type: ``"number"``, ``"comma"``, ``"currency"`` or ``"percent"``.
        scale_percent: Multiply by 100 for ``format_type="percent"``.
        suffix: Appended to each printed value, such as ``"M"``.
        reverse: Reverse the palette.
        outline_color: A border color around each pill; ``None`` for none.
        outline_width: The border width in pixels.
        pal_type: ``"discrete"`` or ``"continuous"``; recorded for the legend only (sdvplotR uses it to look up
            paletteer palettes, which Python does not have).
        pill_height: Pill height in pixels.
        text_color: The pill text color; ``None`` picks black or white per pill.
        na_color: A hex color for a pill over a missing value; ``None`` leaves the cell blank.

    Returns:
        GT: A new table with pills, recording ``_sdvplot_scale``; ``gt`` itself, with one SdvplotWarning, when
        ``rows`` matches nothing.

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: ``columns`` matches nothing; the palette is not a list of hex colors; an option is not one
            of its listed values; or there is no ``domain`` and no numeric value to derive one from.

    Example:
        ::

            gt_color_pills(GT(df), ["disp", "hp"], domain=(50, 500))
            gt_color_pills(GT(df), "hp", fill_type="rank", domain=(1, 6), digits=0)

    See Also:
        Ported from sdvplotR ``gt_color_pills()``; ``gt_color_ranks`` fills the whole cell.
    """
    _check_gt(gt)
    cols = _columns(gt, columns)
    if not cols:
        raise ValueError("columns matched no columns")
    for name, value, allowed in (
        ("fill_type", fill_type, ("continuous", "rank")),
        ("rank_order", rank_order, ("asc", "desc")),
        ("format_type", format_type, _FORMAT_TYPES),
    ):
        if value not in allowed:
            raise ValueError(f"{name} must be one of {allowed}, got {value!r}")
    pal = _palette(palette, pal_type)
    keep = _kept_rows(gt, rows)
    if keep is None:
        return gt

    numbers = {c: [_number(v) for v in _values(gt, c)] for c in cols}
    scaled = {c: _ranks(v, rank_order == "desc") if fill_type == "rank" else v for c, v in numbers.items()}
    lo, hi = _domain(scaled, domain)
    if domain is None:
        _warn(
            f"no domain given, so the colors span the observed range ({_natural(lo)} to {_natural(hi)}); "
            "set domain to compare colors across tables or columns"
        )
    ramp = _ramp(pal[::-1] if reverse else pal, (lo, hi))
    outline = f"border: {outline_width}px solid {outline_color};" if outline_color is not None else ""

    def label(v: float | None) -> str:
        if v is not None and format_type == "percent" and scale_percent:
            v *= 100
        return _format_value(v, digits, format_type, suffix)

    out, outside = gt, 0
    for c in cols:
        width = max((len(label(numbers[c][i])) for i in keep), default=1)
        cells: dict[int, str] = {}
        for i in keep:
            s = scaled[c][i]
            if s is None:
                if na_color is None:
                    cells[i] = ""
                    continue
                fill, text = na_color, ""
            else:
                ramped = ramp(s)
                if ramped is None:
                    outside += 1
                fill, text = ramped or "#808080", label(numbers[c][i])
            ink = text_color or on_color(fill)
            cells[i] = (
                f"<span style='display: inline-block; width: {width}ch; padding-left: 3px; padding-right: 3px; "
                f"height: {pill_height}px; line-height: {pill_height}px; background-color: {fill}; color: {ink}; "
                f"border-radius: 10px; text-align: center; {outline}'>{text}</span>"
            )
        out = _fmt_rows(out, c, cells)
    if outside:
        _warn(f"{outside} value(s) fall outside the domain ({_natural(lo)} to {_natural(hi)}) and are drawn grey")
    return _record_scale(out, cols, palette, (lo, hi), reverse, pal_type)


def gt_color_ranks(
    gt: GT,
    columns: Any,
    rows: Any = None,
    palette: Sequence[str] = ("#3D8B6E", "#9DC5A7", "#EDE0CC", "#DB9070", "#BE4D3A"),
    domain: Sequence[float] | None = None,
    reverse: bool = False,
    na_color: str = "white",
    autocolor_text: bool = True,
    pal_type: str = "discrete",
    **data_color_kwargs: Any,
) -> GT:
    """Fill the cells of columns that already hold ranks (1 is best), green to red by default.

    A shorthand around great_tables' ``data_color``: the values are colored as they are, no ranking is computed.
    The domain is shared across the columns (rank 1 and the largest rank present anchor the ends) unless given.
    The scale is recorded for ``gt_legend_continuous``.

    Args:
        gt: The table.
        columns: The columns to color.
        rows: The rows to color, as great_tables' ``loc.body(rows=)`` takes them; ``None`` colors every row.
        palette: Hex colors, low to high.
        domain: ``(low, high)`` mapped onto the palette; ``None`` uses the selected columns' range.
        reverse: Reverse the palette.
        na_color: The fill of missing values.
        autocolor_text: Set each cell's text to black or white for contrast.
        pal_type: ``"discrete"`` or ``"continuous"``; recorded for the legend only.
        **data_color_kwargs: Passed to ``GT.data_color`` (``alpha``, ``truncate``).

    Returns:
        GT: A new table, recording ``_sdvplot_scale``; ``gt`` itself, with one SdvplotWarning, when ``rows``
        matches nothing.

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: ``columns`` matches nothing, the palette is not a list of hex colors, or there is no
            ``domain`` and no numeric value to derive one from.

    Example:
        ::

            gt_color_ranks(GT(ranked), ["off_rank", "def_rank"])

    See Also:
        Ported from sdvplotR ``gt_color_ranks()``; ``gt_color_pills`` draws pills instead.
    """
    _check_gt(gt)
    cols = _columns(gt, columns)
    if not cols:
        raise ValueError("columns matched no columns")
    _palette(palette, pal_type)
    keep = _kept_rows(gt, rows)
    if keep is None:
        return gt
    lo, hi = _domain({c: [_number(v) for v in _values(gt, c)] for c in cols}, domain)
    out = gt.data_color(
        columns=cols,
        rows=keep,
        palette=list(palette),
        domain=[lo, hi],
        na_color=na_color,
        reverse=reverse,
        autocolor_text=autocolor_text,
        **data_color_kwargs,
    )
    return _record_scale(out, cols, palette, (lo, hi), reverse, pal_type)


def _takes_column(rule: Callable[..., Any]) -> bool:
    """Whether an indicator rule takes the column name as a second argument (R: ``length(formals(rule)) == 2``)."""
    try:
        return len(inspect.signature(rule).parameters) == 2
    except (TypeError, ValueError):
        return False


def _box_label(v: float | None, digits: int | None, format_type: str, suffix: str) -> str:
    # sdvplotR's indicator boxes round before scaling a percent (the pills scale first)
    if v is not None and digits is not None:
        v = round(v, digits)
    if v is not None and format_type == "percent":
        v *= 100
    return _format_value(v, digits, format_type, suffix)


def gt_indicator_boxes(
    gt: GT,
    columns: Any = None,
    key_columns: Any = None,
    indicator_vals: Sequence[float] = (0, 1),
    indicator_rule: Callable[..., Any] | None = None,
    color_yes: str = "#FCCF10",
    color_no: str = "#EEEEEE",
    show_na_as_na: bool = False,
    show_text: bool = False,
    show_only: str | None = None,
    per_column_formats: dict[str, dict[str, Any]] | None = None,
    color_na: str | None = None,
    border_color: str | None = None,
    border_width: float = 0.25,
    box_width: float = 20,
    box_height: float = 20,
    text_size: float = 12,
    text_weight: str = "bold",
) -> GT:
    """Replace values with colored boxes: filled when a value meets a rule, neutral otherwise.

    By default a box is filled when its value equals ``indicator_vals[1]``. Name the columns to convert with
    ``columns``, or the ones to leave alone with ``key_columns`` (not both); with neither, every body column is
    converted. Values are read as numbers, so text becomes missing. Converted columns are centered.

    Args:
        gt: The table.
        columns: The columns to convert.
        key_columns: The columns to leave alone (every other body column is converted).
        indicator_vals: The ``(no, yes)`` values.
        indicator_rule: A function deciding when a box is filled, called with each cell's numeric value (and the
            column name, when it takes two arguments); ``None`` tests equality with ``indicator_vals[1]``.
        color_yes: Fill of boxes meeting the rule (hex).
        color_no: Fill of the others (hex).
        show_na_as_na: Print ``NA`` in a missing value's box instead of leaving it blank.
        show_text: Print the formatted value inside each box (boxes then widen to fit).
        show_only: Print text in only one class of box: ``"yes"``, ``"no"`` or ``"NA"``; ``None`` prints all.
        per_column_formats: ``{column: {"digits": ..., "format_type": ..., "suffix": ...}}``.
        color_na: Fill of missing values' boxes (hex); ``None`` uses ``color_no``.
        border_color: A border color around each box; ``None`` for none.
        border_width: The border width in pixels.
        box_width: Box width in pixels when ``show_text`` is off.
        box_height: Box height in pixels.
        text_size: Box text size in pixels.
        text_weight: Box text weight.

    Returns:
        GT: A new table with the columns shown as boxes.

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: Both ``columns`` and ``key_columns`` were given, no column is left to convert, or
            ``show_only`` is unknown.

    Example:
        ::

            gt_indicator_boxes(GT(roster), key_columns="player", show_text=True, border_color="#333333")

    See Also:
        Ported from sdvplotR ``gt_indicator_boxes()``.
    """
    _check_gt(gt)
    if columns is not None and key_columns is not None:
        raise ValueError(
            "give either columns (the columns to convert to boxes) or key_columns (the ones to leave alone), not both"
        )
    if show_only not in (None, "yes", "no", "NA"):
        raise ValueError(f'show_only must be None, "yes", "no" or "NA", got {show_only!r}')
    if columns is not None:
        cols = _columns(gt, columns)
    else:
        keys = set(_columns(gt, key_columns)) if key_columns is not None else set()
        cols = [c for c in _columns(gt, None) if c not in keys]
    if not cols:
        raise ValueError("no columns left to convert to boxes")
    yes_value = indicator_vals[1]
    rule: Callable[..., Any] = indicator_rule if indicator_rule is not None else (lambda x: x == yes_value)
    with_column = _takes_column(rule)
    na_fill = color_na or color_no
    border = f"border: {border_width}px solid {border_color};" if border_color is not None else ""

    out = gt
    for c in cols:
        spec = (per_column_formats or {}).get(c, {})
        digits, format_type, suffix = spec.get("digits"), spec.get("format_type", "number"), spec.get("suffix", "")
        numbers = [_number(v) for v in _values(gt, c)]
        labels = [_box_label(x, digits, format_type, suffix) for x in numbers]
        width = max((len(s) for s in labels), default=0) * 10 if show_text else box_width
        cells: dict[int, str] = {}
        for i, (x, text) in enumerate(zip(numbers, labels, strict=True)):
            if x is None:
                color = na_fill
            else:
                hit = rule(x, c) if with_column else rule(x)
                color = color_yes if _flags([hit])[0] else color_no
            if not show_text:
                content = ""
            elif show_only == "yes":
                content = text if color == color_yes else ""
            elif show_only == "no":
                content = text if color == color_no else ""
            elif show_only == "NA":
                content = "NA" if x is None and show_na_as_na else ""
            else:
                content = "" if x is None and not show_na_as_na else text
            cells[i] = (
                f"<span style='display:inline-block; width:{width}px; height:{box_height}px; "
                f"line-height:{box_height}px; background-color: {color}; color: {on_color(color)}; "
                f"vertical-align:middle; margin:4px 1px; font-size: {text_size}px; font-weight: {text_weight}; "
                f"text-align:center; {border}'>{content}</span>"
            )
        out = _fmt_rows(out, c, cells)
    return out.cols_align(align="center", columns=cols)


# ---------------------------------------------------------------------------------------------------------------------
# formatting, computed columns and stacked labels


def _ordinal_suffix(n: float) -> str:
    n = abs(n)
    if n % 10 == 1 and n % 100 != 11:
        return "st"
    if n % 10 == 2 and n % 100 != 12:
        return "nd"
    if n % 10 == 3 and n % 100 != 13:
        return "rd"
    return "th"


def gt_fmt_rank(gt: GT, columns: Any, superscript: bool = True, suffix_size: str = "0.7em") -> GT:
    """Format numbers as ordinals: 1 becomes 1st, 2 becomes 2nd, 23 becomes 23rd, 11-13 take "th".

    Applied to the rendered cell text; a cell that does not read as a number is left alone.

    Args:
        gt: The table.
        columns: The columns to format.
        superscript: Render the suffix as superscript.
        suffix_size: The suffix size, as a CSS size.

    Returns:
        GT: A new table with ordinal formatting.

    Raises:
        TypeError: ``gt`` is not a ``GT``.

    Example:
        ::

            gt_fmt_rank(GT(standings), "place", superscript=False)

    See Also:
        Ported from sdvplotR ``gt_fmt_rank()``.
    """
    _check_gt(gt)

    def ordinal(text: str) -> str:
        n = _number(text)
        if n is None:
            return text
        shown, suffix = _natural(n), _ordinal_suffix(n)
        return f"{shown}<sup style='font-size:{suffix_size};'>{suffix}</sup>" if superscript else f"{shown}{suffix}"

    return gt.text_transform(locations=loc.body(columns=columns), fn=ordinal)


def gt_fmt_tally(
    gt: GT,
    columns: Any,
    separator: str = "-",
    label: str | None = None,
    share: bool = False,
    share_of: int | str = 0,
    share_location: str = "inline",
    share_decimals: int = 1,
    share_label: str = "%",
    share_prefix: str = " (",
    share_suffix: str = ")",
    **fmt_percent_kwargs: Any,
) -> GT:
    """Combine two or more count columns into one ``"32-5"`` cell, optionally with one count's share of the total.

    The tally goes in the first column and the others are hidden (or the last one carries the share). A row with a
    missing count is left alone, and the share is blank where the counts sum to zero.

    Args:
        gt: The table.
        columns: The count columns, in reading order (two or more).
        separator: Placed between the counts.
        label: A new label for the combined column; ``None`` keeps its label.
        share: Show one count as a share of the row total.
        share_of: The count the share is computed for: a 0-based position in ``columns`` or a column name.
        share_location: ``"inline"`` (appended to the tally) or ``"column"`` (the last count column carries it).
        share_decimals: Decimal places of the share.
        share_label: The share column's label when ``share_location="column"``.
        share_prefix: Placed before an inline share.
        share_suffix: Placed after an inline share.
        **fmt_percent_kwargs: Passed to great_tables ``vals.fmt_percent``.

    Returns:
        GT: A new table with the counts combined.

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: Fewer than two columns, ``share_of`` is not one of them, or ``share_location`` is unknown.

    Example:
        ::

            gt_fmt_tally(GT(suites), ["passed", "failed"], share=True)          # "142-8 (94.7%)"
            gt_fmt_tally(GT(league), ["w", "d", "l"], label="W-D-L")

    See Also:
        Ported from sdvplotR ``gt_fmt_tally()``.
    """
    _check_gt(gt)
    if share_location not in ("inline", "column"):
        raise ValueError(f'share_location must be "inline" or "column", got {share_location!r}')
    cols = _columns(gt, columns)
    if len(cols) < 2:
        raise ValueError("columns must select at least two columns")
    rows = list(zip(*([_number(v) for v in _values(gt, c)] for c in cols), strict=True))
    complete = [None if any(v is None for v in r) else cast(tuple[float, ...], r) for r in rows]
    tally = [None if r is None else separator.join(_natural(v) for v in r) for r in complete]

    shares: list[str | None] = [None] * len(rows)
    if share:
        pos = cols.index(share_of) if isinstance(share_of, str) and share_of in cols else share_of
        if not isinstance(pos, int) or not 0 <= pos < len(cols):
            raise ValueError(f"share_of must name or index (from 0) one of {cols}")
        props = {i: r[pos] / sum(r) for i, r in enumerate(complete) if r is not None and sum(r) != 0}
        props = {i: p for i, p in props.items() if math.isfinite(p)}
        if props:
            text = cast(
                list[str], vals.fmt_percent(list(props.values()), decimals=share_decimals, **fmt_percent_kwargs)
            )
            for i, s in zip(props, text, strict=True):
                shares[i] = s

    inline = share and share_location == "inline"
    display = [
        f"{t}{share_prefix}{s}{share_suffix}" if inline and t is not None and s is not None else t
        for t, s in zip(tally, shares, strict=True)
    ]
    out = _fmt_rows(gt, cols[0], {i: t for i, t in enumerate(display) if t is not None})
    if share and share_location == "column":
        carrier = cols[-1]
        out = _fmt_rows(out, carrier, {i: s for i, s in enumerate(shares) if s is not None})
        out = out.cols_label(cases={carrier: share_label})
        spent = cols[1:-1]
    else:
        spent = cols[1:]
    if spent:
        out = out.cols_hide(columns=spent)
    if label is not None:
        out = out.cols_label(cases={cols[0]: label})
    return out


def _add_column(gt: GT, name: str, values: list[str], after: str) -> GT:
    """Add a text column placed after ``after``.

    great_tables 1.0 has no ``cols_add``, so this extends the GT's data, empty body and boxhead (private
    attributes, pinned by a test). Formats, styles and labels on the other columns are kept.
    """
    frame = _frame(gt)
    column = nw.new_series(name, values, nw.String(), backend=nw.get_native_namespace(frame))
    data = frame.with_columns(column).to_native()
    boxhead = list(gt._boxhead)
    boxhead.insert([c.var for c in boxhead].index(after) + 1, ColInfo(name))
    return gt._replace(_tbl_data=data, _body=Body.from_empty(data), _boxhead=Boxhead(boxhead))


def gt_delta(
    gt: GT,
    from_: Any,
    to: Any,
    column_label: str = "Change",
    percent: bool = False,
    decimals: int = 1,
    arrows: bool = False,
    color: bool = True,
    color_positive: str = "#1B7837",
    color_negative: str = "#B2182B",
    color_neutral: str | None = None,
    force_sign: bool = True,
    after: int | str | None = None,
) -> GT:
    """Add a column holding the change from one numeric column to another, signed and colored by direction.

    The change is ``to - from_`` (or that over ``from_`` with ``percent=True``). A row is blank where either value
    is missing, or a percent change divides by zero. With ``arrows`` a triangle leads the magnitude in place of a
    sign.

    Args:
        gt: The table.
        from_: The starting column (``from`` is a Python keyword).
        to: The ending column.
        column_label: The new column's label.
        percent: Show the change as a percent of ``from_``.
        decimals: Decimal places.
        arrows: Lead each value with an up or down triangle instead of a sign.
        color: Color the values by direction.
        color_positive: Color of an increase.
        color_negative: Color of a decrease.
        color_neutral: Color of no change; ``None`` leaves it the table's text color.
        force_sign: Show a plus on an increase (ignored with ``arrows``).
        after: The column the new one follows, a name or a 0-based position in the data; ``None`` places it
            after ``to``.

    Returns:
        GT: A new table with the change column (right-aligned).

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: ``from_`` or ``to`` does not select a single column, or ``after`` names no column.

    Example:
        ::

            gt_delta(GT(revenue), "q1", "q2")
            gt_delta(GT(revenue), "q1", "q2", percent=True, arrows=True)

    See Also:
        Ported from sdvplotR ``gt_delta()``.
    """
    _check_gt(gt)
    start, end = _columns(gt, from_), _columns(gt, to)
    if len(start) != 1 or len(end) != 1:
        raise ValueError("from_ and to must each select a single column")
    names = list(_frame(gt).columns)
    if after is None:
        anchor = end[0]
    elif isinstance(after, str) and after in names:
        anchor = after
    elif isinstance(after, int) and not isinstance(after, bool) and -len(names) <= after < len(names):
        anchor = names[after]
    else:
        raise ValueError(f"after must name or index (from 0) one of {names}, got {after!r}")

    delta: list[float | None] = []
    for a, b in zip(_values(gt, start[0]), _values(gt, end[0]), strict=True):
        x, y = _number(a), _number(b)
        if x is None or y is None:
            d = None
        elif percent:
            d = (y - x) / x if x != 0 else None
        else:
            d = y - x
        delta.append(d if d is None or math.isfinite(d) else None)

    present = [abs(d) if arrows else d for d in delta if d is not None]
    fmt = vals.fmt_percent if percent else vals.fmt_number
    texts = iter(cast(list[str], fmt(present, decimals=decimals, force_sign=force_sign and not arrows)))
    body = []
    for d in delta:
        if d is None:
            body.append("")
            continue
        text = next(texts)
        body.append(("▲ " if d > 0 else "▼ " if d < 0 else "") + text if arrows else text)

    new, k = column_label, 0
    while new in names:  # R's make.unique: Change, Change.1, Change.2, ...
        k += 1
        new = f"{column_label}.{k}"
    out = _add_column(gt, new, body, anchor)
    if new != column_label:
        out = out.cols_label(cases={new: column_label})
    out = out.cols_align(align="right", columns=new)
    if color:
        for rows, ink in (
            ([i for i, d in enumerate(delta) if d is not None and d > 0], color_positive),
            ([i for i, d in enumerate(delta) if d is not None and d < 0], color_negative),
            ([i for i, d in enumerate(delta) if d == 0], color_neutral),
        ):
            if rows and ink is not None:
                out = out.tab_style(style=style.text(color=ink), locations=loc.body(columns=new, rows=rows))
    return out


def gt_column_subheaders(
    gt: GT,
    heading_color: str = "black",
    subtitle_color: str = "#808080",
    heading_weight: str = "bold",
    subtitle_weight: str = "normal",
    heading_size: float = 14,
    subtitle_size: float = 10,
    font: str | None = None,
    **subheaders: dict[str, str],
) -> GT:
    """Replace every column label with a two-line header: a heading over a smaller subtitle.

    Every column is relabeled. A column not named in ``subheaders`` keeps its name as the heading and gets a
    non-breaking space as the subtitle, so the headers stay aligned. Call it after other label changes.

    Args:
        gt: The table.
        heading_color: Heading text color.
        subtitle_color: Subtitle text color.
        heading_weight: Heading font weight.
        subtitle_weight: Subtitle font weight.
        heading_size: Heading size in pixels.
        subtitle_size: Subtitle size in pixels.
        font: A CSS font family for both lines (not imported: it must be installed or loaded by the theme).
        **subheaders: ``column={"heading": ..., "subtitle": ...}`` per column (either key may be left out). A
            column named like one of this function's arguments cannot be given this way.

    Returns:
        GT: A new table with stacked labels.

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: A ``subheaders`` key is not a column of the table.

    Example:
        ::

            gt_column_subheaders(GT(df), hp={"heading": "Horsepower", "subtitle": "HP"}, heading_color="blue")

    See Also:
        Ported from sdvplotR ``gt_column_subheaders()``.
    """
    _check_gt(gt)
    names = list(_frame(gt).columns)
    unknown = sorted(set(subheaders) - set(names))
    if unknown:
        raise ValueError(f"subheaders name columns the table does not have: {unknown}")
    # the style attributes are single-quoted, so the family's quotes go in as &quot; (R's '{font}' ends them early)
    font_css = f"font-family: &quot;{escape(font)}&quot;;" if font is not None else ""
    labels: dict[str, Any] = {}
    for name in names:
        info = subheaders.get(name, {})
        labels[name] = html(
            "<div style='line-height: 1.05; margin-bottom: -2px;'>"
            f"<span style='font-size: {heading_size}px; font-weight: {heading_weight}; color: {heading_color}; "
            f"{font_css}'>{info.get('heading', name)}</span><br>"
            f"<span style='font-size: {subtitle_size}px; font-weight: {subtitle_weight}; color: {subtitle_color}; "
            f"{font_css}'>{info.get('subtitle', '&nbsp;')}</span></div>"
        )
    return gt.cols_label(cases=labels)

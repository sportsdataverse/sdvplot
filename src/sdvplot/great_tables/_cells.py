"""sdvplotR's cell styling and formatting helpers for great_tables (wave C1).

Each function ports the sdvplotR function of the same name. Rows are great_tables row selections: 0-based
positions, a polars expression (polars data) or a callable that takes the data and returns a boolean Series
(pandas data). Columns are anything great_tables accepts as a column selection. Divergences from R are listed in
``docs/PARITY_TABLES.md``.
"""

from __future__ import annotations

import re
import warnings
from collections.abc import Callable, Sequence
from typing import Any, cast
from urllib.parse import quote

import narwhals as nw
from great_tables import GT, google_font, html, loc, md, random_id, style
from great_tables._locations import resolve_cols_c, resolve_rows_i
from great_tables._text import _process_text

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
            dark theme), else a neutral gray.
        rule_width: The rule width in pixels.
        size: The top caption's font size in pixels.
        align: The bottom caption's alignment.

    Returns:
        GT: A new table with the captions.

    Raises:
        TypeError: ``gt`` is not a ``GT``.
        ValueError: Neither caption was given.

    Example:
        ::

            gt_538_caption(GT(df), top_caption="Fuel economy and power", bottom_caption="Source: *Motor Trend*")

    See Also:
        Ported from sdvplotR ``gt_538_caption()``.
    """
    _check_gt(gt)
    if top_caption is None and bottom_caption is None:
        raise ValueError("nothing to caption: pass top_caption (above the rule), bottom_caption (below it), or both")
    if rule_color is None:
        found = re.search(r"color:\s(#[0-9A-Fa-f]{6})", gt.as_raw_html())
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
    colors = [colors] if isinstance(colors, str) else list(colors)
    align = _BAR_ALIGN.get(a["bar_align"], _BAR_ALIGN["center"])
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
    subtitle = cast(Any, heading.subtitle)  # typed BaseText on GTData, Text on tab_header
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
            first. One number or several.
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
        ValueError: ``after`` is not numeric, ``gap`` is not one or two non-negative numbers, or
            ``label_position`` is unknown.

    Example:
        ::

            gt_cutline(GT(standings), after=6, label="Playoff line")

    See Also:
        Ported from sdvplotR ``gt_cutline()``.
    """
    _check_gt(gt)
    if label_position not in ("below", "above"):
        raise ValueError(f'label_position must be "below" or "above", got {label_position!r}')
    afters = [after] if isinstance(after, int | float) else list(after)
    if not afters:
        return gt
    if not all(isinstance(a, int | float) and not isinstance(a, bool) for a in afters):
        raise ValueError("after must be numeric row numbers")
    gaps = [gap] if isinstance(gap, int | float) else list(gap)
    if not 1 <= len(gaps) <= 2 or any(not isinstance(g, int | float) or g < 0 for g in gaps):
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

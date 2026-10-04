"""sdvplotR's cell styling and formatting helpers for great_tables (wave C1).

Each function ports the sdvplotR function of the same name. Rows are great_tables row selections: 0-based
positions, a polars expression (polars data) or a callable that takes the data and returns a boolean Series
(pandas data). Columns are anything great_tables accepts as a column selection. Divergences from R are listed in
``docs/PARITY_TABLES.md``.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable, Sequence
from typing import Any

import narwhals as nw
from great_tables import GT, loc, style
from great_tables._locations import resolve_cols_c, resolve_rows_i

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

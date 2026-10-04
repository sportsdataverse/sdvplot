"""Team marks and team identity in great_tables: ports of sdvplotR's R/gt_sdv.R and R/gt_theme_sdv.R."""

from __future__ import annotations

import html
from collections.abc import Callable
from typing import Any

import narwhals as nw
from great_tables import GT, loc
from great_tables import html as gt_html

from sdvplot._colors import team_colors
from sdvplot._placement import KINDS, _missing
from sdvplot._tables import check_px, mark_html


def _check_gt(gt: Any) -> None:
    if not isinstance(gt, GT):
        hint = "wrap the data in great_tables.GT() first" if hasattr(gt, "columns") else "build a table with GT()"
        raise TypeError(f"gt must be a great_tables GT, not {type(gt).__name__}: {hint}")


def _cell_texts(gt: GT, locations: Any) -> list[str]:
    """The distinct texts great_tables hands a text_transform at ``locations``, read by rendering once."""
    seen: list[str] = []

    def record(text: str) -> str:
        seen.append(text)
        return text

    gt.text_transform(locations, record).as_raw_html()
    return list(dict.fromkeys(seen))


def _image_cells(
    gt: GT,
    columns: Any,
    locations: Any,
    *,
    kind: str,
    league: str,
    height: Any,
    season: Any = None,
    include_name: bool = False,
    id_system: str = "auto",
) -> GT:
    """Cells at ``locations`` (default: the body of ``columns``) whose text resolves become their mark's <img>.

    Resolution happens here, at call time, so unknown values warn once now rather than at every render (spec T4).
    great_tables passes cells as escaped HTML text ("A&amp;M"), so values are unescaped before resolving.
    """
    _check_gt(gt)
    h = check_px(height)
    locs = loc.body(columns) if locations is None else locations
    texts = _cell_texts(gt, locs)
    imgs = mark_html([html.unescape(t) for t in texts], league=league, kind=kind, height=h, season=season,
                     include_name=include_name, id_system=id_system)  # fmt: skip
    lookup = {t: img + (t if include_name else "") for t, img in zip(texts, imgs, strict=True) if img is not None}
    return gt.text_transform(locs, lambda text: lookup.get(text, text))


def gt_sdv_logos(
    gt: GT,
    columns: Any,
    *,
    league: str,
    height: Any = 30,
    locations: Any = None,
    include_name: bool = False,
    season: Any = None,
) -> GT:
    """Show each cell's team as its logo in a great_tables table.

    Values are resolved when you call this (team abbreviations, names and provider ids, as in ``resolve()``), so
    unknown values warn once, now. They keep their text. The cell text is read as it renders now, so apply any
    ``fmt_*`` to the same column before this.

    Args:
        gt: A great_tables ``GT``.
        columns: The columns whose body cells become logos: a name, a list of names, or a polars selector. Ignored when
            ``locations`` is given (pass None).
        league: The SDV league key, e.g. "nfl".
        height: The image height in pixels.
        locations: Any great_tables location instead of the body of ``columns``, e.g. ``loc.stub()`` or
            ``loc.row_groups()``.
        include_name: Keep the cell's text after the logo.
        season: One season whose marks every cell shows (the ending year for the NHL, NBA, MBB and WBB); None for
            today's.

    Returns:
        GT: A new table; ``gt`` is unchanged.

    Raises:
        TypeError: If ``gt`` is not a great_tables GT.
        ValueError: If ``height`` is not a positive number of pixels, or ``season`` is not one year.

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_sdv_logos

            gt_sdv_logos(GT(df), "team", league="nfl", height=24)

    See Also:
        Ported from sdvplotR ``gt_sdv_logos()``: https://sdvplotR.sportsdataverse.org/reference/gt_sdv_logos.html ;
        great_tables: https://posit-dev.github.io/great-tables/
    """
    return _image_cells(gt, columns, locations, kind="logo", league=league, height=height, season=season,
                        include_name=include_name)  # fmt: skip


def gt_sdv_wordmarks(
    gt: GT, columns: Any, *, league: str, height: Any = 30, locations: Any = None, season: Any = None
) -> GT:
    """Show each cell's team as its wordmark in a great_tables table.

    Args:
        gt: A great_tables ``GT``.
        columns: The columns whose body cells become wordmarks. Ignored when ``locations`` is given (pass None).
        league: The SDV league key, e.g. "nfl".
        height: The image height in pixels.
        locations: Any great_tables location instead of the body of ``columns``.
        season: One season whose marks every cell shows; None for today's.

    Returns:
        GT: A new table; unknown values keep their text, with one SdvplotWarning now.

    Raises:
        TypeError: If ``gt`` is not a great_tables GT.
        ValueError: If ``height`` is not a positive number of pixels, or ``season`` is not one year.

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_sdv_wordmarks

            gt_sdv_wordmarks(GT(df), "team", league="nfl")

    See Also:
        Ported from sdvplotR ``gt_sdv_wordmarks()``: https://sdvplotR.sportsdataverse.org/reference/gt_sdv_wordmarks.html
    """
    return _image_cells(gt, columns, locations, kind="wordmark", league=league, height=height, season=season)


def gt_sdv_headshots(
    gt: GT, columns: Any, *, league: str, height: Any = 30, locations: Any = None, id_system: str = "espn"
) -> GT:
    """Show each cell's player id as the player's headshot in a great_tables table.

    Args:
        gt: A great_tables ``GT``.
        columns: The columns of player ids. Ignored when ``locations`` is given (pass None).
        league: The SDV league key, e.g. "nfl".
        height: The image height in pixels.
        locations: Any great_tables location instead of the body of ``columns``.
        id_system: "espn" (ESPN athlete ids, any ESPN league) or "gsis" (NFL), as in ``headshot_url``.

    Returns:
        GT: A new table; ids without a headshot keep their text, with one SdvplotWarning now.

    Raises:
        TypeError: If ``gt`` is not a great_tables GT.
        ValueError: If ``height`` is not a positive number of pixels.

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_sdv_headshots

            gt_sdv_headshots(GT(df), "espn_id", league="nfl", height=40)

    See Also:
        Ported from sdvplotR ``gt_sdv_headshots()``: https://sdvplotR.sportsdataverse.org/reference/gt_sdv_headshots.html
    """
    return _image_cells(gt, columns, locations, kind="headshot", league=league, height=height, id_system=id_system)


def gt_sdv_cols_label(
    gt: GT,
    columns: Any = None,
    *,
    league: str,
    height: Any = 30,
    season: Any = None,
    mark_type: str = "logo",
    id_system: str = "espn",
) -> GT:
    """Replace the labels of team-named columns (a ``KC`` column, a ``BUF`` column, ...) with their marks.

    Args:
        gt: A great_tables ``GT``.
        columns: The columns whose labels to replace: a name, a list, a polars selector, or None for every column.
            The column *names* are resolved (not labels set earlier with ``cols_label``).
        league: The SDV league key, e.g. "nfl".
        height: The image height in pixels.
        season: One season whose marks to show; None for today's.
        mark_type: "logo", "wordmark", or "headshot" (the column names are player ids).
        id_system: For ``mark_type="headshot"``: "espn" or "gsis", as in ``headshot_url``.

    Returns:
        GT: A new table; columns whose names do not resolve keep their labels, with one SdvplotWarning now.

    Raises:
        TypeError: If ``gt`` is not a great_tables GT.
        ValueError: If ``height`` is not a positive number of pixels, ``mark_type`` is unknown, or ``season`` is not
            one year.

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_sdv_cols_label

            gt_sdv_cols_label(GT(df), ["KC", "BUF", "SF"], league="nfl")

    See Also:
        Ported from sdvplotR ``gt_sdv_cols_label()``: https://sdvplotR.sportsdataverse.org/reference/gt_sdv_cols_label.html
    """
    _check_gt(gt)
    h = check_px(height)
    if mark_type not in KINDS:
        raise ValueError(f"mark_type must be one of {KINDS}, got {mark_type!r}")
    names: list[str] = []

    def record(name: str) -> str:
        names.append(name)
        return name

    gt.cols_label_with(columns=columns, fn=record)  # great_tables' own column selection; the result is discarded
    imgs = mark_html(names, league=league, kind=mark_type, height=h, season=season,
                     id_system=id_system if mark_type == "headshot" else "auto")  # fmt: skip
    cases: dict[str, Any] = {n: gt_html(img) for n, img in zip(names, imgs, strict=True) if img is not None}
    return gt.cols_label(cases=cases) if cases else gt


def _constant(value: str) -> Callable[[Any], str]:
    return lambda _: value


def _text(value: Any) -> str:
    return "" if _missing(value) else html.escape(str(value))


def gt_merge_stack_team_color(
    gt: GT,
    col1: str,
    col2: str,
    team_col: str,
    *,
    league: str,
    font_size_top: float = 14,
    font_size_bottom: float = 12,
    color: str = "black",
) -> GT:
    """Stack ``col1`` over ``col2`` in one cell: the top in bold small caps, the bottom in the team's primary color.

    Args:
        gt: A great_tables ``GT``.
        col1: The column shown on top (bold small caps, in ``color``); it holds the merged cell.
        col2: The column shown below, smaller and in the row's team color; it is hidden.
        team_col: The column of teams whose primary colors color the bottom line.
        league: The SDV league key, e.g. "nfl".
        font_size_top: The top line's font size in pixels.
        font_size_bottom: The bottom line's font size in pixels.
        color: The top line's CSS color.

    Returns:
        GT: A new table. A team that does not resolve, or has no color, gets grey, with one SdvplotWarning.

    Raises:
        TypeError: If ``gt`` is not a great_tables GT.
        ValueError: If ``col1``, ``col2`` or ``team_col`` is not a column of the table's data.

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_merge_stack_team_color

            gt_merge_stack_team_color(GT(df), "team", "mascot", "team", league="nfl")

    See Also:
        Ported from sdvplotR ``gt_merge_stack_team_color()``:
        https://sdvplotR.sportsdataverse.org/reference/gt_merge_stack_team_color.html
    """
    _check_gt(gt)
    frame = nw.from_native(gt._tbl_data, eager_only=True)  # the GT's own data, positional (spec T4)
    for name in (col1, col2, team_col):
        if name not in frame.columns:
            raise ValueError(f"{name!r} is not a column of the table's data; columns are {frame.columns}")
    colors = team_colors(frame[team_col].to_list(), league)
    top_style = f"font-weight:bold;font-variant:small-caps;color:{color};font-size:{font_size_top}px"
    for row, (top, bottom, team_color) in enumerate(
        zip(frame[col1].to_list(), frame[col2].to_list(), colors, strict=True)
    ):
        cell = (
            f"<div style='line-height:{font_size_top - 2}px'><span style='{top_style}'>{_text(top)}</span></div>\n"
            f"<div style='line-height:{font_size_bottom - 2}px'><span style='font-weight:bold;"
            f"color:{team_color or 'grey'};font-size:{font_size_bottom}px'>{_text(bottom)}</span></div>"
        )
        # fmt() takes data rows, so row groups (which reorder the display) cannot shuffle the pairs
        # one fmt() per row keeps it simple; group identical cells into one call if long tables get slow
        gt = gt.fmt(_constant(cell), columns=col1, rows=[row])
    return gt.cols_hide(col2)

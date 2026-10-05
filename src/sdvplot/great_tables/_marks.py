"""Team marks and team identity in great_tables: ports of sdvplotR's R/gt_sdv.R and R/gt_theme_sdv.R."""

from __future__ import annotations

import copy
import html
import warnings
from collections.abc import Callable
from typing import Any

import narwhals as nw
from great_tables import GT, google_font, loc, px, random_id, style
from great_tables import html as gt_html

from sdvplot._colors import team_colors
from sdvplot._contrast import contrast, mix, on_color, solid
from sdvplot._errors import SdvplotWarning
from sdvplot._placement import KINDS, _missing
from sdvplot._resolve import one_team, resolve
from sdvplot._tables import check_px, mark_html


def _check_gt(gt: Any, arg: str = "gt") -> GT:
    """sdvplotR's ``.check_gt``: every public table function takes a GT, never raw data; returns ``gt``."""
    if isinstance(gt, GT):
        return gt
    if hasattr(gt, "columns"):
        hint = "It looks like raw data: wrap it in great_tables.GT() first."
    else:
        hint = "Build a table with great_tables.GT() and pass that in."
    raise TypeError(f"{arg} must be a great_tables GT, not {type(gt).__name__}. {hint}")


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
    for where in locs if isinstance(locs, list) else [locs]:
        # the locations great_tables' text_transform reaches; it escapes column labels and ignores every other one
        if not isinstance(where, (loc.body, loc.stub, loc.row_groups)):
            hint = (
                "; for marks in the column labels use gt_sdv_cols_label()"
                if isinstance(where, loc.column_labels)
                else ""
            )
            raise ValueError(
                "locations must be loc.body(), loc.stub() or loc.row_groups(), or a list of them, "
                f"not {type(where).__name__}{hint}"
            )
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
        locations: Instead of the body of ``columns``: ``loc.body()``, ``loc.stub()`` or ``loc.row_groups()``, or a
            list of them (the locations great_tables' ``text_transform`` reaches). For marks in the column labels,
            use ``gt_sdv_cols_label``.
        include_name: Keep the cell's text after the logo.
        season: One season whose marks every cell shows (the ending year for the NHL, NBA, MBB and WBB); None for
            today's.

    Returns:
        GT: A new table; ``gt`` is unchanged.

    Raises:
        TypeError: If ``gt`` is not a great_tables GT.
        ValueError: If ``height`` is not a number of pixels of at least 1, ``season`` is not one year, or ``locations``
            holds another location.

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
        locations: Instead of the body of ``columns``: ``loc.body()``, ``loc.stub()`` or ``loc.row_groups()``, or a
            list of them (the locations great_tables' ``text_transform`` reaches). For marks in the column labels,
            use ``gt_sdv_cols_label``.
        season: One season whose marks every cell shows; None for today's.

    Returns:
        GT: A new table; unknown values keep their text, with one SdvplotWarning now.

    Raises:
        TypeError: If ``gt`` is not a great_tables GT.
        ValueError: If ``height`` is not a number of pixels of at least 1, ``season`` is not one year, or ``locations``
            holds another location.

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
        locations: Instead of the body of ``columns``: ``loc.body()``, ``loc.stub()`` or ``loc.row_groups()``, or a
            list of them (the locations great_tables' ``text_transform`` reaches). For marks in the column labels,
            use ``gt_sdv_cols_label``.
        id_system: "espn" (ESPN athlete ids, any ESPN league) or "gsis" (NFL), as in ``headshot_url``.

    Returns:
        GT: A new table; ids without a headshot keep their text, with one SdvplotWarning now.

    Raises:
        TypeError: If ``gt`` is not a great_tables GT.
        ValueError: If ``height`` is not a number of pixels of at least 1, or ``locations`` holds another location.

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
        ValueError: If ``height`` is not a number of pixels of at least 1, ``mark_type`` is unknown, or ``season``
            is not one year.

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
    """A great_tables ``fmt`` function that ignores the cell and returns ``value`` (sdvplotR's ``.constant``)."""
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
    colors = team_colors(league, frame[team_col].to_list())
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


# --- themes (R/gt_theme_sdv.R) ---

DENSITY: dict[str, dict[str, int]] = {  # sdvplotR's .theme_density(): type sizes and row padding per density
    "comfortable": {"body": 14, "pad": 6, "title": 26, "subtitle": 15, "label": 10, "group": 11, "source": 11},
    "compact": {"body": 12, "pad": 3, "title": 22, "subtitle": 13, "label": 9, "group": 10, "source": 10},
    "social": {"body": 17, "pad": 9, "title": 34, "subtitle": 19, "label": 12, "group": 13, "source": 13},
}


def _density(density: str) -> dict[str, int]:
    """The type and padding scale of ``density``; ValueError for an unknown one."""
    if density not in DENSITY:
        raise ValueError(f"density must be 'comfortable', 'compact' or 'social', not {density!r}")
    return DENSITY[density]


# gt::default_fonts() (gt 1.3.0): the fallback stack R puts under every theme font
R_FONTS = (
    "system-ui",
    "Segoe UI",
    "Roboto",
    "Helvetica",
    "Arial",
    "sans-serif",
    "Apple Color Emoji",
    "Segoe UI Emoji",
    "Segoe UI Symbol",
    "Noto Color Emoji",
)


def _record(gt: GT, name: str, value: Any) -> GT:
    """A copy of ``gt`` carrying ``value`` as attribute ``name`` (``_sdvplot_scale``, ``_sdvplot_key``,
    ``_sdvplot_theme_fonts``); great_tables' own methods copy it along."""
    out = copy.copy(gt)
    out.__dict__[name] = value
    return out


def _table_font(gt: GT, font: Any, weight: Any = None) -> GT:
    """R's ``opt_table_font(font = list(google_font(x), default_fonts()))`` for a theme's ``font`` (a GoogleFont).

    As in R, the theme's fonts go in front of the table's, so fonts the caller set stay behind them (a browser falls
    back font by font for each character it cannot draw, which is why gt lists emoji fonts after ``sans-serif``).
    Unlike R, the run of fonts an earlier sdvplot theme put in front (recorded as ``_sdvplot_theme_fonts``) is taken
    out first, so re-theming swaps it instead of stacking. great_tables writes each font once in the CSS.
    """
    ours = [font.get_font_name(), *R_FONTS]
    fonts = list(gt._options.table_font_names.value)
    earlier = list(gt.__dict__.get("_sdvplot_theme_fonts", ()))
    at = next(
        (i for i in range(len(fonts) - len(earlier) + 1) if earlier and fonts[i : i + len(earlier)] == earlier), None
    )
    if at is not None:  # still in the list (fonts the caller added since sit around it, untouched)
        del fonts[at : at + len(earlier)]
    out = gt.opt_table_font(font=[font, *R_FONTS, *fonts], add=False, weight=weight)
    return _record(out, "_sdvplot_theme_fonts", ours)


# great_tables' default paddings that sdvplotR's density also scales (gt has the same defaults)
_DEFAULT_PADDING = {
    "row_group_padding": 8,
    "source_notes_padding": 4,
    "summary_row_padding": 8,
    "grand_summary_row_padding": 8,
}
SDV_NAVY, SDV_CYAN = "#0B1A33", "#7FE6DC"
SDV_HORIZON = "linear-gradient(90deg, #3346F0, #7FE6DC)"


def important(*styles: Any) -> Any:
    """great_tables cell styles as one inline rule with every declaration ``!important``. The notebook repr marks
    great_tables' own cell rules ``!important`` (``td, th {border-style: none}``, the stub's and row groups'
    ``background-color``), and a stylesheet ``!important`` beats a plain inline style: without this, a border or fill
    shows in a saved image and not in Jupyter."""
    rule = "".join(s._to_html_style() for s in styles)
    return style.css(rule=" ".join(f"{d.strip()} !important;" for d in rule.split(";") if d.strip()))


def _table_id(gt: GT) -> tuple[GT, str]:
    """The table's id, so CSS can be scoped to ``#id``, assigning a random one when it has none or an empty one
    (sdvplotR's ``.table_id``; ``"#"`` alone would scope nothing)."""
    table_id = gt._options.table_id.value
    if table_id:
        return gt, str(table_id)
    table_id = random_id()
    return gt.with_id(table_id), table_id


def _light_palette(horizon: str) -> dict[str, str]:
    return {
        "bg": "#FFFFFF",
        "heading_bg": "#FFFFFF",
        "title": SDV_NAVY,
        "muted": "#4A5A75",
        "label": "#16305C",
        "text": SDV_NAVY,
        "rule": "#E3E8F1",
        "group_bg": "#EEF3FA",
        "horizon": horizon,
    }


def _dark_palette() -> dict[str, str]:
    return {
        "bg": SDV_NAVY,
        "heading_bg": SDV_NAVY,
        "title": "#FFFFFF",
        "muted": "#A9B8D0",
        "label": "#9CCBFF",
        "text": "#EAEBEC",
        "rule": "#1D3A66",
        "group_bg": "#16305C",
        "horizon": SDV_HORIZON,
    }


def _background(gt: GT) -> str:
    """The table background as ``#rrggbb``, a best-effort read for picking ink: a translucent hex shows over the
    (assumed white) page, so it is blended onto white; white when it is unset or not a hex color (a CSS name)."""
    try:
        return solid(str(gt._options.table_background_color.value))
    except ValueError:
        return "#ffffff"


def _secondary_on(bg: str, fg: str, target: float = 4.5) -> str:
    """sdvplotR's ``.theme_secondary_on()``: muted but legible, ``fg`` blended toward ``bg`` as far as still clears
    ``target`` contrast."""
    for i in range(12):
        # R's seq(0.45, 1, by = 0.05) is 0.45 + i * 0.05 unrounded (0.6000000000000001, ...): rounding the weight
        # flips a channel's rounding for some colors
        cand = mix(bg, fg, 0.45 + i * 0.05)
        if contrast(cand, bg) >= target:
            return cand
    return fg


def _build_theme(gt: GT, pal: dict[str, str], density: str, tab_options: dict[str, Any]) -> GT:
    """sdvplotR's .sdv_theme_build(): fonts, styles, options and the scoped CSS, at ``density``."""
    d = _density(density)
    k = {role: d[role] / DENSITY["comfortable"][role] for role in DENSITY["comfortable"]}

    def size(n: float, role: str) -> str:
        return f"{round(n * k[role], 1):g}px"

    gt, tid = _table_id(gt)
    chivo, lato = google_font("Chivo"), google_font("Lato")
    weight: Any = "800"  # CSS numeric weights; great_tables types only the keywords
    medium: Any = "500"
    gt = (
        _table_font(gt, lato)
        .tab_style(style.text(font=chivo, weight=weight, size=size(22, "title"), color=pal["title"]), loc.title())
        .tab_style(
            style.text(font=lato, size=size(14, "subtitle"), color=pal.get("subtitle", pal["muted"])), loc.subtitle()
        )
        .tab_style(
            style.text(font=chivo, weight=medium, size=size(13, "label"), color=pal["label"]), loc.column_labels()
        )
        .tab_style(
            [
                style.text(font=chivo, weight=medium, size=size(13, "group"), color=pal["label"]),
                important(style.fill(color=pal["group_bg"])),
            ],
            loc.row_groups(),
        )
        .tab_style(style.text(size=size(12, "source"), color=pal["muted"]), [loc.source_notes(), loc.footnotes()])
    )
    padding: dict[str, Any] = {}
    if density != "comfortable":  # sdvplotR scales great_tables' default paddings too
        padding = {option: size(v, "pad") for option, v in _DEFAULT_PADDING.items()}
    gt = gt.tab_options(
        table_background_color=pal["bg"],
        table_font_color=pal["text"],
        table_font_size=size(15, "body"),
        heading_align="left",
        heading_background_color=pal["heading_bg"],
        heading_padding=size(4, "pad"),
        heading_border_bottom_style="none",
        column_labels_background_color=pal["bg"],
        column_labels_border_top_style="none",
        column_labels_border_bottom_style="none",
        column_labels_padding=size(6, "pad"),
        table_body_hlines_color=pal["rule"],
        table_body_hlines_width=px(1),
        table_body_border_top_style="none",
        table_body_border_bottom_style="none",
        row_group_border_top_style="none",
        row_group_border_bottom_style="none",
        data_row_padding=size(7, "pad"),
        table_border_top_style="none",
        table_border_bottom_style="none",
        source_notes_border_bottom_style="none",  # great_tables 1.0 has no footnotes border options
        **padding,
    )
    s = f"#{tid}"
    css = [
        # the horizon: one line under the column labels, drawn over the thead so a gradient spans the whole table
        f"{s} thead {{position: relative;}}",
        f'{s} thead::after {{content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 4px; '
        f"background: {pal['horizon']};}}",
        f"{s} .gt_col_headings th {{padding-bottom: 10px;}}",
        # spanners as column labels (great_tables 1.0's loc.spanner_labels() needs explicit ids)
        f"{s} .gt_column_spanner {{font-family: Chivo, sans-serif; font-weight: 500; font-size: {size(13, 'label')}; "
        f"color: {pal['label']};}}",
        # one 14px inset shared by the heading, the outer columns and the notes
        f"{s} .gt_heading, {s} .gt_sourcenote, {s} .gt_footnote, {s} .gt_col_headings th:first-child, "
        f"{s} tbody td:first-child {{padding-left: 14px !important;}}",
        f"{s} .gt_heading, {s} .gt_sourcenote, {s} .gt_footnote, {s} .gt_col_headings th:last-child, "
        f"{s} tbody td:last-child {{padding-right: 14px !important;}}",
        f"{s} .gt_title {{padding-top: 12px !important;}}",
        f"{s} .gt_subtitle {{padding-bottom: 12px !important;}}",
        f"{s} tbody tr:last-child {{border-bottom: 2px solid {pal['bg']};}}",  # no double rule under the last row
        f"{s} td {{ font-variant-numeric: tabular-nums; }}",  # digits line up between rows
    ]
    gt = gt.opt_css("\n".join(css))
    return gt.tab_options(**tab_options) if tab_options else gt  # the caller's options last, so they win


def gt_theme_sdv(gt: GT, style: str = "light", density: str = "comfortable", **tab_options: Any) -> GT:
    """The SportsDataverse house table: Chivo labels, a Lato body, and the SDV gradient under the column labels.

    Args:
        gt: A great_tables ``GT``.
        style: "light" (a white table) or "dark" (the SportsDataverse navy).
        density: "comfortable" (as set), "compact" (smaller type and padding) or "social" (larger, for saved images).
        **tab_options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new, themed table. The gradient line is CSS (``thead::after``) scoped to the table's id; an id is
        assigned when the table has none.

    Raises:
        TypeError: If ``gt`` is not a great_tables GT.
        ValueError: If ``style`` or ``density`` is unknown.

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_sdv_logos, gt_theme_sdv

            gt_theme_sdv(gt_sdv_logos(GT(df), "team", league="nfl").tab_header("AFC West"))
            gt_theme_sdv(GT(df), style="dark", density="social")

    See Also:
        Ported from sdvplotR ``gt_theme_sdv()``: https://sdvplotR.sportsdataverse.org/reference/gt_theme_sdv.html
    """
    _check_gt(gt)
    if style not in ("light", "dark"):
        raise ValueError(f"style must be 'light' or 'dark', got {style!r}")
    pal = _dark_palette() if style == "dark" else _light_palette(SDV_HORIZON)
    return _build_theme(gt, pal, density, tab_options)


def gt_theme_sdv_team(gt: GT, team: Any = None, *, league: str, density: str = "comfortable", **tab_options: Any) -> GT:
    """``gt_theme_sdv`` in one team's colors: a title block in the primary color, the line in the secondary.

    Ink on the title block is black or white, whichever reads better, and the subtitle is blended toward it while it
    keeps 4.5:1 contrast. A secondary color too pale for a white table gives way to the primary for the line, and a
    primary too light to read on white gives way to the SportsDataverse navy for the column labels.

    Args:
        gt: A great_tables ``GT``.
        team: One team (an abbreviation, name or provider id); None for the SportsDataverse navy and cyan.
        league: The SDV league key, e.g. "nfl".
        density: "comfortable", "compact" or "social", as in ``gt_theme_sdv``.
        **tab_options: Passed to ``GT.tab_options`` last, so they override the theme.

    Returns:
        GT: A new, themed table. A team with no colors on file gets the SportsDataverse colors, with an
        SdvplotWarning.

    Raises:
        TypeError: If ``gt`` is not a great_tables GT, or ``team`` is not one value.
        UnresolvedTeamError: If ``team`` does not resolve to one team of ``league``.
        ValueError: If ``density`` is unknown.

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_theme_sdv_team

            gt_theme_sdv_team(GT(df).tab_header("Chiefs leaders"), "KC", league="nfl")

    See Also:
        Ported from sdvplotR ``gt_theme_sdv_team()``:
        https://sdvplotR.sportsdataverse.org/reference/gt_theme_sdv_team.html
    """
    _check_gt(gt)
    primary, secondary = SDV_NAVY, SDV_CYAN
    if team is not None:
        team_id = resolve(one_team(team, "gt_theme_sdv_team"), league, strict=True)
        p, s = team_colors(league, team_id, which="primary"), team_colors(league, team_id, which="secondary")
        if p:
            primary, secondary = p, s or p
        else:
            warnings.warn(
                f"no colors on file for {league} team {team!r}; using the SportsDataverse colors",
                SdvplotWarning,
                stacklevel=2,
            )
    title = on_color(primary)
    pal = _light_palette(secondary if contrast(secondary, "#ffffff") >= 1.5 else primary)
    pal.update(
        heading_bg=primary,
        title=title,
        subtitle=_secondary_on(primary, title),
        label=primary if contrast(primary, "#ffffff") >= 3 else SDV_NAVY,
    )
    return _build_theme(gt, pal, density, tab_options)

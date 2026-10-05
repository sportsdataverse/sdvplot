"""great_tables helpers (``pip install sdvplot[tables]``), ported from sdvplotR's ``gt_*`` functions.

Team logos, wordmarks and headshots in cells and column labels, team-colored text, and the SportsDataverse themes.
Heights are pixels: a table has no plot height.

sdvplot's front door routes a ``GT`` here: ``sdvplot.add_logos(gt, "team", league="nfl")`` is ``gt_sdv_logos``
(``add_wordmarks`` and ``add_headshots`` likewise), and ``axis_logos`` raises TypeError (a table has no axes).

Test hooks for ``sdvplot.testing.check_table_adapter_contract``: ``_rendered_html(gt)`` and ``_drawn_cells(gt)``.
"""

from __future__ import annotations

import math
import re
from html.parser import HTMLParser
from typing import Any

from great_tables import GT

from sdvplot.great_tables._cells import (
    gt_538_caption,
    gt_bold_rows,
    gt_border_bars_bottom,
    gt_border_bars_top,
    gt_border_grid,
    gt_color_pills,
    gt_color_ranks,
    gt_color_results,
    gt_column_subheaders,
    gt_cutline,
    gt_delta,
    gt_fmt_rank,
    gt_fmt_tally,
    gt_group_stripes,
    gt_highlight_cells,
    gt_highlight_na,
    gt_indicator_boxes,
)
from sdvplot.great_tables._export import gt_grid, gt_save_batch, gt_save_crop, gt_social_crop, gt_stack_tables
from sdvplot.great_tables._layout import (
    gt_legend_continuous,
    gt_legend_discrete,
    gt_marginalia,
    gt_outliers,
    gt_percentile_bar,
    gt_row_accent,
    gt_scale_note,
    gt_set_font,
    gt_significance,
    gt_snake,
    gt_snake_align,
    gt_social_tag,
    gt_spotlight,
    gt_tiers,
    gt_title_header,
    gt_watermark,
    gt_wrap_labels,
)
from sdvplot.great_tables._marks import (
    gt_merge_stack_team_color,
    gt_sdv_cols_label,
    gt_sdv_headshots,
    gt_sdv_logos,
    gt_sdv_wordmarks,
    gt_theme_sdv,
    gt_theme_sdv_team,
)
from sdvplot.great_tables._themes import (
    gt_theme_almanac,
    gt_theme_athletic,
    gt_theme_booktabs,
    gt_theme_broadsheet,
    gt_theme_brutalist,
    gt_theme_drench,
    gt_theme_gtutils,
    gt_theme_kenpom,
    gt_theme_midnight,
    gt_theme_ncaa,
    gt_theme_pl,
    gt_theme_preview,
    gt_theme_savant,
    gt_theme_scoreboard,
    gt_theme_sofa,
    gt_theme_swiss,
    gt_theme_terminal,
    gt_theme_tier,
    gt_theme_tufte,
    pal_midnight,
)

_SUPPORTS_AXIS_LOGOS = False
add_logos = gt_sdv_logos
add_wordmarks = gt_sdv_wordmarks
add_headshots = gt_sdv_headshots


def axis_logos(target: Any, *args: Any, **kwargs: Any) -> Any:
    """A table has no axes: always TypeError (use ``gt_sdv_cols_label`` for marks in the column labels)."""
    raise TypeError("a great_tables table has no axes; use gt_sdv_cols_label() for marks in the column labels")


def _rendered_html(gt: GT) -> str:
    """The table as great_tables renders it (``as_raw_html()``)."""
    return gt.as_raw_html()


_HEIGHT = re.compile(r"height:\s*([0-9.]+)px")


class _Cells(HTMLParser):
    """Collects the sdvplot images of a rendered table: column-label images (row -1) and body-cell images."""

    def __init__(self) -> None:
        super().__init__()
        self.section = ""
        self.columns: list[str] = []  # the column-label ids, left to right (the stub's is "")
        self.label = ""  # the id of the column label being read
        self.row = -1
        self.col = -1
        self.cells: list[tuple[str, int, str, float, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        classes = a.get("class", "").split()
        if tag in ("thead", "tbody"):
            self.section = tag
        elif tag == "tr" and self.section == "tbody":
            self.col = -1
            if "gt_group_heading_row" not in classes:
                self.row += 1
        elif tag == "th" and a.get("scope") == "col":
            self.label = a.get("id", "")
            self.columns.append(self.label)
        elif tag in ("td", "th") and "gt_row" in classes:
            self.col += 1
        elif tag == "img" and "data-sdvplot-team" in a:
            m = _HEIGHT.search(a.get("style", ""))
            h = float(m.group(1)) if m else math.nan
            team, src = a["data-sdvplot-team"], a.get("src", "")
            if self.section == "thead":
                self.cells.append((team, -1, self.label, h, src))
            elif self.section == "tbody" and self.col >= 0:
                self.cells.append((team, self.row, self.columns[self.col], h, src))


def _drawn_cells(gt: GT) -> list[tuple[str, int, str, float, str]]:
    """``(team_id, row, column, height_px, src)`` per sdvplot image in the rendered table, in display order.

    Body images carry their display row (0-based, group headings not counted) and column name; column-label images
    carry row -1. Images in row-group headings are not listed. Tables with column spanners are not supported.
    """
    parser = _Cells()
    parser.feed(_rendered_html(gt))
    return parser.cells


__all__ = [
    "add_headshots",
    "add_logos",
    "add_wordmarks",
    "axis_logos",
    "gt_538_caption",
    "gt_bold_rows",
    "gt_border_bars_bottom",
    "gt_border_bars_top",
    "gt_border_grid",
    "gt_color_pills",
    "gt_color_ranks",
    "gt_color_results",
    "gt_column_subheaders",
    "gt_cutline",
    "gt_delta",
    "gt_fmt_rank",
    "gt_fmt_tally",
    "gt_grid",
    "gt_group_stripes",
    "gt_highlight_cells",
    "gt_highlight_na",
    "gt_indicator_boxes",
    "gt_legend_continuous",
    "gt_legend_discrete",
    "gt_marginalia",
    "gt_merge_stack_team_color",
    "gt_outliers",
    "gt_percentile_bar",
    "gt_row_accent",
    "gt_save_batch",
    "gt_save_crop",
    "gt_scale_note",
    "gt_sdv_cols_label",
    "gt_sdv_headshots",
    "gt_sdv_logos",
    "gt_sdv_wordmarks",
    "gt_set_font",
    "gt_significance",
    "gt_snake",
    "gt_snake_align",
    "gt_social_crop",
    "gt_social_tag",
    "gt_spotlight",
    "gt_stack_tables",
    "gt_theme_almanac",
    "gt_theme_athletic",
    "gt_theme_booktabs",
    "gt_theme_broadsheet",
    "gt_theme_brutalist",
    "gt_theme_drench",
    "gt_theme_gtutils",
    "gt_theme_kenpom",
    "gt_theme_midnight",
    "gt_theme_ncaa",
    "gt_theme_pl",
    "gt_theme_preview",
    "gt_theme_savant",
    "gt_theme_scoreboard",
    "gt_theme_sdv",
    "gt_theme_sdv_team",
    "gt_theme_sofa",
    "gt_theme_swiss",
    "gt_theme_terminal",
    "gt_theme_tier",
    "gt_theme_tufte",
    "gt_tiers",
    "gt_title_header",
    "gt_watermark",
    "gt_wrap_labels",
    "pal_midnight",
]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)

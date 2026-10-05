"""Borders and fills sdvplot draws inline must show in a notebook too. great_tables' notebook repr marks its own cell
rules !important (``td, th {border-style: none !important}``, the stub's and row groups' ``background-color``), and a
stylesheet !important beats a plain inline style: the bar shows in a saved image and vanishes in Jupyter."""

import ast
import re
from pathlib import Path

import polars as pl
import pytest

pytest.importorskip("great_tables")
from great_tables import GT  # noqa: E402

from sdvplot.great_tables import gt_border_grid, gt_group_stripes, gt_row_accent, gt_spotlight  # noqa: E402

SRC = Path(__file__).parents[1] / "src" / "sdvplot" / "great_tables"
DECL = re.compile(r"((?:border(?:-(?:top|bottom|left|right))?|background-color)\s*:[^;\"]*)(;|\")")


def _df():
    return pl.DataFrame(
        {"team": ["Clemson", "Georgia", "Ohio State"], "conf": ["ACC", "SEC", "B1G"], "wins": [10, 12, 11]}
    )


def _inline(html):
    """Every border or background declaration in a style attribute of a table cell."""
    styles = re.findall(r'<t[dh] [^>]*?style="([^"]*)"', html)
    return [d.strip() for s in styles for d, _ in DECL.findall(s + '"')]


def test_row_accent_bars_survive_the_notebook_repr():
    gt = gt_row_accent(GT(_df()), "conf", palette={"ACC": "#003366", "SEC": "#B8232F", "B1G": "#BB0000"})
    html = gt._repr_html_()
    assert "border-left: 4px solid #003366 !important" in html
    assert all(d.endswith("!important") for d in _inline(html))


@pytest.mark.parametrize(
    "build",
    [
        lambda: gt_row_accent(GT(_df(), rowname_col="team"), "conf", palette=["#003366", "#B8232F"]),  # the stub
        lambda: gt_spotlight(GT(_df()), rows=[1], fill="#FFF3B0", accent_color="#B8232F"),
        lambda: gt_border_grid(GT(_df()), include_labels=True),
        lambda: gt_group_stripes(GT(_df(), groupname_col="conf", rowname_col="team")),  # stub fills
    ],
)
def test_borders_and_fills_carry_important_in_the_repr(build):
    found = _inline(build()._repr_html_())
    assert found and all(d.endswith("!important") for d in found), found


def test_every_border_and_fill_style_goes_through_important():
    """No sdvplot great_tables module builds a border or fill cell style except inside ``important(...)``."""
    bare = []
    for path in sorted(SRC.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        wrapped = {
            id(arg)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "important"
            for arg in node.args
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name)):
                name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
                if name in {"borders", "fill", "_borders"} and id(node) not in wrapped:
                    bare.append(f"{path.name}:{node.lineno}")
    assert bare == []


# --- row striping ------------------------------------------------------------------------------------------------------
# The repr's stylesheet !important also covers the stripes' background and text color, which then beat a plain inline
# fill or text color on every other row: data_color's fills (gt_color_ranks), and the ink sdvplot pairs with a fill.
# An inline !important (sdvplot's fills and borders) and anything drawn inside the cell (pills, boxes) are not covered.

from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.great_tables import (  # noqa: E402
    gt_bold_rows,
    gt_color_pills,
    gt_color_ranks,
    gt_color_results,
    gt_highlight_cells,
    gt_highlight_na,
    gt_indicator_boxes,
    gt_outliers,
    gt_tiers,
)


def _games():
    return pl.DataFrame(
        {
            "team": ["LV", "KC", "BUF", "LAR"],
            "res": ["W", "L", "W", "L"],
            "rk": [1, 2, 3, 4],
            "tier": ["S", "A", "S", "A"],
        }
    )


COVERED = {
    "gt_color_results": lambda gt: gt_color_results(gt, "res"),
    "gt_color_ranks": lambda gt: gt_color_ranks(gt, "rk"),
    "gt_bold_rows": lambda gt: gt_bold_rows(gt, rows=[0], highlight_color="#002244"),
    "gt_highlight_cells": lambda gt: gt_highlight_cells(gt, "rk", lambda s: s > 1, text_color="white"),
    "gt_highlight_na": lambda gt: gt_highlight_na(gt, "rk", na_strings=["2"], fill="#002244", text_color="white"),
    "gt_spotlight": lambda gt: gt_spotlight(gt, rows=[0], fill="#002244", text_color="white"),
    "gt_outliers": lambda gt: gt_outliers(gt, "rk", method="bounds", bounds=(2, 3), fill="#002244"),
    "gt_tiers": lambda gt: gt_tiers(gt, {"S": "#C84630", "A": "#5DA271"}, image_columns=[]),
}
UNCOVERED = {
    "gt_color_pills": lambda gt: gt_color_pills(gt, "rk", domain=[1, 4]),  # the fill is the pill's own element
    "gt_indicator_boxes": lambda gt: gt_indicator_boxes(gt, "rk"),
    "gt_row_accent": lambda gt: gt_row_accent(gt, "res", palette={"W": "#003366", "L": "#B8232F"}),  # a border
    "gt_highlight_cells": lambda gt: gt_highlight_cells(gt, "rk", lambda s: s > 1),  # an !important fill, no ink
}


@pytest.mark.parametrize("helper", sorted(COVERED))
def test_a_fill_helper_warns_once_when_the_stripes_would_cover_it(helper):
    with pytest.warns(SdvplotWarning, match=r"row striping is on.*opt_row_striping\(row_striping=False\)") as seen:
        COVERED[helper](GT(_games()).opt_row_striping())
    assert len([w for w in seen if issubclass(w.category, SdvplotWarning)]) == 1
    COVERED[helper](GT(_games()))  # no striping, no warning (SdvplotWarning is an error here)


@pytest.mark.parametrize("helper", sorted(UNCOVERED))
def test_a_helper_the_stripes_cannot_cover_does_not_warn(helper):
    UNCOVERED[helper](GT(_games()).opt_row_striping())

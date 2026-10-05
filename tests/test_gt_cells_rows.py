import numpy as np
import polars as pl
import pytest

pytest.importorskip("great_tables")
from great_tables import GT  # noqa: E402

from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.great_tables import (  # noqa: E402
    gt_bold_rows,
    gt_color_results,
    gt_group_stripes,
    gt_highlight_cells,
    gt_highlight_na,
)
from tests.gt_html import STUB, body_rows, frame  # noqa: E402

CARS = {"car": ["Mazda", "Datsun", "Fiat"], "mpg": [21.0, 18.5, 30.2], "hp": [110, 175, 66]}


@pytest.fixture(params=["pandas", "polars"])
def lib(request):
    return request.param


def styles(gt):
    return [[s for s, _ in row] for row in body_rows(gt)]


def test_bold_rows_bolds_and_fills_only_the_chosen_rows(lib):
    out = gt_bold_rows(GT(frame(lib, CARS)), rows=[0, 2], highlight_color="#FFF3B0")
    got = styles(out)
    for r in (0, 2):
        assert all(
            "font-weight: bold" in s and "background-color: #FFF3B0" in s and "color: black" in s for s in got[r]
        )
    assert got[1] == ["", "", ""]


def test_bold_rows_without_rows_bolds_every_row_and_adds_no_fill(lib):
    got = styles(gt_bold_rows(GT(frame(lib, CARS))))
    assert all("font-weight: bold" in s and "background-color" not in s for row in got for s in row)


def above(lib, column, value):
    """A row filter in each library's great_tables form: a polars expression, or a callable for pandas."""
    return pl.col(column) > value if lib == "polars" else (lambda d: d[column] > value)


def test_bold_rows_accepts_a_row_filter_on_either_library(lib):
    got = styles(gt_bold_rows(GT(frame(lib, CARS)), rows=above(lib, "mpg", 20)))
    assert ["font-weight: bold" in row[0] for row in got] == [True, False, True]


def test_bold_rows_that_match_nothing_warn_and_return_the_table(lib):
    gt = GT(frame(lib, CARS))
    with pytest.warns(SdvplotWarning, match="matched no rows"):
        assert gt_bold_rows(gt, rows=above(lib, "mpg", 100)) is gt


def test_a_data_frame_instead_of_a_gt_is_a_type_error():
    with pytest.raises(TypeError, match=r"It looks like raw data: wrap it in great_tables\.GT\(\) first"):
        gt_bold_rows(frame("polars", CARS))


GAMES = {"game": ["G1", "G2", "G3", "G4"], "pts": [88, 74, 102, 65], "result": ["W", "L", "T", "W"]}


def test_color_results_fills_wins_and_losses_and_leaves_ties_without_a_tie_color(lib):
    got = styles(gt_color_results(GT(frame(lib, GAMES))))
    assert all("background-color: #5DA271" in s and "color: white" in s for s in got[0] + got[3])
    assert all("background-color: #C84630" in s for s in got[1])
    assert got[2] == ["", "", ""]


def test_color_results_colors_ties_when_given_a_tie_color(lib):
    got = styles(gt_color_results(GT(frame(lib, GAMES)), tie_color="#999999", tie_text_color="black"))
    assert all("background-color: #999999" in s and "color: black" in s for s in got[2])


def test_color_results_binary_encoding(lib):
    data = {**GAMES, "result": [1, 0, 1, 0]}
    got = styles(gt_color_results(GT(frame(lib, data)), result_type="binary", win_color="#1B7837"))
    assert ["#1B7837" in row[0] for row in got] == [True, False, True, False]
    assert ["#C84630" in row[0] for row in got] == [False, True, False, True]


def test_color_results_rejects_two_columns_and_an_unknown_type(lib):
    gt = GT(frame(lib, GAMES))
    with pytest.raises(ValueError, match="exactly one column"):
        gt_color_results(gt, result_column=["pts", "result"])
    with pytest.raises(ValueError, match="result_type"):
        gt_color_results(gt, result_type="score")


GRID = {"name": ["x", "y", "z"], "a": [1.0, 0.2, 0.9], "b": [0.1, 1.0, None], "c": [0.8, 0.0, 1.0]}


def test_highlight_cells_fills_each_column_on_its_own(lib):
    out = gt_highlight_cells(GT(frame(lib, GRID)), ["a", "b", "c"], lambda s: s == 1, fill="#FFD1A9")
    filled = [[("#FFD1A9" in s) for s, _ in row] for row in body_rows(out)]
    # the diagonal only: one tab_style per column, never the rows-by-columns rectangle; a null never matches
    assert filled == [[False, True, False, False], [False, False, True, False], [False, False, False, True]]


def test_highlight_cells_takes_a_precomputed_mask(lib):
    mask = [[True, False], [False, None], [False, True]]
    out = gt_highlight_cells(GT(frame(lib, GRID)), ["a", "c"], mask, bold=True, text_color="#123456")
    got = styles(out)
    assert "#FFF3B0" in got[0][1] and "font-weight: bold" in got[0][1] and "color: #123456" in got[0][1]
    assert "#FFF3B0" in got[2][3] and got[1] == ["", "", "", ""]
    with pytest.raises(ValueError, match="one column per selected column"):
        gt_highlight_cells(GT(frame(lib, GRID)), ["a", "b", "c"], mask)


def test_highlight_cells_passes_text_kwargs_and_names_a_column_the_condition_does_not_fit(lib):
    out = gt_highlight_cells(GT(frame(lib, GRID)), "a", lambda s: s > 0.5, style="italic")
    assert "font-style: italic" in styles(out)[0][1]
    with pytest.raises(ValueError, match="'name'"):
        gt_highlight_cells(GT(frame(lib, GRID)), ["name", "a"], lambda s: s.abs() > 0.5)


MISSING = {"site": ["a", "b", "c", "d"], "ozone": [41.0, None, 12.0, None], "note": ["ok", "NA", " n/a ", None]}


def test_highlight_na_fills_and_relabels_real_and_placeholder_missing_values(lib):
    out = gt_highlight_na(
        GT(frame(lib, MISSING)),
        ["ozone", "note"],
        missing_text="--",
        italic=True,
        na_strings=["NA", "N/A"],
        ignore_case=True,
    )
    rows = body_rows(out)
    flagged = [[("#F0F0F0" in s and "font-style: italic" in s) for s, _ in row] for row in rows]
    assert flagged == [[False, False, False], [False, True, True], [False, False, True], [False, True, True]]
    assert [row[1][1] for row in rows] == ["41.0", "--", "12.0", "--"]
    assert [row[2][1] for row in rows] == ["ok", "--", "--", "--"]


def test_highlight_na_defaults_to_every_column_and_the_string_na(lib):
    out = gt_highlight_na(GT(frame(lib, MISSING)))
    flagged = [["#F0F0F0" in s for s, _ in row] for row in body_rows(out)]
    assert flagged == [[False, False, False], [False, True, True], [False, False, False], [False, True, True]]


def test_highlight_na_with_no_fill_only_relabels(lib):
    out = gt_highlight_na(GT(frame(lib, MISSING)), "ozone", fill=None, missing_text="not recorded")
    rows = body_rows(out)
    assert [row[1] for row in rows][1] == ("", "not recorded")


TEAMS = {
    "conf": ["East", "West", "East", "North", "West", "North"],
    "team": ["A", "B", "C", "D", "E", "F"],
    "wins": [10, 9, 8, 7, 6, 5],
}


def test_group_stripes_band_every_other_group_in_render_order(lib):
    gt = GT(frame(lib, TEAMS), rowname_col="team", groupname_col="conf").row_group_order(["North", "East", "West"])
    out = gt_group_stripes(gt)
    banded_body = ["#F5F5F5" in row[0][0] for row in body_rows(out)]
    banded_stub = ["#F5F5F5" in row[0][0] for row in body_rows(out, STUB)]
    # render order North (D, F), East (A, C), West (B, E): start=2 bands East
    assert banded_body == [False, False, True, True, False, False]
    assert banded_stub == banded_body


def test_group_stripes_start_one_and_no_stub(lib):
    gt = GT(frame(lib, TEAMS), rowname_col="team", groupname_col="conf")
    out = gt_group_stripes(gt, color="#FBF3E4", start=1, include_stub=False)
    # render order East (A, C), West (B, E), North (D, F): start=1 bands East and North
    assert ["#FBF3E4" in row[0][0] for row in body_rows(out)] == [True, True, False, False, True, True]
    assert not any("#FBF3E4" in row[0][0] for row in body_rows(out, STUB))
    with pytest.raises(ValueError, match="start"):
        gt_group_stripes(gt, start=3)


def test_group_stripes_warn_on_a_table_without_groups(lib):
    gt = GT(frame(lib, TEAMS))
    with pytest.warns(SdvplotWarning, match="row groups"):
        assert gt_group_stripes(gt) is gt


@pytest.mark.parametrize(
    "rows",
    [[np.int64(0), np.int64(2)], (0, np.int32(2)), np.array([0, 2])],
    ids=["numpy-ints", "tuple", "array"],
)
def test_bold_rows_takes_numpy_integer_positions(lib, rows):
    # great_tables' resolver silently skips positions that are not plain ints; they must still select their rows
    got = styles(gt_bold_rows(GT(frame(lib, CARS)), rows=rows))
    assert ["font-weight: bold" in row[0] for row in got] == [True, False, True]


def test_bold_rows_takes_a_numpy_integer_scalar(lib):
    got = styles(gt_bold_rows(GT(frame(lib, CARS)), rows=np.int64(1)))
    assert ["font-weight: bold" in row[0] for row in got] == [False, True, False]

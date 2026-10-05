import dataclasses
import re

import pandas as pd
import polars as pl
import pytest

pytest.importorskip("great_tables")
from great_tables import GT, loc, style  # noqa: E402

from sdvplot.great_tables import gt_snake, gt_snake_align, gt_wrap_labels  # noqa: E402
from tests.gt_frames import KINDS, frame  # noqa: E402

TOP5 = {"rank": [1, 2, 3, 4, 5], "team": ["LV", "KC", "BUF", "NYJ", "MIA"], "pts": [1.5, 2.0, 3.0, None, 5.0]}


def body_rows(gt):
    rows = re.findall(r"<tr>(.*?)</tr>", gt.as_raw_html().replace("\n", ""))
    return [re.findall(r"<td[^>]*>.*?</td>", r) for r in rows if "<td" in r]


def labels(gt):
    return [label for _, label in re.findall(r'<th[^>]*id="([^"]+)"[^>]*>([^<]*)</th>', gt.as_raw_html())]


def test_private_styles_api():
    # gt_snake moves body styles by rewriting these private StyleInfo fields and GT._replace
    gt = GT(pl.DataFrame(TOP5)).tab_style(style.fill("#ffff00"), loc.body("team", [3]))
    (info,) = gt._styles
    assert dataclasses.is_dataclass(info) and type(info.locname).__name__ == "LocBody"
    assert (info.colname, info.rownum) == ("team", 3)
    assert gt._replace(_styles=[])._styles == [] and gt._source_notes == []


@pytest.mark.parametrize("kind", KINDS)
def test_snake_lays_blocks_side_by_side(kind):
    gt = GT(frame(kind, TOP5)).cols_label(team="Team").tab_header("Top 5").tab_source_note("source: SDV")
    out = gt_snake(gt, n_cols=2)
    assert list(out._tbl_data.columns) == ["rank_1", "team_1", "pts_1", ".gap1", "rank_2", "team_2", "pts_2"]
    assert type(out._tbl_data) is type(gt._tbl_data)
    assert labels(out) == ["rank", "Team", "pts", "", "rank", "Team", "pts"]
    first, _, third = body_rows(out)
    assert [re.sub(r"<[^>]+>", "", c) for c in first[:6]] == ["1", "LV", "1.5", "", "4", "NYJ"]
    assert [re.sub(r"<[^>]+>", "", c) for c in third[4:]] == ["", "", ""]  # the padding is blank
    assert re.sub(r"<[^>]+>", "", first[6]) != ""  # a real missing value in the last block is not padding
    h = out.as_raw_html()
    assert "Top 5" in h and "source: SDV" in h
    assert '<col style="width:20px;"/>' in h


def test_snake_carries_styles_and_cleans_the_gap():
    gt = (
        GT(pl.DataFrame(TOP5), id="top")
        .tab_style(style.fill("#ffff00"), loc.body("team", [3]))
        .tab_style(style.text(weight="bold"), loc.column_labels("pts"))
    )
    out = gt_snake(gt)
    first = body_rows(out)[0]
    assert first[5] == '<td style="background-color: #ffff00;" class="gt_row gt_left">NYJ</td>'  # row 3 -> block 2
    assert out.as_raw_html().count('style="font-weight: bold;"') == 2  # the label style repeats per block
    h = out.as_raw_html()
    assert "#top td:nth-child(4) {border: 1px solid transparent !important; background: transparent !important;" in h
    assert "#top td:nth-child(3) {border-right: 1px solid transparent !important;}" in h
    assert "#top td:nth-child(5) {border-left: 1px solid transparent !important;}" in h
    spacer = (
        'style="border-top: 1px solid transparent !important; border-bottom: 1px solid transparent !important; '
        'border-left: 1px solid transparent !important; border-right: 1px solid transparent !important;"'
    )
    assert spacer + ' scope="col" id="top-.gap1"' in h


def test_snake_rows_per_col_without_gaps():
    gt = GT(pl.DataFrame(TOP5))
    out = gt_snake(gt, rows_per_col=2, gap=0, fill="-")
    assert list(out._tbl_data.columns) == ["rank_1", "team_1", "pts_1", "rank_2", "team_2", "pts_2", "rank_3",
                                           "team_3", "pts_3"]  # fmt: skip
    assert out._options.table_id.value is None  # no gap css, so no id is forced
    assert [re.sub(r"<[^>]+>", "", c) for c in body_rows(out)[1][6:]] == ["-", "-", "-"]
    assert gt_snake(gt, n_cols=1) is gt
    assert gt_snake(GT(pl.DataFrame({"a": []})), n_cols=3)._tbl_data.columns == ["a"]
    with pytest.raises(ValueError, match="n_cols must be at least 1"):
        gt_snake(gt, n_cols=0)
    with pytest.raises(ValueError, match="rows_per_col must be at least 1"):
        gt_snake(gt, rows_per_col=0)


@pytest.mark.parametrize("kind", KINDS)
def test_snake_align_matches_the_snaked_columns(kind):
    hot = frame(kind, {"rank": [True, False, True, False, True], "team": [False] * 5, "pts": [True] * 5})
    wide = gt_snake_align(hot, n_cols=2)
    snaked = gt_snake(GT(frame(kind, TOP5)), n_cols=2)
    assert list(wide.columns) == [c for c in snaked._tbl_data.columns if not c.startswith(".gap")]
    assert type(wide) is type(hot) and len(wide) == 3
    filled = gt_snake_align(hot, rows_per_col=3, fill=False)
    assert list(filled["rank_2"]) == [False, True, False]


def test_snake_align_edge_cases():
    df = pd.DataFrame({"x": [1, 2, 3]})
    assert gt_snake_align(df, n_cols=1) is df
    assert list(gt_snake_align(df, n_cols=2)["x_2"]) == [3, None]  # integers stay integers next to the padding
    with pytest.raises(TypeError):
        gt_snake_align([1, 2, 3])


@pytest.mark.parametrize("kind", KINDS)
def test_wrap_labels_balances_long_labels(kind):
    df = frame(kind, {"Expected points added per play": [0.1], "Win probability added": [0.2], "EPA": [0.3]})
    out = gt_wrap_labels(GT(df))
    h = out.as_raw_html()
    assert ">Expected<br>points<br>added<br>per play</th>" in h
    assert ">Win<br>probability<br>added</th>" in h
    assert ">EPA</th>" in h


def test_wrap_labels_greedy_selected_and_relabeled_columns():
    gt = GT(pl.DataFrame({"a": [1], "b": [2], "c": [3]})).cols_label(a="Expected points added per play", b="Short one")
    h = gt_wrap_labels(gt, columns=["a", "b"], balance=False).as_raw_html()
    assert ">Expected<br>points<br>added per<br>play</th>" in h
    assert ">Short one</th>" in h  # already shorter than width
    assert ">Expected points<br>added per play</th>" in gt_wrap_labels(gt, "a", width=20).as_raw_html()

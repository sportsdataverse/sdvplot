import re

import pytest

pytest.importorskip("great_tables")
from great_tables import GT, loc, style  # noqa: E402

import sdvplot.great_tables as sgt  # noqa: E402
from sdvplot.great_tables import gt_column_subheaders, gt_delta, gt_fmt_rank, gt_fmt_tally  # noqa: E402
from tests.gt_html import body_rows, frame  # noqa: E402


@pytest.fixture(params=["pandas", "polars"])
def lib(request):
    return request.param


def texts(gt):
    return [[t for _, t in row] for row in body_rows(gt)]


def labels(gt):
    return re.findall(r'<th class="gt_col_heading[^>]*>(.*?)</th>', gt.as_raw_html(), re.S)


PLACES = {"team": list("ABCDEFGHIJK"), "place": [1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 111]}


def test_fmt_rank_writes_ordinals_with_superscript_suffixes(lib):
    out = gt_fmt_rank(GT(frame(lib, PLACES)), "place")
    got = [row[1] for row in texts(out)]
    suffixes = [re.fullmatch(r"(\d+)<sup style='font-size:0.7em;'>(\w+)</sup>", t).groups() for t in got]
    assert suffixes == [
        ("1", "st"), ("2", "nd"), ("3", "rd"), ("4", "th"), ("11", "th"), ("12", "th"),
        ("13", "th"), ("21", "st"), ("22", "nd"), ("23", "rd"), ("111", "th"),
    ]  # fmt: skip


def test_fmt_rank_flat_suffixes_float_columns_and_text_left_alone(lib):
    data = {"place": [1.0, 2.0, 3.0], "note": ["T-5", "2", "x"]}
    out = gt_fmt_rank(GT(frame(lib, data)), ["place", "note"], superscript=False)
    assert texts(out) == [["1st", "T-5"], ["2nd", "2nd"], ["3rd", "x"]]


SUITES = {"suite": ["Parser", "Renderer", "Exporter", "Empty"], "passed": [142, 98, 211, 0], "failed": [8, 2, 17, 0]}


def test_fmt_tally_joins_the_counts_into_the_first_column_and_hides_the_rest(lib):
    out = gt_fmt_tally(GT(frame(lib, SUITES)), ["passed", "failed"], label="Result")
    assert [row[1] for row in texts(out)] == ["142-8", "98-2", "211-17", "0-0"]
    assert labels(out) == ["suite", "Result"]


def test_fmt_tally_inline_share_and_a_blank_share_for_a_zero_total(lib):
    out = gt_fmt_tally(GT(frame(lib, SUITES)), ["passed", "failed"], share=True)
    assert [row[1] for row in texts(out)] == ["142-8 (94.7%)", "98-2 (98.0%)", "211-17 (92.5%)", "0-0"]


def test_fmt_tally_share_in_its_own_column_by_name(lib):
    out = gt_fmt_tally(
        GT(frame(lib, SUITES)), ["passed", "failed"], share=True, share_of="failed", share_location="column",
        share_label="Fail rate", share_decimals=0,
    )  # fmt: skip
    assert labels(out) == ["suite", "passed", "Fail rate"]
    assert [row[1:] for row in texts(out)] == [["142-8", "5%"], ["98-2", "2%"], ["211-17", "7%"], ["0-0", "0"]]


def test_fmt_tally_three_counts_and_a_missing_count(lib):
    data = {"club": ["Arsenal", "Chelsea"], "w": [26, 18], "d": [6, None], "l": [6, 10]}
    out = gt_fmt_tally(GT(frame(lib, data)), ["w", "d", "l"], label="W-D-L")
    assert labels(out) == ["club", "W-D-L"]
    assert texts(out)[0] == ["Arsenal", "26-6-6"]
    assert texts(out)[1][1] in ("18", "18.0")  # a partial tally is never shown: the row keeps its raw value


def test_fmt_tally_rejects_one_column_and_a_bad_share_of(lib):
    gt = GT(frame(lib, SUITES))
    with pytest.raises(ValueError, match="at least two"):
        gt_fmt_tally(gt, "passed")
    with pytest.raises(ValueError, match="share_of"):
        gt_fmt_tally(gt, ["passed", "failed"], share=True, share_of=2)
    with pytest.raises(ValueError, match="share_location"):
        gt_fmt_tally(gt, ["passed", "failed"], share_location="row")


REVENUE = {"segment": ["Hardware", "Software", "Services", "Other"], "q1": [482, 331, 198, 0], "q2": [515, 302, 246, 5]}


def test_delta_adds_a_signed_colored_change_column_after_to(lib):
    gt = GT(frame(lib, REVENUE)).fmt_number(columns="q1", decimals=2).tab_style(style.text(color="red"), loc.body("q2"))
    out = gt_delta(gt, "q1", "q2")
    assert labels(out) == ["segment", "q1", "q2", "Change"]
    rows = body_rows(out)
    assert [r[3][1] for r in rows] == ["+33.0", "−29.0", "+48.0", "+5.0"]
    assert [r[3][0] for r in rows] == ["color: #1B7837;", "color: #B2182B;", "color: #1B7837;", "color: #1B7837;"]
    assert rows[0][1] == ("", "482.00") and rows[0][2][0] == "color: red;"  # earlier formats and styles survive
    assert 'class="gt_row gt_right">' in out.as_raw_html().split("+33.0")[0][-40:]


def test_delta_percent_with_arrows_blanks_a_zero_start(lib):
    out = gt_delta(GT(frame(lib, REVENUE)), "q1", "q2", percent=True, arrows=True, color=False)
    assert [r[3] for r in texts(out)] == ["▲ 6.8%", "▼ 8.8%", "▲ 24.2%", ""]
    assert all(r[3][0] == "" for r in body_rows(out))


def test_delta_placement_neutral_color_and_a_taken_name(lib):
    data = {**REVENUE, "Change": ["x", "y", "z", "w"], "q3": [515, 1, 2, 3]}
    out = gt_delta(GT(frame(lib, data)), "q2", "q3", after="segment", color_neutral="#777777")
    assert labels(out) == ["segment", "Change", "q1", "q2", "Change", "q3"]
    assert [r[1] for r in body_rows(out)][0] == ("color: #777777;", "0.0")
    assert [c.var for c in out._boxhead] == ["segment", "Change.1", "q1", "q2", "Change", "q3"]
    by_position = gt_delta(GT(frame(lib, REVENUE)), "q1", "q2", after=0)
    assert labels(by_position) == ["segment", "Change", "q1", "q2"]
    with pytest.raises(ValueError, match="after"):
        gt_delta(GT(frame(lib, REVENUE)), "q1", "q2", after="nope")
    with pytest.raises(ValueError, match="single column"):
        gt_delta(GT(frame(lib, REVENUE)), ["q1", "q2"], "q2")


def test_delta_leaves_the_input_table_alone(lib):
    gt = GT(frame(lib, REVENUE))
    gt_delta(gt, "q1", "q2")
    assert labels(gt) == ["segment", "q1", "q2"]


def test_column_subheaders_stack_a_heading_over_a_subtitle_on_every_column(lib):
    out = gt_column_subheaders(
        GT(frame(lib, REVENUE)), q1={"heading": "Q1", "subtitle": "Jan-Mar"}, heading_color="blue", font="Lato"
    )
    got = labels(out)
    assert len(got) == 3 and all(g.startswith("<div style='line-height: 1.05; margin-bottom: -2px;'>") for g in got)
    assert (
        "<span style='font-size: 14px; font-weight: bold; color: blue; font-family: 'Lato';'>Q1</span><br>"
        "<span style='font-size: 10px; font-weight: normal; color: #808080; font-family: 'Lato';'>Jan-Mar</span>"
    ) in got[1]
    assert ">segment</span>" in got[0] and ">&nbsp;</span>" in got[0]
    with pytest.raises(ValueError, match="does not have"):
        gt_column_subheaders(GT(frame(lib, REVENUE)), q9={"heading": "x"})


def test_every_c1_function_is_exported_and_the_great_tables_internals_it_reads_exist(lib):
    names = {
        "gt_538_caption", "gt_bold_rows", "gt_border_bars_bottom", "gt_border_bars_top", "gt_border_grid",
        "gt_color_pills", "gt_color_ranks", "gt_color_results", "gt_column_subheaders", "gt_cutline", "gt_delta",
        "gt_fmt_rank", "gt_fmt_tally", "gt_group_stripes", "gt_highlight_cells", "gt_highlight_na",
        "gt_indicator_boxes",
    }  # fmt: skip
    assert names <= set(sgt.__all__)
    # private great_tables 1.0 API read by _cells.py: an upgrade that moves any of it must fail here, loudly
    from great_tables._gt_data import Body, Boxhead, ColInfo
    from great_tables._locations import resolve_cols_c, resolve_rows_i
    from great_tables._text import _process_text

    gt = GT(frame(lib, REVENUE), groupname_col="segment").tab_style(style.text(font="Lato"), loc.title())
    assert resolve_cols_c(data=gt, expr=None) == ["q1", "q2"]
    assert [i for _, i in resolve_rows_i(gt, [1])] == [1]
    assert _process_text("a<b") == "a&lt;b"
    assert {"_tbl_data", "_body", "_boxhead", "_stub", "_styles", "_heading", "_options"} <= set(vars(gt))
    assert [c.var for c in gt._boxhead] == ["segment", "q1", "q2"] and isinstance(gt._boxhead[0], ColInfo)
    assert [g.group_id for g in gt._stub.group_rows] == ["Hardware", "Software", "Services", "Other"]
    assert isinstance(gt._styles[0].locname, loc.title) and gt._styles[0].styles[0].font == "Lato"
    assert gt._options.row_striping_include_table_body.value is False
    assert Body.from_empty(gt._tbl_data) is not None and len(Boxhead(list(gt._boxhead))) == 3

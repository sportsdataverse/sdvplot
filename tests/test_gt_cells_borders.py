import re

import numpy as np
import pytest

pytest.importorskip("great_tables")
from great_tables import GT, loc, md, style  # noqa: E402

from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.great_tables import (  # noqa: E402
    gt_538_caption,
    gt_border_bars_bottom,
    gt_border_bars_top,
    gt_border_grid,
    gt_cutline,
)
from sdvplot.great_tables._cells import _cutline_svg  # noqa: E402
from tests.gt_html import body_rows, frame  # noqa: E402

CARS = {"car": ["Mazda", "Datsun", "Fiat", "Honda", "Valiant"], "mpg": [21.0, 22.8, 32.4, 30.4, 18.1]}


@pytest.fixture(params=["pandas", "polars"])
def lib(request):
    return request.param


def tfoot(gt):
    h = gt.as_raw_html()
    return h[h.index("<tfoot") : h.index("</tfoot>")]


def css(gt):
    h = gt.as_raw_html()
    return h[h.index("<style>") : h.index("</style>")]


def test_538_caption_puts_the_top_caption_over_a_rule_and_the_bottom_caption_under_it(lib):
    out = gt_538_caption(GT(frame(lib, CARS)), top_caption="**Fuel** economy", bottom_caption="Source: *Motor Trend*")
    foot = tfoot(out)
    top = foot.index("<strong>Fuel</strong> economy")
    bottom = foot.index("Source: <em>Motor Trend</em>")
    assert top < bottom
    # the rule takes the table's own text color (#333333 by default) and sits on the top caption only
    assert '<div style="border-bottom: 1px solid #333333; font-size: 12px;"><strong>' in foot
    assert '<div style="text-align: right;">Source:' in foot


def test_538_caption_rule_tracks_the_theme_and_accepts_raw_html(lib):
    themed = GT(frame(lib, CARS)).tab_options(table_font_color="#FAFAFA")
    handles = "<div style='text-align:right;'><span><svg viewBox='0 0 1 1'></svg>@you</span></div>"
    foot = tfoot(gt_538_caption(themed, top_caption="Top", bottom_caption=handles, rule_width=2, size=14))
    assert "border-bottom: 2px solid #FAFAFA; font-size: 14px;" in foot
    assert handles in foot
    foot = tfoot(gt_538_caption(themed, bottom_caption="Only", rule_color="#A6081A", align="left"))
    assert "border-bottom" not in foot and '<div style="text-align: left;">Only</div>' in foot


def test_538_caption_needs_a_caption():
    with pytest.raises(ValueError, match="nothing to caption"):
        gt_538_caption(GT(frame("polars", CARS)))


def test_538_caption_rule_color_skips_background_colors(monkeypatch):
    # a render whose first hex color is a background: the rule takes the text color, not the fill
    rendered = "<style>.x { background-color: #ABCDEF; border-top-color: #00FF00; } .y { color: #123456; }</style>"
    monkeypatch.setattr(GT, "as_raw_html", lambda self, **_: rendered)
    out = gt_538_caption(GT(frame("polars", CARS)), top_caption="Top")
    monkeypatch.undo()
    assert "border-bottom: 1px solid #123456;" in tfoot(out)


def test_538_caption_rejects_an_unknown_align():
    with pytest.raises(ValueError, match="align"):
        gt_538_caption(GT(frame("polars", CARS)), bottom_caption="x", align="middle")


@pytest.mark.parametrize("bars", [gt_border_bars_top, gt_border_bars_bottom])
@pytest.mark.parametrize(
    "arg", [{"bar_align": "middle"}, {"img_align": "center"}, {"text_align": "center"}, {"text_align": "top"}]
)
def test_border_bars_reject_unknown_alignments(bars, arg):
    gt = GT(frame("polars", CARS)).tab_header("Standings")
    with pytest.raises(ValueError, match=next(iter(arg))):
        bars(gt, "#22223B", text="x", img="https://cdn/1.png", **arg)
    with pytest.raises(ValueError, match=next(iter(arg))):
        bars(gt, "#22223B", **arg)  # checked even when the plain bars do not use it


def test_border_bars_bottom_stacks_one_bar_per_color_and_unpads_the_source_notes(lib):
    out = gt_border_bars_bottom(GT(frame(lib, CARS)), ["#1B7837", "#FFFFFF", "#B2182B"], bar_height=6)
    table_id = out._options.table_id.value
    assert table_id
    foot = tfoot(out)
    bars = re.findall(r'<div style="height: 6px; background-color: (#\w+);"></div>', foot)
    assert bars == ["#1B7837", "#FFFFFF", "#B2182B"]
    assert '<div style="background-color: transparent; width: 100%; margin-left: auto; margin-right: auto;">' in foot
    assert f"#{table_id} .gt_sourcenote {{padding-right: 0px !important; padding-left: 0px !important;" in css(out)


def test_border_bars_bottom_with_text_uses_the_source_note_font(lib):
    gt = GT(frame(lib, CARS)).with_id("standings").tab_style(style.text(font="Lato"), loc.source_notes())
    out = gt_border_bars_bottom(gt, ["#22223B", "#ff0000"], text="Source: ESPN", bar_height=28, bar_align="left")
    foot = tfoot(out)
    assert out._options.table_id.value == "standings"
    assert "<style>@import url('https://fonts.googleapis.com/css2?family=Lato&display=swap');</style>" in foot
    assert "height: 28px; background-color: #22223B; width: 100%; margin-left: 0; margin-right: auto;" in foot
    assert "#ff0000" not in foot
    assert (
        '<span style="font-weight:bold; color:#FFFFFF; font-size:18px; padding-left: 10px; font-family: Lato;">'
        "Source: ESPN</span>" in foot
    )
    plain = tfoot(gt_border_bars_bottom(GT(frame(lib, CARS)), "#22223B", text="x"))
    assert "@import" not in plain and "font-family: inherit;" in plain


def test_border_bars_top_sit_above_the_title_and_keep_the_subtitle(lib):
    gt = GT(frame(lib, CARS)).tab_header(title=md("**Standings**"), subtitle="Week 6")
    out = gt_border_bars_top(gt, ["#1B7837", "#B2182B"], img="https://cdn/1111.png")
    h = out.as_raw_html()
    title_cell = h[h.index("<thead") : h.index("gt_heading gt_subtitle")]
    bar = title_cell.index("background-color: #1B7837")
    assert "#B2182B" not in title_cell  # with an image, one bar in the first color
    assert bar < title_cell.index('<div style="padding: 4px 5px;"><strong>Standings</strong></div>')
    assert '<img src="https://cdn/1111.png" width="30px" height="30px" style="padding-right:10px;" />' in title_cell
    assert "Week 6" in h[h.index("gt_heading gt_subtitle") :]
    assert f"#{out._options.table_id.value} .gt_title {{padding: 0px !important;}}" in css(out)


def test_border_bars_top_on_a_table_without_a_title_is_just_the_bars(lib):
    out = gt_border_bars_top(GT(frame(lib, CARS)), ["#1B7837", "#FFFFFF"])
    h = out.as_raw_html()
    cell = re.search(r'class="gt_heading gt_title[^"]*">(.*?)</td>', h, re.S).group(1)
    assert re.findall(r"background-color: (#\w+);", cell) == ["#1B7837", "#FFFFFF"]
    assert "padding: 4px 5px" not in cell


def label_styles(gt):
    heads = re.findall(r'<th class="gt_col_heading[^>]*>', gt.as_raw_html())
    return [m.group(1) if (m := re.search(r'style="([^"]*)"', th)) else "" for th in heads]


def test_border_grid_divides_every_column_but_the_last(lib):
    out = gt_border_grid(GT(frame(lib, {**CARS, "hp": [110, 93, 66, 52, 105]})), color="#BBBBBB", weight=2)
    for row in body_rows(out):
        assert [s for s, _ in row] == ["border-right: 2px solid #BBBBBB;"] * 2 + [""]
    assert label_styles(out) == ["", "", ""]
    assert f"#{out._options.table_id.value} .gt_row {{ border-top-color: #BBBBBB;}}" in css(out)


def test_border_grid_includes_the_labels_and_skips_the_stub(lib):
    gt = GT(frame(lib, {**CARS, "hp": [110, 93, 66, 52, 105]}), rowname_col="car")
    out = gt_border_grid(gt, include_labels=True)
    assert all([s for s, _ in row] == ["border-right: 1px solid black;", ""] for row in body_rows(out))
    assert label_styles(out) == ["", "border-right: 1px solid black;", ""]  # the stubhead, then mpg and hp


def test_cutline_draws_a_dashed_rule_after_the_row(lib):
    out = gt_cutline(GT(frame(lib, CARS)), after=2)
    assert [row[0][0] for row in body_rows(out)] == ["", "", "border-top: 2px dashed #A6081A;", "", ""]
    assert "background-image" not in css(out)


def test_cutline_label_is_sdvplotrs_svg_on_the_row_below():
    # the reference string is sdvplotR's .cutline_svg("Top six & <more>", "#A6081A", 9), run in R 4.6.1
    assert _cutline_svg("Top six & <more>", "#A6081A", 9) == (
        "data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width"
        "%3D%22137%22%20height%3D%2213%22%3E%3Ctext%20x%3D%220%22%20y%3D%229.5%22%20font-family%3D%22Helvetica"
        "%2CArial%2Csans-serif%22%20font-size%3D%229%22%20font-weight%3D%22700%22%20letter-spacing%3D%221.1%22"
        "%20fill%3D%22%23A6081A%22%3ETOP%20SIX%20%26amp%3B%20%26lt%3BMORE%26gt%3B%3C%2Ftext%3E%3C%2Fsvg%3E"
    )
    assert _cutline_svg("Shortlist", "#0054AD", 12.5) == (
        "data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width"
        "%3D%22104%22%20height%3D%2216%22%3E%3Ctext%20x%3D%220%22%20y%3D%2213.0%22%20font-family%3D%22Helvetica"
        "%2CArial%2Csans-serif%22%20font-size%3D%2212.5%22%20font-weight%3D%22700%22%20letter-spacing%3D%221.1%22"
        "%20fill%3D%22%230054AD%22%3ESHORTLIST%3C%2Ftext%3E%3C%2Fsvg%3E"
    )


def test_cutline_labels_pad_and_clear_the_labeled_row_and_repaint_its_stripe(lib):
    gt = GT(frame(lib, CARS)).opt_row_striping()
    out = gt_cutline(gt, after=[1, 3], label=["Top", None])
    table_id = out._options.table_id.value
    rules = css(out)
    # row 2 (1-based) carries the label below the first line; the second line is unlabeled
    assert (
        f"#{table_id} tbody tr:nth-child(2) td {{ padding-top: 22px !important; background-color: transparent !important; }}"
        in rules
    )
    assert f"#{table_id} tbody tr:nth-child(2) {{ background-color: #F4F4F4; background-image: url(" in rules
    assert "background-position: left 5px;" in rules
    assert rules.count("background-image") == 1
    assert [row[0][0] for row in body_rows(out)][1::2] == ["border-top: 2px dashed #A6081A;"] * 2


def test_cutline_label_above_and_gaps(lib):
    out = gt_cutline(GT(frame(lib, CARS)), after=2, label="cut", label_position="above", gap=(4, 12))
    table_id = out._options.table_id.value
    rules = css(out)
    # above: the label sits in row 2's bottom padding (9 + 13 + the 4px gap above); row 3 gets the 12px gap below
    assert f"#{table_id} tbody tr:nth-child(2) td {{ padding-bottom: 26px !important;" in rules
    assert f"#{table_id} tbody tr:nth-child(3) td {{ padding-top: 12px !important; }}" in rules
    assert "background-position: left bottom 5px;" in rules
    assert "tr:nth-child(2) { background-image" in rules  # no striping, no row background


def test_cutline_after_zero_labels_the_first_row(lib):
    rules = css(gt_cutline(GT(frame(lib, CARS)), after=0, label="Top", label_position="above"))
    assert "tbody tr:nth-child(1) td { padding-top: 22px !important;" in rules


def test_cutline_drops_lines_outside_the_table_with_one_warning(lib):
    gt = GT(frame(lib, CARS))
    with pytest.warns(SdvplotWarning, match=r"dropped 2 cut line\(s\) at \[5, -1\]"):
        out = gt_cutline(gt, after=[5, 2, -1])
    assert [row[0][0] for row in body_rows(out)].count("border-top: 2px dashed #A6081A;") == 1
    with pytest.warns(SdvplotWarning):
        assert gt_cutline(gt, after=7) is gt
    with pytest.raises(ValueError, match="gap"):
        gt_cutline(gt, after=1, gap=(1, 2, 3))
    with pytest.raises(ValueError, match="numeric"):
        gt_cutline(gt, after=["2"])
    with pytest.raises(ValueError, match="label_position"):
        gt_cutline(gt, after=1, label_position="left")
    with pytest.raises(ValueError, match="style"):
        gt_cutline(gt, after=1, style="wavy")


def test_cutline_takes_numpy_integers_and_rejects_fractional_rows(lib):
    gt = GT(frame(lib, CARS))
    expected = ["", "", "border-top: 2px dashed #A6081A;", "", ""]
    for after in (np.int64(2), [np.int64(2)], np.array([2]), 2.0):
        assert [row[0][0] for row in body_rows(gt_cutline(gt, after=after))] == expected
    gapped = css(gt_cutline(gt, after=np.int64(2), gap=np.int64(4)))
    assert "tbody tr:nth-child(2) td { padding-bottom: 4px !important; }" in gapped
    for after in (2.5, [1, 2.5], float("nan")):
        with pytest.raises(ValueError, match="whole"):
            gt_cutline(gt, after=after)

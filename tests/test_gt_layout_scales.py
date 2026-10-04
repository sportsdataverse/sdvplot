import copy
import re

import polars as pl
import pytest

pytest.importorskip("great_tables")
from great_tables import GT, loc  # noqa: E402
from great_tables._locations import resolve_cols_c, resolve_rows_i  # noqa: E402

from sdvplot._contrast import mix  # noqa: E402
from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.great_tables import (  # noqa: E402
    gt_color_pills,
    gt_color_ranks,
    gt_legend_continuous,
    gt_legend_discrete,
    gt_percentile_bar,
    gt_tiers,
)
from tests.gt_frames import KINDS, frame  # noqa: E402

PCT = {"metric": ["Barrel %", "Exit velocity", "Chase rate"], "pct": [94.0, 41.0, None]}
SEGMENT = re.compile(r"flex:1 0 auto; (?:height:[\d.]+px; )?background-color:(#[0-9a-f]{6});")


def test_private_great_tables_api():
    # sdvplot reads these private great_tables names; this fails loudly if an upgrade moves them
    gt = GT(pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})).tab_header("T").tab_spanner("s", ["a"])
    assert resolve_cols_c(data=gt, expr=["b"]) == ["b"]
    assert [i for _, i in resolve_rows_i(gt, [1])] == [1]
    assert gt._tbl_data.columns == ["a", "b"]
    assert gt._options.table_id.value is None and gt._options.table_background_color.value == "#FFFFFF"
    assert gt._heading.title == "T" and [s.spanner_id for s in gt._spanners] == ["s"]
    tagged = copy.copy(gt)
    tagged.__dict__["_sdvplot_scale"] = {"columns": ["a"]}
    later = tagged.tab_options(table_font_size="12px").tab_style([], loc.body()).fmt_number("a").tab_source_note("n")
    assert later.__dict__["_sdvplot_scale"] == {"columns": ["a"]}  # GT._replace copies with copy.copy


def test_legend_steps_match_data_color_cells():
    palette = ["#3D8B6E", "#EDE0CC", "#BE4D3A"]
    gt = GT(pl.DataFrame({"v": [10.0, 30.0, 50.0, 70.0, 90.0]})).data_color("v", palette=palette, domain=[0, 100])
    cells = re.findall(r"<td[^>]*background-color: (#\w+)", gt.as_raw_html())
    legend = gt_legend_continuous(gt, palette=palette, domain=(0, 100), type="steps", n_bins=5)
    assert SEGMENT.findall(legend.as_raw_html()) == cells


@pytest.mark.parametrize("kind", KINDS)
def test_legend_takes_the_domain_from_columns(kind):
    gt = GT(frame(kind, {"team": ["LV", "KC"], "pts": [1250.0, 3480.4]}))
    h = gt_legend_continuous(gt, columns="pts", title="Points").as_raw_html()
    assert len(SEGMENT.findall(h)) == 60
    assert SEGMENT.findall(h)[0] == "#3d8b6e" and SEGMENT.findall(h)[-1] == "#be4d3a"
    assert "<span>1,250</span><span>3,480</span>" in h
    assert '<div style="font-size:11px;color:#666666;">Points</div>' in h
    assert 'class="gt_sourcenote"' in h


def test_legend_reads_the_scale_recorded_by_a_coloring_call():
    gt = gt_percentile_bar(GT(pl.DataFrame(PCT)), "pct", palette=["#000000", "#ffffff"], domain=(0, 50), reverse=True)
    h = gt_legend_continuous(gt, type="blocks", n_bins=2).as_raw_html()
    assert SEGMENT.findall(h) == ["#bfbfbf", "#404040"]  # reversed: white end first
    assert "<span>0</span><span>50</span>" in h
    h = gt_legend_continuous(gt, palette=["#ff0000", "#0000ff"], reverse=False, type="steps", n_bins=2).as_raw_html()
    assert SEGMENT.findall(h) == ["#bf0040", "#4000bf"]  # explicit arguments win over the record


def test_legend_matches_the_cells_of_wave_c1s_coloring_functions():
    # gt_color_ranks and gt_color_pills (wave C1) write the record; the legend's steps are the cells' colors
    palette = ["#3D8B6E", "#EDE0CC", "#BE4D3A"]
    ranks = gt_color_ranks(
        GT(pl.DataFrame({"rk": [1.0, 3.0, 5.0, 7.0, 9.0]})), "rk", palette=palette, domain=(0, 10), reverse=True
    )
    cells = re.findall(r"<td[^>]*background-color: (#\w+)", ranks.as_raw_html())
    assert SEGMENT.findall(gt_legend_continuous(ranks, type="steps", n_bins=5).as_raw_html()) == cells
    pills = gt_color_pills(
        GT(pl.DataFrame({"v": [10.0, 30.0, 50.0, 70.0, 90.0]})), "v", palette=palette, domain=(0, 100)
    )
    cells = re.findall(r"<span style='[^']*background-color: (#\w+);", pills.as_raw_html())
    assert SEGMENT.findall(gt_legend_continuous(pills, type="steps", n_bins=5).as_raw_html()) == cells


def test_legend_labels_edges_title_left_and_errors():
    gt = GT(pl.DataFrame({"x": [0.0, 1.0]}))
    h = gt_legend_continuous(
        gt, domain=(0, 1), labels="edges", n_bins=4, digits=2, title="Rate", title_position="left"
    ).as_raw_html()
    assert "<span>0.00</span><span>0.25</span><span>0.50</span><span>0.75</span><span>1.00</span>" in h
    assert "flex-direction:row; align-items:center; gap:4px;" in h
    with pytest.raises(ValueError, match="need columns or domain"):
        gt_legend_continuous(gt)
    with pytest.raises(ValueError, match="no numeric values"):
        gt_legend_continuous(GT(pl.DataFrame({"t": ["a"]})), columns="t")
    with pytest.raises(ValueError, match="type must be one of"):
        gt_legend_continuous(gt, domain=(0, 1), type="smooth")
    with pytest.raises(ValueError, match="list of hex colors"):
        gt_legend_continuous(gt, domain=(0, 1), palette="viridis::mako")


def test_legend_at_the_top_keeps_the_title_and_subtitle():
    gt = GT(pl.DataFrame({"x": [0.0, 1.0]})).tab_header("Rankings", "Week 5")
    out = gt_legend_continuous(gt, domain=(0, 1), location="top", title="Rate", title_style={"font": "Inter"})
    assert out._heading.title.text == "Rankings"
    sub = out._heading.subtitle.text
    assert sub.startswith('Week 5<div style="height:4px;"></div><div style="display:flex; justify-content:center;">')
    assert "fonts.googleapis.com/css2?family=Inter" in out.as_raw_html()
    bare = gt_legend_continuous(GT(pl.DataFrame({"x": [0.0]})), domain=(0, 1), location="top")
    assert bare._heading.title.text.startswith('<div style="display:flex; justify-content:center;">')


@pytest.mark.parametrize("kind", KINDS)
def test_discrete_key_from_a_mapping_or_a_frame(kind):
    gt = GT(frame(kind, {"game": ["@ KC", "BUF"]}))
    h = gt_legend_discrete(gt, {"Home": "#CCE7F5", "Away": "#eeeeee"}).as_raw_html()
    darker = mix("#cce7f5", "#000000", 0.18)
    assert (
        '<span style="display:inline-block; width:14px; height:14px; background-color:#cce7f5; border-radius:0px; '
        f'border:1px solid {darker};"></span><span style="font-size:12px;color:#000000;">Home</span>'
    ) in h
    key = frame(kind, {"label": ["Home", "Away"], "color": ["#cce7f5", "#eeeeee"]})
    assert gt_legend_discrete(gt, key).as_raw_html().count("background-color:#cce7f5") == 1
    positional = frame(kind, {"c": ["#cce7f5"], "l": ["Home"]})
    assert ">Home</span>" in gt_legend_discrete(gt, positional).as_raw_html()


def test_discrete_key_inside_labels_and_a_dark_table():
    gt = GT(pl.DataFrame({"x": [1]})).tab_options(table_background_color="#111111").tab_header("Title")
    out = gt_legend_discrete(gt, {"Win": "#1a7f37", "Loss": "#f2f2f2"}, label_placement="inside", shape="circle")
    sub = out._heading.subtitle.text  # key only: rides under the existing title
    assert "background-color:#1a7f37; border-radius:7px;" in sub and 'color:#ffffff;">Win</span>' in sub
    assert 'color:#000000;">Loss</span>' in sub
    headed = gt_legend_discrete(gt, {"Win": "#1a7f37"}, heading="Result", location="top")
    assert "Title" not in headed._heading.title.text  # a heading replaces the header
    assert '<div style="font-size:16px;color:#ffffff;font-weight:600;">Result</div>' in headed._heading.title.text


def test_discrete_key_errors():
    gt = GT(pl.DataFrame({"x": [1]}))
    with pytest.raises(ValueError, match="no key is recorded"):
        gt_legend_discrete(gt)
    with pytest.raises(TypeError, match="mapping of label to color"):
        gt_legend_discrete(gt, ["#cce7f5"])
    with pytest.raises(ValueError, match="not a hex color"):
        gt_legend_discrete(gt, {"Home": "blue"})


@pytest.mark.parametrize("kind", KINDS)
def test_percentile_bars_draw_values_and_a_missing_row(kind):
    gt = gt_percentile_bar(GT(frame(kind, PCT)), "pct")
    h = gt.as_raw_html()
    assert h.count('<div style="position:relative; width:100%; height:26px;">') == 2
    assert "left:calc(11.00px + 0.9400 * (100% - 22.00px));" in h
    assert "background:#d14058; color:#FFFFFF; font-size:11.0px; font-weight:700;" in h and ">94</div>" in h
    assert ">—</span>" in h  # the missing row: a broken track with an em dash
    assert "width:220px" in h
    assert gt.__dict__["_sdvplot_scale"] == {
        "columns": ["pct"],
        "palette": ["#3661AD", "#C9C9C9", "#D22D49"],
        "domain": (0.0, 100.0),
        "reverse": False,
        "pal_type": "discrete",
    }


def test_percentile_bar_proportions_are_decided_per_column():
    df = pl.DataFrame({"share": [0.5, 0.9], "pct": [30.0, 60.0]})
    h = gt_percentile_bar(GT(df), ["share", "pct"]).as_raw_html()
    printed = re.findall(r"text-align:center;\">(\d+)</div>", h)
    assert printed == ["50", "30", "90", "60"]  # share is read as proportions, pct as percentiles
    kept = gt_percentile_bar(GT(df), "share", scale="none", decimals=2).as_raw_html()
    assert re.findall(r"text-align:center;\">([\d.]+)</div>", kept) == ["0.50", "0.90"]


def test_percentile_bar_rows_and_the_input_table():
    gt = GT(pl.DataFrame(PCT))
    out = gt_percentile_bar(gt, "pct", rows=pl.col("metric") == "Barrel %")
    h = out.as_raw_html()
    assert h.count("position:relative") == 1 and ">41.0</td>" in h  # other rows keep their value
    assert "_sdvplot_scale" not in gt.__dict__  # the input is never mutated
    with pytest.warns(SdvplotWarning, match="rows matched no rows"):
        same = gt_percentile_bar(gt, "pct", rows=pl.col("metric") == "nope")
    assert same is gt


@pytest.mark.parametrize("kind", KINDS)
def test_tiers_fill_each_tier_and_record_the_key(kind):
    df = frame(kind, {"tier": ["S", "A", "B"], "t1": ["https://cdn/1.png", "https://cdn/2.png", None]})
    out = gt_tiers(GT(df), {"S": "#C84630", "A": "#5DA271", "B": "#F2E86D"})
    h = out.as_raw_html()
    # the theme (wave B) adds its own cell styles and a table id, so match the tier fills inside the style attribute
    assert re.search(r'style="[^"]*background-color: #c84630; color: #ffffff;font-weight: bold;"[^>]*>S</td>', h)
    assert re.search(r'style="[^"]*background-color: #f2e86d; color: #000000;font-weight: bold;"[^>]*>B</td>', h)
    assert '<img src="https://cdn/1.png" style="height: 55px;vertical-align: middle;">' in h
    assert re.findall(r'scope="col" id="(?:\w+-)?(\w+)">([^<]*)</th>', h) == [("tier", ""), ("t1", "")]
    assert out.__dict__["_sdvplot_key"] == {"S": "#c84630", "A": "#5da271", "B": "#f2e86d"}
    assert "background-color:#5da271" in gt_legend_discrete(out).as_raw_html()


def test_tiers_two_lists_warnings_and_errors():
    gt = GT(pl.DataFrame({"tier": ["S", "A"], "logo": ["https://cdn/1.png", "https://cdn/2.png"]}))
    with pytest.warns(SdvplotWarning, match=r"tier\(s\) \['C'\] are not in 'tier'"):
        gt_tiers(gt, ["S", "A", "C"], ["#C84630", "#5DA271", "#000000"])
    with pytest.raises(ValueError, match="colors is missing"):
        gt_tiers(gt, ["S", "A"])
    with pytest.raises(ValueError, match="same length"):
        gt_tiers(gt, ["S", "A"], ["#C84630"])
    with pytest.raises(ValueError, match="'rank' is not a column"):
        gt_tiers(gt, {"S": "#C84630"}, tier_column="rank")

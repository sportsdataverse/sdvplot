import re

import numpy as np
import polars as pl
import pytest

pytest.importorskip("great_tables")
from great_tables import GT  # noqa: E402

from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.great_tables import (  # noqa: E402
    gt_outliers,
    gt_row_accent,
    gt_significance,
    gt_spotlight,
    gt_theme_midnight,
)
from tests.gt_frames import KINDS, frame  # noqa: E402

TEAMS = {"team": ["LV", "KC", "BUF"], "wins": [10, 12, 11], "color": ["#A5ACAF", "#E31837", "#00338D"]}


def rows_of(gt):
    return [r.strip() for r in re.findall(r"<tr>(.*?)</tr>", gt.as_raw_html().replace("\n", ""))]


def source_notes(gt):
    notes = re.findall(r'class="gt_sourcenote"[^>]*>(.*?)</td>', gt.as_raw_html(), re.S)
    return [re.sub(r'^<span class="gt_from_md">(.*)</span>$', r"\1", n.strip()) for n in notes]


def test_private_boxhead_api():
    # gt_row_accent / gt_spotlight read the private boxhead to find the visible columns and the stub
    gt = GT(pl.DataFrame(TEAMS), rowname_col="team").cols_hide("color")
    assert [(c.var, c.type.name) for c in gt._boxhead] == [("team", "stub"), ("wins", "default"), ("color", "hidden")]


@pytest.mark.parametrize("kind", KINDS)
def test_spotlight_lights_the_rows_and_dims_the_rest(kind):
    gt = gt_spotlight(GT(frame(kind, TEAMS)), [1], columns=["team", "wins"], fill="#fff3c4", accent_color="#E31837")
    lv, kc, buf = rows_of(gt)
    assert lv.count('style="color: #737373 !important;"') == 3 and buf.count('style="color: #737373 !important;"') == 3
    assert (
        '<td style="background-color: #fff3c4 !important; font-weight: bold !important; border-left: 4px solid #E31837 !important;"'
        in kc
    )
    assert (
        '<td style="background-color: #fff3c4 !important; font-weight: bold !important;" class="gt_row gt_right">12</td>'
        in kc
    )
    assert (
        '<td style="color: #737373 !important;" class="gt_row gt_left">#E31837</td>' in kc
    )  # outside `columns`: dimmed


@pytest.mark.parametrize("kind", KINDS)
def test_numpy_integer_rows_are_positions(kind):
    # great_tables' row resolver silently skips numpy integers; the shared _rows helper turns them into ints
    gt = GT(frame(kind, TEAMS))
    assert rows_of(gt_spotlight(gt, [np.int64(1)])) == rows_of(gt_spotlight(gt, [1]))
    assert rows_of(gt_spotlight(gt, np.int64(1))) == rows_of(gt_spotlight(gt, 1))
    assert rows_of(gt_row_accent(gt, "team", rows=[np.int64(0)])) == rows_of(gt_row_accent(gt, "team", rows=[0]))


def test_spotlight_takes_a_polars_expression_and_an_accent_column():
    gt = gt_spotlight(GT(pl.DataFrame(TEAMS)), pl.col("wins") > 10, dim_color=None, accent_color="#000000",
                      accent_column="wins")  # fmt: skip
    lv, kc, buf = rows_of(gt)
    assert "#737373" not in lv and "font-weight: bold" not in lv
    assert 'font-weight: bold !important; border-left: 4px solid #000000 !important;" class="gt_row gt_right">12' in kc
    assert 'font-weight: bold !important; border-left: 4px solid #000000 !important;" class="gt_row gt_right">11' in buf


def test_spotlight_with_no_matching_rows():
    gt = GT(pl.DataFrame(TEAMS))
    with pytest.warns(SdvplotWarning, match="if_none='dim'"):
        assert gt_spotlight(gt, pl.col("team") == "NYJ") is gt
    assert gt_spotlight(gt, pl.col("team") == "NYJ", if_none="ignore") is gt
    dimmed = gt_spotlight(gt, pl.col("team") == "NYJ", if_none="dim")
    assert sum(r.count("color: #737373 !important;") for r in rows_of(dimmed)) == 9
    with pytest.warns(SdvplotWarning, match="accent_column matched no rendered column"):
        gt_spotlight(gt.cols_hide("wins"), [0], accent_color="#000000", accent_column="wins")


def test_spotlight_dims_the_other_rows_to_a_tone_that_still_passes_wcag_aa():
    # sdvplotR #61: gtUtils dimmed to a fixed #BBBBBB, 1.9:1 on white; "auto" blends the table's text toward its
    # background until it clears 4.5:1 (R's .theme_secondary_on: #737373 on white)
    from sdvplot._contrast import contrast, on_color

    for tbl in (GT(pl.DataFrame(TEAMS)), gt_theme_midnight(GT(pl.DataFrame(TEAMS)))):
        bg = str(tbl._options.table_background_color.value or "#ffffff")
        lv, kc, buf = rows_of(gt_spotlight(tbl, [1]))
        assert "font-weight: bold" in kc and "font-weight: bold" not in lv + buf
        dim = {m for m in re.findall(r"color: (#[0-9a-fA-F]{6}) !important", lv + buf)}
        assert len(dim) == 1
        (dim,) = dim
        assert contrast(dim, bg) >= 4.5
        assert contrast(dim, bg) < contrast(on_color(bg), bg) / 2  # still muted next to full-strength text
    assert "#737373" in rows_of(gt_spotlight(GT(pl.DataFrame(TEAMS)), [1]))[0]
    # a color you pass is used as is
    assert (
        'style="color: #BBBBBB !important;"'
        in rows_of(gt_spotlight(GT(pl.DataFrame(TEAMS)), [1], dim_color="#BBBBBB"))[0]
    )


def test_secondary_on_matches_sdvplotr_on_the_same_backgrounds():
    # sdvplotR's .theme_secondary_on(bg, .theme_on_color(bg), 4.5) (R/utils-theme.R, origin/main 45daa5d)
    from sdvplot._contrast import on_color
    from sdvplot.great_tables._marks import _secondary_on

    r = {"#FFFFFF": "#737373", "#1e1e1e": "#8e8e8e", "#0B1220": "#797d84", "#0D1117": "#7a7c7f", "#000000": "#808080",
         "#F5F5F5": "#6e6e6e", "#002244": "#8090a2"}  # fmt: skip
    assert {bg: _secondary_on(bg, on_color(bg)) for bg in r} == r


@pytest.mark.parametrize("kind", KINDS)
def test_row_accent_reads_colors_from_a_column_and_hides_it(kind):
    gt = gt_row_accent(GT(frame(kind, TEAMS)), "color")
    lv, kc, buf = rows_of(gt)
    assert lv.startswith('<td style="border-left: 4px solid #A5ACAF !important;" class="gt_row gt_left">LV</td>')
    assert "border-left: 4px solid #00338D !important;" in buf
    assert 'id="color"' not in gt.as_raw_html()


def test_row_accent_maps_a_palette_onto_the_stub():
    df = pl.DataFrame({"team": ["Clemson", "Georgia", "Duke", "Army"], "conf": ["ACC", "SEC", "ACC", None]})
    gt = GT(df, rowname_col="team")
    mapped = rows_of(gt_row_accent(gt, "conf", palette={"ACC": "#003366", "SEC": "#B8232F"}, side="right"))
    assert mapped[0].startswith(
        '<th style="border-right: 4px solid #003366 !important;" class="gt_row gt_left gt_stub">'
    )
    assert "border" not in mapped[3]  # a missing key draws no bar (na_color "transparent")
    recycled = rows_of(gt_row_accent(gt, "conf", palette=["#111111"], rows=[1, 2], width=6, hide=False))
    assert "border" not in recycled[0]
    assert 'style="border-left: 6px solid #111111 !important;"' in recycled[1] and "#111111" in recycled[2]
    with pytest.warns(SdvplotWarning, match="rows matched no rows"):
        gt_row_accent(gt, "conf", rows=pl.col("conf") == "B1G")
    with pytest.raises(ValueError, match="exactly one column"):
        gt_row_accent(GT(df), ["team", "conf"])


@pytest.mark.parametrize("kind", KINDS)
def test_outliers_flag_by_iqr_with_a_symbol_and_note(kind):
    df = frame(kind, {"team": list("ABCDEFG"), "pts": [21, 24, 20, 23, 22, 25, 61], "name": list("abcdefg")})
    gt = gt_outliers(GT(df), ["pts", "name"], symbol="†", note=True)
    h = gt.as_raw_html()
    assert '<td style="color: #B3261E !important; font-weight: bold !important;" class="gt_row gt_right">61†</td>' in h
    assert h.count("#B3261E") == 1
    assert source_notes(gt) == ["Marked values fall outside 1.5 × IQR of the column quartiles."]


def test_outliers_sd_bounds_sides_and_fill():
    df = pl.DataFrame({"v": [1.0, 2.0, 3.0, 4.0, 100.0, -50.0]})
    low_only = gt_outliers(GT(df), "v", method="bounds", bounds=(0, None), side="low", note=True)
    assert "-50.0" in rows_of(low_only)[5] and "#B3261E" in rows_of(low_only)[5]
    assert "#B3261E" not in rows_of(low_only)[4]
    assert source_notes(low_only) == ["Marked values fall outside 0–NA (low side only)."]
    sd = gt_outliers(GT(df), "v", method="sd", threshold=1, fill="#B3261E", note="custom")
    assert (
        'style="color: #ffffff !important; font-weight: bold !important; background-color: #B3261E !important;"'
        in rows_of(sd)[4]
    )
    assert source_notes(sd) == ["custom"]
    assert gt_outliers(GT(df), "v", method="sd").as_raw_html().count("#B3261E") == 0  # nothing beyond 3 sd


def test_outliers_errors_and_no_numeric_columns():
    gt = GT(pl.DataFrame({"name": ["a", "b"]}))
    with pytest.warns(SdvplotWarning, match="no numeric columns"):
        assert gt_outliers(gt, "name") is gt
    with pytest.raises(ValueError, match="bounds must be"):
        gt_outliers(gt, "name", method="bounds")


@pytest.mark.parametrize("kind", KINDS)
def test_significance_pairs_each_estimate_with_its_own_p_column(kind):
    data = {"term": ["epa", "wpa", "cpoe"], "est": [0.42, 0.08, 1.5], "p": [0.004, 0.2, 0.03],
            "est2": [1.0, 2.0, 3.0], "p2": [0.5, 0.06, None]}  # fmt: skip
    gt = gt_significance(GT(frame(kind, data)).fmt_number("est"), ["est", "est2"], ["p", "p2"])
    epa, wpa, cpoe = rows_of(gt)
    star = "<sup style='font-size:0.7em;'>{}</sup>"
    assert f">0.42{star.format('***')}</td>" in epa and ">1.0</td>" in epa
    assert ">0.08</td>" in wpa and f">2.0{star.format('*')}</td>" in wpa
    assert f">1.50{star.format('**')}</td>" in cpoe and ">3.0</td>" in cpoe
    assert 'id="p"' not in gt.as_raw_html() and 'id="p2"' not in gt.as_raw_html()
    assert source_notes(gt) == ["*** p < 0.01, ** p < 0.05, * p < 0.1"]


def test_significance_plain_stars_custom_levels_and_errors():
    df = pl.DataFrame({"est": [1.0, 2.0], "p": [0.04, 0.2]})
    gt = gt_significance(GT(df), "est", "p", levels=[0.05], symbols=["+"], superscript=False, legend=False,
                         hide_p=False)  # fmt: skip
    assert ">1.0+</td>" in rows_of(gt)[0] and source_notes(gt) == [] and 'id="p"' in gt.as_raw_html()
    with pytest.raises(ValueError, match="ascending"):
        gt_significance(GT(df), "est", "p", levels=[0.1, 0.05], symbols=["*", "**"])
    with pytest.raises(ValueError, match="same length"):
        gt_significance(GT(df), "est", "p", levels=[0.1], symbols=["*", "**"])
    with pytest.raises(ValueError, match="must pair"):
        gt_significance(GT(df), "est", ["p", "est"])

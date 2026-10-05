import re

import pandas as pd
import polars as pl
import pytest

pytest.importorskip("great_tables")
from great_tables import GT, loc  # noqa: E402

import sdvplot  # noqa: E402
import sdvplot.great_tables as sgt  # noqa: E402
from sdvplot import _placement  # noqa: E402
from sdvplot._dispatch import adapter_for  # noqa: E402
from sdvplot._errors import SdvplotWarning, UnresolvedTeamError  # noqa: E402
from sdvplot.great_tables import (  # noqa: E402
    _marks,
    gt_merge_stack_team_color,
    gt_sdv_cols_label,
    gt_sdv_headshots,
    gt_sdv_logos,
    gt_sdv_wordmarks,
    gt_theme_sdv,
    gt_theme_sdv_team,
)

LV_IMG = (
    '<img src="https://cdn/1111.png" style="height:30px;vertical-align:middle" alt="Las Vegas Raiders" '
    'data-sdvplot-team="13">'
)


def _frame(kind, data, index=None):
    """The same data as a polars frame, or a pandas frame with a non-default index."""
    if kind == "polars":
        return pl.DataFrame(data)
    n = len(next(iter(data.values())))
    return pd.DataFrame(data, index=index or [10 + i for i in range(n)])


FRAMES = pytest.mark.parametrize("kind", ["polars", "pandas"])


def _cells(gt):
    return [c[:3] for c in sgt.drawn_cells(gt)]


def test_the_front_door_routes_a_gt_to_gt_sdv_logos(manifest):
    gt = GT(pl.DataFrame({"team": ["LV", "LAR"]}))
    assert adapter_for(gt) is sgt
    assert _cells(sdvplot.add_logos(gt, "team", league="nfl")) == [("13", 0, "team"), ("14", 1, "team")]
    gt = GT(pl.DataFrame({"team": ["LV", "LAC"]}))
    assert _cells(sdvplot.add_wordmarks(gt, "team", league="nfl", height=20)) == [("13", 0, "team"), ("24", 1, "team")]


def test_axis_logos_on_a_table_is_a_type_error():
    with pytest.raises(TypeError, match="no axes"):
        sdvplot.axis_logos(GT(pl.DataFrame({"team": ["LV"]})), "x", league="nfl")


def test_the_private_great_tables_attributes_sdvplot_reads_still_exist():
    """gt_merge_stack_team_color reads GT._tbl_data and the themes read the table id: pin both (spec T4)."""
    pf, df = pl.DataFrame({"team": ["LV"]}), pd.DataFrame({"team": ["LV"]}, index=[7])
    assert GT(pf)._tbl_data is pf
    assert GT(df)._tbl_data is df
    assert GT(pf)._options.table_id.value is None
    assert GT(pf).with_id("t1")._options.table_id.value == "t1"


@FRAMES
def test_logo_cells_are_img_tags_with_the_archive_url(manifest, kind):
    html = gt_sdv_logos(GT(_frame(kind, {"team": ["LV"], "w": [3]})), "team", league="nfl").as_raw_html()
    assert LV_IMG in html


def test_include_name_keeps_the_text_after_the_logo(manifest):
    html = gt_sdv_logos(GT(pl.DataFrame({"team": ["LV"]})), "team", league="nfl", include_name=True).as_raw_html()
    assert re.search(r'<img [^>]*margin-right:0\.35em[^>]*data-sdvplot-team="13">LV</td>', html)


def test_a_season_shows_that_eras_mark(manifest):
    html = gt_sdv_logos(GT(pl.DataFrame({"team": ["LV"]})), "team", league="nfl", season=2010).as_raw_html()
    assert 'src="https://cdn/3333.png"' in html
    with pytest.raises(ValueError, match="season"):
        gt_sdv_logos(GT(pl.DataFrame({"team": ["LV"]})), "team", league="nfl", season=[2010, 2011])


def test_unknown_values_warn_when_called_not_when_rendered(manifest):
    with pytest.warns(SdvplotWarning, match="'XXX'"):
        gt = gt_sdv_logos(GT(pl.DataFrame({"team": ["XXX", "LV"]})), "team", league="nfl")
    html = gt.as_raw_html()  # SdvplotWarning is an error in this suite: a render-time warning would fail here
    assert ">XXX</td>" in html and LV_IMG in html


def test_cell_text_is_unescaped_before_resolving(manifest):
    """great_tables hands a transform "A&amp;M"; the value resolved (and named in the warning) is "A&M"."""
    with pytest.warns(SdvplotWarning, match="'A&M'"):
        gt = gt_sdv_logos(GT(pl.DataFrame({"team": ["A&M", "LV"]})), "team", league="nfl")
    assert ">A&amp;M</td>" in gt.as_raw_html()


def test_a_pandas_id_column_with_a_gap_still_resolves(manifest):
    """pandas stores [13, None, 14] as floats, so cells read "13.0": still team 13, and the gap is no warning."""
    df = pd.DataFrame({"id": [13, None, 14]}, index=[4, 5, 6])
    assert _cells(gt_sdv_logos(GT(df), "id", league="nfl")) == [("13", 0, "id"), ("14", 2, "id")]


def test_a_repeated_team_is_resolved_once(manifest, monkeypatch):
    calls = []
    real = _placement.select_mark
    monkeypatch.setattr(_placement, "select_mark", lambda *a, **k: calls.append(a[0]) or real(*a, **k))
    gt = gt_sdv_logos(GT(pl.DataFrame({"team": ["LV"] * 50})), "team", league="nfl")
    assert len(sgt.drawn_cells(gt)) == 50 and calls == ["13"]


def test_logos_in_the_stub_and_row_group_labels(manifest):
    df = pl.DataFrame({"team": ["LV", "LAR"], "conf": ["LV", "LAR"], "w": [1, 2]})
    html = gt_sdv_logos(GT(df, rowname_col="team"), None, league="nfl", locations=loc.stub()).as_raw_html()
    assert re.search(r'<th class="gt_row gt_left gt_stub"><img [^>]*data-sdvplot-team="13">', html)
    grouped = GT(df, groupname_col="conf")
    html = gt_sdv_logos(grouped, None, league="nfl", locations=loc.row_groups()).as_raw_html()
    assert re.search(r'<th class="gt_group_heading" colspan="\d+"><img [^>]*data-sdvplot-team="14">', html)
    # drawn_cells counts data rows only: a group heading is not a row
    assert _cells(gt_sdv_logos(grouped, "team", league="nfl")) == [("13", 0, "team"), ("14", 1, "team")]


@FRAMES
def test_wordmark_cells_use_the_wordmark(manifest, kind):
    gt = gt_sdv_wordmarks(GT(_frame(kind, {"team": ["LV", "LAC"]})), "team", league="nfl", height=20)
    assert [(c[0], c[3], c[4]) for c in sgt.drawn_cells(gt)] == [
        ("13", 20.0, "https://cdn/4444.png"),
        ("24", 20.0, "https://cdn/d2.png"),
    ]


@FRAMES
def test_headshot_cells_use_the_espn_headshot(kind):
    gt = gt_sdv_headshots(GT(_frame(kind, {"player": ["3139477"]})), "player", league="nfl", height=40)
    html = gt.as_raw_html()
    assert sgt.drawn_cells(gt) == [("3139477", 0, "player", 40.0, sdvplot.headshot_url("3139477", "nfl"))]
    assert 'alt="3139477"' in html


def test_a_data_frame_instead_of_a_gt_is_a_clear_type_error():
    with pytest.raises(TypeError, match=r"It looks like raw data: wrap it in great_tables\.GT\(\) first"):
        gt_sdv_logos(pl.DataFrame({"team": ["LV"]}), "team", league="nfl")


@FRAMES
def test_cols_label_puts_marks_in_team_named_column_labels(manifest, kind):
    gt = GT(_frame(kind, {"LV": [1], "LAR": [2], "rank": [1]}))
    out = gt_sdv_cols_label(gt, ["LV", "LAR"], league="nfl", height=24)
    assert sgt.drawn_cells(out) == [
        ("13", -1, "LV", 24.0, "https://cdn/1111.png"),
        ("14", -1, "LAR", 24.0, "https://cdn/6666.png"),
    ]


def test_cols_label_warns_for_columns_that_are_not_teams_and_keeps_their_labels(manifest):
    gt = GT(pl.DataFrame({"LV": [1], "rank": [1]})).cols_label(rank="Rank")
    with pytest.warns(SdvplotWarning, match="'rank'"):
        out = gt_sdv_cols_label(gt, league="nfl")
    assert [c[2] for c in sgt.drawn_cells(out)] == ["LV"]
    assert ">Rank</th>" in out.as_raw_html()


def test_cols_label_wordmarks_and_headshots(manifest):
    out = gt_sdv_cols_label(GT(pl.DataFrame({"LV": [1]})), league="nfl", mark_type="wordmark")
    assert sgt.drawn_cells(out)[0][4] == "https://cdn/4444.png"
    out = gt_sdv_cols_label(GT(pl.DataFrame({"3139477": [1]})), league="nfl", mark_type="headshot")
    assert sgt.drawn_cells(out)[0][:3] == ("3139477", -1, "3139477")
    with pytest.raises(ValueError, match="mark_type"):
        gt_sdv_cols_label(GT(pl.DataFrame({"LV": [1]})), league="nfl", mark_type="helmet")


@FRAMES
def test_merge_stack_puts_the_bottom_line_in_the_team_color(kind):
    df = _frame(kind, {"team": ["LV", "LAR"], "mascot": ["Raiders", "Rams"], "w": [1, 2]})
    html = gt_merge_stack_team_color(GT(df), "team", "mascot", "team", league="nfl").as_raw_html()
    assert "font-weight:bold;font-variant:small-caps;color:black;font-size:14px'>LV</span>" in html
    assert "font-weight:bold;color:#003594;font-size:12px'>Rams</span>" in html
    assert 'id="mascot"' not in html  # col2 is hidden
    assert html.index("'>LV</span>") < html.index("'>LAR</span>")  # each row keeps its own cell


def test_merge_stack_pairs_survive_row_groups_that_reorder_rows():
    df = pl.DataFrame(
        {"team": ["LV", "LAR", "LAC"], "mascot": ["Raiders", "Rams", "Chargers"], "conf": ["A", "N", "A"]}
    )
    html = gt_merge_stack_team_color(GT(df, groupname_col="conf"), "team", "mascot", "team", league="nfl").as_raw_html()
    assert "color:#000000;font-size:12px'>Raiders<" in html
    assert "color:#0080c6;font-size:12px'>Chargers<" in html
    assert "color:#003594;font-size:12px'>Rams<" in html
    assert html.index(">Raiders<") < html.index(">Chargers<") < html.index(">Rams<")  # group order, paired by row


def test_merge_stack_greys_an_unknown_team_and_escapes_text():
    df = pl.DataFrame({"team": ["XXX"], "mascot": ["<b>Nobody</b>"]})
    with pytest.warns(SdvplotWarning, match="'XXX'"):
        gt = gt_merge_stack_team_color(GT(df), "team", "mascot", "team", league="nfl")
    assert "color:grey;font-size:12px'>&lt;b&gt;Nobody&lt;/b&gt;</span>" in gt.as_raw_html()
    with pytest.raises(ValueError, match="'nope' is not a column"):
        gt_merge_stack_team_color(GT(df), "team", "nope", "team", league="nfl")


def _theme_css(html):
    return html[: html.index("</style>")]


@FRAMES
def test_the_light_theme(kind):
    gt = GT(_frame(kind, {"team": ["LV"], "w": [1]})).tab_header("AFC West", "Standings").tab_source_note("ESPN")
    html = gt_theme_sdv(gt).as_raw_html()
    tid = re.search(r'<div id="([^"]+)"', html).group(1)
    assert f'#{tid} thead::after {{content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 4px; ' in html
    assert "background: linear-gradient(90deg, #3346F0, #7FE6DC);}" in html
    assert f"#{tid} td {{ font-variant-numeric: tabular-nums; }}" in html
    assert "family=Chivo" in html and "family=Lato" in html
    assert re.search(r'gt_title[^>]*style="color: #0B1A33;font-family: Chivo;font-size: 22px;font-weight: 800;"', html)
    assert "background-color: #FFFFFF" in _theme_css(html)


def test_spanners_are_set_like_column_labels():
    gt = GT(pl.DataFrame({"a": [1], "b": [2]})).tab_spanner("Record", ["a", "b"]).with_id("sp")
    css = _theme_css(gt_theme_sdv(gt).as_raw_html())
    rule = "#sp .gt_column_spanner {font-family: Chivo, sans-serif; font-weight: 500; font-size: 13px; color: #16305C;}"
    assert rule in css and css.rindex("#sp .gt_column_spanner") == css.index(rule)  # ours is the last rule, so it wins


def test_the_dark_theme_sets_the_table_on_navy():
    html = gt_theme_sdv(GT(pl.DataFrame({"w": [1]})).tab_header("T"), style="dark").as_raw_html()
    assert "background-color: #0B1A33" in _theme_css(html)
    assert re.search(r'gt_title[^>]*style="color: #FFFFFF;', html)


def test_density_scales_type_and_padding():
    social = gt_theme_sdv(GT(pl.DataFrame({"w": [1]})).tab_header("T"), density="social").as_raw_html()
    assert "font-size: 28.8px" in social  # title 22px * 34/26
    compact = _theme_css(gt_theme_sdv(GT(pl.DataFrame({"w": [1]})), density="compact").as_raw_html())
    assert "padding-top: 3.5px" in compact  # data rows 7px * 3/6
    with pytest.raises(ValueError, match="density"):
        gt_theme_sdv(GT(pl.DataFrame({"w": [1]})), density="roomy")
    with pytest.raises(ValueError, match="style"):
        gt_theme_sdv(GT(pl.DataFrame({"w": [1]})), style="sepia")


def test_tab_options_override_the_theme_and_an_existing_id_is_kept():
    html = gt_theme_sdv(GT(pl.DataFrame({"w": [1]})).with_id("mine"), table_font_size="20px").as_raw_html()
    assert "#mine thead::after" in html and "font-size: 20px" in _theme_css(html)


def test_the_team_theme_wears_the_teams_colors():
    html = gt_theme_sdv_team(GT(pl.DataFrame({"w": [1]})).tab_header("Rams", "2024"), "LAR", league="nfl").as_raw_html()
    css = _theme_css(html)
    assert "background-color: #003594" in css  # the title block, primary
    assert "background: #ffa300;}" in html  # the line, secondary
    assert re.search(r'gt_title[^>]*style="color: #ffffff;', html)  # readable ink on the primary
    sub = re.search(r'gt_subtitle[^>]*style="color: (#[0-9a-f]{6});', html).group(1)
    assert sub not in ("#ffffff", "#003594") and _marks.contrast(sub, "#003594") >= 4.5


def test_a_pale_secondary_gives_way_to_the_primary_for_the_line():
    html = gt_theme_sdv_team(GT(pl.DataFrame({"w": [1]})), "Alabama", league="cfb").as_raw_html()
    assert "background: #9e1b32;}" in html  # Alabama's secondary is white


def test_the_team_theme_without_a_team_and_its_errors(monkeypatch):
    # navy title block; the cyan secondary is too pale on white (1.47:1 < 1.5), so the line is navy too, as in R
    html = gt_theme_sdv_team(GT(pl.DataFrame({"w": [1]})), league="nfl").as_raw_html()
    assert "background-color: #0B1A33" in _theme_css(html) and "background: #0B1A33;}" in html
    with pytest.raises(UnresolvedTeamError):
        gt_theme_sdv_team(GT(pl.DataFrame({"w": [1]})), "XXX", league="nfl")
    with pytest.raises(TypeError, match="one team"):
        gt_theme_sdv_team(GT(pl.DataFrame({"w": [1]})), ["LV", "LAR"], league="nfl")
    monkeypatch.setattr(_marks, "team_colors", lambda *a, **k: None)
    with pytest.warns(SdvplotWarning, match="no colors on file"):
        html = gt_theme_sdv_team(GT(pl.DataFrame({"w": [1]})), "LV", league="nfl").as_raw_html()
    assert "background: #0B1A33;}" in html


@pytest.mark.parametrize(
    "scoped",
    [
        lambda gt: sgt.gt_theme_sdv(gt),  # wave A
        lambda gt: sgt.gt_theme_almanac(gt),  # wave B
        lambda gt: sgt.gt_border_grid(gt),  # wave C1
        lambda gt: sgt.gt_watermark(gt, "DRAFT"),  # wave C2
    ],
    ids=["gt_theme_sdv", "gt_theme_almanac", "gt_border_grid", "gt_watermark"],
)
def test_a_table_with_an_empty_id_gets_a_random_one_for_its_scoped_css(scoped):
    """An empty id scopes nothing ("# td" selects no cell), so every helper that scopes CSS assigns one."""
    html = scoped(GT(pl.DataFrame({"w": [1]}), id="")).as_raw_html()
    table_id = re.search(r'<div id="([^"]*)"', html).group(1)
    assert table_id and f"#{table_id} " in html


RAW = pl.DataFrame({"team": ["LV"], "w": [1]})


@pytest.mark.parametrize(
    ("call", "arg"),
    [
        (lambda: gt_sdv_logos(RAW, "team", league="nfl"), "gt"),  # wave A
        (lambda: sgt.gt_theme_kenpom(RAW), "gt"),  # wave B
        (lambda: sgt.gt_bold_rows(RAW), "gt"),  # wave C1
        (lambda: sgt.gt_title_header(RAW, "Week 5"), "gt"),  # wave C2
        (lambda: sgt.gt_save_crop(RAW), "data"),  # wave D
    ],
    ids=["A", "B", "C1", "C2", "D"],
)
def test_every_wave_refuses_raw_data_with_one_message(call, arg):
    want = (
        f"{arg} must be a great_tables GT, not DataFrame. It looks like raw data: wrap it in great_tables.GT() first."
    )
    with pytest.raises(TypeError) as err:
        call()
    assert str(err.value) == want


def test_every_wave_words_a_bad_density_and_style_key_alike():
    with pytest.raises(ValueError) as a:
        gt_theme_sdv(GT(RAW), density="roomy")  # wave A
    with pytest.raises(ValueError) as b:
        sgt.gt_theme_kenpom(GT(RAW), density="roomy")  # wave B
    assert str(a.value) == str(b.value) == "density must be 'comfortable', 'compact' or 'social', not 'roomy'"
    with pytest.raises(ValueError) as c:
        sgt.gt_title_header(GT(RAW), "Week 5", title_style={"colour": "red"})  # wave C2
    with pytest.raises(ValueError) as d:
        sgt.gt_grid([GT(RAW)], title="T", title_style={"colour": "red"})  # wave D
    assert str(c.value) == str(d.value) and str(c.value).startswith("title_style has unknown key(s) ['colour']")


@pytest.mark.parametrize("fn", [gt_sdv_logos, gt_sdv_wordmarks, gt_sdv_headshots])
def test_locations_are_body_stub_or_row_groups_only(fn):
    """great_tables' text_transform reaches only those three; column labels came out as escaped <img> text and any
    other location (a title, a source note) was silently ignored."""
    gt = GT(pl.DataFrame({"LV": ["LV"]})).tab_header("LV")
    with pytest.raises(ValueError, match=r"gt_sdv_cols_label\(\)"):
        fn(gt, None, league="nfl", locations=loc.column_labels())
    with pytest.raises(ValueError, match=r"loc\.body\(\), loc\.stub\(\) or loc\.row_groups\(\).*not LocTitle"):
        fn(gt, None, league="nfl", locations=[loc.body(), loc.title()])


def test_drawn_cells_leaves_out_images_in_the_footer(manifest):
    """Not a bug (round-5 review): great_tables puts source notes and footnotes in <tfoot>, whose cells are not
    gt_row cells, so their images are never read as body cells."""
    from great_tables import html as gt_html

    from sdvplot._tables import img_tag

    mark = gt_html(img_tag("https://cdn/1111.png", 30, "Las Vegas Raiders", team="13"))
    gt = gt_sdv_logos(GT(pl.DataFrame({"team": ["LAR"]})), "team", league="nfl")
    gt = gt.tab_source_note(mark).tab_footnote(mark, locations=loc.body(columns="team", rows=[0]))
    html = gt.as_raw_html()
    assert html.count('data-sdvplot-team="13"') == 2 and "<tfoot" in html
    assert _cells(gt) == [("14", 0, "team")]


def test_a_player_id_read_through_a_float_keeps_its_integer_form():
    """pandas stores [3139477, None] as floats, so the cell reads "3139477.0": the alt text and team attribute are the
    id the headshot URL was built from, not "3139477.0"."""
    gt = gt_sdv_headshots(GT(pd.DataFrame({"player": [3139477, None]})), "player", league="nfl")
    assert sgt.drawn_cells(gt) == [("3139477", 0, "player", 30.0, sdvplot.headshot_url("3139477", "nfl"))]
    assert 'alt="3139477"' in gt.as_raw_html()

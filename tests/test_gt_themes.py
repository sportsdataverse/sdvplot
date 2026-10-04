import re

import pandas as pd
import polars as pl
import pytest

pytest.importorskip("great_tables")
import great_tables  # noqa: E402
from great_tables import GT  # noqa: E402

import sdvplot.great_tables as sgt  # noqa: E402
from sdvplot.great_tables import _themes  # noqa: E402

ROWS = {"conf": ["AFC West", "AFC West", "NFC West"], "team": ["LV", "KC", "LAR"], "w": [8, 15, 10], "l": [9, 2, 7]}
# wave A's two themes are tested there; these are this module's
THEMES = sorted(
    n
    for n in sgt.__all__
    if n.startswith("gt_theme_") and n not in ("gt_theme_preview", "gt_theme_sdv", "gt_theme_sdv_team")
)


def table(data=None, **gt_kwargs):
    """A table with every part a theme styles: heading, spanner, row groups, source note; id "tid"."""
    data = pl.DataFrame(ROWS) if data is None else data
    gt_kwargs = {"groupname_col": "conf", "id": "tid", **gt_kwargs}
    return GT(data, **gt_kwargs).tab_header("Title", "Sub").tab_source_note("Src").tab_spanner("Record", ["w", "l"])


def rule(html, selector):
    """The declarations great_tables wrote for ``#tid <selector>``."""
    m = re.search(rf"#tid {re.escape(selector)} \{{([^}}]*)\}}", html)
    assert m, f"no CSS rule for {selector}"
    return m.group(1)


def cell(html, text):
    """The inline style of the cell whose text is ``text`` ("" when it has none)."""
    m = re.search(rf"<t[dh]\b([^>]*)>\s*(?:<span[^>]*>)?{re.escape(text)}(?:</span>)?\s*</t[dh]>", html)
    assert m, f"no cell {text!r}"
    style = re.search(r'style="([^"]*)"', m.group(1))
    return style.group(1) if style else ""


def spanner(html, spanner_id="Record"):
    """The inline style of a spanner's header cell."""
    m = re.search(rf'<th\b[^>]*?style="([^"]*)"[^>]*id="tid-{spanner_id}"', html)
    assert m, f"no styled spanner {spanner_id!r}"
    return m.group(1)


def table_font(html):
    return re.search(r"#tid table \{\s*font-family: ([^;]*);", html).group(1)


# --- helpers ---------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("color", "steps", "r"),
    [
        # gt::adjust_luminance() in R 4.6.1 / gt 1.3.0, 2026-10-04
        ("#123F5E", 0.9, "#516E8B"),
        ("#123F5E", -0.7, "#00294D"),
        ("#F4E8C1", -0.6, "#E4D8B1"),
        ("#F4E8C1", 0.5, "#FDF0CA"),
        ("#E31837", 0.9, "#FF6676"),
        ("#E31837", -0.7, "#AF0000"),
        ("#123F5E", -2, "#C60000"),  # out of gamut, clamped as R clamps
        ("#0A0A0A", 0.9, "#141414"),  # L below 8: the linear branch of Luv
        ("#100008", 2, "#1D1519"),
        ("#000000", 0.9, "#000000"),
    ],
)
def test_adjust_luminance_matches_r(color, steps, r):
    assert _themes._adjust_luminance(color, steps) == r.lower()


def test_adjust_luminance_keeps_white_where_r_returns_na():
    assert _themes._adjust_luminance("#FFFFFF", -0.6) == "#ffffff"


@pytest.mark.parametrize(
    ("ground", "ink", "r"),
    [("#123F5E", "#ffffff", "#94A9B7"), ("#F4E8C1", "#000000", "#6E6857"), ("#E31837", "#ffffff", "#FFFFFF")],
)
def test_secondary_on_matches_r(ground, ink, r):
    # sdvplotR .theme_secondary_on(); the last never clears 4.5:1, so it falls back to the ink
    assert _themes._secondary_on(ground, ink) == r.lower()


def test_scale_output_rescales_text_sizes_and_size_options():
    gt = GT(pl.DataFrame(ROWS)).tab_style(great_tables.style.text(size="12px"), great_tables.loc.column_labels())
    assert _themes._scale_output(gt, "comfortable") is gt
    compact = _themes._scale_output(gt, "compact")
    sizes = {s.size for info in compact._styles for s in info.styles}
    assert sizes == {"10.8px"}  # label role: 12 * 9/10
    assert compact._options.table_font_size.value == "13.7px"  # great_tables' 16px default, body role 12/14
    assert compact._options.data_row_padding.value == "4px"  # 8px, pad role 3/6
    assert compact._options.source_notes_font_size.value == "90%"  # not px: left alone


def test_font_import_asks_for_every_weight():
    stmt = _themes._font("Barlow Condensed").make_import_stmt()
    assert stmt.startswith("@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,100;")
    assert "1,900&display=swap');" in stmt and ".." not in stmt


def test_private_great_tables_attributes_the_themes_read():
    gt = GT(pl.DataFrame(ROWS), id="x").tab_spanner("S", ["w"])
    assert gt._options.table_id.value == "x"
    assert gt._tbl_data is not None
    assert [s.spanner_id for s in gt._spanners] == ["S"]
    assert isinstance(gt._styles, list) and hasattr(gt, "_replace")
    assert issubclass(_themes._Font, great_tables._helpers.GoogleFont)


# --- every theme -----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", THEMES)
def test_pandas_and_polars_tables_theme_the_same(name):
    theme = getattr(sgt, name)
    pandas_html = theme(table(pd.DataFrame(ROWS, index=[10, 11, 12]))).as_raw_html()
    assert pandas_html == theme(table()).as_raw_html()


@pytest.mark.parametrize("name", THEMES)
def test_a_theme_takes_a_gt_not_raw_data(name):
    with pytest.raises(TypeError, match="wrap it in great_tables.GT"):
        getattr(sgt, name)(pl.DataFrame(ROWS))


@pytest.mark.parametrize("name", THEMES)
def test_density_must_be_a_known_scale(name):
    with pytest.raises(ValueError, match="density must be"):
        getattr(sgt, name)(table(), density="cozy")


@pytest.mark.parametrize("name", THEMES)
def test_the_callers_options_win(name):
    html = getattr(sgt, name)(table(), table_background_color="#123456").as_raw_html()
    assert "background-color: #123456" in rule(html, ".gt_table")


@pytest.mark.parametrize("name", THEMES)
def test_theme_css_is_scoped_to_the_tables_id(name):
    theme = getattr(sgt, name)
    kept = theme(GT(pl.DataFrame(ROWS), id="mine")).as_raw_html()
    assert "#mine td" in kept or "#mine tbody tr:last-child" in kept
    assigned = theme(GT(pl.DataFrame(ROWS)))
    table_id = assigned._options.table_id.value
    assert table_id and f"#{table_id} " in assigned.as_raw_html()
    # a second theme on top reuses the id rather than orphaning the first theme's CSS
    assert theme(assigned)._options.table_id.value == table_id


@pytest.mark.parametrize("name", THEMES)
def test_one_row_and_empty_tables_theme_cleanly(name):
    theme = getattr(sgt, name)
    one = theme(table(pl.DataFrame(ROWS).head(1))).as_raw_html()
    assert "LV" in one and "border-bottom: 1px solid" not in cell(one, "LV")
    theme(table(pl.DataFrame(ROWS).head(0))).as_raw_html()


@pytest.mark.parametrize("name", THEMES)
def test_spanners_are_styled_and_a_table_without_them_is_fine(name):
    html = getattr(sgt, name)(table()).as_raw_html()
    if name not in ("gt_theme_athletic", "gt_theme_tier"):  # these two leave spanners alone, as in R
        assert "font-size" in spanner(html)
    getattr(sgt, name)(GT(pl.DataFrame(ROWS), id="tid")).as_raw_html()


@pytest.mark.parametrize("name", THEMES)
def test_theme_fonts_load_every_weight(name):
    imports = re.findall(r"@import url\('([^']*)'\)", getattr(sgt, name)(table()).as_raw_html())
    assert imports and all(":ital,wght@0,100;" in url for url in imports)


# --- print and editorial themes --------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["gt_theme_almanac", "gt_theme_broadsheet", "gt_theme_swiss", "gt_theme_tufte"])
def test_a_color_that_is_not_hex_raises_naming_the_argument(name):
    with pytest.raises(ValueError, match="accent must be a hex color"):
        getattr(sgt, name)(table(), accent="red")
    html = getattr(sgt, name)(table(), accent="#abc").as_raw_html()
    assert "#aabbcc" in html


def test_almanac():
    html = sgt.gt_theme_almanac(table()).as_raw_html()
    assert table_font(html).startswith("'Zilla Slab', system-ui, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif")
    assert "border-top-color: #8c2f1e" in rule(html, ".gt_table")
    assert "background-color: #f1f1ef" in rule(html, ".gt_striped")
    assert 'class="gt_row gt_left gt_striped"' in html
    assert "font-family: Archivo Narrow" in cell(html, "AFC West") and "color: #8c2f1e" in cell(html, "AFC West")
    assert "font-size: 12px" in cell(html, "LV")  # compact by default
    assert "#tid .gt_col_heading, #tid .gt_column_spanner { letter-spacing: 0.05em; }" in html
    plain = sgt.gt_theme_almanac(table(), stripe=None).as_raw_html()
    assert "gt_striped" not in plain.split("<tbody", 1)[1]


def test_booktabs():
    html = sgt.gt_theme_booktabs(table(), accent="#1F3A5F").as_raw_html()
    assert table_font(html).startswith("Tinos, system-ui")
    labels = rule(html, ".gt_col_headings")
    assert "border-top-width: 2px; border-top-color: #1f3a5f" in labels and "border-bottom-color: #1f3a5f" in labels
    assert "border-bottom-width: 2px; border-bottom-color: #1f3a5f" in rule(html, ".gt_table_body")
    assert "font-style: italic" in cell(html, "Sub")
    assert "#tid .gt_sourcenote { padding-top: 10px; }" in html


def test_broadsheet():
    html = sgt.gt_theme_broadsheet(table()).as_raw_html()
    assert table_font(html).startswith("'Source Serif 4', system-ui")
    assert "background-color: #FBFAF7" in rule(html, ".gt_table")
    assert "font-family: Newsreader" in cell(html, "Title")
    assert "#tid .gt_group_heading_row + tr td { padding-top: 4px; }" in html  # gt's .gt_row_group_first
    salmon = sgt.gt_theme_broadsheet(table(), paper="salmon").as_raw_html()
    assert "background-color: #FFF1E5" in rule(salmon, ".gt_table")
    assert "background-color: #102030" in rule(
        sgt.gt_theme_broadsheet(table(), paper="#102030").as_raw_html(), ".gt_table"
    )
    with pytest.raises(ValueError, match="paper must be a hex color"):
        sgt.gt_theme_broadsheet(table(), paper="pink")


def test_swiss():
    html = sgt.gt_theme_swiss(table(), accent="#E30613").as_raw_html()
    assert table_font(html).startswith("Archivo, system-ui")
    assert "border-bottom-color: #e30613" in rule(html, ".gt_col_headings")
    assert "padding-top: 11px" in rule(html, ".gt_row")  # space instead of rules: pad 6 + 5
    assert "border-top-style: none" in rule(html, ".gt_row")


def test_tufte():
    html = sgt.gt_theme_tufte(table(), accent="#A0522D").as_raw_html()
    assert table_font(html).startswith("'EB Garamond', system-ui")
    assert "background-color: #FFFFF8" in rule(html, ".gt_table")
    assert "font-style: italic" in cell(html, "team") and "color: #6F6A60" in cell(html, "team")
    assert "color: #a0522d" in cell(html, "AFC West")
    assert "border-bottom-color: #C9C4B8" in rule(html, ".gt_table_body")


# --- bold and dark themes --------------------------------------------------------------------------------------------


def test_brutalist():
    html = sgt.gt_theme_brutalist(table()).as_raw_html()
    frame = rule(html, ".gt_table")
    for side in ("top", "right", "bottom", "left"):
        assert f"border-{side}-style: solid; border-{side}-width: 3px; border-{side}-color: #000000" in frame
    assert "color: #FFFFFF" in cell(html, "team")  # knocked out of the black label bar
    assert "background-color: #000000" in rule(html, ".gt_col_heading")
    assert "font-family: Archivo Black" in cell(html, "Title")
    assert "color: #ff3b00" in cell(html, "AFC West")


def test_drench_derives_its_colors_like_r():
    html = sgt.gt_theme_drench(table()).as_raw_html()
    assert "background-color: #123f5e" in rule(html, ".gt_table")
    assert "color: #ffffff" in cell(html, "LV")
    assert "color: #94a9b7" in cell(html, "team")  # muted ink, R's .theme_secondary_on
    assert "border-bottom-color: #516e8b" in rule(html, ".gt_col_headings")  # rule: adjust_luminance(+0.9)
    assert "background-color: #00294d" in cell(html, "AFC West")  # band: adjust_luminance(-0.7)
    assert "#tid td, #tid th { line-height: 1.55; }" in html


def test_drench_flips_to_dark_type_on_a_pale_color():
    html = sgt.gt_theme_drench(table(), color="#F4E8C1").as_raw_html()
    assert "color: #000000" in cell(html, "LV")
    assert "color: #6e6857" in cell(html, "team")
    assert "border-bottom-color: #e4d8b1" in rule(html, ".gt_col_headings")
    assert "line-height: 1.55" not in html


def test_midnight():
    html = sgt.gt_theme_midnight(table()).as_raw_html()
    assert "background-color: #0C0D10" in rule(html, ".gt_table") and "color: #FFFFFF" in rule(html, ".gt_table")
    assert "background-color: #16181D" in rule(html, ".gt_col_heading")
    assert "color: #E8E9ED" in cell(html, "LV") and "color: #5b8def" in cell(html, "AFC West")
    assert "border-top-color: #5b8def" in rule(html, ".gt_table")


def test_pal_midnight_reads_on_the_dark_grounds():
    from sdvplot._contrast import contrast

    # sdvplotR R/gt_theme_midnight.R, best to worst
    assert sgt.pal_midnight == ("#3FBF87", "#8FD9A8", "#D8D6A0", "#E8996B", "#E0645C")
    for ground in ("#0C0D10", "#0F1115"):  # gt_theme_midnight, gt_theme_terminal
        assert all(contrast(color, ground) >= 4.5 for color in sgt.pal_midnight)


def test_scoreboard_labels_read_on_the_accent():
    html = sgt.gt_theme_scoreboard(table()).as_raw_html()
    assert "background-color: #0e1621" in rule(html, ".gt_col_heading")
    assert "color: #ffffff" in cell(html, "team") and "font-family: Barlow Condensed" in cell(html, "team")
    gold = sgt.gt_theme_scoreboard(table(), accent="#FFC20E").as_raw_html()
    assert "color: #000000" in cell(gold, "team")
    assert "border-bottom-width: 2px; border-bottom-color: #ffc20e" in rule(gold, ".gt_table_body")


def test_terminal():
    html = sgt.gt_theme_terminal(table(), accent="#7EE787").as_raw_html()
    assert table_font(html).startswith("'JetBrains Mono', system-ui")
    assert "background-color: #0F1115" in rule(html, ".gt_table")
    assert "color: #7ee787" in cell(html, "team") and "text-transform: uppercase" in cell(html, "team")
    assert "border-top-color: #7ee787" in rule(html, ".gt_table")


@pytest.mark.parametrize(
    ("name", "arg"),
    [
        ("gt_theme_brutalist", "accent"),
        ("gt_theme_drench", "color"),
        ("gt_theme_midnight", "accent"),
        ("gt_theme_scoreboard", "accent"),
        ("gt_theme_terminal", "accent"),
    ],
)
def test_a_bold_theme_color_that_is_not_hex_raises(name, arg):
    with pytest.raises(ValueError, match=f"{arg} must be a hex color"):
        getattr(sgt, name)(table(), **{arg: "navy"})

"""reactablefmtr's cell formatters (sdvplot._reactable_formatters, exported from sdvplot.reactable): each test builds a
real ``Reactable`` from NFL teams and checks the Column and the HTML/style its cell functions render."""

import re
import warnings

import pandas as pd
import polars as pl
import pytest

pytest.importorskip("reactable")
from reactable import Column, Reactable  # noqa: E402
from reactable.models import CellInfo  # noqa: E402

from sdvplot._errors import InputError, SdvplotWarning  # noqa: E402
from sdvplot._reactable_formatters import _ntile, _ramp  # noqa: E402
from sdvplot.reactable import (  # noqa: E402
    reactable_sdv_bubble_grid,
    reactable_sdv_color_scales,
    reactable_sdv_color_tiles,
    reactable_sdv_data_bars,
    reactable_sdv_highlight,
    reactable_sdv_icon_assign,
    reactable_sdv_icon_sets,
    reactable_sdv_icon_trend,
    reactable_sdv_merge_column,
    reactable_sdv_pill_buttons,
)

LV, LAR, LAC = "#000000", "#003594", "#0080c6"  # the fixture index's NFL primaries
FRAMES = pytest.mark.parametrize("kind", ["polars", "pandas"])


def _frame(kind, data):
    return (
        pl.DataFrame(data) if kind == "polars" else pd.DataFrame(data, index=[7 + i for i in range(len(data["team"]))])
    )


def _afc(kind="pandas"):
    return _frame(kind, {"team": ["LV", "LAR", "LAC"], "wins": [15, 13, 12], "diff": [4, 0, -3],
                         "record": ["15-2", "13-4", "12-5"]})  # fmt: skip


def _cells(col, data, column_id):
    """The column's built cells (or styles), as a ``Reactable`` built from ``data`` renders them."""
    built = next(c for c in Reactable(data, columns=[col]).columns if c.id == column_id)
    return built.cell if isinstance(built.cell, list) else built.style


def _css(html, prop):
    """The values of ``prop`` in every inline style of ``html``, in order."""
    return re.findall(rf"(?<![-\w]){prop}:([^;\"]+)", html)


# --- the scale helpers match R ------------------------------------------------------------------------------------


def test_ramp_matches_grdevices_colorramp_with_bias():
    # reactablefmtr::color_tiles(data.frame(wins = c(15, 13, 12, 14, 11)), bias = 2) in R 4.6.1
    got = [_ramp(["#15607a", "#ffffff", "#fa8c00"], (v - 11) / 4, 2) for v in (15, 13, 12, 14, 11)]
    assert got == ["#fa8c00", "#fdd8aa", "#ffffff", "#fbb255", "#15607a"]


def test_ntile_matches_dplyr():
    assert _ntile([5, 1, 3, 3, None, 2, 9], 3) == [3, 1, 2, 2, None, 1, 3]  # dplyr::ntile(c(5,1,3,3,NA,2,9), 3)


# --- data bars ----------------------------------------------------------------------------------------------------


@FRAMES
def test_data_bars_fill_by_share_of_the_largest_magnitude(kind):
    col = reactable_sdv_data_bars(_afc(kind), id="wins")
    assert isinstance(col, Column) and col.html is True and col.id == "wins"
    cells = _cells(col, _afc(kind), "wins")
    assert [_css(c, "width")[0] for c in cells] == ["100%", "86.67%", "80%"]
    assert all(_css(c, "background")[:2] == ["#EEEEEE", "#15607a"] for c in cells)  # track, then fill
    assert ">15</div>" in cells[0] and "justify-content:flex-end" in cells[0]  # inside-end
    assert _css(cells[0], "color") == ["#ffffff"]  # white on the dark default fill


def test_data_bars_take_team_colors_and_a_logo(manifest):
    df = pd.DataFrame({"team": ["LV", "LAR"], "wins": [10, 5]})
    cells = _cells(reactable_sdv_data_bars(df, team_col="team", league="nfl", mark="logo", id="wins"), df, "wins")
    assert _css(cells[0], "background")[1] == "#000000" and _css(cells[1], "background")[1] == "#003594"
    assert 'src="https://cdn/1111.png"' in cells[0] and 'data-sdvplot-team="13"' in cells[0]
    assert _css(cells[1], "width")[0] == "50%"


@pytest.mark.parametrize(
    ("position", "check"),
    [
        ("outside-end", lambda c: re.search(r"</div><span[^>]*>15</span>", c)),
        ("outside-base", lambda c: re.search(r"<span[^>]*>15</span><div", c)),
        ("inside-base", lambda c: "justify-content:flex-start" in c and ">15</div>" in c),
        ("center", lambda c: "justify-content:center" in c),
        ("above", lambda c: c.count(">15<") == 1 and "height:5px" in c),
        ("none", lambda c: c.count(">15<") == 1 and re.search(r'<span style="position:absolute[^"]*">15</span>', c)),
    ],
)
def test_data_bars_text_positions(position, check):
    df = _afc()
    assert check(_cells(reactable_sdv_data_bars(df, text_position=position, id="wins"), df, "wins")[0])


def test_data_bars_split_at_zero_with_negative_values():
    df = _afc()
    cells = _cells(reactable_sdv_data_bars(df, fill_color=["#ff0000", "#0000ff"], id="diff"), df, "diff")
    assert "background:#666666" in cells[0]  # the zero line
    assert "#0000ff" in cells[0] and "#ff0000" in cells[2]  # positive right in the second color, negative in the first
    assert "flex-direction:row-reverse" in cells[2]  # the negative bar grows left
    assert "width:100%" in cells[0] and "width:75%" in cells[2]


def test_data_bars_options():
    df = _afc()
    col = reactable_sdv_data_bars(df, round_edges=True, bar_height=10, gradient=True, fill_color=["#ffffff", "#000000"],
                                  tooltip=True, number_fmt=".1f", background="#ddd", align="right", id="wins")  # fmt: skip
    cell = _cells(col, df, "wins")[0]
    assert 'title="15.0"' in cell and "border-radius:5px" in cell and "height:10px" in cell
    assert "linear-gradient(to right, #ffffff, #000000)" in cell and "background:#ddd" in cell
    assert "flex-direction:row-reverse" in cell
    assert _css(_cells(reactable_sdv_data_bars(df, max_value=30, id="wins"), df, "wins")[0], "width") == ["50%"]


def test_data_bars_keep_text_and_blank_missing():
    df = pd.DataFrame({"team": ["KC", "BUF"], "wins": [3.0, None]})
    cells = _cells(reactable_sdv_data_bars(df, id="team"), df, "team")
    assert cells == ["KC", "BUF"]
    assert _cells(reactable_sdv_data_bars(df, id="wins"), df, "wins")[1] == ""


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"text_position": "side"}, "text_position"),
        ({"align": "middle"}, "align"),
        ({"fill_opacity": 2}, "fill_opacity"),
        ({"gradient": True}, "two colors"),
        ({"team_col": "team"}, "league"),
        ({"team_col": "team", "league": "nfl", "fill_color_ref": "team"}, "not both"),
        ({"mark": "logo"}, "mark needs league"),
        ({"fill_color": "teal"}, "hex"),
        ({"number_fmt": 3}, "number_fmt"),
    ],
)
def test_data_bars_reject_bad_options(kwargs, match):
    with pytest.raises(ValueError, match=match):
        reactable_sdv_data_bars(_afc(), id="wins", **kwargs)


# --- color tiles and scales ---------------------------------------------------------------------------------------


@FRAMES
def test_color_tiles_ramp_the_default_colors_with_readable_ink(kind):
    df = _afc(kind)
    cells = _cells(reactable_sdv_color_tiles(df, id="wins"), df, "wins")
    assert [_css(c, "background")[0] for c in cells] == ["#fa8c00", "#b1cad2", "#15607a"]
    assert [_css(c, "color")[0] for c in cells] == ["#000000", "#000000", "#ffffff"]
    assert all("border-radius:6px" in c for c in cells)


def test_color_tiles_team_colors_even_breaks_and_span():
    df = _afc()
    cells = _cells(reactable_sdv_color_tiles(df, team_col="team", league="nfl", opacity=0.5, id="team"), df, "team")
    assert [_css(c, "background")[0] for c in cells] == [f"{LV}80", f"{LAR}80", f"{LAC}80"]
    tiles = _cells(
        reactable_sdv_color_tiles(df, colors=["#ff0000", "#00ff00"], even_breaks=True, id="wins"), df, "wins"
    )
    assert [_css(c, "background")[0] for c in tiles] == ["#00ff00", "#ff0000", "#ff0000"]  # dplyr::ntile into 2 buckets
    span = reactable_sdv_color_tiles(df, colors=["#000000", "#ffffff"], span=True, id="diff")
    assert _css(_cells(span, df, "diff")[2], "background") == ["#000000"]  # -3 is the frame's minimum across columns


def test_color_tiles_with_a_color_column_and_text():
    df = _afc().assign(hue=["#ffffff", "#000000", "#777777"])
    cells = _cells(reactable_sdv_color_tiles(df, color_ref="hue", text_color="#aa0000", id="record"), df, "record")
    assert _css(cells[0], "background") == ["#ffffff"] and _css(cells[0], "color") == ["#aa0000"]  # readable: kept
    assert _css(cells[1], "color") == ["#ffffff"]  # dark red on black is not: brightened
    plain = _cells(reactable_sdv_color_tiles(df, id="record"), df, "record")
    assert plain == ["15-2", "13-4", "12-5"]  # text without a color column passes through


def test_color_tiles_check_min_and_max_against_the_data():
    df = _afc()
    with pytest.raises(InputError, match="min_value"):
        _cells(reactable_sdv_color_tiles(df, min_value=13, id="wins"), df, "wins")
    cells = _cells(reactable_sdv_color_tiles(df, colors=["#000000", "#ffffff"], min_value=0, max_value=30,
                                             id="wins"), df, "wins")  # fmt: skip
    assert _css(cells[0], "background") == ["#7f7f7f"]


@FRAMES
def test_color_scales_style_the_cell(kind):
    df = _afc(kind)
    col = reactable_sdv_color_scales(df, team_col="team", league="nfl", id="wins")
    assert col.cell is None
    styles = _cells(col, df, "wins")
    assert [s["background"] for s in styles] == [LV, LAR, LAC] and [s["color"] for s in styles] == [
        "#ffffff",
        "#ffffff",
        "#000000",
    ]
    col = reactable_sdv_color_scales(df, number_fmt=".1f", tooltip=True, id="wins")
    assert col.html is True and col.cell(CellInfo(15, 0, "wins")) == '<span title="15.0">15.0</span>'
    assert col.style(CellInfo(15, 0, "wins"))["background"] == "#fa8c00"


# --- pills and bubbles --------------------------------------------------------------------------------------------


def test_pill_buttons():
    df = _afc()
    cells = _cells(reactable_sdv_pill_buttons(df, team_col="team", league="nfl", id="record"), df, "record")
    assert [_css(c, "background")[0] for c in cells] == [LV, LAR, LAC]
    assert all("border-radius:15px" in c and "padding:2px 12px" in c for c in cells)
    text = _cells(reactable_sdv_pill_buttons(df, id="record"), df, "record")
    assert all(_css(c, "background") == ["#15607a"] for c in text)  # text: the first color
    nums = _cells(reactable_sdv_pill_buttons(df, colors=["#000000", "#ffffff"], id="wins"), df, "wins")
    assert [_css(c, "background")[0] for c in nums] == ["#ffffff", "#555555", "#000000"]


def test_bubble_grid_sizes_and_shapes():
    df = _afc()
    cells = _cells(reactable_sdv_bubble_grid(df, id="wins"), df, "wins")
    assert [_css(c, "width")[0] for c in cells] == ["100px", "86.67px", "80px"] and "border-radius:50%" in cells[0]
    squares = _cells(reactable_sdv_bubble_grid(df, shape="squares", team_col="team", league="nfl", id="wins"), df,
                     "wins")  # fmt: skip
    assert "border-radius" not in squares[0] and _css(squares[1], "background") == [LAR]
    with pytest.raises(ValueError, match="shape"):
        reactable_sdv_bubble_grid(df, shape="stars", id="wins")


# --- icons --------------------------------------------------------------------------------------------------------


def test_icon_sets_bucket_icons_and_colors():
    df = _afc()
    col = reactable_sdv_icon_sets(df, icons=("arrow-down", "minus", "arrow-up"), icon_position="left", id="wins")
    cells = _cells(col, df, "wins")
    assert 'fill="#fa8c00"' in cells[0] and 'd="M8 1 2 7.5' in cells[0]  # top bucket: up arrow, last color
    assert 'fill="#15607a"' in cells[2] and "M8 15 2 8.5" in cells[2]
    assert cells[0].index("<svg") < cells[0].index("15")  # left of the value
    assert "<svg" not in _cells(reactable_sdv_icon_sets(df, id="record"), df, "record")[0]
    with pytest.raises(InputError, match="unknown icon 'rocket'"):
        reactable_sdv_icon_sets(df, icons="rocket", id="wins")


def test_icon_sets_icon_ref_warns_once_for_an_unknown_icon():
    df = _afc().assign(shape=["star", "rocket", "rocket"])
    col = reactable_sdv_icon_sets(df, icon_ref="shape", id="wins")
    with pytest.warns(SdvplotWarning, match="'rocket'"):
        cells = _cells(col, df, "wins")
    assert "<svg" in cells[0] and cells[1] == "13"
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert col.cell(CellInfo(12, 2, "wins")) == "12"  # the same unknown icon: no second warning


def test_icon_assign_counts_icons():
    df = _afc()
    cells = _cells(reactable_sdv_icon_assign(df, icon="star", show_values="right", seq_by=5, id="diff"), df, "diff")
    assert cells[0].count('fill="#15607a"') == 1 and 'title="4 out of 4"' in cells[0] and cells[0].endswith(" 4</div>")
    assert cells[1].count('fill="#eeeeee"') == 1  # 0: one empty icon (seq 1, 6, ... up to 4)
    bucketed = _cells(reactable_sdv_icon_assign(df, buckets=3, id="wins"), df, "wins")
    assert [c.count('fill="#15607a"') for c in bucketed] == [3, 2, 1] and 'title="2 out of 3"' in bucketed[1]
    with pytest.raises(InputError, match="buckets"):
        reactable_sdv_icon_assign(df, buckets=0, id="wins")


def test_icon_trend_points_up_down_and_flat():
    df = _afc()
    cells = _cells(reactable_sdv_icon_trend(df, number_fmt="+d", icons="triangle", id="diff"), df, "diff")
    assert "M8 1.5 15 14.5H1z" in cells[0] and "color:#b35900" in cells[0] and ">+4</span>" in cells[0]
    # zero: a dash, the label only as visually hidden text
    assert "<rect" in cells[1] and re.search(r'<span style="position:absolute[^"]*">\+0</span>', cells[1])
    assert "M1 1.5h14L8 14.5z" in cells[2] and "color:#15607a" in cells[2]
    with pytest.raises(InputError, match="three colors"):
        reactable_sdv_icon_trend(df, colors=["#000000"], id="diff")


# --- merge column and highlights ----------------------------------------------------------------------------------


@FRAMES
def test_merge_column(kind, manifest):
    df = _frame(kind, {"team": ["LV", "LAR"], "record": ["8-9", "<10-7>"]})
    cells = _cells(reactable_sdv_merge_column(df, merged_name="record", merged_position="below", id="team"), df,
                   "team")  # fmt: skip
    assert cells[0] == ('<div><div style="font-size:14px;font-weight:bold;margin-bottom:3px">LV</div>'
                        '<div style="font-size:12px;color:#777;font-weight:normal">8-9</div></div>')  # fmt: skip
    assert "&lt;10-7&gt;" in cells[1]
    logo = _cells(
        reactable_sdv_merge_column(df, merged_name="record", mark="logo", league="nfl", id="team"), df, "team"
    )
    assert logo[0].startswith('<div style="display:flex;align-items:center;gap:8px"><img src="https://cdn/1111.png"')
    with pytest.raises(ValueError, match="'rec' not found"):
        reactable_sdv_merge_column(df, merged_name="rec", id="team")


def test_highlight():
    df = _afc()
    assert _cells(reactable_sdv_highlight(df, id="wins"), df, "wins") == [{"font-weight": "bold", "color": "green"}, {},
                                                                            {}]  # fmt: skip
    styles = _cells(reactable_sdv_highlight(df, which="min_max", highlighter=("#fee", "#efe"), id="wins"), df, "wins")
    assert styles[0]["background"] == "#efe" and styles[2] == {"font-weight": "bold", "color": "red",
                                                               "background": "#fee"}  # fmt: skip
    with pytest.raises(InputError, match="pair"):
        reactable_sdv_highlight(df, which="min_max", font_color="red")


def test_team_columns_warn_for_unknown_teams():
    df = pd.DataFrame({"team": ["LV", "XXX"], "wins": [1, 2]})
    with pytest.warns(SdvplotWarning, match="'XXX'"):
        col = reactable_sdv_color_tiles(df, team_col="team", league="nfl", id="wins")
    assert [_css(c, "background")[0] for c in _cells(col, df, "wins")] == [LV, "#fa8c00"]  # falls back to the scale


# --- review fixes: injection, a11y, caps, validation ----------------------------------------------------------------

_PAYLOAD = "red;position:fixed;inset:0;z-index:9999"


@pytest.mark.parametrize(
    "make",
    [
        lambda df: reactable_sdv_data_bars(df, fill_color_ref="color", id="wins"),
        lambda df: reactable_sdv_color_tiles(df, color_ref="color", id="wins"),
        lambda df: reactable_sdv_pill_buttons(df, color_ref="color", id="wins"),
        lambda df: reactable_sdv_bubble_grid(df, color_ref="color", id="wins"),
        lambda df: reactable_sdv_icon_sets(df, icon_color_ref="color", id="wins"),
    ],
)
def test_color_columns_never_inject_css(make):
    df = pd.DataFrame({"wins": [15, 13, 12], "color": [_PAYLOAD, "url(https://x/a.png)", "#00ff00"]})
    with pytest.warns(SdvplotWarning, match="not a hex color") as record:
        cells = _cells(make(df), df, "wins")
    assert len(record) == 2  # once per distinct bad value
    joined = "".join(cells)
    assert "position:fixed" not in joined and "z-index:9999" not in joined and "url(" not in joined
    assert "#00ff00" in cells[2]


def test_color_scales_column_and_css_backstop():
    from sdvplot._reactable_formatters import _css

    df = pd.DataFrame({"wins": [15, 13], "color": [_PAYLOAD, "rgb(0, 128, 0)"]})
    with pytest.warns(SdvplotWarning, match="not a hex color"):
        styles = _cells(reactable_sdv_color_scales(df, color_ref="color", id="wins"), df, "wins")
    assert "position" not in str(styles) and styles[1]["background"] == "rgb(0, 128, 0)"
    assert _css(background=_PAYLOAD, color="url(x)", width="5px") == "width:5px"


@pytest.mark.parametrize(
    "make",
    [
        lambda df: reactable_sdv_data_bars(df, text_color=_PAYLOAD, id="wins"),
        lambda df: reactable_sdv_data_bars(df, background="url(x)", id="wins"),
        lambda df: reactable_sdv_color_tiles(df, text_color=_PAYLOAD, id="wins"),
        lambda df: reactable_sdv_icon_trend(df, text_color=_PAYLOAD, id="diff"),
        lambda df: reactable_sdv_merge_column(df, merged_name="record", merged_color=_PAYLOAD, id="team"),
        lambda df: reactable_sdv_merge_column(df, merged_name="record", color="red}", id="team"),
        lambda df: reactable_sdv_highlight(df, font_color=_PAYLOAD, id="wins"),
        lambda df: reactable_sdv_highlight(df, which="min_max", highlighter=("#fee", "url(x)"), id="wins"),
    ],
)
def test_color_arguments_are_checked(make):
    with pytest.raises(InputError, match="CSS color name"):
        make(_afc())


def test_named_and_functional_colors_are_accepted():
    df = _afc()
    styles = _cells(reactable_sdv_highlight(df, font_color="darkgreen", highlighter="hsl(120, 50%, 90%)", id="wins"),
                    df, "wins")  # fmt: skip
    assert styles[0] == {"font-weight": "bold", "color": "darkgreen", "background": "hsl(120, 50%, 90%)"}


def test_data_bars_and_bubbles_check_range_and_bias_up_front():
    df = _afc()
    for make in (reactable_sdv_data_bars, reactable_sdv_bubble_grid):
        with pytest.raises(InputError, match="min_value must be below max_value"):
            make(df, min_value=10, max_value=5, id="wins")
        with pytest.raises(InputError, match="finite"):
            make(df, max_value=float("inf"), id="wins")
        with pytest.raises(InputError, match="bias"):
            make(df, bias=0, id="wins")
    with pytest.raises(InputError, match="bias"):
        reactable_sdv_data_bars(df, bias=float("nan"), id="wins")


def test_fill_by_must_be_numeric():
    with pytest.raises(InputError, match="fill_by must name a numeric column"):
        reactable_sdv_data_bars(_afc(), fill_by="record", id="wins")


def test_peaks_are_computed_once_per_column(monkeypatch):
    from sdvplot import _reactable_formatters as fm

    df = pd.DataFrame({"wins": list(range(1, 51))})
    scans = []

    class Counted(list):  # counts full passes over the column's values (indexing one row is not a pass)
        def __iter__(self):
            scans.append(1)
            return super().__iter__()

    real_values = fm._Scale.values
    monkeypatch.setattr(fm._Scale, "values", lambda self, name: Counted(real_values(self, name)))
    for make in (reactable_sdv_data_bars, reactable_sdv_bubble_grid):
        scans.clear()
        cells = _cells(make(df, id="wins"), df, "wins")
        assert len(cells) == 50 and len(scans) == 1  # one pass for the column's peak, not one per cell


def test_bubbles_clamp_to_100_pixels():
    df = _afc()
    cells = _cells(reactable_sdv_bubble_grid(df, max_value=13, id="wins"), df, "wins")
    assert _css(cells[0], "width")[0] == "100px"


def test_icon_assign_caps_icons_per_cell():
    df = pd.DataFrame({"team": ["LV", "LAR"], "yards": [150, 20]})
    with pytest.warns(SdvplotWarning, match="at most 100 icons"):
        cells = _cells(reactable_sdv_icon_assign(df, id="yards"), df, "yards")
    assert cells[0].count("<svg") == 100
    big = pd.DataFrame({"team": ["LV"], "yards": [5000]})
    with pytest.raises(InputError, match="at most 1000"):
        _cells(reactable_sdv_icon_assign(big, id="yards"), big, "yards")


def test_icon_sets_missing_icon_ref_draws_nothing_silently():
    df = pd.DataFrame({"wins": [15, 13], "icon": ["star", None]})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        cells = _cells(reactable_sdv_icon_sets(df, icon_ref="icon", id="wins"), df, "wins")
    assert "<svg" in cells[0] and "<svg" not in cells[1]


def test_merge_column_and_highlight_tooltips():
    df = _afc()
    merged = _cells(reactable_sdv_merge_column(df, merged_name="record", tooltip=True, id="team"), df, "team")
    assert merged[0].startswith('<div title="LV 15-2">')
    col = reactable_sdv_highlight(df, tooltip=True, id="wins")
    assert _cells(col, df, "wins")[0] == '<span title="15">15</span>'
    assert col.style is not None

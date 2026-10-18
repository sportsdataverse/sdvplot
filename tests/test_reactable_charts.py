import re

import pandas as pd
import polars as pl
import pytest

pytest.importorskip("reactable")
from reactable import Column, Reactable  # noqa: E402
from reactable.models import CellInfo  # noqa: E402

from sdvplot._errors import InputError, SdvplotWarning  # noqa: E402
from sdvplot.reactable import (  # noqa: E402
    reactable_sdv_gauge,
    reactable_sdv_sparkbar,
    reactable_sdv_sparkline,
)

FRAMES = pytest.mark.parametrize("kind", ["polars", "pandas"])


def _frame(kind, data):
    return pl.DataFrame(data) if kind == "polars" else pd.DataFrame(data)


def _cell(col, value, row=0, column="s"):
    return col.cell(CellInfo(value, row, column))


def _attr(svg, element, name, nth=0):
    return re.findall(rf"<{element}\b[^>]*?\b{name}=\"([^\"]*)\"", svg)[nth]


# --- sparkline ---------------------------------------------------------------------------------------------------


def test_sparkline_path_spans_the_margins_and_scales_to_the_series():
    col = reactable_sdv_sparkline(None, id="s")
    assert isinstance(col, Column) and col.html is True and col.id == "s"
    svg = _cell(col, [1, 3, 2])
    # reactablefmtr's default margins (t3 r13 b2 l13) in a 100 x 22 box: x 13..87, y 3 (max) .. 20 (min)
    assert _attr(svg, "path", "d") == "M13,20 L50,3 L87,11.5"
    assert _attr(svg, "path", "stroke") == "slategray"
    assert 'width="100" height="22"' in svg


def test_sparkline_is_an_accessible_image():
    svg = _cell(reactable_sdv_sparkline(None), [4, 9.5, 2, 7])
    assert 'role="img"' in svg
    label = "Sparkline of 4 values: min 2, max 9.5, last 7"
    assert f'aria-label="{label}"' in svg and f"<title>{label}</title>" in svg


def test_sparkline_missing_entries_break_the_line_and_empty_cells_are_blank():
    col = reactable_sdv_sparkline(None)
    assert _attr(_cell(col, [1, None, 3]), "path", "d") == "M13,20 M87,3"
    assert _attr(_cell(col, [1, float("nan"), 2, 3]), "path", "d").startswith("M13,20 M")
    for blank in ([], None, [None, None], float("nan"), "n/a", 5):
        assert _cell(col, blank) == ""


def test_sparkline_highlight_points_by_mapping_and_by_name():
    svg = _cell(reactable_sdv_sparkline(None, highlight_points={"min": "red", "max": "blue"}), [1, 3, 2])
    circles = re.findall(r'<circle[^>]*cx="([^"]+)" cy="([^"]+)"[^>]*fill="([^"]+)"', svg)
    assert circles == [("13", "20", "red"), ("50", "3", "blue")]
    named = _cell(reactable_sdv_sparkline(None, highlight_points=("first", "last")), [1, 3, 2])
    assert re.findall(r'<circle[^>]*cx="([^"]+)"[^>]*fill="([^"]+)"', named) == [("13", "red"), ("87", "red")]
    every = _cell(reactable_sdv_sparkline(None, highlight_points={"all": "gray", "max": "blue"}), [1, 3, 2])
    assert re.findall(r'fill="(gray|blue)"', every) == ["gray", "blue", "gray"]


def test_sparkline_statline_sits_at_the_stat_with_its_label_in_the_right_margin():
    svg = _cell(reactable_sdv_sparkline(None, statline="mean", decimals=1), [1, 3, 2])
    # with a statline the right margin grows to 28: x 13..72, y 4..19; the mean 2 is half way down
    assert _attr(svg, "line", "y1") == _attr(svg, "line", "y2") == "11.5"
    assert (_attr(svg, "line", "x1"), _attr(svg, "line", "x2")) == ("13", "72")
    assert re.search(r'<text class="sdv-statline-label" x="77" y="11.5"[^>]*>2.0</text>', svg)
    median = _cell(reactable_sdv_sparkline(None, statline="max"), [1, 3, 2])
    assert _attr(median, "line", "y1") == "4"


def test_sparkline_bandline_covers_the_inner_quartiles_or_the_range():
    svg = _cell(reactable_sdv_sparkline(None, bandline="innerquartiles"), [1, 2, 3, 4, 5])
    # q1 = 2, q3 = 4 (R type 7); y 3..20
    assert (_attr(svg, "rect", "y"), _attr(svg, "rect", "height")) == ("7.25", "8.5")
    full = _cell(reactable_sdv_sparkline(None, bandline="range"), [1, 2, 3, 4, 5])
    assert (_attr(full, "rect", "y"), _attr(full, "rect", "height")) == ("3", "17")


def test_sparkline_labels_grow_the_default_height_and_print_with_decimals():
    svg = _cell(reactable_sdv_sparkline(None, labels=("max",), decimals=1), [1, 3, 2])
    assert 'height="30"' in svg  # reactablefmtr's 22 -> 30 with labels above the points
    assert re.search(r'<text class="sdv-label" x="50" y="7" text-anchor="middle"[^>]*>3.0</text>', svg)
    ends = _cell(reactable_sdv_sparkline(None, labels=["first", "last"]), [1, 3, 2])
    assert 'text-anchor="end"' in ends and 'text-anchor="start"' in ends and 'height="22"' in ends
    assert len(re.findall("sdv-label", _cell(reactable_sdv_sparkline(None, labels="all"), [1, 3, 2]))) == 3


def test_sparkline_area_and_fixed_bounds():
    svg = _cell(reactable_sdv_sparkline(None, show_area=True, min_value=0, max_value=4), [1, 3])
    area = re.search(r'class="sdv-area" d="([^"]+)" fill="slategray" fill-opacity="0.1"', svg)
    assert area and area.group(1) == "M13,20 L13,15.75 L87,7.25 L87,20 Z"


@FRAMES
def test_sparkline_takes_the_row_team_color_through_a_reactable(kind):
    df = _frame(kind, {"team": ["LV", "LAR", "XXX"], "s": [[1, 2], [2, 1], [3, 3]]})
    with pytest.warns(SdvplotWarning, match="'XXX'"):
        col = reactable_sdv_sparkline(df, id="s", team_col="team", league="nfl", show_area=True)
    cells = next(c for c in Reactable(df, columns=[col]).columns if c.id == "s").cell
    assert [_attr(c, "path", "stroke", 0) for c in cells] == ["#000000", "#003594", "#b3b3b3"]
    assert _attr(cells[1], "path", "fill") == "#003594"  # the area follows the team too
    assert _attr(cells[2], "path", "d", 1) == "M13,11.5 L87,11.5"  # a flat series sits mid-height


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"statline": "mode"}, "statline"),
        ({"bandline": "iqr"}, "bandline"),
        ({"labels": ["middle"]}, "labels"),
        ({"highlight_points": {"peak": "red"}}, "highlight_points"),
        ({"height": 0}, "height"),
        ({"width": "100px"}, "height"),
        ({"area_opacity": 2}, "alpha"),
        ({"decimals": 1.5}, "decimals"),
        ({"max_value": "10"}, "max_value"),
        ({"team_col": "team"}, "league"),
    ],
)
def test_sparkline_rejects_bad_arguments(kwargs, match):
    with pytest.raises(InputError, match=match):
        reactable_sdv_sparkline(pl.DataFrame({"team": ["LV"]}), **kwargs)


def test_team_col_must_be_a_column():
    with pytest.raises(ValueError, match="'club' not found"):
        reactable_sdv_sparkbar(pl.DataFrame({"team": ["LV"]}), team_col="club", league="nfl")


# --- sparkbar ----------------------------------------------------------------------------------------------------


def test_sparkbar_bars_stand_on_zero():
    svg = _cell(reactable_sdv_sparkbar(None), [2, -1])
    rects = re.findall(r'<rect class="sdv-bar" x="([^"]+)" y="([^"]+)" width="([^"]+)" height="([^"]+)"', svg)
    # margins t3 r13 b0 l13: x 13..87, y 3..22; zero sits at y 15.67, two thirds of the way down from 2 to -1
    assert rects == [("16.7", "3", "29.6", "12.67"), ("53.7", "15.67", "29.6", "6.33")]
    assert 'aria-label="Bar chart of 2 values: min -1, max 2, last -1"' in svg
    smallest = _cell(reactable_sdv_sparkbar(None), [5, 10])
    assert _attr(smallest, "rect", "height") == "9.5"  # the smaller bar still shows (dataui drew it 0 tall)


def test_sparkbar_highlights_statline_and_labels():
    svg = _cell(
        reactable_sdv_sparkbar(None, highlight_bars={"max": "gold", "first": "black"}, labels="max", statline="mean"),
        [1, 4, 2],
    )
    assert re.findall(r'class="sdv-bar"[^>]*fill="([^"]+)"', svg) == ["black", "gold", "slategray"]
    assert re.search(r'class="sdv-label"[^>]*>4</text>', svg)
    assert 'class="sdv-statline"' in svg
    assert _cell(reactable_sdv_sparkbar(None), [None, None]) == ""
    gap = _cell(reactable_sdv_sparkbar(None), [1, None, 2])
    assert len(re.findall('class="sdv-bar"', gap)) == 2


@FRAMES
def test_sparkbar_team_fill(kind):
    df = _frame(kind, {"team": ["LAR"], "s": [[1, 2, 3]]})
    col = reactable_sdv_sparkbar(df, id="s", team_col="team", league="nfl", which="secondary", fill_opacity=0.5)
    cells = next(c for c in Reactable(df, columns=[col]).columns if c.id == "s").cell
    assert set(re.findall(r'class="sdv-bar"[^>]*fill="([^"]+)" fill-opacity="0.5"', cells[0])) == {"#ffa300"}


# --- gauge -------------------------------------------------------------------------------------------------------


def test_gauge_arc_fills_its_share_of_the_scale():
    df = pl.DataFrame({"pct": [0.5, 1.0]})
    col = reactable_sdv_gauge(df, id="pct")
    svg = _cell(col, 0.5, column="pct")
    # 50 px wide (reactablefmtr's size = 1), outer radius 25, inner 18.75; half way round ends at the top
    assert _attr(svg, "path", "d", 1) == "M0,25 A25,25 0 0 1 25,0 L25,6.25 A18.75,18.75 0 0 0 6.25,25 Z"
    assert _attr(svg, "path", "fill", 0) == "#EEEEEE"
    assert _attr(svg, "path", "fill", 1) == "#15607A"
    assert re.search(r'class="sdv-value"[^>]*fill="currentColor">0.5</text>', svg)
    assert 'role="img" aria-label="Gauge: 0.5 on a scale from 0 to 1"' in svg
    assert _cell(col, None, column="pct") == "" and _cell(col, "DNP", column="pct") == "DNP"
    empty = _cell(reactable_sdv_gauge(df, min_value=0.5), 0.5, column="pct")
    assert empty.count("<path") == 1  # nothing filled at the bottom of the scale


def test_gauge_bounds_format_and_min_max_labels():
    df = pd.DataFrame({"sv": [0.902, 0.915]})
    col = reactable_sdv_gauge(df, min_value=0.88, max_value=0.93, number_fmt=".3f", show_min_max=True, size=2)
    svg = _cell(col, 0.905, column="sv")
    assert 'width="100" height="74"' in svg
    assert re.search(r'class="sdv-min"[^>]*>0.880</text>', svg) and re.search(r'class="sdv-max"[^>]*>0.930</text>', svg)
    assert re.search(r'class="sdv-value"[^>]*>0.905</text>', svg)
    pct = _cell(reactable_sdv_gauge(df, number_fmt="{:.1%}".format), 0.915, column="sv")
    assert ">91.5%</text>" in pct


def test_gauge_ramps_through_several_colors_and_takes_team_colors():
    df = pl.DataFrame({"team": ["LV", "LAR"], "w": [2, 10]})
    ramp = reactable_sdv_gauge(df, fill_color=["#ff0000", "#0000ff"])
    assert _attr(_cell(ramp, 2, column="w"), "path", "fill", 1) == "#ff0000"
    assert _attr(_cell(ramp, 6, column="w"), "path", "fill", 1) == "#800080"
    team = reactable_sdv_gauge(df, id="w", team_col="team", league="nfl", opacity=0.5)
    cells = next(c for c in Reactable(df, columns=[team]).columns if c.id == "w").cell
    assert [_attr(c, "path", "fill", 1) for c in cells] == ["#000000", "#003594"]
    assert 'fill-opacity="0.5"' in cells[0]


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"size": 0}, "size"),
        ({"bias": -1}, "bias"),
        ({"opacity": 2}, "alpha"),
        ({"fill_color": ["red", "blue"]}, "hex"),
    ],
)
def test_gauge_rejects_bad_arguments(kwargs, match):
    with pytest.raises(InputError, match=match):
        reactable_sdv_gauge(pl.DataFrame({"w": [1]}), **kwargs)


def test_attribute_values_are_escaped():
    svg = _cell(reactable_sdv_sparkline(None, line_color='red" onload="x'), [1, 2])
    assert 'onload="x' not in svg and "&quot;" in svg


# --- review fixes: non-finite values, season, validation, row guard, labels ---------------------------------------


def test_infinities_and_numpy_nan_are_gaps_not_invalid_svg():
    np = pytest.importorskip("numpy")
    line = _cell(reactable_sdv_sparkline(None), [1, float("inf"), 2])
    assert "inf" not in line and "nan" not in line
    assert _attr(line, "path", "d") == "M13,20 M87,3"
    assert "inf" not in _cell(reactable_sdv_sparkbar(None), [1, float("-inf"), 2])
    assert _attr(_cell(reactable_sdv_sparkline(None), [1, np.float32("nan"), 2]), "path", "d") == "M13,20 M87,3"
    df = pd.DataFrame({"g": [0.5, float("inf"), 1.0]})
    gauge = reactable_sdv_gauge(df)
    assert 'aria-label="Gauge: 0.5 on a scale from 0 to 1"' in _cell(gauge, 0.5, column="g")  # inf is not the max
    assert _cell(gauge, float("inf"), column="g") == "" and _cell(gauge, np.float32("nan"), column="g") == ""


def test_season_reaches_team_colors(monkeypatch):
    import sdvplot._reactable_charts as charts

    seen = []

    def fake(league, teams, **kw):
        seen.append(kw["season"])
        return ["#123456"] * len(teams)

    monkeypatch.setattr(charts, "team_colors", fake)
    df = pl.DataFrame({"team": ["OAK"], "s": [[1, 2]], "g": [1.0]})
    for make in (reactable_sdv_sparkline, reactable_sdv_sparkbar):
        assert "#123456" in _cell(make(df, team_col="team", league="nfl", season=2019), [1, 2])
    reactable_sdv_gauge(df, team_col="team", league="nfl", season=2019)
    assert seen == [2019, 2019, 2019]


def test_season_is_validated_through_team_colors():
    with pytest.raises(InputError, match="season 1800"):
        reactable_sdv_sparkline(pl.DataFrame({"team": ["LV"]}), team_col="team", league="nfl", season=1800)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"line_width": float("nan")}, "line_width"),
        ({"line_width": "2"}, "line_width"),
        ({"line_width": 0}, "line_width"),
        ({"point_size": float("inf")}, "point_size"),
        ({"point_size": -1}, "point_size"),
        ({"min_value": 5, "max_value": 5}, "below max_value"),
        ({"min_value": 6, "max_value": 5}, "below max_value"),
    ],
)
def test_sparkline_rejects_bad_sizes_and_bounds(kwargs, match):
    with pytest.raises(InputError, match=match):
        reactable_sdv_sparkline(None, **kwargs)


def test_bounds_must_not_cross():
    with pytest.raises(InputError, match="below max_value"):
        reactable_sdv_sparkbar(None, min_value=1, max_value=0)
    with pytest.raises(InputError, match="below max_value"):
        reactable_sdv_gauge(pl.DataFrame({"w": [1]}), min_value=1, max_value=1)
    with pytest.raises(InputError, match="row 0: .*cross"):
        _cell(reactable_sdv_sparkline(None, min_value=10), [1, 2])
    with pytest.raises(InputError, match="row 0: .*cross"):
        _cell(reactable_sdv_gauge(pl.DataFrame({"w": [1, 2]}), min_value=5), 1, column="w")


def test_gauge_says_when_it_gauges_an_absolute_value():
    df = pl.DataFrame({"m": [-5.0, 10.0]})
    svg = _cell(reactable_sdv_gauge(df), -5.0, column="m")
    assert 'aria-label="Gauge: -5 (its absolute value, 5, is gauged) on a scale from 0 to 10"' in svg
    assert "absolute" not in _cell(reactable_sdv_gauge(df), 5.0, column="m")


def test_a_table_longer_than_data_raises_a_clear_error():
    df = pl.DataFrame({"team": ["LV"], "s": [[1, 2]], "g": [1.0]})
    for col, value in (
        (reactable_sdv_sparkline(df, team_col="team", league="nfl"), [1, 2]),
        (reactable_sdv_sparkbar(df, team_col="team", league="nfl"), [1, 2]),
        (reactable_sdv_gauge(df, team_col="team", league="nfl"), 1.0),
    ):
        with pytest.raises(InputError, match="row 1 is beyond the 1 rows of data"):
            _cell(col, value, row=1, column="g")


def test_labels_use_the_cell_text_color_and_aria_notes_stat_and_band_lines():
    df = pl.DataFrame({"team": ["LV"], "s": [[1, 2]]})
    line = _cell(reactable_sdv_sparkline(df, team_col="team", league="nfl", labels="all"), [1, 2])
    assert set(re.findall(r'class="sdv-label"[^>]*fill="([^"]+)"', line)) == {"currentColor"}
    bars = _cell(reactable_sdv_sparkbar(None, labels="max", statline="mean", bandline="range", decimals=1), [1, 2])
    assert re.search(r'class="sdv-label"[^>]*fill="currentColor"', bars)
    assert 'aria-label="Bar chart of 2 values: min 1, max 2, last 2; mean line at 1.5; band over the range"' in bars


def test_tiny_values_keep_significant_figures_in_the_label():
    svg = _cell(reactable_sdv_sparkline(None), [0.0000125, 0.00002])
    assert "min 0.0000125, max 0.00002" in svg

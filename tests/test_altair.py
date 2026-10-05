import pandas as pd
import pytest

alt = pytest.importorskip("altair")

import sdvplot  # noqa: E402
import sdvplot.altair as salt  # noqa: E402
from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.testing import check_adapter_contract  # noqa: E402


def _chart(**props):
    data = alt.Data(values=[{"a": 0, "b": -10}, {"a": 30, "b": 0}])
    return alt.Chart(data).mark_point().encode(x="a:Q", y="b:Q").properties(**props)


def _axis_chart(categories, **props):
    df = pd.DataFrame({"team": categories, "v": range(1, len(categories) + 1)})
    return alt.Chart(df).mark_bar().encode(x=alt.X("team:N", sort=None), y="v:Q").properties(**props)


def _layer(chart, name):
    (layer,) = [sub for sub in chart.layer if sub.name == name]
    return layer.to_dict()


def test_the_chart_adapter_passes_the_contract(mark_images, headshot_images):
    check_adapter_contract(salt, make_target=lambda: _chart(height=200), make_axis_target=_axis_chart)


def test_a_layer_chart_passes_the_contract(mark_images, headshot_images):
    def layered():
        return alt.layer(_chart(height=200), _chart().mark_line())

    check_adapter_contract(salt, make_target=layered, make_axis_target=lambda c: alt.layer(_axis_chart(c)))


def test_add_logos_returns_a_new_chart_and_leaves_the_old_one_alone(mark_images):
    chart = _chart(height=200)
    before = chart.to_dict()
    out = sdvplot.add_logos(chart, [10], [-3], ["LV"], league="nfl")
    assert isinstance(out, alt.LayerChart) and out is not chart
    assert chart.to_dict() == before


def test_a_logo_is_its_fraction_of_the_chart_height_in_pixels(mark_images):
    out = sdvplot.add_logos(_chart(height=200), [10], [-3], ["LV"], league="nfl", height=0.25)
    mark = _layer(out, "sdvplot_logo")["mark"]
    assert (mark["height"], mark["width"], mark["aspect"]) == (50, 50, True)
    out = sdvplot.add_wordmarks(_chart(height=200), [10, 20], [-3, -7], ["LV", "LAC"], league="nfl", height=0.25)
    mark = _layer(out, "sdvplot_wordmark")["mark"]
    assert (mark["height"], mark["width"]) == (50, 125)  # the box fits the widest (2.5:1) wordmark by height


def test_without_a_height_the_theme_view_height_is_used(mark_images):
    out = sdvplot.add_logos(_chart(), [10], [-3], ["LV"], league="nfl", height=0.1)
    assert _layer(out, "sdvplot_logo")["mark"]["height"] == pytest.approx(30)  # 0.1 of 300 px
    assert salt._drawn_marks(out)[0][3] == pytest.approx(0.1)


def test_a_step_sized_discrete_y_needs_a_pixel_height(mark_images):
    chart = alt.Chart(pd.DataFrame({"team": ["LV"], "v": [1]})).mark_bar().encode(y="team:N", x="v:Q")
    with pytest.raises(ValueError, match="sized by its step"):
        sdvplot.add_logos(chart, [1], ["LV"], ["LV"], league="nfl")
    sdvplot.add_logos(chart.properties(height=100), [1], ["LV"], ["LV"], league="nfl")


def test_the_layer_reuses_the_chart_fields_types_and_sort(mark_images):
    out = sdvplot.add_logos(_axis_chart(["LV", "LAR"]), ["LV", "LAR"], [1, 2], ["LV", "LAR"], league="nfl")
    enc = _layer(out, "sdvplot_logo")["encoding"]
    assert enc["x"] == {"field": "team", "type": "nominal", "sort": None}
    assert enc["y"] == {"field": "v", "type": "quantitative"}


def test_the_axis_titles_survive_the_layer(mark_images):
    vlc = pytest.importorskip("vl_convert")
    out = sdvplot.add_logos(_axis_chart(["LV", "LAR"]), ["LV", "LAR"], [1, 2], ["LV", "LAR"], league="nfl")
    vega = vlc.vegalite_to_vega(out.to_json())
    titles = {a["orient"]: a.get("title") for a in vega["axes"] if not a.get("grid")}
    assert titles == {"bottom": "team", "left": "v"}


def test_a_sort_vega_lite_would_drop_raises(mark_images):
    df = pd.DataFrame({"team": ["LV", "LAR"], "v": [1, 2]})
    chart = alt.Chart(df).mark_bar().encode(x=alt.X("team:N", sort="-y"), y="v:Q")
    with pytest.raises(ValueError, match="drops the x sort '-y'"):
        sdvplot.add_logos(chart, ["LV"], [1], ["LV"], league="nfl")
    kept = chart.encode(x=alt.X("team:N", sort=alt.EncodingSortField("v", op="max", order="descending")))
    sdvplot.add_logos(kept, ["LV"], [1], ["LV"], league="nfl")


@pytest.mark.parametrize(
    ("combine", "fix"),
    [(lambda c: c | c, r"chart\.hconcat\[i\]"), (lambda c: c & c, r"chart\.vconcat\[i\]"),
     (lambda c: c.facet(column="a:N"), r"chart\.spec")],
)  # fmt: skip
def test_facet_and_concat_charts_name_the_chart_to_pass(mark_images, combine, fix):
    with pytest.raises(ValueError, match=fix):
        sdvplot.add_logos(combine(_chart()), [10], [-3], ["LV"], league="nfl")


def test_logo_layer_is_a_native_layer(mark_images):
    layer = salt.logo_layer([10], [-3], ["LV"], league="nfl", height=0.1, chart_height=400)
    spec = layer.to_dict()
    assert spec["name"] == "sdvplot_logo" and spec["mark"]["height"] == pytest.approx(40)
    assert spec["encoding"]["x"] == {"field": "x", "type": "quantitative"}
    assert spec["data"]["values"] == [{"x": 10, "y": -3, "sdvplot_url": "https://cdn/1111.png", "sdvplot_team": "13"}]
    out = alt.layer(_chart(height=400), layer)
    assert salt._drawn_marks(out) == [("13", 10, -3, pytest.approx(0.1), "https://cdn/1111.png")]


@pytest.mark.parametrize("chart_height", [0, -100, float("nan"), float("inf")])
def test_logo_layer_needs_a_positive_chart_height(mark_images, chart_height):
    with pytest.raises(ValueError, match="chart_height"):
        salt.logo_layer([10], [-3], ["LV"], league="nfl", chart_height=chart_height)


def test_a_chart_height_that_is_not_a_positive_number_of_pixels_raises(mark_images):
    with pytest.raises(ValueError, match="height"):
        sdvplot.add_logos(_chart(height=0), [10], [-3], ["LV"], league="nfl")


@pytest.mark.parametrize(
    ("x", "y", "key"),
    [("a:Q", "mean(b):Q", "aggregate='mean'"), (alt.X("a:Q", bin=True), "b:Q", "bin=True")],
)
def test_an_aggregated_or_binned_axis_raises_naming_the_key(mark_images, x, y, key):
    chart = alt.Chart(alt.Data(values=[{"a": 0, "b": -10}])).mark_bar().encode(x=x, y=y)
    with pytest.raises(ValueError, match=key):
        sdvplot.add_logos(chart, [10], [-3], ["LV"], league="nfl")


def test_a_time_unit_is_copied_so_logos_sit_on_their_points(mark_images):
    vlc = pytest.importorskip("vl_convert")
    days = pd.to_datetime(["2025-09-14", "2025-10-20"])
    df = pd.DataFrame({"day": days, "v": [1, 2]})
    chart = alt.Chart(df).mark_point().encode(x=alt.X("yearmonth(day):T"), y="v:Q")
    out = sdvplot.add_logos(chart, pd.Series(days), [1, 2], ["LV", "LAR"], league="nfl")
    assert _layer(out, "sdvplot_logo")["encoding"]["x"]["timeUnit"] == "yearmonth"
    xs: dict[str, list[float]] = {}

    def walk(node):
        if isinstance(node, dict):
            if node.get("marktype") in ("symbol", "image"):  # a symbol's x is its centre, an image's its left edge
                xs.setdefault(node["marktype"], []).extend(
                    i["x"] + i.get("width", 0) / 2 for i in node.get("items", [])
                )
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(vlc.vegalite_to_scenegraph(out.to_json()))
    assert sorted(xs["image"]) == pytest.approx(sorted(xs["symbol"]))  # at yearmonth(day), as the points are


def test_dates_are_written_as_iso_strings(mark_images):
    days = pd.to_datetime(["2025-09-07", "2025-09-14"])
    chart = alt.Chart(pd.DataFrame({"day": days, "v": [1, 2]})).mark_line().encode(x="day:T", y="v:Q")
    out = sdvplot.add_logos(chart, pd.Series(days), [1, 2], ["LV", "LAR"], league="nfl")
    assert [m[1] for m in salt._drawn_marks(out)] == ["2025-09-07T00:00:00", "2025-09-14T00:00:00"]


def test_embed_inlines_the_cached_image(mark_images):
    out = sdvplot.add_logos(_chart(), [10], [-3], ["LV"], league="nfl", embed=True)
    assert salt._drawn_marks(out)[0][4].startswith("data:image/png;base64,")


def test_empty_input_adds_an_empty_layer_quietly(mark_images):
    out = sdvplot.add_logos(_chart(), [], [], [], league="nfl")
    assert salt._drawn_marks(out) == []


def test_axis_logos_blank_only_resolved_labels_and_make_room(mark_images):
    chart = _axis_chart(["LV", "XXX", "LAR"], height=200)
    with pytest.warns(SdvplotWarning):
        out = sdvplot.axis_logos(chart, "x", league="nfl", height=0.1)
    assert salt._drawn_axis_marks(out, "x") == [("13", 0.0, pytest.approx(0.1)), ("14", 2.0, pytest.approx(0.1))]
    assert salt._visible_axis_labels(out, "x") == ["XXX"]
    axis = out.layer[0].to_dict()["encoding"]["x"]["axis"]
    assert axis["labelExpr"] == 'indexof(["LV", "LAR"], datum.label) >= 0 ? \'\' : datum.label'
    assert axis["labelPadding"] == 2 + 20 + salt._AXIS_GAP  # past the 20 px images
    layer = _layer(out, "sdvplot_axis_x")
    assert layer["encoding"]["y"] == {"value": 200 + salt._AXIS_GAP} and layer["mark"]["baseline"] == "top"
    assert "axis" not in chart.to_dict()["encoding"]["x"]  # the caller's chart is unchanged


def test_axis_logos_keep_the_callers_label_expression(mark_images):
    chart = _axis_chart(["LV", "XXX"]).encode(
        x=alt.X("team:N", sort=None, axis=alt.Axis(labelExpr="upper(datum.label)"))
    )
    with pytest.warns(SdvplotWarning):
        out = sdvplot.axis_logos(chart, "x", league="nfl")
    assert out.layer[0].to_dict()["encoding"]["x"]["axis"]["labelExpr"].endswith(": (upper(datum.label))")


def test_y_axis_logos(mark_images):
    df = pd.DataFrame({"team": ["LV", "LAR"], "v": [1, 2]})
    chart = alt.Chart(df).mark_bar().encode(y=alt.Y("team:N", sort=None), x="v:Q").properties(height=100)
    out = sdvplot.axis_logos(chart, "y", league="nfl", height=0.2)
    assert salt._drawn_axis_marks(out, "y") == [("13", 0.0, pytest.approx(0.2)), ("14", 1.0, pytest.approx(0.2))]
    assert salt._visible_axis_labels(out, "y") == []
    layer = _layer(out, "sdvplot_axis_y")
    assert layer["encoding"]["x"] == {"value": -salt._AXIS_GAP} and layer["mark"]["align"] == "right"


def test_axis_logos_need_a_visible_discrete_axis(mark_images):
    with pytest.raises(ValueError, match="needs a nominal or ordinal x axis"):
        sdvplot.axis_logos(_chart(), "x", league="nfl")
    hidden = _axis_chart(["LV"]).encode(x=alt.X("team:N", axis=None))
    with pytest.raises(ValueError, match="hidden"):
        sdvplot.axis_logos(hidden, "x", league="nfl")
    with pytest.raises(ValueError, match="axis must be 'x' or 'y'"):
        sdvplot.axis_logos(_axis_chart(["LV"]), "z", league="nfl")


def test_categories_of_url_data_need_an_explicit_sort(mark_images):
    chart = alt.Chart("https://example.com/teams.csv").mark_bar().encode(x="team:N", y="v:Q")
    with pytest.raises(ValueError, match="explicit sort"):
        sdvplot.axis_logos(chart, "x", league="nfl")
    listed = chart.encode(x=alt.X("team:N", sort=["LV", "LAR"]))
    marks = salt._drawn_axis_marks(sdvplot.axis_logos(listed, "x", league="nfl"), "x")
    assert [m[:2] for m in marks] == [("13", 0.0), ("14", 1.0)]

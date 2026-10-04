"""Render tests: the web sizing models measured in pixels, Plotly through kaleido and Altair through vl-convert.

Every image is embedded (embed=True), so nothing is downloaded. kaleido drives a local Chrome: without one these tests
skip, unless SDVPLOT_RENDER_TESTS=1 (CI), where a missing Chrome is a failure. The fixture marks are solid tinted
squares (tests/conftest.py mark_images): the LV logo is (70, 240, 72), the LAR logo (197, 115, 143), the LV wordmark
(107, 71, 156).
"""

import io
import math
import os

import numpy as np
import pytest
from PIL import Image

import sdvplot
from sdvplot._errors import SdvplotWarning

pytestmark = pytest.mark.render

LV, LAR, LV_WORDMARK = (70, 240, 72), (197, 115, 143), (107, 71, 156)
BLUE = (0, 0, 255)
TOLERANCE_PX = 2  # anti-aliased edges


def _pixels(png):
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(int)


def _box(png, color, tol=24):
    """(x0, x1, y0, y1) of the pixels within ``tol`` of ``color``."""
    ys, xs = np.where(np.abs(_pixels(png) - np.array(color)).sum(axis=2) <= tol)
    assert len(ys), f"no {color} pixels in the render"
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


def _size(box):
    x0, x1, y0, y1 = box
    return x1 - x0 + 1, y1 - y0 + 1


def _center(box):
    x0, x1, y0, y1 = box
    return (x0 + x1) / 2, (y0 + y1) / 2


@pytest.fixture(scope="module")
def go():
    go = pytest.importorskip("plotly.graph_objects")
    pytest.importorskip("kaleido")
    try:
        go.Figure().to_image(format="png", width=20, height=20)
    except Exception as e:  # noqa: BLE001  kaleido found no Chrome to drive
        if os.environ.get("SDVPLOT_RENDER_TESTS") == "1":
            raise
        pytest.skip(f"kaleido cannot render here: {e}")
    return go


def _plotly_png(fig):
    return fig.to_image(format="png", scale=1)


def _blank_layout(fig, **kw):
    fig.update_layout(width=600, height=400, margin={"l": 50, "r": 50, "t": 50, "b": 50}, plot_bgcolor="white",
                      paper_bgcolor="white", showlegend=False, **kw)  # fmt: skip
    return fig


def test_plotly_a_logo_is_its_fraction_of_the_plot_area(go, mark_images):
    fig = _blank_layout(go.Figure(go.Scatter(x=[0, 30], y=[-10, 0], mode="markers", marker={"opacity": 0})))
    fig.update_xaxes(range=[0, 30], visible=False)
    fig.update_yaxes(visible=False)
    sdvplot.add_logos(fig, [10], [-3], ["LV"], league="nfl", height=0.25, embed=True)
    sdvplot.add_wordmarks(fig, [20], [-8], ["LV"], league="nfl", height=0.25, embed=True)
    png = _plotly_png(fig)
    logo, wordmark = _box(png, LV), _box(png, LV_WORDMARK)
    plot_h = 400 - 50 - 50
    assert _size(logo)[1] == pytest.approx(0.25 * plot_h, abs=TOLERANCE_PX)
    lo, hi = fig.layout.yaxis.range
    expected = (50 + 10 / 30 * 500, 50 + (hi - -3) / (hi - lo) * plot_h)
    assert _center(logo) == pytest.approx(expected, abs=TOLERANCE_PX)
    w, h = _size(wordmark)
    assert h == pytest.approx(0.25 * plot_h, abs=TOLERANCE_PX) and w == pytest.approx(2.5 * h, abs=2 * TOLERANCE_PX)


def test_plotly_category_logos_sit_on_their_categories(go, mark_images):
    fig = _blank_layout(go.Figure(go.Bar(x=["LV", "XXX", "LAR"], y=[1, 2, 3], marker_color="white")))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    sdvplot.add_logos(fig, ["LV", "LAR"], [1, 3], ["LV", "LAR"], league="nfl", height=0.1, embed=True)
    png = _plotly_png(fig)
    lo, hi = fig.layout.xaxis.range
    for color, index in ((LV, 0), (LAR, 2)):
        assert _center(_box(png, color))[0] == pytest.approx(50 + (index - lo) / (hi - lo) * 500, abs=TOLERANCE_PX)
        assert _size(_box(png, color))[1] == pytest.approx(30, abs=TOLERANCE_PX)


def test_plotly_axis_logos_hang_under_the_axis_in_place_of_their_labels(go, mark_images):
    fig = go.Figure(go.Bar(x=["LV", "XXX", "LAR"], y=[1, 2, 3], marker_color="white"))
    fig.update_layout(width=600, height=400, margin={"l": 80, "r": 80, "t": 50, "b": 50}, plot_bgcolor="white")
    with pytest.warns(SdvplotWarning):
        sdvplot.axis_logos(fig, "x", league="nfl", height=0.1, embed=True)
    png = _plotly_png(fig)
    plot_bottom = int(400 - fig.layout.margin.b)
    plot_h = plot_bottom - 50
    assert fig.layout.margin.b == 50 + math.ceil(0.1 * 300 / 1.1)
    columns = {}
    for color, index in ((LV, 0), (LAR, 2)):
        box = _box(png, color)
        assert _size(box)[1] == pytest.approx(0.1 * plot_h, abs=TOLERANCE_PX)
        assert box[2] == pytest.approx(plot_bottom, abs=TOLERANCE_PX)  # the image hangs from the axis line
        columns[index] = _center(box)[0]
        assert columns[index] == pytest.approx(80 + (index + 0.5) / 3 * 440, abs=TOLERANCE_PX)
    # tick label text (the template's #2a3f5f) shows under XXX only
    band = _pixels(png)[plot_bottom : plot_bottom + 25]
    text = np.abs(band - np.array((42, 63, 95))).sum(axis=2) <= 60
    xxx = round(80 + 1.5 / 3 * 440)
    assert text[:, xxx - 20 : xxx + 20].any()
    lv = int(round(columns[0]))
    assert not text[:, lv - 20 : lv + 20].any()


def test_plotly_y_axis_logos_sit_left_of_the_plot(go, mark_images):
    fig = go.Figure(go.Bar(y=["LV", "LAR"], x=[1, 2], orientation="h", marker_color="white"))
    fig.update_layout(width=600, height=400, margin={"l": 80, "r": 50, "t": 50, "b": 50}, plot_bgcolor="white")
    sdvplot.axis_logos(fig, "y", league="nfl", height=0.1, embed=True)
    png = _plotly_png(fig)
    for color in (LV, LAR):
        box = _box(png, color)
        assert _size(box)[1] == pytest.approx(0.1 * 300, abs=TOLERANCE_PX)
        assert box[1] + 1 == pytest.approx(fig.layout.margin.l, abs=TOLERANCE_PX)  # ends at the plot's left edge


def _vl_png(chart):
    vlc = pytest.importorskip("vl_convert")
    return vlc.vegalite_to_png(chart.configure_view(fill="#0000ff", stroke=None).to_json(), scale=1)


def test_altair_a_logo_is_its_fraction_of_the_chart_height(mark_images):
    alt = pytest.importorskip("altair")
    data = alt.Data(values=[{"a": 0, "b": -10}, {"a": 30, "b": 0}])
    chart = (
        alt.Chart(data)
        .mark_point(opacity=0)
        .encode(x=alt.X("a:Q", scale=alt.Scale(domain=[0, 30], nice=False)),
                y=alt.Y("b:Q", scale=alt.Scale(domain=[-10, 0], nice=False)))
        .properties(width=400, height=300)
    )  # fmt: skip
    chart = sdvplot.add_logos(chart, [10], [-3], ["LV"], league="nfl", height=0.25, embed=True)
    chart = sdvplot.add_wordmarks(chart, [25], [-8], ["LV"], league="nfl", height=0.25, embed=True)
    png = _vl_png(chart)
    x0, _, y0, _ = _box(png, BLUE, tol=60)
    logo, wordmark = _box(png, LV), _box(png, LV_WORDMARK)
    assert _size(logo)[1] == pytest.approx(75, abs=TOLERANCE_PX)
    assert _center(logo) == pytest.approx((x0 + 10 / 30 * 400, y0 + 3 / 10 * 300), abs=TOLERANCE_PX)
    w, h = _size(wordmark)
    assert h == pytest.approx(75, abs=TOLERANCE_PX) and w == pytest.approx(2.5 * h, abs=2 * TOLERANCE_PX)


def test_altair_axis_logos_hang_under_the_axis_in_place_of_their_labels(mark_images):
    alt = pytest.importorskip("altair")
    vlc = pytest.importorskip("vl_convert")
    import pandas as pd

    df = pd.DataFrame({"team": ["LV", "XXX", "LAR"], "v": [1, 2, 3]})
    chart = (
        alt.Chart(df).mark_bar(color="white").encode(x=alt.X("team:N", sort=None), y="v:Q")
        .properties(width=300, height=200)
    )  # fmt: skip
    with pytest.warns(SdvplotWarning):
        chart = sdvplot.axis_logos(chart, "x", league="nfl", height=0.1, embed=True)
    png = _vl_png(chart)
    x0, x1, _, y1 = _box(png, BLUE, tol=60)
    for color, index in ((LV, 0), (LAR, 2)):
        box = _box(png, color)
        assert _size(box)[1] == pytest.approx(20, abs=TOLERANCE_PX)
        assert box[2] == pytest.approx(y1 + 1 + 6, abs=TOLERANCE_PX)  # AXIS_GAP below the plot area
        assert _center(box)[0] == pytest.approx(x0 + (index + 0.5) / 3 * (x1 - x0 + 1), abs=TOLERANCE_PX)
    labels = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("marktype") == "text" and "axis-label" in (node.get("role") or ""):
                labels.append([item.get("text") for item in node.get("items", [])])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(vlc.vegalite_to_scenegraph(chart.to_json()))
    assert ["", "XXX", ""] in labels

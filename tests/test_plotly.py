import math

import pytest

go = pytest.importorskip("plotly.graph_objects")

import sdvplot  # noqa: E402
import sdvplot.plotly as splotly  # noqa: E402
from sdvplot import _web  # noqa: E402
from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.testing import check_adapter_contract  # noqa: E402


def _fig():
    return go.Figure(go.Scatter(x=[0, 30], y=[-10, 0], mode="markers"))


def _axis_fig(categories):
    return go.Figure(go.Bar(x=categories, y=list(range(1, len(categories) + 1))))


def test_the_figure_adapter_passes_the_contract(mark_images, headshot_images):
    check_adapter_contract(splotly, make_target=_fig, make_axis_target=_axis_fig)


def test_pinned_ranges_size_the_logo_and_leave_room_at_the_edges(mark_images):
    fig = _fig()
    fig.update_layout(width=600, height=400, margin={"l": 50, "r": 50, "t": 50, "b": 50})  # a 500 x 300 px plot
    assert sdvplot.add_logos(fig, [10], [-3], ["LV"], league="nfl", height=0.25) is fig
    x_lo, x_hi = fig.layout.xaxis.range
    assert x_hi - x_lo == pytest.approx(30 / (1 - 0.25 * 300 / 500))  # half a 75 px logo of room at each end
    lo, hi = fig.layout.yaxis.range
    (im,) = fig.layout.images
    assert hi - lo == pytest.approx(10 / 0.75)  # the data's [-10, 0], with half a logo of room at each end
    assert (lo + hi) / 2 == pytest.approx(-5)
    assert fig.layout.yaxis.autorange is False
    assert im.sizey == pytest.approx(0.25 * (hi - lo))
    assert (im.xref, im.yref, im.xanchor, im.yanchor, im.sizing) == ("x", "y", "center", "middle", "contain")
    assert im.source == "https://cdn/1111.png" and im.name == "sdvplot:logo:13"


def test_a_range_the_caller_set_is_kept(mark_images):
    fig = _fig()
    fig.update_yaxes(range=[-20, 5])
    sdvplot.add_logos(fig, [10], [-3], ["LV"], league="nfl", height=0.1)
    assert tuple(fig.layout.yaxis.range) == (-20, 5)
    assert fig.layout.images[0].sizey == pytest.approx(2.5)


def test_a_reversed_axis_stays_reversed(mark_images):
    fig = _fig()
    fig.update_yaxes(autorange="reversed")
    sdvplot.add_logos(fig, [10], [-3], ["LV"], league="nfl", height=0.2)
    lo, hi = fig.layout.yaxis.range
    assert lo > hi
    assert splotly._drawn_marks(fig)[0][3] == pytest.approx(0.2)


def test_a_bar_chart_keeps_zero_and_whole_bars_in_the_pinned_ranges(mark_images):
    fig = go.Figure(go.Bar(x=["LV", "LAR"], y=[3, 2]))
    sdvplot.add_logos(fig, ["LV", "LAR"], [3, 2], ["LV", "LAR"], league="nfl", height=0.1)
    lo, hi = fig.layout.yaxis.range
    assert lo < 0 and hi > 3
    lo, hi = fig.layout.xaxis.range
    assert lo < -0.5 and hi > 1.5  # each category's whole band
    assert [m[:3] for m in splotly._drawn_marks(fig)] == [("13", 0, 3), ("14", 1, 2)]  # categories at their index
    fig = go.Figure(go.Bar(x=[1, 2, 3], y=[3, 2, 1]))
    sdvplot.add_logos(fig, [1], [3], ["LV"], league="nfl", height=0.1)
    lo, hi = fig.layout.xaxis.range
    assert lo < 0.5 and hi > 3.5  # numeric bars are as wide as the gap between them


@pytest.mark.parametrize("barmode", ["stack", "relative"])
def test_stacked_bars_keep_every_whole_stack_in_the_pinned_range(mark_images, barmode):
    # px.bar's default: barmode="relative", and rows at the same x stack, within a trace and across traces
    fig = go.Figure([go.Bar(x=["a", "a", "b"], y=[5, 5, -5]), go.Bar(x=["a", "b"], y=[5, -5])])
    fig.update_layout(barmode=barmode)
    sdvplot.add_logos(fig, ["a"], [2], ["LV"], league="nfl")
    lo, hi = fig.layout.yaxis.range
    assert lo <= -10 and hi >= 15  # no single bar reaches past 5, the stacks reach -10 and 15


def test_relative_bars_stack_each_sign_on_its_own(mark_images):
    def fig(barmode):
        f = go.Figure([go.Bar(x=["a"], y=[5]), go.Bar(x=["a"], y=[-3]), go.Bar(x=["a"], y=[5])])
        f.update_layout(barmode=barmode)
        sdvplot.add_logos(f, ["a"], [1], ["LV"], league="nfl")
        return f.layout.yaxis.range

    lo, hi = fig("relative")
    assert lo <= -3 and hi >= 10  # 5 + 5 above zero, -3 below
    lo, hi = fig("stack")
    assert -3 < lo <= 0 and 7 <= hi < 10  # 5, then 5 - 3 = 2, then 2 + 5 = 7


@pytest.mark.parametrize(
    ("traces", "layout", "what"),
    [
        ([go.Bar(x=["a"], y=[5], base=[2])], {}, "base"),
        ([go.Bar(x=["a"], y=[5]), go.Bar(x=["a"], y=[5])], {"barnorm": "percent"}, "barnorm"),
        ([go.Bar(x=["a"], y=[5], offsetgroup="1"), go.Bar(x=["a"], y=[5], offsetgroup="2")],
         {"barmode": "stack"}, "offsetgroup"),
        ([go.Scatter(x=["a", "b"], y=[1, 2], stackgroup="one"), go.Scatter(x=["a", "b"], y=[1, 2], stackgroup="one")],
         {}, "stackgroup"),
    ],
)  # fmt: skip
def test_stacking_sdvplot_does_not_work_out_needs_the_range_set_first(mark_images, traces, layout, what):
    fig = go.Figure(traces, layout=layout)
    with pytest.raises(ValueError, match=f"{what}.*set it first"):
        sdvplot.add_logos(fig, ["a"], [1], ["LV"], league="nfl")
    fig.update_yaxes(range=[0, 20])
    sdvplot.add_logos(fig, ["a"], [1], ["LV"], league="nfl")  # the other axis is still worked out
    assert fig.layout.xaxis.range is not None


def test_a_fill_to_the_next_trace_fills_to_zero_only_on_the_first_trace(mark_images):
    fig = go.Figure(go.Scatter(x=[0, 1], y=[5, 6], fill="tonexty"))  # no trace before it: Plotly fills to zero
    sdvplot.add_logos(fig, [0], [5], ["LV"], league="nfl")
    assert fig.layout.yaxis.range[0] <= 0
    fig = go.Figure([go.Scatter(x=[0, 1], y=[100, 101]), go.Scatter(x=[0, 1], y=[110, 111], fill="tonexty")])
    sdvplot.add_logos(fig, [0], [105], ["LV"], league="nfl")
    assert fig.layout.yaxis.range[0] > 90  # a band between two traces, not down to zero


@pytest.mark.parametrize(
    ("trace", "covers"),
    [
        (go.Scatter(y=[1, 2, 3]), (0, 2)),  # Plotly draws a trace without x at 0, 1, 2, ...
        (go.Scatter(y=[1, 2, 3], x0=10, dx=5), (10, 20)),  # ... or at x0 + i * dx
        (go.Bar(y=[3, 2, 1]), (-0.5, 2.5)),  # whole bars
    ],
)
def test_a_trace_without_x_spans_plotlys_own_default_positions(mark_images, trace, covers):
    fig = go.Figure(trace)
    sdvplot.add_logos(fig, [1 if covers[0] < 1 else 15], [2], ["LV"], league="nfl")
    lo, hi = fig.layout.xaxis.range
    assert lo <= covers[0] and hi >= covers[1]


def test_category_order_follows_the_axis(mark_images):
    fig = go.Figure(go.Bar(x=["LV", "LAR"], y=[3, 2]))
    fig.update_xaxes(categoryorder="array", categoryarray=["LAR", "LV"])
    sdvplot.add_logos(fig, ["LV"], [3], ["LV"], league="nfl")
    assert splotly._drawn_marks(fig)[0][1] == 1
    fig.update_xaxes(categoryorder="total descending")
    with pytest.raises(ValueError, match="categoryorder='total descending'"):
        sdvplot.add_logos(fig, ["LV"], [3], ["LV"], league="nfl")


def test_a_category_not_on_the_axis_is_skipped_with_a_warning(mark_images):
    fig = go.Figure(go.Bar(x=["LV", "LAR"], y=[3, 2]))
    with pytest.warns(SdvplotWarning, match="not on the axis"):
        sdvplot.add_logos(fig, ["LV", "KC"], [3, 2], ["LV", "LAR"], league="nfl")
    assert [m[0] for m in splotly._drawn_marks(fig)] == ["13"]


@pytest.mark.parametrize("axis_type", ["log", "date"])
def test_log_and_date_axes_are_not_supported_yet(mark_images, axis_type):
    fig = _fig()
    fig.update_yaxes(type=axis_type)
    with pytest.raises(ValueError, match=f"does not support {axis_type} axes yet"):
        sdvplot.add_logos(fig, [10], [-3], ["LV"], league="nfl")


def test_date_values_are_recognised_as_a_date_axis(mark_images):
    fig = go.Figure(go.Scatter(x=["2025-09-07", "2025-09-14"], y=[1, 2]))
    with pytest.raises(ValueError, match="does not support date axes yet"):
        sdvplot.add_logos(fig, ["2025-09-07"], [1], ["LV"], league="nfl")


def test_a_trace_sdvplot_cannot_measure_needs_the_range_set_first(mark_images):
    fig = go.Figure(go.Histogram(x=[1, 2, 2, 3]))
    with pytest.raises(ValueError, match=r"histogram trace; set it first"):
        sdvplot.add_logos(fig, [2], [1], ["LV"], league="nfl")
    fig.update_xaxes(range=[0, 4])
    fig.update_yaxes(range=[0, 3])
    sdvplot.add_logos(fig, [2], [1], ["LV"], league="nfl")
    assert len(fig.layout.images) == 1


def test_subplots_place_on_the_named_axes(mark_images):
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=1, cols=2)
    fig.add_scatter(x=[0, 1], y=[0, 1], row=1, col=1)
    fig.add_scatter(x=[0, 10], y=[0, 100], row=1, col=2)
    sdvplot.add_logos(fig, [5], [50], ["LV"], league="nfl", xref="x2", yref="y2", height=0.2)
    (im,) = fig.layout.images
    assert (im.xref, im.yref) == ("x2", "y2")
    assert fig.layout.yaxis.range is None and fig.layout.yaxis2.range is not None and fig.layout.xaxis2.range
    assert splotly._drawn_marks(fig)[0][3] == pytest.approx(0.2)
    with pytest.raises(ValueError, match="yref must name a y axis"):
        sdvplot.add_logos(fig, [5], [50], ["LV"], league="nfl", yref="x2")


def test_embed_inlines_the_cached_image(mark_images):
    fig = _fig()
    sdvplot.add_logos(fig, [10], [-3], ["LV"], league="nfl", embed=True)
    assert fig.layout.images[0].source.startswith("data:image/png;base64,")


def test_a_repeated_team_reads_its_image_once_and_draws_every_point(mark_images, monkeypatch):
    calls = []
    real = _web.image_src
    monkeypatch.setattr(_web, "image_src", lambda p, *, embed=False: calls.append(p.url) or real(p, embed=embed))
    fig = _fig()
    sdvplot.add_logos(fig, [5, 10, 15], [-1, -2, -3], ["LV", "LV", "LV"], league="nfl", embed=True)
    assert len(splotly._drawn_marks(fig)) == 3 and calls == ["https://cdn/1111.png"]


def test_empty_input_draws_nothing_and_leaves_the_axes_alone(mark_images):
    fig = _fig()
    assert sdvplot.add_logos(fig, [], [], [], league="nfl") is fig
    assert splotly._drawn_marks(fig) == [] and fig.layout.xaxis.range is None and fig.layout.yaxis.range is None


def test_axis_logos_blank_only_resolved_labels_and_make_room(mark_images):
    fig = _axis_fig(["LV", "XXX", "LAR"])
    fig.update_layout(height=400, margin={"t": 50, "b": 50})
    with pytest.warns(SdvplotWarning):
        sdvplot.axis_logos(fig, "x", league="nfl", height=0.1)
    assert splotly._drawn_axis_marks(fig, "x") == [("13", 0.0, pytest.approx(0.1)), ("14", 2.0, pytest.approx(0.1))]
    assert splotly._visible_axis_labels(fig, "x") == ["XXX"]
    assert fig.layout.margin.b == 50 + math.ceil(0.1 * 300 / 1.1)  # the image height in the shrunk plot area
    im = fig.layout.images[0]
    assert (im.yref, im.y, im.sizey, im.yanchor) == ("paper", 0, 0.1, "top")


def test_y_axis_logos(mark_images):
    fig = go.Figure(go.Bar(y=["LV", "LAR"], x=[1, 2], orientation="h"))
    sdvplot.axis_logos(fig, "y", league="nfl", height=0.1)
    assert splotly._drawn_axis_marks(fig, "y") == [("13", 0.0, pytest.approx(0.1)), ("14", 1.0, pytest.approx(0.1))]
    assert splotly._visible_axis_labels(fig, "y") == []
    assert tuple(fig.layout.yaxis.range) == (-0.5, 1.5)
    assert fig.layout.images[0].sizey == pytest.approx(0.2)  # 0.1 of the two-category span
    assert fig.layout.margin.l > 80


def test_axis_logos_need_a_category_axis(mark_images):
    with pytest.raises(ValueError, match="needs a category x axis"):
        sdvplot.axis_logos(_fig(), "x", league="nfl")
    with pytest.raises(ValueError, match="axis must be 'x' or 'y'"):
        sdvplot.axis_logos(_axis_fig(["LV"]), "z", league="nfl")


def test_a_non_figure_is_a_type_error(mark_images):
    with pytest.raises(TypeError, match="draws on a plotly.graph_objects.Figure"):
        splotly.add_logos(go.Scatter(), [0], [0], ["LV"], league="nfl")

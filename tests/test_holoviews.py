import warnings

import pytest

hv = pytest.importorskip("holoviews")
pytest.importorskip("bokeh")
import holoviews.plotting.bokeh  # noqa: E402, F401

import sdvplot  # noqa: E402
import sdvplot.bokeh as sbokeh  # noqa: E402
import sdvplot.holoviews as shv  # noqa: E402
from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.testing import check_adapter_contract  # noqa: E402


@pytest.fixture(autouse=True)
def _bokeh_backend():
    previous = hv.Store.current_backend
    hv.Store.set_current_backend("bokeh")
    yield
    hv.Store.set_current_backend(previous)


def _element():
    return hv.Scatter([(0, -10), (30, 0)]).opts(frame_height=300)


def test_an_element_passes_the_contract(mark_images, headshot_images):
    check_adapter_contract(shv, make_target=_element)


def test_an_overlay_passes_the_contract(mark_images, headshot_images):
    check_adapter_contract(shv, make_target=lambda: _element() * hv.Curve([(0, -10), (30, 0)]))


def test_add_logos_returns_a_copy_and_keeps_the_existing_hooks(mark_images):
    seen = []
    element = _element().opts(hooks=[lambda plot, el: seen.append("mine")])
    out = sdvplot.add_logos(element, [10], [-3], ["LV"], league="nfl", height=0.2)
    assert out is not element
    fig = hv.render(out, backend="bokeh")
    assert seen == ["mine"]
    assert sbokeh._drawn_marks(fig) == [("13", 10, -3, pytest.approx(0.2), "https://cdn/1111.png")]
    assert shv._drawn_marks(element) == []  # the element passed in is unchanged


def test_warnings_come_at_call_time_not_at_render_time(mark_images):
    with pytest.warns(SdvplotWarning):
        out = sdvplot.add_logos(_element(), [10, 20], [-3, -7], ["XXX", "LV"], league="nfl")
    with warnings.catch_warnings():
        warnings.simplefilter("error", SdvplotWarning)
        assert [m[0] for m in shv._drawn_marks(out)] == ["13"]


def test_a_responsive_plot_without_a_frame_height_says_to_set_one(mark_images, caplog):
    out = sdvplot.add_logos(hv.Scatter([(0, -10), (30, 0)]).opts(responsive=True), [10], [-3], ["LV"], league="nfl")
    fig = hv.render(out, backend="bokeh")  # HoloViews logs a plot hook's error instead of raising it
    assert "set frame_height (or height)" in caplog.text
    assert not [r for r in fig.renderers if (r.name or "").startswith("sdvplot_")]


def test_a_backend_other_than_bokeh_is_a_type_error(mark_images):
    pytest.importorskip("matplotlib")
    import holoviews.plotting.mpl  # noqa: F401

    hv.Store.set_current_backend("matplotlib")
    with pytest.raises(TypeError, match="current backend is 'matplotlib'"):
        sdvplot.add_logos(_element(), [10], [-3], ["LV"], league="nfl")


def test_axis_logos_name_the_workaround(mark_images):
    with pytest.raises(TypeError, match="add_logos"):
        sdvplot.axis_logos(hv.Bars([("LV", 1)]), "x", league="nfl")

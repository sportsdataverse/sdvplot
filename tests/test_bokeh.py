import pytest

pytest.importorskip("bokeh")
from bokeh.models import ColumnDataSource  # noqa: E402
from bokeh.plotting import figure  # noqa: E402

import sdvplot  # noqa: E402
import sdvplot.bokeh as sbokeh  # noqa: E402
from sdvplot.testing import check_adapter_contract  # noqa: E402


def _fig(**kw):
    return figure(x_range=(0, 30), y_range=(-10, 0), **kw)


def _renderer(p, name):
    (r,) = [r for r in p.renderers if r.name == name]
    return r


def test_a_figure_with_a_frame_height_passes_the_contract(mark_images, headshot_images):
    check_adapter_contract(sbokeh, make_target=lambda: _fig(frame_height=300))


def test_a_figure_with_only_a_height_passes_the_contract(mark_images, headshot_images):
    check_adapter_contract(sbokeh, make_target=_fig)


def test_logos_are_screen_sized_from_the_frame_height(mark_images):
    p = _fig(frame_height=400, height=600)
    assert sdvplot.add_logos(p, [10, 20], [-3, -7], ["LV", "LAR"], league="nfl", height=0.25) is p
    r = _renderer(p, "sdvplot_logo")
    assert (r.glyph.w_units, r.glyph.h_units, r.glyph.anchor) == ("screen", "screen", "center")
    assert r.data_source.data["h"] == [100, 100] and r.data_source.data["w"] == [100, 100]


def test_without_a_frame_height_the_figure_height_is_the_reference(mark_images):
    p = _fig(height=500)
    sdvplot.add_logos(p, [10], [-3], ["LV"], league="nfl", height=0.1)
    assert _renderer(p, "sdvplot_logo").data_source.data["h"] == [50]


def test_a_figure_without_a_pixel_height_says_to_set_frame_height(mark_images):
    p = _fig(sizing_mode="stretch_both")
    p.height = None  # a responsive figure (e.g. a HoloViews plot with responsive=True) has no pixel height
    with pytest.raises(ValueError, match="frame_height"):
        sdvplot.add_logos(p, [10], [-3], ["LV"], league="nfl")


def test_a_wordmark_keeps_its_aspect_ratio(mark_images):
    p = _fig(frame_height=300)
    sdvplot.add_wordmarks(p, [10], [-3], ["LV"], league="nfl", height=0.1)
    data = _renderer(p, "sdvplot_wordmark").data_source.data
    assert data["w"] == [pytest.approx(75)] and data["h"] == [pytest.approx(30)]


def test_logos_sit_on_factor_ranges(mark_images):
    p = figure(x_range=["LV", "LAR"], frame_height=300)
    p.vbar(x=["LV", "LAR"], top=[3, 2], width=0.8)
    sdvplot.add_logos(p, ["LV", "LAR"], [3, 2], ["LV", "LAR"], league="nfl")
    assert [m[:3] for m in sbokeh._drawn_marks(p)] == [("13", "LV", 3), ("14", "LAR", 2)]


def test_alpha_and_embed(mark_images):
    p = _fig()
    sdvplot.add_logos(p, [10], [-3], ["LV"], league="nfl", alpha=0.5, embed=True)
    r = _renderer(p, "sdvplot_logo")
    assert r.glyph.global_alpha == 0.5
    assert r.data_source.data["url"][0].startswith("data:image/png;base64,")


def test_empty_input_adds_no_renderer(mark_images):
    p = _fig()
    before = len(p.renderers)
    sdvplot.add_logos(p, [], [], [], league="nfl")
    assert len(p.renderers) == before


def test_axis_logos_name_the_workaround(mark_images):
    with pytest.raises(TypeError, match="add_logos"):
        sdvplot.axis_logos(_fig(), "x", league="nfl")


def test_a_bokeh_object_that_is_not_a_figure_is_a_type_error(mark_images):
    with pytest.raises(TypeError, match="bokeh.plotting figure"):
        sdvplot.add_logos(ColumnDataSource(), [10], [-3], ["LV"], league="nfl")

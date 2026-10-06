import base64
import copy
import datetime as dt
import hashlib
import io
import pickle
import xml.etree.ElementTree as ET

import numpy as np
import pytest

pygal = pytest.importorskip("pygal")

import sdvplot  # noqa: E402
import sdvplot.pygal as spg  # noqa: E402
from sdvplot import _cache  # noqa: E402
from sdvplot._errors import SdvplotWarning, UnsupportedTargetError  # noqa: E402
from sdvplot._web import HEADSHOT_ASPECT  # noqa: E402
from sdvplot.testing import check_adapter_contract  # noqa: E402

HREF = "{http://www.w3.org/1999/xlink}href"
LV_TINT = tuple(hashlib.md5(("1" * 64).encode()).digest()[:3])  # the LV logo's color in the mark_images fixture


def _chart(cls=pygal.XY, **config):
    chart = cls(stroke=False, show_legend=False, **config)
    chart.add("games", [(10, -3), (20, -7)])  # pygal's own dots at the contract's points
    return chart


def _local(el):
    return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""


def _group(root, cls):
    return next(el for el in root.iter() if el.get("class") == cls)


def _images(root):
    """The <image> elements in the plot overlay, the group where pygal draws its dots."""
    return [el for el in _group(root, "plot overlay").iter() if _local(el) == "image"]


def _dots(root):
    return [el for el in _group(root, "plot overlay").iter() if _local(el) == "circle"]


def _plot_height(root):
    plot = _group(root, "plot")
    return float(next(el for el in plot if _local(el) == "rect" and el.get("class") == "background").get("height"))


def _center(img):
    x, y, w, h = (float(img.get(k)) for k in ("x", "y", "width", "height"))
    return x + w / 2, y + h / 2


def test_the_xy_adapter_passes_the_contract(mark_images, headshot_images):
    check_adapter_contract(spg, make_target=_chart)


def test_a_datetime_chart_passes_the_contract(mark_images, headshot_images):
    # an empty chart renders no plot, so no marks: give it pygal's own dots at the contract's points
    check_adapter_contract(spg, make_target=lambda: _chart(pygal.DateTimeLine))


def test_logos_sit_on_pygals_own_dots_at_their_height(mark_images):
    chart = _chart()
    spg.add_logos(chart, [10, 20], [-3, -7], ["LV", "LAR"], league="nfl", height=0.2)
    root = chart.render_tree()
    images, dots = _images(root), _dots(root)
    assert [img.get(HREF) for img in images] == ["https://cdn/1111.png", "https://cdn/6666.png"]
    for img, dot in zip(images, dots, strict=True):
        assert _center(img) == pytest.approx((float(dot.get("cx")), float(dot.get("cy"))), abs=1e-3)
        assert float(img.get("height")) == pytest.approx(0.2 * _plot_height(root), abs=1e-3)
        assert float(img.get("width")) == pytest.approx(float(img.get("height")), abs=1e-3)  # 500 x 500 logos
        assert img.get("preserveAspectRatio") == "xMidYMid meet"
        assert img.get("pointer-events") == "none"  # drawn over the dot, but its tooltip still triggers
    order = list(_group(root, "plot overlay").iter())
    assert order.index(images[0]) > order.index(dots[-1])  # above pygal's dots


def test_datetime_logos_sit_on_pygals_dots(mark_images):
    days = [dt.datetime(2025, 9, 7, 13), dt.datetime(2025, 9, 14, 16)]
    chart = pygal.DateTimeLine(stroke=False, show_legend=False)
    chart.add("games", list(zip(days, [3, 7], strict=True)))
    spg.add_logos(chart, days, [3, 7], ["LV", "LAR"], league="nfl")
    root = chart.render_tree()
    want = [(float(d.get("cx")), float(d.get("cy"))) for d in _dots(root)]
    assert len(want) == 2
    assert [_center(img) for img in _images(root)] == [pytest.approx(w, abs=1e-3) for w in want]


def test_a_numpy_datetime64_array_places_logos_on_pygals_dots(mark_images):
    days = [dt.datetime(2025, 9, 7, 13), dt.datetime(2025, 9, 14, 16)]
    chart = pygal.DateTimeLine(stroke=False, show_legend=False)
    chart.add("games", list(zip(days, [3, 7], strict=True)))
    spg.add_logos(chart, np.array(days, dtype="datetime64[ns]"), [3, 7], ["LV", "LAR"], league="nfl")  # pandas' dtype
    root = chart.render_tree()
    want = [(float(d.get("cx")), float(d.get("cy"))) for d in _dots(root)]
    assert [_center(img) for img in _images(root)] == [pytest.approx(w, abs=1e-3) for w in want]


LV, LAR, LV_DARK = "https://cdn/1111.png", "https://cdn/6666.png", "https://cdn/2222.png"


def _drawn(chart):
    """(href, center) of each rendered mark, and the test hook's urls."""
    images = _images(chart.render_tree())
    return [(img.get(HREF), _center(img)) for img in images], [m[4] for m in spg._drawn_marks(chart)]


def test_a_deep_copy_renders_the_marks_its_original_had(mark_images):
    chart = _chart()
    spg.add_logos(chart, [10, 20], [-3, -7], ["LV", "LAR"], league="nfl")
    copied = copy.deepcopy(chart)
    assert _drawn(copied) == _drawn(chart)
    assert [href for href, _ in _drawn(copied)[0]] == [LV, LAR]


def test_marks_added_after_a_deep_copy_stay_on_their_own_chart(mark_images):
    chart = _chart()
    spg.add_logos(chart, [10], [-3], ["LV"], league="nfl")
    copied = copy.deepcopy(chart)
    spg.add_logos(copied, [20], [-7], ["LAR"], league="nfl")
    spg.add_logos(chart, [20], [-7], ["LV"], league="nfl", variant="dark")
    for c, want in ((copied, [LV, LAR]), (chart, [LV, LV_DARK])):
        rendered, hook = _drawn(c)
        assert [href for href, _ in rendered] == want  # each once: no filter is shared or doubled
        assert hook == want


def test_a_pickled_chart_still_renders_its_marks(mark_images):
    chart = _chart()
    spg.add_logos(chart, [10, 20], [-3, -7], ["LV", "LAR"], league="nfl")
    assert _drawn(pickle.loads(pickle.dumps(chart))) == _drawn(chart)


def test_marks_draw_through_a_user_filter_that_wraps_the_filters(mark_images):
    chart = _chart()
    spg.add_logos(chart, [10, 20], [-3, -7], ["LV", "LAR"], league="nfl")
    want = _drawn(chart)
    chart.xml_filters[:] = [lambda r, f=f: f(r) for f in chart.xml_filters]  # e.g. instrumenting every filter
    assert _drawn(chart) == want


def _svg(chart, how, tmp_path):
    if how == "render":
        return ET.fromstring(chart.render())
    if how == "render_unicode":
        return ET.fromstring(chart.render(is_unicode=True).encode())
    if how == "render_tree":
        return chart.render_tree()
    if how == "render_to_file":
        chart.render_to_file(str(tmp_path / "chart.svg"))
        return ET.parse(tmp_path / "chart.svg").getroot()
    if how == "render_data_uri":
        return ET.fromstring(base64.b64decode(chart.render_data_uri().split(",", 1)[1]))
    return ET.fromstring(chart._repr_svg_().encode())  # what a notebook displays


@pytest.mark.parametrize(
    "how", ["render", "render_unicode", "render_tree", "render_to_file", "render_data_uri", "repr"]
)
def test_logos_appear_once_in_every_render(mark_images, how, tmp_path):
    chart = _chart()
    spg.add_logos(chart, [10, 20], [-3, -7], ["LV", "LAR"], league="nfl")
    chart.render()  # an earlier render must not leave images behind
    images = _images(_svg(chart, how, tmp_path))
    assert [img.get(HREF) for img in images] == ["https://cdn/1111.png", "https://cdn/6666.png"]


def test_wordmarks_keep_their_aspect_and_headshots_use_the_espn_shape(mark_images, headshot_images):
    chart = _chart()
    spg.add_wordmarks(chart, [10], [-3], ["LV"], league="nfl", height=0.1)
    spg.add_headshots(chart, [20], [-7], ["3139477"], league="nfl", height=0.1)
    wordmark, headshot = _images(chart.render_tree())
    assert float(wordmark.get("width")) / float(wordmark.get("height")) == pytest.approx(2.5, rel=1e-3)
    assert float(headshot.get("width")) / float(headshot.get("height")) == pytest.approx(HEADSHOT_ASPECT, rel=1e-3)
    assert headshot.get(HREF).startswith("https://a.espncdn.com/")


def test_alpha_becomes_the_image_opacity(mark_images):
    chart = _chart()
    spg.add_logos(chart, [10], [-3], ["LV"], league="nfl", alpha=0.4)
    (img,) = _images(chart.render_tree())
    assert float(img.get("opacity")) == pytest.approx(0.4)


class _NoNetwork:
    def get(self, *args, **kwargs):
        raise AssertionError("the network was touched")


def test_embed_renders_with_no_network(mark_images, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", _NoNetwork())
    chart = _chart()
    spg.add_logos(chart, [10], [-3], ["LV"], league="nfl", embed=True)
    (img,) = _images(chart.render_tree())
    head, data = img.get(HREF).split(",", 1)
    assert head == "data:image/png;base64"
    cached = mark_images / "images" / "11" / f"{'1' * 64}.png"
    assert base64.b64decode(data) == cached.read_bytes()
    assert spg._drawn_marks(chart)[0][4] == "https://cdn/1111.png"  # the hook still reports the mark, not the bytes


def test_render_to_png_draws_the_embedded_logo(mark_images, monkeypatch):
    try:
        import cairosvg  # noqa: F401
    except (ImportError, OSError):  # cairocffi raises OSError when the Cairo library is missing
        pytest.skip("render_to_png needs cairosvg and the Cairo library")
    from PIL import Image

    monkeypatch.setattr(_cache, "SESSION", _NoNetwork())
    chart = pygal.XY(stroke=False, show_legend=False, show_dots=False)
    chart.add("games", [(10, -3), (20, -7)])
    spg.add_logos(chart, [10], [-3], ["LV"], league="nfl", height=0.2, embed=True)
    root = chart.render_tree()
    tx, ty = (float(v) for v in _group(root, "plot overlay").get("transform")[10:-1].split(","))  # translate(x, y)
    cx, cy = _center(_images(root)[0])
    png = Image.open(io.BytesIO(chart.render_to_png())).convert("RGB")
    assert png.getpixel((round(tx + cx), round(ty + cy))) == LV_TINT


@pytest.mark.parametrize("cls", [pygal.Bar, pygal.Line, pygal.Pie, pygal.Histogram])
def test_category_and_angle_charts_raise_type_error(mark_images, cls):
    with pytest.raises(TypeError, match=r"XY-family charts \(pygal.XY"):
        sdvplot.add_logos(cls(), [0], [0], ["LV"], league="nfl")


def test_a_point_outside_the_range_is_not_drawn(mark_images):
    chart = _chart(xrange=(0, 30), range=(-10, 0))
    spg.add_logos(chart, [10, 100], [-3, -3], ["LV", "LAR"], league="nfl")
    images = _images(chart.render_tree())
    assert [img.get(HREF) for img in images] == ["https://cdn/1111.png"]  # pygal itself draws off-plot dots


def test_a_repeated_team_builds_its_image_source_once(mark_images, monkeypatch):
    calls = []
    real = spg.image_src
    monkeypatch.setattr(spg, "image_src", lambda p, *, embed=False: calls.append(p.url) or real(p, embed=embed))
    chart = _chart()
    spg.add_logos(chart, [12, 15, 18], [-4, -5, -6], ["LV", "LV", "LV"], league="nfl", embed=True)
    assert len(_images(chart.render_tree())) == 3 and calls == ["https://cdn/1111.png"]


def test_empty_input_and_a_chart_without_data_render_quietly(mark_images):
    chart = _chart()
    assert spg.add_logos(chart, [], [], [], league="nfl") is chart
    assert _images(chart.render_tree()) == []
    bare = pygal.XY()
    bare.add("empty", [])
    spg.add_logos(bare, [1], [1], ["LV"], league="nfl")
    assert "No data" in bare.render(is_unicode=True)  # pygal's own no-data chart, no crash


def test_team_style_colors_series_in_order(mark_images):
    style = spg.team_style(["LV", "LAR"], league="nfl", background="transparent")
    assert style.colors == ("#000000", "#003594")
    assert style.background == "transparent"
    assert spg.team_style(["LAR"], league="nfl", which="secondary").colors == ("#ffa300",)


def test_team_style_takes_one_team_as_a_scalar(mark_images):
    assert spg.team_style("LAR", league="nfl").colors == ("#003594",)  # not one color per character of "LAR"


def test_team_style_keeps_the_default_color_for_an_unknown_team(mark_images):
    with pytest.warns(SdvplotWarning, match="XXX"):
        style = spg.team_style(["LV", "XXX", "LAR"], league="nfl")
    assert style.colors == ("#000000", pygal.style.Style.colors[1], "#003594")  # the others keep their positions


def test_axis_logos_are_not_drawn_whatever_the_mark_type(mark_images):
    for mark_type in ("logo", "headshot"):
        with pytest.raises(UnsupportedTargetError, match="does not draw axis logos"):
            sdvplot.axis_logos(pygal.Bar(), "x", league="nfl", mark_type=mark_type)

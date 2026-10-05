"""title_image (sdvplotR ggtitle_image): an image beside the plot title, for matplotlib and plotnine."""

import hashlib
import json
import time

import pandas as pd
import pytest

mpl = pytest.importorskip("matplotlib")
mpl.use("Agg")
mpl.rcParams["figure.max_open_warning"] = 0
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from PIL import Image  # noqa: E402

import sdvplot.matplotlib as smpl  # noqa: E402
from sdvplot import _cache  # noqa: E402
from sdvplot._errors import SdvplotWarning  # noqa: E402
from tests.conftest import seed_image  # noqa: E402

URL = "https://example.com/banner.png"


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.fixture
def url_image(cache):
    """URL cached as a fresh 30 x 20 PNG, so load_url_image never downloads."""
    key = hashlib.sha256(URL.encode()).hexdigest()
    path = seed_image(cache / "urlimages" / key[:2] / key, size=(30, 20))
    _cache._meta_path(path).write_text(json.dumps({"fetched_at": time.time()}))
    return URL


def _extents(fig, box, text):
    if not hasattr(fig.canvas, "get_renderer"):  # a plotnine figure comes without a renderer
        FigureCanvasAgg(fig)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    return box.get_window_extent(r), text.get_window_extent(r)


def _box(container):
    (box,) = [a for a in container.artists if hasattr(a, "_sdvplot_title_image")]
    return box


# ---- matplotlib --------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("dpi", [72, 200])
def test_the_logo_sits_left_of_the_title_at_its_height_in_points(mark_images, dpi):
    fig, ax = plt.subplots(figsize=(6, 4), dpi=dpi)
    assert smpl.title_image(ax, "LV", "Raiders", league="nfl", height=20) is ax
    assert ax.get_title() == "Raiders"
    img, text = _extents(fig, _box(ax), ax.title)
    assert img.height == pytest.approx(20 * dpi / 72, abs=0.5)
    assert img.x1 < text.x0 and text.x0 - img.x1 == pytest.approx(4 * dpi / 72, abs=0.5)  # a 4-point gap
    assert (img.y0 + img.y1) / 2 == pytest.approx((text.y0 + text.y1) / 2, abs=0.5)
    assert smpl.drawn_title_images(ax) == [("left", "LV")]


def test_the_title_and_image_keep_the_titles_alignment(mark_images):
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    smpl.title_image(ax, "LV", "Raiders", league="nfl")  # a centred title: the pair is centred
    img, text = _extents(fig, _box(ax), ax.title)
    assert (img.x0 + text.x1) / 2 == pytest.approx((ax.bbox.x0 + ax.bbox.x1) / 2, abs=1)

    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    smpl.title_image(ax, "LV", "Raiders", league="nfl", side="right", loc="left")  # left-aligned: starts at the edge
    img, text = _extents(fig, _box(ax), ax._left_title)
    assert text.x0 == pytest.approx(ax.bbox.x0, abs=1) and img.x0 > text.x1


def test_a_figure_gets_a_suptitle_with_the_image(mark_images):
    fig, _ = plt.subplots(1, 2)
    assert smpl.title_image(fig, "LAR", "Two panels", league="nfl", side="right", fontsize=20) is fig
    assert fig._suptitle.get_text() == "Two panels" and fig._suptitle.get_fontsize() == 20
    img, text = _extents(fig, _box(fig), fig._suptitle)
    assert img.x0 > text.x1


def test_an_image_by_url_or_local_path(url_image, tmp_path):
    fig, ax = plt.subplots(dpi=100)
    smpl.title_image(ax, url_image, "From a URL", height=10)
    img, _ = _extents(fig, _box(ax), ax.title)
    assert img.width / img.height == pytest.approx(1.5, rel=0.02)
    assert smpl.drawn_title_images(ax) == [("left", URL)]

    path = tmp_path / "local.png"
    Image.new("RGBA", (10, 40), (0, 0, 255, 255)).save(path)
    fig, ax = plt.subplots(dpi=100)
    smpl.title_image(ax, str(path), "From a file", height=10)
    img, _ = _extents(fig, _box(ax), ax.title)
    assert img.width / img.height == pytest.approx(0.25, rel=0.05)


def test_an_unknown_team_warns_once_and_keeps_the_title(mark_images):
    _, ax = plt.subplots()
    with pytest.warns(SdvplotWarning) as rec:
        smpl.title_image(ax, "XXX", "No logo", league="nfl")
    assert len(rec) == 1 and ax.get_title() == "No logo" and smpl.drawn_title_images(ax) == []


def test_bad_side_or_height_raise(mark_images):
    _, ax = plt.subplots()
    with pytest.raises(ValueError, match="side"):
        smpl.title_image(ax, "LV", league="nfl", side="top")
    for bad in (0, -3, float("nan"), "15"):
        with pytest.raises(ValueError, match="height"):
            smpl.title_image(ax, "LV", league="nfl", height=bad)


def test_an_empty_title_still_places_the_image(mark_images):
    fig, ax = plt.subplots(dpi=100)
    smpl.title_image(ax, "LV", league="nfl")
    img, _ = _extents(fig, _box(ax), ax.title)
    assert img.y0 > ax.bbox.y1 - 1  # above the panel, where the title goes


# ---- plotnine ----------------------------------------------------------------------------------------------------


def _sp9():
    p9 = pytest.importorskip("plotnine")
    import sdvplot.plotnine as sp9

    return p9, sp9


def _p9_plot(p9):
    return p9.ggplot(pd.DataFrame({"x": [1.0, 2.0], "y": [1.0, 2.0]}), p9.aes("x", "y")) + p9.geom_point()


def _p9_title(fig, title):
    return next(t for t in fig.texts if t.get_text() == title)


def test_plotnine_title_image_sets_the_title_and_draws_beside_it(mark_images):
    p9, sp9 = _sp9()
    base = _p9_plot(p9)
    p = base + sp9.title_image("LV", "Raiders", league="nfl", height=20)
    assert p.labels.title == "Raiders" and base.labels.title is None
    fig = p.draw()
    img, text = _extents(fig, _box(fig), _p9_title(fig, "Raiders"))
    assert img.height == pytest.approx(20 * fig.dpi / 72, abs=0.5)
    assert img.x1 < text.x0 and (img.y0 + img.y1) / 2 == pytest.approx((text.y0 + text.y1) / 2, abs=0.5)
    # plotnine centres a lone title: the image and the title are centred together over the panel
    panel = fig.axes[0].bbox
    assert (img.x0 + text.x1) / 2 == pytest.approx((panel.x0 + panel.x1) / 2, abs=1)


def test_plotnine_left_aligned_title_starts_with_the_image(mark_images):
    p9, sp9 = _sp9()
    p = _p9_plot(p9) + p9.labs(subtitle="a subtitle") + sp9.title_image("LV", "Raiders", league="nfl")
    fig = p.draw()  # with a subtitle, plotnine left-aligns the title at the panel's edge
    img, text = _extents(fig, _box(fig), _p9_title(fig, "Raiders"))
    sub = _p9_title(fig, "a subtitle").get_window_extent(fig.canvas.get_renderer())
    assert img.x0 == pytest.approx(sub.x0, abs=1) and img.x1 < text.x0


def test_plotnine_title_image_checks_arguments_and_resolves_when_built(mark_images):
    _, sp9 = _sp9()
    with pytest.raises(ValueError, match="side"):
        sp9.title_image("LV", league="nfl", side="top")
    with pytest.raises(ValueError, match="height"):
        sp9.title_image("LV", league="nfl", height=0)
    with pytest.warns(SdvplotWarning) as rec:
        sp9.title_image("XXX", "No logo", league="nfl")
    assert len(rec) == 1


def test_plotnine_title_replaced_afterwards_warns(mark_images):
    p9, sp9 = _sp9()
    p = _p9_plot(p9) + sp9.title_image("LV", "Raiders", league="nfl") + p9.labs(title="Another")
    with pytest.warns(SdvplotWarning, match="title_image"):
        fig = p.draw()
    assert [a for a in fig.artists if hasattr(a, "_sdvplot_title_image")] == []

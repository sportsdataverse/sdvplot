import io

import numpy as np
import pytest

mpl = pytest.importorskip("matplotlib")
mpl.use("Agg")
mpl.rcParams["figure.max_open_warning"] = 0  # the contract builds many targets
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

import sdvplot  # noqa: E402
import sdvplot.matplotlib as smpl  # noqa: E402
from sdvplot import _images  # noqa: E402
from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.testing import check_adapter_contract  # noqa: E402
from tests.conftest import seed_image  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _axes():
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    ax.set_xlim(0, 30)
    ax.set_ylim(-10, 0)
    return ax


def _axis_target(categories):
    _, ax = plt.subplots(figsize=(6, 4), dpi=100)
    ax.bar(categories, range(1, len(categories) + 1))
    return ax


def test_the_axes_adapter_passes_the_contract(mark_images, headshot_images):
    check_adapter_contract(smpl, make_target=_axes, make_axis_target=_axis_target)


def test_a_one_axes_figure_passes_the_contract(mark_images, headshot_images):
    check_adapter_contract(smpl, make_target=lambda: _axes().figure, make_axis_target=lambda c: _axis_target(c).figure)


def test_a_seaborn_grid_passes_the_contract(mark_images, headshot_images):
    sns = pytest.importorskip("seaborn")
    import pandas as pd

    def grid():
        g = sns.FacetGrid(pd.DataFrame({"x": [0.0, 30.0], "y": [-10.0, 0.0]}))
        g.map(plt.scatter, "x", "y")
        return g

    def axis_grid(categories):
        g = sns.FacetGrid(pd.DataFrame({"team": categories, "v": range(len(categories))}))
        g.map(sns.barplot, "team", "v", order=categories)
        return g

    check_adapter_contract(smpl, make_target=grid, make_axis_target=axis_grid)


@pytest.mark.parametrize(("figsize", "dpi"), [((6, 4), 72), ((6, 4), 200), ((10, 3), 100)])
def test_a_logo_is_its_height_fraction_of_the_axes_at_any_size(mark_images, figsize, dpi):
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.set_xlim(0, 30)
    ax.set_ylim(-10, 0)
    sdvplot.add_logos(ax, [10], [-3], ["LV"], league="nfl", height=0.25)
    fig.canvas.draw()
    (box,) = [a for a in ax.artists if hasattr(a, "_sdvplot_mark")]
    ext = box.offsetbox.get_window_extent(fig.canvas.get_renderer())
    assert ext.height / ax.bbox.height == pytest.approx(0.25, abs=1e-6)
    cx, cy = ax.transData.inverted().transform(((ext.x0 + ext.x1) / 2, (ext.y0 + ext.y1) / 2))
    assert (cx, cy) == pytest.approx((10, -3), abs=0.05)


def test_the_saved_png_shows_the_logo_at_its_height(mark_images):
    fig = plt.figure(figsize=(6, 4), dpi=100)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_axis_off()
    sdvplot.add_logos(ax, [0.5], [0.5], ["LV"], league="nfl", height=0.25)
    buf = io.BytesIO()
    fig.savefig(buf, dpi=200, format="png", facecolor="white")
    pixels = np.asarray(Image.open(io.BytesIO(buf.getvalue())).convert("L"))
    rows = np.where((pixels < 200).any(axis=1))[0]
    assert (rows.max() - rows.min() + 1) / pixels.shape[0] == pytest.approx(0.25, abs=0.01)


def test_a_wordmark_keeps_its_aspect_ratio(mark_images):
    ax = _axes()
    sdvplot.add_wordmarks(ax, [10], [-3], ["LV"], league="nfl", height=0.2)
    ax.figure.canvas.draw()
    (box,) = ax.artists
    ext = box.offsetbox.get_window_extent(ax.figure.canvas.get_renderer())
    assert ext.width / ext.height == pytest.approx(2.5, rel=0.01)


def test_a_4096_px_mark_is_decoded_no_bigger_than_it_is_drawn(mark_images):  # re-audit finding 2
    images = mark_images / "images"
    seed_image(images / "11" / f"{'1' * 64}.png", size=(4096, 4096))  # LV's logo (500 x 500 in the manifest)
    seed_image(images / "44" / f"{'4' * 64}.png", size=(4096, 1638))  # LV's wordmark (500 x 200)
    _images._clear_decoded()
    ax = _axes()
    sdvplot.add_logos(ax, [10], [-3], ["LV"], league="nfl")
    sdvplot.add_wordmarks(ax, [20], [-3], ["LV"], league="nfl")
    smpl.title_image(ax, "LV", "Raiders", league="nfl")
    # 512 px tall at most, as drawn (_MAX_IMAGE_HEIGHT); the wide wordmark keeps that height, not 512 px of width
    assert sorted(img.size for img in _images._decoded.values()) == [(512, 512), (1280, 512)]


def test_a_figure_with_several_axes_names_the_fix(mark_images):
    fig, _ = plt.subplots(1, 2)
    with pytest.raises(ValueError, match=r"pass the Axes to draw on, e.g. fig.axes\[0\]"):
        sdvplot.add_logos(fig, [0], [0], ["LV"], league="nfl")


def test_a_colorbar_does_not_count_as_an_axes(mark_images):
    fig, ax = plt.subplots()
    fig.colorbar(ax.scatter([0, 1], [0, 1], c=[0, 1]))
    sdvplot.add_logos(fig, [0.5], [0.5], ["LV"], league="nfl")
    assert [m[0] for m in smpl._drawn_marks(ax)] == ["13"]


def test_axis_logos_hide_only_resolved_labels_and_make_room(mark_images):
    ax = _axis_target(["LV", "XXX", "LAR"])
    pad_before = ax.xaxis.get_major_ticks()[0].get_pad()
    with pytest.warns(SdvplotWarning):
        sdvplot.axis_logos(ax, "x", league="nfl", height=0.1)
    assert smpl._drawn_axis_marks(ax, "x") == [("13", 0.0, pytest.approx(0.1)), ("14", 2.0, pytest.approx(0.1))]
    assert smpl._visible_axis_labels(ax, "x") == ["XXX"]
    assert ax.xaxis.get_major_ticks()[0].get_pad() > pad_before


def test_y_axis_logos(mark_images):
    _, ax = plt.subplots()
    ax.barh(["LV", "LAR"], [1, 2])
    sdvplot.axis_logos(ax, "y", league="nfl")
    assert smpl._drawn_axis_marks(ax, "y") == [("13", 0.0, pytest.approx(0.1)), ("14", 1.0, pytest.approx(0.1))]
    assert smpl._visible_axis_labels(ax, "y") == []


def test_axis_must_be_x_or_y(mark_images):
    with pytest.raises(ValueError, match="axis must be 'x' or 'y'"):
        sdvplot.axis_logos(_axis_target(["LV"]), "z", league="nfl")


def test_logos_draw_on_an_mplsoccer_pitch(mark_images):
    mplsoccer = pytest.importorskip("mplsoccer")
    _, ax = mplsoccer.Pitch().draw()
    sdvplot.add_logos(ax, [60, 30], [40, 20], ["LV", "LAR"], league="nfl", height=0.1)
    assert [m[:3] for m in smpl._drawn_marks(ax)] == [("13", 60, 40), ("14", 30, 20)]


def test_a_repeated_team_loads_its_image_once_and_draws_every_point(mark_images, monkeypatch):
    calls = []
    real = smpl.load_mark_image
    monkeypatch.setattr(smpl, "load_mark_image", lambda row, size=None: calls.append(row["sha256"]) or real(row, size))
    ax = _axes()
    sdvplot.add_logos(ax, [5, 10, 15], [-1, -2, -3], ["LV", "LV", "LV"], league="nfl")
    assert len(smpl._drawn_marks(ax)) == 3 and len(calls) == 1


def test_logos_sit_on_category_and_date_positions(mark_images):
    import datetime as dt

    _, ax = plt.subplots()
    ax.bar(["LV", "LAR"], [3, 2])
    sdvplot.add_logos(ax, ["LV", "LAR"], [3, 2], ["LV", "LAR"], league="nfl")
    ax.figure.canvas.draw()
    centers = [box.offsetbox.get_window_extent(ax.figure.canvas.get_renderer()) for box in ax.artists]
    xs = [ax.transData.inverted().transform(((e.x0 + e.x1) / 2, 0))[0] for e in centers]
    assert xs == pytest.approx([0.0, 1.0], abs=0.01)

    _, ax = plt.subplots()
    days = [dt.date(2025, 9, 7), dt.date(2025, 9, 14)]
    ax.plot(days, [1, 2])
    sdvplot.add_logos(ax, days, [1, 2], ["LV", "LAR"], league="nfl")
    ax.figure.canvas.draw()
    assert len(smpl._drawn_marks(ax)) == 2


def test_empty_input_draws_nothing_quietly(mark_images):
    ax = _axes()
    assert sdvplot.add_logos(ax, [], [], [], league="nfl") is ax
    assert smpl._drawn_marks(ax) == []


def test_a_point_outside_the_limits_is_not_drawn(mark_images):
    fig = plt.figure(figsize=(3, 2), dpi=100)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_axis_off()
    ax.set_xlim(0, 30)
    ax.set_ylim(-10, 0)
    sdvplot.add_logos(ax, [100], [-3], ["LV"], league="nfl")  # like any matplotlib annotation outside the limits
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white")
    assert np.asarray(Image.open(io.BytesIO(buf.getvalue())).convert("L")).min() == 255


def test_axis_logos_skip_ticks_outside_the_view(mark_images):
    _, ax = plt.subplots()
    ax.bar(["LV", "LAR", "LAC"], [1, 2, 3])
    ax.set_xlim(-0.5, 1.5)  # LAC (no logo archived) sits outside the view: no image and no warning for it
    sdvplot.axis_logos(ax, "x", league="nfl")
    assert [m[:2] for m in smpl._drawn_axis_marks(ax, "x")] == [("13", 0.0), ("14", 1.0)]


def test_axis_logos_keep_a_configured_label_pad(mark_images):
    _, ax = plt.subplots(figsize=(6, 4), dpi=100)
    ax.bar(["LV", "XXX"], [1, 2])
    ax.tick_params(axis="x", pad=10)
    with pytest.warns(SdvplotWarning):
        sdvplot.axis_logos(ax, "x", league="nfl", height=0.1)
    image_points = 0.1 * ax.bbox.height * 72 / ax.figure.dpi
    assert ax.xaxis.get_major_ticks()[0].get_pad() == pytest.approx(10 + 2 + image_points)


def test_a_matplotlib_transform_places_logos_in_its_coordinates(mark_images):
    ax = _axes()
    sdvplot.add_logos(ax, [0.25], [0.75], ["LV"], league="nfl", transform=ax.transAxes)
    ax.figure.canvas.draw()
    ext = ax.artists[0].offsetbox.get_window_extent(ax.figure.canvas.get_renderer())
    cx, cy = ax.transAxes.inverted().transform(((ext.x0 + ext.x1) / 2, (ext.y0 + ext.y1) / 2))
    assert (cx, cy) == pytest.approx((0.25, 0.75), abs=1e-3)


# add_images: any image by local path or URL (the port of ggpath's geom_from_path)


def _png(path, size=(40, 20), color=(30, 90, 200, 255)):
    Image.new("RGBA", size, color).save(path, format="PNG")
    return str(path)


def _cached_url(cache, url, size=(30, 30)):
    """Seed the url-image cache with a fresh PNG for url, so add_images never downloads."""
    import hashlib
    import json
    import time

    from sdvplot import _cache
    from tests.conftest import seed_image

    key = hashlib.sha256(url.encode()).hexdigest()
    path = seed_image(cache / "urlimages" / key[:2] / key, size=size)
    _cache._meta_path(path).write_text(json.dumps({"fetched_at": time.time()}))
    return url


def test_add_images_draws_local_paths_and_urls_at_their_height(tmp_path, cache):
    pl = pytest.importorskip("polars")
    a, b = _png(tmp_path / "a.png"), _cached_url(cache, "https://example.com/b.png")
    ax = _axes()
    out = smpl.add_images(ax, pl.Series([5.0, 20.0]), pl.Series([-3.0, -7.0]), pl.Series([a, b]), height=0.2)
    assert out is ax
    assert smpl._drawn_marks(ax) == [(a, 5.0, -3.0, pytest.approx(0.2), a), (b, 20.0, -7.0, pytest.approx(0.2), b)]
    ax.figure.canvas.draw()
    ext = ax.artists[0].offsetbox.get_window_extent(ax.figure.canvas.get_renderer())
    assert ext.height / ax.bbox.height == pytest.approx(0.2, abs=1e-6) and ext.width / ext.height == pytest.approx(2)


def test_add_images_takes_alpha_zorder_and_transform(tmp_path):
    _png(tmp_path / "a.png")
    ax = _axes()
    smpl.add_images(ax, [0.25], [0.75], [tmp_path / "a.png"], alpha=0.5, zorder=7, transform=ax.transAxes)  # a Path
    (box,) = ax.artists
    assert box.offsetbox.get_children()[0].get_alpha() == 0.5 and box.get_zorder() == 7
    ax.figure.canvas.draw()
    ext = box.offsetbox.get_window_extent(ax.figure.canvas.get_renderer())
    assert ax.transAxes.inverted().transform(((ext.x0 + ext.x1) / 2, (ext.y0 + ext.y1) / 2)) == pytest.approx(
        (0.25, 0.75), abs=1e-3
    )


def test_unreadable_images_are_skipped_with_one_warning(tmp_path, cache, monkeypatch):
    from sdvplot import _cache
    from tests.conftest import FakeResponse, FakeSession

    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(404)))
    good = _png(tmp_path / "good.png")
    (tmp_path / "notes.txt").write_text("not an image")
    paths = [str(tmp_path / "missing.png"), good, str(tmp_path / "notes.txt"), "https://example.com/gone.png"]
    ax = _axes()
    with pytest.warns(SdvplotWarning, match=r"skipped 3 point\(s\) whose image could not be read") as rec:
        smpl.add_images(ax, [1, 2, 3, 4], [-1, -2, -3, -4], paths)
    assert len(rec) == 1 and "missing.png" in str(rec[0].message) and "gone.png" in str(rec[0].message)
    assert [m[0] for m in smpl._drawn_marks(ax)] == [good]


def test_a_repeated_image_loads_once_and_a_missing_x_or_path_is_skipped(tmp_path, monkeypatch):
    a = _png(tmp_path / "a.png")
    calls = []
    real = smpl.load_path_image
    monkeypatch.setattr(smpl, "load_path_image", lambda p: calls.append(p) or real(p))
    ax = _axes()
    with pytest.warns(SdvplotWarning, match=r"skipped 1 point\(s\) with a missing x or y"):
        smpl.add_images(ax, [1.0, 2.0, None, 4.0], [-1.0, -2.0, -3.0, -4.0], [a, a, a, None])
    assert [m[1] for m in smpl._drawn_marks(ax)] == [1.0, 2.0] and calls == [a]


def test_add_images_checks_its_arguments(tmp_path):
    ax = _axes()
    with pytest.raises(ValueError, match="fraction of the plot height"):
        smpl.add_images(ax, [1], [1], ["a.png"], height=0)
    with pytest.raises(ValueError, match="opacity"):
        smpl.add_images(ax, [1], [1], ["a.png"], alpha=2)
    with pytest.raises(ValueError, match="x, y and paths must have the same length, got 2, 1 and 1"):
        smpl.add_images(ax, [1, 2], [1], ["a.png"])


def test_add_images_takes_one_path_an_uppercase_scheme_and_a_file_uri(tmp_path, cache):
    from pathlib import Path

    a = _png(tmp_path / "a b.png")  # a space, so the file URI is percent-encoded
    upper = _cached_url(cache, "HTTPS://example.com/b.png")
    ax = _axes()
    smpl.add_images(ax, 5, -5, Path(a))  # one point, as a pathlib.Path
    smpl.add_images(ax, [10, 15], [-5, -5], [upper, Path(a).as_uri()])
    assert [m[0] for m in smpl._drawn_marks(ax)] == [a, upper, Path(a).as_uri()]


def test_add_images_warns_exactly_once_per_skip_reason_and_checks_height_at_the_call(tmp_path):
    a = _png(tmp_path / "a.png")
    ax = _axes()
    with pytest.warns(SdvplotWarning) as rec:
        smpl.add_images(ax, [1, None, 3, 4], [-1, -2, -3, -4], [a, a, str(tmp_path / "x.png"), str(tmp_path / "y.png")])
    assert [str(w.message).split(": ")[0] for w in rec] == [
        "skipped 1 point(s) with a missing x or y",
        "skipped 2 point(s) whose image could not be read",
    ]
    with pytest.raises(ValueError, match="fraction of the plot height"):
        smpl.add_images(object(), [], [], [], height=2)  # before the target or the points are looked at


def test_a_very_wide_mark_is_decoded_within_max_size(monkeypatch):
    """512 px tall is asked for, but never a longest side past MAX_SIZE (a wordmark wider than 8:1)."""
    from sdvplot import matplotlib as smpl
    from sdvplot._images import MAX_SIZE

    seen = []
    monkeypatch.setattr(smpl, "load_mark_image", lambda mark, size=None: seen.append(size) or Image.new("RGBA", (8, 1)))
    p = type("P", (), {"mark": {"sha256": "0" * 64}, "url": None, "aspect": 20.0})()
    smpl._image(p)
    assert seen == [MAX_SIZE]

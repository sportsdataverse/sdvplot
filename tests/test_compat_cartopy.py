"""Cartopy: logos at longitude/latitude on a GeoAxes, through the matplotlib adapter's transform= (no network)."""

import io

import numpy as np
import pytest

ccrs = pytest.importorskip("cartopy.crs")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

import sdvplot  # noqa: E402
import sdvplot.matplotlib as smpl  # noqa: E402

LAS_VEGAS, LOS_ANGELES, LONDON = (-115.17, 36.17), (-118.24, 34.05), (-0.13, 51.51)
MEXICO_CITY = (-99.13, 19.43)  # below a lower-48 map, inside the figure margin


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _map(projection, extent=None):
    fig = plt.figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(projection=projection)
    if extent is None:
        ax.set_global()
    else:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
    return ax


def _pixels(ax):
    buf = io.BytesIO()
    ax.figure.savefig(buf, format="png", facecolor="white")
    return np.asarray(Image.open(io.BytesIO(buf.getvalue())).convert("RGB"))


def test_logos_sit_at_longitude_latitude_on_a_projected_map(mark_images):
    ax = _map(ccrs.Robinson())
    lons, lats = zip(LAS_VEGAS, LOS_ANGELES, strict=True)
    sdvplot.add_logos(ax, lons, lats, ["LV", "LAR"], league="nfl", height=0.1, transform=ccrs.PlateCarree())
    assert [m[:3] for m in smpl._drawn_marks(ax)] == [("13", *LAS_VEGAS), ("14", *LOS_ANGELES)]
    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()
    for box, (lon, lat) in zip(ax.artists, (LAS_VEGAS, LOS_ANGELES), strict=True):
        ext = box.offsetbox.get_window_extent(renderer)
        want = ax.transData.transform(ax.projection.transform_point(lon, lat, ccrs.PlateCarree()))
        assert ((ext.x0 + ext.x1) / 2, (ext.y0 + ext.y1) / 2) == pytest.approx(tuple(want), abs=0.01)
        assert ext.height / ax.bbox.height == pytest.approx(0.1, abs=1e-6)


def test_wordmarks_and_headshots_take_the_transform_too(mark_images, headshot_images):
    ax = _map(ccrs.PlateCarree())
    sdvplot.add_wordmarks(ax, [LAS_VEGAS[0]], [LAS_VEGAS[1]], ["LV"], league="nfl", transform=ccrs.PlateCarree())
    sdvplot.add_headshots(ax, [LONDON[0]], [LONDON[1]], ["3139477"], league="nfl", transform=ccrs.PlateCarree())
    assert [m[0] for m in smpl._drawn_marks(ax)] == ["13", "3139477"]


def test_a_geoaxes_without_transform_names_the_fix(mark_images):
    with pytest.raises(ValueError, match=r"transform=ccrs\.PlateCarree\(\)"):
        sdvplot.add_logos(_map(ccrs.Robinson()), [LAS_VEGAS[0]], [LAS_VEGAS[1]], ["LV"], league="nfl")


def test_a_point_outside_a_regional_map_is_not_drawn(mark_images):
    ax = _map(ccrs.LambertConformal(), extent=[-125, -66, 24, 50])  # the lower 48
    before = _pixels(ax)
    sdvplot.add_logos(ax, [MEXICO_CITY[0]], [MEXICO_CITY[1]], ["LV"], league="nfl", transform=ccrs.PlateCarree())
    assert np.array_equal(_pixels(ax), before)  # not drawn in the margin, like a data point outside the limits
    sdvplot.add_logos(ax, [LAS_VEGAS[0]], [LAS_VEGAS[1]], ["LV"], league="nfl", transform=ccrs.PlateCarree())
    assert not np.array_equal(_pixels(ax), before)


def test_a_point_behind_the_globe_is_skipped(mark_images):
    ax = _map(ccrs.Orthographic(-100, 40))
    before = _pixels(ax)
    sdvplot.add_logos(ax, [100.0], [-40.0], ["LV"], league="nfl", transform=ccrs.PlateCarree())  # projects to NaN
    assert np.array_equal(_pixels(ax), before)

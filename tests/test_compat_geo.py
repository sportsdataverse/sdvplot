"""GeoPandas and geoplot draw on matplotlib Axes, so sdvplot's matplotlib adapter puts logos on their maps (no network)."""

import pytest

gpd = pytest.importorskip("geopandas")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from shapely.geometry import box  # noqa: E402

import sdvplot  # noqa: E402
import sdvplot.matplotlib as smpl  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _states():
    """Two rectangles standing in for Nevada and California, in longitude/latitude (EPSG:4326)."""
    shapes = [box(-120.0, 35.0, -114.0, 42.0), box(-124.4, 32.5, -120.0, 42.0)]
    return gpd.GeoDataFrame({"team": ["LV", "LAR"]}, geometry=shapes, crs="EPSG:4326", index=[7, 9])


def test_geopandas_plot_takes_logos_at_centroids(mark_images):
    states = _states()
    ax = states.plot(color="#dddddd")
    centers = states.to_crs(3857).centroid.to_crs(4326)  # centroids in a projected CRS, back to lon/lat
    sdvplot.add_logos(ax, centers.x, centers.y, states["team"], league="nfl", height=0.15)
    want = list(zip(["13", "14"], centers.x, centers.y, strict=True))
    assert [m[:3] for m in smpl.drawn_marks(ax)] == want  # read by position: the frame's index is [7, 9]


def test_geoplot_takes_logos_on_its_plain_and_projected_axes(mark_images):
    gplt = pytest.importorskip("geoplot")
    ccrs = pytest.importorskip("cartopy.crs")
    states = _states()
    ax = gplt.polyplot(states)  # no projection: a plain matplotlib Axes in longitude/latitude
    sdvplot.add_logos(ax, [-117.0], [38.5], ["LV"], league="nfl")
    assert [m[0] for m in smpl.drawn_marks(ax)] == ["13"]

    ax = gplt.polyplot(states, projection=gplt.crs.AlbersEqualArea())  # a Cartopy GeoAxes
    with pytest.raises(ValueError, match="transform="):
        sdvplot.add_logos(ax, [-117.0], [38.5], ["LV"], league="nfl")
    sdvplot.add_logos(ax, [-117.0], [38.5], ["LV"], league="nfl", transform=ccrs.PlateCarree())
    assert [m[0] for m in smpl.drawn_marks(ax)] == ["13"]

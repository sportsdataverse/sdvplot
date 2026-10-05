import pandas as pd
import polars as pl
import pytest

pytest.importorskip("plotnine")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
matplotlib.rcParams["figure.max_open_warning"] = 0
import matplotlib.pyplot as plt  # noqa: E402
from plotnine import aes, facet_wrap, geom_col, geom_point, ggplot  # noqa: E402

import sdvplot  # noqa: E402
import sdvplot.plotnine as sp9  # noqa: E402
from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.testing import check_adapter_contract  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _plot():
    frame = pd.DataFrame({"x": [0.0, 30.0], "y": [-10.0, 0.0]})
    return ggplot(frame, aes("x", "y")) + geom_point()


def _axis_plot(categories):
    return ggplot(pd.DataFrame({"team": pd.Categorical(categories, categories), "v": range(len(categories))}),
                  aes("team", "v")) + geom_col()  # fmt: skip


def test_the_plotnine_adapter_passes_the_contract(mark_images, headshot_images):
    check_adapter_contract(sp9, make_target=_plot, make_axis_target=_axis_plot)


def test_the_geom_draws_on_every_facet(mark_images):
    df = pd.DataFrame({"x": [1.0, 2.0], "y": [1.0, 2.0], "team": ["LV", "LAR"], "panel": ["a", "b"]})
    p = ggplot(df, aes("x", "y", team="team")) + sp9.geom_sdv_logos(league="nfl", height=0.2) + facet_wrap("panel")
    marks = sp9.drawn_marks(p)
    assert sorted(m[0] for m in marks) == ["13", "14"] and all(m[3] == 0.2 for m in marks)


def test_the_geom_accepts_polars_data(mark_images):
    df = pl.DataFrame({"x": [1.0], "y": [1.0], "team": ["LV"]})
    p = ggplot(df, aes("x", "y", team="team")) + sp9.geom_sdv_logos(league="nfl")
    assert [m[0] for m in sp9.drawn_marks(p)] == ["13"]


def test_the_geom_needs_a_league():
    with pytest.raises(TypeError, match="needs league="):
        sp9.geom_sdv_logos()


def test_the_geom_checks_height_when_built():
    with pytest.raises(ValueError, match="fraction of the plot height"):
        sp9.geom_sdv_logos(league="nfl", height=2)


def test_add_logos_leaves_the_original_plot_alone(mark_images):
    p = _plot()
    p2 = sdvplot.add_logos(p, [10.0], [-3.0], ["LV"], league="nfl")
    assert p2 is not p and len(p.layers) == 1 and len(p2.layers) == 2


def test_axis_logos_keep_unknown_labels_as_text(mark_images):
    p = sdvplot.axis_logos(_axis_plot(["LV", "XXX", "LAR"]), "x", league="nfl")
    with pytest.warns(SdvplotWarning):
        assert [m[0] for m in sp9.drawn_axis_marks(p, "x")] == ["13", "14"]
    with pytest.warns(SdvplotWarning):
        assert sp9.visible_axis_labels(p, "x") == ["XXX"]


def test_scale_color_sdv_maps_any_team_value_to_its_color(mark_images):
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0], "team": ["LV", "LAR", "XXX"]})
    p = ggplot(df, aes("x", "y", color="team")) + geom_point() + sp9.scale_color_sdv("nfl", na_value="#123456")
    with pytest.warns(SdvplotWarning):
        fig = p.draw()
    colors = [tuple(c) for c in fig.axes[0].collections[0].get_facecolors()]
    to_rgba = matplotlib.colors.to_rgba
    assert colors == [to_rgba("#000000"), to_rgba("#003594"), to_rgba("#123456")]


def test_bad_arguments_fail_when_built_not_when_drawn():
    with pytest.raises(ValueError):
        sdvplot.axis_logos(_axis_plot(["LV"]), "x", league="nfl", mark_type="banner")
    with pytest.raises(ValueError):
        sp9.scale_color_sdv("nfl", which="tertiary")


# geom_from_path: any image by local path or URL (the port of ggpath's geom_from_path)


def _pngs(tmp_path, *names):
    from PIL import Image

    out = []
    for i, name in enumerate(names):
        Image.new("RGBA", (40, 20), (30 * i, 90, 200, 255)).save(tmp_path / name, format="PNG")
        out.append(str(tmp_path / name))
    return out


@pytest.mark.parametrize("lib", [pd, pl])
def test_geom_from_path_draws_each_image_on_its_facet(tmp_path, lib):
    a, b = _pngs(tmp_path, "a.png", "b.png")
    df = lib.DataFrame({"x": [1.0, 2.0], "y": [1.0, 2.0], "img": [a, b], "panel": ["p", "q"]})
    p = ggplot(df, aes("x", "y", path="img")) + sp9.geom_from_path(height=0.2, alpha=0.5) + facet_wrap("panel")
    assert sorted(sp9.drawn_marks(p)) == [(a, 1.0, 1.0, 0.2, a), (b, 2.0, 2.0, 0.2, b)]


def test_geom_from_path_skips_unreadable_images_with_one_warning(tmp_path):
    (a,) = _pngs(tmp_path, "a.png")
    df = pd.DataFrame({"x": [1.0, 2.0], "y": [1.0, 2.0], "img": [a, str(tmp_path / "missing.png")]})
    p = ggplot(df, aes("x", "y", path="img")) + sp9.geom_from_path()
    with pytest.warns(SdvplotWarning, match=r"skipped 1 point\(s\) whose image could not be read"):
        assert [m[0] for m in sp9.drawn_marks(p)] == [a]


def test_geom_from_path_checks_height_and_alpha_when_built():
    with pytest.raises(ValueError, match="fraction of the plot height"):
        sp9.geom_from_path(height=0)
    with pytest.raises(ValueError, match="opacity"):
        sp9.geom_from_path(alpha=-1)

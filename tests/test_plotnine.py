from pathlib import Path

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


# geom_mean_lines / geom_median_lines (the ports of ggpath's), checked against ggpath on real shot rows

FIXTURES = Path(__file__).parent / "fixtures"


def _ref_lines(fig):
    """Per panel, in facet order: the x of each vertical and the y of each horizontal line segment drawn."""
    from matplotlib.collections import LineCollection

    out = []
    for ax in fig.axes:
        v, h = [], []
        for coll in (c for c in ax.collections if isinstance(c, LineCollection)):
            for seg in coll.get_segments():
                (x0, y0), (x1, _) = seg[0], seg[-1]
                (v if x0 == x1 else h).append(float(x0 if x0 == x1 else y0))
        out.append((v, h))
    return out


@pytest.mark.parametrize("ref", ["mean", "median"])
def test_reference_lines_match_ggpath_on_every_facet_panel(ref):
    shots = pl.read_csv(FIXTURES / "nba_shotchartdetail_2023.csv", schema_overrides={"game_id": pl.Utf8})
    oracle = pl.read_csv(FIXTURES / "ggpath_ref_lines.csv").filter(pl.col("ref") == ref).sort("shot_zone_basic")
    geom = sp9.geom_mean_lines if ref == "mean" else sp9.geom_median_lines
    p = (ggplot(shots, aes("loc_x", "loc_y", x0="loc_x", y0="loc_y")) + geom_point() + geom()
         + facet_wrap("shot_zone_basic"))  # fmt: skip
    fig = p.draw()
    counts = shots["shot_zone_basic"].value_counts().sort("shot_zone_basic")["count"].to_list()
    assert [len(ax.collections[0].get_offsets()) for ax in fig.axes] == counts  # facet order = the oracle's
    lines = _ref_lines(fig)
    assert [v for v, _ in lines] == [[pytest.approx(x, rel=1e-12)] for x in oracle["x0"]]
    assert [h for _, h in lines] == [[pytest.approx(y, rel=1e-12)] for y in oracle["y0"]]


def test_one_aesthetic_draws_one_direction():
    df = pd.DataFrame({"x": [1.0, 2.0, 6.0], "y": [1.0, 2.0, 9.0]})
    v_only = (ggplot(df, aes("x", "y")) + geom_point() + sp9.geom_mean_lines(aes(x0="x"))).draw()
    h_only = (ggplot(df, aes("x", "y")) + geom_point() + sp9.geom_median_lines(aes(y0="y"))).draw()
    assert _ref_lines(v_only) == [([3.0], [])] and _ref_lines(h_only) == [([], [2.0])]


def test_reference_lines_need_x0_or_y0():
    p = ggplot(pd.DataFrame({"x": [1.0], "y": [1.0]}), aes("x", "y")) + geom_point() + sp9.geom_mean_lines()
    with pytest.raises(ValueError, match=r"geom_mean_lines\(\) needs an x0 and/or a y0 aesthetic"):
        p.draw()


def test_reference_lines_default_to_ggpath_red_dashed_half_width():
    from plotnine._utils import SIZE_FACTOR

    df = pl.DataFrame({"x": [1.0, 3.0], "y": [1.0, 3.0]})
    fig = (ggplot(df, aes("x", "y", x0="x")) + geom_point() + sp9.geom_mean_lines()).draw()
    (line,) = [c for c in fig.axes[0].collections if type(c).__name__ == "LineCollection"]
    assert tuple(line.get_edgecolor()[0]) == matplotlib.colors.to_rgba("red")
    assert line.get_linewidth()[0] == pytest.approx(0.5 * SIZE_FACTOR) and line.get_linestyle()[0][1] is not None
    fig = (ggplot(df, aes("x", "y", x0="x")) + sp9.geom_mean_lines(color="blue", size=1, linetype="solid",
                                                                    alpha=0.5)).draw()  # fmt: skip
    (line,) = [c for c in fig.axes[0].collections if type(c).__name__ == "LineCollection"]
    assert tuple(line.get_edgecolor()[0]) == pytest.approx(matplotlib.colors.to_rgba("blue", 0.5), abs=1 / 255)
    assert line.get_linewidth()[0] == pytest.approx(SIZE_FACTOR) and line.get_linestyle()[0][1] is None


def test_a_missing_value_drops_that_panels_line_unless_na_rm():
    from plotnine.exceptions import PlotnineWarning

    df = pd.DataFrame({"x": [1.0, 2.0, None, 4.0, 5.0, 6.0], "y": [1.0, 2, 3, 4, 5, 6], "f": list("aaabbb")})
    base = ggplot(df, aes("x", "y", x0="x", y0="y")) + facet_wrap("f")
    with pytest.warns(PlotnineWarning, match="geom_mean_lines : Removed 1 rows containing missing values"):
        lines = _ref_lines((base + sp9.geom_mean_lines()).draw())
    assert lines == [([], [2.0]), ([5.0], [5.0])]  # as ggpath: mean(na.rm = FALSE) is NA, so no vertical line
    assert _ref_lines((base + sp9.geom_mean_lines(na_rm=True)).draw()) == [([1.5], [2.0]), ([5.0], [5.0])]


def test_reference_lines_average_on_the_scale_like_ggplot2():
    from plotnine import scale_x_log10

    # x0/y0 are position aesthetics in ggplot2: on a log10 scale ggpath averages the logs (R: mean(log10(x)) = 1)
    df = pd.DataFrame({"x": [1.0, 10.0, 100.0], "y": [1.0, 2.0, 9.0]})
    fig = (ggplot(df, aes("x", "y", x0="x", y0="y")) + geom_point() + scale_x_log10() + sp9.geom_mean_lines()).draw()
    assert _ref_lines(fig) == [([1.0], [4.0])]


def test_a_mean_line_over_team_bars():
    df = pd.DataFrame({"team": ["LV", "LAR", "LAC"], "epa": [0.1, 0.2, 0.6]})
    fig = (ggplot(df, aes("team", "epa", y0="epa")) + geom_col() + sp9.geom_mean_lines()).draw()
    assert _ref_lines(fig) == [([], [pytest.approx(0.3)])]

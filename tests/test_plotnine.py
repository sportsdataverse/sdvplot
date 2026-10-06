import sys
import warnings
from pathlib import Path

import pandas as pd
import polars as pl
import pytest

pytest.importorskip("plotnine")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
matplotlib.rcParams["figure.max_open_warning"] = 0
import matplotlib.pyplot as plt  # noqa: E402
from plotnine import aes, facet_wrap, geom_col, geom_point, ggplot, xlim  # noqa: E402

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
    marks = sp9._drawn_marks(p)
    assert sorted(m[0] for m in marks) == ["13", "14"] and all(m[3] == pytest.approx(0.2) for m in marks)


def _sdv_warnings(rec):
    return [str(w.message) for w in rec if issubclass(w.category, SdvplotWarning)]


def test_a_faceted_geom_warns_once_per_render_not_once_per_panel(mark_images):
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [1.0, 2.0, 3.0, 4.0], "team": ["LV", "XXX", "LAR", "YYY"],
                       "panel": ["a", "a", "b", "b"]})  # fmt: skip
    p = ggplot(df, aes("x", "y", team="team")) + sp9.geom_sdv_logos(league="nfl") + facet_wrap("panel")
    with pytest.warns(SdvplotWarning) as rec:
        marks = sp9._drawn_marks(p)
    assert sorted(m[0] for m in marks) == ["13", "14"]
    (msg,) = _sdv_warnings(rec)  # one warning naming the unknown teams of every panel
    assert "'XXX'" in msg and "'YYY'" in msg


def test_add_logos_on_a_faceted_plot_warns_once_per_render(mark_images):
    # add_logos' data has no facet column, so plotnine draws the layer in every panel: still one warning
    p = _plot() + facet_wrap("g")
    p.data = p.data.assign(g=["a", "b"])
    p = sdvplot.add_logos(p, [10.0, 20.0], [-3.0, -7.0], ["LV", "XXX"], league="nfl")
    with pytest.warns(SdvplotWarning) as rec:
        assert [m[0] for m in sp9._drawn_marks(p)] == ["13", "13"]
    assert len(_sdv_warnings(rec)) == 1


def test_drawing_leaves_the_process_wide_warning_filters_alone(mark_images, monkeypatch):
    # warnings.catch_warnings swaps the interpreter's one filter list: another thread's warnings change with it
    real, callers = warnings.catch_warnings, []

    def spy(*a, **k):
        callers.append(sys._getframe(1).f_globals.get("__name__", ""))
        return real(*a, **k)

    monkeypatch.setattr(warnings, "catch_warnings", spy)
    p = _plot() + facet_wrap("g")
    p.data = p.data.assign(g=["a", "b"])
    bars = pd.DataFrame({"team": ["LV", "XXX", "LAR"] * 2, "v": [1, 2, 3] * 2, "g": list("aaabbb")})
    for plot in (
        sdvplot.add_logos(p, [10.0, 20.0], [-3.0, -7.0], ["LV", "XXX"], league="nfl"),
        sdvplot.axis_logos(ggplot(bars, aes("team", "v")) + geom_col() + facet_wrap("g"), "x", league="nfl"),
    ):
        with pytest.warns(SdvplotWarning):
            plt.close(plot.draw())
    assert [c for c in callers if c.startswith("sdvplot")] == []


@pytest.mark.parametrize("dropped_by", ["na_rm", "xlim"])
def test_rows_plotnine_drops_itself_do_not_warn(mark_images, dropped_by):
    # na_rm=True silences a missing x, and xlim() removes an out-of-limits one: plotnine's call, not a skip of ours
    x, extra, geom_kw = (
        ([1.0, float("nan")], [], {"na_rm": True}) if dropped_by == "na_rm" else ([1.0, 5.0], [xlim(0, 2)], {})
    )
    p = ggplot(pd.DataFrame({"x": x, "y": [1.0, 2.0], "team": ["LV", "LAR"]}), aes("x", "y", team="team"))
    p = p + sp9.geom_sdv_logos(league="nfl", **geom_kw)
    for layer in extra:
        p = p + layer
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        marks = sp9._drawn_marks(p)
    assert [m[0] for m in marks] == ["13"] and _sdv_warnings(rec) == []


def test_a_point_copied_into_every_panel_counts_once_in_the_warning(mark_images):
    p = _plot() + facet_wrap("g")
    p.data = p.data.assign(g=["a", "b"])
    p = sdvplot.add_wordmarks(p, [10.0, 20.0], [-3.0, -7.0], ["LV", "LAR"], league="nfl")  # no LAR wordmark
    with pytest.warns(SdvplotWarning) as rec:
        sp9._drawn_marks(p)
    assert _sdv_warnings(rec) == ["skipped 1 point(s) with no wordmark archived: 'LAR'"]


def test_a_season_per_team_follows_its_row_into_every_panel(mark_images):
    # plotnine copies add_logos' rows into each panel; each copy keeps its own season (the Oakland mark for 2010)
    p = _plot() + facet_wrap("g")
    p.data = p.data.assign(g=["a", "b"])
    p = sdvplot.add_logos(p, [10.0, 20.0], [-3.0, -7.0], ["LV", "LV"], league="nfl", season=[2010, 2021])
    urls = [m[4] for m in sp9._drawn_marks(p)]
    assert urls == ["https://cdn/3333.png", "https://cdn/1111.png"] * 2


def test_axis_logos_on_a_faceted_plot_warn_once_per_render(mark_images):
    bars = pd.DataFrame({"team": ["LV", "XXX", "LAR"] * 2, "v": [1, 2, 3] * 2, "g": list("aaabbb")})
    p = sdvplot.axis_logos(ggplot(bars, aes("team", "v")) + geom_col() + facet_wrap("g"), "x", league="nfl")
    with pytest.warns(SdvplotWarning) as rec:
        assert sorted(m[0] for m in sp9._drawn_axis_marks(p, "x")) == ["13", "14"]
    assert len(_sdv_warnings(rec)) == 1


def test_the_geom_accepts_polars_data(mark_images):
    df = pl.DataFrame({"x": [1.0], "y": [1.0], "team": ["LV"]})
    p = ggplot(df, aes("x", "y", team="team")) + sp9.geom_sdv_logos(league="nfl")
    assert [m[0] for m in sp9._drawn_marks(p)] == ["13"]


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
        assert [m[0] for m in sp9._drawn_axis_marks(p, "x")] == ["13", "14"]
    with pytest.warns(SdvplotWarning):
        assert sp9._visible_axis_labels(p, "x") == ["XXX"]


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
    with pytest.raises(ValueError, match="alpha"):
        sp9.scale_fill_sdv("nfl", alpha=1.5)


def test_scale_alpha_fades_the_team_colors_but_not_na_value(mark_images):
    # sdvplotR's scale_*_sdv(alpha=) applies scales::alpha() to the team colors only; na.value is drawn as given
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0], "team": ["LV", "LAR", "XXX"]})
    p = ggplot(df, aes("x", "y", fill="team")) + geom_point() + sp9.scale_fill_sdv("nfl", alpha=0.4, na_value="#123456")
    with pytest.warns(SdvplotWarning):
        fig = p.draw()
    colors = [tuple(c) for c in fig.axes[0].collections[0].get_facecolors()]
    to_rgba = matplotlib.colors.to_rgba
    assert colors == [to_rgba("#00000066"), to_rgba("#00359466"), to_rgba("#123456")]
    assert sp9.scale_colour_sdv is sp9.scale_color_sdv
    assert sp9.scale_color_sdv("nfl", alpha=1).map(["LV"], limits=["LV"]) == ["#000000ff"]
    assert sp9.scale_color_sdv("nfl").map(["LV"], limits=["LV"]) == ["#000000"]


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
    marks = sorted(sp9._drawn_marks(p))
    # the hook measures the drawn height, which matplotlib 3.10 (py3.10) rounds a hair off 0.2
    assert [(m[0], m[1], m[2], m[4]) for m in marks] == [(a, 1.0, 1.0, a), (b, 2.0, 2.0, b)]
    assert [m[3] for m in marks] == [pytest.approx(0.2), pytest.approx(0.2)]


def test_geom_from_path_skips_unreadable_images_with_one_warning(tmp_path):
    (a,) = _pngs(tmp_path, "a.png")
    df = pd.DataFrame({"x": [1.0, 2.0], "y": [1.0, 2.0], "img": [a, str(tmp_path / "missing.png")]})
    p = ggplot(df, aes("x", "y", path="img")) + sp9.geom_from_path()
    with pytest.warns(SdvplotWarning, match=r"skipped 1 point\(s\) whose image could not be read"):
        assert [m[0] for m in sp9._drawn_marks(p)] == [a]


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
    # the discrete x makes each team a group, so ggpath 1.1.1 draws 3 identical segments (one per group) at the mean
    assert _ref_lines(fig) == [([], [pytest.approx(0.3)] * 3)]


@pytest.mark.parametrize(("na_rm", "expected"), [(True, [([5.0], [])]), (False, [([], [])])])
def test_reference_lines_drop_values_outside_the_scale_limits_like_ggplot2(na_rm, expected):
    from plotnine import scale_x_continuous
    from plotnine.exceptions import PlotnineWarning

    # R 4.6.1 / ggpath 1.1.1: x0 is a position aesthetic, so 30 (outside the limits) is NA before the mean: na.rm=TRUE
    # draws the line at mean(1, 10, 2, 4, 8) = 5 and na.rm=FALSE draws no vertical line
    df = pd.DataFrame({"x": [1.0, 10, 30, 2, 4, 8], "y": [1.0, 2, 3, 4, 5, 6]})
    p = (ggplot(df, aes("x", "y", x0="x")) + geom_point() + scale_x_continuous(limits=(0, 20))
         + sp9.geom_mean_lines(na_rm=na_rm))  # fmt: skip
    with pytest.warns(PlotnineWarning):  # geom_point drops the point outside the limits, as ggplot2 does
        fig = p.draw()
    assert _ref_lines(fig) == expected


def test_reference_lines_draw_one_segment_per_distinct_aesthetics_like_ggplot2():
    from matplotlib.collections import LineCollection

    # R 4.6.1 / ggpath 1.1.1: GeomVline de-duplicates its rows, so aes(colour = g) draws one segment per group, all at
    # the panel's mean (5), each in its group's colour (#F8766D, #00BFC4: the points' colours); unmapped, one segment
    df = pd.DataFrame({"x": [1.0, 2, 3, 7, 8, 9], "y": [1.0, 2, 3, 4, 5, 6], "g": list("aaabbb")})
    fig = (ggplot(df, aes("x", "y", x0="x", color="g")) + geom_point() + sp9.geom_mean_lines()).draw()
    assert _ref_lines(fig) == [([5.0, 5.0], [])]
    ax = fig.axes[0]
    line_colors = [tuple(c.get_edgecolor()[0]) for c in ax.collections if isinstance(c, LineCollection)]
    point_colors = list(dict.fromkeys(tuple(c) for c in ax.collections[0].get_facecolors()))
    assert line_colors == point_colors and len(set(line_colors)) == 2
    assert _ref_lines((ggplot(df, aes("x", "y", x0="x")) + sp9.geom_mean_lines()).draw()) == [([5.0], [])]


def test_geom_from_path_warns_once_per_draw_and_reads_each_image_once_across_facets(tmp_path, cache, monkeypatch):
    from sdvplot import _cache
    from tests.conftest import FakeResponse, FakeSession

    session = FakeSession(FakeResponse(404))  # one response: a second download of the dead URL would fail the test
    monkeypatch.setattr(_cache, "SESSION", session)
    (a,) = _pngs(tmp_path, "a.png")
    dead = "https://example.com/gone.png"
    # the dead points differ (x 2 and 3): two points; identical points count once, as for the team geoms
    df = pd.DataFrame({"x": [1.0, 2.0, 1.0, 3.0], "y": [1.0] * 4, "img": [a, dead, a, dead], "f": list("ppqq")})
    p = ggplot(df, aes("x", "y", path="img")) + sp9.geom_from_path() + facet_wrap("f")
    with pytest.warns(SdvplotWarning, match=r"skipped 2 point\(s\) whose image could not be read") as rec:
        assert [m[0] for m in sp9._drawn_marks(p)] == [a, a]
    assert len(rec) == 1 and len(session.calls) == 1


def test_geom_from_path_leaves_a_missing_x_to_plotnine(tmp_path):
    from plotnine.exceptions import PlotnineWarning

    (a,) = _pngs(tmp_path, "a.png")
    df = pd.DataFrame({"x": [1.0, None], "y": [1.0, 2.0], "img": [a, a]})
    with pytest.warns(PlotnineWarning, match="Removed 1 rows"):  # plotnine's warning, and no SdvplotWarning
        assert [m[0] for m in sp9._drawn_marks(ggplot(df, aes("x", "y", path="img")) + sp9.geom_from_path())] == [a]

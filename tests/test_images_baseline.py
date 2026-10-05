"""pytest-mpl image baselines: run with `pytest --mpl`; regenerate with `pytest --mpl-generate-path=tests/baseline`.

Figures avoid text (no tick labels, titles or legends) so fonts cannot make the comparison flaky across machines.
"""

import pandas as pd
import pytest

pytest.importorskip("pytest_mpl")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import sdvplot  # noqa: E402

COMPARE = pytest.mark.mpl_image_compare(baseline_dir="baseline", tolerance=2, style="default")


def _bare(ax):
    ax.set_xticks([])
    ax.set_yticks([])
    return ax


@COMPARE
def test_baseline_scatter_with_logos(mark_images):
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.set_xlim(0, 30)
    ax.set_ylim(-10, 0)
    sdvplot.add_logos(_bare(ax), [10, 20], [-3, -7], ["LV", "LAR"], league="nfl", height=0.2)
    sdvplot.add_wordmarks(ax, [15], [-5], ["LV"], league="nfl", height=0.1)
    return fig


@COMPARE
def test_baseline_x_axis_logos(mark_images):
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.bar(["LV", "LAC"], [3, 2])
    ax.set_yticks([])
    sdvplot.axis_logos(ax, "x", league="nfl", mark_type="wordmark", height=0.08)
    return fig


@COMPARE
def test_baseline_y_axis_logos(mark_images):
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.barh(["LV", "LAR"], [3, 2])
    ax.set_xticks([])
    sdvplot.axis_logos(ax, "y", league="nfl", height=0.15)
    return fig


@COMPARE
def test_baseline_plotnine_facets(mark_images):
    p9 = pytest.importorskip("plotnine")
    from sdvplot.plotnine import geom_sdv_logos

    df = pd.DataFrame({"x": [1.0, 2.0, 1.5], "y": [1.0, 2.0, 1.5], "team": ["LV", "LAR", "LV"], "f": ["a", "a", "b"]})
    p = (
        p9.ggplot(df, p9.aes("x", "y", team="team"))
        + geom_sdv_logos(league="nfl", height=0.2)
        + p9.facet_wrap("f")
        + p9.theme_void()
        + p9.theme(figure_size=(4, 2), strip_text=p9.element_blank())
    )
    return p.draw()


@COMPARE
def test_baseline_title_image(mark_images):
    from sdvplot.matplotlib import title_image

    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    title_image(_bare(ax), "LV", league="nfl")  # a blank title: the image alone, centred, no glyphs
    return fig


@COMPARE
def test_baseline_court_coords_half_court():
    pytest.importorskip("sportypy")
    from pathlib import Path

    import polars as pl

    raw = pl.read_csv(Path(__file__).parent / "fixtures" / "nba_shotchartdetail_2023.csv")  # real shots (README)
    shots = sdvplot.court_coords(raw, x="loc_x", y="loc_y")
    fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
    sdvplot.surface("nba", ax=ax, display_range="defense")
    made = shots["shot_made_flag"] == 1
    ax.scatter(shots["court_x"].filter(made), shots["court_y"].filter(made), s=14, c="#1a9850", zorder=50)
    ax.scatter(shots["court_x"].filter(~made), shots["court_y"].filter(~made), s=14, c="#d73027", marker="x", zorder=50)
    return fig


@COMPARE
def test_baseline_add_images(tmp_path):
    from PIL import Image

    from sdvplot.matplotlib import add_images

    wide, tall = tmp_path / "wide.png", tmp_path / "tall.png"
    Image.new("RGBA", (60, 20), (31, 119, 180, 255)).save(wide)
    Image.new("RGBA", (20, 40), (214, 39, 40, 255)).save(tall)
    fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    add_images(_bare(ax), [3, 7], [5, 5], [wide, tall], height=0.25, alpha=0.8)
    return fig


@COMPARE
def test_baseline_team_tiers(mark_images):
    from sdvplot.matplotlib import team_tiers

    df = pd.DataFrame({"tier_no": [1, 1, 2, 3, 3], "team": ["LV", "LAR", "LV", "LAR", "LV"]})
    fig = team_tiers(df, "nfl", title="", subtitle="", tier_desc={}, no_line_below_tier=2)  # no text to drift
    fig.set_size_inches(4, 3)
    return fig


@COMPARE
def test_baseline_team_tiers_light(mark_images):
    from sdvplot.matplotlib import team_tiers

    df = pd.DataFrame({"tier_no": [1, 1, 2, 3, 3], "team": ["LV", "LAR", "LV", "LAR", "LV"]})
    fig = team_tiers(df, "nfl", title="", subtitle="", tier_desc={}, no_line_below_tier=2, theme="light")
    fig.set_size_inches(4, 3)
    return fig


@COMPARE
def test_baseline_plotnine_title_image(mark_images):
    p9 = pytest.importorskip("plotnine")
    from sdvplot.plotnine import title_image

    df = pd.DataFrame({"x": [1.0, 2.0], "y": [1.0, 2.0]})
    p = (
        p9.ggplot(df, p9.aes("x", "y"))
        + p9.geom_point()
        + title_image("LAR", league="nfl", side="right")
        + p9.theme_void()
        + p9.theme(figure_size=(4, 2))
    )
    return p.draw()


@COMPARE
def test_baseline_plotnine_team_tiers(mark_images):
    pytest.importorskip("plotnine")
    import plotnine as p9

    from sdvplot.plotnine import team_tiers

    df = pd.DataFrame({"tier_no": [1, 1, 2, 3, 3], "team": ["LV", "LAR", "LV", "LAR", "LV"]})
    p = team_tiers(df, "nfl", title="", subtitle="", tier_desc={}, no_line_below_tier=2) + p9.theme(figure_size=(4, 3))
    return p.draw()


@COMPARE
def test_baseline_plotnine_team_tiers_light(mark_images):
    pytest.importorskip("plotnine")
    import plotnine as p9

    from sdvplot.plotnine import team_tiers

    df = pd.DataFrame({"tier_no": [1, 1, 2, 3, 3], "team": ["LV", "LAR", "LV", "LAR", "LV"]})
    p = team_tiers(df, "nfl", title="", subtitle="", tier_desc={}, no_line_below_tier=2, theme="light")
    return (p + p9.theme(figure_size=(4, 3))).draw()


@COMPARE
def test_baseline_plotnine_mean_and_median_lines():
    p9 = pytest.importorskip("plotnine")
    from sdvplot.plotnine import geom_mean_lines, geom_median_lines

    df = pd.DataFrame({"x": [1.0, 2.0, 6.0, 1.0, 3.0, 8.0], "y": [1.0, 2.0, 9.0, 4.0, 5.0, 6.0], "f": list("aaabbb")})
    p = (
        p9.ggplot(df, p9.aes("x", "y", x0="x", y0="y"))
        + p9.geom_point()
        + geom_mean_lines()
        + geom_median_lines(color="blue", linetype="dotted")
        + p9.facet_wrap("f")
        + p9.theme_void()
        + p9.theme(figure_size=(4, 2), strip_text=p9.element_blank())
    )
    return p.draw()

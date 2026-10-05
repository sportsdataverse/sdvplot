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

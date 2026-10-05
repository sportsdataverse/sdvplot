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

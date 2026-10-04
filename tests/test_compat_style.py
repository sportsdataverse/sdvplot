"""PyPalettes, morethemes, pyfonts and wordcloud style a plot; sdvplot hands them team colors, and logos still draw on
the styled Axes. Offline except pyfonts, which downloads its fonts (live only)."""

import os

import pytest

pytest.importorskip("matplotlib")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import to_hex  # noqa: E402

import sdvplot  # noqa: E402
import sdvplot.matplotlib as smpl  # noqa: E402

TEAMS = ["LV", "LAR"]


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def test_pypalettes_builds_a_colormap_from_team_colors(mark_images):
    pypalettes = pytest.importorskip("pypalettes")
    colors = sdvplot.team_colors(TEAMS, "nfl")
    cmap = pypalettes.create_cmap(colors, cmap_type="discrete")
    assert [to_hex(c) for c in cmap.colors] == colors
    _, ax = plt.subplots()
    ax.scatter([10, 20], [-3, -7], c=[0, 1], cmap=cmap, s=400)
    sdvplot.add_logos(ax, [10, 20], [-3, -7], TEAMS, league="nfl")
    assert [m[0] for m in smpl.drawn_marks(ax)] == ["13", "14"]


def test_a_morethemes_theme_keeps_logos_drawing(mark_images):
    morethemes = pytest.importorskip("morethemes")
    with matplotlib.rc_context():  # set_theme changes global rcParams; keep them out of other tests
        morethemes.set_theme("wsj")
        _, ax = plt.subplots()
        ax.plot([0, 30], [-10, 0])
        sdvplot.add_logos(ax, [10, 20], [-3, -7], TEAMS, league="nfl", height=0.15)
        ax.figure.canvas.draw()
        assert [m[0] for m in smpl.drawn_marks(ax)] == ["13", "14"]


def test_wordcloud_colors_each_team_with_its_own_color(mark_images):
    wordcloud = pytest.importorskip("wordcloud")
    names = ["Las Vegas Raiders", "Los Angeles Rams"]
    color = dict(zip(names, sdvplot.team_colors(names, "nfl"), strict=True))  # names resolve like any other id
    cloud = wordcloud.WordCloud(
        width=200, height=100, background_color="white", random_state=1, color_func=lambda word, **kw: color[word]
    ).generate_from_frequencies({"Las Vegas Raiders": 3, "Los Angeles Rams": 2})
    assert {word: c for (word, _), _, _, _, c in cloud.layout_} == color


@pytest.mark.skipif(os.environ.get("SDVPLOT_LIVE_TESTS") != "1", reason="network: pyfonts downloads its fonts")
def test_a_pyfonts_font_and_logos_share_an_axes(mark_images):
    pyfonts = pytest.importorskip("pyfonts")
    font = pyfonts.load_google_font("Roboto", weight="bold")
    _, ax = plt.subplots()
    ax.set_title("Raiders vs Rams", font=font)
    sdvplot.add_logos(ax, [10, 20], [-3, -7], TEAMS, league="nfl")
    ax.figure.canvas.draw()
    assert ax.title.get_fontproperties().get_name() == "Roboto"
    assert [m[0] for m in smpl.drawn_marks(ax)] == ["13", "14"]

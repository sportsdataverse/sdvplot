"""highlight-text, Flexitext and drawarrow annotate matplotlib Axes: their text and arrows, in team colors, share the
Axes with sdvplot logos (no network)."""

import pytest

pytest.importorskip("matplotlib")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import to_hex  # noqa: E402
from matplotlib.text import Text  # noqa: E402

import sdvplot  # noqa: E402
import sdvplot.matplotlib as smpl  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _axes():
    _, ax = plt.subplots(figsize=(6, 4), dpi=100)
    ax.set_xlim(0, 30)
    ax.set_ylim(-10, 0)
    return ax


def _colored_texts(ax):
    """{text: hex color} of every Text drawn on the figure, after a draw."""
    ax.figure.canvas.draw()
    return {t.get_text(): to_hex(t.get_color()) for t in ax.figure.findobj(Text) if t.get_text().strip()}


def test_highlight_text_and_logos_share_an_axes(mark_images):
    highlight_text = pytest.importorskip("highlight_text")
    lv, lar = sdvplot.team_colors("nfl", ["LV", "LAR"])
    ax = _axes()
    highlight_text.ax_text(
        2, -1, "<Raiders> beat the <Rams>", highlight_textprops=[{"color": lv}, {"color": lar}], ax=ax
    )
    sdvplot.add_logos(ax, [10, 20], [-3, -7], ["LV", "LAR"], league="nfl")
    texts = _colored_texts(ax)
    assert texts["Raiders"] == lv and texts["Rams"] == lar
    assert [m[0] for m in smpl._drawn_marks(ax)] == ["13", "14"]


def test_flexitext_and_logos_share_an_axes(mark_images):
    flexitext = pytest.importorskip("flexitext")
    lv, lar = sdvplot.team_colors("nfl", ["LV", "LAR"])
    ax = _axes()
    flexitext.flexitext(0.05, 0.95, f"<color:{lv}>Raiders</> vs <color:{lar}>Rams</>", ax=ax)
    sdvplot.add_logos(ax, [10, 20], [-3, -7], ["LV", "LAR"], league="nfl")
    texts = _colored_texts(ax)
    assert texts["Raiders"] == lv and texts["Rams"] == lar
    assert [m[0] for m in smpl._drawn_marks(ax)] == ["13", "14"]


def test_drawarrow_arrows_join_logos(mark_images):
    drawarrow = pytest.importorskip("drawarrow")
    ax = _axes()
    arrow = drawarrow.ax_arrow((10, -3), (20, -7), ax=ax, color=sdvplot.team_colors("nfl", "LAR"))
    sdvplot.add_logos(ax, [10, 20], [-3, -7], ["LV", "LAR"], league="nfl", height=0.1)
    ax.figure.canvas.draw()
    assert arrow in ax.patches
    assert [m[:3] for m in smpl._drawn_marks(ax)] == [("13", 10, -3), ("14", 20, -7)]

import pandas as pd
import pytest

pytest.importorskip("plottable")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from plottable import Table  # noqa: E402

from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.plottable import headshot_column, logo_column  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _cells(fig):
    return [ax._sdvplot_cell for ax in fig.axes if hasattr(ax, "_sdvplot_cell")]


def test_a_logo_column_draws_each_known_team(mark_images):
    fig, ax = plt.subplots()
    df = pd.DataFrame({"team": ["LV", "XXX", "LAR"], "wins": [10, 5, 8]}).set_index("wins")
    with pytest.warns(SdvplotWarning):
        Table(df, ax=ax, column_definitions=[logo_column("team", league="nfl", title="")])
    assert _cells(fig) == ["13", "14"]


def test_a_headshot_column_draws_each_player(headshot_images):
    fig, ax = plt.subplots()
    df = pd.DataFrame({"player": ["3139477", "4241479"], "n": [1, 2]}).set_index("n")
    Table(df, ax=ax, column_definitions=[headshot_column("player", league="nfl")])
    assert _cells(fig) == ["3139477", "4241479"]

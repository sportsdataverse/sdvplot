"""NetworkX, PyWaffle, DayPlot and bumplot draw on matplotlib Axes: logos go on their output through sdvplot's
matplotlib adapter, at positions those packages report (no network)."""

import datetime as dt

import pytest

pytest.importorskip("matplotlib")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import sdvplot  # noqa: E402
import sdvplot.matplotlib as smpl  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _xyz(ax):
    return [m[:3] for m in smpl.drawn_marks(ax)]


def test_networkx_nodes_take_logos_at_their_layout_positions(mark_images):
    nx = pytest.importorskip("networkx")
    graph = nx.Graph([("LV", "LAR")])
    pos = nx.spring_layout(graph, seed=7)
    _, ax = plt.subplots()
    nx.draw(graph, pos, ax=ax, node_color="#dddddd")
    nodes = list(graph)
    sdvplot.add_logos(ax, [pos[n][0] for n in nodes], [pos[n][1] for n in nodes], nodes, league="nfl")
    assert _xyz(ax) == [(t, pos[n][0], pos[n][1]) for t, n in zip(["13", "14"], nodes, strict=True)]


def test_a_pywaffle_figure_takes_logos(mark_images):
    pywaffle = pytest.importorskip("pywaffle")
    fig = plt.figure(FigureClass=pywaffle.Waffle, rows=5, values={"LV": 12, "LAR": 8})
    ax = fig.axes[0]
    sdvplot.add_logos(fig, [0.25, 0.75], [0.5, 0.5], ["LV", "LAR"], league="nfl", transform=ax.transAxes)
    assert _xyz(ax) == [("13", 0.25, 0.5), ("14", 0.75, 0.5)]
    fig.canvas.draw()


def test_dayplot_calendar_cells_take_logos(mark_images):
    dayplot = pytest.importorskip("dayplot")
    games = [dt.date(2025, 9, 7), dt.date(2025, 9, 14), dt.date(2025, 9, 21)]
    _, ax = plt.subplots(figsize=(12, 3))
    cells = dayplot.calendar(games, [24, 17, 31], start_date="2025-09-01", end_date="2025-09-30", ax=ax)
    first, last = cells[0].get_bbox(), cells[-1].get_bbox()  # one patch per day, in date order
    xs, ys = [(first.x0 + first.x1) / 2, (last.x0 + last.x1) / 2], [(first.y0 + first.y1) / 2, (last.y0 + last.y1) / 2]
    sdvplot.add_logos(ax, xs, ys, ["LV", "LAR"], league="nfl", height=0.12)
    assert _xyz(ax) == [("13", xs[0], ys[0]), ("14", xs[1], ys[1])]
    ax.figure.canvas.draw()


def test_bumplot_lines_take_logos_at_their_last_rank(mark_images):
    bumplot = pytest.importorskip("bumplot")
    import pandas as pd

    df = pd.DataFrame({"week": [1, 2, 3], "LV": [10, 30, 20], "LAR": [20, 10, 30]})
    _, ax = plt.subplots()
    _, artists = bumplot.bumplot(x="week", y_columns=["LV", "LAR"], data=df, ax=ax)
    ends = [artists[team][1].get_offsets()[-1] for team in ("LV", "LAR")]  # each line's last scatter point
    sdvplot.add_logos(ax, [e[0] for e in ends], [e[1] for e in ends], ["LV", "LAR"], league="nfl")
    assert _xyz(ax) == [("13", 3, 2), ("14", 3, 1)]  # week 3: LAR ranks first, LV second
    ax.figure.canvas.draw()

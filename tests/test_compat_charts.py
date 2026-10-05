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
    return [m[:3] for m in smpl._drawn_marks(ax)]


def _teams(ax):
    return [m[0] for m in smpl._drawn_marks(ax)]


def _logo_centres(ax):
    """Where matplotlib drew each sdvplot mark after the last canvas draw, in display pixels."""
    renderer = ax.figure.canvas.get_renderer()
    boxes = [a for a in ax.artists if hasattr(a, "_sdvplot_mark")]
    return [tuple(b.get_window_extent(renderer).get_points().mean(axis=0)) for b in boxes]


def _centre(patch):
    return pytest.approx(tuple(patch.get_window_extent().get_points().mean(axis=0)), abs=1)  # within a pixel


def test_networkx_nodes_take_logos_at_their_layout_positions(mark_images):
    nx = pytest.importorskip("networkx")
    from matplotlib.collections import PathCollection

    graph = nx.Graph([("LV", "LAR")])
    pos = nx.spring_layout(graph, seed=7)
    _, ax = plt.subplots()
    nx.draw(graph, pos, ax=ax, node_color="#dddddd")
    nodes = list(graph)
    sdvplot.add_logos(ax, [pos[n][0] for n in nodes], [pos[n][1] for n in nodes], nodes, league="nfl")
    ax.figure.canvas.draw()
    dots = next(c for c in ax.collections if isinstance(c, PathCollection))  # networkx's nodes, in graph order
    want = dots.get_offset_transform().transform(dots.get_offsets())
    got = _logo_centres(ax)
    assert _teams(ax) == ["13", "14"]
    assert got == [pytest.approx(tuple(w), abs=1) for w in want]  # each logo on the node networkx drew
    assert all(ax.bbox.contains(*c) for c in got)  # inside the limits networkx set, so not clipped


def test_a_pywaffle_figure_takes_logos(mark_images):
    pywaffle = pytest.importorskip("pywaffle")
    fig = plt.figure(FigureClass=pywaffle.Waffle, rows=5, values={"LV": 12, "LAR": 8})
    ax = fig.axes[0]
    fig.canvas.draw()
    blocks = [ax.patches[0], ax.patches[12]]  # pywaffle draws LV's 12 blocks, then LAR's 8
    assert blocks[0].get_facecolor() != blocks[1].get_facecolor()
    centres = [b.get_window_extent().get_points().mean(axis=0) for b in blocks]
    xs, ys = zip(*ax.transAxes.inverted().transform(centres), strict=True)  # the block centres as Axes fractions
    sdvplot.add_logos(fig, xs, ys, ["LV", "LAR"], league="nfl", transform=ax.transAxes)
    fig.canvas.draw()
    assert _teams(ax) == ["13", "14"]
    assert _logo_centres(ax) == [_centre(b) for b in blocks]


def test_dayplot_calendar_cells_take_logos(mark_images):
    dayplot = pytest.importorskip("dayplot")
    games = [dt.date(2025, 9, 7), dt.date(2025, 9, 14), dt.date(2025, 9, 21)]
    _, ax = plt.subplots(figsize=(12, 3))
    cells = dayplot.calendar(games, [24, 17, 31], start_date="2025-09-01", end_date="2025-09-30", ax=ax)
    first, last = cells[0].get_bbox(), cells[-1].get_bbox()  # one patch per day, in date order
    xs, ys = [(first.x0 + first.x1) / 2, (last.x0 + last.x1) / 2], [(first.y0 + first.y1) / 2, (last.y0 + last.y1) / 2]
    sdvplot.add_logos(ax, xs, ys, ["LV", "LAR"], league="nfl", height=0.12)
    ax.figure.canvas.draw()
    assert _teams(ax) == ["13", "14"]
    assert _logo_centres(ax) == [_centre(cells[0]), _centre(cells[-1])]  # on the cells dayplot drew


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

"""Live: real teams from the shipped index, real logos and a real headshot from the archive (network)."""

import os

import pytest

pytest.importorskip("matplotlib")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import sdvplot  # noqa: E402
import sdvplot.matplotlib as smpl  # noqa: E402

pytestmark = [
    pytest.mark.real_index,
    pytest.mark.skipif(os.environ.get("SDVPLOT_LIVE_TESTS") != "1", reason="network: set SDVPLOT_LIVE_TESTS=1"),
]


@pytest.mark.parametrize(
    ("league", "teams"), [("nfl", ["KC", "BUF"]), ("nba", ["LAL", "BOS"]), ("cfb", ["Alabama", "Georgia"])]
)
def test_real_logos_draw(league, teams, tmp_path, monkeypatch):
    monkeypatch.setenv("SDVPLOT_CACHE_DIR", str(tmp_path))
    _, ax = plt.subplots()
    sdvplot.add_logos(ax, [0.3, 0.7], [0.5, 0.5], teams, league=league, height=0.2)
    assert [m[0] for m in smpl.drawn_marks(ax)] == sdvplot.resolve(teams, league)
    plt.close("all")


def test_a_real_headshot_draws(tmp_path, monkeypatch):
    monkeypatch.setenv("SDVPLOT_CACHE_DIR", str(tmp_path))
    _, ax = plt.subplots()
    sdvplot.add_headshots(ax, [0.5], [0.5], ["3139477"], league="nfl", height=0.3)
    assert [m[0] for m in smpl.drawn_marks(ax)] == ["3139477"]
    plt.close("all")

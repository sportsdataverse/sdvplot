"""Headshots by the league's own player id (``id_system="league"``, sdvplotR's ``id_type = "league"``): the CDN URL
templates, the error for a league without them, the placement key, every adapter, and the datacenter 403 message."""

import hashlib
import io
import json
import time

import numpy as np
import polars as pl
import pytest

import sdvplot
from sdvplot import _cache, _headshots
from sdvplot._errors import DownloadError, InputError
from sdvplot._images import load_url_image
from sdvplot._placement import place
from tests.conftest import FakeResponse, FakeSession, seed_image

# real ids: LeBron James (NBA Stats), A'ja Wilson (WNBA Stats), Shohei Ohtani (MLBAM), Connor McDavid (NHL API)
TEMPLATES = {
    "nba": ("2544", "https://cdn.nba.com/headshots/nba/latest/260x190/2544.png"),
    "wnba": ("1628932", "https://cdn.wnba.com/headshots/wnba/latest/260x190/1628932.png"),
    "mlb": (
        "660271",
        "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/"
        "w_213,q_auto:best/v1/people/660271/headshot/67/current.png",
    ),
    "nhl": ("8478402", "https://assets.nhle.com/mugs/nhl/latest/8478402.png"),
}
PLAYERS = ("2544", "201939")  # NBA Stats PERSON_IDs the adapter tests draw


@pytest.mark.parametrize("league", sorted(TEMPLATES))
def test_league_ids_build_each_cdns_url_as_sdvplotr_does(league):
    pid, url = TEMPLATES[league]
    assert _headshots.headshot_url(pid, league, id_system="league") == url


@pytest.mark.parametrize("player_id", [2544, "2544", 2544.0, " 2544 ", np.int64(2544)])
def test_league_ids_accept_numeric_variants(player_id):
    assert _headshots.headshot_url(player_id, "nba", id_system="league") == TEMPLATES["nba"][1]


@pytest.mark.parametrize("player_id", [None, float("nan"), "", "abc", "1.5", 1.5, True, "٢٥٤٤"])
def test_league_ids_return_none_for_null_and_malformed_ids(player_id):
    assert _headshots.headshot_url(player_id, "nba", id_system="league") is None


@pytest.mark.parametrize("league", ["cfb", "mbb", "wbb", "ohl"])
def test_a_league_without_league_id_headshots_is_an_error_that_names_the_ones_with_them(league):
    with pytest.raises(
        InputError, match=r"no headshots by league player id for league '.*'; supported: \['nfl', 'nba'"
    ):
        _headshots.headshot_url("1", league, id_system="league")
    with pytest.raises(InputError, match="id_system='espn'"):  # a null id does not hide the bad league
        _headshots.headshot_url(None, league, id_system="league")


def test_the_nfls_league_id_is_the_gsis_id(cache, monkeypatch):
    buf = io.BytesIO()
    pl.DataFrame({"gsis_id": ["00-0033873"], "espn_id": ["3139477"], "headshot": [None]}).write_parquet(buf)
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, buf.getvalue())))
    _headshots._players.cache_clear()
    gsis = _headshots.headshot_url("00-0033873", "nfl", id_system="gsis")
    assert gsis == "https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/3139477.png"
    assert _headshots.headshot_url("00-0033873", "nfl", id_system="league") == gsis


def test_place_keys_a_league_id_by_its_integer_form():
    (p,) = place([1.0], [2.0], [2544.0], league="nba", kind="headshot", id_system="league")
    assert (p.team_id, p.url) == ("2544", TEMPLATES["nba"][1])


@pytest.fixture
def league_headshot_images(cache):
    """The PLAYERS' NBA league-id headshots as cached, fresh PNGs (cdn.nba.com's 260 x 190)."""
    for pid in PLAYERS:
        url = _headshots.headshot_url(pid, "nba", id_system="league")
        key = hashlib.sha256(url.encode()).hexdigest()
        path = seed_image(cache / "urlimages" / key[:2] / key, size=(130, 95))
        _cache._meta_path(path).write_text(json.dumps({"fetched_at": time.time()}))
    return cache


def _matplotlib():
    plt = pytest.importorskip("matplotlib.pyplot")
    import sdvplot.matplotlib as mod

    _, ax = plt.subplots()
    ax.set(xlim=(0, 30), ylim=(-10, 0))
    return mod, ax


def _plotnine():
    pytest.importorskip("plotnine")
    import pandas as pd
    from plotnine import aes, geom_point, ggplot

    import sdvplot.plotnine as mod

    return mod, ggplot(pd.DataFrame({"x": [0.0, 30.0], "y": [-10.0, 0.0]}), aes("x", "y")) + geom_point()


def _plotly():
    go = pytest.importorskip("plotly.graph_objects")
    import sdvplot.plotly as mod

    return mod, go.Figure(go.Scatter(x=[0, 30], y=[-10, 0], mode="markers"))


def _altair():
    alt = pytest.importorskip("altair")
    import sdvplot.altair as mod

    data = alt.Data(values=[{"a": 0, "b": -10}, {"a": 30, "b": 0}])
    return mod, alt.Chart(data).mark_point().encode(x="a:Q", y="b:Q").properties(height=200)


def _bokeh():
    pytest.importorskip("bokeh")
    from bokeh.plotting import figure

    import sdvplot.bokeh as mod

    return mod, figure(x_range=(0, 30), y_range=(-10, 0), frame_height=300)


def _holoviews():
    hv = pytest.importorskip("holoviews")
    pytest.importorskip("bokeh")
    import holoviews.plotting.bokeh  # noqa: F401

    import sdvplot.holoviews as mod

    hv.Store.set_current_backend("bokeh")
    return mod, hv.Scatter([(0, -10), (30, 0)]).opts(frame_height=300)


def _folium():
    folium = pytest.importorskip("folium")
    import sdvplot.folium as mod

    return mod, folium.Map(location=[0, 0], zoom_start=2)


def _pygal():
    pygal = pytest.importorskip("pygal")
    import sdvplot.pygal as mod

    chart = pygal.XY(stroke=False, show_legend=False)
    chart.add("games", [(10, -3), (20, -7)])
    return mod, chart


@pytest.mark.parametrize("make", [_matplotlib, _plotnine, _plotly, _altair, _bokeh, _holoviews, _folium, _pygal])
def test_every_plot_adapter_draws_headshots_by_league_id(make, league_headshot_images):
    mod, target = make()
    drawn = sdvplot.add_headshots(target, [10, 20], [-3, -7], list(PLAYERS), league="nba", id_system="league")
    marks = mod._drawn_marks(drawn)
    assert [m[0] for m in marks] == list(PLAYERS)
    urls = {_headshots.headshot_url(p, "nba", id_system="league") for p in PLAYERS}
    assert all(m[4] in urls or str(m[4]).startswith("data:image/png;base64,") for m in marks), marks
    if hasattr(target, "figure"):  # matplotlib
        import matplotlib.pyplot as plt

        plt.close("all")


def test_great_tables_cells_and_column_labels_take_league_ids(league_headshot_images):
    great_tables = pytest.importorskip("great_tables")
    import sdvplot.great_tables as sgt

    url = _headshots.headshot_url("2544", "nba", id_system="league")
    gt = great_tables.GT(pl.DataFrame({"player": ["2544"]}))
    out = sdvplot.add_headshots(gt, "player", league="nba", id_system="league")
    assert sgt._drawn_cells(out) == [("2544", 0, "player", 30.0, url)]
    out = sgt.gt_sdv_headshots(gt, "player", league="nba", height=40, id_system="league")
    assert sgt._drawn_cells(out) == [("2544", 0, "player", 40.0, url)]
    labels = sgt.gt_sdv_cols_label(
        great_tables.GT(pl.DataFrame({"2544": [1]})), mark_type="headshot", league="nba", id_system="league"
    )
    assert sgt._drawn_cells(labels) == [("2544", -1, "2544", 30.0, url)]


def test_reactable_columns_take_league_ids():
    pytest.importorskip("reactable")
    from reactable import CellInfo

    from sdvplot.reactable import reactable_sdv_headshots

    shot = reactable_sdv_headshots(league="nba", id="p", id_system="league").cell(CellInfo("2544", 0, "p"))
    assert f'src="{TEMPLATES["nba"][1]}"' in shot


def test_plottable_columns_take_league_ids(league_headshot_images):
    pytest.importorskip("plottable")
    import matplotlib.pyplot as plt
    import pandas as pd
    from plottable import Table

    from sdvplot.plottable import headshot_column

    fig, ax = plt.subplots()
    df = pd.DataFrame({"player": list(PLAYERS), "n": [1, 2]}).set_index("n")
    Table(df, ax=ax, column_definitions=[headshot_column("player", league="nba", id_system="league")])
    assert [a._sdvplot_cell for a in fig.axes if hasattr(a, "_sdvplot_cell")] == list(PLAYERS)
    plt.close("all")


@pytest.mark.parametrize("league", ["nba", "wnba"])
def test_a_403_from_the_nba_cdns_names_the_datacenter_block(cache, monkeypatch, league):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(403, b"forbidden")))
    url = _headshots.headshot_url(TEMPLATES[league][0], league, id_system="league")
    with pytest.raises(DownloadError, match=r"answers 403 to datacenter and cloud IPs .*residential connection"):
        load_url_image(url)


def test_a_403_elsewhere_keeps_the_plain_message(cache, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(403, b"forbidden")))
    with pytest.raises(DownloadError, match="HTTP 403") as e:
        load_url_image(_headshots.headshot_url("3139477", "nfl"))
    assert "datacenter" not in str(e.value)

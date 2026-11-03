import base64

import pytest
import requests

from sdvplot import _cache, _web
from sdvplot._errors import DownloadError, OfflineError, SdvplotWarning
from sdvplot._placement import Placement, place
from tests.conftest import FakeResponse, FakeSession


def test_aspect_comes_from_the_manifest_or_the_headshot_constant(manifest):
    (logo,) = place([0], [0], ["LV"], league="nfl")
    (wordmark,) = place([0], [0], ["LV"], league="nfl", kind="wordmark")
    (headshot,) = place([0], [0], ["3139477"], league="nfl", kind="headshot", id_system="espn")
    assert (_web.aspect(logo), _web.aspect(wordmark)) == (1.0, 2.5)
    assert _web.aspect(headshot) == _web.HEADSHOT_ASPECT == pytest.approx(600 / 436)
    (hockeytech,) = place([0], [0], ["52"], league="pwhl", kind="headshot", id_system="league")
    assert _web.aspect(hockeytech) == 1.0  # leaguestat's 240x240 squares, not ESPN's 600x436
    (junior,) = place([0], [0], ["5833"], league="mjhl", kind="headshot", id_system="league")
    assert _web.aspect(junior) == 1.0  # the junior and minor leagues share the prefix


def test_without_embed_the_source_is_the_archive_url_and_nothing_is_downloaded(manifest):
    (p,) = place([0], [0], ["LV"], league="nfl")
    assert _web.image_src(p) == "https://cdn/1111.png"  # the fake session has no response left to serve


def test_embed_is_a_data_uri_of_the_cached_bytes(mark_images):
    (p,) = place([0], [0], ["LV"], league="nfl")
    head, body = _web.image_src(p, embed=True).split(",", 1)
    assert head == "data:image/png;base64"
    assert base64.b64decode(body) == (mark_images / "images" / "11" / f"{'1' * 64}.png").read_bytes()


def test_an_svg_mark_embeds_as_svg(cache):
    sha = "e" * 64
    path = cache / "images" / sha[:2] / f"{sha}.svg"
    path.parent.mkdir(parents=True)
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>')
    _cache._intact.add(str(path.resolve()))  # the sha is made up: count the seeded file as verified
    row = {"sha256": sha, "ext": "svg", "archive_url": "https://cdn/eeee.svg"}
    p = Placement("13", 0, 0, "https://cdn/eeee.svg", 1.0, row)
    assert _web.image_src(p, embed=True).startswith("data:image/svg+xml;base64,")


def test_a_headshot_embeds_with_the_type_of_its_bytes(headshot_images):
    (p,) = place([0], [0], ["3139477"], league="nfl", kind="headshot", id_system="espn")
    assert _web.image_src(p, embed=True).startswith("data:image/png;base64,")


def test_embed_offline_without_a_cached_image_raises(manifest, monkeypatch):
    (p,) = place([0], [0], ["LV"], league="nfl")
    monkeypatch.setattr(_cache, "SESSION", FakeSession(requests.ConnectionError("offline")))
    with pytest.raises(OfflineError, match="https://cdn/1111.png"):
        _web.image_src(p, embed=True)


def test_image_sources_read_each_image_once(mark_images, monkeypatch):
    calls = []
    real = _web.image_src
    monkeypatch.setattr(_web, "image_src", lambda p, *, embed=False: calls.append(p.url) or real(p, embed=embed))
    placements = place([0, 1, 2], [0, 0, 0], ["LV", "LAR", "LV"], league="nfl")
    sources = _web.image_sources(placements, embed=True)
    assert calls == ["https://cdn/1111.png", "https://cdn/6666.png"]
    assert sources[0] == sources[2] != sources[1]


def test_present_skips_a_404_headshot_with_one_warning(headshot_images, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(404)))  # one download: the unknown id
    placements = place([0, 1, 2], [0, 0, 0], ["3139477", "999", "4241479"], league="nfl", kind="headshot")
    with pytest.warns(SdvplotWarning, match=r"skipped 1 point\(s\) whose headshot is missing \(HTTP 404\): '999'"):
        kept = _web.present(placements, embed=True)
    assert [p.team_id for p in kept] == ["3139477", "4241479"]
    assert _web.present(placements) is placements  # without embed the browser loads it: nothing downloads


def test_present_raises_any_other_download_error(headshot_images, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(500)))
    placements = place([0], [0], ["999"], league="nfl", kind="headshot")
    with pytest.raises(DownloadError):
        _web.present(placements, embed=True)


def _pygal_chart():
    chart = pytest.importorskip("pygal").XY(stroke=False)
    chart.add("games", [(10, -3), (20, -7)])  # pygal draws no plot area for a chart with no data
    return chart


@pytest.mark.parametrize(
    ("module", "make_target"),
    [
        ("bokeh", lambda: __import__("bokeh.plotting").plotting.figure(x_range=(0, 30), y_range=(-10, 0))),
        ("plotly", lambda: __import__("plotly.graph_objects").graph_objects.Figure()),
        (
            "altair",
            lambda: (
                __import__("altair")
                .Chart(__import__("altair").Data(values=[{"a": 0, "b": 0}]))
                .mark_point()
                .encode(x="a:Q", y="b:Q")
            ),
        ),  # fmt: skip
        ("folium", lambda: __import__("folium").Map(location=[0, 0], zoom_start=2)),
        ("pygal", _pygal_chart),
    ],
)
def test_web_adapters_skip_a_404_headshot_when_embedding(module, make_target, headshot_images, monkeypatch):
    adapter = pytest.importorskip(f"sdvplot.{module}")
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(404)))
    with pytest.warns(SdvplotWarning, match="whose headshot is missing"):
        out = adapter.add_headshots(make_target(), [10, 20], [-3, -7], ["3139477", "999"], league="nfl", embed=True)
    assert [m[0] for m in adapter._drawn_marks(out)] == ["3139477"]

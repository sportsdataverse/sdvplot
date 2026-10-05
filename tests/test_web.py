import base64

import pytest
import requests

from sdvplot import _cache, _web
from sdvplot._errors import OfflineError
from sdvplot._placement import Placement, place
from tests.conftest import FakeSession


def test_aspect_comes_from_the_manifest_or_the_headshot_constant(manifest):
    (logo,) = place([0], [0], ["LV"], league="nfl")
    (wordmark,) = place([0], [0], ["LV"], league="nfl", kind="wordmark")
    (headshot,) = place([0], [0], ["3139477"], league="nfl", kind="headshot", id_system="espn")
    assert (_web.aspect(logo), _web.aspect(wordmark)) == (1.0, 2.5)
    assert _web.aspect(headshot) == _web.HEADSHOT_ASPECT == pytest.approx(600 / 436)


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

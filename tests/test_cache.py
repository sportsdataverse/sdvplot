import hashlib
import os

import pytest
import requests

from sdvplot import _cache
from sdvplot._errors import OfflineError, SdvplotWarning
from tests.conftest import FakeResponse, FakeSession


def test_first_fetch_downloads_and_records_the_etag(cache, monkeypatch):
    s = FakeSession(FakeResponse(200, b"a,b\n1,2\n", {"ETag": '"v1"', "Last-Modified": "Wed, 01 Oct 2026"}))
    monkeypatch.setattr(_cache, "SESSION", s)
    path = _cache.fetch_cached("https://x/m.csv", "manifest/m.csv")
    assert path.read_bytes() == b"a,b\n1,2\n"
    assert _cache.read_meta("manifest/m.csv")["etag"] == '"v1"'


def test_within_the_ttl_nothing_is_requested(cache, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"x", {"ETag": '"v1"'})))
    _cache.fetch_cached("https://x/m.csv", "m.csv")
    monkeypatch.setattr(_cache, "SESSION", FakeSession())  # any request would IndexError
    assert _cache.fetch_cached("https://x/m.csv", "m.csv").read_bytes() == b"x"


def test_after_the_ttl_a_304_keeps_the_file_and_sends_if_none_match(cache, monkeypatch):
    monkeypatch.setenv("SDVPLOT_CACHE_TTL", "0")
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"x", {"ETag": '"v1"'})))
    _cache.fetch_cached("https://x/m.csv", "m.csv")
    s = FakeSession(FakeResponse(304))
    monkeypatch.setattr(_cache, "SESSION", s)
    assert _cache.fetch_cached("https://x/m.csv", "m.csv").read_bytes() == b"x"
    assert s.calls[0][1] == {"If-None-Match": '"v1"'}


def test_a_truncated_download_keeps_the_good_copy_and_writes_nothing_partial(cache, monkeypatch):  # Review Focus 4
    monkeypatch.setenv("SDVPLOT_CACHE_TTL", "0")
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"good", {"ETag": '"v1"'})))
    path = _cache.fetch_cached("https://x/m.csv", "m.csv")
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"ba", {"Content-Length": "999"})))
    with pytest.warns(SdvplotWarning, match="using the cached copy"):
        assert _cache.fetch_cached("https://x/m.csv", "m.csv").read_bytes() == b"good"
    assert not [p for p in os.listdir(path.parent) if p.endswith(".part")]


def test_a_dropped_connection_falls_back_to_the_cache(cache, monkeypatch):  # Review Focus 4
    monkeypatch.setenv("SDVPLOT_CACHE_TTL", "0")
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"good")))
    _cache.fetch_cached("https://x/m.csv", "m.csv")
    monkeypatch.setattr(_cache, "SESSION", FakeSession(requests.ConnectionError("reset")))
    with pytest.warns(SdvplotWarning):
        assert _cache.fetch_cached("https://x/m.csv", "m.csv").read_bytes() == b"good"


def test_a_validator_rejection_keeps_the_old_copy(cache, monkeypatch):
    monkeypatch.setenv("SDVPLOT_CACHE_TTL", "0")
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"good")))
    _cache.fetch_cached("https://x/m.csv", "m.csv")

    def reject(body):
        raise ValueError("missing columns")

    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"bad")))
    with pytest.warns(SdvplotWarning):
        assert _cache.fetch_cached("https://x/m.csv", "m.csv", validate=reject).read_bytes() == b"good"


def test_offline_with_no_cache_names_the_url(cache, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(requests.ConnectionError("down")))
    with pytest.raises(OfflineError, match="https://x/m.csv"):
        _cache.fetch_cached("https://x/m.csv", "m.csv")


def test_immutable_fetch_verifies_the_hash_and_never_refetches(cache, monkeypatch):
    body = b"\x89PNG fake"
    sha = hashlib.sha256(body).hexdigest()
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, body)))
    path = _cache.fetch_immutable("https://x/a.png", f"images/{sha[:2]}/{sha}.png", sha)
    monkeypatch.setattr(_cache, "SESSION", FakeSession())
    assert _cache.fetch_immutable("https://x/a.png", f"images/{sha[:2]}/{sha}.png", sha) == path


def test_immutable_fetch_rejects_a_hash_mismatch(cache, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"other")))
    with pytest.raises(OSError, match="does not match"):
        _cache.fetch_immutable("https://x/a.png", "images/ab/abc.png", "0" * 64)


def test_clear_cache_removes_everything(cache, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"x")))
    _cache.fetch_cached("https://x/m.csv", "m.csv")
    _cache.clear_cache()
    assert not cache.exists()

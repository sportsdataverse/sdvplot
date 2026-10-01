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
    _cache.fetch_cached("https://x/m.csv", "manifest/m.csv")
    monkeypatch.setattr(_cache, "SESSION", FakeSession())  # any request would IndexError
    assert _cache.fetch_cached("https://x/m.csv", "manifest/m.csv").read_bytes() == b"x"


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


def test_write_failure_with_existing_copy_uses_cached_and_warns(cache, monkeypatch):
    """R14a: After a good first fetch, os.replace failure keeps the old copy and warns."""
    monkeypatch.setenv("SDVPLOT_CACHE_TTL", "0")
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"good", {"ETag": '"v1"'})))
    path = _cache.fetch_cached("https://x/m.csv", "m.csv")
    assert path.read_bytes() == b"good"

    def replace_fails(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(os, "replace", replace_fails)
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"updated")))
    with pytest.warns(SdvplotWarning, match="using the cached copy"):
        result = _cache.fetch_cached("https://x/m.csv", "m.csv")
    assert result.read_bytes() == b"good"
    assert not [p for p in os.listdir(path.parent) if p.endswith(".part")]


def test_bad_sidecar_json_forces_refetch(cache, monkeypatch):
    """R14b: Unreadable or invalid JSON sidecar returns None, forcing a refetch."""
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"good")))
    path = _cache.fetch_cached("https://x/m.csv", "m.csv")

    meta_path = _cache._meta_path(path)
    meta_path.write_text("not json")

    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"new")))
    result = _cache.fetch_cached("https://x/m.csv", "m.csv")
    assert result.read_bytes() == b"new"


def test_file_mode_is_world_readable(cache, monkeypatch):
    """R15: Written files have mode 0o666 & ~umask, not 0600."""
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"data")))
    _cache.fetch_cached("https://x/m.csv", "manifest/m.csv")

    current_umask = os.umask(0)
    os.umask(current_umask)
    expected_mode = 0o666 & ~current_umask
    path = _cache.cache_dir() / "manifest" / "m.csv"
    actual_mode = os.stat(path).st_mode & 0o777
    assert actual_mode == expected_mode


def test_atomic_write_never_touches_the_process_umask(tmp_path, monkeypatch):
    """F4: os.umask(0) + restore races between threads and can leave the process umask at 0."""
    before = os.umask(0o022)
    os.umask(before)

    def no_umask(mask):
        raise AssertionError("atomic_write changed the process umask")

    monkeypatch.setattr(os, "umask", no_umask)
    _cache.atomic_write(tmp_path / "f", b"x")
    monkeypatch.undo()
    assert (tmp_path / "f").read_bytes() == b"x" and not list(tmp_path.glob("*.part"))
    after = os.umask(before)
    assert after == before


def test_repeated_offline_uses_cache_without_request(cache, monkeypatch):
    """R16: After a failing refresh, repeated calls skip the network and don't warn again."""
    import warnings

    monkeypatch.setenv("SDVPLOT_CACHE_TTL", "0")
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"good")))
    _cache.fetch_cached("https://x/m.csv", "manifest/m.csv")

    monkeypatch.setattr(_cache, "SESSION", FakeSession(requests.ConnectionError("reset")))
    with pytest.warns(SdvplotWarning, match="using the cached copy"):
        _cache.fetch_cached("https://x/m.csv", "manifest/m.csv")

    monkeypatch.setattr(_cache, "SESSION", FakeSession())
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = _cache.fetch_cached("https://x/m.csv", "manifest/m.csv")
    assert result.read_bytes() == b"good"
    assert len(w) == 0


def test_clear_cache_only_removes_known_subdirs(cache, monkeypatch):
    """R17: clear_cache removes only manifest/images/rasters/nflverse, preserving foreign files."""
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"x")))
    _cache.fetch_cached("https://x/m.csv", "manifest/m.csv")

    foreign = cache / "foreign.txt"
    foreign.write_text("keep me")

    _cache.clear_cache()
    assert not (cache / "manifest").exists()
    assert foreign.exists()


def test_immutable_404_raises_httperror_not_offline(cache, monkeypatch):
    """R18: A 404 on immutable is re-raised as HTTPError, not wrapped as OfflineError."""
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(404)))
    with pytest.raises(requests.HTTPError, match="HTTP 404"):
        _cache.fetch_immutable("https://x/missing.png", "images/ab/cd.png", "0" * 64)


def test_immutable_connection_error_gives_offline_guidance(cache, monkeypatch):
    """R18: ConnectionError on immutable becomes OfflineError with SDVPLOT_CACHE_DIR guidance."""
    monkeypatch.setattr(_cache, "SESSION", FakeSession(requests.ConnectionError("down")))
    with pytest.raises(OfflineError, match="SDVPLOT_CACHE_DIR"):
        _cache.fetch_immutable("https://x/a.png", "images/ab/cd.png", "0" * 64)


def test_fetch_cached_uses_timeout_5_60(cache, monkeypatch):
    """R16: fetch_cached must use timeout=(5, 60) to prevent network hangs."""
    s = FakeSession(FakeResponse(200, b"data"))
    monkeypatch.setattr(_cache, "SESSION", s)
    _cache.fetch_cached("https://x/m.csv", "manifest/m.csv")
    assert s.timeouts[0] == (5, 60)


def test_fetch_immutable_uses_timeout_5_60(cache, monkeypatch):
    """R16: fetch_immutable must use timeout=(5, 60) to prevent network hangs."""
    body = b"\x89PNG"
    sha = hashlib.sha256(body).hexdigest()
    s = FakeSession(FakeResponse(200, body))
    monkeypatch.setattr(_cache, "SESSION", s)
    _cache.fetch_immutable("https://x/a.png", f"images/{sha[:2]}/{sha}.png", sha)
    assert s.timeouts[0] == (5, 60)

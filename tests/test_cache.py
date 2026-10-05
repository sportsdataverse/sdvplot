import hashlib
import os
import shutil
import time
import types
from pathlib import Path

import pytest
import requests

from sdvplot import _cache, _manifest
from sdvplot._errors import DownloadError, IntegrityError, OfflineError, SdvplotWarning, UnsafeDownloadError
from tests.conftest import FIXTURE, FakeResponse, FakeSession, in_threads, slow_download


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


def test_a_fresh_file_is_served_from_memory(cache, monkeypatch):  # re-audit finding 1: no bookkeeping when warm
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"x")))
    path = _cache.fetch_cached("https://x/m.csv", "manifest/m.csv")

    def fail(*args, **kwargs):
        raise AssertionError("the path was resolved or the sidecar read again")

    monkeypatch.setattr(_cache, "cache_path", fail)
    monkeypatch.setattr(_cache, "read_meta", fail)
    assert _cache.fetch_cached("https://x/m.csv", "manifest/m.csv") == path


def test_the_memory_of_a_fresh_file_ends_with_its_ttl(cache, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"x", {"ETag": '"v1"'})))
    _cache.fetch_cached("https://x/m.csv", "m.csv")
    later = time.time() + (_cache.DEFAULT_TTL_DAYS + 1) * 86400
    monkeypatch.setattr(_cache, "time", types.SimpleNamespace(time=lambda: later, monotonic=time.monotonic))
    s = FakeSession(FakeResponse(304))
    monkeypatch.setattr(_cache, "SESSION", s)
    assert _cache.fetch_cached("https://x/m.csv", "m.csv").read_bytes() == b"x"
    assert s.calls[0][1] == {"If-None-Match": '"v1"'}  # revalidated, not served from memory


@pytest.mark.parametrize(
    "clear",
    [_cache.clear_cache, lambda: shutil.rmtree(_cache.cache_dir() / "manifest")],
    ids=["clear_cache", "another-process-cleared-it"],
)
def test_a_cleared_cache_is_downloaded_again_although_memory_had_it_fresh(cache, monkeypatch, clear):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"old")))
    _cache.fetch_cached("https://x/m.csv", "manifest/m.csv")
    clear()
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"new")))
    assert _cache.fetch_cached("https://x/m.csv", "manifest/m.csv").read_bytes() == b"new"


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
        if body != b"good":
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
    with pytest.raises(IntegrityError, match="does not match") as exc:  # M5: sdvplot's error, still an OSError
        _cache.fetch_immutable("https://x/a.png", "images/ab/abc.png", "0" * 64)
    assert isinstance(exc.value, OSError)
    assert not (cache / "images/ab/abc.png").exists()


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
    _cache._intact.clear()  # a new process: this one remembers the file is fresh and never reads the sidecar again

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


def test_atomic_write_never_touches_the_process_umask(cache, monkeypatch):
    tmp_path = cache
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


@pytest.mark.parametrize("status", [404, 503])
def test_an_immutable_http_error_is_a_download_error_not_a_requests_error(cache, monkeypatch, status):
    """M5: a 4xx or 5xx raises sdvplot's DownloadError (an OfflineError and an OSError), never requests.HTTPError."""
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(status)))
    with pytest.raises(DownloadError, match=f"HTTP {status}") as exc:
        _cache.fetch_immutable("https://x/missing.png", "images/ab/cd.png", "0" * 64)
    assert isinstance(exc.value, (OfflineError, OSError)) and not isinstance(exc.value, requests.RequestException)


def test_a_cached_fetch_http_error_with_no_copy_is_a_download_error(cache, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(404)))
    with pytest.raises(DownloadError, match="HTTP 404"):
        _cache.fetch_cached("https://x/m.csv", "m.csv")


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


def test_immutable_5xx_is_offline_not_httperror(cache, monkeypatch):
    """A server error is transient: OfflineError (a DownloadError) with the cache guidance (R18)."""
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(503)))
    with pytest.raises(OfflineError, match="HTTP 503"):
        _cache.fetch_immutable("https://x/a.png", "images/ab/cd.png", "0" * 64)


def test_a_304_whose_meta_write_fails_warns_and_uses_the_cached_copy(cache, monkeypatch):
    monkeypatch.setenv("SDVPLOT_CACHE_TTL", "0")
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"good", {"ETag": '"v1"'})))
    _cache.fetch_cached("https://x/m.csv", "m.csv")

    def replace_fails(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(os, "replace", replace_fails)
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(304)))
    with pytest.warns(SdvplotWarning, match="using the cached copy") as w:
        assert _cache.fetch_cached("https://x/m.csv", "m.csv").read_bytes() == b"good"
    assert len(w) == 1


def test_a_gzip_body_longer_than_its_content_length_is_not_truncated(cache, monkeypatch):
    """Content-Length is the compressed size when the server gzips; requests hands over the decoded body."""
    body = b"a,b\n" + b"1,2\n" * 100
    headers = {"Content-Length": "40", "Content-Encoding": "gzip"}
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, body, headers)))
    assert _cache.fetch_cached("https://x/m.csv", "m.csv").read_bytes() == body


def test_a_manifest_ext_that_climbs_out_of_the_cache_raises_and_writes_nothing(cache, monkeypatch, tmp_path):
    from sdvplot import _images
    from sdvplot._errors import UnsafeCachePathError

    body = b"payload"
    sha = hashlib.sha256(body).hexdigest()
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, body)))
    row = {"sha256": sha, "ext": "/../../../escaped.txt", "archive_url": "https://x/a"}
    with pytest.raises(UnsafeCachePathError):
        _images.mark_file(row)
    assert not list(tmp_path.rglob("escaped*")) and not (cache / "images").exists()


@pytest.mark.parametrize("sha", ["../" * 3 + "x", "A" * 64, "ab" * 31, "g" * 64])
def test_a_malformed_manifest_sha_is_refused(cache, monkeypatch, sha):
    from sdvplot import _images
    from sdvplot._errors import UnsafeCachePathError

    monkeypatch.setattr(_cache, "SESSION", FakeSession())
    with pytest.raises(UnsafeCachePathError):
        _images.mark_file({"sha256": sha, "ext": "png", "archive_url": "https://x/a"})


def test_cache_path_refuses_a_relpath_outside_the_cache(cache):
    from sdvplot._errors import UnsafeCachePathError

    with pytest.raises(UnsafeCachePathError):
        _cache.cache_path("../outside")
    with pytest.raises(UnsafeCachePathError):
        _cache.fetch_immutable("https://x/a", "images/../../outside.png", "0" * 64)
    assert _cache.cache_path("images/ab/x.png").is_relative_to(cache.resolve())


def test_cache_path_refuses_the_cache_root_itself(cache):
    from sdvplot._errors import UnsafeCachePathError

    for rel in ("", ".", "images/.."):
        with pytest.raises(UnsafeCachePathError):
            _cache.cache_path(rel)


def test_atomic_write_refuses_a_target_outside_the_cache(cache, tmp_path):
    from sdvplot._errors import UnsafeCachePathError

    with pytest.raises(UnsafeCachePathError):
        _cache.atomic_write(tmp_path / "outside.txt", b"x")
    assert not (tmp_path / "outside.txt").exists()


def test_a_bmp_manifest_row_is_accepted(cache, monkeypatch):
    from sdvplot import _images

    body = b"BM fake bitmap"
    sha = hashlib.sha256(body).hexdigest()
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, body)))
    path = _images.mark_file({"sha256": sha, "ext": "bmp", "archive_url": "https://x/a"})
    assert path.name == f"{sha}.bmp" and path.read_bytes() == body


# --- bounded downloads ---------------------------------------------------------------------------------------------


def test_a_body_over_the_byte_cap_is_refused_and_not_cached(cache, monkeypatch):
    body = b"x" * 100
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, body)))
    with pytest.raises(UnsafeDownloadError):
        _cache.fetch_immutable("https://x/a.png", "images/ab/a.png", hashlib.sha256(body).hexdigest(), max_bytes=10)
    assert not (cache / "images" / "ab" / "a.png").exists()


def test_a_declared_content_length_over_the_cap_is_refused_before_reading(cache, monkeypatch):
    resp = FakeResponse(200, b"x", {"Content-Length": "999999999"})
    monkeypatch.setattr(_cache, "SESSION", FakeSession(resp))
    with pytest.raises(UnsafeDownloadError, match="limit"):
        _cache.fetch_cached("https://x/m.csv", "m.csv", max_bytes=1000)
    assert not (cache / "m.csv").exists()


def test_a_drip_fed_download_stops_at_the_total_deadline(cache, monkeypatch):
    clock = iter([0.0] + [10_000.0] * 50)
    monkeypatch.setattr(_cache.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"x" * 200000)))
    with pytest.raises(UnsafeDownloadError, match="exceeded"):
        _cache.fetch_immutable("https://x/a.png", "images/ab/a.png", "0" * 64)


def test_a_redirect_off_https_is_refused_without_requesting_the_http_url(cache, monkeypatch):
    s = FakeSession(FakeResponse(302, b"", {"Location": "http://evil/m.csv"}), FakeResponse(200, b"pwned"))
    monkeypatch.setattr(_cache, "SESSION", s)
    with pytest.raises(UnsafeDownloadError):  # a refusal is not "offline": it says what was refused
        _cache.fetch_cached("https://x/m.csv", "m.csv")
    assert [c[0] for c in s.calls] == ["https://x/m.csv"]
    with pytest.raises(UnsafeDownloadError):
        _cache._download("http://x/m.csv", None, 10)


def test_an_https_redirect_is_followed(cache, monkeypatch):
    s = FakeSession(FakeResponse(301, b"", {"Location": "/moved.csv"}), FakeResponse(200, b"ok"))
    monkeypatch.setattr(_cache, "SESSION", s)
    assert _cache.fetch_cached("https://x/m.csv", "m.csv").read_bytes() == b"ok"
    assert [c[0] for c in s.calls] == ["https://x/m.csv", "https://x/moved.csv"]


# --- cache self-heal -----------------------------------------------------------------------------------------------


def test_a_corrupt_immutable_file_is_deleted_and_downloaded_again(cache, monkeypatch):
    body = b"real image bytes"
    sha = hashlib.sha256(body).hexdigest()
    rel = f"images/{sha[:2]}/{sha}.png"
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, body)))
    path = _cache.fetch_immutable("https://x/a.png", rel, sha)
    path.write_bytes(body[:5])  # a partial file left behind
    _cache._intact.clear()  # a new process
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, body)))
    assert _cache.fetch_immutable("https://x/a.png", rel, sha).read_bytes() == body


def test_a_cached_file_that_fails_its_validator_is_refetched(cache, monkeypatch):
    def parse(b):
        if not b.startswith(b"a,b"):
            raise ValueError("not a csv")

    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"a,b\n1,2\n", {"ETag": '"v1"'})))
    path = _cache.fetch_cached("https://x/m.csv", "m.csv", validate=parse)
    path.write_bytes(b"garbage")
    _cache._intact.clear()
    s = FakeSession(FakeResponse(200, b"a,b\n3,4\n"))
    monkeypatch.setattr(_cache, "SESSION", s)
    assert _cache.fetch_cached("https://x/m.csv", "m.csv", validate=parse).read_bytes() == b"a,b\n3,4\n"
    assert "If-None-Match" not in s.calls[0][1]  # the stale ETag went with the corrupt copy


def test_an_empty_cached_file_is_refetched(cache, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"data")))
    path = _cache.fetch_cached("https://x/m.csv", "m.csv")
    path.write_bytes(b"")
    _cache._intact.clear()
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"data")))
    assert _cache.fetch_cached("https://x/m.csv", "m.csv").read_bytes() == b"data"


# --- clear_cache ---------------------------------------------------------------------------------------------------


def test_clear_cache_also_clears_the_url_image_cache(cache, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"x")))
    _cache.fetch_cached("https://x/h.png", "urlimages/ab/abc")
    assert (cache / "urlimages" / "ab" / "abc").exists()
    _cache.clear_cache()
    assert not (cache / "urlimages").exists()


def test_clear_cache_never_deletes_a_folder_sdvplot_did_not_create(cache, monkeypatch):
    mine = cache / "images"
    mine.mkdir(parents=True)
    (mine / "keep.txt").write_text("my data")
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"x"), FakeResponse(200, b"x")))
    _cache.fetch_cached("https://x/m.csv", "manifest/m.csv")  # sdvplot creates (and marks) manifest/ only
    _cache.fetch_cached("https://x/i", "images/ab/i")  # writes into the user's images/, which stays unmarked
    with pytest.warns(SdvplotWarning):
        _cache.clear_cache()
    assert (mine / "keep.txt").exists()
    assert not (cache / "manifest").exists()


# --- real local servers --------------------------------------------------------------------------------------------


@pytest.fixture
def server():
    """A local http.server whose handler is set per test; yields (base_url, set_handler)."""
    import http.server
    import threading

    box = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            box["handler"](self)

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}", lambda fn: box.__setitem__("handler", fn)
    srv.shutdown()
    srv.server_close()


def test_a_drip_fed_body_hits_the_deadline_on_time(server, monkeypatch):
    import time

    base, handler = server

    def drip(h):
        h.send_response(200)
        h.send_header("Content-Length", "1000000")
        h.end_headers()
        try:
            for _ in range(1000):
                h.wfile.write(b"x")
                h.wfile.flush()
                time.sleep(0.2)
        except OSError:
            pass

    handler(drip)
    monkeypatch.setattr(_cache, "DEADLINE_SECONDS", 1.5)
    monkeypatch.setattr(_cache, "_check_https", lambda url: None)  # the local server speaks http
    start = time.monotonic()
    with pytest.raises(UnsafeDownloadError, match="exceeded"):
        _cache._download(base + "/", None, 10_000_000)
    assert time.monotonic() - start < 1.5 + 1


def test_a_real_redirect_hop_is_checked_before_it_is_requested(server, monkeypatch):
    base, handler = server
    hits = []

    def redirect(h):
        hits.append(h.path)
        h.send_response(302)
        h.send_header("Location", "/second")  # stands in for a hop that leaves https
        h.end_headers()

    handler(redirect)
    real = _cache._check_https  # the local server speaks http: accept only the first URL, refuse every later hop

    def only_start(url):
        if not url.endswith("/start"):
            real("http://refused")

    monkeypatch.setattr(_cache, "_check_https", only_start)
    with pytest.raises(UnsafeDownloadError):
        _cache._download(base + "/start", None, 100)
    assert hits == ["/start"]  # requests following the redirect itself would also have hit /second


# --- heal and clear_cache details ----------------------------------------------------------------------------------


def test_heal_does_not_delete_on_a_read_error(cache, monkeypatch):
    body = b"data"
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, body)))
    path = _cache.fetch_cached("https://x/m.csv", "m.csv")
    _cache._intact.clear()

    def boom(self):
        raise PermissionError("denied")

    monkeypatch.setattr(type(path), "read_bytes", boom)
    with pytest.raises(PermissionError):
        _cache.fetch_cached("https://x/m.csv", "m.csv")
    monkeypatch.undo()
    assert path.exists()


def test_heal_raises_when_the_corrupt_file_cannot_be_deleted(cache, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"data")))
    path = _cache.fetch_cached("https://x/m.csv", "m.csv")
    path.write_bytes(b"")
    _cache._intact.clear()

    def no_unlink(self, *a, **k):
        raise PermissionError("read-only")

    monkeypatch.setattr(type(path), "unlink", no_unlink)
    with pytest.raises(PermissionError):
        _cache.fetch_cached("https://x/m.csv", "m.csv")


def test_the_default_cache_directory_is_cleared_without_markers(tmp_path, monkeypatch):
    import platformdirs

    root = tmp_path / "default"
    monkeypatch.delenv("SDVPLOT_CACHE_DIR", raising=False)
    monkeypatch.setattr(platformdirs, "user_cache_dir", lambda *a, **k: str(root))
    for sub in _cache.CACHE_SUBDIRS:
        (root / sub).mkdir(parents=True)  # a cache from before the marker existed
        (root / sub / "f").write_text("x")
    _cache.clear_cache()
    assert not any((root / sub).exists() for sub in _cache.CACHE_SUBDIRS)


def test_the_skip_warning_names_the_path_and_says_to_delete_by_hand(cache):
    (cache / "images").mkdir(parents=True)
    with pytest.warns(SdvplotWarning, match=r"images.*by hand"):
        _cache.clear_cache()


# --- concurrent callers --------------------------------------------------------------------------------------------


def test_threads_fetching_one_uncached_image_download_it_once(cache, monkeypatch):
    body = b"\x89PNG fake"
    sha = hashlib.sha256(body).hexdigest()
    calls = []
    monkeypatch.setattr(_cache, "_download", slow_download({"https://x/a.png": body}, calls))
    paths = in_threads(lambda: _cache.fetch_immutable("https://x/a.png", f"images/{sha[:2]}/{sha}.png", sha))
    assert calls == ["https://x/a.png"]
    assert len(set(paths)) == 1 and paths[0].read_bytes() == body


def test_threads_loading_an_uncached_manifest_download_it_once(cache, monkeypatch):
    calls = []
    monkeypatch.setattr(_cache, "_download", slow_download({_manifest.MANIFEST_URL: FIXTURE.read_bytes()}, calls))
    _manifest._read.cache_clear()
    frames = in_threads(_manifest.load_manifest)  # a "could not refresh" warning would raise here
    assert calls == [_manifest.MANIFEST_URL]
    assert all(f.equals(frames[0]) for f in frames)


@pytest.mark.parametrize("theirs", [b"real image bytes", b"something else"])
def test_a_replace_refused_over_a_file_another_process_wrote(cache, monkeypatch, theirs):
    # Windows refuses os.replace onto a file another process holds open; a content-addressed file it wrote is ours too
    body = b"real image bytes"
    sha = hashlib.sha256(body).hexdigest()
    rel = f"images/{sha[:2]}/{sha}.png"
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, body)))

    def refused(src, dst):
        Path(dst).write_bytes(theirs)
        raise PermissionError(13, "Access is denied", str(src))

    monkeypatch.setattr(_cache.os, "replace", refused)
    if theirs == body:
        assert _cache.fetch_immutable("https://x/a.png", rel, sha).read_bytes() == body
    else:
        with pytest.raises(PermissionError):
            _cache.fetch_immutable("https://x/a.png", rel, sha)
    assert not list((cache / "images" / sha[:2]).glob("*.part"))  # the temp file is dropped either way

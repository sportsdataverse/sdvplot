"""The local cache: the logo manifest (refreshed by TTL + ETag) and logo images (content-addressed, immutable)."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import socket
import threading
import time
import weakref
from collections.abc import Callable, Hashable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlsplit

import platformdirs

from sdvplot._errors import (
    DownloadError,
    IntegrityError,
    OfflineError,
    UnsafeCachePathError,
    UnsafeDownloadError,
    warn,
)

if TYPE_CHECKING:
    import requests

CACHE_ENV = "SDVPLOT_CACHE_DIR"
TTL_ENV = "SDVPLOT_CACHE_TTL"
DEFAULT_TTL_DAYS = 7.0
CACHE_SUBDIRS = ("manifest", "images", "rasters", "nflverse", "urlimages")
MARKER = ".sdvplot-cache"  # written into a subdirectory sdvplot created; clear_cache only deletes marked ones
MAX_BYTES = 200 * 1024 * 1024  # default body cap, for the tables (the logo manifest is ~18 MB and grows)
IMAGE_MAX_BYTES = 25 * 1024 * 1024
DEADLINE_SECONDS = 120.0  # total wall-clock budget for one download (the (5, 60) timeout is per socket read)
MAX_REDIRECTS = 5
MEMORY_CACHES: list[Callable[[], object]] = []  # in-memory caches (decoded images) that clear_cache() empties
_warned: set[str] = set()
_intact: set[str] = set()  # cached files already checked this process
_fresh: dict[tuple[str, str], tuple[Path, float]] = {}  # (cache dir, relpath) -> (path, fetched_at): fetch_cached
_locks: weakref.WeakValueDictionary[Hashable, threading.Lock] = weakref.WeakValueDictionary()
_locks_guard = threading.Lock()


def key_lock(key: Hashable) -> threading.Lock:
    """The one lock for key while anyone holds it, so threads after the same file (or image) do the work once: the
    rest wait, then find it done. Windows also refuses to replace a file another thread holds open."""
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


def _session() -> Any:
    """The shared requests Session, created on first use so ``import sdvplot`` does not import requests (~0.1 s)."""
    session = globals().get("SESSION")
    if session is None:
        import requests

        session = globals()["SESSION"] = requests.Session()
        session.headers["User-Agent"] = "sdvplot (+https://github.com/sportsdataverse/sdvplot)"
        adapter = _watched_adapter()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
    return session


def _watched_adapter() -> Any:
    """A requests adapter whose pools tell the current thread's ``_Watchdog`` which connection they hand out and every
    socket they open, so it can shut a download down before there is a response (the TLS handshake, the headers)."""
    from requests.adapters import HTTPAdapter
    from urllib3 import HTTPConnectionPool, HTTPSConnectionPool
    from urllib3.connection import HTTPConnection, HTTPSConnection

    def watched(pool: Any, connection: Any) -> Any:
        class Connection(connection):
            def _new_conn(self) -> socket.socket:
                sock = super()._new_conn()
                if (dog := getattr(_watched, "dog", None)) is not None:
                    # a duplicate: wrapping the socket in TLS detaches the one urllib3 holds until the handshake ends
                    dog.socks.append(sock.dup())
                return sock

        class Pool(pool):
            ConnectionCls = Connection

            def _get_conn(self, timeout: float | None = None) -> Any:
                conn = super()._get_conn(timeout)
                if (dog := getattr(_watched, "dog", None)) is not None:
                    dog.conn = conn
                return conn

        return Pool

    pools = {
        "http": watched(HTTPConnectionPool, HTTPConnection),
        "https": watched(HTTPSConnectionPool, HTTPSConnection),
    }

    # ponytail: a proxy's pools (proxy_manager_for) are not watched; through a proxy the deadline covers the body only
    class Adapter(HTTPAdapter):
        def init_poolmanager(self, *args: Any, **kwargs: Any) -> None:
            super().init_poolmanager(*args, **kwargs)
            self.poolmanager.pool_classes_by_scheme = pools

    return Adapter()


def __getattr__(name: str) -> Any:
    if name == "SESSION":  # `_cache.SESSION` stays reachable (and patchable) although it is created lazily
        return _session()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def cache_dir() -> Path:
    return Path(os.environ.get(CACHE_ENV) or platformdirs.user_cache_dir("sdvplot"))


def cache_path(relpath: str) -> Path:
    """cache_dir() / relpath, refusing any relpath whose resolved location is outside the cache directory."""
    path = (cache_dir().resolve() / relpath).resolve()
    _check_contained(path, relpath)
    return path


def _check_contained(path: Path, label: object) -> None:
    root = cache_dir().resolve()
    if path == root or not path.is_relative_to(root):
        raise UnsafeCachePathError(f"cache path {label!r} is not inside the cache directory")


def ttl_seconds() -> float:
    raw = os.environ.get(TTL_ENV)
    return (float(raw) if raw else DEFAULT_TTL_DAYS) * 86400


def _meta_path(path: Path) -> Path:
    return path.with_name(path.name + ".meta.json")


def read_meta(relpath: str) -> dict | None:
    meta = _meta_path(cache_path(relpath))
    if not meta.exists():
        return None
    try:
        return json.loads(meta.read_text())
    except (OSError, ValueError):
        return None


def _mark_new_subdir(path: Path) -> None:
    """When this write creates one of the cache subdirectories, mark it as ours (an existing folder is never marked)."""
    try:
        root = cache_dir().resolve()
        sub = path.resolve().relative_to(root).parts[0]
    except (ValueError, IndexError):
        return
    subdir = root / sub
    if sub in CACHE_SUBDIRS and not subdir.exists():
        subdir.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(OSError):
            (subdir / MARKER).write_bytes(b"")


def atomic_write(path: Path, data: bytes) -> None:
    """Write to a temp file beside the target, then rename: a reader never sees a partial file."""
    _check_contained(path.resolve(), str(path))
    _mark_new_subdir(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.urandom(8).hex()}.part")
    # mode 0o666 with the kernel applying the umask: world-readable like any file, and the process umask is never
    # read or changed (toggling it races between threads)
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o666)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def _warn_once(key: str, message: str) -> None:
    if key not in _warned:
        _warned.add(key)
        warn(message)


def _offline_message(url: str) -> str:
    return (
        f"could not download {url} and there is no cached copy; connect once, or point {CACHE_ENV} "
        "at a directory that has one"
    )


def _check_https(url: str) -> None:
    if urlsplit(url).scheme != "https":
        raise UnsafeDownloadError(f"refusing to download {url}: not https")


# A plain https URL: a host, then only RFC 3986 characters, minus ' (RFC 3986 allows it, but it ends a single-quoted
# HTML attribute). No quote, <, >, whitespace, backslash or control character, so a URL from the logo manifest or
# nflverse's player table cannot break out of the HTML attribute or <script> block a web adapter writes it into.
# A pattern both re and polars (Rust regex) read the same way.
SAFE_URL = r"https://[A-Za-z0-9.\-]+(?::[0-9]+)?(?:[/?#][A-Za-z0-9\-._~:/?#\[\]@!$&()*+,;=%]*)?"


def safe_url(url: object) -> bool:
    """True when ``url`` is a plain https URL (``SAFE_URL``)."""
    return isinstance(url, str) and re.fullmatch(SAFE_URL, url) is not None


def _pieces(r: requests.Response) -> Iterator[bytes]:
    """Body pieces as they arrive, so the cap and the deadline are checked on every receive (not per full chunk: a
    server dripping a byte at a time would otherwise stall a 64 KiB read for hours). urllib3 >= 2.6 (a dependency floor)
    returns whatever has arrived, and decompresses at most the amount asked for."""
    while chunk := r.raw.read1(65536, decode_content=True):
        yield chunk


_watched = threading.local()  # .dog: the _Watchdog of the download running on this thread


class _Watchdog:
    """Shuts a download's sockets down at its deadline. The (5, 60) timeout bounds each socket read, not the call: a
    server sending a byte every 59 s held the TLS handshake or the headers open indefinitely, and the body loop's own
    deadline check only runs between reads. One timer covers the handshake, the headers and the body of every hop."""

    def __init__(self, seconds: float) -> None:
        self.conn: Any = None  # the pooled connection in use (a reused one opens no socket)
        self.socks: list[socket.socket] = []  # duplicates of the sockets this download opened
        self.response: Any = None
        self.expired = self.stopped = False
        self._start(seconds)

    def _start(self, seconds: float) -> None:
        self._timer = threading.Timer(seconds, self._fire)
        self._timer.daemon = True
        self._timer.start()

    def _fire(self) -> None:
        if self.stopped:
            return
        self.expired = True
        # each attempt may meet a socket already closed, or none yet: that is fine, the next tick tries again
        for sock in (*self.socks, getattr(self.conn, "sock", None)):
            with contextlib.suppress(Exception):
                if sock is not None:  # the plain socket's method: it wakes a read blocked inside TLS too
                    socket.socket.shutdown(sock, socket.SHUT_RDWR)
        with contextlib.suppress(Exception):
            self.response.raw.shutdown()  # urllib3's: the response owns a socket the connection let go of
        self._start(0.1)  # until stop(): a reconnect or the next hop is shut down too

    def stop(self) -> None:
        self.stopped = True
        self._timer.cancel()
        for sock in self.socks:
            sock.close()


def _download(url: str, headers: dict | None, max_bytes: int) -> tuple[requests.Response, bytes]:
    """GET url with a byte cap, a total deadline and https-only redirects (followed by hand, so a hop to http is never
    requested). Raises UnsafeDownloadError when refused or past the deadline; requests errors propagate."""
    deadline = time.monotonic() + DEADLINE_SECONDS
    dog = _watched.dog = _Watchdog(DEADLINE_SECONDS)
    try:
        for _ in range(MAX_REDIRECTS + 1):
            _check_https(url)
            left = deadline - time.monotonic()
            if left <= 0:
                raise UnsafeDownloadError(f"{url}: download exceeded {DEADLINE_SECONDS:.0f} s")
            # no read waits past the deadline either: on Windows a shut socket does not wake a read already waiting
            timeout = (min(5, left), min(60, left))
            r = dog.response = _session().get(url, headers=headers, timeout=timeout, stream=True, allow_redirects=False)
            try:
                if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("Location"):
                    url = urljoin(url, r.headers["Location"])
                    continue
                declared = r.headers.get("Content-Length")
                if declared is not None and declared.isdigit() and int(declared) > max_bytes:
                    raise UnsafeDownloadError(f"{url}: {declared} bytes exceeds the {max_bytes} byte limit")
                if r.status_code >= 400 or r.status_code == 304:
                    return r, b""
                chunks, size = [], 0
                for chunk in _pieces(r):
                    size += len(chunk)
                    if size > max_bytes:
                        raise UnsafeDownloadError(f"{url}: body exceeds the {max_bytes} byte limit")
                    if time.monotonic() > deadline:
                        raise UnsafeDownloadError(f"{url}: download exceeded {DEADLINE_SECONDS:.0f} s")
                    chunks.append(chunk)
                if dog.expired:  # a shut socket can end a body early without an error
                    raise UnsafeDownloadError(f"{url}: download exceeded {DEADLINE_SECONDS:.0f} s")
                return r, b"".join(chunks)
            finally:
                r.close()
        raise UnsafeDownloadError(f"{url}: more than {MAX_REDIRECTS} redirects")
    except Exception as e:
        # a read that timed out at the deadline can raise before the watchdog fires: both are the deadline
        if isinstance(e, UnsafeDownloadError) or not (dog.expired or time.monotonic() >= deadline):
            raise
        raise UnsafeDownloadError(f"{url}: download exceeded {DEADLINE_SECONDS:.0f} s") from e
    finally:
        dog.stop()
        _watched.dog = None


def _heal(path: Path, validate: Callable[[bytes], object] | None, sha256: str | None = None) -> bool:
    """True when the cached file is intact (checked once per process); a corrupt or empty one is deleted."""
    key = str(path)
    if key in _intact:
        return True
    data = path.read_bytes()  # a read error (permissions, a transient fault) is not corruption: it propagates
    try:
        if not data:
            raise ValueError("empty file")
        if sha256 is not None and hashlib.sha256(data).hexdigest() != sha256:
            raise ValueError("sha256 mismatch")
        if validate is not None:
            validate(data)
    except Exception:  # a failed integrity check (sha, parse, empty): the cached copy cannot be trusted
        path.unlink()  # if this fails the error propagates: never hand back the corrupt file
        _meta_path(path).unlink(missing_ok=True)
        return False
    _intact.add(key)
    return True


def fetch_cached(
    url: str, relpath: str, *, validate: Callable[[bytes], object] | None = None, max_bytes: int = MAX_BYTES
) -> Path:
    """``_fetch_cached``, with a file this process found fresh remembered until its TTL runs out: a warm call is a dict
    lookup and one stat, not two path resolutions and a JSON read. It is trusted only while ``_intact`` vouches for the
    file (``clear_cache()`` empties it) and the file still exists (another process may have cleared the cache). Threads
    after the same file share one refresh: the others wait, then find it fresh."""
    key = (str(cache_dir()), relpath)
    hit = _fresh.get(key)
    if hit is not None and str(hit[0]) in _intact and hit[0].exists() and time.time() - hit[1] < ttl_seconds():
        return hit[0]
    with key_lock(str(cache_path(relpath))):
        path = _fetch_cached(url, relpath, validate=validate, max_bytes=max_bytes)
    fetched_at = (read_meta(relpath) or {}).get("fetched_at", 0)
    if str(path) in _intact and time.time() - fetched_at < ttl_seconds():  # not a stale copy kept after a failure
        _fresh[key] = (path, fetched_at)
    return path


def _fetch_cached(
    url: str, relpath: str, *, validate: Callable[[bytes], object] | None = None, max_bytes: int = MAX_BYTES
) -> Path:
    """A cached copy of url, refreshed when older than the TTL (a 304 just renews it). On any failure (network,
    truncation, a validate() rejection) the previous copy is kept and used with one warning."""
    path = cache_path(relpath)
    if path.exists() and not _heal(path, validate):
        pass  # a corrupt cached file was deleted: fall through to a fresh download
    meta = read_meta(relpath) or {}
    if path.exists() and time.time() - meta.get("fetched_at", 0) < ttl_seconds():
        return path
    if url in _warned and path.exists():
        return path
    headers = {"If-None-Match": meta["etag"]} if path.exists() and meta.get("etag") else {}
    import requests  # lazy: only a download needs it

    try:
        r, body = _download(url, headers, max_bytes)
        if r.status_code == 304 and path.exists():
            # a failed meta write lands in the except below, which keeps the cached copy with one warning
            atomic_write(_meta_path(path), json.dumps({**meta, "fetched_at": time.time()}).encode())
            return path
        r.raise_for_status()
        declared = r.headers.get("Content-Length")
        if (
            declared is not None
            and r.headers.get("Content-Encoding") in (None, "identity")
            and int(declared) != len(body)
        ):
            raise OSError(f"truncated download: {len(body)} of {declared} bytes")
        if validate is not None:
            try:
                validate(body)
            except Exception as e:  # any validator error (a polars parse error too) rejects the body: never cache it
                raise ValueError(f"{type(e).__name__}: {e}") from e
    except (requests.RequestException, OSError, ValueError) as e:
        if path.exists():
            _warn_once(url, f"could not refresh {url} ({e}); using the cached copy")
            return path
        if isinstance(e, UnsafeDownloadError):
            raise
        error = DownloadError if isinstance(e, requests.HTTPError) else OfflineError
        raise error(f"{_offline_message(url)} ({e})") from e
    try:
        atomic_write(path, body)
        new_meta = {
            "etag": r.headers.get("ETag"),
            "last_modified": r.headers.get("Last-Modified"),
            "fetched_at": time.time(),
        }
        atomic_write(_meta_path(path), json.dumps(new_meta).encode())
        _intact.add(str(path))
    except (OSError, ValueError) as e:
        if path.exists():
            _warn_once(url, f"could not refresh {url} ({e}); using the cached copy")
            return path
        raise OfflineError(f"{_offline_message(url)} ({e})") from e
    return path


def fetch_immutable(url: str, relpath: str, sha256: str, *, max_bytes: int = IMAGE_MAX_BYTES) -> Path:
    """A content-addressed file: downloaded once, checked against its sha256, never refreshed. A cached copy that no
    longer matches its sha256 (corrupt, truncated) is deleted and downloaded again. Threads after the same file share
    one download."""
    path = cache_path(relpath)
    with key_lock(str(path)):
        if path.exists() and _heal(path, None, sha256):
            return path
        import requests  # lazy: only a download needs it

        try:
            r, body = _download(url, None, max_bytes)
            r.raise_for_status()
        except requests.HTTPError as e:  # a 4xx or 5xx: sdvplot's error, still an OSError as requests' was
            raise DownloadError(f"{_offline_message(url)} ({e})") from e
        except requests.RequestException as e:
            raise OfflineError(f"{_offline_message(url)} ({e})") from e
        digest = hashlib.sha256(body).hexdigest()
        if digest != sha256:
            raise IntegrityError(f"{url}: sha256 {digest} does not match the manifest ({sha256}); not cached")
        try:
            atomic_write(path, body)
        except PermissionError:
            # Windows refuses to replace a file another process holds open; when that process wrote the same content
            # (it is content-addressed), the file is already what this call wanted. atomic_write dropped the .part.
            if not (path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == sha256):
                raise
        _intact.add(str(path))
        return path


def clear_cache() -> None:
    """Delete everything sdvplot has cached (manifest, images, rasters, nflverse, URL images such as headshots).

    The next call that needs a mark downloads it again. The cache directory is ``SDVPLOT_CACHE_DIR`` when set. In the
    default cache directory every subdirectory above is removed. In a directory you chose with ``SDVPLOT_CACHE_DIR``
    only subdirectories sdvplot created (they hold a ``.sdvplot-cache`` marker) are removed; a folder of your own with
    the same name is left alone with a warning that names it. A subdirectory that is a symlink is unlinked in the
    default directory (what it points to is untouched) and left alone with a warning in one you chose.

    Returns:
        None: Nothing; the cache subdirectories are removed.

    Example:
        ::

            import sdvplot

            sdvplot.clear_cache()   # the next logo_url() / logo_image() re-downloads

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    root = cache_dir()
    owned = not os.environ.get(CACHE_ENV)  # the default directory is sdvplot's own; a custom one may hold other things
    try:
        for subdir in CACHE_SUBDIRS:
            path = root / subdir
            if path.is_symlink():  # sdvplot never makes one, and cache_path() refuses one that leads out of the cache
                if owned:
                    path.unlink()  # the link only, never what it points to
                else:
                    warn(f"{path} is a symlink sdvplot did not create, so it was left in place; delete it by hand")
            elif path.exists() and (owned or (path / MARKER).exists()):
                shutil.rmtree(path)
            elif path.exists():
                warn(f"{path} was not created by sdvplot, so it was left in place; delete it by hand if it is a cache")
    finally:  # a failed removal still empties the in-memory caches
        _warned.clear()
        _intact.clear()
        for clear in MEMORY_CACHES:
            clear()

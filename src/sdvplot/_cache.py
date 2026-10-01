"""The local cache: the logo manifest (refreshed by TTL + ETag) and logo images (content-addressed, immutable)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
import warnings
from collections.abc import Callable
from pathlib import Path

import platformdirs
import requests

from sdvplot._errors import OfflineError, SdvplotWarning

CACHE_ENV = "SDVPLOT_CACHE_DIR"
TTL_ENV = "SDVPLOT_CACHE_TTL"
DEFAULT_TTL_DAYS = 7.0
CACHE_SUBDIRS = ("manifest", "images", "rasters", "nflverse")
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "sdvplot (+https://github.com/sportsdataverse/sdvplot)"
_warned: set[str] = set()


def cache_dir() -> Path:
    return Path(os.environ.get(CACHE_ENV) or platformdirs.user_cache_dir("sdvplot"))


def ttl_seconds() -> float:
    raw = os.environ.get(TTL_ENV)
    return (float(raw) if raw else DEFAULT_TTL_DAYS) * 86400


def _meta_path(path: Path) -> Path:
    return path.with_name(path.name + ".meta.json")


def read_meta(relpath: str) -> dict | None:
    meta = _meta_path(cache_dir() / relpath)
    if not meta.exists():
        return None
    try:
        return json.loads(meta.read_text())
    except (OSError, ValueError):
        return None


def atomic_write(path: Path, data: bytes) -> None:
    """Write to a temp file beside the target, then rename: a reader never sees a partial file."""
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
        warnings.warn(message, SdvplotWarning, stacklevel=4)


def _offline_message(url: str) -> str:
    return (
        f"could not download {url} and there is no cached copy; connect once, or point {CACHE_ENV} "
        "at a directory that has one"
    )


def fetch_cached(url: str, relpath: str, *, validate: Callable[[bytes], object] | None = None) -> Path:
    """A cached copy of url, refreshed when older than the TTL (a 304 just renews it). On any failure (network,
    truncation, a validate() rejection) the previous copy is kept and used with one warning."""
    path = cache_dir() / relpath
    meta = read_meta(relpath) or {}
    if path.exists() and time.time() - meta.get("fetched_at", 0) < ttl_seconds():
        return path
    if url in _warned and path.exists():
        return path
    headers = {"If-None-Match": meta["etag"]} if path.exists() and meta.get("etag") else {}
    try:
        r = SESSION.get(url, headers=headers, timeout=(5, 60))
        if r.status_code == 304 and path.exists():
            try:
                atomic_write(_meta_path(path), json.dumps({**meta, "fetched_at": time.time()}).encode())
            except (OSError, ValueError) as e:
                if path.exists():
                    _warn_once(url, f"could not refresh {url} ({e}); using the cached copy")
                    return path
                raise
            return path
        r.raise_for_status()
        body = r.content
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
        raise OfflineError(f"{_offline_message(url)} ({e})") from e
    try:
        atomic_write(path, body)
        new_meta = {
            "etag": r.headers.get("ETag"),
            "last_modified": r.headers.get("Last-Modified"),
            "fetched_at": time.time(),
        }
        atomic_write(_meta_path(path), json.dumps(new_meta).encode())
    except (OSError, ValueError) as e:
        if path.exists():
            _warn_once(url, f"could not refresh {url} ({e}); using the cached copy")
            return path
        raise OfflineError(f"{_offline_message(url)} ({e})") from e
    return path


def fetch_immutable(url: str, relpath: str, sha256: str) -> Path:
    """A content-addressed file: downloaded once, checked against its sha256, never refreshed."""
    path = cache_dir() / relpath
    if path.exists():
        return path
    try:
        r = SESSION.get(url, timeout=(5, 60))
        r.raise_for_status()
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code < 500:
            raise
        raise OfflineError(f"{_offline_message(url)} ({e})") from e
    except requests.RequestException as e:
        raise OfflineError(f"{_offline_message(url)} ({e})") from e
    digest = hashlib.sha256(r.content).hexdigest()
    if digest != sha256:
        raise OSError(f"{url}: sha256 {digest} does not match the manifest ({sha256}); not cached")
    atomic_write(path, r.content)
    return path


def clear_cache() -> None:
    """Delete everything sdvplot has cached (manifest, images, rasters, nflverse).

    The next call that needs a mark downloads it again. The cache directory is ``SDVPLOT_CACHE_DIR`` when set.

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
    for subdir in CACHE_SUBDIRS:
        path = root / subdir
        if path.exists():
            shutil.rmtree(path)
    _warned.clear()

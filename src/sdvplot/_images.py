"""Decoded logo images for matplotlib-style libraries (web libraries use logo_url() instead)."""

from __future__ import annotations

import collections
import contextlib
import hashlib
import io
import re
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit
from urllib.request import url2pathname

from sdvplot._cache import MEMORY_CACHES, atomic_write, cache_path, fetch_cached, fetch_immutable
from sdvplot._errors import OptionalDependencyError, UnsafeCachePathError, warn
from sdvplot._marks import _check_mark_type, _check_variant, select_mark
from sdvplot._resolve import one_team, resolve
from sdvplot._types import MarkType

if TYPE_CHECKING:
    from PIL import Image

DEFAULT_SVG_SIZE = 512
_SHA256 = re.compile(r"[0-9a-f]{64}")
URL_IMAGE_MAX_BYTES = 10 * 1024 * 1024
IMAGE_EXTS = frozenset({"png", "jpg", "jpeg", "svg", "webp", "gif", "bmp"})


def _rasterize(path: Path, sha: str, size: int, ext: str) -> Image.Image:
    from PIL import Image

    try:
        import importlib.metadata

        import resvg_py
    except ImportError as e:
        raise OptionalDependencyError("SVG logos need the svg extra: pip install sdvplot[svg]") from e

    try:
        version = importlib.metadata.version("resvg-py")
    except importlib.metadata.PackageNotFoundError as e:
        raise OptionalDependencyError("SVG logos need the svg extra: pip install sdvplot[svg]") from e
    out = cache_path(f"rasters/{sha}_{size}_v{version}.png")

    # Try to open cached raster; if corrupt, treat as cache miss
    if out.exists():
        try:
            img = Image.open(out)
            img.load()
            return img
        except (OSError, Image.UnidentifiedImageError):
            # Cache miss due to corruption; delete (best effort: the cache may be read-only) and re-render
            with contextlib.suppress(OSError):
                out.unlink()

    # Render SVG
    try:
        svg = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as e:
        raise ValueError(f"SVG {sha}.{ext}: {e}") from e

    try:
        png = bytes(resvg_py.svg_to_bytes(svg_string=svg, width=size))
        probe = Image.open(io.BytesIO(png))
        if probe.height > size:  # portrait: fit the longest side instead
            png = bytes(resvg_py.svg_to_bytes(svg_string=svg, height=size))
    except ValueError as e:
        raise ValueError(f"SVG {sha}.{ext}: {e}") from e

    with contextlib.suppress(OSError):  # a read-only cache still gets the image, just not cached
        atomic_write(out, png)
    img = Image.open(io.BytesIO(png))
    img.load()
    return img


def logo_image(
    team: Any,
    league: str,
    *,
    season: Any = None,
    variant: str = "default",
    mark_type: MarkType = "logo",
    size: int | None = None,
) -> Image.Image | None:
    """The team's mark as a PIL image (downloaded once, then cached).

    Args:
        team: One team identifier (abbreviation, name, ESPN id, ...).
        league: The SDV league key, e.g. "nfl".
        season: A season year; None picks the current mark.
        variant: "default", "dark", or a named variant from ``marks()``.
        mark_type: "logo" or "wordmark".
        size: The longest side in pixels. Rasters are only scaled down; SVGs are rasterized at it (default 512).

    Returns:
        PIL.Image.Image | None: The image, or None when the team does not resolve or has no mark.

    Raises:
        TypeError: If ``team`` is not a single value.
        OptionalDependencyError: If the mark is an SVG and the ``svg`` extra is not installed.
        OfflineError: If the download fails and no cached copy exists.
        UnsafeDownloadError: (an OSError) If the download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If the manifest's sha256 or extension for the mark would put the file
            outside the cache directory.
        requests.HTTPError: If the CDN refuses the file (a 4xx response).
        OSError: If the download does not match the manifest's sha256, or is not an image PIL can decode
            (``PIL.UnidentifiedImageError`` subclasses OSError).
        InputError: (a ValueError) If ``league`` is unknown, ``mark_type`` is not "logo"/"wordmark", ``variant`` is a
            name no mark in the archive has, or ``season`` is outside the seasons sdvplot knows for the league.
        ValueError: If an SVG cannot be parsed.

    Example:
        ::

            import sdvplot

            img = sdvplot.logo_image("KC", "nfl", size=64)
            img.size   # (64, 64)

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    _check_mark_type(mark_type)
    _check_variant(variant, league)
    team_id = resolve(one_team(team, "logo_image"), league, season=season)
    if team_id is None:
        return None
    row = select_mark(team_id, league, season, variant, mark_type)
    if row is None:
        warn(f"no {mark_type} archived for {team!r} ({league})")
        return None
    return load_mark_image(row, size)


def mark_file(row: dict[str, Any]) -> Path:
    """The cached file of one manifest row's image, downloaded once and checked against its sha256."""
    sha, ext = str(row["sha256"]), str(row["ext"])
    if not _SHA256.fullmatch(sha) or ext not in IMAGE_EXTS:
        raise UnsafeCachePathError(f"manifest row has an invalid sha256 or ext ({sha!r}, {ext!r}); not fetched")
    return fetch_immutable(str(row["archive_url"]), f"images/{sha[:2]}/{sha}.{ext}", sha)


def _decode_mark(sha: str, ext: str, url: str, size: int | None) -> Image.Image:
    """The decoded image of one mark (SVGs rasterized, rasters scaled down to ``size``)."""
    from PIL import Image

    path = mark_file({"sha256": sha, "ext": ext, "archive_url": url})
    if ext == "svg":
        return _rasterize(path, sha, size or DEFAULT_SVG_SIZE, ext)
    img: Image.Image = Image.open(path)
    img.load()
    if size is not None:
        img = img.copy()
        img.thumbnail((size, size))
    return img


# Decoded images kept in memory, least recently used first, bounded by pixel bytes rather than entry count: the archive
# holds thousands of 4096 x 4096 rasters (67 MB each decoded), so a count bound alone could pin gigabytes.
DECODED_BUDGET = 256 * 1024 * 1024
_decoded: collections.OrderedDict[tuple[str, str, str, int | None], Image.Image] = collections.OrderedDict()
_decoded_bytes = 0
_decoded_lock = threading.Lock()


def _nbytes(img: Image.Image) -> int:
    return img.width * img.height * len(img.getbands())


def _decoded_mark(sha: str, ext: str, url: str, size: int | None) -> Image.Image:
    """The decoded image of one mark, kept per (sha256, ext, url, size) so repeated calls decode a team's logo once.
    An image over a quarter of the budget is decoded per call instead of pushing everything else out. Callers must go
    through ``load_mark_image``, which hands out a copy."""
    global _decoded_bytes
    key = (sha, ext, url, size)
    with _decoded_lock:
        if (hit := _decoded.get(key)) is not None:
            _decoded.move_to_end(key)
            return hit
    img = _decode_mark(*key)
    nbytes = _nbytes(img)
    if nbytes <= DECODED_BUDGET // 4:
        with _decoded_lock:
            if key not in _decoded:
                _decoded[key] = img
                _decoded_bytes += nbytes
                while _decoded_bytes > DECODED_BUDGET:
                    _, old = _decoded.popitem(last=False)
                    _decoded_bytes -= _nbytes(old)
    return img


def _clear_decoded() -> None:
    global _decoded_bytes
    with _decoded_lock:
        _decoded.clear()
        _decoded_bytes = 0


MEMORY_CACHES.append(_clear_decoded)  # clear_cache() also drops the decoded images held in memory


def load_mark_image(row: dict[str, Any], size: int | None = None) -> Image.Image:
    """The image for one manifest row (as ``select_mark`` returns it): fetched by sha256 once, SVGs rasterized.

    ``size`` is the longest side in pixels: rasters are only scaled down; SVGs are rasterized at it (default 512).
    Decoded images are kept in memory (up to ``DECODED_BUDGET`` bytes of pixels, least recently used dropped first);
    the caller gets its own copy, free to modify, with the source ``format`` kept.
    """
    img = _decoded_mark(str(row["sha256"]), str(row["ext"]), str(row["archive_url"]), size)
    out = img.copy()
    out.format = img.format  # Image.copy() drops it; callers may read img.format / Image.MIME
    return out


def _check_image(body: bytes) -> None:
    from PIL import Image

    Image.open(io.BytesIO(body)).verify()


def url_file(url: str) -> Path:
    """The cached file of an image that is not content-addressed (a headshot): keyed by sha256(url), refreshed after
    SDVPLOT_CACHE_TTL, non-images rejected."""
    key = hashlib.sha256(url.encode()).hexdigest()
    return fetch_cached(url, f"urlimages/{key[:2]}/{key}", validate=_check_image, max_bytes=URL_IMAGE_MAX_BYTES)


def load_url_image(url: str) -> Image.Image:
    """An image that is not content-addressed (a headshot): cached by sha256(url), refreshed after SDVPLOT_CACHE_TTL."""
    from PIL import Image

    path = url_file(url)
    img: Image.Image = Image.open(path)
    img.load()
    return img


def load_path_image(path: str) -> Image.Image:
    """Any image by http(s) URL (cached like a headshot), file:// URI or local path; raises OSError, ValueError or
    OfflineError."""
    scheme = urlsplit(path).scheme.lower()  # URL schemes are case-insensitive; a Windows drive letter is no scheme
    if scheme in ("http", "https"):
        return load_url_image(path)
    if scheme == "file":  # what pathlib.Path.as_uri() writes
        path = url2pathname(urlsplit(path).path)
    from PIL import Image

    img: Image.Image = Image.open(path)
    img.load()
    return img

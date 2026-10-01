"""Decoded logo images for matplotlib-style libraries (web libraries use logo_url() instead)."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from PIL import Image

from sdvplot._cache import atomic_write, cache_dir, fetch_immutable
from sdvplot._errors import OptionalDependencyError
from sdvplot._marks import select_mark

DEFAULT_SVG_SIZE = 512


def _rasterize(path: Path, sha: str, size: int, ext: str) -> Image.Image:
    try:
        import importlib.metadata

        import resvg_py
    except ImportError as e:
        raise OptionalDependencyError("SVG logos need the svg extra: pip install sdvplot[svg]") from e

    try:
        version = importlib.metadata.version("resvg-py")
    except importlib.metadata.PackageNotFoundError as e:
        raise OptionalDependencyError("SVG logos need the svg extra: pip install sdvplot[svg]") from e
    out = cache_dir() / "rasters" / f"{sha}_{size}_v{version}.png"

    # Try to open cached raster; if corrupt, treat as cache miss
    if out.exists():
        try:
            img = Image.open(out)
            img.load()
            return img
        except (OSError, Image.UnidentifiedImageError):
            # Cache miss due to corruption; delete and re-render
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

    atomic_write(out, png)
    img = Image.open(out)
    img.load()
    return img


def logo_image(
    team: Any,
    league: str,
    season: Any = None,
    variant: str = "default",
    mark_type: str = "logo",
    size: int | None = None,
) -> Image.Image | None:
    """The team's mark as a PIL image (cached). size is the longest side in pixels: rasters are only scaled down,
    SVGs are rasterized at it (default 512; needs the svg extra)."""
    row = select_mark(team, league, season, variant, mark_type)
    if row is None:
        return None
    sha, ext = str(row["sha256"]), str(row["ext"])
    path = fetch_immutable(str(row["archive_url"]), f"images/{sha[:2]}/{sha}.{ext}", sha)
    if ext == "svg":
        return _rasterize(path, sha, size or DEFAULT_SVG_SIZE, ext)
    img: Image.Image = Image.open(path)
    img.load()
    if size is not None:
        img = img.copy()
        img.thumbnail((size, size))
    return img

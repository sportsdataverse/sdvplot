"""What the web adapters (Plotly, Altair, Bokeh, HoloViews, Folium, pygal) share: image sources and aspect ratios.

Browsers load images themselves, so a web adapter hands over the mark's ``archive_url`` (immutable, content-addressed),
or with ``embed=True`` a ``data:`` URI of the cached bytes, for HTML that renders offline and for static export.
"""

from __future__ import annotations

import base64

from PIL import Image

from sdvplot._images import mark_file, url_file
from sdvplot._placement import Placement

# ESPN's combiner serves full headshots at 600x436 (measured 2026-10-04 for NFL, NBA and MLB ids); checked by
# tests/test_web_live.py.
HEADSHOT_ASPECT = 600 / 436


def aspect(p: Placement) -> float:
    """Width / height of the placement's image: the manifest's, or HEADSHOT_ASPECT for a headshot."""
    return p.aspect if p.aspect is not None else HEADSHOT_ASPECT


def axis_letter(axis: str) -> str:
    """``axis`` if it is "x" or "y", else a ValueError (the check every web adapter's axis verb starts with)."""
    if axis not in ("x", "y"):
        raise ValueError(f"axis must be 'x' or 'y', got {axis!r}")
    return axis


def image_src(p: Placement, *, embed: bool = False) -> str:
    """The image source for a browser: ``p.url``, or with ``embed=True`` a data URI of the cached image bytes.

    Embedding reads through the cache (downloading on a miss), so offline with no cached copy it raises OfflineError.
    """
    if not embed:
        return p.url
    path = mark_file(p.mark) if p.mark is not None else url_file(p.url)
    if p.mark is not None and str(p.mark["ext"]).lower() == "svg":
        mime = "image/svg+xml"
    else:
        with Image.open(path) as img:
            mime = Image.MIME.get(img.format or "", "application/octet-stream")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def image_sources(placements: list[Placement], *, embed: bool = False) -> list[str]:
    """``image_src`` for each placement, reading each distinct image once."""
    seen: dict[str, str] = {}
    out = []
    for p in placements:
        if p.url not in seen:
            seen[p.url] = image_src(p, embed=embed)
        out.append(seen[p.url])
    return out

"""What the web adapters (Plotly, Altair, Bokeh, HoloViews, Folium, pygal) share: image sources and aspect ratios.

Browsers load images themselves, so a web adapter hands over the mark's ``archive_url`` (immutable, content-addressed),
or with ``embed=True`` a ``data:`` URI of the cached bytes, for HTML that renders offline and for static export.
"""

from __future__ import annotations

import base64
from urllib.parse import quote

from PIL import Image

from sdvplot._errors import DownloadError
from sdvplot._images import mark_file, url_file
from sdvplot._placement import Placement, _warn_skipped

# ESPN's combiner serves full headshots at 600x436 (measured 2026-10-04 for NFL, NBA and MLB ids); checked by
# tests/test_web_live.py.
HEADSHOT_ASPECT = 600 / 436
HOCKEYTECH_HEADSHOT_PREFIX = "https://assets.leaguestat.com/"  # 240x240 squares (_headshots.HOCKEYTECH_HEADSHOT_URL)
_URL_PUNCTUATION = "-._~:/?#[]@!$&()*+,;=%"  # SAFE_URL's characters besides letters and digits (quote keeps those)


def aspect(p: Placement) -> float:
    """Width / height of the placement's image: the manifest's, 1 for a HockeyTech headshot, else HEADSHOT_ASPECT."""
    if p.aspect is not None:
        return p.aspect
    return 1.0 if p.url.startswith(HOCKEYTECH_HEADSHOT_PREFIX) else HEADSHOT_ASPECT


def axis_letter(axis: str) -> str:
    """``axis`` if it is "x" or "y", else a ValueError (the check every web adapter's axis verb starts with)."""
    if axis not in ("x", "y"):
        raise ValueError(f"axis must be 'x' or 'y', got {axis!r}")
    return axis


def image_src(p: Placement, *, embed: bool = False) -> str:
    """The image source for a browser: ``p.url``, or with ``embed=True`` a data URI of the cached image bytes.

    Embedding reads through the cache (downloading on a miss), so offline with no cached copy it raises OfflineError.
    The URL is percent-encoded past ``SAFE_URL``'s characters, a no-op on the URLs the manifest and player table let
    through, so an unvalidated one still cannot close the <script> block or attribute an adapter writes it into.
    """
    if not embed:
        return quote(p.url, safe=_URL_PUNCTUATION)
    path = mark_file(p.mark) if p.mark is not None else url_file(p.url)
    if p.mark is not None and str(p.mark["ext"]).lower() == "svg":
        mime = "image/svg+xml"
    else:
        with Image.open(path) as img:
            mime = Image.MIME.get(img.format or "", "application/octet-stream")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def present(placements: list[Placement], *, embed: bool = False) -> list[Placement]:
    """With ``embed=True``, the placements minus those whose headshot the CDN answers 404 (an ESPN or HockeyTech id it
    has no photo for), skipped with one SdvplotWarning as matplotlib skips an unreadable image. Any other download
    error still raises. Without ``embed`` the browser loads the URL, and shows a missing one as a broken image."""
    if not embed:
        return placements
    missing = set()
    for url in dict.fromkeys(p.url for p in placements if p.mark is None):
        try:
            url_file(url)  # cached now, so image_sources reads it from disk
        except DownloadError as e:
            if getattr(getattr(e.__cause__, "response", None), "status_code", None) != 404:
                raise
            missing.add(url)
    _warn_skipped("whose headshot is missing (HTTP 404)", [p.team_id for p in placements if p.url in missing])
    return [p for p in placements if p.url not in missing]


def image_sources(placements: list[Placement], *, embed: bool = False) -> list[str]:
    """``image_src`` for each placement, reading each distinct image once."""
    seen: dict[str, str] = {}
    out = []
    for p in placements:
        if p.url not in seen:
            seen[p.url] = image_src(p, embed=embed)
        out.append(seen[p.url])
    return out

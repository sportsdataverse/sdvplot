"""The sdv-assets logo manifest: every archived mark with its season range, source and CDN URL."""

from __future__ import annotations

import functools
import io
from typing import TYPE_CHECKING

from sdvplot._cache import MEMORY_CACHES, SAFE_URL, fetch_cached
from sdvplot._errors import warn

if TYPE_CHECKING:
    import polars as pl
else:
    from sdvplot._lazy import pl

MANIFEST_URL = "https://sdv.nyc3.cdn.digitaloceanspaces.com/assets/public/manifest/marks.csv"
# The columns sdvplot reads: a contract with sdv-assets (checked live by tests/test_manifest.py)
REQUIRED_COLUMNS = (
    "level",
    "league",
    "entity_id",
    "entity_name",
    "program",
    "mark_type",
    "variant",
    "valid_from",
    "valid_to",
    "source",
    "sha256",
    "ext",
    "archive_url",
    "first_seen",
)


def _validate(body: bytes) -> None:
    # parse the whole body the way _read() will, so a ragged or header-only manifest never replaces the cached one
    m = pl.read_csv(io.BytesIO(body), infer_schema_length=0)
    missing = [c for c in REQUIRED_COLUMNS if c not in m.columns]
    if missing:
        raise ValueError(f"the logo manifest is missing columns {missing}")
    if m.is_empty():
        raise ValueError("the logo manifest has no rows")


# keyed by mtime so a refreshed file is read again; only the current file matters, so the previous frame (~17 MiB) is
# dropped rather than kept for the session
@functools.lru_cache(maxsize=1)
def _read(path: str, mtime: float) -> pl.DataFrame:
    # every column as text first, so ids keep leading zeros and never become floats; then type the season range
    m = pl.read_csv(path, infer_schema_length=0)
    # archive_url reaches the web adapters' HTML: a row whose URL is not a plain https URL is dropped, never passed on
    ok = m["archive_url"].str.contains(f"^(?:{SAFE_URL})$").fill_null(False)
    if not ok.all():
        bad = m.filter(~ok)["archive_url"]
        warn(
            f"dropped {len(bad)} logo manifest row(s) whose archive_url is not a plain https URL, e.g. {bad[0]!r:.100}"
        )
        m = m.filter(ok)
    return m.with_columns(
        pl.col("valid_from").cast(pl.Int32, strict=False),
        pl.col("valid_to").cast(pl.Int32, strict=False),
    )


MEMORY_CACHES.append(_read.cache_clear)  # clear_cache() also frees the parsed manifest


def load_manifest() -> pl.DataFrame:
    """The logo manifest, from the local cache (refreshed after SDVPLOT_CACHE_TTL days)."""
    path = fetch_cached(MANIFEST_URL, "manifest/marks.csv", validate=_validate)
    return _read(str(path), path.stat().st_mtime)

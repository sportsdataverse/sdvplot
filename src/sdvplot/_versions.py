"""What a bug report needs: package version, bundled-index version, and the cached manifest's date."""

from __future__ import annotations

from sdvplot._cache import read_meta
from sdvplot._index import index_version


def versions() -> dict[str, str | None]:
    from sdvplot import __version__

    meta = read_meta("manifest/marks.csv") or {}
    return {"sdvplot": __version__, "index": index_version(), "manifest_last_modified": meta.get("last_modified")}

"""What a bug report needs: package version, bundled-index version, and the cached manifest's date."""

from __future__ import annotations

from sdvplot._cache import read_meta
from sdvplot._index import index_version


def versions() -> dict[str, str | None]:
    """What a bug report needs: the package version, the bundled-index version, and the cached manifest's date.

    Returns:
        dict[str, str | None]: Keys ``sdvplot``, ``index`` and ``manifest_last_modified`` (None until the manifest has
        been downloaded).

    Example:
        ::

            import sdvplot

            sdvplot.versions()["sdvplot"]   # '0.1.0'

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    from sdvplot import __version__

    meta = read_meta("manifest/marks.csv") or {}
    return {"sdvplot": __version__, "index": index_version(), "manifest_last_modified": meta.get("last_modified")}

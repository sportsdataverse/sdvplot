import os

import polars as pl
import pytest

from sdvplot import _cache, _manifest


def test_manifest_types(manifest):
    assert manifest.schema["entity_id"] == pl.String and manifest.schema["valid_from"] == pl.Int32
    assert manifest.height == 11


def test_a_manifest_missing_required_columns_is_rejected(cache, monkeypatch):
    from tests.conftest import FakeResponse, FakeSession

    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"level,league\nteam,nfl\n")))
    _manifest._read.cache_clear()
    with pytest.raises(Exception, match="missing columns"):
        _manifest.load_manifest()


@pytest.mark.skipif(os.environ.get("SDVPLOT_LIVE_TESTS") != "1", reason="network: set SDVPLOT_LIVE_TESTS=1")
def test_live_manifest_still_has_the_columns_sdvplot_reads(tmp_path, monkeypatch):
    """Cross-repo contract with sdv-assets: if this fails, sdv-assets changed its manifest columns."""
    monkeypatch.setenv("SDVPLOT_CACHE_DIR", str(tmp_path))
    _manifest._read.cache_clear()
    m = _manifest.load_manifest()
    assert set(_manifest.REQUIRED_COLUMNS) <= set(m.columns) and m.height > 40_000

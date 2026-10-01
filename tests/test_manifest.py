import os

import polars as pl
import pytest

from sdvplot import _cache, _manifest
from sdvplot._errors import SdvplotWarning
from tests.conftest import FIXTURE, FakeResponse, FakeSession


def test_manifest_types(manifest):
    assert manifest.schema["entity_id"] == pl.String and manifest.schema["valid_from"] == pl.Int32
    assert manifest.height == 15


def test_a_manifest_missing_required_columns_is_rejected(cache, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"level,league\nteam,nfl\n")))
    _manifest._read.cache_clear()
    with pytest.raises(Exception, match="missing columns"):
        _manifest.load_manifest()


@pytest.mark.parametrize(
    "body",
    [
        FIXTURE.read_bytes().split(b"\n", 1)[0] + b"\n",  # header only: a failed producer run
        FIXTURE.read_bytes() + b"," * 40 + b"\n",  # a ragged row the parser rejects
    ],
    ids=["header-only", "unparseable"],
)
def test_a_header_only_or_unparseable_manifest_keeps_the_cached_copy(manifest, monkeypatch, body):
    monkeypatch.setenv("SDVPLOT_CACHE_TTL", "0")
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, body)))
    with pytest.warns(SdvplotWarning, match="using the cached copy") as w:
        assert _manifest.load_manifest().equals(manifest)
    assert len(w) == 1


@pytest.mark.skipif(os.environ.get("SDVPLOT_LIVE_TESTS") != "1", reason="network: set SDVPLOT_LIVE_TESTS=1")
def test_live_manifest_still_has_the_columns_sdvplot_reads(tmp_path, monkeypatch):
    """Cross-repo contract with sdv-assets: if this fails, sdv-assets changed its manifest columns."""
    monkeypatch.setenv("SDVPLOT_CACHE_DIR", str(tmp_path))
    _manifest._read.cache_clear()
    m = _manifest.load_manifest()
    assert set(_manifest.REQUIRED_COLUMNS) <= set(m.columns) and m.height > 40_000

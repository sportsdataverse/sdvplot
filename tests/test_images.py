import hashlib
import io

import polars as pl
import pytest
from PIL import Image

from sdvplot import _cache, _images, _manifest
from tests.conftest import FakeResponse, FakeSession


def _png(w, h):
    buf = io.BytesIO()
    Image.new("RGBA", (w, h), (200, 0, 0, 255)).save(buf, "PNG")
    return buf.getvalue()


SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50" viewBox="0 0 100 50"><rect width="100" height="50" fill="#c00"/></svg>'


def _manifest_with(monkeypatch, body, ext):
    sha = hashlib.sha256(body).hexdigest()
    df = pl.DataFrame(
        {
            "level": ["team"],
            "league": ["nfl"],
            "entity_id": ["13"],
            "entity_name": ["Las Vegas Raiders"],
            "program": ["pro"],
            "mark_type": ["logo"],
            "variant": ["default"],
            "valid_from": [None],
            "valid_to": [None],
            "source": ["espn"],
            "sha256": [sha],
            "ext": [ext],
            "archive_url": [f"https://cdn/{sha}.{ext}"],
            "first_seen": ["2026-09-26"],
        },
        schema_overrides={"valid_from": pl.Int32, "valid_to": pl.Int32},
    )
    monkeypatch.setattr(_manifest, "load_manifest", lambda: df)
    monkeypatch.setattr("sdvplot._marks.load_manifest", lambda: df)
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, body)))


def test_png_logo_is_decoded_and_scaled_down(cache, monkeypatch):
    _manifest_with(monkeypatch, _png(500, 250), "png")
    img = _images.logo_image("LV", "nfl", size=100)
    assert img.size == (100, 50)


def test_png_without_size_keeps_its_pixels(cache, monkeypatch):
    _manifest_with(monkeypatch, _png(500, 250), "png")
    assert _images.logo_image("LV", "nfl").size == (500, 250)


def test_svg_is_rasterized_at_the_requested_longest_side(cache, monkeypatch):
    pytest.importorskip("resvg_py")
    _manifest_with(monkeypatch, SVG, "svg")
    assert _images.logo_image("LV", "nfl", size=200).size == (200, 100)


def test_svg_without_the_extra_names_the_extra(cache, monkeypatch):
    import builtins

    real_import = builtins.__import__

    def no_resvg(name, *a, **k):
        if name == "resvg_py":
            raise ImportError("no resvg")
        return real_import(name, *a, **k)

    _manifest_with(monkeypatch, SVG, "svg")
    monkeypatch.setattr(builtins, "__import__", no_resvg)
    with pytest.raises(ImportError, match=r"sdvplot\[svg\]"):
        _images.logo_image("LV", "nfl", size=64)

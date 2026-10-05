import hashlib
import io
import os
import subprocess
import sys

import polars as pl
import pytest
from PIL import Image

from sdvplot import _cache, _images, _manifest
from sdvplot._errors import InputError, SdvplotWarning
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


def test_svg_raster_cache_includes_version(cache, monkeypatch):
    pytest.importorskip("resvg_py")
    _manifest_with(monkeypatch, SVG, "svg")
    _images.logo_image("LV", "nfl", size=200)

    # After first call, exactly one raster file exists
    rasters_dir = _cache.cache_dir() / "rasters"
    rasters_v1 = list(rasters_dir.glob("*_200_v*.png"))
    assert len(rasters_v1) == 1, f"Expected 1 raster file, got {len(rasters_v1)}"

    # Monkeypatch version to simulate an upgrade
    def mock_version(dist):
        return "99.9.9" if dist == "resvg-py" else "0.1.0"

    monkeypatch.setattr("importlib.metadata.version", mock_version)
    _images._clear_decoded()  # an upgrade means a new process, which has no decoded image in memory

    # Second call with different version should create a new raster file
    img = _images.logo_image("LV", "nfl", size=200)
    assert img.size == (200, 100)

    # After second call with different version, two raster files exist
    rasters_v2 = list(rasters_dir.glob("*_200_v*.png"))
    assert len(rasters_v2) == 2, f"Expected 2 raster files, got {len(rasters_v2)}"
    # One of the files should contain the new version string
    assert any("99.9.9" in f.name for f in rasters_v2), (
        f"Expected a file with version '99.9.9', got {[f.name for f in rasters_v2]}"
    )


def test_malformed_svg_error_names_sha(cache, monkeypatch):
    pytest.importorskip("resvg_py")
    bad_svg = b"<svg>unclosed"
    sha = hashlib.sha256(bad_svg).hexdigest()
    _manifest_with(monkeypatch, bad_svg, "svg")
    with pytest.raises(ValueError, match=sha):
        _images.logo_image("LV", "nfl", size=64)


def test_corrupt_cached_raster_is_rerendered(cache, monkeypatch):
    pytest.importorskip("resvg_py")
    import importlib.metadata

    _manifest_with(monkeypatch, SVG, "svg")

    # First render
    img1 = _images.logo_image("LV", "nfl", size=200)
    assert img1 is not None

    # Find and corrupt the cached raster file
    version = importlib.metadata.version("resvg-py")
    sha = hashlib.sha256(SVG).hexdigest()
    raster_dir = _cache.cache_dir() / "rasters"
    raster_files = list(raster_dir.glob(f"{sha}_200_v{version}.png"))
    assert len(raster_files) == 1, f"Expected cached raster file, got {len(raster_files)}"
    raster_path = raster_files[0]
    raster_path.write_bytes(b"corrupted garbage data")

    # Second call should detect corruption and re-render
    img2 = _images.logo_image("LV", "nfl", size=200)
    assert img2 is not None
    assert img2.size == (200, 100)


def test_missing_resvg_metadata_error_names_extra(cache, monkeypatch):
    pytest.importorskip("resvg_py")
    import importlib.metadata

    _manifest_with(monkeypatch, SVG, "svg")

    # Monkeypatch metadata.version to raise PackageNotFoundError
    def mock_version(dist):
        if dist == "resvg-py":
            raise importlib.metadata.PackageNotFoundError(dist)
        return "0.1.0"

    monkeypatch.setattr("importlib.metadata.version", mock_version)

    with pytest.raises(ImportError, match=r"sdvplot\[svg\]"):
        _images.logo_image("LV", "nfl", size=64)


def test_a_resolved_team_with_no_mark_gets_one_warning(manifest):  # the Chargers have only wordmarks
    with pytest.warns(SdvplotWarning, match=r"no logo archived for 'LAC' \(nfl\)") as w:
        assert _images.logo_image("LAC", "nfl") is None
    assert len(w) == 1


def test_an_unknown_team_gets_only_the_resolver_warning(manifest):
    with pytest.warns(SdvplotWarning, match="'XXX'") as w:
        assert _images.logo_image("XXX", "nfl") is None
    assert len(w) == 1


def test_a_read_only_cache_still_returns_the_rasterized_svg(cache, monkeypatch):
    pytest.importorskip("resvg_py")
    _manifest_with(monkeypatch, SVG, "svg")
    assert _images.logo_image("LV", "nfl", size=200).size == (200, 100)  # caches the raster
    raster = next((_cache.cache_dir() / "rasters").glob("*.png"))
    raster.write_bytes(b"corrupt")

    def read_only(*args, **kwargs):
        raise PermissionError("read-only file system")

    monkeypatch.setattr(_images, "atomic_write", read_only)
    monkeypatch.setattr(type(raster), "unlink", read_only)
    assert _images.logo_image("LV", "nfl", size=200).size == (200, 100)  # corrupt raster, no unlink, no write
    assert _images.logo_image("LV", "nfl", size=100).size == (100, 50)  # a new size, no write


# --- bounded SVG rendering -----------------------------------------------------------------------------------------


def _svg(w, h):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}"/></svg>'.encode()
    )


def _svg_row(monkeypatch, body):
    _manifest_with(monkeypatch, body, "svg")
    sha = hashlib.sha256(body).hexdigest()
    return {"sha256": sha, "ext": "svg", "archive_url": f"https://cdn/{sha}.svg"}


@pytest.mark.parametrize(
    ("shape", "size", "expected"), [((1, 4), 512, (128, 512)), ((4, 1), 64, (64, 16)), ((1, 64), 640, (10, 640))]
)
def test_an_svg_is_rendered_with_its_longest_side_at_size(cache, monkeypatch, shape, size, expected):
    pytest.importorskip("resvg_py")
    assert _images.load_mark_image(_svg_row(monkeypatch, _svg(*shape)), size).size == expected


def test_an_svg_size_over_max_size_is_refused_before_anything_is_rendered(cache, monkeypatch):
    resvg_py = pytest.importorskip("resvg_py")
    row = _svg_row(monkeypatch, SVG)
    rendered = []
    monkeypatch.setattr(resvg_py, "svg_to_bytes", lambda **kw: rendered.append(kw))
    with pytest.raises(InputError, match="4096"):
        _images.load_mark_image(row, _images.MAX_SIZE + 1)
    assert rendered == []


def test_an_svg_beyond_1_to_64_is_refused(cache, monkeypatch):
    pytest.importorskip("resvg_py")
    with pytest.raises(InputError, match="aspect ratio"):
        _images.load_mark_image(_svg_row(monkeypatch, _svg(1, 100)))


@pytest.mark.skipif(sys.platform != "linux", reason="RLIMIT_AS is enforced on Linux")
def test_the_svgs_that_used_to_abort_the_process_raise_under_a_memory_limit(tmp_path):
    """These renders asked resvg for 100 GB and 6.4 GB: the process died with SIGABRT (Rust's allocation failure)."""
    pytest.importorskip("resvg_py")
    script = (
        "import resource, sys\n"
        "resource.setrlimit(resource.RLIMIT_AS, (1 << 30, 1 << 30))\n"
        "from pathlib import Path\n"
        "from sdvplot import _images\n"
        "from sdvplot._errors import InputError\n"
        "for name, size in [('tall', 512), ('square', 40000), ('square', 512)]:\n"
        "    try:\n"
        "        print('ok', _images._rasterize(Path(sys.argv[1]) / f'{name}.svg', name[0] * 64, size, 'svg').size)\n"
        "    except InputError:\n"
        "        print('InputError')\n"
    )
    (tmp_path / "tall.svg").write_bytes(_svg(1, 100000))
    (tmp_path / "square.svg").write_bytes(_svg(10, 10))
    env = {**os.environ, "SDVPLOT_CACHE_DIR": str(tmp_path / "cache")}
    r = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)], capture_output=True, text=True, env=env, timeout=120
    )
    assert r.returncode == 0, r.stderr[-2000:]
    assert r.stdout.splitlines() == ["InputError", "InputError", "ok (512, 512)"]


def test_the_decoded_image_cache_counts_bytes_per_sample(cache, monkeypatch):
    """A 16-bit grayscale PNG decodes as I;16, two bytes a pixel; counting one byte a sample let 16- and 32-bit images
    (I;16, I, F) hold two to four times DECODED_BUDGET."""
    buf = io.BytesIO()
    Image.new("I;16", (40, 30), 1000).save(buf, "PNG")
    body = buf.getvalue()
    _manifest_with(monkeypatch, body, "png")
    sha = hashlib.sha256(body).hexdigest()
    img = _images.load_mark_image({"sha256": sha, "ext": "png", "archive_url": f"https://cdn/{sha}.png"})
    assert img.mode == "I;16"
    assert _images._decoded_bytes == len(img.tobytes()) == 40 * 30 * 2

import importlib.util
import json
import struct
import warnings
from pathlib import Path

import pytest

import sdvplot.matplotlib  # noqa: F401

ROOT = Path(__file__).parents[1]
IMG = ROOT / "docs" / "static" / "img" / "home"

spec = importlib.util.spec_from_file_location("home_figures", ROOT / "tools" / "home_figures.py")
hf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hf)


def _figures():  # written by tools/home_figures.py with the PNGs
    return json.loads((ROOT / "docs" / "src" / "data" / "home_figures.json").read_text(encoding="utf-8"))


def test_every_home_figure_has_both_pngs_at_its_size_and_nothing_else_is_there():
    expected = {f"{f['name']}-{mode}.png": (f["width"], f["height"]) for f in _figures() for mode in ("light", "dark")}
    assert sorted(p.name for p in IMG.glob("*")) == sorted(expected)
    for name, size in expected.items():
        head = (IMG / name).read_bytes()[:24]
        assert head[:8] == b"\x89PNG\r\n\x1a\n", name
        assert struct.unpack(">II", head[16:24]) == size, name  # the IHDR width and height


def test_every_home_figure_has_alt_text_and_a_caption():
    figures = _figures()
    assert len(figures) >= 3
    for f in figures:
        assert len(f["alt"].split()) >= 15 and f["caption"].strip(), f["name"]


def test_the_home_page_draws_the_figures_from_the_manifest():
    page = (ROOT / "docs" / "src" / "pages" / "index.tsx").read_text(encoding="utf-8")
    assert "from '@site/src/data/home_figures.json'" in page
    assert "/img/home/${f.name}-light.png" in page and "/img/home/${f.name}-dark.png" in page


def _one_image(ax, variant):  # add_images() skips an image it cannot read with only an SdvplotWarning
    ax.set_xlim(0, 2)
    ax.set_ylim(0, 2)
    hf.sdvplot.matplotlib.add_images(ax, [1], [1], ["https://example.invalid/a.png"], height=0.2)
    return "alt text " * 8


def _one_headshot(ax, variant):  # add_headshots() raises when the download fails
    ax.set_xlim(0, 2)
    ax.set_ylim(0, 2)
    hf.sdvplot.add_headshots(ax, [1], [1], ["3139477"], league="nfl", height=0.2)
    return "alt text " * 8


def _isolated(monkeypatch, tmp_path, fn):
    """home_figures pointed at a scratch dir with one stale PNG in it and one figure, with no network."""
    img = tmp_path / "home"
    img.mkdir()
    (img / "removed-figure-light.png").write_bytes(b"stale")
    manifest = tmp_path / "home_figures.json"
    manifest.write_text("[]\n")
    monkeypatch.setattr(hf, "IMG", img)
    monkeypatch.setattr(hf, "DATA", manifest)
    monkeypatch.setattr(hf, "FIGURES", [("one", "A caption.", fn)])
    return img, manifest


@pytest.mark.real_index
def test_main_drops_the_pngs_of_removed_figures(monkeypatch, tmp_path):
    from PIL import Image

    import sdvplot.matplotlib as m

    monkeypatch.setattr(m, "load_path_image", lambda url: Image.new("RGBA", (8, 8), "red"))
    img, manifest = _isolated(monkeypatch, tmp_path, _one_image)
    assert hf.main() == 0
    assert sorted(p.name for p in img.glob("*")) == ["one-dark.png", "one-light.png"]
    assert json.loads(manifest.read_text())[0]["name"] == "one"


@pytest.mark.real_index
@pytest.mark.parametrize("fn", [_one_image, _one_headshot], ids=["warns", "raises"])
def test_an_image_that_cannot_be_fetched_fails_the_run_and_writes_nothing(monkeypatch, tmp_path, fn):
    import sdvplot.matplotlib as m

    def fail(url):
        raise OSError("download failed")

    monkeypatch.setattr(m, "load_path_image", fail)
    monkeypatch.setattr(m, "load_url_image", fail)
    img, manifest = _isolated(monkeypatch, tmp_path, fn)
    with warnings.catch_warnings():
        warnings.simplefilter("always")  # pytest's own error filter must not be what fails the run
        assert hf.main() == 1
    assert [p.name for p in img.glob("*")] == ["removed-figure-light.png"]  # the committed set is untouched
    assert manifest.read_text() == "[]\n"

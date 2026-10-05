import json
import struct
from pathlib import Path

ROOT = Path(__file__).parents[1]
IMG = ROOT / "docs" / "static" / "img" / "home"


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
        assert len(f["alt"].split()) >= 8 and f["caption"].strip(), f["name"]


def test_the_home_page_draws_the_figures_from_the_manifest():
    page = (ROOT / "docs" / "src" / "pages" / "index.tsx").read_text(encoding="utf-8")
    assert "from '@site/src/data/home_figures.json'" in page
    assert "/img/home/${f.name}-light.png" in page and "/img/home/${f.name}-dark.png" in page

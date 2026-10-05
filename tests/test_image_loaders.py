import io

from PIL import Image

from sdvplot import _cache
from sdvplot._images import load_mark_image, load_url_image
from sdvplot._marks import select_mark
from tests.conftest import FakeResponse, FakeSession


def test_load_mark_image_reads_the_cached_mark(mark_images):
    img = load_mark_image(select_mark("LV", "nfl", mark_type="wordmark"))
    assert img.size == (50, 20)  # the fixture wordmark is 500 x 200, cached at 1/10


def test_load_mark_image_scales_down_to_size(mark_images):
    assert max(load_mark_image(select_mark("LV", "nfl"), size=10).size) == 10


def test_load_url_image_downloads_once_then_uses_the_cache(cache, monkeypatch):
    buf = io.BytesIO()
    Image.new("RGBA", (8, 6)).save(buf, format="PNG")
    session = FakeSession(FakeResponse(200, buf.getvalue()))
    monkeypatch.setattr(_cache, "SESSION", session)
    assert load_url_image("https://example.com/h.png").size == (8, 6)
    assert load_url_image("https://example.com/h.png").size == (8, 6)  # FakeSession has no second response
    assert len(session.calls) == 1


def test_load_url_image_never_caches_a_non_image(cache, monkeypatch):
    import pytest

    from sdvplot._errors import OfflineError

    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, b"<html>not an image</html>")))
    with pytest.raises(OfflineError):
        load_url_image("https://example.com/broken.png")


def test_load_mark_image_decodes_a_mark_once(mark_images, monkeypatch):
    row = select_mark("LV", "nfl")
    decoded = []
    real_open = Image.open
    monkeypatch.setattr(Image, "open", lambda *a, **k: decoded.append(a) or real_open(*a, **k))
    first, second = load_mark_image(row), load_mark_image(row)
    assert len(decoded) == 1
    assert first is not second  # a copy: a caller drawing on it cannot poison the next
    first.putpixel((0, 0), (1, 2, 3, 4))
    assert load_mark_image(row).getpixel((0, 0)) != (1, 2, 3, 4)
    load_mark_image(row, size=10)  # another size is another entry
    assert len(decoded) == 2


def test_clear_cache_also_drops_the_decoded_images(mark_images, monkeypatch):
    import sdvplot

    row = select_mark("LV", "nfl")
    load_mark_image(row)
    for sub in mark_images.iterdir():
        (sub / _cache.MARKER).touch()  # a custom cache directory: only marked subdirectories are deleted
    sdvplot.clear_cache()
    assert not (mark_images / "images").exists()
    import pytest

    from sdvplot._errors import OfflineError

    monkeypatch.setattr(_cache, "SESSION", FakeSession())  # nothing to download from, and no stale decode to serve
    with pytest.raises((OfflineError, IndexError)):
        load_mark_image(row)

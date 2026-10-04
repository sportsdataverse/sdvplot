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

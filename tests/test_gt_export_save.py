"""gt_save_crop and gt_social_crop, with a fake renderer in place of headless Chrome."""

import io

import polars as pl
import pytest

pytest.importorskip("great_tables")
from great_tables import GT  # noqa: E402
from PIL import Image  # noqa: E402

from sdvplot.great_tables._export import gt_save_crop, gt_social_crop  # noqa: E402
from tests.gt_export_fakes import BLACK, MAGENTA, WHITE, fake_render, forbid_render  # noqa: E402

DF = pl.DataFrame({"team": ["LV", "LAR"], "wins": [10, 8]})


def test_save_crop_trims_pads_and_writes(monkeypatch, tmp_path):
    calls = fake_render(monkeypatch, [(40, 30)])
    out = tmp_path / "t.png"
    assert gt_save_crop(GT(DF), out, bg="#ff00ff", whitespace=10, zoom=3, expand=7) == out
    with Image.open(out) as im:
        assert im.size == (60, 50)
        corners = [im.getpixel(p) for p in [(0, 0), (9, 9), (10, 10), (49, 39), (50, 40)]]
    assert corners == [MAGENTA, MAGENTA, BLACK, BLACK, MAGENTA]
    assert calls[0][1:] == (3, 7)  # zoom and expand reach gtsave


def test_save_crop_returns_the_image_with_r_defaults(monkeypatch):
    calls = fake_render(monkeypatch, [(40, 30)])
    im = gt_save_crop(GT(DF))
    assert isinstance(im, Image.Image) and im.size == (140, 130)  # whitespace=50
    assert calls[0][1:] == (2, 5)  # zoom=2, expand=5


def test_save_crop_scales_to_a_width(monkeypatch):
    fake_render(monkeypatch, [(40, 30)])
    assert gt_save_crop(GT(DF), width=70).size == (70, 65)


def test_save_crop_writes_a_jpeg_at_magicks_quality(monkeypatch, tmp_path):
    fake_render(monkeypatch, [(40, 30)])
    reference = io.BytesIO()
    Image.new("RGB", (8, 8)).save(reference, "JPEG", quality=92)
    with Image.open(gt_save_crop(GT(DF), tmp_path / "t.jpeg")) as im, Image.open(reference) as ref:
        assert im.format == "JPEG" and im.size == (140, 130)
        assert im.quantization == ref.quantization  # quality 92, not Pillow's 75


def test_social_crop_grows_the_short_side_and_centers_the_table(monkeypatch):
    fake_render(monkeypatch, [(40, 30)])
    im = gt_social_crop(GT(DF), aspect_ratio="16:9", whitespace=10)  # 60x50 padded -> 89x50
    assert im.size == (89, 50)
    assert im.getpixel((24, 10)) == BLACK and im.getpixel((23, 10)) == WHITE  # (89 - 60) // 2 + 10 = 24


def test_social_crop_gravity_then_width(monkeypatch):
    fake_render(monkeypatch, [(40, 30)])
    im = gt_social_crop(GT(DF), aspect_ratio=0.5, whitespace=10, gravity="NorthWest", width=30)  # 60x120 -> 30x60
    assert im.size == (30, 60)
    assert im.getpixel((15, 12))[0] < 40 and im.getpixel((15, 50)) == WHITE  # the table sits at the top


@pytest.mark.parametrize(
    ("call", "error"),
    [
        (lambda: gt_save_crop(GT(DF), bg="whitee"), ValueError),
        (lambda: gt_save_crop(GT(DF), "table.txt"), ValueError),
        (lambda: gt_save_crop(GT(DF), "table"), ValueError),
        (lambda: gt_save_crop(GT(DF), whitespace=-1), ValueError),
        (lambda: gt_save_crop(GT(DF), whitespace="5"), ValueError),
        (lambda: gt_save_crop(GT(DF), width=0), ValueError),
        (lambda: gt_save_crop(DF), TypeError),
        (lambda: gt_social_crop(GT(DF), aspect_ratio="16:0"), ValueError),
        (lambda: gt_social_crop(GT(DF), gravity="middle"), ValueError),
        (lambda: gt_save_crop(GT(DF), zoom=0), ValueError),
        (lambda: gt_save_crop(GT(DF), zoom=-1), ValueError),
        (lambda: gt_save_crop(GT(DF), zoom="2"), ValueError),
        (lambda: gt_save_crop(GT(DF), zoom=None), ValueError),
        (lambda: gt_social_crop(GT(DF), zoom=float("inf")), ValueError),
        (lambda: gt_social_crop(GT(DF), zoom=float("nan")), ValueError),
    ],
)
def test_bad_arguments_fail_before_rendering(monkeypatch, call, error):
    forbid_render(monkeypatch)
    with pytest.raises(error):
        call()

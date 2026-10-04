"""The Pillow ports of sdvplotR's magick calls, against ImageMagick.

Expected values were measured on 2026-10-04 with R 4.6.1 + magick 2.9.1 (ImageMagick 6.9.13-29) on the same images,
built there with image_blank() + image_composite(): image_trim(), image_border(), image_extent(gravity=) and
image_resize("{w}x"). The canvas and ratio cases are gt_social_crop()'s own R arithmetic.
"""

import pytest

pytest.importorskip("great_tables")
import sdvplot.great_tables._export as ex  # noqa: E402
from tests.gt_export_fakes import BLACK, RED, img  # noqa: E402


def test_trim_matches_imagemagick_for_a_block():
    t = ex._trim(img(12, 10, blocks=[(4, 3, 3, 2, "black"), (6, 4, 1, 1, "red")]))
    assert t.size == (3, 2)
    assert t.getpixel((2, 1)) == RED and sorted(t.getcolors()) == [(1, RED), (5, BLACK)]


def test_trim_compares_each_edge_with_its_own_corner_like_imagemagick():
    # right edge vs the top-right pixel (white), left/top vs the top-left (gray): magick keeps 4x10
    band = img(12, 10, blocks=[(0, 0, 6, 10, "#cccccc"), (2, 3, 2, 2, "red")])
    assert ex._trim(band).size == (4, 10)
    # bottom edge vs the bottom-left pixel (blue): magick keeps 12x5
    bottom = img(12, 10, blocks=[(0, 7, 12, 3, "blue"), (5, 2, 2, 2, "red")])
    assert ex._trim(bottom).size == (12, 5)


def test_trim_leaves_a_one_color_image_alone():  # magick raises GeometryDoesNotContainImage here
    assert ex._trim(img(6, 4)).size == (6, 4)


def test_pad_matches_image_border():
    p = ex._pad(img(3, 2, "black", blocks=[(2, 1, 1, 1, "red")]), "#FBFAF7", 2)
    assert p.size == (7, 6)
    assert p.getpixel((0, 0)) == (251, 250, 247) and p.getpixel((4, 3)) == RED and p.getpixel((2, 2)) == BLACK


# gravity -> where the source's red pixel (at 2,1 of a 3x2 image) lands on an 8x5 and on a 9x6 canvas
EXTENT = {
    "center": ((4, 2), (5, 3)),
    "north": ((4, 1), (5, 1)),
    "south": ((4, 4), (5, 5)),
    "east": ((7, 2), (8, 3)),
    "west": ((2, 2), (2, 3)),
    "northwest": ((2, 1), (2, 1)),
    "northeast": ((7, 1), (8, 1)),
    "southwest": ((2, 4), (2, 5)),
    "southeast": ((7, 4), (8, 5)),
}


@pytest.mark.parametrize("gravity", EXTENT)
def test_extent_places_like_imagemagick(gravity):
    source = img(3, 2, "black", blocks=[(2, 1, 1, 1, "red")])
    for canvas, red in zip([(8, 5), (9, 6)], EXTENT[gravity], strict=True):
        e = ex._extent(source, *canvas, "white", gravity)
        assert e.size == canvas
        assert e.getpixel(red) == RED


@pytest.mark.parametrize(
    ("size", "width", "expected"),
    [((333, 101), 200, (200, 61)), ((100, 37), 250, (250, 93)), ((7, 3), 10, (10, 4)), ((640, 480), 1080, (1080, 810))],
)
def test_fit_width_rounds_half_up_like_imagemagick(size, width, expected):
    assert ex._fit_width(img(*size), width).size == expected


# round() is half-to-even in R and in Python: 201 / 2 = 100.5 -> 100
@pytest.mark.parametrize(
    ("w", "h", "ratio", "expected"),
    [
        (201, 100, 2, (201, 100)),
        (300, 200, 1, (300, 300)),
        (300, 200, 16 / 9, (356, 200)),
        (250, 400, 4 / 5, (320, 400)),
        (101, 100, 1.91, (191, 100)),
        (500, 401, 1.25, (501, 401)),
    ],
)
def test_canvas_grows_the_short_side_like_r(w, h, ratio, expected):
    assert ex._canvas(w, h, ratio) == expected


@pytest.mark.parametrize(
    ("value", "expected"), [("1:1", 1.0), ("16:9", 16 / 9), ("4x5", 0.8), ("1.91", 1.91), (1.91, 1.91), (2, 2.0)]
)
def test_ratio_reads_the_r_forms(value, expected):
    assert ex._ratio(value) == pytest.approx(expected)


@pytest.mark.parametrize(
    "bad", ["", "wide", "16:0", "0:9", "-1", "1:2:3", 0, -2.0, True, None, float("nan"), float("inf")]
)
def test_ratio_rejects_anything_but_a_positive_ratio(bad):
    with pytest.raises(ValueError, match="aspect_ratio"):
        ex._ratio(bad)

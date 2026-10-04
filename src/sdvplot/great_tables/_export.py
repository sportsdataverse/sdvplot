"""Image export and composition for great_tables: sdvplotR's gt_save_crop, gt_save_batch, gt_social_crop, gt_grid and
gt_stack_tables.

A table renders through great_tables' own ``GT.gtsave`` (headless Chrome over nokap, which great_tables 1.0 installs)
and composed HTML through ``nokap.from_html``, the counterparts of the ``gtExtras::gtsave_extra`` and
``webshot2::webshot`` calls sdvplotR makes. Trimming, padding, placing and resizing are Pillow ports of its magick
calls, checked against ImageMagick 6.9 in the tests.
"""

from __future__ import annotations

import math
import re
import tempfile
from pathlib import Path

from great_tables import GT
from PIL import Image, ImageChops

# ---------------------------------------------------------------------------------------------------------------------
# Rendering (the only steps that need Chrome; tests replace these two functions)


def _open_rgb(path: Path) -> Image.Image:
    with Image.open(path) as im:
        return im.convert("RGB")


def _render_gt(gt: GT, zoom: float, expand: int) -> Image.Image:
    """Screenshot one table with great_tables' gtsave, as sdvplotR's gtsave_extra(zoom, expand)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "table.png"
        gt.gtsave(path, zoom=zoom, expand=expand)
        return _open_rgb(path)


def _render_html(page: str, zoom: float) -> Image.Image:
    """Screenshot the element ``#sdvplot-page`` of an HTML page, as sdvplotR's webshot2::webshot(zoom=zoom)."""
    import nokap  # a great_tables dependency; imported here so the module loads without starting anything

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "page.png"
        nokap.from_html(page, path, selector="#sdvplot-page", zoom=zoom)
        return _open_rgb(path)


# ---------------------------------------------------------------------------------------------------------------------
# Pillow ports of the magick calls


def _trim(img: Image.Image) -> Image.Image:
    """magick::image_trim(): crop uniform edges. As ImageMagick, the left and top edges match the top-left pixel, the
    right edge the top-right pixel and the bottom edge the bottom-left pixel (fuzz 0). One color everywhere is
    returned unchanged (magick raises there)."""
    w, h = img.size

    def box(xy: tuple[int, int]) -> tuple[int, int, int, int] | None:
        return ImageChops.difference(img, Image.new(img.mode, img.size, img.getpixel(xy))).getbbox()

    tl, tr, bl = box((0, 0)), box((w - 1, 0)), box((0, h - 1))
    if tl is None or tr is None or bl is None or tr[2] <= tl[0] or bl[3] <= tl[1]:
        return img
    return img.crop((tl[0], tl[1], tr[2], bl[3]))


def _extent(img: Image.Image, width: int, height: int, bg: str, gravity: str = "center") -> Image.Image:
    """magick::image_extent(): ``img`` on a ``width`` x ``height`` canvas of ``bg``, placed by ``gravity``."""
    dx, dy = width - img.width, height - img.height
    x = 0 if gravity.endswith("west") else dx if gravity.endswith("east") else dx // 2
    y = 0 if gravity.startswith("north") else dy if gravity.startswith("south") else dy // 2
    canvas = Image.new("RGB", (width, height), bg)
    canvas.paste(img, (x, y))
    return canvas


def _pad(img: Image.Image, bg: str, whitespace: int) -> Image.Image:
    """magick::image_border(bg, "{whitespace}x{whitespace}")."""
    return _extent(img, img.width + 2 * whitespace, img.height + 2 * whitespace, bg)


def _fit_width(img: Image.Image, width: int) -> Image.Image:
    """magick::image_resize("{width}x"): scale to ``width``, the height following (rounded half up, as ImageMagick)."""
    height = max(1, math.floor(img.height * width / img.width + 0.5))
    return img.resize((width, height), Image.Resampling.LANCZOS)


def _canvas(width: int, height: int, ratio: float) -> tuple[int, int]:
    """gt_social_crop's canvas: grow the short side until width / height is ``ratio`` (R's round: half to even)."""
    if width / height > ratio:
        return width, round(width / ratio)
    return round(height * ratio), height


def _ratio(aspect_ratio: str | float) -> float:
    """``"16:9"``, ``"4x5"`` or a number -> a positive finite ratio."""
    ratio = math.nan
    try:
        if isinstance(aspect_ratio, str) and re.search("[:x]", aspect_ratio):
            a, b = re.split("[:x]", aspect_ratio)
            ratio = float(a) / float(b)
        elif not isinstance(aspect_ratio, bool):
            ratio = float(aspect_ratio)
    except (TypeError, ValueError, ZeroDivisionError):
        pass
    if not (ratio > 0 and math.isfinite(ratio)):
        raise ValueError(
            f"aspect_ratio could not be read as a ratio: got {aspect_ratio!r}; use '1:1', '16:9', '4x5' or a number "
            "like 1.91"
        )
    return ratio

"""Image export and composition for great_tables: sdvplotR's gt_save_crop, gt_save_batch, gt_social_crop, gt_grid and
gt_stack_tables.

A table renders through great_tables' own ``GT.gtsave`` (headless Chrome over nokap, which great_tables 1.0 installs)
and composed HTML through ``nokap.from_html``, the counterparts of the ``gtExtras::gtsave_extra`` and
``webshot2::webshot`` calls sdvplotR makes. Trimming, padding, placing and resizing are Pillow ports of its magick
calls, checked against ImageMagick 6.9 in the tests.
"""

from __future__ import annotations

import math
import numbers
import re
import sys
import tempfile
import warnings
from collections import Counter
from collections.abc import Callable
from os import PathLike
from pathlib import Path
from typing import Any

import narwhals as nw
from great_tables import GT
from PIL import Image, ImageChops, ImageColor

from sdvplot._errors import SdvplotWarning

_GRAVITY = ("center", "north", "south", "east", "west", "northwest", "northeast", "southwest", "southeast")
_JPEG_QUALITY = 92  # magick's default; Pillow's own (75) blurs table text

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


# ---------------------------------------------------------------------------------------------------------------------
# Argument checks: all run before anything renders, so a typo never costs a browser start


def _check_gt(value: Any, what: str = "data") -> None:
    if not isinstance(value, GT):
        raise TypeError(f"{what} must be a great_tables GT, not {type(value).__name__}")


def _pixels(name: str, value: Any, *, positive: bool = False) -> int:
    ok = isinstance(value, numbers.Real) and not isinstance(value, bool) and math.isfinite(value)
    if not ok or value < 0 or (positive and value == 0):
        raise ValueError(
            f"{name} must be a {'positive' if positive else 'non-negative'} number of pixels, got {value!r}"
        )
    return int(value)


def _check_file(file: str | PathLike[str] | None) -> None:
    if file is None:
        return
    fmt = Image.registered_extensions().get(Path(file).suffix.lower())
    if fmt is None or fmt not in Image.SAVE:
        raise ValueError(f"file must end in an image extension such as .png, .jpg or .jpeg, got {str(file)!r}")


def _check_common(bg: str, whitespace: Any, width: Any, file: str | PathLike[str] | None) -> tuple[int, int | None]:
    ImageColor.getrgb(bg)  # ValueError: unknown color specifier
    _check_file(file)
    return _pixels("whitespace", whitespace), None if width is None else _pixels("width", width, positive=True)


def _check_gravity(gravity: str) -> str:
    g = str(gravity).lower()
    if g not in _GRAVITY:
        raise ValueError(f"gravity must be one of {', '.join(_GRAVITY)}, got {gravity!r}")
    return g


def _finish(img: Image.Image, file: str | PathLike[str] | None, width: int | None) -> Any:
    if width is not None:
        img = _fit_width(img, width)
    if file is None:
        return img
    img.save(file, quality=_JPEG_QUALITY)
    return file


# ---------------------------------------------------------------------------------------------------------------------
# Single tables


def gt_save_crop(
    data: GT,
    file: str | PathLike[str] | None = None,
    bg: str = "white",
    whitespace: int = 50,
    zoom: float = 2,
    expand: int = 5,
    width: int | None = None,
) -> Any:
    """Save a table to an image, trimmed to its content with an even border.

    Renders the table in headless Chrome (great_tables' ``GT.gtsave``), trims the page around it and pads a
    ``whitespace`` border of ``bg`` back on.

    Args:
        data: The great_tables ``GT`` to save.
        file: A path ending in an image extension Pillow writes (``.png``, ``.jpg``, ``.jpeg``, ...). ``None`` returns
            the image instead of writing it.
        bg: The border color: a CSS color name or hex code.
        whitespace: The border, in pixels, left around the trimmed table.
        zoom: The rendering zoom; 2 gives a sharp (retina) image.
        expand: Pixels of page captured around the table before trimming.
        width: A final width in pixels, the height following, so a series of tables shares one width. ``None`` keeps
            the rendered width.

    Returns:
        str | os.PathLike | PIL.Image.Image: ``file`` after writing it, or the image when ``file`` is ``None``.

    Raises:
        TypeError: If ``data`` is not a ``GT``.
        ValueError: If ``bg``, ``whitespace``, ``width`` or the extension of ``file`` is invalid (checked before
            rendering).
        nokap.ChromeNotFoundError: If no Chrome or Chromium is installed (set ``CHROME_PATH`` to point at one).

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_save_crop

            gt_save_crop(GT(df), "table.png", bg="#FBFAF7", width=900)

    See Also:
        gt_social_crop: the same, padded onto a fixed-ratio canvas.
        Ported from sdvplotR ``gt_save_crop()``: https://sdvplotR.sportsdataverse.org/reference/gt_save_crop.html
    """
    _check_gt(data)
    pad, final = _check_common(bg, whitespace, width, file)
    return _finish(_pad(_trim(_render_gt(data, zoom, expand)), bg, pad), file, final)


def gt_social_crop(
    data: GT,
    file: str | PathLike[str] | None = None,
    aspect_ratio: str | float = "1:1",
    bg: str = "white",
    whitespace: int = 60,
    gravity: str = "center",
    zoom: float = 2,
    expand: int = 5,
    width: int | None = None,
) -> Any:
    """Save a table centered on a canvas of a fixed aspect ratio, for social posts.

    The trimmed table is never cropped: the canvas' short side grows until the ratio is met.

    Args:
        data: The great_tables ``GT`` to save.
        file: A path ending in an image extension (``.png``, ``.jpg``, ...). ``None`` returns the image.
        aspect_ratio: The canvas ratio, width to height: ``"1:1"``, ``"16:9"``, ``"4x5"`` or a number such as 1.91.
        bg: The canvas color.
        whitespace: Pixels left around the table before the canvas grows to the ratio.
        gravity: Where the table sits on the canvas, as in magick: ``"center"``, ``"north"``, ``"south"``,
            ``"east"``, ``"west"``, ``"northwest"``, ``"northeast"``, ``"southwest"`` or ``"southeast"``.
        zoom: The rendering zoom.
        expand: Pixels of page captured around the table before trimming.
        width: A final width in pixels for the finished canvas, the ratio held.

    Returns:
        str | os.PathLike | PIL.Image.Image: ``file`` after writing it, or the image when ``file`` is ``None``.

    Raises:
        TypeError: If ``data`` is not a ``GT``.
        ValueError: If ``aspect_ratio`` is not a positive ratio, ``gravity`` is unknown, or ``bg``, ``whitespace``,
            ``width`` or the extension of ``file`` is invalid (all checked before rendering).
        nokap.ChromeNotFoundError: If no Chrome or Chromium is installed.

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_social_crop

            gt_social_crop(GT(df), "post.png", aspect_ratio="4:5", bg="#0C0D10")

    See Also:
        gt_save_crop: a plain trimmed save.
        Ported from sdvplotR ``gt_social_crop()``: https://sdvplotR.sportsdataverse.org/reference/gt_social_crop.html
    """
    _check_gt(data)
    ratio = _ratio(aspect_ratio)
    place = _check_gravity(gravity)
    pad, final = _check_common(bg, whitespace, width, file)
    img = _pad(_trim(_render_gt(data, zoom, expand)), bg, pad)
    img = _extent(img, *_canvas(img.width, img.height, ratio), bg, place)
    return _finish(img, file, final)


# ---------------------------------------------------------------------------------------------------------------------
# Batches


def _slug(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(value)).strip("-").lower()


def gt_save_batch(
    data: Any,
    group: str,
    fn: Callable[[Any, Any], GT],
    file: str,
    dir: str | PathLike[str],
    match_width: bool = True,
    bg: str = "white",
    whitespace: int = 50,
    zoom: float = 2,
    quiet: bool = False,
) -> list[str]:
    """Save a matched set of table images, one per group.

    Splits ``data`` by a column, builds a table per group with ``fn`` and writes one image per group, padded to a
    common width so a posted series is not ragged. A group whose table fails to build or render is skipped and named
    in one warning at the end; the rest are still written.

    Args:
        data: A pandas or polars DataFrame (any narwhals-supported eager frame).
        group: The column to split on. Its missing values are skipped.
        fn: Builds one table, called as ``fn(df, value)`` with the group's rows (the same frame type as ``data``) and
            its value; it must return a ``GT``.
        file: A file name containing ``{group}``, replaced by the group value with anything awkward turned into a
            dash and lower-cased, so ``"North / East"`` writes ``"net-north-east.png"`` for ``"net-{group}.png"``.
        dir: The directory to write into, created when missing. It has no default, so a batch never lands in the
            working directory unasked; pass ``"."`` for that.
        match_width: Pad every image to the widest one's width.
        bg: The padding color.
        whitespace: The border, in pixels, around each table.
        zoom: The rendering zoom.
        quiet: Do not print the per-group progress lines (to stderr).

    Returns:
        list[str]: The files written, in group order.

    Raises:
        TypeError: If ``data`` is not a data frame or ``fn`` is not callable.
        ValueError: If ``group`` is not a column, has no non-missing values, two values would write the same file,
            ``file`` lacks ``{group}`` or an image extension, or ``bg`` / ``whitespace`` is invalid (all before
            rendering).
        RuntimeError: If no group built.
        nokap.ChromeNotFoundError: If no browser can start (raised at the first group, not collected per group).

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_save_batch

            def build(df, value):
                return GT(df).tab_header(title=f"{value} cylinders")

            gt_save_batch(cars, "cyl", build, "cars-{group}.png", dir="out")

    See Also:
        gt_grid: the same split composed into one image.
        Ported from sdvplotR ``gt_save_batch()``: https://sdvplotR.sportsdataverse.org/reference/gt_save_batch.html
    """
    from nokap import ChromeNotFoundError, ChromeStartError

    frame = nw.from_native(data, eager_only=True)
    if not callable(fn):
        raise TypeError("fn must be a function returning a GT")
    if "{group}" not in file:
        raise ValueError(f"file must contain {{group}}, as in 'net-{{group}}.png', got {file!r}")
    if not isinstance(group, str) or group not in frame.columns:
        raise ValueError(f"group must name one column of data, got {group!r}")
    pad, _ = _check_common(bg, whitespace, None, file.replace("{group}", "x"))
    keys = frame[group].drop_nulls().unique(maintain_order=True).to_list()
    if not keys:
        raise ValueError(f"group {group!r} has no non-missing values")
    names = [file.replace("{group}", _slug(k)) for k in keys]
    shared = sorted(n for n, c in Counter(names).items() if c > 1)
    if shared:
        raise ValueError(f"group values write to the same file name: {', '.join(shared)}; rename the values first")

    built: list[tuple[str, Image.Image]] = []
    failed: list[str] = []
    for key, name in zip(keys, names, strict=True):
        if not quiet:
            print(f"Building {key!r}", file=sys.stderr)
        try:
            tbl = fn(frame.filter(nw.col(group) == key).to_native(), key)
            _check_gt(tbl, "fn's return value")
            built.append((name, _trim(_render_gt(tbl, zoom, 5))))
        except (ChromeNotFoundError, ChromeStartError):
            raise  # no browser: every group would fail the same way
        except Exception as e:
            failed.append(f"{key}: {e}")
    if not built:
        raise RuntimeError("No group built successfully:\n" + "\n".join(failed))

    widest = max(img.width for _, img in built) if match_width else None
    Path(dir).mkdir(parents=True, exist_ok=True)
    paths = []
    for name, img in built:
        if widest is not None:
            img = _extent(img, widest, img.height, bg)
        path = str(Path(dir) / name)
        _pad(img, bg, pad).save(path, quality=_JPEG_QUALITY)
        paths.append(path)
    if failed:
        warnings.warn(
            f"{len(failed)} group(s) failed and were skipped:\n" + "\n".join(failed), SdvplotWarning, stacklevel=2
        )
    if not quiet:
        print(f"Wrote {len(paths)} file(s) to {dir}", file=sys.stderr)
    return paths

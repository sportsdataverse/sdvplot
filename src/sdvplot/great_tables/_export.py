"""Image export and composition for great_tables: sdvplotR's gt_save_crop, gt_save_batch, gt_social_crop, gt_grid and
gt_stack_tables.

A table renders through great_tables' own ``GT.gtsave`` (headless Chrome over nokap, which great_tables 1.0 installs)
and composed HTML through ``nokap.from_html``, the counterparts of the ``gtExtras::gtsave_extra`` and
``webshot2::webshot`` calls sdvplotR makes. Trimming, padding, placing and resizing are Pillow ports of its magick
calls, checked against ImageMagick 6.9 in the tests.
"""

from __future__ import annotations

import html
import math
import numbers
import re
import sys
import tempfile
import warnings
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from os import PathLike
from pathlib import Path
from typing import Any

import htmltools
import narwhals as nw
from great_tables import GT
from PIL import Image, ImageChops, ImageColor

from sdvplot._errors import SdvplotWarning
from sdvplot.great_tables._marks import _check_gt

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


def _finite(value: Any) -> bool:
    return isinstance(value, numbers.Real) and not isinstance(value, bool) and math.isfinite(value)


def _pixels(name: str, value: Any, *, positive: bool = False) -> int:
    if not _finite(value) or value < 0 or (positive and value == 0):
        raise ValueError(
            f"{name} must be a {'positive' if positive else 'non-negative'} number of pixels, got {value!r}"
        )
    return int(value)


def _check_zoom(zoom: Any) -> None:
    if not (_finite(zoom) and zoom > 0):
        raise ValueError(f"zoom must be a positive number, got {zoom!r}")


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
        zoom: The rendering zoom, a positive number; 2 gives a sharp (retina) image.
        expand: Pixels of page captured around the table before trimming.
        width: A final width in pixels, the height following, so a series of tables shares one width. ``None`` keeps
            the rendered width.

    Returns:
        str | os.PathLike | PIL.Image.Image: ``file`` after writing it, or the image when ``file`` is ``None``.

    Raises:
        TypeError: If ``data`` is not a ``GT``.
        ValueError: If ``bg``, ``whitespace``, ``width``, ``zoom`` or the extension of ``file`` is invalid (checked
            before rendering).
        nokap.ChromeNotFoundError: If no Chrome or Chromium is installed (set ``CHROME_PATH`` to point at one).

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_save_crop
            import polars as pl

            df = pl.DataFrame(
                {
                    "team": ["KC", "BUF", "BAL"],
                    "espn_id": ["3139477", "3918298", "3916387"],
                    "wins": [12, 10, 9],
                }
            )

            gt_save_crop(GT(df), "table.png", bg="#FBFAF7", width=900)

    See Also:
        gt_social_crop: the same, padded onto a fixed-ratio canvas.
        Ported from sdvplotR ``gt_save_crop()``: https://sdvplotR.sportsdataverse.org/reference/gt_save_crop.html
    """
    _check_gt(data, "data")
    _check_zoom(zoom)
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
            ``width``, ``zoom`` or the extension of ``file`` is invalid (all checked before rendering).
        nokap.ChromeNotFoundError: If no Chrome or Chromium is installed.

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_social_crop
            import polars as pl

            df = pl.DataFrame(
                {
                    "team": ["KC", "BUF", "BAL"],
                    "espn_id": ["3139477", "3918298", "3916387"],
                    "wins": [12, 10, 9],
                }
            )

            gt_social_crop(GT(df), "post.png", aspect_ratio="4:5", bg="#0C0D10")

    See Also:
        gt_save_crop: a plain trimmed save.
        Ported from sdvplotR ``gt_social_crop()``: https://sdvplotR.sportsdataverse.org/reference/gt_social_crop.html
    """
    _check_gt(data, "data")
    ratio = _ratio(aspect_ratio)
    place = _check_gravity(gravity)
    _check_zoom(zoom)
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
            ``file`` lacks ``{group}`` or an image extension, or ``bg``, ``whitespace`` or ``zoom`` is invalid (all
            before rendering).
        RuntimeError: If no group built.
        nokap.ChromeNotFoundError: If no browser can start (raised at the first group, not collected per group).

    Example:
        ::

            from great_tables import GT
            from sdvplot.great_tables import gt_save_batch
            import polars as pl

            cars = pl.DataFrame({"cyl": [4, 4, 6], "mpg": [22.8, 24.4, 21.0]})

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
    _check_zoom(zoom)
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


# ---------------------------------------------------------------------------------------------------------------------
# Composition (sdvplotR's utils-style.R *_style lists and the shared header/footer)

_STYLE_KEYS = (
    "font",
    "size",
    "color",
    "weight",
    "italic",
    "spacing",
    "transform",
    "align",
    "line_height",
    "margin_top",
    "margin_bottom",
    "padding_top",
    "padding_bottom",
)
_CSS_PROPS = (
    ("size", "font-size"),
    ("color", "color"),
    ("weight", "font-weight"),
    ("spacing", "letter-spacing"),
    ("transform", "text-transform"),
    ("align", "text-align"),
    ("line_height", "line-height"),
    ("margin_top", "margin-top"),
    ("margin_bottom", "margin-bottom"),
    ("padding_top", "padding-top"),
    ("padding_bottom", "padding-bottom"),
)
_LENGTHS = {"size", "spacing", "margin_top", "margin_bottom", "padding_top", "padding_bottom"}
_FONT_FALLBACK = "system-ui, -apple-system, sans-serif"
_STYLE_DEFAULTS: dict[str, dict[str, Any]] = {
    "title": {"size": "28px", "weight": 700, "color": "#111111", "align": "center", "margin_bottom": 4},
    "subtitle": {"size": "16px", "weight": 400, "color": "#666666", "align": "center", "margin_bottom": 12},
    "caption": {"size": "12px", "weight": 400, "color": "#8A8A8A", "align": "center", "margin_top": 10},
    "source_note": {"size": "12px", "weight": 400, "color": "#8A8A8A", "align": "right", "margin_top": 6},
    "label": {"size": "12px", "weight": 600, "color": "#555555", "align": "left", "margin_bottom": 6},
}


def _style(arg: str, user: Mapping[str, Any] | None, default: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """A style dict (sdvplotR's ``*_style`` lists): ``default`` with the caller's keys (argument ``arg``) on top."""
    user = dict(user or {})
    unknown = sorted(set(user) - set(_STYLE_KEYS))
    if unknown:
        raise ValueError(f"{arg} has unknown key(s) {unknown}; recognized: {', '.join(_STYLE_KEYS)}")
    return {**(default or {}), **user}


def _css_len(value: Any) -> str:
    """A number (numpy numbers included) reads as pixels; anything else is a CSS length already."""
    return f"{value}px" if isinstance(value, numbers.Real) and not isinstance(value, bool) else str(value)


def _style_css(style: Mapping[str, Any], font_fallback: str | None = None) -> str:
    """A style dict -> inline CSS, in sdvplotR's .style_css() order.

    With ``font_fallback`` the font family is always set (composed HTML, which has no table font to inherit); without
    it a style with no font sets none, so the text inherits the theme's (the wave C2 headers and legends).
    """
    font = style.get("font")
    out = []
    if font is not None:
        out.append(f"font-family:'{font}', {font_fallback or 'sans-serif'};")
    elif font_fallback is not None:
        out.append(f"font-family:{font_fallback};")
    for key, prop in _CSS_PROPS:
        value = style.get(key)
        if value is not None:
            out.append(f"{prop}:{_css_len(value) if key in _LENGTHS else value};")
        if key == "weight" and style.get("italic") is True:
            out.append("font-style:italic;")
    return "".join(out)


def _text(value: Any) -> htmltools.HTML:
    """A title, caption or label: md() and html() text render as markup; anything else is escaped, as great_tables
    does (sdvplotR inserts plain strings as HTML)."""
    return htmltools.HTML(value.to_html() if hasattr(value, "to_html") else html.escape(str(value)))


def _fonts(*styles: Mapping[str, Any]) -> list[str]:
    """The distinct Google font names across style dicts, in order."""
    return list(dict.fromkeys(s["font"] for s in styles if s.get("font") is not None))


def _font_link(styles: Sequence[Mapping[str, Any]]) -> htmltools.Tag | None:
    """composed HTML never runs through great_tables' google_font(), so a named font is fetched here."""
    fonts = _fonts(*styles)
    if not fonts:
        return None
    families = "&".join(f"family={f.replace(' ', '+')}:wght@100..900" for f in fonts)
    return htmltools.tags.link(rel="stylesheet", href=f"https://fonts.googleapis.com/css2?{families}&display=swap")


def _tables(tables: Any) -> list[GT]:
    if isinstance(tables, GT):
        raise TypeError("tables must be a list of GT objects; wrap a single table as [gt]")
    items = [] if tables is None else list(tables.values()) if isinstance(tables, Mapping) else list(tables)
    if not items:
        raise ValueError("tables must be a non-empty list of GT objects")
    bad = [i for i, t in enumerate(items) if not isinstance(t, GT)]
    if bad:
        raise TypeError(f"tables must contain only GT objects; item(s) {bad} are not")
    return items


def _table_html(gt: GT) -> htmltools.Tag:
    return htmltools.div(htmltools.HTML(gt.as_raw_html()))


def _compose(
    body: htmltools.Tag,
    *,
    title: Any,
    subtitle: Any,
    caption: Any,
    source_note: Any,
    caption_rule: bool,
    title_style: Mapping[str, Any] | None,
    subtitle_style: Mapping[str, Any] | None,
    caption_style: Mapping[str, Any] | None,
    source_note_style: Mapping[str, Any] | None,
    more_styles: Sequence[Mapping[str, Any]] = (),
) -> htmltools.Tag:
    """The shared heading and footer around a grid or stack, in a shrink-to-fit wrapper (sdvplotR's layout)."""
    s_title = _style("title_style", title_style, _STYLE_DEFAULTS["title"])
    s_subtitle = _style("subtitle_style", subtitle_style, _STYLE_DEFAULTS["subtitle"])
    s_caption = _style("caption_style", caption_style, _STYLE_DEFAULTS["caption"])
    s_source = _style("source_note_style", source_note_style, _STYLE_DEFAULTS["source_note"])
    # with no subtitle the title carries the gap the subtitle would have held
    if subtitle is None and "margin_bottom" not in (title_style or {}):
        s_title["margin_bottom"] = _STYLE_DEFAULTS["subtitle"]["margin_bottom"]
    if caption_rule and "padding_bottom" not in (caption_style or {}):
        s_caption["padding_bottom"] = 6
    link = _font_link([s_title, s_subtitle, s_caption, s_source, *more_styles])

    has_header = title is not None or subtitle is not None
    has_footer = caption is not None or source_note is not None
    if not (has_header or has_footer):
        return htmltools.div(link, body) if link is not None else body
    rule = f"border-bottom:1px solid {s_caption['color']};" if caption_rule else ""
    header = footer = None
    if has_header:
        header = htmltools.div(
            htmltools.div(_text(title), style=_style_css(s_title, _FONT_FALLBACK)) if title is not None else None,
            htmltools.div(_text(subtitle), style=_style_css(s_subtitle, _FONT_FALLBACK))
            if subtitle is not None
            else None,
        )
    if has_footer:
        footer = htmltools.div(
            htmltools.div(_text(caption), style=_style_css(s_caption, _FONT_FALLBACK) + rule)
            if caption is not None
            else None,
            htmltools.div(_text(source_note), style=_style_css(s_source, _FONT_FALLBACK))
            if source_note is not None
            else None,
        )
    # inner wrapper shrinks to the tables, outer one recenters it; "safe" centering plus overflow-x keeps a sheet
    # wider than a phone scrollable
    return htmltools.div(
        link,
        htmltools.div(header, body, footer, style="display: inline-block;"),
        style="display: flex; justify-content: center; justify-content: safe center; overflow-x: auto;",
    )


def _save_composed(
    composed: htmltools.Tag, file: str | PathLike[str], bg: str, whitespace: int, zoom: float
) -> str | PathLike[str]:
    # the wrapper, not the page, is captured: it is bg on every edge, so trimming is even on all four sides
    page = htmltools.div(
        composed, id="sdvplot-page", style=f"display: inline-block; padding: 8px; background-color: {bg};"
    )
    doc = f'<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>{page}</body></html>'
    _pad(_trim(_render_html(doc, zoom)), bg, whitespace).save(file, quality=_JPEG_QUALITY)
    return file


def gt_grid(
    tables: Sequence[GT] | Mapping[Any, GT] | None = None,
    ncol: int = 2,
    labels: Any = None,
    label_style: Mapping[str, Any] | None = None,
    title: Any = None,
    subtitle: Any = None,
    caption: Any = None,
    source_note: Any = None,
    caption_rule: bool = False,
    title_style: Mapping[str, Any] | None = None,
    subtitle_style: Mapping[str, Any] | None = None,
    caption_style: Mapping[str, Any] | None = None,
    source_note_style: Mapping[str, Any] | None = None,
    gap: float = 24,
    align: str = "top",
    file: str | PathLike[str] | None = None,
    bg: str = "white",
    whitespace: int = 50,
    zoom: float = 2,
) -> Any:
    """Arrange several tables in a grid of rows and columns, as small multiples.

    The grid is HTML, not a ``GT``: each table keeps its own columns and header, so this is a last step after every
    table is themed. Give ``file`` to write it straight to an image.

    Args:
        tables: A list of ``GT`` objects (a dict's values are used in order, so ``gt_theme_preview()``'s dict works).
        ncol: The number of tables across.
        labels: A caption above each table, recycled across ``tables``: a string, ``md()``/``html()`` text, or a
            non-empty list of them. Plain strings are escaped; use ``html()`` for markup.
        label_style: Style for the labels (see ``title_style``).
        title: A heading above the whole grid: a string, ``md()`` or ``html()``. Plain strings are escaped (as in
            great_tables); use ``html()`` for markup. ``subtitle``, ``caption`` and ``source_note`` take the same.
        subtitle: A line below ``title``.
        caption: A note below the grid.
        source_note: A second line below ``caption``, right-aligned by default.
        caption_rule: Draw a hairline between ``caption`` and ``source_note``.
        title_style: A dict of any of ``font`` (a Google font name), ``size``, ``color``, ``weight``, ``italic``,
            ``spacing``, ``transform``, ``align``, ``line_height``, ``margin_top``, ``margin_bottom``,
            ``padding_top``, ``padding_bottom``. Lengths take a number (pixels) or a CSS string; keys left out keep
            their defaults.
        subtitle_style: As ``title_style``, for the subtitle.
        caption_style: As ``title_style``, for the caption.
        source_note_style: As ``title_style``, for the source note.
        gap: The space between tables, a non-negative number of pixels.
        align: How tables of differing height line up in a row: ``"top"``, ``"center"`` or ``"bottom"``.
        file: A path to write an image to; ``None`` returns the HTML.
        bg: The background color when saving.
        whitespace: Padding, in pixels, around the grid when saving.
        zoom: The rendering zoom when saving.

    Returns:
        htmltools.Tag | str | os.PathLike: The grid as HTML (it displays in a notebook), or ``file`` after writing it.

    Raises:
        TypeError: If ``tables`` holds anything but ``GT`` objects.
        TypeError: If ``labels`` is neither text nor a list of it.
        ValueError: If ``tables`` or ``labels`` is empty, ``ncol`` is below 1, ``gap`` is not a non-negative number,
            ``zoom`` is not a positive number, ``align`` or a style key is unknown, or (when saving) ``bg``,
            ``whitespace`` or the extension of ``file`` is invalid.
        nokap.ChromeNotFoundError: If saving and no Chrome or Chromium is installed.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_grid

            east = GT(pl.DataFrame({"team": ["BUF", "MIA"], "wins": [11, 9]}))
            west = GT(pl.DataFrame({"team": ["KC", "LV"], "wins": [12, 8]}))
            north = GT(pl.DataFrame({"team": ["BAL", "CIN"], "wins": [10, 9]}))
            south = GT(pl.DataFrame({"team": ["HOU", "IND"], "wins": [10, 8]}))

            gt_grid([east, west, north, south], ncol=2, title="Division leaders", caption="Data: ESPN")
            gt_grid([east, west], file="divisions.png", bg="#FBFAF7")

    See Also:
        gt_stack_tables: a vertical stack.
        Ported from sdvplotR ``gt_grid()``: https://sdvplotR.sportsdataverse.org/reference/gt_grid.html
    """
    items = _tables(tables)
    if isinstance(ncol, bool) or not isinstance(ncol, numbers.Integral) or ncol < 1:
        raise ValueError(f"ncol must be an integer of at least 1, got {ncol!r}")
    places = {"top": "start", "center": "center", "bottom": "end"}
    if align not in places:
        raise ValueError(f"align must be one of {', '.join(places)}, got {align!r}")
    _pixels("gap", gap)
    _check_zoom(zoom)
    s_label = _style("label_style", label_style, _STYLE_DEFAULTS["label"])
    pad = 0 if file is None else _check_common(bg, whitespace, None, file)[0]
    if labels is not None:
        if isinstance(labels, str) or hasattr(labels, "to_html"):
            labs = [labels]
        elif isinstance(labels, Iterable):
            labs = list(labels)
        else:
            raise TypeError(
                f"labels must be a string, md() or html() text, or a list of them, not {type(labels).__name__}"
            )
        if not labs:
            raise ValueError("labels must be non-empty; pass None for no labels")

    if labels is None:
        cells = [_table_html(t) for t in items]
    else:
        cells = [
            htmltools.div(
                htmltools.div(_text(labs[i % len(labs)]), style=_style_css(s_label, _FONT_FALLBACK)), _table_html(t)
            )
            for i, t in enumerate(items)
        ]
    grid = htmltools.div(
        *cells,
        style=f"display: grid; grid-template-columns: repeat({ncol}, max-content); gap: {gap}px; "
        f"align-items: {places[align]}; justify-content: center;",
    )
    composed = _compose(
        grid,
        title=title,
        subtitle=subtitle,
        caption=caption,
        source_note=source_note,
        caption_rule=caption_rule,
        title_style=title_style,
        subtitle_style=subtitle_style,
        caption_style=caption_style,
        source_note_style=source_note_style,
        more_styles=[s_label] if labels is not None else [],
    )
    return composed if file is None else _save_composed(composed, file, bg, pad, zoom)


def gt_stack_tables(
    tables: Sequence[GT] | Mapping[Any, GT] | None = None,
    gap: float = 16,
    align: str = "center",
    title: Any = None,
    subtitle: Any = None,
    caption: Any = None,
    source_note: Any = None,
    caption_rule: bool = False,
    title_style: Mapping[str, Any] | None = None,
    subtitle_style: Mapping[str, Any] | None = None,
    caption_style: Mapping[str, Any] | None = None,
    source_note_style: Mapping[str, Any] | None = None,
    file: str | PathLike[str] | None = None,
    bg: str = "white",
    whitespace: int = 50,
    zoom: float = 2,
) -> Any:
    """Stack several tables vertically in one block, with an optional shared heading and footer.

    The stack is HTML, not a ``GT``: each table keeps its own columns, widths and header. Give ``file`` to write it
    straight to an image.

    Args:
        tables: A list of ``GT`` objects (a dict's values are used in order).
        gap: The space between tables, a non-negative number of pixels.
        align: How tables of differing width line up: ``"center"``, ``"left"`` or ``"right"``.
        title: A heading above the stack: a string, ``md()`` or ``html()``. Plain strings are escaped (as in
            great_tables); use ``html()`` for markup. ``subtitle``, ``caption`` and ``source_note`` take the same.
        subtitle: A line below ``title``.
        caption: A note below the stack.
        source_note: A second line below ``caption``, right-aligned by default.
        caption_rule: Draw a hairline between ``caption`` and ``source_note``.
        title_style: A style dict, with the keys of ``gt_grid``'s ``title_style``.
        subtitle_style: As ``title_style``, for the subtitle.
        caption_style: As ``title_style``, for the caption.
        source_note_style: As ``title_style``, for the source note.
        file: A path to write an image to; ``None`` returns the HTML.
        bg: The background color when saving.
        whitespace: Padding, in pixels, around the stack when saving.
        zoom: The rendering zoom when saving.

    Returns:
        htmltools.Tag | str | os.PathLike: The stack as HTML (it displays in a notebook), or ``file`` after writing it.

    Raises:
        TypeError: If ``tables`` holds anything but ``GT`` objects.
        ValueError: If ``tables`` is empty, ``gap`` is not a non-negative number, ``zoom`` is not a positive number,
            ``align`` or a style key is unknown, or (when saving) ``bg``, ``whitespace`` or the extension of ``file``
            is invalid.
        nokap.ChromeNotFoundError: If saving and no Chrome or Chromium is installed.

    Example:
        ::

            import polars as pl
            from great_tables import GT
            from sdvplot.great_tables import gt_stack_tables

            offense = GT(pl.DataFrame({"team": ["KC", "BUF"], "epa": [0.2, 0.15]}))
            defense = GT(pl.DataFrame({"team": ["BAL", "SF"], "epa": [-0.1, -0.08]}))

            gt_stack_tables([offense, defense], title="Two tables", title_style={"font": "Oswald", "size": 30})

    See Also:
        gt_grid: tables side by side.
        Ported from sdvplotR ``gt_stack_tables()``: https://sdvplotR.sportsdataverse.org/reference/gt_stack_tables.html
    """
    items = _tables(tables)
    places = {"left": "flex-start", "center": "center", "right": "flex-end"}
    if align not in places:
        raise ValueError(f"align must be one of {', '.join(places)}, got {align!r}")
    _pixels("gap", gap)
    _check_zoom(zoom)
    pad = 0 if file is None else _check_common(bg, whitespace, None, file)[0]
    stack = htmltools.div(
        *[_table_html(t) for t in items],
        style=f"display: flex; flex-direction: column; gap: {gap}px; align-items: {places[align]};",
    )
    composed = _compose(
        stack,
        title=title,
        subtitle=subtitle,
        caption=caption,
        source_note=source_note,
        caption_rule=caption_rule,
        title_style=title_style,
        subtitle_style=subtitle_style,
        caption_style=caption_style,
        source_note_style=source_note_style,
    )
    return composed if file is None else _save_composed(composed, file, bg, pad, zoom)

"""The matplotlib adapter: logos, wordmarks and headshots on Axes, single-Axes Figures and seaborn grids.

sdvplot routes matplotlib and seaborn targets here (sdvplot._dispatch). An image's height is a fraction of its Axes'
height at draw time (_AxesFractionImage), so it holds at any dpi or figure size. plotnine draws through
draw_placements too. Cartopy GeoAxes are matplotlib Axes: transform= takes the CRS of the caller's coordinates.
"""

from __future__ import annotations

import numbers
import sys
from collections.abc import Callable
from typing import Any

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.text import Text
from matplotlib.ticker import FixedFormatter, FixedLocator
from matplotlib.transforms import Affine2D, Bbox
from PIL import Image

from sdvplot._images import load_mark_image, load_url_image, logo_image
from sdvplot._placement import Placement, _real, check_alpha, check_height, place

SUPPORTS_AXIS_LOGOS = True
MAX_IMAGE_HEIGHT = 512  # px handed to matplotlib: sharp at 0.25 of a 6-inch Axes at 300 dpi, small in PDF/SVG
TITLE_GAP = 4  # points between a title image and its title text
_HA = {"left": 0.0, "center": 0.5, "right": 1.0}


class _AxesFractionImage(OffsetImage):
    """An OffsetImage drawn at a fixed fraction of its Axes' height, whatever the dpi or figure size."""

    def __init__(self, arr: np.ndarray, ax: Axes, fraction: float, **kwargs: Any) -> None:
        super().__init__(arr, **kwargs)
        self._sdv_ax, self._sdv_fraction = ax, fraction
        self._sdv_rows, self._sdv_cols = arr.shape[:2]

    def get_bbox(self, renderer: Any) -> Bbox:
        h = self._sdv_fraction * self._sdv_ax.bbox.height
        return Bbox.from_bounds(0, 0, h * self._sdv_cols / self._sdv_rows, h)


def rgba_array(img: Image.Image) -> np.ndarray:
    """An image as an RGBA array, at most MAX_IMAGE_HEIGHT pixels tall."""
    img = img.convert("RGBA")
    if img.height > MAX_IMAGE_HEIGHT:
        width = max(1, round(img.width * MAX_IMAGE_HEIGHT / img.height))
        img = img.resize((width, MAX_IMAGE_HEIGHT), Image.Resampling.LANCZOS)
    return np.asarray(img)


def target_axes(target: Any) -> Axes:
    """The one Axes to draw on: an Axes, a Figure's only Axes, a JointGrid's joint Axes, or a one-Axes grid."""
    if isinstance(target, Axes):
        return target
    if isinstance(target, Figure):
        axes = [a for a in target.axes if a.get_label() != "<colorbar>"]
        if len(axes) == 1:
            return axes[0]
        raise ValueError(f"this Figure has {len(axes)} Axes; pass the Axes to draw on, e.g. fig.axes[0]")
    joint = getattr(target, "ax_joint", None)  # seaborn JointGrid
    if isinstance(joint, Axes):
        return joint
    grid = getattr(target, "axes", None)  # seaborn FacetGrid / PairGrid: an array of Axes
    if grid is not None:
        flat = list(np.ravel(grid))
        if len(flat) == 1 and isinstance(flat[0], Axes):
            return flat[0]
        raise ValueError(f"this grid has {len(flat)} Axes; pass the Axes to draw on, e.g. g.axes.flat[0]")
    raise TypeError(f"sdvplot.matplotlib cannot draw on a {type(target).__name__}")


def _image(p: Placement) -> np.ndarray:
    return rgba_array(load_mark_image(p.mark) if p.mark is not None else load_url_image(p.url))


def _xycoords(ax: Axes, transform: Any) -> Any:
    """The coordinates (x, y) are in: the Axes' data, or ``transform`` (a Cartopy CRS or a matplotlib Transform)."""
    if transform is None:
        geoaxes = sys.modules.get("cartopy.mpl.geoaxes")  # loaded whenever a GeoAxes exists
        if geoaxes is not None and isinstance(ax, geoaxes.GeoAxes):
            raise ValueError(
                "this is a Cartopy GeoAxes, whose data coordinates are the projection's: pass the CRS of x and y, "
                "e.g. transform=ccrs.PlateCarree() for longitude/latitude"
            )
        return "data"
    return transform._as_mpl_transform(ax) if hasattr(transform, "_as_mpl_transform") else transform


def draw_placements(
    ax: Axes,
    placements: list[Placement],
    *,
    height: float,
    alpha: float = 1.0,
    zorder: float = 3,
    xycoords: Any = "data",
) -> list[AnnotationBbox]:
    """Draw each placement centred on its (x, y) in ``xycoords``, ``height`` of the Axes tall.

    A point outside the Axes is not drawn, whatever ``xycoords`` is (matplotlib only clips "data" by default).
    """
    images: dict[str, np.ndarray] = {}
    boxes = []
    for p in placements:
        if p.url not in images:
            images[p.url] = _image(p)
        box = AnnotationBbox(
            _AxesFractionImage(images[p.url], ax, height, alpha=alpha),
            (p.x, p.y),
            xycoords=xycoords,
            frameon=False,
            pad=0,
            zorder=zorder,
            annotation_clip=True,
        )
        box._sdvplot_mark = (p.team_id, p.x, p.y, height, p.url)  # type: ignore[attr-defined]
        ax.add_artist(box)
        boxes.append(box)
    return boxes


def _add(
    target: Any,
    x: Any,
    y: Any,
    teams: Any,
    *,
    kind: str,
    league: str,
    season: Any,
    height: float,
    alpha: float,
    variant: str,
    zorder: float,
    id_system: str,
    transform: Any,
) -> Any:
    h, a = check_height(height), check_alpha(alpha)
    ax = target_axes(target)
    xycoords = _xycoords(ax, transform)
    placements = place(x, y, teams, league=league, season=season, kind=kind, variant=variant, id_system=id_system)
    draw_placements(ax, placements, height=h, alpha=a, zorder=zorder, xycoords=xycoords)
    return target


def add_logos(
    target: Any,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = "default",
    zorder: float = 3,
    id_system: str = "auto",
    transform: Any = None,
) -> Any:
    """Draw each team's logo centred on its (x, y) point of a matplotlib or seaborn plot.

    Args:
        target: A matplotlib Axes, a Figure with one Axes, or a seaborn grid with one Axes (or a JointGrid).
        x: The points' x positions, in data coordinates (list, numpy array, or pandas/polars Series; read by position).
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point, to pick each team's mark for that era.
        height: The logo height as a fraction of the Axes height, in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        zorder: matplotlib drawing order (3 draws above lines and markers).
        id_system: The id system of ``teams``; "auto" tries each in order.
        transform: The coordinates x and y are in, when not the Axes' data: a Cartopy CRS such as
            ``ccrs.PlateCarree()`` (longitude/latitude, required on a GeoAxes) or a matplotlib Transform.
            A mark whose position falls outside the Axes is not drawn, whatever the transform.

    Returns:
        object: ``target`` itself, drawn on.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, ``x``/``y``/``teams`` differ in length, the target
            has several Axes, or the target is a Cartopy GeoAxes and ``transform`` is None.

    Example:
        ::

            import matplotlib.pyplot as plt
            import sdvplot

            fig, ax = plt.subplots()
            ax.set_xlim(0, 30)
            ax.set_ylim(-10, 0)
            sdvplot.add_logos(ax, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)

        On a Cartopy map, at longitude/latitude::

            import cartopy.crs as ccrs

            ax = plt.axes(projection=ccrs.Robinson())
            ax.set_global()
            sdvplot.add_logos(ax, [-94.48], [39.05], ["KC"], league="nfl", transform=ccrs.PlateCarree())

    See Also:
        sdvplotR geom_nfl_logos(): https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    return _add(
        target, x, y, teams, kind="logo", league=league, season=season, height=height, alpha=alpha,
        variant=variant, zorder=zorder, id_system=id_system, transform=transform,
    )  # fmt: skip


def add_wordmarks(
    target: Any,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = "default",
    zorder: float = 3,
    id_system: str = "auto",
    transform: Any = None,
) -> Any:
    """Draw each team's wordmark centred on its (x, y) point of a matplotlib or seaborn plot.

    Args:
        target: A matplotlib Axes, a Figure with one Axes, or a seaborn grid with one Axes (or a JointGrid).
        x: The points' x positions, in data coordinates (read by position).
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point.
        height: The wordmark height as a fraction of the Axes height, in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        zorder: matplotlib drawing order.
        id_system: The id system of ``teams``; "auto" tries each in order.
        transform: The coordinates x and y are in, when not the Axes' data: a Cartopy CRS such as
            ``ccrs.PlateCarree()`` (longitude/latitude, required on a GeoAxes) or a matplotlib Transform.
            A mark whose position falls outside the Axes is not drawn, whatever the transform.

    Returns:
        object: ``target`` itself, drawn on.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, the inputs differ in length, the target has
            several Axes, or the target is a Cartopy GeoAxes and ``transform`` is None.

    Example:
        ::

            import matplotlib.pyplot as plt
            import sdvplot

            fig, ax = plt.subplots()
            sdvplot.add_wordmarks(ax, [0.5], [0.5], ["KC"], league="nfl", height=0.1)

    See Also:
        sdvplotR geom_nfl_wordmarks(): https://sdvplotR.sportsdataverse.org/
    """
    return _add(
        target, x, y, teams, kind="wordmark", league=league, season=season, height=height, alpha=alpha,
        variant=variant, zorder=zorder, id_system=id_system, transform=transform,
    )  # fmt: skip


def add_headshots(
    target: Any,
    x: Any,
    y: Any,
    players: Any,
    *,
    league: str,
    height: float = 0.1,
    alpha: float = 1,
    zorder: float = 3,
    id_system: str = "espn",
    transform: Any = None,
) -> Any:
    """Draw each player's headshot centred on its (x, y) point of a matplotlib or seaborn plot.

    Args:
        target: A matplotlib Axes, a Figure with one Axes, or a seaborn grid with one Axes (or a JointGrid).
        x: The points' x positions, in data coordinates (read by position).
        y: The points' y positions, the same length as ``x``.
        players: The player id for each point.
        league: The SDV league key, e.g. "nfl".
        height: The headshot height as a fraction of the Axes height, in (0, 1].
        alpha: Opacity, 0 to 1.
        zorder: matplotlib drawing order.
        id_system: "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``.
        transform: The coordinates x and y are in, when not the Axes' data: a Cartopy CRS such as
            ``ccrs.PlateCarree()`` (longitude/latitude, required on a GeoAxes) or a matplotlib Transform.
            A mark whose position falls outside the Axes is not drawn, whatever the transform.

    Returns:
        object: ``target`` itself, drawn on.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, the inputs differ in length, the target has
            several Axes, or the target is a Cartopy GeoAxes and ``transform`` is None.

    Example:
        ::

            import matplotlib.pyplot as plt
            import sdvplot

            fig, ax = plt.subplots()
            sdvplot.add_headshots(ax, [0.5], [0.5], ["3139477"], league="nfl", height=0.2)

    See Also:
        sdvplotR geom_nfl_headshots(): https://sdvplotR.sportsdataverse.org/
    """
    return _add(
        target, x, y, players, kind="headshot", league=league, season=None, height=height, alpha=alpha,
        variant="default", zorder=zorder, id_system=id_system, transform=transform,
    )  # fmt: skip


def _axis(ax: Axes, axis: str) -> Any:
    if axis not in ("x", "y"):
        raise ValueError(f"axis must be 'x' or 'y', got {axis!r}")
    return ax.xaxis if axis == "x" else ax.yaxis


def _ticks(which: Any) -> tuple[list[float], list[str]]:
    locs = [float(v) for v in which.get_majorticklocs()]
    return locs, [str(s) for s in which.get_major_formatter().format_ticks(locs)]


def axis_logos(
    target: Any,
    axis: str,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    variant: str = "default",
    mark_type: str = "logo",
    id_system: str = "auto",
) -> Any:
    """Replace a team axis' tick labels with the teams' logos (or wordmarks).

    Reads the axis' ticks and labels when called, so call it after setting the categories and limits. Labels that are
    not teams stay as text, with one SdvplotWarning.

    Args:
        target: A matplotlib Axes, a Figure with one Axes, or a seaborn grid with one Axes.
        axis: "x" or "y".
        league: The SDV league key, e.g. "nfl".
        season: One season for every label.
        height: The image height as a fraction of the Axes height, in (0, 1].
        variant: "default", "dark", or a named variant from ``marks()``.
        mark_type: "logo" or "wordmark".
        id_system: The id system of the labels; "auto" tries each in order.

    Returns:
        object: ``target`` itself, drawn on.

    Raises:
        ValueError: If ``axis`` is not "x"/"y", ``height`` is out of range, or the target has several Axes.

    Example:
        ::

            import matplotlib.pyplot as plt
            import sdvplot

            fig, ax = plt.subplots()
            ax.bar(["KC", "BUF", "BAL"], [12, 10, 9])
            sdvplot.axis_logos(ax, "x", league="nfl", height=0.08)

    See Also:
        sdvplotR element_sdv_logo(): https://sdvplotR.sportsdataverse.org/
    """
    h = check_height(height)
    ax = target_axes(target)
    which = _axis(ax, axis)
    locs, labels = _ticks(which)
    low, high = sorted(ax.get_xlim() if axis == "x" else ax.get_ylim())
    in_view = [(loc, lab) for loc, lab in zip(locs, labels, strict=True) if low <= loc <= high]
    view_locs, view_labels = [loc for loc, _ in in_view], [lab for _, lab in in_view]
    if axis == "x":
        positions: tuple[list[Any], list[Any]] = (view_locs, [0.0] * len(view_locs))
    else:
        positions = ([0.0] * len(view_locs), view_locs)
    placements = place(*positions, view_labels, league=league, season=season, kind=mark_type, variant=variant,
                       id_system=id_system)  # fmt: skip
    drawn = {(p.x if axis == "x" else p.y) for p in placements}
    which.set_major_locator(FixedLocator(locs))
    which.set_major_formatter(
        FixedFormatter(["" if loc in drawn else lab for loc, lab in zip(locs, labels, strict=True)])
    )
    tick = which.get_major_ticks()[0] if which.get_major_ticks() else None
    offset = (tick.get_tick_padding() if tick is not None else 0) + 2  # images start this many points past the axis
    image_points = h * ax.bbox.height * 72 / ax.figure.dpi
    if tick is not None:  # keep the configured label pad, plus room for the images below/left of the tick marks
        which.set_tick_params(pad=tick.get_pad() + 2 + image_points)
    images: dict[str, np.ndarray] = {}
    for p in placements:
        loc = p.x if axis == "x" else p.y
        if p.url not in images:
            images[p.url] = _image(p)
        box = AnnotationBbox(
            _AxesFractionImage(images[p.url], ax, h),
            (loc, 0) if axis == "x" else (0, loc),
            xycoords=ax.get_xaxis_transform() if axis == "x" else ax.get_yaxis_transform(),
            xybox=(0, -offset) if axis == "x" else (-offset, 0),
            boxcoords="offset points",
            box_alignment=(0.5, 1.0) if axis == "x" else (1.0, 0.5),
            frameon=False,
            pad=0,
            annotation_clip=False,
        )
        box._sdvplot_axis_mark = (axis, p.team_id, loc)  # type: ignore[attr-defined]
        ax.add_artist(box)
    return target


def _align(ha: Any) -> float:
    """A horizontal alignment as a fraction: 0 left, 0.5 centre, 1 right (plotnine also takes a number)."""
    if isinstance(ha, numbers.Real):
        return float(ha)
    return _HA.get(ha, 0.5)


class _TitleImage(AnnotationBbox):
    """An image beside a title Text, ``height`` points tall. sdvplotR puts the image inside the title, so the pair is
    aligned as one: at each draw this shifts the text by the image's width (times the title's alignment) to match."""

    def __init__(self, arr: np.ndarray, text: Text, side: str, height: float, align: Callable[[], float]) -> None:
        left = side == "left"
        super().__init__(
            OffsetImage(arr, zoom=height / arr.shape[0]),  # OffsetImage sizes in points: rows * zoom
            (0.0, 0.5) if left else (1.0, 0.5),
            xycoords=text,  # a fraction of the text's bbox
            xybox=(-TITLE_GAP if left else TITLE_GAP, 0),
            boxcoords="offset points",
            box_alignment=(1.0, 0.5) if left else (0.0, 0.5),
            frameon=False,
            pad=0,
            annotation_clip=False,
            zorder=text.get_zorder() - 0.01,  # drawn just before the text, so the text draws with this draw's shift
        )
        self._sdv_left, self._sdv_align, self._sdv_shift = left, align, Affine2D()
        text.set_transform(text.get_transform() + self._sdv_shift)

    def update_positions(self, renderer: Any) -> None:
        room = self.offsetbox.get_bbox(renderer).width + renderer.points_to_pixels(TITLE_GAP)
        rel = self._sdv_align()
        self._sdv_shift.clear().translate((1 - rel) * room if self._sdv_left else -rel * room, 0)
        super().update_positions(renderer)


def check_title_image(side: Any, height: Any) -> float:
    """``height`` as a float, or ValueError unless ``side`` is "left"/"right" and ``height`` is a positive number."""
    if side not in ("left", "right"):
        raise ValueError(f"side must be 'left' or 'right', got {side!r}")
    if not _real(height) or height <= 0:
        raise ValueError(f"height is the image height in points, > 0, got {height!r}")
    return float(height)


def title_source(image: Any, league: str | None, season: Any) -> tuple[np.ndarray, str] | None:
    """The image to put beside a title, plus what it was: a team's logo when ``league`` is given (None, with one
    SdvplotWarning, when the team does not resolve or has no logo), else the image at a URL or local path."""
    if league is not None:
        img = logo_image(image, league, season=season)
        return None if img is None else (rgba_array(img), str(image))
    source = str(image)
    if source.startswith(("http://", "https://")):
        return rgba_array(load_url_image(source)), source
    with Image.open(source) as img:
        return rgba_array(img), source


def add_title_image(
    container: Any, text: Text, source: tuple[np.ndarray, str], side: str, height: float, align: Callable[[], float]
) -> AnnotationBbox:
    """Draw ``source`` (from title_source) beside ``text``, an Axes title or a Figure's suptitle/text."""
    box = _TitleImage(source[0], text, side, height, align)
    box._sdvplot_title_image = (side, source[1])  # type: ignore[attr-defined]
    container.add_artist(box)
    return box


def title_image(
    target: Any,
    image: Any,
    title: str = "",
    *,
    league: str | None = None,
    season: Any = None,
    side: str = "left",
    height: float = 15,
    **text_kw: Any,
) -> Any:
    """Set the plot title and draw an image (a team logo, or any image) beside it.

    The title and the image are aligned together, like the image inside sdvplotR's title: a centred title centres the
    pair, a left-aligned one starts with the image.

    Args:
        target: A matplotlib Axes (sets its title), a Figure (sets its suptitle), or a seaborn grid with one Axes.
        image: A team, in any id system ``resolve()`` understands, when ``league`` is given; otherwise an image URL
            (http or https) or a local file path.
        title: The title text.
        league: The SDV league key, e.g. "nfl"; None reads ``image`` as a URL or path.
        season: One season, to pick the team's logo for that era.
        side: "left" or "right" of the title text.
        height: The image height in points (1/72 inch), at any dpi. The title keeps its own line height, so an image
            much taller than the text needs room: raise ``pad``.
        **text_kw: Passed to ``Axes.set_title`` (``loc``, ``fontsize``, ``pad``, ...) or ``Figure.suptitle``.

    Returns:
        object: ``target`` itself, titled.

    Raises:
        ValueError: If ``side`` is not "left"/"right", ``height`` is not a positive number, or the target has several
            Axes.
        OfflineError: If a URL or logo cannot be downloaded and is not cached.
        FileNotFoundError: If a local path does not exist.

    Example:
        ::

            import matplotlib.pyplot as plt
            from sdvplot.matplotlib import title_image

            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [3, 1, 2])
            title_image(ax, "KC", "Kansas City Chiefs Analysis", league="nfl", height=20)

        A Figure's suptitle, the image on the right::

            title_image(fig, "https://example.com/banner.png", "Week 1", side="right")

    See Also:
        sdvplotR ggtitle_image(): https://sdvplotR.sportsdataverse.org/reference/ggtitle_image.html ;
        sdvplot.plotnine.title_image: the same for plotnine.
    """
    h = check_title_image(side, height)
    source = title_source(image, league, season)
    if isinstance(target, Figure):
        container: Any = target
        text = target.suptitle(title or " ", **text_kw)  # a blank title still gives the image a line to sit on
    else:
        container = target_axes(target)
        text = container.set_title(title or " ", **text_kw)
    if source is not None:
        add_title_image(container, text, source, side, h, lambda: _align(text.get_horizontalalignment()))
    return target


def drawn_title_images(target: Any) -> list[tuple[str, str]]:
    """Test hook: (side, image) for each title image on a Figure or an Axes, image being the team or URL/path given."""
    container = target if isinstance(target, Figure) else target_axes(target)
    return [a._sdvplot_title_image for a in container.artists if hasattr(a, "_sdvplot_title_image")]


def drawn_marks(target: Any) -> list[tuple[Any, ...]]:
    """Test hook: (team_id, x, y, height, url) for each image add_logos/add_wordmarks/add_headshots drew."""
    return [a._sdvplot_mark for a in target_axes(target).artists if hasattr(a, "_sdvplot_mark")]


def drawn_axis_marks(target: Any, axis: str) -> list[tuple[str, float]]:
    """Test hook: (team_id, tick position) for each axis image on ``axis``, in tick order."""
    marks = [a._sdvplot_axis_mark for a in target_axes(target).artists if hasattr(a, "_sdvplot_axis_mark")]
    return sorted(((team_id, loc) for which, team_id, loc in marks if which == axis), key=lambda m: m[1])


def visible_axis_labels(target: Any, axis: str) -> list[str]:
    """Test hook: the tick labels on ``axis`` still shown as text."""
    _, labels = _ticks(_axis(target_axes(target), axis))
    return [lab for lab in labels if lab]

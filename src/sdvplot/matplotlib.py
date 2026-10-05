"""The matplotlib adapter: logos, wordmarks and headshots on Axes, single-Axes Figures and seaborn grids.

sdvplot routes matplotlib and seaborn targets here (sdvplot._dispatch). An image's height is a fraction of its Axes'
height at draw time (_AxesFractionImage), so it holds at any dpi or figure size. plotnine draws through
draw_placements too. Cartopy GeoAxes are matplotlib Axes: transform= takes the CRS of the caller's coordinates.
"""

from __future__ import annotations

import sys
from typing import Any

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.ticker import FixedFormatter, FixedLocator
from matplotlib.transforms import Bbox
from PIL import Image

from sdvplot._images import load_mark_image, load_url_image
from sdvplot._placement import Placement, check_alpha, check_height, place

SUPPORTS_AXIS_LOGOS = True
MAX_IMAGE_HEIGHT = 512  # px handed to matplotlib: sharp at 0.25 of a 6-inch Axes at 300 dpi, small in PDF/SVG


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
        box._sdvplot_mark = (p.team_id, p.x, p.y, p.url)  # type: ignore[attr-defined]
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


def _in_view(ax: Axes, axis: str) -> tuple[list[float], list[str]]:
    """The positions and labels of the ticks of ``axis`` inside the view: the ones axis_logos turns into images."""
    locs, labels = _ticks(_axis(ax, axis))
    low, high = sorted(ax.get_xlim() if axis == "x" else ax.get_ylim())
    in_view = [(loc, lab) for loc, lab in zip(locs, labels, strict=True) if low <= loc <= high]
    return [loc for loc, _ in in_view], [lab for _, lab in in_view]


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
    return _axis_logos(target, axis, league=league, season=season, height=height, variant=variant,
                       mark_type=mark_type, id_system=id_system)  # fmt: skip


def _axis_logos(
    target: Any,
    axis: str,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    variant: str = "default",
    mark_type: str = "logo",
    id_system: str = "auto",
    warn: bool = True,
) -> Any:
    """axis_logos; ``warn=False`` skips the labels that are not teams without warning (plotnine warns once for every
    panel's labels, then draws each panel quietly)."""
    h = check_height(height)
    ax = target_axes(target)
    which = _axis(ax, axis)
    locs, labels = _ticks(which)
    view_locs, view_labels = _in_view(ax, axis)
    if axis == "x":
        positions: tuple[list[Any], list[Any]] = (view_locs, [0.0] * len(view_locs))
    else:
        positions = ([0.0] * len(view_locs), view_locs)
    placements = place(*positions, view_labels, league=league, season=season, kind=mark_type, variant=variant,
                       id_system=id_system, _warn=warn)  # fmt: skip
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


def _drawn_boxes(target: Any, tag: str) -> tuple[Axes, list[Any]]:
    """The Axes and its sdvplot image boxes tagged ``tag``, after a draw. A layout engine (constrained, tight) resizes
    the Axes on draw, so an image sized before that only shows the wrong fraction afterwards."""
    ax = target_axes(target)
    ax.figure.canvas.draw()
    return ax, [a for a in ax.artists if hasattr(a, tag)]


def _drawn_height(ax: Axes, box: Any) -> float:
    """The height the box's image is drawn at, measured from its extent, as a fraction of the Axes height."""
    return float(box.offsetbox.get_window_extent().height / ax.bbox.height)


def drawn_marks(target: Any) -> list[tuple[Any, ...]]:
    """Test hook: (team_id, x, y, height, url) for each image add_logos/add_wordmarks/add_headshots drew; height is
    measured from the drawn image."""
    ax, boxes = _drawn_boxes(target, "_sdvplot_mark")
    return [(*b._sdvplot_mark[:3], _drawn_height(ax, b), b._sdvplot_mark[3]) for b in boxes]


def drawn_axis_marks(target: Any, axis: str) -> list[tuple[str, float, float]]:
    """Test hook: (team_id, tick position, height) for each axis image on ``axis``, in tick order; height is measured
    from the drawn image."""
    ax, boxes = _drawn_boxes(target, "_sdvplot_axis_mark")
    marks = [(b._sdvplot_axis_mark, _drawn_height(ax, b)) for b in boxes]
    return sorted(((team_id, loc, h) for (which, team_id, loc), h in marks if which == axis), key=lambda m: m[1])


def visible_axis_labels(target: Any, axis: str) -> list[str]:
    """Test hook: the tick labels on ``axis`` still shown as text."""
    _, labels = _ticks(_axis(target_axes(target), axis))
    return [lab for lab in labels if lab]

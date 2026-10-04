"""The matplotlib adapter: logos, wordmarks and headshots on Axes, single-Axes Figures and seaborn grids.

sdvplot routes matplotlib and seaborn targets here (sdvplot._dispatch). An image's height is a fraction of its Axes'
height at draw time (_AxesFractionImage), so it holds at any dpi or figure size. plotnine draws through
draw_placements too.
"""

from __future__ import annotations

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


def draw_placements(
    ax: Axes, placements: list[Placement], *, height: float, alpha: float = 1.0, zorder: float = 3
) -> list[AnnotationBbox]:
    """Draw each placement centred on its (x, y) in data coordinates, ``height`` of the Axes tall."""
    images: dict[str, np.ndarray] = {}
    boxes = []
    for p in placements:
        if p.url not in images:
            images[p.url] = _image(p)
        box = AnnotationBbox(
            _AxesFractionImage(images[p.url], ax, height, alpha=alpha),
            (p.x, p.y),
            xycoords="data",
            frameon=False,
            pad=0,
            zorder=zorder,
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
) -> Any:
    h, a = check_height(height), check_alpha(alpha)
    ax = target_axes(target)
    placements = place(x, y, teams, league=league, season=season, kind=kind, variant=variant, id_system=id_system)
    draw_placements(ax, placements, height=h, alpha=a, zorder=zorder)
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

    Returns:
        object: ``target`` itself, drawn on.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, ``x``/``y``/``teams`` differ in length, or the target
            has several Axes.

    Example:
        ::

            import matplotlib.pyplot as plt
            import sdvplot

            fig, ax = plt.subplots()
            ax.set_xlim(0, 30)
            ax.set_ylim(-10, 0)
            sdvplot.add_logos(ax, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)

    See Also:
        sdvplotR geom_nfl_logos(): https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    return _add(
        target, x, y, teams, kind="logo", league=league, season=season, height=height, alpha=alpha,
        variant=variant, zorder=zorder, id_system=id_system,
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

    Returns:
        object: ``target`` itself, drawn on.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or the target has
            several Axes.

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
        variant=variant, zorder=zorder, id_system=id_system,
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

    Returns:
        object: ``target`` itself, drawn on.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or the target has
            several Axes.

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
        variant="default", zorder=zorder, id_system=id_system,
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
    if axis == "x":
        positions: tuple[list[Any], list[Any]] = (locs, [0.0] * len(locs))
    else:
        positions = ([0.0] * len(locs), locs)
    placements = place(*positions, labels, league=league, season=season, kind=mark_type, variant=variant,
                       id_system=id_system)  # fmt: skip
    drawn = {(p.x if axis == "x" else p.y) for p in placements}
    which.set_major_locator(FixedLocator(locs))
    which.set_major_formatter(
        FixedFormatter(["" if loc in drawn else lab for loc, lab in zip(locs, labels, strict=True)])
    )
    tick = which.get_major_ticks()[0] if which.get_major_ticks() else None
    offset = (tick.get_tick_padding() if tick is not None else 0) + 2  # points past the tick marks
    image_points = h * ax.bbox.height * 72 / ax.figure.dpi
    which.set_tick_params(pad=image_points + offset)  # move unknown labels and the axis label past the images
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

"""The matplotlib adapter: logos, wordmarks and headshots on Axes, single-Axes Figures and seaborn grids.

sdvplot routes matplotlib and seaborn targets here (sdvplot._dispatch). An image's height is a fraction of its Axes'
height at draw time (_AxesFractionImage), so it holds at any dpi or figure size. plotnine draws through
_draw_placements too. Cartopy GeoAxes are matplotlib Axes: transform= takes the CRS of the caller's coordinates.
"""

from __future__ import annotations

import numbers
import sys
from collections.abc import Callable
from typing import Any, Literal

from sdvplot._errors import InputError, OfflineError, UnsupportedTargetError, requires_extra, warn

with requires_extra("mpl"):
    import numpy as np
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.offsetbox import AnnotationBbox, OffsetImage
    from matplotlib.text import Text
    from matplotlib.ticker import FixedFormatter, FixedLocator
    from matplotlib.transforms import Affine2D, Bbox, Transform
    from PIL import Image

from sdvplot import _tiers
from sdvplot._images import MAX_SIZE, load_mark_image, load_path_image, load_url_image, logo_image
from sdvplot._placement import Placement, _real, _warn_skipped, check_alpha, check_height, place, place_images
from sdvplot._types import AxisMarkType

_SUPPORTS_AXIS_LOGOS = True
_MAX_IMAGE_HEIGHT = 512  # px handed to matplotlib: sharp at 0.25 of a 6-inch Axes at 300 dpi, small in PDF/SVG
_TITLE_GAP = 4  # points between a title image and its title text
_HA = {"left": 0.0, "center": 0.5, "right": 1.0}

__all__ = ["add_headshots", "add_images", "add_logos", "add_wordmarks", "axis_logos", "team_tiers", "title_image"]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)


class _AxesFractionImage(OffsetImage):
    """An OffsetImage drawn at a fixed fraction of its Axes' height, whatever the dpi or figure size."""

    def __init__(self, arr: np.ndarray, ax: Axes, fraction: float, **kwargs: Any) -> None:
        super().__init__(arr, **kwargs)
        self._sdv_ax, self._sdv_fraction = ax, fraction
        self._sdv_rows, self._sdv_cols = arr.shape[:2]

    def get_bbox(self, renderer: Any) -> Bbox:
        h = self._sdv_fraction * self._sdv_ax.bbox.height
        return Bbox.from_bounds(0, 0, h * self._sdv_cols / self._sdv_rows, h)


def _rgba_array(img: Image.Image) -> np.ndarray:
    """An image as an RGBA array, at most _MAX_IMAGE_HEIGHT pixels tall."""
    img = img.convert("RGBA")
    if img.height > _MAX_IMAGE_HEIGHT:
        width = max(1, round(img.width * _MAX_IMAGE_HEIGHT / img.height))
        img = img.resize((width, _MAX_IMAGE_HEIGHT), Image.Resampling.LANCZOS)
    return np.asarray(img)


def _target_axes(target: Any) -> Axes:
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
    raise UnsupportedTargetError(f"sdvplot.matplotlib cannot draw on a {type(target).__name__}")


def _image(p: Placement) -> np.ndarray:
    if p.mark is None:
        return _rgba_array(load_url_image(p.url))
    # decoded no bigger than drawn: half the archive is 4096 px (64 MiB each decoded); a wide mark keeps its full
    # height, up to the longest side sdvplot renders (a mark wider than 8:1 is drawn from a 4096 px decode)
    size = min(MAX_SIZE, round(_MAX_IMAGE_HEIGHT * max(1.0, p.aspect or 1.0)))
    return _rgba_array(load_mark_image(p.mark, size))


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


def _draw_placements(
    ax: Axes,
    placements: list[Placement],
    *,
    height: float,
    alpha: float = 1.0,
    zorder: float = 3,
    xycoords: Any = "data",
    images: dict[str, np.ndarray] | None = None,
) -> list[AnnotationBbox]:
    """Draw each placement centred on its (x, y) in ``xycoords``, ``height`` of the Axes tall.

    A point outside the Axes is not drawn, whatever ``xycoords`` is (matplotlib only clips "data" by default).
    ``images`` holds arrays already loaded, by url; the rest are loaded once each.
    """
    images = dict(images or {})
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
    ax = _target_axes(target)
    xycoords = _xycoords(ax, transform)
    placements = place(x, y, teams, league=league, season=season, kind=kind, variant=variant, id_system=id_system)
    _draw_placements(ax, placements, height=h, alpha=a, zorder=zorder, xycoords=xycoords)
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
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant``
            is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If ``x``/``y``/``teams`` differ in length, the target has several Axes, or the target is a Cartopy
            GeoAxes and ``transform`` is None.
        UnsupportedTargetError: (a TypeError) If ``target`` is not a matplotlib Axes, a Figure or a seaborn grid.
        OfflineError: If the logo manifest or a mark's image is neither cached nor downloadable (a DownloadError, also
            an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not
            match the manifest's sha256, or one PIL cannot decode).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If the manifest's sha256 or extension for a mark would put the file outside
            the cache directory.
        OptionalDependencyError: If a mark is an SVG and the ``svg`` extra is not installed.

    Example:
        ::

            import matplotlib.pyplot as plt
            import sdvplot

            fig, ax = plt.subplots()
            ax.set_xlim(0, 30)
            ax.set_ylim(-10, 0)
            sdvplot.add_logos(ax, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)

            # On a Cartopy map, at longitude/latitude:
            #   import cartopy.crs as ccrs
            #   ax = plt.axes(projection=ccrs.Robinson())
            #   ax.set_global()
            #   sdvplot.add_logos(ax, [-94.48], [39.05], ["KC"], league="nfl", transform=ccrs.PlateCarree())

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
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant``
            is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If the inputs differ in length, the target has several Axes, or the target is a Cartopy GeoAxes and
            ``transform`` is None.
        UnsupportedTargetError: (a TypeError) If ``target`` is not a matplotlib Axes, a Figure or a seaborn grid.
        OfflineError: If the logo manifest or a mark's image is neither cached nor downloadable (a DownloadError, also
            an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not
            match the manifest's sha256, or one PIL cannot decode).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If the manifest's sha256 or extension for a mark would put the file outside
            the cache directory.
        OptionalDependencyError: If a mark is an SVG and the ``svg`` extra is not installed.

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
        id_system: "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and
            WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``.
        transform: The coordinates x and y are in, when not the Axes' data: a Cartopy CRS such as
            ``ccrs.PlateCarree()`` (longitude/latitude, required on a GeoAxes) or a matplotlib Transform.
            A mark whose position falls outside the Axes is not drawn, whatever the transform.

    Returns:
        object: ``target`` itself, drawn on.

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league`` has no ESPN headshots, or
            ``id_system`` is not valid for ``league``.
        ValueError: If the inputs differ in length, the target has several Axes, or the target is a Cartopy GeoAxes and
            ``transform`` is None.
        UnsupportedTargetError: (a TypeError) If ``target`` is not a matplotlib Axes, a Figure or a seaborn grid.
        OfflineError: If a headshot, or with ``id_system="gsis"`` the nflverse player table, is neither cached nor
            downloadable (a DownloadError, also an OSError, for an HTTP error status).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.

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


def _read_images(placements: list[Placement], cache: dict[str, np.ndarray | None]) -> list[str]:
    """Read each placement's image into ``cache`` (url -> RGBA array, or None when it cannot be read), each url once
    across calls; return the urls of the points whose image cannot be read, one per point."""
    for p in placements:
        if p.url not in cache:
            try:
                cache[p.url] = _rgba_array(load_path_image(p.url))
            except (OSError, ValueError, OfflineError):  # missing file, not an image, failed download
                cache[p.url] = None
    return [p.url for p in placements if cache[p.url] is None]


def _draw_images(
    ax: Axes,
    placements: list[Placement],
    *,
    height: float,
    alpha: float = 1.0,
    zorder: float = 3,
    xycoords: Any = "data",
    cache: dict[str, np.ndarray | None] | None = None,
    warn: bool = True,
) -> list[AnnotationBbox]:
    """``_draw_placements`` for ``place_images``: each image is read once; the points whose image cannot be read are
    skipped with one SdvplotWarning. ``cache`` holds images already read (``_read_images``); ``warn=False`` skips
    without warning, for a caller that already warned (plotnine reads and warns once per render, then draws panels)."""
    cache = {} if cache is None else cache
    unreadable = _read_images(placements, cache)
    if warn:
        _warn_skipped("whose image could not be read", unreadable)
    images = {url: img for url, img in cache.items() if img is not None}
    drawable = [p for p in placements if p.url in images]
    return _draw_placements(ax, drawable, height=height, alpha=alpha, zorder=zorder, xycoords=xycoords, images=images)


def add_images(
    target: Any,
    x: Any,
    y: Any,
    paths: Any,
    *,
    height: float = 0.1,
    alpha: float = 1,
    zorder: float = 3,
    transform: Any = None,
) -> Any:
    """Draw any image, by local path or URL, centred on each (x, y) point of a matplotlib or seaborn plot.

    The image counterpart of ``add_logos``, with the same sizing: ``height`` is a fraction of the Axes height, and
    each image keeps its aspect ratio. URLs are downloaded once and cached (like headshots); local files are read
    as they are. PNG, JPEG, GIF, WebP and the other formats Pillow reads work; SVG does not.

    Args:
        target: A matplotlib Axes, a Figure with one Axes, or a seaborn grid with one Axes (or a JointGrid).
        x: The points' x positions, in data coordinates (list, numpy array, or pandas/polars Series; read by position).
        y: The points' y positions, the same length as ``x``.
        paths: The image for each point (or one ``pathlib.Path`` for one point): a local path (str or
            ``pathlib.Path``), a ``file://`` URI or an https URL (http is refused). A null path draws nothing.
        height: The image height as a fraction of the Axes height, in (0, 1].
        alpha: Opacity, 0 to 1.
        zorder: matplotlib drawing order (3 draws above lines and markers).
        transform: The coordinates x and y are in, when not the Axes' data: a Cartopy CRS (required on a GeoAxes) or
            a matplotlib Transform such as ``ax.transAxes``.

    Returns:
        object: ``target`` itself, drawn on. Points whose image cannot be read (a missing file, a file that is not
        an image, a failed download) or whose x or y is missing are skipped, with one SdvplotWarning per reason.

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range.
        ValueError: If ``x``/``y``/``paths`` differ in length, the target has several Axes, or the target is a Cartopy
            GeoAxes and ``transform`` is None. (An image that cannot be read or downloaded is skipped with a warning,
            not raised.)
        UnsupportedTargetError: (a TypeError) If ``target`` is not a matplotlib Axes, a Figure or a seaborn grid.

    Example:
        ::

            import matplotlib.pyplot as plt
            from sdvplot.matplotlib import add_images

            fig, ax = plt.subplots()
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 10)
            add_images(ax, [3, 7], [5, 5], ["court.png", "https://www.python.org/static/img/python-logo.png"],
                       height=0.2)

    See Also:
        ggpath geom_from_path(): https://mrcaseb.github.io/ggpath/ ;
        sdvplotR: https://sdvplotR.sportsdataverse.org/
    """
    h, a = check_height(height), check_alpha(alpha)
    ax = _target_axes(target)
    _draw_images(ax, place_images(x, y, paths), height=h, alpha=a, zorder=zorder, xycoords=_xycoords(ax, transform))
    return target


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
    mark_type: AxisMarkType = "logo",
    id_system: str = "auto",
) -> Any:
    """Replace a team axis' tick labels with the teams' logos (or wordmarks), or a player axis' with headshots.

    Reads the axis' ticks and labels when called, so call it after setting the categories and limits. Labels that are
    not teams (or, with ``mark_type="headshot"``, not player ids with a headshot) stay as text, with one SdvplotWarning.

    Args:
        target: A matplotlib Axes, a Figure with one Axes, or a seaborn grid with one Axes.
        axis: "x" or "y".
        league: The SDV league key, e.g. "nfl".
        season: One season for every label.
        height: The image height as a fraction of the Axes height, in (0, 1].
        variant: "default", "dark", or a named variant from ``marks()``.
        mark_type: "logo", "wordmark" or "headshot". With "headshot" the labels are player ids (``id_system`` "espn",
            "gsis" or "league" as in ``headshot_url``, "auto" meaning "espn"; ``season`` is ignored), drawn at their
            own aspect.
        id_system: The id system of the labels; "auto" tries each in order.

    Returns:
        object: ``target`` itself, drawn on.

    Raises:
        InputError: (a ValueError) If ``height`` is out of range, ``league``, ``id_system``, ``mark_type`` or
            ``variant`` is unknown, ``season`` is not a year or is outside the seasons sdvplot knows for the league, or
            ``league`` has no ESPN headshots for ``mark_type="headshot"``.
        ValueError: If ``axis`` is not "x"/"y", or the target has several Axes.
        UnsupportedTargetError: (a TypeError) If ``target`` is not a matplotlib Axes, a Figure or a seaborn grid.
        OfflineError: If the logo manifest, a mark's image or a headshot is neither cached nor downloadable (a
            DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends
            a file that does not match the manifest's sha256, or one PIL cannot decode).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If the manifest's sha256 or extension for a mark would put the file outside
            the cache directory.
        OptionalDependencyError: If a mark is an SVG and the ``svg`` extra is not installed.

    Example:
        ::

            import matplotlib.pyplot as plt
            import sdvplot

            fig, ax = plt.subplots()
            ax.bar(["KC", "BUF", "BAL"], [12, 10, 9])
            sdvplot.axis_logos(ax, "x", league="nfl", height=0.08)

            # player headshots as the labels of a leaderboard (ESPN athlete ids)
            fig, ax = plt.subplots()
            ax.barh(["3139477", "3918298"], [0.31, 0.27])
            sdvplot.axis_logos(ax, "y", league="nfl", mark_type="headshot", height=0.2)

    See Also:
        sdvplotR element_sdv_logo(), scale_x_sdv_headshots(): https://sdvplotR.sportsdataverse.org/
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
    mark_type: AxisMarkType = "logo",
    id_system: str = "auto",
    warn: bool = True,
) -> Any:
    """axis_logos; ``warn=False`` skips the labels that are not teams without warning (plotnine warns once for every
    panel's labels, then draws each panel quietly)."""
    h = check_height(height)
    ax = _target_axes(target)
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
    images: dict[str, np.ndarray] = {}
    for p in placements:
        if p.url not in images:
            images[p.url] = _image(p)
    image_points = h * ax.bbox.height * 72 / ax.figure.dpi
    if axis == "y":  # left of the axis the widest image takes the room: its width, from its own aspect (a headshot is
        image_points *= max((im.shape[1] / im.shape[0] for im in images.values()), default=1.0)  # wider than tall)
    if tick is not None:  # keep the configured label pad, plus room for the images below/left of the tick marks
        which.set_tick_params(pad=tick.get_pad() + 2 + image_points)
    for p in placements:
        loc = p.x if axis == "x" else p.y
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
            xybox=(-_TITLE_GAP if left else _TITLE_GAP, 0),
            boxcoords="offset points",
            box_alignment=(1.0, 0.5) if left else (0.0, 0.5),
            frameon=False,
            pad=0,
            annotation_clip=False,
            zorder=text.get_zorder() - 0.01,  # drawn just before the text, so the text draws with this draw's shift
        )
        self._sdv_text, self._sdv_left, self._sdv_align, self._sdv_shift = text, left, align, Affine2D()
        self._sdv_base: Transform | None = None
        self._sdv_shifted: Transform | None = None
        self._shift_text()

    def _shift_text(self) -> None:
        """Compose the shift onto the text's transform, and again whenever something replaced that transform
        (``Axes.set_title`` resets all three Axes titles' transforms on every call)."""
        if self._sdv_text.get_transform() is not self._sdv_shifted:
            self._sdv_base = self._sdv_text.get_transform()
            self._sdv_shifted = self._sdv_base + self._sdv_shift
            self._sdv_text.set_transform(self._sdv_shifted)

    def update_positions(self, renderer: Any) -> None:
        self._shift_text()
        room = self.offsetbox.get_bbox(renderer).width + renderer.points_to_pixels(_TITLE_GAP)
        rel = self._sdv_align()
        self._sdv_shift.clear().translate((1 - rel) * room if self._sdv_left else -rel * room, 0)
        super().update_positions(renderer)

    def remove(self) -> None:
        """Remove the image and give the title text back its unshifted transform."""
        if self._sdv_base is not None and self._sdv_text.get_transform() is self._sdv_shifted:
            self._sdv_text.set_transform(self._sdv_base)
        super().remove()


def _check_title_image(side: Any, height: Any) -> float:
    """``height`` as a float, or ValueError unless ``side`` is "left"/"right" (InputError unless ``height`` is a number
    of points of at least 1)."""
    if side not in ("left", "right"):
        raise ValueError(f"side must be 'left' or 'right', got {side!r}")
    if not _real(height) or height < 1:
        raise InputError(f"height is the image height in points (1/72 inch), at least 1, got {height!r}")
    return float(height)


def _title_source(image: Any, league: str | None, season: Any) -> tuple[np.ndarray, str] | None:
    """The image to put beside a title, plus what it was: a team's logo when ``league`` is given (None, with one
    SdvplotWarning, when the team does not resolve or has no logo; a failed download raises, as in add_logos), else
    the image at a URL or local path (None, with one SdvplotWarning, when it cannot be read)."""
    if league is not None:
        img = logo_image(image, league, season=season, size=_MAX_IMAGE_HEIGHT)  # a title image is points tall
        return None if img is None else (_rgba_array(img), str(image))
    source = str(image)
    try:
        return _rgba_array(load_path_image(source)), source
    except (OSError, ValueError, OfflineError) as e:  # missing file, not an image, failed download (as _read_images)
        warn(f"title_image: could not read {source!r} ({e}); drawn without it")
        return None


def _add_title_image(
    container: Any,
    text: Text,
    source: tuple[np.ndarray, str] | None,
    side: str,
    height: float,
    align: Callable[[], float],
) -> AnnotationBbox | None:
    """Draw ``source`` (from _title_source) beside ``text``, an Axes title or a Figure's suptitle/text, replacing any
    image already beside that text; None draws nothing new."""
    for old in [a for a in container.artists if isinstance(a, _TitleImage) and a._sdv_text is text]:
        old.remove()
    if source is None:
        return None
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
            (https; http is refused) or a local file path.
        title: The title text.
        league: The SDV league key, e.g. "nfl"; None reads ``image`` as a URL or path.
        season: One season, to pick the team's logo for that era.
        side: "left" or "right" of the title text.
        height: The image height in points (1/72 inch), at any dpi. The title keeps its own line height, so an image
            much taller than the text needs room: ``pad=`` on an Axes title, ``y=`` on a Figure's suptitle.
        **text_kw: Passed to ``Axes.set_title`` (``loc``, ``fontsize``, ``pad``, ...) or ``Figure.suptitle``.

    Returns:
        object: ``target`` itself, titled. Calling it again on the same title replaces the image. An image by URL or
        path that cannot be read gives one SdvplotWarning and the title without it.

    Raises:
        TypeError: If ``league`` is given and ``image`` is not one team.
        InputError: (a ValueError) If ``height`` is not a number of points of at least 1, or ``league`` is given and it
            is unknown or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If ``side`` is not "left"/"right", or the target has several Axes.
        UnsupportedTargetError: (a TypeError) If ``target`` is not a matplotlib Axes, a Figure or a seaborn grid.
        OfflineError: If ``league`` is given and the team's logo (or the logo manifest) is neither cached nor
            downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError
            when it sends a file that does not match the manifest's sha256, or one PIL cannot decode). An image by URL
            or path that cannot be read is skipped with a warning instead.
        UnsafeDownloadError: (an OSError) If ``league`` is given and a download is refused: larger than the byte cap,
            past the deadline, or redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``league`` is given and the manifest's sha256 or extension for the logo
            would put the file outside the cache directory.
        OptionalDependencyError: If ``league`` is given, the logo is an SVG and the ``svg`` extra is not installed.

    Example:
        ::

            import matplotlib.pyplot as plt
            from sdvplot.matplotlib import title_image

            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [3, 1, 2])
            title_image(ax, "KC", "Kansas City Chiefs Analysis", league="nfl", height=20)

            # A Figure's suptitle, the image on the right:
            title_image(fig, "https://example.com/banner.png", "Week 1", side="right")

    See Also:
        sdvplotR ggtitle_image(): https://sdvplotR.sportsdataverse.org/reference/ggtitle_image.html ;
        sdvplot.plotnine.title_image: the same for plotnine.
    """
    h = _check_title_image(side, height)
    source = _title_source(image, league, season)
    if isinstance(target, Figure):
        container: Any = target
        text = target.suptitle(title or " ", **text_kw)  # a blank title still gives the image a line to sit on
    else:
        container = _target_axes(target)
        text = container.set_title(title or " ", **text_kw)
    _add_title_image(container, text, source, side, h, lambda: _align(text.get_horizontalalignment()))
    return target


def team_tiers(
    data: Any,
    league: str,
    *,
    title: str | None = None,
    subtitle: str | None = _tiers.SUBTITLE,
    caption: str | None = None,
    tier_desc: dict[Any, str] | None = None,
    presort: bool = False,
    alpha: float = 0.8,
    height: float | None = None,
    no_line_below_tier: Any = None,
    devel: bool = False,
    theme: Literal["dark", "light"] = "dark",
    variant: str = "auto",
) -> Figure:
    """A tier list: each team's logo in its tier's row, tier 1 on top, on a dark (sdvplotR) or light theme.

    Args:
        data: A pandas or polars DataFrame with ``tier_no`` (1 is the top tier) and ``team`` (any id system
            ``resolve()`` understands), and optionally ``tier_rank``, the position within the tier; without it, teams
            keep their order in ``data``.
        league: The SDV league key, e.g. "nfl".
        title: The title; None gives "{LEAGUE} Team Tiers", "" none.
        subtitle: The subtitle; None or "" for none.
        caption: The caption, bottom right; None for none.
        tier_desc: Each tier's label, keyed by tier number; None gives sdvplotR's (1 "Elite" ... 5 "What are they
            doing?"). Labels wrap at 15 characters; a tier without one gets none.
        presort: Sort teams alphabetically within each tier (ignores ``tier_rank``).
        alpha: Logo opacity, 0 to 1.
        height: Logo height as a fraction of the panel height; None gives 0.1, about the largest height at
            which 32 logos in 5 tiers (7, 7, 6, 6, 6) neither overlap nor leave the panel at the default 6.4 x 4.8 in
            figure.
        no_line_below_tier: A tier number, or several, with no separator line below.
        devel: Draw each team as text instead of its logo (fast, and needs no download).
        theme: "dark" (sdvplotR's: a near-black background) or "light" (white).
        variant: The logo variant: "auto" (the default) draws the archive's "dark" variant, a mark made for dark
            backgrounds, on the dark theme and "default" on the light one; a team with no dark mark draws its
            default one, with no warning. Any other value ("default", "dark" or a named variant from ``marks()``)
            is drawn on either theme, as ``add_logos`` draws it: ``variant="default"`` keeps the default logos on
            the dark theme, as sdvplotR and sdvplot 0.1.0 draw them.

    Returns:
        matplotlib.figure.Figure: A new figure with one Axes; a team that does not resolve is skipped with one
        SdvplotWarning, keeping its slot.

    Raises:
        TypeError: If ``data`` is not a DataFrame, or ``tier_no``/``tier_rank`` hold non-numbers.
        InputError: (a ValueError) If ``height``/``alpha`` is out of range, or ``league`` is unknown; unless
            ``devel=True``, if ``variant`` is a name no mark in the archive has.
        ValueError: If ``data`` lacks ``tier_no`` or ``team``, has no row with a tier, or ``theme`` is not "dark" or
            "light".
        OfflineError: Unless ``devel=True``, if the logo manifest or a mark's image is neither cached nor downloadable
            (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it
            sends a file that does not match the manifest's sha256, or one PIL cannot decode).
        UnsafeDownloadError: (an OSError) Unless ``devel=True``, if a download is refused: larger than the byte cap,
            past the deadline, or redirected away from https.
        UnsafeCachePathError: (a ValueError) Unless ``devel=True``, if the manifest's sha256 or extension for a mark
            would put the file outside the cache directory.
        OptionalDependencyError: Unless ``devel=True``, if a logo is an SVG and the ``svg`` extra is not installed.

    Example:
        ::

            import pandas as pd
            from sdvplot.matplotlib import team_tiers

            df = pd.DataFrame({"tier_no": [1, 1, 2, 3], "team": ["KC", "BUF", "BAL", "NYJ"]})
            fig = team_tiers(df, "nfl")

            # Draft it as text first, then add logos:
            fig = team_tiers(df, "nfl", devel=True, no_line_below_tier=1)

            # A white background:
            fig = team_tiers(df, "cfb", theme="light")

            # The default logos on the dark background, as sdvplotR draws them:
            fig = team_tiers(df, "nfl", variant="default")

    See Also:
        sdvplotR sdv_team_tiers(): https://sdvplotR.sportsdataverse.org/reference/sdv_team_tiers.html ;
        sdvplot.plotnine.team_tiers: the same as a plotnine ggplot.
    """
    import matplotlib.pyplot as plt

    t = _tiers.prepare(
        data, league, title=title, subtitle=subtitle, caption=caption, tier_desc=tier_desc, presort=presort,
        alpha=alpha, height=height, no_line_below_tier=no_line_below_tier, theme=theme, variant=variant,
    )  # fmt: skip
    fig, ax = plt.subplots(layout="constrained", facecolor=t.bg)
    ax.set_facecolor(t.bg)
    for y in t.lines:
        ax.axhline(y, color=t.line_color, linewidth=0.8)
    ax.set_xlim(t.xlim)
    ax.set_ylim(t.ylim[1], t.ylim[0])  # tier 1 on top
    ax.set_xticks([])
    ax.set_yticks(t.breaks, t.break_labels, color=t.text, fontweight="bold")
    ax.tick_params(length=0)
    ax.spines[:].set_visible(False)
    if devel:
        for x, y, label in zip(t.x, t.y, t.labels, strict=True):
            ax.text(x, y, label, color=t.text, ha="center", va="center")
    else:
        placements = place(t.x, t.y, t.team_ids, league=league, variant=t.variant, id_system="team_id")
        _draw_placements(ax, placements, height=t.height, alpha=t.alpha)
    anchor: Text | None = None  # the subtitle sits on the panel, the title on the subtitle, both left-aligned
    size = ax.title.get_fontproperties().get_size_in_points()
    styles: list[tuple[str | None, dict[str, Any]]] = [
        (t.subtitle, {"color": t.muted, "fontsize": size}),
        (t.title, {"color": t.text, "fontweight": "bold", "fontsize": 1.2 * size}),  # sdvplotR: rel(1.2)
    ]
    for text, style in styles:
        if not text:
            continue
        if anchor is None:
            anchor = ax.set_title(text, loc="left", **style)
        else:
            anchor = ax.annotate(text, (0, 1), xycoords=anchor, xytext=(0, 4), textcoords="offset points",
                                 va="bottom", **style)  # fmt: skip
    if t.caption:
        ax.annotate(t.caption, (1, 0), xycoords="axes fraction", xytext=(0, -6), textcoords="offset points",
                    ha="right", va="top", color=t.muted, fontsize="small")  # fmt: skip
    return fig


def _drawn_title_images(target: Any) -> list[tuple[str, str]]:
    """Test hook: (side, image) for each title image on a Figure or an Axes, image being the team or URL/path given."""
    container = target if isinstance(target, Figure) else _target_axes(target)
    return [a._sdvplot_title_image for a in container.artists if hasattr(a, "_sdvplot_title_image")]


def _drawn_boxes(target: Any, tag: str) -> tuple[Axes, list[Any]]:
    """The Axes and its sdvplot image boxes tagged ``tag``, after a draw. A layout engine (constrained, tight) resizes
    the Axes on draw, so an image sized before that only shows the wrong fraction afterwards."""
    ax = _target_axes(target)
    ax.figure.canvas.draw()
    return ax, [a for a in ax.artists if hasattr(a, tag)]


def _drawn_height(ax: Axes, box: Any) -> float:
    """The height the box's image is drawn at, measured from its extent, as a fraction of the Axes height."""
    return float(box.offsetbox.get_window_extent().height / ax.bbox.height)


def _drawn_marks(target: Any) -> list[tuple[Any, ...]]:
    """Test hook: (team_id, x, y, height, url) for each image add_logos/add_wordmarks/add_headshots drew; height is
    measured from the drawn image."""
    ax, boxes = _drawn_boxes(target, "_sdvplot_mark")
    return [(*b._sdvplot_mark[:3], _drawn_height(ax, b), b._sdvplot_mark[3]) for b in boxes]


def _drawn_axis_marks(target: Any, axis: str) -> list[tuple[str, float, float]]:
    """Test hook: (team_id, tick position, height) for each axis image on ``axis``, in tick order; height is measured
    from the drawn image."""
    ax, boxes = _drawn_boxes(target, "_sdvplot_axis_mark")
    marks = [(b._sdvplot_axis_mark, _drawn_height(ax, b)) for b in boxes]
    return sorted(((team_id, loc, h) for (which, team_id, loc), h in marks if which == axis), key=lambda m: m[1])


def _visible_axis_labels(target: Any, axis: str) -> list[str]:
    """Test hook: the tick labels on ``axis`` still shown as text."""
    _, labels = _ticks(_axis(_target_axes(target), axis))
    return [lab for lab in labels if lab]

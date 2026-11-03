"""The HoloViews adapter: a Bokeh plot hook that draws the marks through the Bokeh adapter when the element renders.

The marks are resolved (and any warning raised) when ``add_logos`` is called; the hook only draws them on
``plot.state``, the Bokeh figure. Only the Bokeh backend is supported.
"""

from __future__ import annotations

from typing import Any

from sdvplot._errors import UnsupportedTargetError, requires_extra

with requires_extra("holoviews"):
    import holoviews as hv

from sdvplot import bokeh as _bokeh
from sdvplot._bins import _cells, _values
from sdvplot._placement import check_alpha, check_height, place
from sdvplot._types import BinShape, BinValue
from sdvplot._web import image_sources, present

_SUPPORTS_AXIS_LOGOS = False

__all__ = ["add_bins", "add_headshots", "add_logos", "add_wordmarks", "axis_logos"]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)


def _require_bokeh() -> None:
    import holoviews.plotting.bokeh  # noqa: F401  registers the Bokeh backend; it becomes current if none was loaded

    if hv.Store.current_backend != "bokeh":
        raise TypeError(
            f"sdvplot.holoviews draws through the Bokeh backend, but the current backend is "
            f"{hv.Store.current_backend!r}; call hv.extension('bokeh') or hv.output(backend='bokeh') first"
        )


def _add(
    element: Any,
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
    embed: bool,
    id_system: str,
) -> Any:
    h, a = check_height(height), check_alpha(alpha)
    if not isinstance(element, hv.core.Dimensioned):
        raise UnsupportedTargetError(
            f"sdvplot.holoviews draws on a HoloViews element or overlay, got {type(element).__name__}"
        )
    _require_bokeh()
    placements = place(x, y, teams, league=league, season=season, kind=kind, variant=variant, id_system=id_system)
    placements = present(placements, embed=embed)
    sources = image_sources(placements, embed=embed)

    def hook(plot: Any, _element: Any) -> None:
        _bokeh._draw(plot.state, placements, sources, kind=kind, height=h, alpha=a)

    hooks = hv.Store.lookup_options("bokeh", element, "plot").kwargs.get("hooks", [])
    return element.opts(hooks=[*hooks, hook], clone=True, backend="bokeh")


def add_logos(
    element: Any,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = "default",
    embed: bool = False,
    id_system: str = "auto",
) -> Any:
    """Draw each team's logo centred on its (x, y) point of a HoloViews element (Bokeh backend).

    Returns a copy of the element with a Bokeh plot hook; the logos appear when it renders (``hv.render``, a notebook,
    ``hv.save``). Sizing is the Bokeh adapter's: a fraction of the plot's ``frame_height`` when set, else its height;
    a responsive plot has neither, so give it a ``frame_height`` (without one, HoloViews logs the hook's ValueError and
    draws no marks).

    Args:
        element: A HoloViews element or overlay (``hv.Scatter``, ``hv.Points * hv.Curve``, ...).
        x: The points' x positions, in the element's x values.
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point, to pick each team's mark for that era.
        height: The logo height as a fraction of the plot's reference height, in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        object: A copy of ``element`` with the drawing hook added to its existing hooks.

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant``
            is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If the inputs differ in length; when the plot renders, if its figure has no pixel height (no
            ``frame_height`` or ``height`` option).
        TypeError: If the current HoloViews backend is not Bokeh.
        UnsupportedTargetError: (a TypeError) If ``element`` is not a HoloViews element or overlay.
        OfflineError: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a
            DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a
            file that does not match the manifest's sha256).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would
            put the file outside the cache directory.

    Example:
        ::

            import holoviews as hv
            import sdvplot

            hv.extension("bokeh")
            points = hv.Scatter([(10, -3), (20, -7)]).opts(frame_height=300)
            points = sdvplot.add_logos(points, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)

    See Also:
        sdvplotR geom_nfl_logos(): https://sdvplotR.sportsdataverse.org/ ;
        HoloViews plot hooks: https://holoviews.org/user_guide/Customizing_Plots.html
    """
    return _add(
        element, x, y, teams, kind="logo", league=league, season=season, height=height, alpha=alpha,
        variant=variant, embed=embed, id_system=id_system,
    )  # fmt: skip


def add_wordmarks(
    element: Any,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = "default",
    embed: bool = False,
    id_system: str = "auto",
) -> Any:
    """Draw each team's wordmark centred on its (x, y) point of a HoloViews element (Bokeh backend).

    Args:
        element: A HoloViews element or overlay.
        x: The points' x positions, in the element's x values.
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point.
        height: The wordmark height as a fraction of the plot's reference height, in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        object: A copy of ``element`` with the drawing hook added.

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant``
            is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If the inputs differ in length; when the plot renders, if its figure has no pixel height (no
            ``frame_height`` or ``height`` option).
        TypeError: If the current HoloViews backend is not Bokeh.
        UnsupportedTargetError: (a TypeError) If ``element`` is not a HoloViews element or overlay.
        OfflineError: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a
            DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a
            file that does not match the manifest's sha256).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would
            put the file outside the cache directory.

    Example:
        ::

            import holoviews as hv
            import sdvplot

            hv.extension("bokeh")
            bars = hv.Bars([("KC", 12), ("BUF", 10)])
            bars = sdvplot.add_wordmarks(bars, ["KC", "BUF"], [12, 10], ["KC", "BUF"], league="nfl", height=0.06)

    See Also:
        sdvplotR geom_nfl_wordmarks(): https://sdvplotR.sportsdataverse.org/
    """
    return _add(
        element, x, y, teams, kind="wordmark", league=league, season=season, height=height, alpha=alpha,
        variant=variant, embed=embed, id_system=id_system,
    )  # fmt: skip


def add_headshots(
    element: Any,
    x: Any,
    y: Any,
    players: Any,
    *,
    league: str,
    height: float = 0.1,
    alpha: float = 1,
    embed: bool = False,
    id_system: str = "espn",
) -> Any:
    """Draw each player's headshot centred on its (x, y) point of a HoloViews element (Bokeh backend).

    Args:
        element: A HoloViews element or overlay.
        x: The points' x positions, in the element's x values.
        y: The points' y positions, the same length as ``x``.
        players: The player id for each point.
        league: The SDV league key, e.g. "nfl".
        height: The headshot height as a fraction of the plot's reference height, in (0, 1].
        alpha: Opacity, 0 to 1.
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and
            WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``.

    Returns:
        object: A copy of ``element`` with the drawing hook added.

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league`` has no ESPN headshots, or
            ``id_system`` is not valid for ``league``.
        ValueError: If the inputs differ in length; when the plot renders, if its figure has no pixel height (no
            ``frame_height`` or ``height`` option).
        TypeError: If the current HoloViews backend is not Bokeh.
        UnsupportedTargetError: (a TypeError) If ``element`` is not a HoloViews element or overlay.
        OfflineError: If the nflverse player table (``id_system="gsis"``), or with ``embed=True`` a headshot, is neither
            cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.

    Example:
        ::

            import holoviews as hv
            import sdvplot

            hv.extension("bokeh")
            sdvplot.add_headshots(hv.Scatter([(0.5, 0.5)]), [0.5], [0.5], ["3139477"], league="nfl", height=0.2)

    See Also:
        sdvplotR geom_nfl_headshots(): https://sdvplotR.sportsdataverse.org/
    """
    return _add(
        element, x, y, players, kind="headshot", league=league, season=None, height=height, alpha=alpha,
        variant="default", embed=embed, id_system=id_system,
    )  # fmt: skip


def axis_logos(target: Any, axis: str, **kwargs: Any) -> Any:
    """Not supported on HoloViews (it draws through Bokeh, which has no axis logos yet).

    Args:
        target: A HoloViews element.
        axis: "x" or "y".
        **kwargs: Ignored.

    Returns:
        object: Never returns.

    Raises:
        UnsupportedTargetError: (a TypeError) Always. Draw the logos inside the plot with ``add_logos``, or use the
            matplotlib, Plotly or Altair adapter for axis logos.

    Example:
        ::

            import holoviews as hv
            import sdvplot

            try:
                sdvplot.axis_logos(hv.Bars([("KC", 12)]), "x", league="nfl")
            except TypeError:
                pass   # raised: HoloViews has no axis logos yet

    See Also:
        sdvplotR element_sdv_logo(): https://sdvplotR.sportsdataverse.org/
    """
    raise UnsupportedTargetError(
        "HoloViews has no axis logos yet (its Bokeh plots cannot hold them): draw them inside the plot with "
        "add_logos, or use matplotlib, Plotly or Altair for axis logos"
    )


def add_bins(
    target: Any,
    x: Any,
    y: Any,
    *,
    shape: BinShape = "hex",
    radius: float | None = None,
    side: float | None = None,
    equal_area: bool = False,
    ids: Any = None,
    weights: Any = None,
    origin: tuple[float, float] = (0.0, 0.0),
    value: BinValue = "count",
    fill: float | None = None,
    min_count: int = 1,
    palette: Any = "Viridis256",
    alpha: float = 1.0,
    link: Any = None,
) -> Any:
    """Hexagonal or square bins, colored by count or weight, on a HoloViews element: the Bokeh adapter's ``add_bins``.

    A Bokeh plot hook draws the cells with ``sdvplot.bokeh.add_bins`` when the element renders (one ``patches`` glyph
    named ``"sdvplot_bins"``, with its ``ColumnDataSource`` of ``bin_id``, ``count``, ``weight``, ``point_ids`` and
    ``rows``), so the cells, ids and colors are the Bokeh adapter's. Only the Bokeh backend is supported.

    Linking: as Bokeh's, in the browser with no server. Pass the points element of the plot (e.g. the ``hv.Points`` in
    ``target``, or ``target`` itself) as ``link``: its rendered ``ColumnDataSource`` is linked both ways, so selecting
    cells (add ``tools=["tap", "box_select"]``) selects their points and selecting points selects their cells. Its rows
    must be the points of ``x`` and ``y``, in that order.

    Args:
        target: A HoloViews element or overlay.
        x: The points' x values, in data units.
        y: The points' y values.
        shape: ``"hex"`` (the default) or ``"square"``.
        radius: The hexagon's circumradius, in data units; for squares, with ``equal_area=True``.
        side: The square's side (``shape="square"``).
        equal_area: Squares of a radius-``radius`` hexagon's area.
        ids: Optional link ids, one per point (default the row number); see ``sdvplot.hexbin``.
        weights: Optional non-negative weights, one per point (see ``sdvplot.hexbin``): each bin's ``weight``.
        origin: The point a cell centre falls on (default ``(0.0, 0.0)``): a hoop-centred lattice, origin = the
            basket's coordinates.
        value: What the fill encodes: ``"count"`` (the default, the points in each cell) or ``"weight"`` (the sum of
            their ``weights``).
        fill: The drawn cell's size as a fraction of the lattice cell, in (0, 1]: default 0.88 for squares (a gap, so
            they do not touch edge to edge) and 1.0 for hexagons (the tiled hexbin look).
        min_count: Cells with fewer points are not drawn (default 1, every cell). ``min_count=2`` suits shot charts:
            single attempts are not drawn. ``sdvplot.hexbin`` / ``squarebin`` still return every cell.
        palette: A Bokeh palette name or list of colors (default ``"Viridis256"``), lowest to highest value.
        alpha: The cells' fill opacity, 0 to 1.
        link: Optional points element of ``target`` (or ``target`` itself) to link selections with.

    Returns:
        element: A clone of ``target`` with the hook added.

    Raises:
        InputError: If the lattice options are not valid (see ``sdvplot.binner``), ``value`` is not "count" or
            "weight", ``fill`` is not in (0, 1], ``min_count`` is not a whole number >= 1, or ``alpha`` is outside
            [0, 1].
        UnsupportedTargetError: If ``target`` is not a HoloViews element or overlay.
        TypeError: If the current HoloViews backend is not Bokeh.
        ValueError: If ``x``, ``y``, ``ids`` and ``weights`` differ in length, or ``link`` is not an element of
            ``target``.

    Example:
        ::

            import holoviews as hv
            from sdvplot.holoviews import add_bins

            hv.extension("bokeh")
            # three Brooklyn shots of 2025-26, legacy tenths of a foot (sportsdataverse-data nba_stats_shots)
            x, y = [0, -1, -44], [0, 7, 252]
            shots = hv.Points({"x": x, "y": y}, ["x", "y"]).opts(tools=["tap", "box_select"])
            plot = add_bins(shots, x, y, shape="square", side=15, alpha=0.6, link=shots)

    See Also:
        sdvplot.bokeh.add_bins: https://sdvplot.sportsdataverse.org/docs/reference/bokeh ;
        HoloViews hooks: https://holoviews.org/user_guide/Customizing_Plots.html
    """
    if not isinstance(target, hv.core.Dimensioned):
        raise UnsupportedTargetError(
            f"sdvplot.holoviews draws on a HoloViews element or overlay, got {type(target).__name__}"
        )
    _require_bokeh()
    check_alpha(alpha)
    # checked now: a plot hook's errors only become HoloViews warnings at render
    bins, _ = _cells(x, y, shape=shape, radius=radius, side=side, equal_area=equal_area, ids=ids, weights=weights,
                     origin=origin, fill=fill, min_count=min_count)  # fmt: skip
    _values(bins, value)
    data = getattr(link, "data", object())
    if link is not None and not any(
        getattr(e, "data", None) is data for e in target.traverse(lambda e: e)
    ):  # a clone keeps its data object, so the rendered element of the plot is found by it
        raise ValueError("link must be an element of target (its points), e.g. the hv.Points it overlays")
    options = {"shape": shape, "radius": radius, "side": side, "equal_area": equal_area, "ids": ids,
               "weights": weights, "origin": origin, "value": value, "fill": fill, "min_count": min_count,
               "palette": palette, "alpha": alpha}  # fmt: skip

    def hook(plot: Any, _element: Any) -> None:
        source = None
        if link is not None:
            source = next(
                p.handles["source"]
                for p in plot.traverse(lambda p: p, [lambda p: "source" in getattr(p, "handles", {})])
                if p.current_frame is not None and p.current_frame.data is data
            )
        _bokeh.add_bins(plot.state, x, y, link=source, **options)

    hooks = hv.Store.lookup_options("bokeh", target, "plot").kwargs.get("hooks", [])
    return target.opts(hooks=[*hooks, hook], clone=True, backend="bokeh")


def _drawn_marks(target: Any) -> list[tuple[Any, ...]]:
    """Test hook: render the element with Bokeh and read the marks the hook drew."""
    return _bokeh._drawn_marks(hv.render(target, backend="bokeh"))


def _drawn_bins(target: Any) -> list[tuple[str, float, float, int, tuple[str, ...]]]:
    """Test hook: render the element with Bokeh and read the cells add_bins' hook drew."""
    return _bokeh._drawn_bins(hv.render(target, backend="bokeh"))

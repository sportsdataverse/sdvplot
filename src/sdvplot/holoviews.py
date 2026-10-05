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
from sdvplot._placement import check_alpha, check_height, place
from sdvplot._web import image_sources

_SUPPORTS_AXIS_LOGOS = False

__all__ = ["add_headshots", "add_logos", "add_wordmarks", "axis_logos"]


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
        ValueError: If ``height`` or ``alpha`` is out of range, or the inputs differ in length.
        TypeError: If ``element`` is not a HoloViews object, or the current backend is not Bokeh.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

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
        ValueError: If ``height`` or ``alpha`` is out of range, or the inputs differ in length.
        TypeError: If ``element`` is not a HoloViews object, or the current backend is not Bokeh.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

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
        id_system: "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``.

    Returns:
        object: A copy of ``element`` with the drawing hook added.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, or the inputs differ in length.
        TypeError: If ``element`` is not a HoloViews object, or the current backend is not Bokeh.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

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
        TypeError: Always. Draw the logos inside the plot with ``add_logos``, or use the matplotlib, Plotly or Altair
            adapter for axis logos.

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


def _drawn_marks(target: Any) -> list[tuple[Any, ...]]:
    """Test hook: render the element with Bokeh and read the marks the hook drew."""
    return _bokeh._drawn_marks(hv.render(target, backend="bokeh"))

"""The Bokeh adapter: logos, wordmarks and headshots as one ``image_url`` glyph per call on a Bokeh figure.

Images are sized in screen pixels, so they keep their size when the user zooms: ``height`` times the reference height,
which is the figure's ``frame_height`` (the plot area) when set, else its ``height`` (the whole canvas: set
``frame_height`` for exact sizing). Factor (categorical) and datetime axes work natively, because ``x``/``y`` hold the
caller's own values. HoloViews draws through ``_draw`` too.
"""

from __future__ import annotations

from typing import Any

from bokeh.models import ColumnDataSource

from sdvplot._errors import UnsupportedTargetError
from sdvplot._placement import Placement, check_alpha, check_height, place
from sdvplot._web import aspect, image_sources

_SUPPORTS_AXIS_LOGOS = False

__all__ = ["add_headshots", "add_logos", "add_wordmarks", "axis_logos"]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)


def _figure(target: Any) -> Any:
    if not hasattr(target, "image_url") or not hasattr(target, "frame_height"):
        raise UnsupportedTargetError(f"sdvplot.bokeh draws on a bokeh.plotting figure, got {type(target).__name__}")
    return target


def _reference_height(fig: Any) -> float:
    """The pixel height ``height`` is a fraction of: ``frame_height`` when set, else the figure's ``height``."""
    h = fig.frame_height or fig.height
    if not h:  # a responsive figure (e.g. a HoloViews plot with responsive=True) has neither
        raise ValueError(
            "sdvplot sizes images from the figure's pixel height, but it has none; set frame_height (or height), "
            "e.g. figure(frame_height=400) or .opts(frame_height=400) in HoloViews"
        )
    return float(h)


def _draw(fig: Any, placements: list[Placement], sources: list[str], *, kind: str, height: float, alpha: float) -> Any:
    """One ``image_url`` renderer named ``sdvplot_<kind>`` with every placement, centred on its (x, y)."""
    if not placements:
        return None
    h = height * _reference_height(fig)
    data = {
        "url": sources,
        "x": [p.x for p in placements],
        "y": [p.y for p in placements],
        "w": [h * aspect(p) for p in placements],
        "h": [h] * len(placements),
        "team_id": [p.team_id for p in placements],
    }
    return fig.image_url(
        url="url", x="x", y="y", w="w", h="h", w_units="screen", h_units="screen", anchor="center",
        global_alpha=alpha, source=ColumnDataSource(data), name=f"sdvplot_{kind}",
    )  # fmt: skip


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
    embed: bool,
    id_system: str,
) -> Any:
    h, a = check_height(height), check_alpha(alpha)
    fig = _figure(target)
    placements = place(x, y, teams, league=league, season=season, kind=kind, variant=variant, id_system=id_system)
    _draw(fig, placements, image_sources(placements, embed=embed), kind=kind, height=h, alpha=a)
    return fig


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
    embed: bool = False,
    id_system: str = "auto",
) -> Any:
    """Draw each team's logo centred on its (x, y) point of a Bokeh figure.

    The logos are sized in screen pixels, so they keep their size when the user zooms. ``height`` is a fraction of
    the figure's ``frame_height`` (the plot area) when it is set, else of its ``height`` (the whole canvas, a little
    taller than the plot area): set ``frame_height`` for the same sizing as the other libraries.

    Args:
        target: A ``bokeh.plotting.figure``.
        x: The points' x positions, in the figure's x values (numbers, factors or datetimes).
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point, to pick each team's mark for that era.
        height: The logo height as a fraction of the reference height, in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        embed: Inline each image as a data URI (HTML that renders offline) instead of linking its URL.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        object: ``target`` itself, with one ``image_url`` renderer named ``sdvplot_logo`` added.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or the figure has no
            pixel height (neither ``frame_height`` nor ``height`` is set).
        TypeError: If ``target`` is not a Bokeh figure.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

    Example:
        ::

            from bokeh.plotting import figure
            import sdvplot

            p = figure(frame_width=400, frame_height=300)
            p.scatter([10, 20], [-3, -7])
            sdvplot.add_logos(p, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)

    See Also:
        sdvplotR geom_nfl_logos(): https://sdvplotR.sportsdataverse.org/ ;
        Bokeh ImageURL: https://docs.bokeh.org/en/latest/docs/reference/models/glyphs/image_url.html
    """
    return _add(
        target, x, y, teams, kind="logo", league=league, season=season, height=height, alpha=alpha,
        variant=variant, embed=embed, id_system=id_system,
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
    embed: bool = False,
    id_system: str = "auto",
) -> Any:
    """Draw each team's wordmark centred on its (x, y) point of a Bokeh figure.

    Args:
        target: A ``bokeh.plotting.figure``.
        x: The points' x positions, in the figure's x values.
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point.
        height: The wordmark height as a fraction of the reference height (see ``add_logos``), in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        object: ``target`` itself, with one renderer named ``sdvplot_wordmark`` added.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or the figure has no
            pixel height (neither ``frame_height`` nor ``height`` is set).
        TypeError: If ``target`` is not a Bokeh figure.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

    Example:
        ::

            from bokeh.plotting import figure
            import sdvplot

            p = figure(x_range=["KC", "BUF"], frame_height=300)
            p.vbar(x=["KC", "BUF"], top=[12, 10], width=0.8)
            sdvplot.add_wordmarks(p, ["KC", "BUF"], [12, 10], ["KC", "BUF"], league="nfl", height=0.06)

    See Also:
        sdvplotR geom_nfl_wordmarks(): https://sdvplotR.sportsdataverse.org/
    """
    return _add(
        target, x, y, teams, kind="wordmark", league=league, season=season, height=height, alpha=alpha,
        variant=variant, embed=embed, id_system=id_system,
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
    embed: bool = False,
    id_system: str = "espn",
) -> Any:
    """Draw each player's headshot centred on its (x, y) point of a Bokeh figure.

    Args:
        target: A ``bokeh.plotting.figure``.
        x: The points' x positions, in the figure's x values.
        y: The points' y positions, the same length as ``x``.
        players: The player id for each point.
        league: The SDV league key, e.g. "nfl".
        height: The headshot height as a fraction of the reference height (see ``add_logos``), in (0, 1].
        alpha: Opacity, 0 to 1.
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``.

    Returns:
        object: ``target`` itself, with one renderer named ``sdvplot_headshot`` added.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or the figure has no
            pixel height (neither ``frame_height`` nor ``height`` is set).
        TypeError: If ``target`` is not a Bokeh figure.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

    Example:
        ::

            from bokeh.plotting import figure
            import sdvplot

            p = figure(frame_height=300)
            sdvplot.add_headshots(p, [0.5], [0.5], ["3139477"], league="nfl", height=0.2)

    See Also:
        sdvplotR geom_nfl_headshots(): https://sdvplotR.sportsdataverse.org/
    """
    return _add(
        target, x, y, players, kind="headshot", league=league, season=None, height=height, alpha=alpha,
        variant="default", embed=embed, id_system=id_system,
    )  # fmt: skip


def axis_logos(target: Any, axis: str, **kwargs: Any) -> Any:
    """Not supported on Bokeh: Bokeh glyphs cannot sit outside the plot frame at a fixed pixel offset.

    Args:
        target: A Bokeh figure.
        axis: "x" or "y".
        **kwargs: Ignored.

    Returns:
        object: Never returns.

    Raises:
        TypeError: Always. Draw the logos inside the plot with ``add_logos`` at a y below the bars, or use the
            matplotlib, Plotly or Altair adapter for axis logos.

    Example:
        ::

            from bokeh.plotting import figure
            import sdvplot

            try:
                sdvplot.axis_logos(figure(), "x", league="nfl")
            except TypeError:
                pass   # raised: Bokeh has no axis logos yet

    See Also:
        sdvplotR element_sdv_logo(): https://sdvplotR.sportsdataverse.org/
    """
    raise UnsupportedTargetError(
        "Bokeh has no axis logos yet: draw them inside the plot with add_logos (e.g. at a y just below the bars), "
        "or use matplotlib, Plotly or Altair for axis logos"
    )


def _drawn_marks(target: Any) -> list[tuple[Any, ...]]:
    """Test hook: (team_id, x, y, height, url) for each image of the sdvplot renderers, height = h / reference."""
    ref = _reference_height(target)
    out = []
    for r in target.renderers:
        if (r.name or "").startswith("sdvplot_"):
            d = r.data_source.data
            out += list(zip(d["team_id"], d["x"], d["y"], [h / ref for h in d["h"]], d["url"], strict=True))
    return out

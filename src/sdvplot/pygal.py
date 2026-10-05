"""The pygal adapter: logos, wordmarks and headshots on pygal XY charts, plus team colors as a pygal Style.

pygal builds a new SVG tree on every render, so add_* records the marks on the chart and registers one xml filter
(``chart.add_xml_filter``, pygal's public hook) that appends one ``<image>`` per recorded mark to the plot overlay
group, above pygal's own dots, during the render. Positions come from ``chart.view``, the projection pygal uses for its
own dots, after pygal's own value adapters (dates become timestamps), so a logo sits exactly where pygal would draw that
point. Resolution and its warnings happen when add_* is called, not at render time.

Copy a chart with ``copy.deepcopy``: the copy renders the marks the chart had, and marks added to either one afterwards
stay on that one. ``copy.copy`` is not supported: a shallow copy shares pygal's own series and filters.
"""

from __future__ import annotations

from typing import Any

import pygal
from pygal.style import Style

from sdvplot._colors import team_colors
from sdvplot._errors import UnsupportedTargetError
from sdvplot._placement import check_alpha, check_height, place
from sdvplot._resolve import _unpack
from sdvplot._web import aspect, image_src

_SUPPORTS_AXIS_LOGOS = False
_SUPPORTED = "pygal.XY, DateTimeLine, DateLine, TimeLine or TimeDeltaLine"
_HREF = "{http://www.w3.org/1999/xlink}href"  # pygal writes its own links as xlink:href (SVG 1.1 renderers need it)
_MARK = "data-sdvplot-mark"  # on each mark <image>: its index in the chart's _sdvplot_marks

__all__ = ["add_headshots", "add_logos", "add_wordmarks", "axis_logos", "team_style"]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)


def _check_chart(chart: Any) -> None:
    if not isinstance(chart, pygal.XY):
        raise UnsupportedTargetError(
            f"sdvplot.pygal draws on XY-family charts ({_SUPPORTED}); a {type(chart).__name__} chart places values by "
            "category or angle, not at an (x, y) point"
        )


class _MarksFilter:
    """The xml filter of one chart: appends the chart's recorded marks to its plot overlay (pygal's dot layer).

    An object rather than a closure, so ``copy.deepcopy`` points the copy's filter at the copy (through the memo) and
    the chart still pickles.
    """

    def __init__(self, chart: Any) -> None:
        self.chart = chart

    def __call__(self, root: Any) -> Any:
        chart = self.chart
        view = getattr(chart, "view", None)  # set during a render; absent when every series is empty
        overlay = next((el for el in root.iter() if el.get("class") == "plot overlay"), None)
        if view is None or overlay is None:
            return root
        ident = lambda v: v  # noqa: E731
        adapt = getattr(chart, "_adapt", None) or ident  # pygal's value adapters, as applied to its own points
        x_adapt = getattr(chart, "_x_adapt", None) or ident
        for index, (_, x, y, height, _, src, ratio, alpha) in enumerate(vars(chart).get("_sdvplot_marks", ())):
            cx, cy = view((adapt(x_adapt(x)), adapt(y)))
            if cx is None or cy is None or not (0 <= cx <= view.width and 0 <= cy <= view.height):
                continue  # outside the plot, like a matplotlib annotation outside the limits
            h = height * view.height
            w = h * ratio
            attrs = {
                _HREF: src, "x": f"{cx - w / 2:.3f}", "y": f"{cy - h / 2:.3f}", "width": f"{w:.3f}",
                "height": f"{h:.3f}", "preserveAspectRatio": "xMidYMid meet", "opacity": f"{alpha:g}",
                "pointer-events": "none",  # hovering still reaches pygal's dot (and its tooltip) underneath
                _MARK: str(index),  # which recorded mark this is: lets _drawn_marks measure the rendered image
            }  # fmt: skip
            overlay.append(overlay.makeelement("image", attrs))
        return root


def _add(
    chart: Any,
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
    _check_chart(chart)
    h, a = check_height(height), check_alpha(alpha)
    placements = place(x, y, teams, league=league, season=season, kind=kind, variant=variant, id_system=id_system)
    sources: dict[str, str] = {}
    marks = []
    for p in placements:
        if p.url not in sources:
            sources[p.url] = image_src(p, embed=embed)  # with embed=True this reads the cache now, not at render
        marks.append((p.team_id, p.x, p.y, h, p.url, sources[p.url], aspect(p), a))
    state = vars(chart)
    state["_sdvplot_marks"] = [*state.get("_sdvplot_marks", ()), *marks]  # a new list, never one another chart holds
    if not any(isinstance(f, _MarksFilter) and f.chart is chart for f in chart.xml_filters):
        chart.add_xml_filter(_MarksFilter(chart))  # one per chart: it draws every add_* call's marks
    return chart


def add_logos(
    chart: Any,
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
    """Draw each team's logo centred on its (x, y) point of a pygal XY chart, in every render of the chart.

    Copy the chart with ``copy.deepcopy`` (the copy keeps the logos); a shallow copy shares pygal's own series and
    filters.

    Args:
        chart: A pygal ``XY`` chart (``XY(stroke=False)`` for a scatter) or a ``DateTimeLine``/``DateLine``/
            ``TimeLine``/``TimeDeltaLine``.
        x: The points' x positions in the chart's units (numbers, or dates for the time charts; read by position).
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point, to pick each team's mark for that era.
        height: The logo height as a fraction of the plot height, in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        embed: True puts the image bytes in the SVG as data URIs, so the SVG and ``render_to_png()`` need no network.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        object: ``chart`` itself, with a filter that draws the logos whenever it renders.

    Raises:
        TypeError: If ``chart`` is not an XY-family chart (Bar, Line and Pie place values by category or angle).
        ValueError: If ``height`` or ``alpha`` is out of range, or ``x``/``y``/``teams`` differ in length.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

    Example:
        ::

            import pygal
            import sdvplot

            chart = pygal.XY(stroke=False)
            chart.add("games", [(10, -3), (20, -7)])
            sdvplot.add_logos(chart, [10, 20], [-3, -7], ["KC", "BUF"], league="nfl", height=0.15)
            chart.render_to_file("chart.svg")

    See Also:
        sdvplotR geom_nfl_logos(): https://sdvplotR.sportsdataverse.org/ ;
        pygal: https://www.pygal.org/
    """
    return _add(
        chart, x, y, teams, kind="logo", league=league, season=season, height=height, alpha=alpha,
        variant=variant, embed=embed, id_system=id_system,
    )  # fmt: skip


def add_wordmarks(
    chart: Any,
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
    """Draw each team's wordmark centred on its (x, y) point of a pygal XY chart, in every render of the chart.

    Copy the chart with ``copy.deepcopy`` (the copy keeps the wordmarks); a shallow copy shares pygal's own series and
    filters.

    Args:
        chart: A pygal ``XY`` chart or one of its time variants (``DateTimeLine``, ``DateLine``, ...).
        x: The points' x positions in the chart's units (read by position).
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point.
        height: The wordmark height as a fraction of the plot height, in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        embed: True puts the image bytes in the SVG as data URIs (no network when rendering).
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        object: ``chart`` itself, with a filter that draws the wordmarks whenever it renders.

    Raises:
        TypeError: If ``chart`` is not an XY-family chart.
        ValueError: If ``height`` or ``alpha`` is out of range, or the inputs differ in length.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

    Example:
        ::

            import pygal
            import sdvplot

            chart = pygal.XY(stroke=False)
            chart.add("games", [(10, -3)])
            sdvplot.add_wordmarks(chart, [10], [-3], ["KC"], league="nfl", height=0.08)

    See Also:
        sdvplotR geom_nfl_wordmarks(): https://sdvplotR.sportsdataverse.org/
    """
    return _add(
        chart, x, y, teams, kind="wordmark", league=league, season=season, height=height, alpha=alpha,
        variant=variant, embed=embed, id_system=id_system,
    )  # fmt: skip


def add_headshots(
    chart: Any,
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
    """Draw each player's headshot centred on its (x, y) point of a pygal XY chart, in every render of the chart.

    Copy the chart with ``copy.deepcopy`` (the copy keeps the headshots); a shallow copy shares pygal's own series and
    filters.

    Args:
        chart: A pygal ``XY`` chart or one of its time variants (``DateTimeLine``, ``DateLine``, ...).
        x: The points' x positions in the chart's units (read by position).
        y: The points' y positions, the same length as ``x``.
        players: The player id for each point.
        league: The SDV league key, e.g. "nfl".
        height: The headshot height as a fraction of the plot height, in (0, 1].
        alpha: Opacity, 0 to 1.
        embed: True puts the image bytes in the SVG as data URIs (no network when rendering).
        id_system: "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``.

    Returns:
        object: ``chart`` itself, with a filter that draws the headshots whenever it renders.

    Raises:
        TypeError: If ``chart`` is not an XY-family chart.
        ValueError: If ``height`` or ``alpha`` is out of range, or the inputs differ in length.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

    Example:
        ::

            import pygal
            import sdvplot

            chart = pygal.XY(stroke=False)
            chart.add("passing", [(4.2, 0.31)])
            sdvplot.add_headshots(chart, [4.2], [0.31], ["3139477"], league="nfl", height=0.15)

    See Also:
        sdvplotR geom_nfl_headshots(): https://sdvplotR.sportsdataverse.org/
    """
    return _add(
        chart, x, y, players, kind="headshot", league=league, season=None, height=height, alpha=alpha,
        variant="default", embed=embed, id_system=id_system,
    )  # fmt: skip


def axis_logos(chart: Any, axis: str, **kwargs: Any) -> Any:
    """Not supported: pygal draws axis labels as text nodes, so sdvplot.pygal cannot put logos in their place.

    Args:
        chart: A pygal chart.
        axis: "x" or "y".
        **kwargs: The arguments the other adapters take (``league``, ``height``, ...); ignored.

    Returns:
        object: Never returns.

    Raises:
        TypeError: Always.

    Example:
        ::

            import pygal
            import sdvplot.pygal

            try:
                sdvplot.pygal.axis_logos(pygal.Bar(), "x", league="nfl")
            except TypeError:
                pass   # use matplotlib, plotnine or Plotly for axis logos

    See Also:
        sdvplot.matplotlib.axis_logos(): https://sdvplot.sportsdataverse.org/
    """
    raise UnsupportedTargetError("sdvplot.pygal does not draw axis logos: pygal axis labels are text nodes")


def team_style(teams: Any, *, league: str, which: str = "primary", season: Any = None, **style_kwargs: Any) -> Style:
    """A pygal Style whose series colors are the teams' colors, in the order the series are added.

    A team that does not resolve keeps pygal's default color for its position (with one SdvplotWarning), so the
    other series keep theirs.

    Args:
        teams: One team per series, in series order (or one team, for one series), in any id system ``resolve()``
            understands.
        league: The SDV league key, e.g. "nfl".
        which: "primary" or "secondary".
        season: One season, or one per team.
        **style_kwargs: Any other ``pygal.style.Style`` option (``background``, ``font_family``, ...).

    Returns:
        pygal.style.Style: A style for ``pygal.XY(style=...)`` or any other pygal chart.

    Raises:
        ValueError: If ``league`` is unknown or ``which`` is not "primary"/"secondary".

    Example:
        ::

            import pygal
            import sdvplot.pygal

            chart = pygal.Bar(style=sdvplot.pygal.team_style(["KC", "BUF"], league="nfl"))
            chart.add("KC", [12])
            chart.add("BUF", [10])

    See Also:
        sdvplot.team_colors(): https://sdvplot.sportsdataverse.org/ ;
        pygal styles: https://www.pygal.org/en/stable/documentation/styles.html
    """
    defaults = Style.colors
    colors = team_colors(league, _unpack(teams)[0], which=which, season=season)  # a bare "KC" is one team
    return Style(colors=tuple(c or defaults[i % len(defaults)] for i, c in enumerate(colors)), **style_kwargs)


def _drawn_marks(chart: Any) -> list[tuple[Any, ...]]:
    """Test hook: render the chart, then (team_id, x, y, height, url) for each mark image in the SVG, in draw order;
    height = the image's height attribute / the plot area's height."""
    recorded = vars(chart).get("_sdvplot_marks", ())
    root = chart.render_tree()
    images = [el for el in root.iter() if el.get(_MARK) is not None]
    if not images:
        return []
    plot = next(el for el in root.iter() if el.get("class") == "plot")
    plot_h = float(next(el for el in plot if el.get("class") == "background").get("height"))
    out = []
    for el in images:
        team_id, x, y, _, url = recorded[int(el.get(_MARK))][:5]
        out.append((team_id, x, y, float(el.get("height")) / plot_h, url))
    return out

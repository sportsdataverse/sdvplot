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

from sdvplot._errors import UnsupportedTargetError, requires_extra

with requires_extra("pygal"):
    import pygal
    from pygal.style import Style

from sdvplot._bins import _cells, _values
from sdvplot._colors import team_colors
from sdvplot._placement import check_alpha, check_height, place
from sdvplot._resolve import _unpack
from sdvplot._types import BinShape, BinValue, IdSystem, Which
from sdvplot._web import aspect, image_src, present

_SUPPORTS_AXIS_LOGOS = False
_SUPPORTED = "pygal.XY, DateTimeLine, DateLine, TimeLine or TimeDeltaLine"
_HREF = "{http://www.w3.org/1999/xlink}href"  # pygal writes its own links as xlink:href (SVG 1.1 renderers need it)
_MARK = "data-sdvplot-mark"  # on each mark <image>: its index in the chart's _sdvplot_marks
_BIN = "data-sdvplot-bin"  # on each bin <polygon>: its index in the chart's _sdvplot_bins

__all__ = ["add_bins", "add_headshots", "add_logos", "add_wordmarks", "axis_logos", "team_style"]


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


class _BinsFilter:
    """The xml filter of one chart's bins: polygons in the plot group, under pygal's series and the marks.

    The polygons go in a nested ``<svg>`` the size of the plot area, which clips a cell at the plot edge (an ``<svg>``
    clips to its viewport), inserted before the first series group so pygal's dots and lines draw over them.
    """

    def __init__(self, chart: Any) -> None:
        self.chart = chart

    def __call__(self, root: Any) -> Any:
        chart = self.chart
        view = getattr(chart, "view", None)
        plot = next((el for el in root.iter() if el.get("class") == "plot"), None)
        if view is None or plot is None:
            return root
        ident = lambda v: v  # noqa: E731
        adapt = getattr(chart, "_adapt", None) or ident
        x_adapt = getattr(chart, "_x_adapt", None) or ident
        box = plot.makeelement("svg", {"x": "0", "y": "0", "width": f"{view.width:.3f}", "height": f"{view.height:.3f}",
                                       "class": "sdvplot-bins"})  # fmt: skip
        for index, (b, poly, color, alpha) in enumerate(vars(chart).get("_sdvplot_bins", ())):
            pts = [view((adapt(x_adapt(px)), adapt(py))) for px, py in poly]
            if any(p is None or p[0] is None or p[1] is None for p in pts):
                continue
            cell = box.makeelement("polygon", {
                "points": " ".join(f"{px:.3f},{py:.3f}" for px, py in pts), "fill": color, "fill-opacity": f"{alpha:g}",
                "stroke": "white", "stroke-width": "0.5", _BIN: str(index),
            })  # fmt: skip
            title = cell.makeelement("title", {})
            title.text = f"{b.id}: count {b.count}, weight {b.weight:g}"
            cell.append(title)
            box.append(cell)
        series = next((i for i, el in enumerate(plot) if (el.get("class") or "").startswith("series")), len(plot))
        plot.insert(series, box)
        return root


def _ramp(low: str, high: str, t: float) -> str:
    """The color ``t`` (0 to 1) of the way from ``low`` to ``high``, in RGB, as ``#rrggbb``."""
    from PIL import ImageColor

    lo, hi = ImageColor.getrgb(low)[:3], ImageColor.getrgb(high)[:3]
    return "#" + "".join(f"{round(a + (b - a) * t):02x}" for a, b in zip(lo, hi, strict=True))


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
    placements = present(placements, embed=embed)
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
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant``
            is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If ``x``/``y``/``teams`` differ in length.
        UnsupportedTargetError: (a TypeError) If ``chart`` is not an XY-family chart (Bar, Line and Pie place values by
            category or angle).
        OfflineError: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a
            DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a
            file that does not match the manifest's sha256).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would
            put the file outside the cache directory.

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
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant``
            is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If the inputs differ in length.
        UnsupportedTargetError: (a TypeError) If ``chart`` is not an XY-family chart.
        OfflineError: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a
            DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a
            file that does not match the manifest's sha256).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would
            put the file outside the cache directory.

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
        id_system: "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and
            WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``.

    Returns:
        object: ``chart`` itself, with a filter that draws the headshots whenever it renders.

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league`` has no ESPN headshots, or
            ``id_system`` is not valid for ``league``.
        ValueError: If the inputs differ in length.
        UnsupportedTargetError: (a TypeError) If ``chart`` is not an XY-family chart.
        OfflineError: If the nflverse player table (``id_system="gsis"``), or with ``embed=True`` a headshot, is neither
            cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.

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
        UnsupportedTargetError: (a TypeError) Always.

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


def team_style(
    teams: Any,
    *,
    league: str,
    which: Which = "primary",
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
    **style_kwargs: Any,
) -> Style:
    """A pygal Style whose series colors are the teams' colors, in the order the series are added.

    A team that does not resolve keeps pygal's default color for its position (with one SdvplotWarning), so the
    other series keep theirs.

    Args:
        teams: One team per series, in series order (or one team, for one series), in any id system ``resolve()``
            understands.
        league: The SDV league key, e.g. "nfl".
        which: "primary" or "secondary".
        season: One season, or one per team.
        id_system: The id system of ``teams``: ``"auto"`` (the default) tries them in order; pass ``"nhl_id"`` for NHL
            stats ids, which ``"auto"`` never tries.
        strict: Raise ``UnresolvedTeamError`` for a team that does not resolve, instead of keeping pygal's default
            color for it with one ``SdvplotWarning``.
        **style_kwargs: Any other ``pygal.style.Style`` option (``background``, ``font_family``, ...).

    Returns:
        pygal.style.Style: A style for ``pygal.XY(style=...)`` or any other pygal chart.

    Raises:
        TypeError: If ``teams`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
        InputError: (a ValueError) If ``league`` or ``id_system`` is unknown, ``which`` is not "primary"/"secondary", or
            ``season`` is not a year or is outside the seasons sdvplot knows for the league (or a list whose length does
            not match the teams).
        UnresolvedTeamError: (a ValueError) With ``strict=True``, for a team that does not resolve.

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
    colors = team_colors(  # a bare "KC" is one team
        league, _unpack(teams)[0], which=which, season=season, id_system=id_system, strict=strict
    )
    return Style(colors=tuple(c or defaults[i % len(defaults)] for i, c in enumerate(colors)), **style_kwargs)


def add_bins(
    chart: Any,
    x: Any,
    y: Any,
    *,
    shape: BinShape = "hex",
    radius: float | None = None,
    side: float | None = None,
    equal_area: bool = False,
    weights: Any = None,
    origin: tuple[float, float] = (0.0, 0.0),
    value: BinValue = "count",
    fill: float | None = None,
    min_count: int = 1,
    low: str = "#deebf7",
    high: str = "#08519c",
    opacity: float = 1.0,
) -> Any:
    """Hexagonal or square bins, colored by count or weight, as SVG polygons on a pygal XY chart.

    As the marks: ``add_bins`` records the cells on the chart and one xml filter (``chart.add_xml_filter``) draws them
    at each render, through ``chart.view``, pygal's own projection, so each vertex sits where pygal would draw that
    point. The cells go under pygal's series, clipped to the plot area; each is a ``<polygon>`` with a ``<title>``
    (its ``bin_id``, count and weight, the browser's hover text). The fill runs from ``low`` (the lowest value) to
    ``high`` (the highest), in RGB. Linking: none, pygal's SVG is static.

    Args:
        chart: A pygal XY-family chart (``pygal.XY``, ``DateTimeLine``, ...).
        x: The points' x values, in the chart's x units.
        y: The points' y values.
        shape: ``"hex"`` (the default) or ``"square"``.
        radius: The hexagon's circumradius, in data units; for squares, with ``equal_area=True``.
        side: The square's side (``shape="square"``).
        equal_area: Squares of a radius-``radius`` hexagon's area.
        weights: Optional non-negative weights, one per point (see ``sdvplot.hexbin``): each bin's ``weight``.
        origin: The point a cell centre falls on (default ``(0.0, 0.0)``): a hoop-centred lattice, origin = the
            basket's coordinates.
        value: What the fill encodes: ``"count"`` (the default, the points in each cell) or ``"weight"`` (the sum of
            their ``weights``).
        fill: The drawn cell's size as a fraction of the lattice cell, in (0, 1]: default 0.88 for squares (a gap, so
            they do not touch edge to edge) and 1.0 for hexagons (the tiled hexbin look).
        min_count: Cells with fewer points are not drawn (default 1, every cell). ``min_count=2`` suits shot charts:
            single attempts are not drawn. ``sdvplot.hexbin`` / ``squarebin`` still return every cell.
        low: The color of the lowest value (default ``"#deebf7"``), any CSS color.
        high: The color of the highest value (default ``"#08519c"``).
        opacity: The cells' fill opacity, 0 to 1.

    Returns:
        chart: ``chart``, with the cells recorded.

    Raises:
        InputError: If the lattice options are not valid (see ``sdvplot.binner``), ``value`` is not "count" or
            "weight", ``fill`` is not in (0, 1], ``min_count`` is not a whole number >= 1, or ``opacity`` is outside
            [0, 1].
        UnsupportedTargetError: If ``chart`` is not an XY-family chart.
        ValueError: If ``x``, ``y`` and ``weights`` differ in length, or ``low`` / ``high`` is not a color.

    Example:
        ::

            import pygal
            from sdvplot.pygal import add_bins

            # three Brooklyn shots of 2025-26, legacy tenths of a foot (sportsdataverse-data nba_stats_shots)
            x, y = [0, -1, -44], [0, 7, 252]
            chart = pygal.XY(stroke=False)
            chart.add("shots", list(zip(x, y)))
            add_bins(chart, x, y, shape="square", side=15, opacity=0.7)
            svg = chart.render()

    See Also:
        sdvplot.binner: https://sdvplot.sportsdataverse.org/docs/reference/binner ;
        pygal xml filters: https://www.pygal.org/en/stable/documentation/output.html
    """
    _check_chart(chart)
    a = check_alpha(opacity)
    bins, polygons = _cells(
        x,
        y,
        shape=shape,
        radius=radius,
        side=side,
        equal_area=equal_area,
        ids=None,
        weights=weights,
        origin=origin,
        fill=fill,
        min_count=min_count,
    )
    vals = _values(bins, value)
    lo, hi = min(vals, default=0.0), max(vals, default=0.0)
    _ramp(low, high, 0)  # checks both colors now, not at render
    cells = [(b, poly, _ramp(low, high, (v - lo) / (hi - lo) if hi > lo else 0.0), a)
             for b, poly, v in zip(bins, polygons, vals, strict=True)]  # fmt: skip
    state = vars(chart)
    state["_sdvplot_bins"] = [*state.get("_sdvplot_bins", ()), *cells]  # a new list, never one another chart holds
    if not any(isinstance(f, _BinsFilter) and f.chart is chart for f in chart.xml_filters):
        chart.add_xml_filter(_BinsFilter(chart))
    return chart


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


def _drawn_bins(chart: Any) -> list[tuple[str, float, float, int, tuple[str, ...]]]:
    """Test hook: render the chart, then (bin id, x, y, count, ()) for each cell polygon in the SVG, in draw order."""
    recorded = vars(chart).get("_sdvplot_bins", ())
    root = chart.render_tree()
    out: list[tuple[str, float, float, int, tuple[str, ...]]] = []
    for el in root.iter():
        if el.get(_BIN) is not None:
            b = recorded[int(el.get(_BIN))][0]
            out.append((b.id, b.x, b.y, b.count, ()))
    return out

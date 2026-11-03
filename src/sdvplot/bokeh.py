"""The Bokeh adapter: logos, wordmarks and headshots as one ``image_url`` glyph per call on a Bokeh figure.

Images are sized in screen pixels, so they keep their size when the user zooms: ``height`` times the reference height,
which is the figure's ``frame_height`` (the plot area) when set, else its ``height`` (the whole canvas: set
``frame_height`` for exact sizing). Factor (categorical) and datetime axes work natively, because ``x``/``y`` hold the
caller's own values. HoloViews draws through ``_draw`` too.
"""

from __future__ import annotations

from typing import Any

from sdvplot._errors import UnsupportedTargetError, requires_extra

with requires_extra("bokeh"):
    from bokeh.models import ColumnDataSource

from sdvplot._bins import _cells, _values
from sdvplot._placement import Placement, check_alpha, check_height, place
from sdvplot._types import BinShape, BinValue
from sdvplot._web import aspect, image_sources, present

_SUPPORTS_AXIS_LOGOS = False

__all__ = ["add_bins", "add_headshots", "add_logos", "add_wordmarks", "axis_logos"]


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
    placements = present(placements, embed=embed)
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
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant``
            is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If the inputs differ in length, or the figure has no pixel height (neither ``frame_height`` nor
            ``height`` is set).
        UnsupportedTargetError: (a TypeError) If ``target`` is not a Bokeh figure.
        OfflineError: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a
            DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a
            file that does not match the manifest's sha256).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would
            put the file outside the cache directory.

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
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant``
            is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If the inputs differ in length, or the figure has no pixel height (neither ``frame_height`` nor
            ``height`` is set).
        UnsupportedTargetError: (a TypeError) If ``target`` is not a Bokeh figure.
        OfflineError: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a
            DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a
            file that does not match the manifest's sha256).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would
            put the file outside the cache directory.

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
        id_system: "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and
            WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``.

    Returns:
        object: ``target`` itself, with one renderer named ``sdvplot_headshot`` added.

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league`` has no ESPN headshots, or
            ``id_system`` is not valid for ``league``.
        ValueError: If the inputs differ in length, or the figure has no pixel height (neither ``frame_height`` nor
            ``height`` is set).
        UnsupportedTargetError: (a TypeError) If ``target`` is not a Bokeh figure.
        OfflineError: If the nflverse player table (``id_system="gsis"``), or with ``embed=True`` a headshot, is neither
            cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.

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
        UnsupportedTargetError: (a TypeError) Always. Draw the logos inside the plot with ``add_logos`` at a y below the
            bars, or use the matplotlib, Plotly or Altair adapter for axis logos.

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
        if (r.name or "").startswith("sdvplot_") and r.name != "sdvplot_bins":
            d = r.data_source.data
            out += list(zip(d["team_id"], d["x"], d["y"], [h / ref for h in d["h"]], d["url"], strict=True))
    return out


# The two directions of add_bins' link, as CustomJS on each source's selection. A cell selection selects its points,
# a point selection selects the cells holding them; a selection already consistent both ways is left alone, so one
# selected point stays one point (its cell does not grow it to the whole cell) and the two callbacks never ping-pong.
_CELLS_TO_POINTS = """
const sel = new Set(cells.selected.indices);
const held = new Set();
for (const i of sel) for (const r of cells.data.rows[i]) held.add(r);
const now = points.selected.indices;
const covered = now.every((r) => held.has(r));
const touched = [...sel].every((i) => cells.data.rows[i].some((r) => now.includes(r)));
if (!(covered && touched)) points.selected.indices = [...held].sort((a, b) => a - b);
"""
_POINTS_TO_CELLS = """
const now = new Set(points.selected.indices);
const want = [];
cells.data.rows.forEach((rows, i) => { if (rows.some((r) => now.has(r))) want.push(i); });
const have = cells.selected.indices;
if (want.length !== have.length || want.some((i, k) => i !== have[k])) cells.selected.indices = want;
"""


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
    """Draw hexagonal or square bins, colored by count or weight, as one ``patches`` glyph on a Bokeh figure.

    The cells are ``sdvplot.binner``'s, in data units. The glyph (named ``"sdvplot_bins"``) has its own
    ``ColumnDataSource``, one row per cell: ``xs``/``ys`` (the polygon), ``x``/``y`` (the centre), ``count``,
    ``weight``, ``bin_id`` (``"x,y"``, as sdvplot-js stamps ``data-sdv-id``), ``point_ids`` (the ids of its points)
    and ``rows`` (their row numbers); a ``linear_cmap`` on ``value`` (``count`` or ``weight``) colors it.

    Linking: pass the points' ``ColumnDataSource`` (row ``i`` is the point at ``x[i]``, ``y[i]``) as ``link``, and
    two ``CustomJS`` callbacks tie the selections in the browser, with no server: selecting cells (with a ``tap`` or
    ``box_select`` tool on the figure) selects their points, and selecting points (in any glyph or ``DataTable`` on
    that source) selects the cells holding them. A selection already consistent both ways is left as it is.

    Args:
        target: A ``bokeh.plotting`` figure.
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
        palette: A Bokeh palette name or list of colors (default ``"Viridis256"``), fewest to most points.
        alpha: The cells' fill opacity, 0 to 1.
        link: Optional ``ColumnDataSource`` of the same points, in the same order, to link selections with.

    Returns:
        figure: ``target``, with the glyph added.

    Raises:
        InputError: If the lattice options are not valid (see ``sdvplot.binner``), ``value`` is not "count" or
            "weight", ``fill`` is not in (0, 1], ``min_count`` is not a whole number >= 1, or ``alpha`` is outside
            [0, 1].
        UnsupportedTargetError: If ``target`` is not a ``bokeh.plotting`` figure.
        TypeError: If ``link`` is not a ``ColumnDataSource``.
        ValueError: If ``x``, ``y`` and ``ids`` differ in length, or ``link`` does not hold one row per point.

    Example:
        ::

            from bokeh.models import ColumnDataSource
            from bokeh.plotting import figure
            from sdvplot.bokeh import add_bins

            # three Brooklyn shots of 2025-26, legacy tenths of a foot (sportsdataverse-data nba_stats_shots)
            shots = ColumnDataSource({"x": [0, -1, -44], "y": [0, 7, 252]})
            p = figure(tools="tap,box_select,reset", frame_height=300)
            p.scatter("x", "y", source=shots)
            add_bins(p, shots.data["x"], shots.data["y"], shape="square", side=15, alpha=0.6, link=shots)

    See Also:
        sdvplot.binner: https://sdvplot.sportsdataverse.org/docs/reference/binner ;
        Bokeh linked selection: https://docs.bokeh.org/en/latest/docs/user_guide/interaction/linking.html
    """
    from bokeh.models import CustomJS
    from bokeh.transform import linear_cmap

    fig = _figure(target)
    fill_alpha = check_alpha(alpha)
    if link is not None and not isinstance(link, ColumnDataSource):
        raise TypeError(f"link must be the points' ColumnDataSource, got {type(link).__name__}")
    bins, polygons = _cells(
        x,
        y,
        shape=shape,
        radius=radius,
        side=side,
        equal_area=equal_area,
        ids=ids,
        weights=weights,
        origin=origin,
        fill=fill,
        min_count=min_count,
    )
    values = _values(bins, value)
    if link is not None and len(next(iter(link.data.values()), ())) != len(x):
        raise ValueError(f"link must hold one row per point ({len(x)}), in the order of x and y")
    counts = [b.count for b in bins]
    cells = ColumnDataSource({
        "xs": [[p[0] for p in poly] for poly in polygons], "ys": [[p[1] for p in poly] for poly in polygons],
        "x": [b.x for b in bins], "y": [b.y for b in bins], "count": counts, "weight": [b.weight for b in bins],
        "bin_id": [b.id for b in bins],
        "point_ids": [list(b.ids) for b in bins], "rows": [list(b.rows) for b in bins],
    })  # fmt: skip
    color = linear_cmap(value, palette, min(values, default=0), max(values, default=1))
    fig.patches("xs", "ys", source=cells, fill_color=color, fill_alpha=fill_alpha, line_color="white",
                line_width=0.5, name="sdvplot_bins")  # fmt: skip
    if link is not None:
        args = {"cells": cells, "points": link}
        cells.selected.js_on_change("indices", CustomJS(args=args, code=_CELLS_TO_POINTS))
        link.selected.js_on_change("indices", CustomJS(args=args, code=_POINTS_TO_CELLS))
    return fig


def _drawn_bins(target: Any) -> list[tuple[str, float, float, int, tuple[str, ...]]]:
    """Test hook: (bin id, x, y, count, point ids) for each cell add_bins drew, in draw order."""
    out = []
    for r in _figure(target).renderers:
        if r.name == "sdvplot_bins":
            d = r.data_source.data
            cells = zip(d["bin_id"], d["x"], d["y"], d["count"], d["point_ids"], strict=True)
            out += [(i, cx, cy, n, tuple(p)) for i, cx, cy, n, p in cells]
    return out

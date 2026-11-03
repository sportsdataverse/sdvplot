"""The Folium adapter: logos, wordmarks and headshots as map markers with image icons.

On a map, ``x`` is longitude and ``y`` latitude. A map has no plot height, so ``height`` is a fraction of the map's
pixel height when it is given in pixels, else of _FOLIUM_REFERENCE_HEIGHT (a notebook map's usual height). The markers
go into one ``FeatureGroup`` named "sdvplot logos", so a ``LayerControl`` can toggle them.
"""

from __future__ import annotations

from typing import Any

from sdvplot._errors import UnsupportedTargetError, requires_extra

with requires_extra("folium"):
    import folium

from sdvplot._bins import _cells, _values
from sdvplot._index import teams as team_index
from sdvplot._placement import check_alpha, check_height, place
from sdvplot._types import BinShape, BinValue
from sdvplot._web import aspect, image_sources, present

_SUPPORTS_AXIS_LOGOS = False
_FOLIUM_REFERENCE_HEIGHT = 500  # px: the reference for a map whose height is not in pixels (the default "100%")
_GROUP_NAME = "sdvplot logos"
_BINS_NAME = "sdvplot bins"

__all__ = ["add_bins", "add_headshots", "add_logos", "add_wordmarks", "axis_logos"]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)


def _map(target: Any) -> folium.Map:
    if not isinstance(target, folium.Map):
        raise UnsupportedTargetError(f"sdvplot.folium draws on a folium.Map, got {type(target).__name__}")
    return target


def _reference_height(m: folium.Map) -> float:
    """The pixel height ``height`` is a fraction of: the map's own when in pixels, else _FOLIUM_REFERENCE_HEIGHT."""
    value, unit = m.height
    return float(value) if unit == "px" else float(_FOLIUM_REFERENCE_HEIGHT)


def _group(m: folium.Map) -> folium.FeatureGroup:
    for child in m._children.values():
        if isinstance(child, folium.FeatureGroup) and child.layer_name == _GROUP_NAME:
            return child
    group = folium.FeatureGroup(name=_GROUP_NAME)
    group.add_to(m)
    return group


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
    m = _map(target)
    placements = place(x, y, teams, league=league, season=season, kind=kind, variant=variant, id_system=id_system)
    placements = present(placements, embed=embed)
    if not placements:
        return m
    names = {} if kind == "headshot" else dict(team_index(league).select("team_id", "name").iter_rows())
    px = max(1, round(h * _reference_height(m)))  # Leaflet icon sizes are whole pixels
    group = _group(m)
    for p, src in zip(placements, image_sources(placements, embed=embed), strict=True):
        w = max(1, round(px * aspect(p)))
        marker: Any = folium.Marker(  # Any: it carries the test hook below (a type: ignore is unused without folium)
            location=[p.y, p.x],
            icon=folium.CustomIcon(src, icon_size=(w, px), icon_anchor=(w // 2, px // 2)),
            tooltip=names.get(p.team_id, p.team_id),
            opacity=a,
        )
        marker._sdvplot_mark = (p.team_id, p.x, p.y, src)
        marker.add_to(group)
    return m


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
    """Put each team's logo on a Folium map at its (longitude, latitude), with the team name as a tooltip.

    Args:
        target: A ``folium.Map``.
        x: The longitudes.
        y: The latitudes, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point, to pick each team's mark for that era.
        height: The logo height as a fraction of the map's pixel height (or of _FOLIUM_REFERENCE_HEIGHT, 500 px, when
            the map height is not in pixels), in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        embed: Inline each image as a data URI (a map that renders offline) instead of linking its URL.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        object: ``target`` itself, with the markers in the "sdvplot logos" feature group.

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant``
            is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If the inputs differ in length, or a location is not a number.
        UnsupportedTargetError: (a TypeError) If ``target`` is not a ``folium.Map``.
        OfflineError: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a
            DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a
            file that does not match the manifest's sha256).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would
            put the file outside the cache directory.

    Example:
        ::

            import folium
            import sdvplot

            m = folium.Map(location=[39, -95], zoom_start=4, height=600)
            sdvplot.add_logos(m, [-94.48, -78.79], [39.05, 42.77], ["KC", "BUF"], league="nfl", height=0.06)

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        Folium CustomIcon: https://python-visualization.github.io/folium/latest/user_guide/ui_elements/icons.html
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
    """Put each team's wordmark on a Folium map at its (longitude, latitude).

    Args:
        target: A ``folium.Map``.
        x: The longitudes.
        y: The latitudes, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point.
        height: The wordmark height as a fraction of the map's reference height (see ``add_logos``), in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        object: ``target`` itself, with the markers added.

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant``
            is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If the inputs differ in length, or a location is not a number.
        UnsupportedTargetError: (a TypeError) If ``target`` is not a ``folium.Map``.
        OfflineError: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a
            DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a
            file that does not match the manifest's sha256).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would
            put the file outside the cache directory.

    Example:
        ::

            import folium
            import sdvplot

            m = folium.Map(location=[39, -95], zoom_start=4)
            sdvplot.add_wordmarks(m, [-94.48], [39.05], ["KC"], league="nfl", height=0.04)

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/
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
    """Put each player's headshot on a Folium map at its (longitude, latitude).

    Args:
        target: A ``folium.Map``.
        x: The longitudes.
        y: The latitudes, the same length as ``x``.
        players: The player id for each point (shown as the tooltip).
        league: The SDV league key, e.g. "nfl".
        height: The headshot height as a fraction of the map's reference height (see ``add_logos``), in (0, 1].
        alpha: Opacity, 0 to 1.
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and
            WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``.

    Returns:
        object: ``target`` itself, with the markers added.

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league`` has no ESPN headshots, or
            ``id_system`` is not valid for ``league``.
        ValueError: If the inputs differ in length, or a location is not a number.
        UnsupportedTargetError: (a TypeError) If ``target`` is not a ``folium.Map``.
        OfflineError: If the nflverse player table (``id_system="gsis"``), or with ``embed=True`` a headshot, is neither
            cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.

    Example:
        ::

            import folium
            import sdvplot

            m = folium.Map(location=[39, -95], zoom_start=4)
            sdvplot.add_headshots(m, [-94.48], [39.05], ["3139477"], league="nfl", height=0.08)

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/
    """
    return _add(
        target, x, y, players, kind="headshot", league=league, season=None, height=height, alpha=alpha,
        variant="default", embed=embed, id_system=id_system,
    )  # fmt: skip


def axis_logos(target: Any, axis: str, **kwargs: Any) -> Any:
    """Not supported: a map has no category axes.

    Args:
        target: A ``folium.Map``.
        axis: "x" or "y".
        **kwargs: Ignored.

    Returns:
        object: Never returns.

    Raises:
        UnsupportedTargetError: (a TypeError) Always. Put the logos on the map with ``add_logos`` instead.

    Example:
        ::

            import folium
            import sdvplot

            try:
                sdvplot.axis_logos(folium.Map(), "x", league="nfl")
            except TypeError:
                pass   # raised: maps have no axis logos

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/
    """
    raise UnsupportedTargetError("a folium map has no category axes; put the logos on the map with add_logos instead")


def add_bins(
    target: Any,
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
    palette: Any = "viridis",
    opacity: float = 0.7,
) -> Any:
    """Hexagonal or square bins, colored by count or weight, as one GeoJSON layer of polygons on a folium map.

    On a map ``x`` is longitude and ``y`` latitude, so the lattice is in degrees: ``radius``, ``side`` and ``origin``
    are degrees of longitude and latitude, not metres. Leaflet's Web Mercator stretches a degree of longitude less than
    one of latitude away from the equator, so cells look taller than wide by ``1 / cos(latitude)`` (about 1.3 at 40
    degrees); bin projected coordinates and convert the vertices yourself for equal-area cells on the ground. The
    layer is a ``folium.GeoJson`` named ``"sdvplot bins"`` (a ``LayerControl`` toggles it), one ``Polygon`` feature
    per cell with ``bin_id`` (``"x,y"``), ``count`` and ``weight`` properties, shown on hover. Linking: none, the
    layer is static.

    Args:
        target: A ``folium.Map``.
        x: The points' longitudes, in degrees.
        y: The points' latitudes, in degrees.
        shape: ``"hex"`` (the default) or ``"square"``.
        radius: The hexagon's circumradius, in degrees; for squares, with ``equal_area=True``.
        side: The square's side, in degrees (``shape="square"``).
        equal_area: Squares of a radius-``radius`` hexagon's area.
        weights: Optional non-negative weights, one per point (see ``sdvplot.hexbin``): each bin's ``weight``.
        origin: The point a cell centre falls on, ``(longitude, latitude)`` (default ``(0.0, 0.0)``): as a
            hoop-centred lattice puts origin at the basket's coordinates.
        value: What the fill encodes: ``"count"`` (the default, the points in each cell) or ``"weight"`` (the sum of
            their ``weights``).
        fill: The drawn cell's size as a fraction of the lattice cell, in (0, 1]: default 0.88 for squares (a gap, so
            they do not touch edge to edge) and 1.0 for hexagons (the tiled hexbin look).
        min_count: Cells with fewer points are not drawn (default 1, every cell). ``min_count=2`` suits shot charts:
            single attempts are not drawn. ``sdvplot.hexbin`` / ``squarebin`` still return every cell.
        palette: A ``branca.colormap.linear`` name (default ``"viridis"``) or a branca colormap, lowest to highest
            value.
        opacity: The cells' fill opacity, 0 to 1.

    Returns:
        Map: ``target``, with the layer added.

    Raises:
        InputError: If the lattice options are not valid (see ``sdvplot.binner``), ``value`` is not "count" or
            "weight", ``fill`` is not in (0, 1], ``min_count`` is not a whole number >= 1, or ``opacity`` is outside
            [0, 1].
        UnsupportedTargetError: If ``target`` is not a ``folium.Map``.
        ValueError: If ``x``, ``y`` and ``weights`` differ in length, or ``palette`` is not a branca linear colormap.

    Example:
        ::

            import folium
            from sdvplot.folium import add_bins

            # three stadiums' longitudes and latitudes: two in New Jersey share a half-degree hexagon
            lon, lat = [-74.074, -74.07, -71.264], [40.813, 40.81, 42.091]
            m = folium.Map(location=[41.5, -72.5], zoom_start=6)
            add_bins(m, lon, lat, radius=0.5)

    See Also:
        sdvplot.binner: https://sdvplot.sportsdataverse.org/docs/reference/binner ;
        folium GeoJson: https://python-visualization.github.io/folium/latest/user_guide/geojson/geojson.html
    """
    import branca.colormap as bcm

    m = _map(target)
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
    if isinstance(palette, str):
        if not isinstance(getattr(bcm.linear, palette, None), bcm.LinearColormap):
            raise ValueError(f"palette must name a branca.colormap.linear colormap, got {palette!r}")
        palette = getattr(bcm.linear, palette)
    if not isinstance(palette, (bcm.LinearColormap, bcm.StepColormap)):
        raise ValueError(f"palette must be a branca colormap or the name of one, got {type(palette).__name__}")
    lo, hi = min(vals, default=0.0), max(vals, default=1.0)
    cmap = palette.scale(lo, hi if hi > lo else lo + 1)
    features = [
        {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[*map(list, poly), list(poly[0])]]},
         "properties": {"bin_id": b.id, "x": b.x, "y": b.y, "count": b.count, "weight": b.weight,
                        "fill_color": cmap(v)}}
        for b, poly, v in zip(bins, polygons, vals, strict=True)
    ]  # fmt: skip
    layer: Any = folium.GeoJson(  # Any: it carries the test hook below
        {"type": "FeatureCollection", "features": features},
        name=_BINS_NAME,
        style_function=lambda f: {
            "fillColor": f["properties"]["fill_color"],
            "fillOpacity": a,
            "color": "white",
            "weight": 0.5,
        },  # fmt: skip
        tooltip=folium.GeoJsonTooltip(["bin_id", "count", "weight"]) if features else None,
    )
    layer._sdvplot_bins = True
    layer.add_to(m)
    return m


def _drawn_marks(target: Any) -> list[tuple[Any, ...]]:
    """Test hook: (team_id, x, y, height, url) for each marker sdvplot added; height = icon px / reference px."""
    m = _map(target)
    ref = _reference_height(m)
    out = []
    for group in m._children.values():
        if isinstance(group, folium.FeatureGroup) and group.layer_name == _GROUP_NAME:
            markers: list[Any] = list(group._children.values())
            for marker in markers:
                if hasattr(marker, "_sdvplot_mark"):
                    team_id, x, y, src = marker._sdvplot_mark
                    out.append((team_id, x, y, marker.icon.options["icon_size"][1] / ref, src))
    return out


def _drawn_bins(target: Any) -> list[tuple[str, float, float, int, tuple[str, ...]]]:
    """Test hook: (bin id, x, y, count, ()) for each cell add_bins drew, in draw order; no point ids are kept."""
    out: list[tuple[str, float, float, int, tuple[str, ...]]] = []
    layers: list[Any] = list(_map(target)._children.values())
    for layer in layers:
        if getattr(layer, "_sdvplot_bins", False):
            for f in layer.data["features"]:
                p = f["properties"]
                out.append((p["bin_id"], p["x"], p["y"], p["count"], ()))
    return out

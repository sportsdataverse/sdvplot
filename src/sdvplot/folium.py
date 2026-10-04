"""The Folium adapter: logos, wordmarks and headshots as map markers with image icons.

On a map, ``x`` is longitude and ``y`` latitude. A map has no plot height, so ``height`` is a fraction of the map's
pixel height when it is given in pixels, else of FOLIUM_REFERENCE_HEIGHT (a notebook map's usual height). The markers
go into one ``FeatureGroup`` named "sdvplot logos", so a ``LayerControl`` can toggle them.
"""

from __future__ import annotations

from typing import Any

import folium

from sdvplot._index import teams as team_index
from sdvplot._placement import check_alpha, check_height, place
from sdvplot._web import aspect, image_sources

SUPPORTS_AXIS_LOGOS = False
FOLIUM_REFERENCE_HEIGHT = 500  # px: the reference for a map whose height is not in pixels (the default "100%")
GROUP_NAME = "sdvplot logos"


def _map(target: Any) -> folium.Map:
    if not isinstance(target, folium.Map):
        raise TypeError(f"sdvplot.folium draws on a folium.Map, got {type(target).__name__}")
    return target


def reference_height(m: folium.Map) -> float:
    """The pixel height ``height`` is a fraction of: the map's own when in pixels, else FOLIUM_REFERENCE_HEIGHT."""
    value, unit = m.height
    return float(value) if unit == "px" else float(FOLIUM_REFERENCE_HEIGHT)


def _group(m: folium.Map) -> folium.FeatureGroup:
    for child in m._children.values():
        if isinstance(child, folium.FeatureGroup) and child.layer_name == GROUP_NAME:
            return child
    group = folium.FeatureGroup(name=GROUP_NAME)
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
    if not placements:
        return m
    names = {} if kind == "headshot" else dict(team_index(league).select("team_id", "name").iter_rows())
    px = max(1, round(h * reference_height(m)))  # Leaflet icon sizes are whole pixels
    group = _group(m)
    for p, src in zip(placements, image_sources(placements, embed=embed), strict=True):
        w = max(1, round(px * aspect(p)))
        marker = folium.Marker(
            location=[p.y, p.x],
            icon=folium.CustomIcon(src, icon_size=(w, px), icon_anchor=(w // 2, px // 2)),
            tooltip=names.get(p.team_id, p.team_id),
            opacity=a,
        )
        marker._sdvplot_mark = (p.team_id, p.x, p.y, src)  # type: ignore[attr-defined]
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
        height: The logo height as a fraction of the map's pixel height (or of FOLIUM_REFERENCE_HEIGHT, 500 px, when
            the map height is not in pixels), in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        embed: Inline each image as a data URI (a map that renders offline) instead of linking its URL.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        object: ``target`` itself, with the markers in the "sdvplot logos" feature group.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or a location is not a
            number.
        TypeError: If ``target`` is not a ``folium.Map``.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

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
        ValueError: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or a location is not a
            number.
        TypeError: If ``target`` is not a ``folium.Map``.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

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
        id_system: "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``.

    Returns:
        object: ``target`` itself, with the markers added.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, the inputs differ in length, or a location is not a
            number.
        TypeError: If ``target`` is not a ``folium.Map``.
        OfflineError: If ``embed=True`` and an image is neither cached nor downloadable.

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
        TypeError: Always. Put the logos on the map with ``add_logos`` instead.

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
    raise TypeError("a folium map has no category axes; put the logos on the map with add_logos instead")


def drawn_marks(target: Any) -> list[tuple[Any, ...]]:
    """Test hook: (team_id, x, y, height, url) for each marker sdvplot added; height = icon px / reference px."""
    m = _map(target)
    ref = reference_height(m)
    out = []
    for group in m._children.values():
        if isinstance(group, folium.FeatureGroup) and group.layer_name == GROUP_NAME:
            markers: list[Any] = list(group._children.values())
            for marker in markers:
                if hasattr(marker, "_sdvplot_mark"):
                    team_id, x, y, src = marker._sdvplot_mark
                    out.append((team_id, x, y, marker.icon.options["icon_size"][1] / ref, src))
    return out

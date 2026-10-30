"""The pydeck adapter: team logos, team-colored arcs and sportypy playing surfaces as pydeck layer props.

``logo_icon_layer``, ``pass_arc_layer`` and ``surface_layer`` return plain dicts, ``pydeck.Layer``'s keyword arguments
(``pdk.Layer(**props)``): the layer type, the data rows, the accessors that name their fields, and constant strings
quoted (``"'pixels'"``), as pydeck reads an unquoted string as an expression. ``deck`` puts them in a
``pydeck.Deck`` with its view fitted. Like every adapter module, this one needs its library: importing it without
the ``pydeck`` extra raises OptionalDependencyError naming the extra. sdvplot-js's ``@sportsdataverse/sdvplot/deckgl``
builds the same props for deck.gl (camelCase keys, accessor functions): the two are held to one shared fixture,
tests/fixtures/deckgl_shared.json.
"""

from __future__ import annotations

import importlib
import math
import numbers
import re
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any

import numpy as np

from sdvplot._colors import team_colors
from sdvplot._contrast import hex6
from sdvplot._errors import InputError, OptionalDependencyError, requires_extra, warn

with requires_extra("pydeck"):
    import pydeck

from sdvplot._normalize import norm_value
from sdvplot._placement import _missing, check_alpha, place
from sdvplot._resolve import resolve
from sdvplot._team_palette import _round, team_palette
from sdvplot._web import aspect

if TYPE_CHECKING:
    from sdvplot._types import IdSystem, Which

__all__ = ["deck", "logo_icon_layer", "pass_arc_layer", "surface_layer"]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)


# pydeck reads an unquoted string keyword as an expression (an accessor naming a row field); a constant string prop
# is quoted, which pydeck strips before it sends the value to deck.gl
_CARTESIAN = "'cartesian'"
_ICON_PX = 128  # the px height a logo is packed into deck.gl's atlas at (it is drawn at `size`: this is its sharpness)
# sport -> (sportypy.surfaces module, the class that takes a league_code): the ten sports sporty and sportypy 1.2 draw
_SPORTS = {
    "baseball": "BaseballField",
    "basketball": "BasketballCourt",
    "curling": "CurlingSheet",
    "football": "FootballField",
    "hockey": "HockeyRink",
    "lacrosse": "LacrosseField",
    "soccer": "SoccerPitch",
    "softball": "SoftballField",
    "tennis": "TennisCourt",
    "volleyball": "VolleyballCourt",
}


def _columns(rows: Any, names: Sequence[str], what: Sequence[str]) -> tuple[list[list[Any]], Callable[[str], bool]]:
    """Each named column of ``rows`` (a polars or pandas DataFrame, or a sequence of mappings) as a list, and a test of
    whether ``rows`` has a column. A column no row has is an InputError (an empty sequence has every column)."""
    if hasattr(rows, "columns"):
        import narwhals as nw

        frame = nw.from_native(rows, eager_only=True)
        cols = set(frame.columns)
        has: Callable[[str], bool] = cols.__contains__
        get: Callable[[str], list[Any]] = lambda n: frame[n].to_list()  # noqa: E731
    else:
        records = list(rows)
        keys = {k for r in records if isinstance(r, Mapping) for k in r}
        has = lambda n: not records or n in keys  # noqa: E731
        get = lambda n: [r.get(n) if isinstance(r, Mapping) else None for r in records]  # noqa: E731
    for name, w in zip(names, what, strict=True):
        if not has(name):
            raise InputError(f"{w} column {name!r} is not in rows")
    return [get(n) for n in names], has


def _real(v: Any) -> bool:
    return isinstance(v, numbers.Real) and not isinstance(v, bool) and math.isfinite(v)


def _px(name: str, v: Any) -> float:
    if not _real(v) or v < 1:
        raise InputError(f"{name} is in px, 1 or more, got {v!r}")
    return float(v)


def _label(team: Any) -> str:
    """An unresolved team value as text, the same in sdvplot-js: a number without ".0", a missing one empty."""
    if _missing(team):
        return ""
    if _real(team):
        return norm_value(team) or ""
    return str(team)


def _rgba(color: str) -> list[int]:
    """``#rrggbb`` / ``#rrggbbaa`` as deck.gl's ``[r, g, b, a]``."""
    c = str(color).strip().lstrip("#")
    h = hex6(color, drop_alpha=True)
    return [int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), int(c[6:8], 16) if len(c) == 8 else 255]


def logo_icon_layer(
    rows: Any,
    *,
    x: str,
    y: str,
    team: str,
    league: str,
    season: Any = None,
    variant: str = "default",
    id_system: IdSystem = "auto",
    strict: bool = False,
    size: float = 32,
    alpha: float = 1.0,
    id: str = "sdvplot-logos",
) -> dict[str, Any]:
    """pydeck ``IconLayer`` props drawing each row's team logo at its (x, y).

    The logos are deck.gl's auto-packed icons: deck.gl fetches each URL once and packs it into its own atlas, 128 px
    tall at the logo's aspect, centred on the point. A team with no logo (or one that does not resolve) is left out
    with one warning, as the other adapters do; so is a row with a missing x or y. ``x`` and ``y`` are in the layer's
    coordinates: longitude and latitude on a map, or a surface's own units over ``surface_layer`` (``deck`` sets the
    coordinate system for you).

    Args:
        rows: The rows: a polars or pandas DataFrame, or a sequence of mappings.
        x: The column of each logo's x (a longitude on a map, or a surface's x).
        y: The column of each logo's y.
        team: The column of each row's team (abbreviation, name or id; see ``id_system``).
        league: The SDV league key, e.g. "nhl".
        season: A season for every row, or the name of a column holding each row's season.
        variant: The logo variant, e.g. "dark".
        id_system: How the team values are read.
        strict: Raise UnresolvedTeamError for a team that does not resolve, instead of warning.
        size: The logo's height on screen in px, 1 or more (deck.gl's ``getSize`` in "pixels" units).
        alpha: The layer's opacity in [0, 1].
        id: The layer id.

    Returns:
        dict: ``pydeck.Layer`` keyword arguments: ``type`` "IconLayer", ``data`` (one dict per logo: ``position``,
        ``icon`` with its ``url``, ``width``, ``height``, ``anchorY`` and ``mask``, the resolved ``team`` id and the
        row's ``index``), the accessors ``get_position`` and ``get_icon``, ``get_size``, ``size_units`` and
        ``opacity``.

    Raises:
        InputError: (a ValueError) If a column is not in ``rows``, ``size`` is under 1 px, ``alpha`` is outside
            [0, 1], or ``league``, ``season``, ``variant`` or ``id_system`` is not valid.
        UnresolvedTeamError: With ``strict=True``, for a team that does not resolve.
        OfflineError: If the logo manifest is neither cached nor downloadable.

    Example:
        ::

            import sdvplot.pydeck

            # Arrowhead and Lincoln Financial Field, by longitude and latitude
            stadiums = [
                {"team": "KC", "lon": -94.4839, "lat": 39.0489},
                {"team": "PHI", "lon": -75.1675, "lat": 39.9008},
            ]
            props = sdvplot.pydeck.logo_icon_layer(stadiums, x="lon", y="lat", team="team", league="nfl", size=40)
            assert [d["team"] for d in props["data"]] == ["12", "21"]

    See Also:
        deck.gl IconLayer: https://deck.gl/docs/api-reference/layers/icon-layer ;
        pydeck: https://deckgl.readthedocs.io/
    """
    px = _px("size", size)
    opacity = check_alpha(alpha)
    rows = rows if hasattr(rows, "columns") else list(rows)  # read twice below
    names = [x, y, team]
    per_row = isinstance(season, str) and _columns(rows, [], [])[1](season)  # a season column, as sdvplot-js reads it
    cols = [*names, season] if per_row else names
    (xs, ys, teams, *seasons), _ = _columns(rows, cols, ["x", "y", "team", "season"][: len(cols)])
    if per_row:
        season = seasons[0]
    # place() reads x and y only to skip a row with a missing one: give it the row's index as x, so each placement
    # names its row (the position is read from the row itself)
    index = [None if _missing(a) or _missing(b) else i for i, (a, b) in enumerate(zip(xs, ys, strict=True))]
    marks = place(index, index, teams, league=league, season=season, variant=variant, id_system=id_system,
                  strict=strict)  # fmt: skip
    data = [
        {
            "position": [float(xs[p.x]), float(ys[p.x])],
            "icon": {
                "url": p.url,
                "width": _round(_ICON_PX * aspect(p)),
                "height": _ICON_PX,
                "anchorY": _ICON_PX // 2,
                "mask": False,
            },
            "team": p.team_id,
            "index": p.x,
        }
        for p in marks
    ]
    return {
        "type": "IconLayer",
        "id": id,
        "data": data,
        "get_position": "position",
        "get_icon": "icon",
        "get_size": px,
        "size_units": "'pixels'",
        "opacity": opacity,
    }


def _end_colors(
    ids: list[str | None], *, league: str, season: Any, which: Which, background: str | None, fallback: str
) -> list[str]:
    """One color per distinct team at one end of the arcs (None for a team that did not resolve): the teams' ``which``
    colors, or the shared palette of them on ``background``. A team that did not resolve takes the fallback and stays
    out of the palette, so it never moves a real team's color (and no warning names it); as sdvplot-js does."""
    known = [i for i in ids if i is not None]
    kw = {"season": season, "id_system": "team_id"}
    main = team_colors(league, known, which=which, **kw) if known else []
    other = team_colors(league, known, which="secondary" if which == "primary" else "primary", **kw) if known else []
    # a team with no `which` color (often no secondary) takes its other color, then the fallback
    colors = [hex6(m or o or fallback, drop_alpha=True) for m, o in zip(main, other, strict=True)]
    if background is not None:
        colors = team_palette(colors, other, hex6(background), known)
    got = iter(colors)
    return [fallback if i is None else next(got) for i in ids]


def pass_arc_layer(
    rows: Any,
    *,
    x: str,
    y: str,
    xend: str,
    yend: str,
    team: str,
    league: str,
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
    which: Which = "primary",
    background: str | None = None,
    fallback: str = "#808080",
    width: float = 2,
    alpha: float = 1.0,
    height: float | None = None,
    tilt: float | None = None,
    id: str = "sdvplot-arcs",
) -> dict[str, Any]:
    """pydeck ``ArcLayer`` props: one arc per row from (x, y) to (xend, yend), in the team's colors.

    The team's primary color is at the source and its secondary at the target (``which="secondary"`` swaps them), so
    where the two colors differ the ends tell the direction. Each team keeps one color per end, the teams taken in the
    order they first appear. With ``background``, every color keeps 3:1 contrast against it (dark mode) and stays
    distinct (CIE76 ΔE of 20 or more) from the other teams' colors at that end. Caveat: a color that does not read
    gives way to the team's other color, so when only one of a team's two colors reads on the background, both ends
    take it and the arcs no longer show their direction (France's navy and mint on a dark pitch are both mint); pick a
    background on which both read (France's both read on a mid-tone green such as ``#4a7f3a``), or check that
    ``sourceColor`` and ``targetColor`` differ. A team that does not resolve takes ``fallback`` as given, outside the
    palette; a row with a missing coordinate is left out with one warning.

    Args:
        rows: The rows: a polars or pandas DataFrame, or a sequence of mappings.
        x: The column of each arc's source x.
        y: The column of each arc's source y.
        xend: The column of each arc's target x.
        yend: The column of each arc's target y.
        team: The column of the team each arc is colored by.
        league: The SDV league key, e.g. "soccer".
        season: The season the teams are resolved for.
        id_system: How the team values are read.
        strict: Raise UnresolvedTeamError for a team that does not resolve, instead of warning (and drawing it in
            ``fallback``).
        which: The color at the source end, "primary" or "secondary"; the target end takes the other.
        background: The background the arcs are drawn on; given, each color keeps 3:1 contrast against it and stays
            distinct from the other teams'.
        fallback: The color of a team that does not resolve, or has no color (an unresolved team's is used as given).
        width: The arc's width in px, 1 or more.
        alpha: The layer's opacity in [0, 1].
        height: deck.gl's ``getHeight``, how high each arc rises for its length, 0 or more (0 draws a straight line).
            None (the default) keeps deck.gl's 1; lower, such as 0.3, keeps arcs laid flat (``tilt=90``) close to their
            chord, inside the surface.
        tilt: deck.gl's ``getTilt``, degrees in [-90, 90]: 90 lays each arc flat on the surface, so a top-down 2D view
            shows the curve. None (the default) keeps deck.gl's upright arcs, for a pitched 3D view.
        id: The layer id.

    Returns:
        dict: ``pydeck.Layer`` keyword arguments: ``type`` "ArcLayer", ``data`` (one dict per arc: ``source``,
        ``target``, ``sourceColor`` and ``targetColor`` as ``[r, g, b, a]``, ``team`` (the resolved id, else the row's
        value as text) and the row's ``index``), the accessors ``get_source_position``, ``get_target_position``,
        ``get_source_color`` and ``get_target_color``, ``get_width``, ``width_units``, ``opacity`` and, with
        ``height`` and ``tilt``, ``get_height`` and ``get_tilt``.

    Raises:
        InputError: (a ValueError) If a column is not in ``rows``, ``width`` is under 1 px, ``alpha`` is outside
            [0, 1], ``height`` is negative, ``tilt`` is outside [-90, 90], ``which`` is not "primary" or
            "secondary", or ``league``, ``season`` or ``id_system`` is not valid.
        UnresolvedTeamError: With ``strict=True``, for a team that does not resolve.
        ValueError: If ``background`` or ``fallback`` is not a hex color.

    Example:
        ::

            import sdvplot.pydeck

            # two of France's passes in the 2018 World Cup final (StatsBomb open data through SPADL, metres)
            passes = [
                {"team": "478", "start_x": 54.69, "start_y": 6.38, "end_x": 56.44, "end_y": 1.28},
                {"team": "478", "start_x": 22.31, "start_y": 9.78, "end_x": 6.56, "end_y": 31.88},
            ]
            props = sdvplot.pydeck.pass_arc_layer(
                passes, x="start_x", y="start_y", xend="end_x", yend="end_y", team="team", league="soccer",
                id_system="team_id", tilt=90,
            )
            assert props["data"][0]["sourceColor"] == [0, 0, 128, 255]  # France's navy at the passer
            assert props["data"][0]["targetColor"] != props["data"][0]["sourceColor"]  # its mint at the receiver

    See Also:
        deck.gl ArcLayer: https://deck.gl/docs/api-reference/layers/arc-layer ;
        sdvplot-js passArcLayer: https://plot.sportsdataverse.org/
    """
    px = _px("width", width)
    opacity = check_alpha(alpha)
    if which not in ("primary", "secondary"):
        raise InputError(f"which must be one of primary, secondary, got {which!r}")
    if tilt is not None and not (_real(tilt) and -90 <= tilt <= 90):
        raise InputError(f"tilt is in degrees, in [-90, 90], got {tilt!r}")
    if height is not None and not (_real(height) and height >= 0):
        raise InputError(f"height is an arc's height multiplier, 0 or more, got {height!r}")
    (x0, y0, x1, y1, teams), _ = _columns(rows, [x, y, xend, yend, team], ["x", "y", "xend", "yend", "team"])
    keep = [i for i in range(len(teams)) if all(_real(c[i]) for c in (x0, y0, x1, y1))]
    kept_set = set(keep)
    missing = [teams[i] for i in range(len(teams)) if i not in kept_set]
    if missing:
        shown = ", ".join(_label(v) or "null" for v in missing[:10]) + (  # as sdvplot-js writes them
            f" and {len(missing) - 10} more" if len(missing) > 10 else ""
        )
        warn(f"skipped {len(missing)} arc(s) with a missing coordinate: {shown}")
    kept = [teams[i] for i in keep]
    resolved: list[str | None] = (
        resolve(kept, league, season=season, id_system=id_system, strict=strict) if kept else []
    )
    # one color per distinct team, in order of first appearance; an unresolved team is keyed by its own value
    keys = [r if r is not None else f"?{_label(t)}" for r, t in zip(resolved, kept, strict=True)]
    distinct = list(dict.fromkeys(keys))
    ids = [None if k.startswith("?") else k for k in distinct]
    other: Which = "secondary" if which == "primary" else "primary"
    opts = {"league": league, "season": season, "background": background, "fallback": hex6(fallback)}
    src = _end_colors(ids, which=which, **opts)
    tgt = _end_colors(ids, which=other, **opts)
    at = {k: j for j, k in enumerate(distinct)}
    data = [
        {
            "source": [x0[i], y0[i]],
            "target": [x1[i], y1[i]],
            "sourceColor": _rgba(src[at[keys[n]]]),
            "targetColor": _rgba(tgt[at[keys[n]]]),
            "team": resolved[n] if resolved[n] is not None else _label(kept[n]),
            "index": i,
        }
        for n, i in enumerate(keep)
    ]
    props: dict[str, Any] = {
        "type": "ArcLayer",
        "id": id,
        "data": data,
        "get_source_position": "source",
        "get_target_position": "target",
        "get_source_color": "sourceColor",
        "get_target_color": "targetColor",
        "get_width": px,
        "width_units": "'pixels'",
        "opacity": opacity,
    }
    if height is not None:
        props["get_height"] = height
    if tilt is not None:
        props["get_tilt"] = tilt
    return props


def _loops(xy: list[tuple[float, float]]) -> list[list[tuple[float, float]]]:
    """A feature's path as closed loops. sportypy (after sportyR) draws some features as two loops in one path, such
    as a faceoff circle's two half rings each closing back on its first point: matplotlib fills that as it is, but
    deck.gl triangulates a polygon as one simple ring and fills the wrong side of it. A loop ends where the path comes
    back to that loop's first point, after at least two other points (a repeated first point does not end it); the
    same rule as sdvplot-js's surfaceLayer."""
    # ponytail: a loop inside another would be filled, not cut out as a hole; sportypy builds every ring from two half
    # rings, so none is
    out: list[list[tuple[float, float]]] = []
    loop: list[tuple[float, float]] = []
    away = 0  # points of this loop that are not its first
    for p in xy:
        loop.append(p)
        if len(loop) == 1:
            continue
        if p != loop[0]:
            away += 1
        elif away >= 2:
            out.append(loop)
            loop, away = [], 0
    if away >= 2:
        out.append(loop)  # an open path, closed by deck.gl
    return out


def _signed_area(r: Sequence[Sequence[float]]) -> float:
    a = np.asarray(r, dtype=float)
    b = np.roll(a, -1, axis=0)
    return float(np.sum(a[:, 0] * b[:, 1] - b[:, 0] * a[:, 1])) / 2


def _empty(r: Sequence[Sequence[float]]) -> bool:
    """No area to fill: a path out along a line and back along it (the NLL goal fan), which a fill leaves invisible,
    or the sliver left where a ring touched itself; sdvplot-js's rule (from its three.js surface)."""
    if len(r) < 3:
        return True
    a = np.asarray(r, dtype=float)
    w, h = a.max(axis=0) - a.min(axis=0)
    return abs(_signed_area(r)) <= 1e-9 * (w**2 + h**2)


def _turn(p: Any, q: Any, t: Any) -> Any:
    return (q[..., 0] - p[..., 0]) * (t[..., 1] - p[..., 1]) - (t[..., 0] - p[..., 0]) * (q[..., 1] - p[..., 1])


def _first_crossing(a: Any, b: Any) -> tuple[int, int] | None:
    """The first pair of edges (i, then j > i + 1; edge k runs a[k] -> b[k], the last closing the ring) that cross,
    as sdvplot-js finds it scanning every pair. Edges are sorted into a quadtree first, so an unthinned loop of 40,000
    points is not 800 million pair tests."""
    n = len(a)
    lo, hi = np.minimum(a, b), np.maximum(a, b)
    best: tuple[int, int] | None = None

    def test(i: Any, j: Any) -> None:
        nonlocal best
        i, j = np.minimum(i, j), np.maximum(i, j)
        keep = (j - i >= 2) & ~((i == 0) & (j == n - 1))
        i, j = i[keep], j[keep]
        if i.size == 0:
            return
        ai, bi, c, d = a[i], b[i], a[j], b[j]
        hit = (np.sign(_turn(ai, bi, c)) * np.sign(_turn(ai, bi, d)) < 0) & (
            np.sign(_turn(c, d, ai)) * np.sign(_turn(c, d, bi)) < 0
        )
        for pair in zip(i[hit].tolist(), j[hit].tolist(), strict=True):
            if best is None or pair < best:
                best = pair

    def split(idx: Any, box: Any, depth: int) -> None:
        if len(idx) <= 64 or depth >= 24:
            # a leaf: every pair, in blocks of 512 edges so a dense cell never builds one huge array
            blocks = [idx[k : k + 512] for k in range(0, len(idx), 512)]
            for x, bx in enumerate(blocks):
                u, v = np.triu_indices(len(bx), 1)
                test(bx[u], bx[v])
                for by in blocks[x + 1 :]:
                    u, v = np.meshgrid(bx, by, indexing="ij")
                    test(u.ravel(), v.ravel())
            return
        (x0, y0), (x1, y1) = box
        xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
        for qx0, qy0, qx1, qy1 in ((x0, y0, xm, ym), (xm, y0, x1, ym), (x0, ym, xm, y1), (xm, ym, x1, y1)):
            inside = idx[(lo[idx, 0] <= qx1) & (hi[idx, 0] >= qx0) & (lo[idx, 1] <= qy1) & (hi[idx, 1] >= qy0)]
            if 0 < len(inside) < len(idx):
                split(inside, ((qx0, qy0), (qx1, qy1)), depth + 1)
            elif len(inside) == len(idx):  # every edge spans the cell: nothing to gain by splitting
                split(inside, ((qx0, qy0), (qx1, qy1)), 24)

    split(np.arange(n), (lo.min(axis=0), hi.max(axis=0)), 0)
    return best


def _simple(r: list[list[float]]) -> list[list[list[float]]]:
    """A ring that crosses itself split at each crossing into rings that do not, each to be filled: what an SVG
    (nonzero) fill shows of a figure-of-eight, and what deck.gl's earcut cannot triangulate. sportypy, like sporty, has
    a few (the NHL goaltender's trapezoids). sdvplot-js's rule (from its three.js surface): the first crossing in the
    order i, then j > i + 1, is split first, and each half is split again."""
    if len(r) < 4:
        return [r]
    a = np.asarray(r, dtype=float)
    b = np.roll(a, -1, axis=0)  # edge k runs a[k] -> b[k]
    first = _first_crossing(a, b)
    if first is None:
        return [r]
    i, k = first
    tc, td = _turn(a[k], b[k], a[i]), _turn(a[k], b[k], b[i])
    t = float(tc / (tc - td))  # where the crossing is along a[i] -> b[i]
    x = [float(a[i][0] + t * (b[i][0] - a[i][0])), float(a[i][1] + t * (b[i][1] - a[i][1]))]
    return [*_simple([*r[: i + 1], x, *r[k + 1 :]]), *_simple([x, *r[i + 1 : k + 1]])]


def _simplify(xy: list[tuple[float, float]], tol: float) -> list[list[float]]:
    """``xy`` thinned, rounded to 0.0001 of the unit. A point is kept when it is at least ``t`` from the last point
    kept, or when the next point is at least ``t`` from it: both ends of a long segment stay, so a thin line keeps its
    corners where a lone radial-distance pass would cut across it. ``t`` is ``tol`` capped at the loop's mean width
    (2 x area / perimeter), so a thin band (a 2-inch line, a faceoff ring) is thinned along its length only. The first
    and last points always stay. Measured on all ten sports: every loop within 5% of its area unthinned."""
    # ponytail: a Python loop, about 0.2 s for an NHL rink's 123,000 points; numpy can vectorize the keep test if a
    # surface is ever built in a loop
    a = np.asarray(xy, dtype=float)
    b = np.roll(a, 1, axis=0)
    area = abs(float(np.sum(a[:, 0] * b[:, 1] - b[:, 0] * a[:, 1]))) / 2
    perimeter = float(np.sum(np.hypot(*(a - b).T)))
    t = min(tol, 2 * area / perimeter) if perimeter > 0 else 0.0
    out = [xy[0]]
    for i in range(1, len(xy) - 1):
        p, last, q = xy[i], out[-1], xy[i + 1]
        if math.hypot(p[0] - last[0], p[1] - last[1]) >= t or math.hypot(q[0] - p[0], q[1] - p[1]) >= t:
            out.append(p)
    if len(xy) > 1:
        out.append(xy[-1])
    return [[round(float(x), 4), round(float(y), 4)] for x, y in out]


def surface_layer(
    sport: str, league: str, *, id: str = "sdvplot-surface", tolerance: float | None = None, **sportypy_kwargs: Any
) -> dict[str, Any]:
    """pydeck ``PolygonLayer`` props drawing sportypy's playing surface for ``sport`` and ``league``.

    The surface is in its own coordinates: deck.gl's "cartesian" coordinate system, in the surface's units (feet for
    a rink, metres for a pitch) with the origin at its centre, the frame sportypy draws in and NHL api-web's shot
    coordinates are in. Each closed loop of a visible sportypy feature is one data row (a faceoff circle is two: its
    half rings; a loop that crosses itself, such as a goaltender trapezoid, is split at the crossing into loops that
    do not, and a loop with no area is left out), in sportypy's drawing order (its zorder), filled with its color
    (alpha included); a hidden one (a ``#rrggbb00`` fill, or none) is left out. sportypy draws arcs with up to 8,000
    points (80,000 before sportypy 1.2.2); each loop is thinned to ``tolerance`` (see below), which leaves an NHL rink
    about 14,400 points instead of 123,000, and the coordinates are rounded to 0.0001 of the unit, so a deck stays a
    few hundred kilobytes.
    sdvplot-js's ``surfaceLayer`` draws sporty's own
    geometry, so the two languages' vertices differ (the props, colors and extents agree).

    Args:
        sport: The sportypy sport: "hockey", "soccer", "basketball", "football", "baseball", "softball", "lacrosse",
            "tennis", "volleyball" or "curling".
        league: sportypy's league code for the sport, e.g. "nhl", "fifa", "nba".
        id: The layer id.
        tolerance: The simplification distance, in the surface's units; None for a 2,000th of the surface's
            diagonal (about 0.11 ft on an NHL rink), 0 to keep every point. Each loop caps it at its own mean width
            and keeps both ends of every segment at least that long, so thin lines and rings keep their corners and
            shape (every loop within 5% of its area unthinned, measured on all ten sports).
        **sportypy_kwargs: Passed to the sportypy surface class: ``rink_updates`` / ``pitch_updates`` /
            ``court_updates`` / ``field_updates``, ``color_updates``, ``units``.

    Returns:
        dict: ``pydeck.Layer`` keyword arguments: ``type`` "PolygonLayer", ``data`` (one dict per closed loop of a
        feature: ``name``, sportypy's class name in snake case, ``polygon`` and ``fillColor`` as ``[r, g, b, a]``),
        the accessors ``get_polygon`` and ``get_fill_color``, ``coordinate_system`` "'cartesian'" (quoted, a
        constant), ``filled`` and ``stroked``.

    Raises:
        InputError: (a ValueError) If sportypy has no surface for ``sport``, no ``league`` for it, or ``tolerance`` is
            negative.
        OptionalDependencyError: If the surfaces extra (sportypy) is not installed.

    Example:
        ::

            import sdvplot.pydeck

            rink = sdvplot.pydeck.surface_layer("hockey", "nhl")
            assert rink["coordinate_system"] == "'cartesian'"  # quoted: a constant, not an expression
            assert rink["data"][0]["name"] == "defensive_zone"

    See Also:
        sportypy: https://sportypy.sportsdataverse.org/ ;
        deck.gl PolygonLayer: https://deck.gl/docs/api-reference/layers/polygon-layer
    """
    if sport not in _SPORTS:
        raise InputError(f"no sportypy surface for sport {sport!r}; supported: {sorted(_SPORTS)}")
    if tolerance is not None and not (_real(tolerance) and tolerance >= 0):
        raise InputError(f"tolerance is a distance in the surface's units, 0 or more, got {tolerance!r}")
    try:
        module = importlib.import_module(f"sportypy.surfaces.{sport}")
    except ModuleNotFoundError as e:
        raise OptionalDependencyError(
            'sdvplot.pydeck.surface_layer() needs the surfaces extra: pip install "sdvplot[surfaces]"', name=e.name
        ) from e
    drawing = getattr(module, _SPORTS[sport])(league_code=league, **sportypy_kwargs)
    if drawing.league_code not in drawing.league_dimensions:
        raise InputError(
            f"sportypy has no {sport} surface for {league!r}; supported: {sorted(drawing.league_dimensions)}"
        )
    features = []
    # ponytail: reads sportypy's private members (the surface's `_features`, each feature's `_translate_feature()` and
    # `plot_kwargs`, `visible`), as sportypy 1.0 has no public geometry API; pin them if sportypy ever adds one
    for order, f in enumerate(drawing._features):
        fill = f.plot_kwargs.get("facecolor")
        if not f.visible or not fill or re.fullmatch(r"#?[0-9a-fA-F]{6}00", str(fill)):
            continue
        df = f._translate_feature()
        xy = list(zip(df["x"].tolist(), df["y"].tolist(), strict=True))
        if not xy or not all(math.isfinite(a) and math.isfinite(b) for a, b in xy):
            continue
        features.append((f.plot_kwargs.get("zorder", 0), order, f, xy))
    features.sort(key=lambda t: (t[0], t[1]))  # matplotlib draws by zorder, then in the order added
    if tolerance is None:
        xs = [p[0] for *_, xy in features for p in xy]
        ys = [p[1] for *_, xy in features for p in xy]
        tolerance = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) / 2000 if xs else 0
    data = [
        {
            "name": re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", type(f).__name__).lower(),
            "polygon": ring,
            "fillColor": _rgba(str(f.plot_kwargs["facecolor"])),
        }
        for _, _, f, xy in features
        for loop in _loops(xy)
        for ring in _simple(_simplify(loop, tolerance))
        if not _empty(ring)
    ]
    return {
        "type": "PolygonLayer",
        "id": id,
        "data": data,
        "get_polygon": "polygon",
        "get_fill_color": "fillColor",
        "coordinate_system": _CARTESIAN,
        "filled": True,
        "stroked": False,
    }


def deck(*layers: Mapping[str, Any], height: int = 480, width: int = 720, **deck_kwargs: Any) -> pydeck.Deck:
    """A ``pydeck.Deck`` of sdvplot layer props, its view fitted to them.

    With a ``surface_layer`` among them, the deck has a top-down OrthographicView (y up) fitted to the surface, and
    every other layer is drawn in the surface's own coordinates. Without one, it is a map, fitted to the layers'
    positions (longitude and latitude). The layers are drawn in the order given.

    Args:
        *layers: Props from ``surface_layer``, ``logo_icon_layer``, ``pass_arc_layer`` or any other
            ``pydeck.Layer`` keyword arguments.
        height: The deck's height in px.
        width: The width in px the view is fitted to (the deck itself fills its container's width).
        **deck_kwargs: Passed to ``pydeck.Deck`` (``tooltip``, ``map_style``, ...).

    Returns:
        pydeck.Deck: The deck; show it in a notebook, or ``to_html()`` it.

    Raises:
        InputError: (a ValueError) If no layer is given, or ``height`` or ``width`` is under 1 px.

    Example:
        ::

            import sdvplot.pydeck

            rink = sdvplot.pydeck.surface_layer("hockey", "nhl")
            d = sdvplot.pydeck.deck(rink, height=300)
            assert d.views[0].type == "OrthographicView"

    See Also:
        pydeck Deck: https://deckgl.readthedocs.io/en/latest/deck.html
    """
    if not layers:
        raise InputError("deck() needs at least one layer")
    _px("height", height)
    _px("width", width)
    surfaces = [p for p in layers if p.get("coordinate_system") == _CARTESIAN and p.get("type") == "PolygonLayer"]
    if surfaces:
        pts = [pt for s in surfaces for d in s["data"] for pt in d["polygon"]]
        x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
        y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
        zoom = math.log2(min(width / (x1 - x0), height / (y1 - y0)))
        view = pydeck.View(type="OrthographicView", controller=True, flip_y=False)
        state = pydeck.ViewState(target=[(x0 + x1) / 2, (y0 + y1) / 2, 0], zoom=zoom)
        built = [pydeck.Layer(**{"coordinate_system": _CARTESIAN, **p}) for p in layers]
        return pydeck.Deck(layers=built, views=[view], initial_view_state=state, map_provider=None, height=height,
                           **deck_kwargs)  # fmt: skip
    points = [
        pt
        for p in layers
        for d in p.get("data", [])
        if isinstance(d, Mapping)
        for pt in ([d["position"]] if "position" in d else [d[k] for k in ("source", "target") if k in d])
    ]
    state = pydeck.data_utils.compute_view(points) if points else pydeck.ViewState(latitude=0, longitude=0, zoom=1)
    return pydeck.Deck(layers=[pydeck.Layer(**p) for p in layers], initial_view_state=state, height=height,
                       **deck_kwargs)  # fmt: skip

"""The Altair adapter: logos, wordmarks and headshots as a native Vega-Lite image layer.

An image's size is a mark-level pixel property, so a layer's images are ``height`` times the chart height (in
pixels) tall, each fitted by height (``aspect=True``) inside a box as wide as the widest mark. ``add_logos`` returns a
new ``LayerChart`` (Altair charts are immutable values); grammar users can layer ``logo_layer(...)`` themselves.
"""

from __future__ import annotations

import json
import math
import numbers
import re
from typing import Any

from sdvplot._errors import UnsupportedTargetError, requires_extra

with requires_extra("altair"):
    import altair as alt

from sdvplot._placement import Placement, check_alpha, check_height, place
from sdvplot._web import aspect, axis_letter, image_sources

_SUPPORTS_AXIS_LOGOS = True
_VEGA_LITE_DEFAULT_HEIGHT = 300  # px: Vega-Lite's continuous view height when neither chart nor theme sets one
_AXIS_GAP = 6  # px between the axis line and the axis images (past Vega-Lite's 5 px ticks)
_VEGA_LITE_LABEL_PADDING = 2  # px: Vega-Lite's default axis labelPadding
_URL, _TEAM = "sdvplot_url", "sdvplot_team"  # the image layer's own columns
_DISCRETE = ("nominal", "ordinal")
_SUBCHARTS = {"FacetChart": "spec", "RepeatChart": "spec", "HConcatChart": "hconcat[i]",
              "VConcatChart": "vconcat[i]", "ConcatChart": "concat[i]"}  # fmt: skip
_BLANKED = re.compile(r"^indexof\((\[.*?\]), datum\.label\) >= 0")

__all__ = ["add_headshots", "add_logos", "add_wordmarks", "axis_logos", "logo_layer"]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)


def _jsonable(v: Any) -> Any:
    """A position value Vega-Lite can read from inline data: numbers as numbers, dates as ISO strings."""
    if hasattr(v, "item") and not hasattr(v, "isoformat"):
        v = v.item()  # a numpy scalar
    return v.isoformat() if hasattr(v, "isoformat") else v


def _key(field: str) -> str:
    """A Vega-Lite field name ("a\\.b") as its data column ("a.b")."""
    return re.sub(r"\\(.)", r"\1", field)


def _check_chart(chart: Any) -> None:
    name = type(chart).__name__
    if name in _SUBCHARTS:
        raise ValueError(
            f"sdvplot cannot draw on a {name}; draw on one of its charts (chart.{_SUBCHARTS[name]}), then combine"
        )
    if not isinstance(chart, (alt.Chart, alt.LayerChart)):
        raise UnsupportedTargetError(f"sdvplot.altair draws on an altair Chart or LayerChart, got {name}")


def _units(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """A chart spec and every layer inside it, outermost first."""
    out = [spec]
    for sub in spec.get("layer", []):
        out += _units(sub)
    return out


def _unit(spec: dict[str, Any], channel: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """The first (unit spec, channel definition) that encodes ``channel`` with a field; ({}, {}) when none does."""
    for u in _units(spec):
        enc = u.get("encoding", {}).get(channel)
        if isinstance(enc, dict) and "field" in enc:
            return u, enc
    return {}, {}


def _pixels(h: Any, name: str) -> float:
    """``h`` as a float, or ValueError unless it is a finite number of pixels above zero."""
    if not isinstance(h, numbers.Real) or isinstance(h, bool) or not math.isfinite(h) or h <= 0:
        raise ValueError(
            f"sdvplot sizes marks from the chart height; {name} must be a positive number of pixels, not {h!r}"
        )
    return float(h)


def _chart_height(spec: dict[str, Any]) -> float:
    """The chart's plot height in pixels: its own, else the theme's (or Vega-Lite's) continuous view height."""
    for u in _units(spec):
        h = u.get("height")
        if h is not None:
            return _pixels(h, ".properties(height=...)")
    if _unit(spec, "y")[1].get("type") in _DISCRETE:
        raise ValueError(
            "a discrete y axis is sized by its step; set the chart height in pixels: .properties(height=...)"
        )
    h = spec.get("config", {}).get("view", {}).get("continuousHeight", _VEGA_LITE_DEFAULT_HEIGHT)
    return _pixels(h, "config.view.continuousHeight")


def _sort(enc: dict[str, Any], channel: str) -> Any:
    """The discrete axis' sort, when Vega-Lite keeps it once another layer shares the scale (it drops the rest)."""
    sort = enc.get("sort", "ascending")
    kept = (
        sort is None
        or sort in ("ascending", "descending")
        or isinstance(sort, list)
        or (isinstance(sort, dict) and "field" in sort and sort.get("op") in ("count", "min", "max"))
    )
    if not kept:
        raise ValueError(
            f"Vega-Lite drops the {channel} sort {sort!r} once a layer is added; sort with an explicit list "
            "(sort=[...]) or by a field with op 'count', 'min' or 'max', then add the marks"
        )
    return sort


def _encodings(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """The x and y encodings the image layer copies from the chart: field name, type, time unit and (discrete) sort.

    A time unit is copied (the layer applies it to its own positions, as the chart does); an aggregate or a bin is
    not, as it would be computed over the layer's few rows, so it raises.
    """
    out = {}
    for ch in ("x", "y"):
        enc = _unit(spec, ch)[1]
        for key in ("aggregate", "bin"):
            if enc.get(key) not in (None, False, "binned"):
                raise ValueError(
                    f"the chart's {ch} encoding has {key}={enc[key]!r}, which the logo layer cannot copy; compute it "
                    "in the data first (e.g. with pandas), encode the result, then add the marks"
                )
        e: dict[str, Any] = {"field": enc.get("field", ch), "type": enc.get("type", "quantitative")}
        if "timeUnit" in enc:
            e["timeUnit"] = enc["timeUnit"]
        if e["type"] in _DISCRETE and "sort" in enc:
            e["sort"] = _sort(enc, ch)
        out[ch] = e
    return out


def _layer(
    placements: list[Placement],
    *,
    kind: str,
    height: float,
    chart_height: float,
    alpha: float,
    x: dict[str, Any],
    y: dict[str, Any],
    embed: bool,
) -> alt.Chart:
    h_px = height * chart_height
    rows = [
        {_key(x["field"]): _jsonable(p.x), _key(y["field"]): _jsonable(p.y), _URL: src, _TEAM: p.team_id}
        for p, src in zip(placements, image_sources(placements, embed=embed), strict=True)
    ]
    widest = max((aspect(p) for p in placements), default=1.0)
    return (
        alt.Chart(alt.Data(values=rows), name=f"sdvplot_{kind}")
        .mark_image(width=h_px * widest, height=h_px, aspect=True, opacity=alpha)
        .encode(x=alt.X(**x), y=alt.Y(**y), url=alt.Url(_URL, type="nominal"))
    )


def logo_layer(
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    chart_height: float | None = None,
    alpha: float = 1,
    variant: str = "default",
    x_type: str = "quantitative",
    y_type: str = "quantitative",
    embed: bool = False,
    id_system: str = "auto",
) -> alt.Chart:
    """A Vega-Lite image layer of team logos, to layer onto a chart: ``alt.layer(chart, logo_layer(...))``.

    The layer encodes its own columns named ``x`` and ``y``, so give your chart explicit axis titles (an explicit title
    wins over the layer's), or use ``add_logos``, which reuses the chart's own field names, types and sort.

    Args:
        x: The points' x positions, in the chart's x values (numbers, category names or dates).
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point, to pick each team's mark for that era.
        height: The logo height as a fraction of the chart height, in (0, 1].
        chart_height: The chart's height in pixels (a positive number); None means Vega-Lite's default (300).
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        x_type: The Vega-Lite type of the chart's x axis ("quantitative", "nominal", "ordinal", "temporal").
        y_type: The Vega-Lite type of the chart's y axis.
        embed: Inline each image as a data URI (HTML that renders offline, and PNG export with vl-convert) instead of
            linking its URL.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        altair.Chart: The image layer.

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant``
            is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If ``chart_height`` is not a positive number of pixels, or the inputs differ in length.
        OfflineError: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a
            DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a
            file that does not match the manifest's sha256).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would
            put the file outside the cache directory.

    Example:
        ::

            import altair as alt
            import pandas as pd
            import sdvplot.altair as salt

            df = pd.DataFrame({"x": [10, 20], "y": [-3, -7], "team": ["KC", "BUF"]})
            points = alt.Chart(df).mark_point().encode(x=alt.X("x", title="EPA"), y=alt.Y("y", title="Success"))
            alt.layer(points, salt.logo_layer(df["x"], df["y"], df["team"], league="nfl", height=0.12))

    See Also:
        sdvplotR geom_nfl_logos(): https://sdvplotR.sportsdataverse.org/ ;
        Altair image marks: https://altair-viz.github.io/user_guide/marks/image.html
    """
    h, a = check_height(height), check_alpha(alpha)
    placements = place(x, y, teams, league=league, season=season, kind="logo", variant=variant, id_system=id_system)
    return _layer(
        placements, kind="logo", height=h, alpha=a,
        chart_height=_VEGA_LITE_DEFAULT_HEIGHT if chart_height is None else _pixels(chart_height, "chart_height"),
        x={"field": "x", "type": x_type}, y={"field": "y", "type": y_type}, embed=embed,
    )  # fmt: skip


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
) -> alt.LayerChart:
    h, a = check_height(height), check_alpha(alpha)
    _check_chart(chart)
    spec = chart.to_dict()
    enc = _encodings(spec)
    placements = place(x, y, teams, league=league, season=season, kind=kind, variant=variant, id_system=id_system)
    layer = _layer(placements, kind=kind, height=h, chart_height=_chart_height(spec), alpha=a, x=enc["x"], y=enc["y"],
                   embed=embed)  # fmt: skip
    return chart + layer


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
) -> alt.LayerChart:
    """Layer each team's logo, centred on its (x, y) point, onto an Altair chart.

    The image layer reuses the chart's x/y field names, types, time units and sort, so a nominal axis stays nominal,
    a logo on ``yearmonth(date)`` sits on its month, and the axis titles stay as they were. An aggregated or binned
    axis is not copied: aggregate or bin in the data first.

    Args:
        chart: An ``altair.Chart`` or ``LayerChart`` (facet, concat and repeat charts: pass one of their charts).
        x: The points' x positions, in the chart's x values.
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point, to pick each team's mark for that era.
        height: The logo height as a fraction of the chart height, in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        altair.LayerChart: A new chart, ``chart`` plus the image layer (``chart`` itself is unchanged).

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant``
            is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If the inputs differ in length, the chart is a facet, concat or repeat chart, its height is not a
            positive number of pixels where it must be, its x or y encoding aggregates or bins, or a discrete axis is
            sorted in a way Vega-Lite drops once layers share the axis.
        UnsupportedTargetError: (a TypeError) If ``chart`` is not an Altair ``Chart`` or ``LayerChart``.
        OfflineError: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a
            DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a
            file that does not match the manifest's sha256).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would
            put the file outside the cache directory.

    Example:
        ::

            import altair as alt
            import pandas as pd
            import sdvplot

            df = pd.DataFrame({"epa": [0.2, 0.1], "sr": [0.48, 0.45], "team": ["KC", "BUF"]})
            chart = alt.Chart(df).mark_point().encode(x="epa", y="sr")
            chart = sdvplot.add_logos(chart, df["epa"], df["sr"], df["team"], league="nfl", height=0.12)

    See Also:
        sdvplotR geom_nfl_logos(): https://sdvplotR.sportsdataverse.org/
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
) -> alt.LayerChart:
    """Layer each team's wordmark, centred on its (x, y) point, onto an Altair chart.

    Args:
        chart: An ``altair.Chart`` or ``LayerChart``.
        x: The points' x positions, in the chart's x values.
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season, or one per point.
        height: The wordmark height as a fraction of the chart height, in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        altair.LayerChart: A new chart, ``chart`` plus the image layer.

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league``, ``id_system`` or ``variant``
            is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If the inputs differ in length, or the chart cannot take a layer (see ``add_logos``).
        UnsupportedTargetError: (a TypeError) If ``chart`` is not an Altair ``Chart`` or ``LayerChart``.
        OfflineError: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a
            DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a
            file that does not match the manifest's sha256).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would
            put the file outside the cache directory.

    Example:
        ::

            import altair as alt
            import pandas as pd
            import sdvplot

            df = pd.DataFrame({"team": ["KC", "BUF"], "wins": [12, 10]})
            bars = alt.Chart(df).mark_bar().encode(x=alt.X("team", sort=None), y="wins")
            sdvplot.add_wordmarks(bars, df["team"], df["wins"], df["team"], league="nfl", height=0.06)

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
) -> alt.LayerChart:
    """Layer each player's headshot, centred on its (x, y) point, onto an Altair chart.

    Args:
        chart: An ``altair.Chart`` or ``LayerChart``.
        x: The points' x positions, in the chart's x values.
        y: The points' y positions, the same length as ``x``.
        players: The player id for each point.
        league: The SDV league key, e.g. "nfl".
        height: The headshot height as a fraction of the chart height, in (0, 1].
        alpha: Opacity, 0 to 1.
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``.

    Returns:
        altair.LayerChart: A new chart, ``chart`` plus the image layer.

    Raises:
        InputError: (a ValueError) If ``height`` or ``alpha`` is out of range, ``league`` has no ESPN headshots, or
            ``id_system`` is not valid for ``league``.
        ValueError: If the inputs differ in length, or the chart cannot take a layer (see ``add_logos``).
        UnsupportedTargetError: (a TypeError) If ``chart`` is not an Altair ``Chart`` or ``LayerChart``.
        OfflineError: If the nflverse player table (``id_system="gsis"``), or with ``embed=True`` a headshot, is neither
            cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.

    Example:
        ::

            import altair as alt
            import pandas as pd
            import sdvplot

            df = pd.DataFrame({"x": [0.3], "y": [0.5], "player": ["3139477"]})
            chart = alt.Chart(df).mark_point().encode(x="x", y="y")
            sdvplot.add_headshots(chart, df["x"], df["y"], df["player"], league="nfl", height=0.2)

    See Also:
        sdvplotR geom_nfl_headshots(): https://sdvplotR.sportsdataverse.org/
    """
    return _add(
        chart, x, y, players, kind="headshot", league=league, season=None, height=height, alpha=alpha,
        variant="default", embed=embed, id_system=id_system,
    )  # fmt: skip


def _categories(spec: dict[str, Any], unit: dict[str, Any], enc: dict[str, Any]) -> list[Any]:
    """A discrete axis' categories in display order, from its explicit domain or sort list, or the inline data."""
    domain = enc.get("scale", {}).get("domain")
    if isinstance(domain, list):
        return domain
    sort = enc.get("sort", "ascending")
    data = unit.get("data") or spec.get("data") or {}
    rows = spec.get("datasets", {}).get(data.get("name"), data.get("values"))
    if rows is None:
        if isinstance(sort, list):
            return sort
        raise ValueError("axis_logos reads the categories from inline data; give the axis an explicit sort=[...] list")
    key = _key(enc["field"])
    seen = list(dict.fromkeys(r.get(key) for r in rows if r.get(key) is not None))
    if isinstance(sort, list):
        return sort + [c for c in seen if c not in sort]
    if sort in ("ascending", "descending"):
        return sorted(seen, reverse=sort == "descending")
    return seen  # sort=None, or a field sort: data order


def _target_channel(chart: Any, channel: str) -> Any:
    """The channel object (alt.X / alt.Y) the chart's spec reads the axis from: the first with a field, as ``_unit``."""
    enc: Any = getattr(chart, "encoding", alt.Undefined)
    ch: Any = alt.Undefined if enc is alt.Undefined else getattr(enc, channel, alt.Undefined)
    # ``field`` or the ``alt.X("team")`` shorthand: reading either does not serialize the channel, which Altair refuses
    # for an untyped channel when the chart's data is not at hand
    if ch is not alt.Undefined and any(
        getattr(ch, a, alt.Undefined) is not alt.Undefined for a in ("field", "shorthand")
    ):
        return ch
    for sub in getattr(chart, "layer", None) or []:
        found = _target_channel(sub, channel)
        if found is not None:
            return found
    return None


def axis_logos(
    chart: Any,
    axis: str,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    variant: str = "default",
    mark_type: str = "logo",
    embed: bool = False,
    id_system: str = "auto",
) -> alt.LayerChart:
    """Replace a discrete axis' team labels with the teams' logos (or wordmarks).

    The images are a layer placed just outside the plot (under the x axis, left of the y axis), ``height`` of the chart
    height tall; the axis' ``labelExpr`` blanks only the labels that became images and its ``labelPadding`` grows past
    them, so labels that are not teams stay as text (with one SdvplotWarning). The categories come from an explicit
    scale domain or sort list, or the chart's inline data.

    Args:
        chart: An ``altair.Chart`` or ``LayerChart`` with a nominal or ordinal ``axis``.
        axis: "x" or "y".
        league: The SDV league key, e.g. "nfl".
        season: One season for every label.
        height: The image height as a fraction of the chart height, in (0, 1].
        variant: "default", "dark", or a named variant from ``marks()``.
        mark_type: "logo" or "wordmark".
        embed: Inline each image as a data URI instead of linking its URL.
        id_system: The id system of the labels; "auto" tries each in order.

    Returns:
        altair.LayerChart: A new chart: ``chart`` with the axis labels blanked, plus the image layer.

    Raises:
        InputError: (a ValueError) If ``height`` is out of range, ``league``, ``id_system``, ``mark_type`` or
            ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
        ValueError: If ``axis`` is not "x"/"y", the axis is not discrete or is hidden, the categories cannot be read, or
            the chart cannot take a layer (see ``add_logos``).
        UnsupportedTargetError: (a TypeError) If ``chart`` is not an Altair ``Chart`` or ``LayerChart``.
        OfflineError: If the logo manifest, or with ``embed=True`` a mark's image, is neither cached nor downloadable (a
            DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a
            file that does not match the manifest's sha256).
        UnsafeDownloadError: (an OSError) If a download is refused: larger than the byte cap, past the deadline, or
            redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``embed=True`` and the manifest's sha256 or extension for a mark would
            put the file outside the cache directory.

    Example:
        ::

            import altair as alt
            import pandas as pd
            import sdvplot

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [12, 10, 9]})
            bars = alt.Chart(df).mark_bar().encode(x=alt.X("team", sort=None), y="wins")
            sdvplot.axis_logos(bars, "x", league="nfl", height=0.1)

    See Also:
        sdvplotR element_sdv_logo(): https://sdvplotR.sportsdataverse.org/
    """
    letter = axis_letter(axis)
    h = check_height(height)
    _check_chart(chart)
    spec = chart.to_dict()
    unit, enc = _unit(spec, letter)
    if enc.get("type") not in _DISCRETE:
        raise ValueError(f"axis_logos needs a nominal or ordinal {letter} axis (team names on the axis)")
    if enc.get("axis", {}) is None:
        raise ValueError(f"the chart's {letter} axis is hidden (axis=None)")
    sort = _sort(enc, letter)
    cats = _categories(spec, unit, enc)
    index: list[Any] = list(range(len(cats)))
    across: list[Any] = [0.0] * len(cats)
    xs, ys = (index, across) if letter == "x" else (across, index)
    placements = place(xs, ys, [str(c) for c in cats], league=league, season=season, kind=mark_type, variant=variant,
                       id_system=id_system)  # fmt: skip
    chart_h = _chart_height(spec)
    h_px = h * chart_h
    widest = max((aspect(p) for p in placements), default=1.0)
    pos = [int(p.x if letter == "x" else p.y) for p in placements]
    blank = json.dumps([str(cats[i]) for i in pos])
    # the axis: blank the labels that became images, and move the rest past the images
    old = dict(enc.get("axis", {}))
    room = (h_px if letter == "x" else h_px * widest) + _AXIS_GAP
    expr = f"indexof({blank}, datum.label) >= 0 ? '' : " + (
        f"({old['labelExpr']})" if "labelExpr" in old else "datum.label"
    )
    base = chart.copy(deep=True)
    _target_channel(base, letter).axis = alt.Axis(
        **{**old, "labelExpr": expr, "labelPadding": old.get("labelPadding", _VEGA_LITE_LABEL_PADDING) + room}
    )
    key = _key(enc["field"])
    rows = [{key: cats[i], _URL: src, _TEAM: p.team_id}
            for i, p, src in zip(pos, placements, image_sources(placements, embed=embed), strict=True)]  # fmt: skip
    channel = {"field": enc["field"], "type": enc["type"], **({"sort": sort} if "sort" in enc else {})}
    layer = alt.Chart(alt.Data(values=rows), name=f"sdvplot_axis_{letter}")
    url = alt.Url(_URL, type="nominal")
    if letter == "x":  # under the plot: the images hang from just below the x axis
        layer = layer.mark_image(width=h_px * widest, height=h_px, aspect=True, baseline="top").encode(
            x=alt.X(**channel), y=alt.value(chart_h + _AXIS_GAP), url=url
        )
    else:  # left of the plot: the images end just left of the y axis
        layer = layer.mark_image(width=h_px * widest, height=h_px, aspect=True, align="right").encode(
            y=alt.Y(**channel), x=alt.value(-_AXIS_GAP), url=url
        )
    return base + layer


def _named(chart: Any, prefix: str) -> list[Any]:
    """Every layer of ``chart`` (itself included) whose name starts with ``prefix``, in layer order."""
    found = [chart] if isinstance(getattr(chart, "name", None), str) and chart.name.startswith(prefix) else []
    for sub in getattr(chart, "layer", []) or []:
        found += _named(sub, prefix)
    return found


def _drawn_marks(chart: Any) -> list[tuple[Any, ...]]:
    """Test hook: (team_id, x, y, height, url) per image of the sdvplot layers; height = image px / chart px."""
    ref = _chart_height(chart.to_dict())
    out = []
    for layer in _named(chart, "sdvplot_"):
        if layer.name.startswith("sdvplot_axis_"):
            continue
        xk, yk = _key(layer.encoding.x.to_dict()["field"]), _key(layer.encoding.y.to_dict()["field"])
        out += [(r[_TEAM], r[xk], r[yk], layer.mark.height / ref, r[_URL]) for r in layer.data.values]
    return out


def _drawn_axis_marks(chart: Any, axis: str) -> list[tuple[str, float, float]]:
    """Test hook: (team_id, category position, height) for each image on ``axis``, in tick order; height = image px /
    chart px."""
    letter = axis_letter(axis)
    spec = chart.to_dict()
    unit, enc = _unit(spec, letter)
    cats = _categories(spec, unit, enc)
    ref = _chart_height(spec)
    marks = []
    for layer in _named(chart, f"sdvplot_axis_{letter}"):
        key = _key(getattr(layer.encoding, letter).to_dict()["field"])
        marks += [(r[_TEAM], float(cats.index(r[key])), layer.mark.height / ref) for r in layer.data.values]
    return sorted(marks, key=lambda m: m[1])


def _visible_axis_labels(chart: Any, axis: str) -> list[str]:
    """Test hook: the labels on ``axis`` the axis' labelExpr still shows as text."""
    letter = axis_letter(axis)
    spec = chart.to_dict()
    unit, enc = _unit(spec, letter)
    found = _BLANKED.match(enc.get("axis", {}).get("labelExpr", ""))
    blanked = set(json.loads(found.group(1))) if found else set()
    return [str(c) for c in _categories(spec, unit, enc) if str(c) not in blanked]

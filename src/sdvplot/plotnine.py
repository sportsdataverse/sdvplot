"""The plotnine adapter: logo, wordmark and headshot geoms, axis logos, and team color scales.

The geoms draw through the matplotlib adapter (sdvplot.matplotlib.draw_placements), so sizing matches it: ``height``
is a fraction of each panel's height. ``add_logos(p, ...)`` returns a new ggplot (plotnine's ``+`` copies).
"""

from __future__ import annotations

import warnings
from typing import Any

import pandas as pd
from matplotlib.figure import Figure
from plotnine import aes, element_text, ggplot, scale_color_manual, scale_fill_manual, theme
from plotnine.geoms.geom import geom

from sdvplot._colors import _column, team_colors
from sdvplot._errors import SdvplotWarning
from sdvplot._marks import _check_mark_type
from sdvplot._placement import Placement, check_alpha, check_height, place
from sdvplot._resolve import _seasons, _unpack
from sdvplot.matplotlib import _in_view, draw_placements
from sdvplot.matplotlib import axis_logos as _mpl_axis_logos
from sdvplot.matplotlib import drawn_axis_marks as _mpl_drawn_axis_marks
from sdvplot.matplotlib import drawn_marks as _mpl_drawn_marks
from sdvplot.matplotlib import visible_axis_labels as _mpl_visible_axis_labels

SUPPORTS_AXIS_LOGOS = True
_MARK_PARAMS = {
    "stat": "identity",
    "position": "identity",
    "na_rm": False,
    "league": None,
    "season": None,
    "height": 0.1,
    "alpha": 1,
    "variant": "default",
    "id_system": "auto",
}


class _geom_sdv_marks(geom):
    """Shared drawing for the three mark geoms; subclasses set the kind and the id aesthetic."""

    _kind = "logo"
    _id_aes = "team"
    DEFAULT_AES: dict[str, Any] = {"season": None}  # optional: one season per row, which plotnine copies with the row
    REQUIRED_AES = {"x", "y", "team"}
    DEFAULT_PARAMS = _MARK_PARAMS

    def __init__(self, mapping: Any = None, data: Any = None, **kwargs: Any) -> None:
        if kwargs.get("league") is None:
            raise TypeError(f"{type(self).__name__}() needs league=, e.g. league='nfl'")
        check_height(kwargs.get("height", 0.1))
        check_alpha(kwargs.get("alpha", 1))
        kwargs.setdefault("show_legend", False)
        super().__init__(mapping, data, **kwargs)

    def _place(self, data: pd.DataFrame, x: list[Any], y: list[Any]) -> list[Placement]:
        p = self.params
        # the season= parameter, else the season aesthetic (a column, so each panel's copy of a row keeps its season)
        season = p["season"] if p["season"] is not None or "season" not in data else data["season"].tolist()
        return place(x, y, data[self._id_aes].tolist(), league=p["league"], season=season, kind=self._kind,
                     variant=p["variant"], id_system=p["id_system"])  # fmt: skip

    def setup_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Once per layer and render: place every panel's rows together, so an unknown team or a missing mark warns
        once. At zero positions: x and y are plotnine's to check, after this (``na_rm``, scale limits, its own
        "Removed rows" warning), so they never warn here."""
        zeros = [0.0] * len(data)
        self._place(data, zeros, zeros)
        return data

    def draw_panel(self, data: pd.DataFrame, panel_params: Any, coord: Any, ax: Any) -> None:
        # ponytail: setup_data already warned for this layer's rows in every panel; a point that only a coord_trans
        # makes missing is skipped quietly here (warn from draw_panel too if that case ever matters)
        data = coord.transform(data, panel_params)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SdvplotWarning)
            placements = self._place(data, data["x"].tolist(), data["y"].tolist())
        draw_placements(ax, placements, height=float(self.params["height"]), alpha=float(self.params["alpha"]))


class geom_sdv_logos(_geom_sdv_marks):
    """Team logos at (x, y): ``aes(x=..., y=..., team=...)``, plus ``league=`` and optional ``season``, ``height``
    (fraction of the panel height), ``alpha``, ``variant`` and ``id_system``. For a season per row, map it instead:
    ``aes(..., season="season")`` (a ``season=`` parameter wins over the mapping).

    Example:
        ::

            import pandas as pd
            from plotnine import aes, ggplot
            from sdvplot.plotnine import geom_sdv_logos

            df = pd.DataFrame({"team": ["KC", "BUF"], "epa": [0.2, 0.15], "sr": [0.48, 0.47]})
            p = ggplot(df, aes("epa", "sr", team="team")) + geom_sdv_logos(league="nfl", height=0.12)
    """


class geom_sdv_wordmarks(_geom_sdv_marks):
    """Team wordmarks at (x, y): the same aesthetics and parameters as ``geom_sdv_logos``.

    Example:
        ::

            p = ggplot(df, aes("epa", "sr", team="team")) + geom_sdv_wordmarks(league="nfl", height=0.08)
    """

    _kind = "wordmark"


class geom_sdv_headshots(_geom_sdv_marks):
    """Player headshots at (x, y): ``aes(x=..., y=..., player_id=...)``, plus ``league=`` and ``id_system``
    ("espn" or "gsis"), ``height`` and ``alpha``.

    Example:
        ::

            p = ggplot(df, aes("x", "y", player_id="espn_id")) + geom_sdv_headshots(league="nfl", height=0.15)
    """

    _kind = "headshot"
    _id_aes = "player_id"
    REQUIRED_AES = {"x", "y", "player_id"}
    DEFAULT_PARAMS = {**_MARK_PARAMS, "id_system": "espn"}


def _frame(x: Any, y: Any, ids: Any, column: str, season: Any = None) -> pd.DataFrame:
    """The layer data: one row per point, with its season, so plotnine's per-panel copies of a row keep it."""
    xs, ys, ts = _unpack(x)[0], _unpack(y)[0], _unpack(ids)[0]
    if not len(xs) == len(ys) == len(ts):
        raise ValueError(f"x, y and teams must have the same length, got {len(xs)}, {len(ys)} and {len(ts)}")
    return pd.DataFrame({"x": xs, "y": ys, column: ts, "season": pd.Series(_seasons(season, len(ts)), dtype=object)})


def add_logos(
    target: ggplot,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = "default",
    id_system: str = "auto",
) -> ggplot:
    """A copy of the plot with each team's logo at its (x, y); the front door's plotnine adapter.

    Args:
        target: A plotnine ggplot.
        x: The points' x positions (read by position).
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point, in any id system ``resolve()`` understands.
        league: The SDV league key, e.g. "nfl".
        season: One season for every point.
        height: The logo height as a fraction of the panel height, in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        id_system: The id system of ``teams``; "auto" tries each in order.

    Returns:
        ggplot: A new plot with a ``geom_sdv_logos`` layer; ``target`` is unchanged.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, or the inputs differ in length.

    Example:
        ::

            import sdvplot
            p2 = sdvplot.add_logos(p, [0.2], [0.48], ["KC"], league="nfl")
    """
    layer = geom_sdv_logos(
        aes("x", "y", team="team", season="season"), data=_frame(x, y, teams, "team", season), inherit_aes=False,
        league=league, height=height, alpha=alpha, variant=variant, id_system=id_system,
    )  # fmt: skip
    return target + layer


def add_wordmarks(
    target: ggplot,
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    alpha: float = 1,
    variant: str = "default",
    id_system: str = "auto",
) -> ggplot:
    """A copy of the plot with each team's wordmark at its (x, y).

    Args:
        target: A plotnine ggplot.
        x: The points' x positions (read by position).
        y: The points' y positions, the same length as ``x``.
        teams: The team for each point.
        league: The SDV league key, e.g. "nfl".
        season: One season for every point.
        height: The wordmark height as a fraction of the panel height, in (0, 1].
        alpha: Opacity, 0 to 1.
        variant: "default", "dark", or a named variant from ``marks()``.
        id_system: The id system of ``teams``.

    Returns:
        ggplot: A new plot with a ``geom_sdv_wordmarks`` layer.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, or the inputs differ in length.

    Example:
        ::

            p2 = sdvplot.add_wordmarks(p, [0.2], [0.48], ["KC"], league="nfl")
    """
    layer = geom_sdv_wordmarks(
        aes("x", "y", team="team", season="season"), data=_frame(x, y, teams, "team", season), inherit_aes=False,
        league=league, height=height, alpha=alpha, variant=variant, id_system=id_system,
    )  # fmt: skip
    return target + layer


def add_headshots(
    target: ggplot,
    x: Any,
    y: Any,
    players: Any,
    *,
    league: str,
    height: float = 0.1,
    alpha: float = 1,
    id_system: str = "espn",
) -> ggplot:
    """A copy of the plot with each player's headshot at its (x, y).

    Args:
        target: A plotnine ggplot.
        x: The points' x positions (read by position).
        y: The points' y positions, the same length as ``x``.
        players: The player id for each point.
        league: The SDV league key, e.g. "nfl".
        height: The headshot height as a fraction of the panel height, in (0, 1].
        alpha: Opacity, 0 to 1.
        id_system: "espn" or "gsis" (NFL).

    Returns:
        ggplot: A new plot with a ``geom_sdv_headshots`` layer.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range, or the inputs differ in length.

    Example:
        ::

            p2 = sdvplot.add_headshots(p, [0.2], [0.48], ["3139477"], league="nfl")
    """
    layer = geom_sdv_headshots(
        aes("x", "y", player_id="player_id"), data=_frame(x, y, players, "player_id"), inherit_aes=False,
        league=league, height=height, alpha=alpha, id_system=id_system,
    )  # fmt: skip
    return target + layer


class _AxisLogos:
    """Added with ``+``: pads the axis text to make room, then (as a plotnine watermark, drawn after the breaks and
    labels) runs the matplotlib axis-logo routine on every panel."""

    def __init__(self, axis: str, **kw: Any) -> None:
        if axis not in ("x", "y"):
            raise ValueError(f"axis must be 'x' or 'y', got {axis!r}")
        check_height(kw["height"])
        _check_mark_type(kw["mark_type"])
        self.axis, self.kw = axis, kw

    def __radd__(self, gg: ggplot) -> ggplot:
        size = gg.theme.getp("figure_size") or (6.4, 4.8)
        points = self.kw["height"] * size[1] * 72 * 0.8  # ~ the panel's share of the figure height
        margin: Any = {"t": points, "unit": "pt"} if self.axis == "x" else {"r": points, "unit": "pt"}
        gg += theme(**{f"axis_text_{self.axis}": element_text(margin=margin)})
        gg.watermarks.append(self)
        return gg

    def draw(self, figure: Figure) -> None:
        # every panel's labels are placed together first, so each skip reason warns once, not once per panel
        kw = self.kw
        labels = list(dict.fromkeys(lab for ax in figure.axes for lab in _in_view(ax, self.axis)[1]))
        zeros = [0.0] * len(labels)
        place(zeros, zeros, labels, league=kw["league"], season=kw["season"], kind=kw["mark_type"],
              variant=kw["variant"], id_system=kw["id_system"])  # fmt: skip
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SdvplotWarning)
            for ax in figure.axes:
                _mpl_axis_logos(ax, self.axis, **kw)


def axis_logos(
    target: ggplot,
    axis: str,
    *,
    league: str,
    season: Any = None,
    height: float = 0.1,
    variant: str = "default",
    mark_type: str = "logo",
    id_system: str = "auto",
) -> ggplot:
    """A copy of the plot whose team axis shows logos (or wordmarks) instead of tick labels.

    Args:
        target: A plotnine ggplot whose ``axis`` is a discrete team axis.
        axis: "x" or "y".
        league: The SDV league key, e.g. "nfl".
        season: One season for every label.
        height: The image height as a fraction of the panel height, in (0, 1].
        variant: "default", "dark", or a named variant from ``marks()``.
        mark_type: "logo" or "wordmark".
        id_system: The id system of the labels.

    Returns:
        ggplot: A new plot; labels that are not teams stay as text, with one SdvplotWarning when drawn.

    Raises:
        ValueError: If ``axis`` is not "x"/"y" or ``height`` is out of range.

    Example:
        ::

            from plotnine import aes, geom_col, ggplot
            p = ggplot(df, aes("team", "epa")) + geom_col()
            p2 = sdvplot.axis_logos(p, "x", league="nfl")
    """
    return target + _AxisLogos(
        axis, league=league, season=season, height=height, variant=variant, mark_type=mark_type, id_system=id_system
    )


def _scale(kind: Any, league: str, which: str, season: Any, na_value: str, kwargs: dict[str, Any]) -> Any:
    _column(which)  # "primary" / "secondary", else ValueError now rather than when the plot is drawn

    class _TeamScale(kind):
        def __init__(self) -> None:
            super().__init__(values={}, na_value=na_value, **kwargs)

        def map(self, x: Any, limits: Any = None) -> Any:
            values = [v for v in (limits if limits is not None else self.final_limits) if v is not None]
            colors = team_colors(values, league, which=which, season=season)
            self._values = {v: c for v, c in zip(values, colors, strict=True) if c is not None}
            self.palette = lambda n: [self._values.get(v, na_value) for v in values]
            return [self._values.get(v, na_value) for v in x]

    return _TeamScale()


def scale_color_sdv(
    league: str, which: str = "primary", season: Any = None, na_value: str = "grey", **kwargs: Any
) -> Any:
    """A discrete color scale that maps each team value (any id system) to its team color.

    Args:
        league: The SDV league key, e.g. "nfl".
        which: "primary" or "secondary".
        season: One season for every value.
        na_value: The color of values that are not teams.
        **kwargs: Passed to plotnine's ``scale_color_manual`` (``name``, ``breaks``, ``guide``, ...).

    Returns:
        scale: A plotnine color scale.

    Example:
        ::

            p = ggplot(df, aes("epa", "sr", color="team")) + geom_point() + scale_color_sdv("nfl")
    """
    return _scale(scale_color_manual, league, which, season, na_value, kwargs)


def scale_fill_sdv(
    league: str, which: str = "primary", season: Any = None, na_value: str = "grey", **kwargs: Any
) -> Any:
    """A discrete fill scale that maps each team value (any id system) to its team color.

    Args:
        league: The SDV league key, e.g. "nfl".
        which: "primary" or "secondary".
        season: One season for every value.
        na_value: The color of values that are not teams.
        **kwargs: Passed to plotnine's ``scale_fill_manual``.

    Returns:
        scale: A plotnine fill scale.

    Example:
        ::

            p = ggplot(df, aes("team", "epa", fill="team")) + geom_col() + scale_fill_sdv("nfl")
    """
    return _scale(scale_fill_manual, league, which, season, na_value, kwargs)


def _drawn(target: ggplot) -> Figure:
    return target.draw()


def drawn_marks(target: ggplot) -> list[tuple[Any, ...]]:
    """Test hook: draw the plot, then (team_id, x, y, height, url) for each mark image on any panel."""
    import matplotlib.pyplot as plt

    fig = _drawn(target)
    try:
        return [m for ax in fig.axes for m in _mpl_drawn_marks(ax)]
    finally:
        plt.close(fig)


def drawn_axis_marks(target: ggplot, axis: str) -> list[tuple[str, float, float]]:
    """Test hook: draw the plot, then (team_id, tick position, measured height) for each axis image on the first
    panel."""
    import matplotlib.pyplot as plt

    fig = _drawn(target)
    try:
        return _mpl_drawn_axis_marks(fig.axes[0], axis)
    finally:
        plt.close(fig)


def visible_axis_labels(target: ggplot, axis: str) -> list[str]:
    """Test hook: draw the plot, then the first panel's tick labels still shown as text."""
    import matplotlib.pyplot as plt

    fig = _drawn(target)
    try:
        return _mpl_visible_axis_labels(fig.axes[0], axis)
    finally:
        plt.close(fig)

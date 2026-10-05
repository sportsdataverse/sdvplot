"""The plotnine adapter: logo, wordmark, headshot and image geoms, axis logos, team color scales and reference lines.

The geoms draw through the matplotlib adapter (sdvplot.matplotlib.draw_placements), so sizing matches it: ``height``
is a fraction of each panel's height. ``add_logos(p, ...)`` returns a new ggplot (plotnine's ``+`` copies).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from plotnine import aes, element_text, ggplot, scale_color_manual, scale_fill_manual, theme
from plotnine._utils import remove_missing
from plotnine.geoms import geom_hline, geom_vline
from plotnine.geoms.geom import geom

from sdvplot._colors import _column, team_colors
from sdvplot._marks import _check_mark_type
from sdvplot._placement import check_alpha, check_height, place, place_images
from sdvplot._resolve import _unpack
from sdvplot.matplotlib import axis_logos as _mpl_axis_logos
from sdvplot.matplotlib import draw_images, draw_placements
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
    """Shared drawing for the image geoms; subclasses set the kind and the id aesthetic."""

    _kind = "logo"
    _id_aes = "team"
    _needs_league = True
    DEFAULT_AES: dict[str, Any] = {}
    REQUIRED_AES = {"x", "y", "team"}
    DEFAULT_PARAMS = _MARK_PARAMS

    def __init__(self, mapping: Any = None, data: Any = None, **kwargs: Any) -> None:
        if self._needs_league and kwargs.get("league") is None:
            raise TypeError(f"{type(self).__name__}() needs league=, e.g. league='nfl'")
        check_height(kwargs.get("height", 0.1))
        check_alpha(kwargs.get("alpha", 1))
        kwargs.setdefault("show_legend", False)
        super().__init__(mapping, data, **kwargs)

    def draw_panel(self, data: pd.DataFrame, panel_params: Any, coord: Any, ax: Any) -> None:
        data = coord.transform(data, panel_params)
        p = self.params
        placements = place(
            data["x"].tolist(), data["y"].tolist(), data[self._id_aes].tolist(), league=p["league"],
            season=p["season"], kind=self._kind, variant=p["variant"], id_system=p["id_system"],
        )  # fmt: skip
        draw_placements(ax, placements, height=float(p["height"]), alpha=float(p["alpha"]))


class geom_sdv_logos(_geom_sdv_marks):
    """Team logos at (x, y): ``aes(x=..., y=..., team=...)``, plus ``league=`` and optional ``season``, ``height``
    (fraction of the panel height), ``alpha``, ``variant`` and ``id_system``.

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


class geom_from_path(_geom_sdv_marks):
    """Any image, by local path or URL, at (x, y): ``aes(x=..., y=..., path=...)``, plus ``height`` (fraction of the
    panel height, default 0.1) and ``alpha``. The port of ggpath's ``geom_from_path()``, sized like the logo geoms.

    Args:
        mapping: ``aes(x=..., y=..., path=...)``; ``path`` holds a local file path or an http(s) URL per row.
        data: The layer's data (pandas or polars), when not the plot's.
        **kwargs: ``height`` in (0, 1], ``alpha`` in [0, 1], and plotnine's layer arguments (``inherit_aes``, ...).

    Returns:
        geom: A plotnine layer to add with ``+``. Images that cannot be read (a missing file, a file that is not an
        image, a failed download) are skipped with one SdvplotWarning when the plot is drawn; SVG is not read.

    Raises:
        ValueError: If ``height`` or ``alpha`` is out of range (when the layer is built).

    Example:
        ::

            import pandas as pd
            from plotnine import aes, ggplot
            from sdvplot.plotnine import geom_from_path

            df = pd.DataFrame({"x": [1, 2], "y": [1, 2], "img": ["a.png", "https://www.python.org/static/favicon.ico"]})
            p = ggplot(df, aes("x", "y", path="img")) + geom_from_path(height=0.15)

    See Also:
        ggpath geom_from_path(): https://mrcaseb.github.io/ggpath/ ;
        sdvplot.matplotlib.add_images: the matplotlib counterpart
    """

    _id_aes = "path"
    _needs_league = False
    REQUIRED_AES = {"x", "y", "path"}
    DEFAULT_PARAMS = {"stat": "identity", "position": "identity", "na_rm": False, "height": 0.1, "alpha": 1}

    def draw_panel(self, data: pd.DataFrame, panel_params: Any, coord: Any, ax: Any) -> None:
        data = coord.transform(data, panel_params)
        placements = place_images(data["x"].tolist(), data["y"].tolist(), data["path"].tolist())
        draw_images(ax, placements, height=float(self.params["height"]), alpha=float(self.params["alpha"]))


class _geom_ref_lines(geom):
    """A vertical line at ``_ref(x0)`` and a horizontal line at ``_ref(y0)`` per panel, drawn by plotnine's own
    geom_vline / geom_hline (ggpath draws through GeomVline / GeomHline the same way)."""

    _ref: Any = staticmethod(np.mean)
    # ggpath's GeomRefLines, except alpha: ggplot2's NA (the color's own alpha) is 1 in plotnine, which also keeps
    # an 8-digit hex color's alpha
    DEFAULT_AES = {"color": "red", "size": 0.5, "linetype": "dashed", "alpha": 1}
    REQUIRED_AES: set[str] = set()
    DEFAULT_PARAMS = {"stat": "identity", "position": "identity", "na_rm": False}

    def __init__(self, mapping: Any = None, data: Any = None, **kwargs: Any) -> None:
        kwargs.setdefault("show_legend", False)
        super().__init__(mapping, data, **kwargs)

    def draw_layer(self, data: pd.DataFrame, layout: Any, coord: Any) -> None:
        # x0/y0 are position aesthetics in ggplot2: each panel's position scale transforms them (a log scale averages
        # the logs) and censors those outside its limits to NA before the mean. plotnine does not know them, so do
        # both here, panel by panel (free scales differ).
        data = data.copy()
        for ae, which in (("x0", "x"), ("y0", "y")):
            if ae not in data:
                continue
            data[ae] = data[ae].astype(float)
            for panel, rows in data.groupby("PANEL", observed=True).groups.items():
                sc = getattr(layout.get_scales(panel), which)
                data.loc[rows, ae] = sc.map(sc.transform(data.loc[rows, ae].to_numpy()))
        super().draw_layer(data, layout, coord)

    def draw_panel(self, data: pd.DataFrame, panel_params: Any, coord: Any, ax: Any) -> None:
        name = type(self).__name__
        if "x0" not in data and "y0" not in data:
            raise ValueError(f"{name}() needs an x0 and/or a y0 aesthetic, e.g. aes(x0='epa', y0='success_rate')")
        # ggplot2's GeomHline/GeomVline draw one segment per distinct row of these (ggpath passes them on): one line per
        # panel, or one per group when a colour (or another line aesthetic) is mapped, all at the panel's value
        styles = data[[c for c in ("PANEL", "group", "color", "size", "linetype", "alpha") if c in data]]
        lines: tuple[tuple[str, Any, str], ...] = (("y0", geom_hline, "yintercept"), ("x0", geom_vline, "xintercept"))
        for ae, line, column in lines:
            if ae not in data:
                continue
            values = data[ae].to_numpy(dtype=float)
            if self.params["na_rm"]:
                values = values[~np.isnan(values)]
            ref = float(self._ref(values)) if len(values) else np.nan  # NaN when a value is missing, as R's mean()
            # ggplot2 drops (and warns about) a line at NA whatever na.rm says; so does plotnine's remove_missing
            frame = styles.assign(**{column: ref}).drop_duplicates().reset_index(drop=True)
            frame = remove_missing(frame, False, [column], name)
            if len(frame):
                line.draw_panel(self, frame, panel_params, coord, ax)


class geom_mean_lines(_geom_ref_lines):
    """Reference lines at the mean of ``x0`` (vertical) and/or ``y0`` (horizontal), per panel: the port of ggpath's
    ``geom_mean_lines()``.

    Args:
        mapping: ``aes(x0=..., y0=...)``, at least one of them (``x0`` alone draws only the vertical line).
        data: The layer's data (pandas or polars), when not the plot's.
        **kwargs: ``color`` (default "red"), ``size`` (line width, default 0.5), ``linetype`` (default "dashed"),
            ``alpha``, ``na_rm`` and plotnine's layer arguments. With ``na_rm=False`` (the default) a panel whose
            values include a missing one draws no line on that axis, with a PlotnineWarning, as ggpath does;
            ``na_rm=True`` ignores the missing values.

    Returns:
        geom: A plotnine layer to add with ``+``; each facet panel gets its own reference value.

    Raises:
        ValueError: When the plot is drawn, if neither ``x0`` nor ``y0`` is mapped.

    Example:
        ::

            from plotnine import aes, geom_point, ggplot
            from sdvplot.plotnine import geom_mean_lines

            p = (ggplot(df, aes("epa", "success_rate", x0="epa", y0="success_rate"))
                 + geom_point() + geom_mean_lines(color="grey"))

    See Also:
        ggpath geom_mean_lines(): https://mrcaseb.github.io/ggpath/ ;
        geom_median_lines: the same at the median
    """


class geom_median_lines(_geom_ref_lines):
    """Reference lines at the median of ``x0`` (vertical) and/or ``y0`` (horizontal), per panel: the port of ggpath's
    ``geom_median_lines()``.

    Args:
        mapping: ``aes(x0=..., y0=...)``, at least one of them.
        data: The layer's data (pandas or polars), when not the plot's.
        **kwargs: ``color`` (default "red"), ``size`` (default 0.5), ``linetype`` (default "dashed"), ``alpha``,
            ``na_rm`` (as ``geom_mean_lines``) and plotnine's layer arguments.

    Returns:
        geom: A plotnine layer to add with ``+``; each facet panel gets its own reference value.

    Raises:
        ValueError: When the plot is drawn, if neither ``x0`` nor ``y0`` is mapped.

    Example:
        ::

            p = ggplot(df, aes("epa", "success_rate", x0="epa", y0="success_rate")) + geom_point() + geom_median_lines()

    See Also:
        ggpath geom_median_lines(): https://mrcaseb.github.io/ggpath/ ;
        geom_mean_lines: the same at the mean
    """

    _ref = staticmethod(np.median)


def _frame(x: Any, y: Any, ids: Any, column: str) -> pd.DataFrame:
    xs, ys, ts = _unpack(x)[0], _unpack(y)[0], _unpack(ids)[0]
    if not len(xs) == len(ys) == len(ts):
        raise ValueError(f"x, y and teams must have the same length, got {len(xs)}, {len(ys)} and {len(ts)}")
    return pd.DataFrame({"x": xs, "y": ys, column: ts})


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
        aes("x", "y", team="team"), data=_frame(x, y, teams, "team"), inherit_aes=False, league=league,
        season=season, height=height, alpha=alpha, variant=variant, id_system=id_system,
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
        aes("x", "y", team="team"), data=_frame(x, y, teams, "team"), inherit_aes=False, league=league,
        season=season, height=height, alpha=alpha, variant=variant, id_system=id_system,
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
        for ax in figure.axes:
            _mpl_axis_logos(ax, self.axis, **self.kw)


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


def drawn_axis_marks(target: ggplot, axis: str) -> list[tuple[str, float]]:
    """Test hook: draw the plot, then (team_id, tick position) for each axis image on the first panel."""
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

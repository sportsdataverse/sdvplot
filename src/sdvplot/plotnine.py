"""The plotnine adapter: logo, wordmark, headshot and image geoms, axis logos, team color scales and reference lines.

The geoms draw through the matplotlib adapter's drawing step, so sizing matches it: ``height``
is a fraction of each panel's height. ``add_logos(p, ...)`` returns a new ggplot (plotnine's ``+`` copies).
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_reverse,
    theme_minimal,
)
from plotnine import theme as p9_theme  # team_tiers takes a `theme` argument
from plotnine._utils import remove_missing
from plotnine.geoms import geom_hline, geom_vline
from plotnine.geoms.geom import geom

from sdvplot import _tiers
from sdvplot._colors import _column, team_colors
from sdvplot._errors import UnsupportedTargetError, warn
from sdvplot._marks import _check_mark_type
from sdvplot._placement import Placement, _warn_skipped, check_alpha, check_height, place, place_images
from sdvplot._resolve import _seasons, _unpack
from sdvplot._types import Which
from sdvplot.matplotlib import (
    _add_title_image,
    _align,
    _check_title_image,
    _draw_images,
    _draw_placements,
    _in_view,
    _read_images,
    _title_source,
)
from sdvplot.matplotlib import _axis_logos as _mpl_axis_logos
from sdvplot.matplotlib import _drawn_axis_marks as _mpl_drawn_axis_marks
from sdvplot.matplotlib import _drawn_marks as _mpl_drawn_marks
from sdvplot.matplotlib import _visible_axis_labels as _mpl_visible_axis_labels

_SUPPORTS_AXIS_LOGOS = True
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

__all__ = [
    "add_logos",
    "add_wordmarks",
    "add_headshots",
    "axis_logos",
    "geom_sdv_logos",
    "geom_sdv_wordmarks",
    "geom_sdv_headshots",
    "geom_from_path",
    "geom_mean_lines",
    "geom_median_lines",
    "scale_color_sdv",
    "scale_fill_sdv",
    "title_image",
    "team_tiers",
]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)


class _geom_sdv_marks(geom):
    """Shared drawing for the image geoms; subclasses set the kind and the id aesthetic."""

    _kind = "logo"
    _id_aes = "team"
    _needs_league = True
    DEFAULT_AES: dict[str, Any] = {"season": None}  # optional: one season per row, which plotnine copies with the row
    REQUIRED_AES = {"x", "y", "team"}
    DEFAULT_PARAMS = _MARK_PARAMS

    def __init__(self, mapping: Any = None, data: Any = None, **kwargs: Any) -> None:
        if self._needs_league and kwargs.get("league") is None:
            raise TypeError(f"{type(self).__name__}() needs league=, e.g. league='nfl'")
        check_height(kwargs.get("height", 0.1))
        check_alpha(kwargs.get("alpha", 1))
        kwargs.setdefault("show_legend", False)
        super().__init__(mapping, data, **kwargs)

    def _place(self, data: pd.DataFrame, x: list[Any], y: list[Any], *, warn: bool) -> list[Placement]:
        p = self.params
        # the season= parameter, else the season aesthetic (a column, so each panel's copy of a row keeps its season)
        season = p["season"] if p["season"] is not None or "season" not in data else data["season"].tolist()
        return place(x, y, data[self._id_aes].tolist(), league=p["league"], season=season, kind=self._kind,
                     variant=p["variant"], id_system=p["id_system"], _warn=warn)  # fmt: skip

    def setup_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Once per layer and render: place every panel's rows together, so an unknown team or a missing mark warns
        once, and a point plotnine copies into every panel counts once. At zero positions: x and y are plotnine's to
        check, after this (``na_rm``, scale limits, its own "Removed rows" warning), so they never warn here."""
        # ponytail: two identical points (same x, y and team) in one panel also count once
        rows = data.drop(columns="PANEL", errors="ignore").drop_duplicates()  # a row plotnine copies to every panel
        zeros = [0.0] * len(rows)
        self._place(rows, zeros, zeros, warn=True)
        return data

    def draw_panel(self, data: pd.DataFrame, panel_params: Any, coord: Any, ax: Any) -> None:
        # setup_data already warned for this layer's rows in every panel, so each panel places its rows quietly
        data = coord.transform(data, panel_params)
        placements = self._place(data, data["x"].tolist(), data["y"].tolist(), warn=False)
        _draw_placements(ax, placements, height=float(self.params["height"]), alpha=float(self.params["alpha"]))


class geom_sdv_logos(_geom_sdv_marks):
    """Team logos at (x, y), as a plotnine layer.

    For a season per row, map it instead of passing ``season=``: ``aes(..., season="season")`` (a ``season=``
    parameter wins over the mapping).

    Args:
        mapping: ``aes(x=..., y=..., team=...)``, plus optional ``season``.
        data: The layer's data (pandas or polars), when not the plot's.
        **kwargs: ``league`` (required, e.g. "nfl"), ``season``, ``height`` (a fraction of the panel height, in (0, 1],
            default 0.1), ``alpha`` (0 to 1), ``variant`` ("default", "dark" or a named variant), ``id_system`` and
            plotnine's layer arguments (``inherit_aes``, ...).

    Returns:
        geom: A plotnine layer to add with ``+``. Marks that cannot be placed (an unknown team, a missing mark) are
        skipped with one SdvplotWarning when the plot is drawn.

    Raises:
        TypeError: If ``league`` is missing.
        ValueError: If ``height`` or ``alpha`` is out of range (when the layer is built).

    Example:
        ::

            import pandas as pd
            from plotnine import aes, ggplot
            from sdvplot.plotnine import geom_sdv_logos

            df = pd.DataFrame({"team": ["KC", "BUF"], "epa": [0.2, 0.15], "sr": [0.48, 0.47]})
            p = ggplot(df, aes("epa", "sr", team="team")) + geom_sdv_logos(league="nfl", height=0.12)

    See Also:
        sdvplotR geom_nfl_logos(): https://sdvplotR.sportsdataverse.org/ ;
        sdvplot.plotnine.geom_sdv_wordmarks: the same with wordmarks
    """


class geom_sdv_wordmarks(_geom_sdv_marks):
    """Team wordmarks at (x, y), as a plotnine layer: the same aesthetics and parameters as ``geom_sdv_logos``.

    Args:
        mapping: ``aes(x=..., y=..., team=...)``, plus optional ``season``.
        data: The layer's data (pandas or polars), when not the plot's.
        **kwargs: ``league`` (required, e.g. "nfl"), ``season``, ``height`` (a fraction of the panel height, in (0, 1],
            default 0.1), ``alpha`` (0 to 1), ``variant`` ("default", "dark" or a named variant), ``id_system`` and
            plotnine's layer arguments (``inherit_aes``, ...).

    Returns:
        geom: A plotnine layer to add with ``+``. Marks that cannot be placed (an unknown team, a missing mark) are
        skipped with one SdvplotWarning when the plot is drawn.

    Raises:
        TypeError: If ``league`` is missing.
        ValueError: If ``height`` or ``alpha`` is out of range (when the layer is built).

    Example:
        ::

            import pandas as pd
            from plotnine import aes, ggplot
            from sdvplot.plotnine import geom_sdv_wordmarks

            df = pd.DataFrame({"team": ["KC", "BUF"], "epa": [0.2, 0.15], "sr": [0.48, 0.47]})
            p = ggplot(df, aes("epa", "sr", team="team")) + geom_sdv_wordmarks(league="nfl", height=0.08)

    See Also:
        sdvplotR geom_nfl_wordmarks(): https://sdvplotR.sportsdataverse.org/ ;
        sdvplot.plotnine.geom_sdv_logos: the same with logos
    """

    _kind = "wordmark"


class geom_sdv_headshots(_geom_sdv_marks):
    """Player headshots at (x, y), as a plotnine layer.

    Args:
        mapping: ``aes(x=..., y=..., player_id=...)``.
        data: The layer's data (pandas or polars), when not the plot's.
        **kwargs: ``league`` (required, e.g. "nfl"), ``height`` (a fraction of the panel height, in (0, 1],
            default 0.1), ``alpha`` (0 to 1), ``id_system`` and
            plotnine's layer arguments (``inherit_aes``, ...).

    Returns:
        geom: A plotnine layer to add with ``+``. Marks that cannot be placed (an unknown team, a missing mark) are
        skipped with one SdvplotWarning when the plot is drawn.

    Raises:
        TypeError: If ``league`` is missing.
        ValueError: If ``height`` or ``alpha`` is out of range (when the layer is built).

    Example:
        ::

            import pandas as pd
            from plotnine import aes, ggplot
            from sdvplot.plotnine import geom_sdv_headshots

            df = pd.DataFrame({"x": [0.3, 0.7], "y": [0.4, 0.6], "espn_id": ["3139477", "3918298"]})
            p = ggplot(df, aes("x", "y", player_id="espn_id")) + geom_sdv_headshots(league="nfl", height=0.15)

    See Also:
        sdvplotR geom_nfl_headshots(): https://sdvplotR.sportsdataverse.org/ ;
        sdvplot.plotnine.geom_sdv_logos: the same with team logos
    """

    _kind = "headshot"
    _id_aes = "player_id"
    REQUIRED_AES = {"x", "y", "player_id"}
    DEFAULT_PARAMS = {**_MARK_PARAMS, "id_system": "espn"}


class geom_from_path(_geom_sdv_marks):
    """Any image, by local path or URL, at (x, y): ``aes(x=..., y=..., path=...)``, plus ``height`` (fraction of the
    panel height, default 0.1) and ``alpha``. The port of ggpath's ``geom_from_path()``, sized like the logo geoms.

    Args:
        mapping: ``aes(x=..., y=..., path=...)``; ``path`` holds a local file path, ``file://`` URI or http(s) URL per
            row.
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
    DEFAULT_AES: dict[str, Any] = {}
    REQUIRED_AES = {"x", "y", "path"}
    DEFAULT_PARAMS = {"stat": "identity", "position": "identity", "na_rm": False, "height": 0.1, "alpha": 1}
    _sdv_images: dict[str, Any]  # path -> image (None when unreadable), read once per render by setup_data

    def _place(self, data: pd.DataFrame, x: list[Any], y: list[Any], *, warn: bool) -> list[Placement]:
        return place_images(x, y, data["path"].tolist(), _warn=warn)

    def setup_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Once per layer and render, as for the team geoms: read every distinct image once, so an image that cannot
        be read (or downloaded) is tried once and warns once, whatever the facets; the panels draw from these."""
        rows = data.drop(columns="PANEL", errors="ignore").drop_duplicates()  # a row plotnine copies to every panel
        zeros = [0.0] * len(rows)
        self._sdv_images = {}
        _warn_skipped("whose image could not be read", _read_images(self._place(rows, zeros, zeros, warn=True),
                                                                   self._sdv_images))  # fmt: skip
        return data

    def draw_panel(self, data: pd.DataFrame, panel_params: Any, coord: Any, ax: Any) -> None:
        # setup_data already read the images and warned, so each panel draws its rows quietly
        data = coord.transform(data, panel_params)
        placements = self._place(data, data["x"].tolist(), data["y"].tolist(), warn=False)
        _draw_images(ax, placements, height=float(self.params["height"]), alpha=float(self.params["alpha"]),
                    cache=self._sdv_images, warn=False)  # fmt: skip


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

            import pandas as pd
            from plotnine import aes, geom_point, ggplot
            from sdvplot.plotnine import geom_mean_lines

            df = pd.DataFrame({"epa": [0.2, 0.15, 0.05], "success_rate": [0.48, 0.47, 0.44]})
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

            import pandas as pd
            from plotnine import aes, geom_point, ggplot
            from sdvplot.plotnine import geom_median_lines

            df = pd.DataFrame({"epa": [0.2, 0.15, 0.05], "success_rate": [0.48, 0.47, 0.44]})
            p = ggplot(df, aes("epa", "success_rate", x0="epa", y0="success_rate")) + geom_point() + geom_median_lines()

    See Also:
        ggpath geom_median_lines(): https://mrcaseb.github.io/ggpath/ ;
        geom_mean_lines: the same at the mean
    """

    _ref = staticmethod(np.median)


def _ggplot(target: Any) -> ggplot:
    if not isinstance(target, ggplot):
        raise UnsupportedTargetError(f"sdvplot.plotnine draws on a plotnine ggplot, got {type(target).__name__}")
    return target


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

            import pandas as pd
            import sdvplot
            from plotnine import aes, geom_point, ggplot

            df = pd.DataFrame({"epa": [0.2, 0.15], "sr": [0.48, 0.47]})
            p = ggplot(df, aes("epa", "sr")) + geom_point()
            p2 = sdvplot.add_logos(p, [0.2], [0.48], ["KC"], league="nfl")

    See Also:
        sdvplotR geom_nfl_logos(): https://sdvplotR.sportsdataverse.org/ ;
        sdvplot.plotnine.geom_sdv_logos: the layer this adds
    """
    layer = geom_sdv_logos(
        aes("x", "y", team="team", season="season"), data=_frame(x, y, teams, "team", season), inherit_aes=False,
        league=league, height=height, alpha=alpha, variant=variant, id_system=id_system,
    )  # fmt: skip
    return _ggplot(target) + layer


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

            import pandas as pd
            import sdvplot
            from plotnine import aes, geom_point, ggplot

            df = pd.DataFrame({"epa": [0.2, 0.15], "sr": [0.48, 0.47]})
            p = ggplot(df, aes("epa", "sr")) + geom_point()
            p2 = sdvplot.add_wordmarks(p, [0.2], [0.48], ["KC"], league="nfl")

    See Also:
        sdvplotR geom_nfl_wordmarks(): https://sdvplotR.sportsdataverse.org/ ;
        sdvplot.plotnine.geom_sdv_wordmarks: the layer this adds
    """
    layer = geom_sdv_wordmarks(
        aes("x", "y", team="team", season="season"), data=_frame(x, y, teams, "team", season), inherit_aes=False,
        league=league, height=height, alpha=alpha, variant=variant, id_system=id_system,
    )  # fmt: skip
    return _ggplot(target) + layer


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

            import pandas as pd
            import sdvplot
            from plotnine import aes, geom_point, ggplot

            df = pd.DataFrame({"epa": [0.2, 0.15], "sr": [0.48, 0.47]})
            p = ggplot(df, aes("epa", "sr")) + geom_point()
            p2 = sdvplot.add_headshots(p, [0.2], [0.48], ["3139477"], league="nfl")

    See Also:
        sdvplotR geom_nfl_headshots(): https://sdvplotR.sportsdataverse.org/ ;
        sdvplot.plotnine.geom_sdv_headshots: the layer this adds
    """
    layer = geom_sdv_headshots(
        aes("x", "y", player_id="player_id"), data=_frame(x, y, players, "player_id"), inherit_aes=False,
        league=league, height=height, alpha=alpha, id_system=id_system,
    )  # fmt: skip
    return _ggplot(target) + layer


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
        gg += p9_theme(**{f"axis_text_{self.axis}": element_text(margin=margin)})
        gg.watermarks.append(self)
        return gg

    def draw(self, figure: Figure) -> None:
        # every panel's labels are placed together first, so each skip reason warns once, not once per panel
        kw = self.kw
        labels = list(dict.fromkeys(lab for ax in figure.axes for lab in _in_view(ax, self.axis)[1]))
        zeros = [0.0] * len(labels)
        place(zeros, zeros, labels, league=kw["league"], season=kw["season"], kind=kw["mark_type"],
              variant=kw["variant"], id_system=kw["id_system"])  # fmt: skip
        for ax in figure.axes:
            _mpl_axis_logos(ax, self.axis, **kw, warn=False)


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

            import pandas as pd
            import sdvplot
            from plotnine import aes, geom_col, ggplot

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "epa": [0.2, 0.15, 0.1]})
            p = ggplot(df, aes("team", "epa")) + geom_col()
            p2 = sdvplot.axis_logos(p, "x", league="nfl")

    See Also:
        sdvplotR element_sdv_logo(): https://sdvplotR.sportsdataverse.org/ ;
        sdvplot.plotnine.title_image: an image beside the plot title
    """
    return _ggplot(target) + _AxisLogos(
        axis, league=league, season=season, height=height, variant=variant, mark_type=mark_type, id_system=id_system
    )


class _TitleImage:
    """Added with ``+``: sets the title, then (as a plotnine watermark, drawn after the figure texts) puts the image
    beside the rendered title, aligned with it as the theme's ``plot_title`` alignment says."""

    def __init__(self, image: Any, title: str, league: str | None, season: Any, side: str, height: float) -> None:
        self.height = _check_title_image(side, height)
        self.side, self.title = side, title or " "  # a blank title still gives the image a line to sit on
        self.source = _title_source(image, league, season)  # resolved (and warned about) when built, not drawn

    def __radd__(self, gg: ggplot) -> ggplot:
        gg += labs(title=self.title)
        gg.watermarks = [w for w in gg.watermarks if not isinstance(w, _TitleImage)] + [self]  # one title image
        return gg

    def draw(self, figure: Figure) -> None:
        if self.source is None:
            return
        text = next((t for t in figure.texts if t.get_text() == self.title), None)
        if text is None:
            warn(f"title_image: the plot's title is no longer {self.title!r}; add title_image() after labs(title=...)")
            return

        def align() -> float:  # plotnine left-aligns the text and places it by the theme's plot_title ha
            theme_ = getattr(figure.get_layout_engine(), "theme", None)
            return _align(theme_.getp(("plot_title", "ha")) if theme_ is not None else "left")

        _add_title_image(figure, text, self.source, self.side, self.height, align)


def title_image(
    image: Any,
    title: str = "",
    *,
    league: str | None = None,
    season: Any = None,
    side: str = "left",
    height: float = 15,
) -> Any:
    """A plot title with an image (a team logo, or any image) beside it, added to a ggplot with ``+``.

    The pair follows the theme's ``plot_title`` alignment, like the image inside sdvplotR's title: plotnine centres a
    lone title and left-aligns one with a subtitle.

    Args:
        image: A team, in any id system ``resolve()`` understands, when ``league`` is given; otherwise an image URL
            (http or https) or a local file path.
        title: The title text; it replaces ``labs(title=...)``, so add ``title_image`` after any ``labs``.
        league: The SDV league key, e.g. "nfl"; None reads ``image`` as a URL or path.
        season: One season, to pick the team's logo for that era.
        side: "left" or "right" of the title text.
        height: The image height in points (1/72 inch). The title keeps its own line height, so an image much taller
            than the text needs room: a ``plot_title`` margin in ``theme()``.

    Returns:
        object: An object to add to a ggplot; the image is loaded now, and an unknown team, or an image by URL or path
        that cannot be read, gives one SdvplotWarning now (the title is drawn without the image). A second
        ``title_image`` added to the same plot replaces the first.

    Raises:
        ValueError: If ``side`` is not "left"/"right" or ``height`` is not a positive number.
        OfflineError: If a team's logo cannot be downloaded and is not cached (as in ``add_logos``).

    Example:
        ::

            import pandas as pd
            from plotnine import aes, geom_point, ggplot
            from sdvplot.plotnine import title_image

            df = pd.DataFrame({"epa": [0.2, 0.15], "sr": [0.48, 0.47]})
            p = ggplot(df, aes("epa", "sr")) + geom_point() + title_image("KC", "Chiefs", league="nfl", height=20)

    See Also:
        sdvplotR ggtitle_image(): https://sdvplotR.sportsdataverse.org/reference/ggtitle_image.html ;
        sdvplot.matplotlib.title_image: the same for matplotlib.
    """
    return _TitleImage(image, title, league, season, side, height)


def team_tiers(
    data: Any,
    league: str,
    *,
    title: str | None = None,
    subtitle: str | None = _tiers.SUBTITLE,
    caption: str | None = None,
    tier_desc: dict[Any, str] | None = None,
    presort: bool = False,
    alpha: float = 0.8,
    height: float | None = None,
    no_line_below_tier: Any = None,
    devel: bool = False,
    theme: Literal["dark", "light"] = "dark",
) -> ggplot:
    """A tier list as a ggplot: each team's logo in its tier's row, tier 1 on top, on a dark (sdvplotR) or light theme.

    Args:
        data: A pandas or polars DataFrame with ``tier_no`` (1 is the top tier) and ``team`` (any id system
            ``resolve()`` understands), and optionally ``tier_rank``, the position within the tier; without it, teams
            keep their order in ``data``.
        league: The SDV league key, e.g. "nfl".
        title: The title; None gives "{LEAGUE} Team Tiers", "" none.
        subtitle: The subtitle; None or "" for none.
        caption: The caption; None for none.
        tier_desc: Each tier's label, keyed by tier number; None gives sdvplotR's (1 "Elite" ... 5 "What are they
            doing?"). Labels wrap at 15 characters; a tier without one gets none.
        presort: Sort teams alphabetically within each tier (ignores ``tier_rank``).
        alpha: Logo opacity, 0 to 1.
        height: Logo height as a fraction of the panel height; None gives 0.1, about the largest height at
            which 32 logos in 5 tiers (7, 7, 6, 6, 6) neither overlap nor leave the panel at the default 6.4 x 4.8 in
            figure.
        no_line_below_tier: A tier number, or several, with no separator line below.
        devel: Draw each team as text instead of its logo (fast, and needs no download).
        theme: "dark" (sdvplotR's: a near-black background) or "light" (white, for dark logos such as Ohio State's,
            Texas A&M's or Penn State's, which vanish on dark).

    Returns:
        ggplot: The plot; a team that does not resolve is skipped with one SdvplotWarning, keeping its slot.

    Raises:
        TypeError: If ``data`` is not a DataFrame, or ``tier_no``/``tier_rank`` hold non-numbers.
        ValueError: If ``data`` lacks ``tier_no`` or ``team``, has no row with a tier, ``height``/``alpha`` is
            out of range, or ``theme`` is not "dark" or "light".

    Example:
        ::

            import pandas as pd
            from sdvplot.plotnine import team_tiers

            df = pd.DataFrame({"tier_no": [1, 1, 2, 3], "team": ["KC", "BUF", "BAL", "NYJ"]})
            p = team_tiers(df, "nfl", caption="data: nflverse")

            # Draft it as text first:
            p = team_tiers(df, "nfl", devel=True)

            # Dark logos on a white background:
            p = team_tiers(df, "cfb", theme="light")

    See Also:
        sdvplotR sdv_team_tiers(): https://sdvplotR.sportsdataverse.org/reference/sdv_team_tiers.html ;
        sdvplot.matplotlib.team_tiers: the same as a matplotlib Figure.
    """
    t = _tiers.prepare(
        data, league, title=title, subtitle=subtitle, caption=caption, tier_desc=tier_desc, presort=presort,
        alpha=alpha, height=height, no_line_below_tier=no_line_below_tier, theme=theme,
    )  # fmt: skip
    frame = pd.DataFrame({"x": t.x, "y": t.y, "team": t.team_ids, "label": t.labels})
    if devel:
        marks: Any = geom_text(aes(label="label"), color=t.text)
    else:
        marks = geom_sdv_logos(aes(team="team"), league=league, id_system="team_id", height=t.height, alpha=t.alpha)
    texts = {"title": t.title, "subtitle": t.subtitle, "caption": t.caption}
    return (
        ggplot(frame, aes("x", "y"))
        + geom_hline(yintercept=t.lines, color=t.line_color)
        + marks
        + scale_x_continuous(limits=t.xlim, expand=(0, 0))
        + scale_y_reverse(limits=t.ylim, breaks=t.breaks, labels=t.break_labels, expand=(0, 0))
        + labs(**{k: v for k, v in texts.items() if v})
        + theme_minimal(base_size=11.5)
        + p9_theme(
            plot_title=element_text(color=t.text, weight="bold"),
            plot_subtitle=element_text(color=t.muted),
            plot_caption=element_text(color=t.muted, ha="right"),
            plot_title_position="plot",
            axis_text_x=element_blank(),
            axis_text_y=element_text(color=t.text, weight="bold", size=11.5 * 0.8 * 1.1),  # sdvplotR: rel(1.1)
            axis_title=element_blank(),
            panel_grid=element_blank(),
            plot_background=element_rect(fill=t.bg, color=t.bg),
            panel_background=element_rect(fill=t.bg, color=t.bg),
        )
    )


def _scale(kind: Any, league: str, which: Which, season: Any, na_value: str, kwargs: dict[str, Any]) -> Any:
    _column(which)  # "primary" / "secondary", else ValueError now rather than when the plot is drawn

    class _TeamScale(kind):
        def __init__(self) -> None:
            super().__init__(values={}, na_value=na_value, **kwargs)

        def map(self, x: Any, limits: Any = None) -> Any:
            values = [v for v in (limits if limits is not None else self.final_limits) if v is not None]
            colors = team_colors(league, values, which=which, season=season)
            self._values = {v: c for v, c in zip(values, colors, strict=True) if c is not None}
            self.palette = lambda n: [self._values.get(v, na_value) for v in values]
            return [self._values.get(v, na_value) for v in x]

    return _TeamScale()


def scale_color_sdv(
    league: str, which: Which = "primary", season: Any = None, na_value: str = "grey", **kwargs: Any
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

    Raises:
        ValueError: If ``which`` is not "primary" or "secondary".

    Example:
        ::

            import pandas as pd
            from plotnine import aes, geom_point, ggplot
            from sdvplot.plotnine import scale_color_sdv

            df = pd.DataFrame({"team": ["KC", "BUF"], "epa": [0.2, 0.15], "sr": [0.48, 0.47]})
            p = ggplot(df, aes("epa", "sr", color="team")) + geom_point() + scale_color_sdv("nfl")

    See Also:
        sdvplotR scale_color_sdv(): https://sdvplotR.sportsdataverse.org/ ;
        sdvplot.plotnine.scale_fill_sdv: the fill scale
    """
    return _scale(scale_color_manual, league, which, season, na_value, kwargs)


def scale_fill_sdv(
    league: str, which: Which = "primary", season: Any = None, na_value: str = "grey", **kwargs: Any
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

    Raises:
        ValueError: If ``which`` is not "primary" or "secondary".

    Example:
        ::

            import pandas as pd
            from plotnine import aes, geom_col, ggplot
            from sdvplot.plotnine import scale_fill_sdv

            df = pd.DataFrame({"team": ["KC", "BUF"], "epa": [0.2, 0.15]})
            p = ggplot(df, aes("team", "epa", fill="team")) + geom_col() + scale_fill_sdv("nfl")

    See Also:
        sdvplotR scale_fill_sdv(): https://sdvplotR.sportsdataverse.org/ ;
        sdvplot.plotnine.scale_color_sdv: the color scale
    """
    return _scale(scale_fill_manual, league, which, season, na_value, kwargs)


def _drawn(target: ggplot) -> Figure:
    return target.draw()


def _drawn_marks(target: ggplot) -> list[tuple[Any, ...]]:
    """Test hook: draw the plot, then (team_id, x, y, height, url) for each mark image on any panel."""
    import matplotlib.pyplot as plt

    fig = _drawn(target)
    try:
        return [m for ax in fig.axes for m in _mpl_drawn_marks(ax)]
    finally:
        plt.close(fig)


def _drawn_axis_marks(target: ggplot, axis: str) -> list[tuple[str, float, float]]:
    """Test hook: draw the plot, then (team_id, tick position, measured height) for each axis image on the first
    panel."""
    import matplotlib.pyplot as plt

    fig = _drawn(target)
    try:
        return _mpl_drawn_axis_marks(fig.axes[0], axis)
    finally:
        plt.close(fig)


def _visible_axis_labels(target: ggplot, axis: str) -> list[str]:
    """Test hook: draw the plot, then the first panel's tick labels still shown as text."""
    import matplotlib.pyplot as plt

    fig = _drawn(target)
    try:
        return _mpl_visible_axis_labels(fig.axes[0], axis)
    finally:
        plt.close(fig)

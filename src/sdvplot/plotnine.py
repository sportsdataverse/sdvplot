"""The plotnine adapter: logo, wordmark and headshot geoms, axis logos, and team color scales.

The geoms draw through the matplotlib adapter (sdvplot.matplotlib.draw_placements), so sizing matches it: ``height``
is a fraction of each panel's height. ``add_logos(p, ...)`` returns a new ggplot (plotnine's ``+`` copies).
"""

from __future__ import annotations

import warnings
from typing import Any

import pandas as pd
from matplotlib.figure import Figure
from plotnine import (
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_hline,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_reverse,
    theme,
    theme_minimal,
)
from plotnine.geoms.geom import geom

from sdvplot import _tiers
from sdvplot._colors import _column, team_colors
from sdvplot._errors import SdvplotWarning
from sdvplot._marks import _check_mark_type
from sdvplot._placement import check_alpha, check_height, place
from sdvplot._resolve import _unpack
from sdvplot.matplotlib import _align, add_title_image, check_title_image, draw_placements, title_source
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
    DEFAULT_AES: dict[str, Any] = {}
    REQUIRED_AES = {"x", "y", "team"}
    DEFAULT_PARAMS = _MARK_PARAMS

    def __init__(self, mapping: Any = None, data: Any = None, **kwargs: Any) -> None:
        if kwargs.get("league") is None:
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


class _TitleImage:
    """Added with ``+``: sets the title, then (as a plotnine watermark, drawn after the figure texts) puts the image
    beside the rendered title, aligned with it as the theme's ``plot_title`` alignment says."""

    def __init__(self, image: Any, title: str, league: str | None, season: Any, side: str, height: float) -> None:
        self.height = check_title_image(side, height)
        self.side, self.title = side, title or " "  # a blank title still gives the image a line to sit on
        self.source = title_source(image, league, season)  # resolved (and warned about) when built, not drawn

    def __radd__(self, gg: ggplot) -> ggplot:
        gg += labs(title=self.title)
        gg.watermarks = [w for w in gg.watermarks if not isinstance(w, _TitleImage)] + [self]  # one title image
        return gg

    def draw(self, figure: Figure) -> None:
        if self.source is None:
            return
        text = next((t for t in figure.texts if t.get_text() == self.title), None)
        if text is None:
            warnings.warn(
                f"title_image: the plot's title is no longer {self.title!r}; add title_image() after labs(title=...)",
                SdvplotWarning,
                stacklevel=2,
            )
            return

        def align() -> float:  # plotnine left-aligns the text and places it by the theme's plot_title ha
            theme_ = getattr(figure.get_layout_engine(), "theme", None)
            return _align(theme_.getp(("plot_title", "ha")) if theme_ is not None else "left")

        add_title_image(figure, text, self.source, self.side, self.height, align)


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

            from plotnine import aes, geom_point, ggplot
            from sdvplot.plotnine import title_image

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
) -> ggplot:
    """A tier list as a ggplot: each team's logo in its tier's row, tier 1 on top, on sdvplotR's dark theme.

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
        height: Logo height as a fraction of the panel height; None gives 0.1, the largest two-decimal height at
            which 32 logos in 5 tiers (7, 7, 6, 6, 6) neither overlap nor leave the panel at the default 6.4 x 4.8 in
            figure.
        no_line_below_tier: A tier number, or several, with no separator line below.
        devel: Draw each team as text instead of its logo (fast, and needs no download).

    Returns:
        ggplot: The plot; a team that does not resolve is skipped with one SdvplotWarning, keeping its slot.

    Raises:
        TypeError: If ``data`` is not a DataFrame, or ``tier_no``/``tier_rank`` hold non-numbers.
        ValueError: If ``data`` lacks ``tier_no`` or ``team``, has no row with a tier, or ``height``/``alpha`` is
            out of range.

    Example:
        ::

            import pandas as pd
            from sdvplot.plotnine import team_tiers

            df = pd.DataFrame({"tier_no": [1, 1, 2, 3], "team": ["KC", "BUF", "BAL", "NYJ"]})
            p = team_tiers(df, "nfl", caption="data: nflverse")

        Draft it as text first::

            p = team_tiers(df, "nfl", devel=True)

    See Also:
        sdvplotR sdv_team_tiers(): https://sdvplotR.sportsdataverse.org/reference/sdv_team_tiers.html ;
        sdvplot.matplotlib.team_tiers: the same as a matplotlib Figure.
    """
    t = _tiers.prepare(
        data, league, title=title, subtitle=subtitle, caption=caption, tier_desc=tier_desc, presort=presort,
        alpha=alpha, height=height, no_line_below_tier=no_line_below_tier,
    )  # fmt: skip
    frame = pd.DataFrame({"x": t.x, "y": t.y, "team": t.team_ids, "label": t.labels})
    if devel:
        marks: Any = geom_text(aes(label="label"), color="white")
    else:
        marks = geom_sdv_logos(aes(team="team"), league=league, id_system="team_id", height=t.height, alpha=t.alpha)
    texts = {"title": t.title, "subtitle": t.subtitle, "caption": t.caption}
    return (
        ggplot(frame, aes("x", "y"))
        + geom_hline(yintercept=t.lines, color=_tiers.LINES)
        + marks
        + scale_x_continuous(limits=t.xlim, expand=(0, 0))
        + scale_y_reverse(limits=t.ylim, breaks=t.breaks, labels=t.break_labels, expand=(0, 0))
        + labs(**{k: v for k, v in texts.items() if v})
        + theme_minimal(base_size=11.5)
        + theme(
            plot_title=element_text(color="white", weight="bold"),
            plot_subtitle=element_text(color=_tiers.MUTED),
            plot_caption=element_text(color=_tiers.MUTED, ha="right"),
            plot_title_position="plot",
            axis_text_x=element_blank(),
            axis_text_y=element_text(color="white", weight="bold", size=11.5 * 0.8 * 1.1),  # sdvplotR: rel(1.1)
            axis_title=element_blank(),
            panel_grid=element_blank(),
            plot_background=element_rect(fill=_tiers.BG, color=_tiers.BG),
            panel_background=element_rect(fill=_tiers.BG, color=_tiers.BG),
        )
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

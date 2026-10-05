"""sportypy playing surfaces in team colors: the port of sdvplotR's sdv_surface()."""

from __future__ import annotations

import contextlib
import importlib
from collections.abc import Iterator
from typing import Any

from sdvplot._colors import team_colors
from sdvplot._contrast import contrast, on_color
from sdvplot._errors import InputError, OptionalDependencyError

# SDV league -> (sportypy.surfaces module, class). Always the sport module: the top-level sportypy.surfaces.NCAACourt
# is the tennis court and NCAAField the football field, shadowing the basketball court and the baseball field.
SURFACES: dict[str, tuple[str, str]] = {
    "nfl": ("football", "NFLField"),
    "aaf": ("football", "NFLField"),
    "ufl": ("football", "NFLField"),
    "usfl": ("football", "NFLField"),
    "xfl": ("football", "NFLField"),
    "cfb": ("football", "NCAAField"),
    "nba": ("basketball", "NBACourt"),
    "nbagl": ("basketball", "NBAGLeagueCourt"),
    "wnba": ("basketball", "WNBACourt"),
    "mbb": ("basketball", "NCAACourt"),
    "wbb": ("basketball", "NCAACourt"),
    "mlb": ("baseball", "MLBField"),
    "milb": ("baseball", "MiLBField"),
    "ncaa_baseball": ("baseball", "NCAAField"),
    "nhl": ("hockey", "NHLRink"),
    "whl": ("hockey", "NHLRink"),
    "pwhl": ("hockey", "NHLRink"),
    "ahl": ("hockey", "AHLRink"),
    "echl": ("hockey", "ECHLRink"),
    "ohl": ("hockey", "OHLRink"),
    "qmjhl": ("hockey", "QMJHLRink"),
    "ushl": ("hockey", "USHLRink"),
    "phf": ("hockey", "PHFRink"),
    "ncaa_mhockey": ("hockey", "NCAARink"),
    "ncaa_whockey": ("hockey", "NCAARink"),
    "soccer": ("soccer", "FIFAPitch"),
}
SURFACE_BASE = {"basketball": "#d2ab6f", "football": "#196f0c", "hockey": "#ffffff"}  # sportyR's default colors
_DRAW_KWARGS = ("display_range", "xlim", "ylim", "rotation")
_NUMBER_FONT = "Clarendon-Regular"  # sportypy's football yard-line number font (data/surface_dimensions.json)


def _has_font(family: str) -> bool:
    """Whether matplotlib can find ``family`` itself; asking with no fallback logs nothing."""
    from matplotlib import font_manager

    try:
        font_manager.findfont(font_manager.FontProperties(family=family), fallback_to_default=False)
    except ValueError:
        return False
    return True


@contextlib.contextmanager
def _polygon_limits(ax: Any) -> Iterator[None]:
    """Within the block, ``ax.add_patch`` takes a polygon's data limits from its vertices in one call.

    matplotlib walks every segment of an added patch as a Bezier curve to find its extrema, and sportypy draws its
    circles and arcs as 10,000-point polygons: a rink or court walked ~1.3 M segments, 16-19 s. A straight segment's
    extrema are its two ends, so a polygon's vertices are exactly the points matplotlib's walk measures (the CLOSEPOLY
    slot is not a point; one vertex alone is no segment). Anything else (a curve, a NaN, a transform not in data on
    both axes, a non-rectilinear Axes) goes through matplotlib's own walk.
    """
    import numpy as np
    from matplotlib.patches import Polygon
    from matplotlib.path import Path

    straight = (Path.LINETO, Path.CLOSEPOLY)

    walk = ax._update_patch_limits  # the Axes' own updater, or one set on it before this block
    own = vars(ax).get("_update_patch_limits")

    def update(patch: Any) -> None:
        path, transform = patch.get_path(), patch.get_transform()
        codes, vertices = path.codes, path.vertices
        if not (
            isinstance(patch, Polygon)
            and len(vertices) > 1
            and (codes is None or (codes[0] == Path.MOVETO and np.isin(codes[1:], straight).all()))
            and np.isfinite(vertices).all()
            and ax.name == "rectilinear"
            and transform.contains_branch(ax.transData)
        ):
            walk(patch)
            return
        points = vertices if codes is None else vertices[codes != Path.CLOSEPOLY]
        ax.update_datalim((transform - ax.transData).transform(points))

    ax._update_patch_limits = update
    try:
        yield
    finally:
        if own is None:
            del ax._update_patch_limits
        else:
            ax._update_patch_limits = own


def color_updates(sport: str, primary: str, secondary: str | None) -> dict[str, str]:
    """sportypy ``color_updates`` for a team (sdvplotR's ``surface_color_updates()``): basketball paints the lane and
    apron with a readable ink on top, football the end zones, hockey the center line, faceoff circle and spot and the
    boards (the secondary color when the primary does not read on ice); baseball and soccer nothing."""
    if sport == "basketball":
        ink = on_color(primary)
        return {
            "painted_area": primary,
            "court_apron": primary,
            "restricted_arc": ink,
            "free_throw_circle_dash": ink,
            "lane_lower_defensive_box": ink,
            "baseline_lower_defensive_box": ink,
        }
    if sport == "football":
        return {"offensive_endzone": primary, "defensive_endzone": primary}
    if sport == "hockey":
        ice = SURFACE_BASE["hockey"]
        readable = secondary is not None and contrast(primary, ice) < 3 and contrast(secondary, ice) >= 3
        accent = secondary if readable and secondary is not None else primary
        return {
            "center_line": accent,
            "center_faceoff_circle": accent,
            "center_faceoff_spot": accent,
            "boards": primary,
        }
    return {}


def surface(
    league: str,
    team: Any = None,
    *,
    season: Any = None,
    ax: Any = None,
    center_logo: bool | float = False,
    **sportypy_kwargs: Any,
) -> Any:
    """Draw the league's playing surface with sportypy, in a team's colors.

    Args:
        league: The SDV league key, e.g. "nfl", "nba", "nhl", "cfb", "soccer".
        team: A team to color the surface by (end zones, lane and apron, center line and boards); None for the plain
            surface.
        season: The season, for teams whose colors changed.
        ax: The matplotlib Axes to draw on; None makes a new figure.
        center_logo: True to draw the team's logo at center ice / court / field (0.25 of the Axes height), or a
            height fraction.
        **sportypy_kwargs: Passed to sportypy: ``display_range``, ``xlim``, ``ylim`` and ``rotation`` go to
            ``draw()``; the rest (``field_updates``, ``color_updates``, ``units``, ...) to the surface class.

    Returns:
        matplotlib.axes.Axes: The Axes sportypy drew on.

    Raises:
        InputError: (a ValueError) If sportypy has no surface for ``league``; and, when ``team`` is given, if
            ``season`` is not a year or is outside the seasons sdvplot knows for the league, or ``center_logo`` is a
            height outside (0, 1]. Without ``team``, ``season`` and ``center_logo`` are not used.
        OptionalDependencyError: If the surfaces extra (sportypy) is not installed, or ``team`` and ``center_logo`` are
            set and the team's logo is an SVG without the ``svg`` extra.
        OfflineError: If ``team`` and ``center_logo`` are set and the logo manifest or the team's logo is neither
            cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an
            IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode).
        UnsafeDownloadError: (an OSError) If ``team`` and ``center_logo`` are set and a download is refused: larger
            than the byte cap, past the deadline, or redirected away from https.
        UnsafeCachePathError: (a ValueError) If ``team`` and ``center_logo`` are set and the manifest's sha256 or
            extension for the logo would put the file outside the cache directory.

    Example:
        ::

            import sdvplot

            ax = sdvplot.surface("nfl", "KC", center_logo=True)

    See Also:
        sdvplotR sdv_surface(): https://sdvplotR.sportsdataverse.org/ ;
        sportypy: https://sportypy.sportsdataverse.org/
    """
    if league not in SURFACES:
        raise InputError(f"no sportypy surface for league {league!r}; supported: {sorted(SURFACES)}")
    sport, cls_name = SURFACES[league]
    try:
        module = importlib.import_module(f"sportypy.surfaces.{sport}")
    except ModuleNotFoundError as e:
        raise OptionalDependencyError(
            "sdvplot.surface() needs the surfaces extra: pip install sdvplot[surfaces]"
        ) from e
    draw_kwargs = {k: sportypy_kwargs.pop(k) for k in _DRAW_KWARGS if k in sportypy_kwargs}
    if sport == "football" and not _has_font(_NUMBER_FONT):
        # sportypy numbers football fields in Clarendon-Regular, which it does not ship: matplotlib then logs "findfont:
        # Font family 'Clarendon-Regular' not found" for every number it measures and draws its default font anyway.
        # Naming that default draws the same numbers (bar sportypy's Clarendon-only nudge of one "1") and logs nothing.
        sportypy_kwargs["field_updates"] = {"number_font": "DejaVu Sans", **sportypy_kwargs.get("field_updates", {})}
    if team is not None:
        primary, secondary = (team_colors(league, [team], which=w, season=season)[0] for w in ("primary", "secondary"))
        if primary is not None:
            sportypy_kwargs["color_updates"] = {
                **color_updates(sport, primary, secondary),
                **sportypy_kwargs.get("color_updates", {}),
            }
    drawing = getattr(module, cls_name)(**sportypy_kwargs)
    if ax is None:  # as sportypy's draw() does, so the limits shortcut has an Axes to go on
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        fig.patch.set_facecolor(drawing.feature_colors["plot_background"])
    with _polygon_limits(ax):
        drawn = drawing.draw(ax=ax, **draw_kwargs)
    if center_logo and team is not None:
        from sdvplot.matplotlib import add_logos

        top = max((a.get_zorder() for a in drawn.get_children()), default=0)
        add_logos(drawn, [0.0], [0.0], [team], league=league, season=season, zorder=top + 1,
                  height=0.25 if center_logo is True else float(center_logo))  # fmt: skip
    return drawn

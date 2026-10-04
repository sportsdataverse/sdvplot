"""sportypy playing surfaces in team colors: the port of sdvplotR's sdv_surface()."""

from __future__ import annotations

import importlib
from typing import Any

from sdvplot._colors import team_colors
from sdvplot._contrast import contrast, on_color
from sdvplot._errors import OptionalDependencyError

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
        ValueError: If sportypy has no surface for ``league``.
        OptionalDependencyError: If the surfaces extra (sportypy) is not installed.

    Example:
        ::

            import sdvplot

            ax = sdvplot.surface("nfl", "KC", center_logo=True)

    See Also:
        sdvplotR sdv_surface(): https://sdvplotR.sportsdataverse.org/ ;
        sportypy: https://sportypy.sportsdataverse.org/
    """
    if league not in SURFACES:
        raise ValueError(f"no sportypy surface for league {league!r}; supported: {sorted(SURFACES)}")
    sport, cls_name = SURFACES[league]
    try:
        module = importlib.import_module(f"sportypy.surfaces.{sport}")
    except ModuleNotFoundError as e:
        raise OptionalDependencyError(
            "sdvplot.surface() needs the surfaces extra: pip install sdvplot[surfaces]"
        ) from e
    draw_kwargs = {k: sportypy_kwargs.pop(k) for k in _DRAW_KWARGS if k in sportypy_kwargs}
    if team is not None:
        primary, secondary = (team_colors([team], league, which=w, season=season)[0] for w in ("primary", "secondary"))
        if primary is not None:
            sportypy_kwargs["color_updates"] = {
                **color_updates(sport, primary, secondary),
                **sportypy_kwargs.get("color_updates", {}),
            }
    drawn = getattr(module, cls_name)(**sportypy_kwargs).draw(ax=ax, **draw_kwargs)
    if center_logo and team is not None:
        from sdvplot.matplotlib import add_logos

        top = max((a.get_zorder() for a in drawn.get_children()), default=0)
        add_logos(drawn, [0.0], [0.0], [team], league=league, season=season, zorder=top + 1,
                  height=0.25 if center_logo is True else float(center_logo))  # fmt: skip
    return drawn

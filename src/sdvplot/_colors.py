"""Team colors as plain {team: "#hex"} dicts, which seaborn, Plotly, Altair, Bokeh and PyPalettes all accept."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any, overload

from sdvplot import _index
from sdvplot._errors import InputError, warn
from sdvplot._resolve import _seasons, _unpack, resolve
from sdvplot._types import IdSystem, Which

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd
    import polars as pl
else:
    from sdvplot._lazy import pl

_COLUMNS = {"primary": "color_primary", "secondary": "color_secondary"}


def _column(which: str) -> str:
    if which not in _COLUMNS:
        raise InputError(f"which must be one of {sorted(_COLUMNS)}, got {which!r}")
    return _COLUMNS[which]


def _colors(league: str, column: str) -> dict[str, str]:
    t = _index.team_table().filter(pl.col("league") == league)
    return {tid: c for tid, c in t.select("team_id", column).iter_rows() if c}


def palette(
    league: str,
    teams: Any = None,
    *,
    which: Which = "primary",
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
) -> dict[Any, str]:
    """A ``{team: "#hex"}`` dict for a league, ready for seaborn, Plotly, Altair, Bokeh or PyPalettes.

    Without ``teams`` the keys are canonical abbreviations, or the team_id where a team has no abbreviation or shares
    it with another team of the league (never guessing which team an abbreviation means). With ``teams`` the keys are
    the caller's own values, so they match a seaborn ``hue`` column or a Plotly color column exactly.

    Args:
        league: The SDV league key, e.g. "nfl".
        teams: Team values to key the dict by; None returns the whole league.
        which: "primary" or "secondary".
        season: One season, or one per team, for values reused across eras.
        id_system: The id system of ``teams``, as in ``resolve``: "auto" tries each in order; NHL stats ids need
            "nhl_id".
        strict: Raise UnresolvedTeamError instead of warning when a team does not resolve.

    Returns:
        dict: ``{team: "#hex"}``. Teams that do not resolve, or have no color, are left out. Without ``teams``, a team
        whose abbreviation another team of the league shares is keyed by its team_id, with one SdvplotWarning naming
        the shared abbreviations.

    Raises:
        TypeError: If ``teams`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
        InputError: (a ValueError) If ``league`` is not a known league key, ``which`` is not "primary"/"secondary",
            ``teams`` holds "primary" or "secondary" (the slot goes in ``which=``), ``id_system`` is unknown, or
            ``season`` is not a year, is outside the seasons sdvplot knows for the league, or is a list whose length
            does not match the teams.
        UnresolvedTeamError: (a ValueError) If ``strict=True`` and a team does not resolve.

    Example:
        ::

            import sdvplot

            sdvplot.palette("nfl", teams=["KC", "SF"])   # {'KC': '#e31837', 'SF': '#aa0000'}

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    column = _column(which)
    _index.check_league(league)
    colors = _colors(league, column)
    if teams is None:
        rows = _index.team_table().filter(pl.col("league") == league).select("team_id", "abbr").rows()
        shared = {a for a, n in Counter(a for _, a in rows if a).items() if n > 1}
        if shared:
            warn(f"abbreviations shared by several {league} teams are keyed by team_id: {', '.join(sorted(shared))}")
        return {(tid if not abbr or abbr in shared else abbr): colors[tid] for tid, abbr in rows if tid in colors}
    values, _ = _unpack(teams)
    if slots := [v for v in values if isinstance(v, str) and v in _COLUMNS]:  # pre-0.1: palette(league, which)
        raise InputError(
            f"{slots[0]!r} is a color slot, not a team; pass it by keyword: "
            f'palette(league, teams=..., which="{slots[0]}")'
        )
    pairs = [p for p in dict.fromkeys(zip(values, _seasons(season, len(values)), strict=True)) if p[0] is not None]
    ids = resolve([v for v, _ in pairs], league, season=[s for _, s in pairs], id_system=id_system, strict=strict)
    out: dict[Any, str] = {}
    for (v, _), i in zip(pairs, ids, strict=True):
        if i is not None and i in colors:
            out.setdefault(v, colors[i])  # a value two teams wore across the seasons keeps its first team's color
    return out


# resolve()'s container rule, and so its overloads (the last one's ignore included).
@overload
def team_colors(
    league: str,
    teams: str | bytes | int | float | None,
    *,
    which: Which = "primary",
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
) -> str | None: ...
@overload
def team_colors(
    league: str,
    teams: pl.Series,
    *,
    which: Which = "primary",
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
) -> pl.Series: ...
@overload
def team_colors(
    league: str,
    teams: list[Any] | tuple[Any, ...] | np.ndarray[Any, Any],
    *,
    which: Which = "primary",
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
) -> list[str | None]: ...
@overload
def team_colors(
    league: str,
    teams: pd.Series,
    *,
    which: Which = "primary",
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
) -> pd.Series: ...
@overload
def team_colors(  # type: ignore[overload-cannot-match]
    league: str,
    teams: Any,
    *,
    which: Which = "primary",
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
) -> Any: ...
def team_colors(
    league: str,
    teams: Any,
    *,
    which: Which = "primary",
    season: Any = None,
    id_system: IdSystem = "auto",
    strict: bool = False,
) -> Any:
    """One "#hex" (or None) per team value, in the same container the values came in.

    Args:
        league: The SDV league key, e.g. "nfl".
        teams: A scalar, list/tuple, numpy array, or pandas/polars Series of team identifiers.
        which: "primary" or "secondary".
        season: One season, or one per team, for values reused across eras.
        id_system: The id system of ``teams``, as in ``resolve``: "auto" tries each in order; NHL stats ids need
            "nhl_id".
        strict: Raise UnresolvedTeamError instead of warning when a team does not resolve.

    Returns:
        str | list | Series | None: The hex color for each team, None where a team does not resolve or has no color.

    Raises:
        TypeError: If ``teams`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
        InputError: (a ValueError) If ``league`` is not a known league key (a list or Series there is the pre-0.1
            ``team_colors(teams, league)`` order), ``which`` is not "primary"/"secondary", ``id_system`` is unknown,
            or ``season`` is not a year, is outside the seasons sdvplot knows for the league, or is a list whose
            length does not match the teams.
        UnresolvedTeamError: (a ValueError) If ``strict=True`` and a team does not resolve.

    Example:
        ::

            import sdvplot

            sdvplot.team_colors("nfl", ["KC", "SF"])              # ['#e31837', '#aa0000']
            sdvplot.team_colors("nfl", "KC", which="secondary")   # '#ffb612'
            sdvplot.team_colors("nhl", [1, 6, 10], id_system="nhl_id")   # NHL stats ids: Devils, Bruins, Leafs

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    column = _column(which)
    _index.check_league(league)
    colors = _colors(league, column)
    values, wrap = _unpack(teams)
    ids = resolve(values, league, season=season, id_system=id_system, strict=strict)
    return wrap([colors.get(i) if i is not None else None for i in ids])

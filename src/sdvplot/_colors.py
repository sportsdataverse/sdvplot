"""Team colors as plain {team: "#hex"} dicts, which seaborn, Plotly, Altair, Bokeh and PyPalettes all accept."""

from __future__ import annotations

import warnings
from collections import Counter
from typing import Any

import polars as pl

from sdvplot import _index
from sdvplot._errors import SdvplotWarning
from sdvplot._resolve import _seasons, _unpack, resolve

_COLUMNS = {"primary": "color_primary", "secondary": "color_secondary"}


def _column(which: str) -> str:
    if which not in _COLUMNS:
        raise ValueError(f"which must be one of {sorted(_COLUMNS)}, got {which!r}")
    return _COLUMNS[which]


def _colors(league: str, column: str) -> dict[str, str]:
    t = _index.team_table().filter(pl.col("league") == league)
    return {tid: c for tid, c in t.select("team_id", column).iter_rows() if c}


def palette(league: str, which: str = "primary", teams: Any = None, season: Any = None) -> dict[Any, str]:
    """A ``{team: "#hex"}`` dict for a league, ready for seaborn, Plotly, Altair, Bokeh or PyPalettes.

    Without ``teams`` the keys are canonical abbreviations, or the team_id where a team has no abbreviation or shares
    it with another team of the league (never guessing which team an abbreviation means). With ``teams`` the keys are
    the caller's own values, so they match a seaborn ``hue`` column or a Plotly color column exactly.

    Args:
        league: The SDV league key, e.g. "nfl".
        which: "primary" or "secondary".
        teams: Team values to key the dict by; None returns the whole league.
        season: One season, or one per team, for values reused across eras.

    Returns:
        dict: ``{team: "#hex"}``. Teams that do not resolve, or have no color, are left out. Without ``teams``, a team
        whose abbreviation another team of the league shares is keyed by its team_id, with one SdvplotWarning naming
        the shared abbreviations.

    Raises:
        TypeError: If ``teams`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
        ValueError: If ``league`` is unknown, ``which`` is not "primary"/"secondary", or
            ``season`` is not a year (or a list whose length does not match the teams).

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
            warnings.warn(
                f"abbreviations shared by several {league} teams are keyed by team_id: {', '.join(sorted(shared))}",
                SdvplotWarning,
                stacklevel=2,
            )
        return {(tid if not abbr or abbr in shared else abbr): colors[tid] for tid, abbr in rows if tid in colors}
    values, _ = _unpack(teams)
    pairs = [p for p in dict.fromkeys(zip(values, _seasons(season, len(values)), strict=True)) if p[0] is not None]
    ids = resolve([v for v, _ in pairs], league, season=[s for _, s in pairs])
    out: dict[Any, str] = {}
    for (v, _), i in zip(pairs, ids, strict=True):
        if i is not None and i in colors:
            out.setdefault(v, colors[i])  # a value two teams wore across the seasons keeps its first team's color
    return out


def team_colors(teams: Any, league: str, which: str = "primary", season: Any = None) -> Any:
    """One "#hex" (or None) per team value, in the same container the values came in.

    Args:
        teams: A scalar, list/tuple, numpy array, or pandas/polars Series of team identifiers.
        league: The SDV league key, e.g. "nfl".
        which: "primary" or "secondary".
        season: One season, or one per team, for values reused across eras.

    Returns:
        str | list | Series | None: The hex color for each team, None where a team does not resolve or has no color.

    Raises:
        TypeError: If ``teams`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
        ValueError: If ``league`` is unknown, ``which`` is not "primary"/"secondary", or
            ``season`` is not a year (or a list whose length does not match the teams).

    Example:
        ::

            import sdvplot

            sdvplot.team_colors(["KC", "SF"], "nfl")      # ['#e31837', '#aa0000']
            sdvplot.team_colors("KC", "nfl", "secondary")  # '#ffb612'

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    column = _column(which)
    _index.check_league(league)
    colors = _colors(league, column)
    values, wrap = _unpack(teams)
    ids = resolve(values, league, season=season)
    return wrap([colors.get(i) if i is not None else None for i in ids])

"""Team colors as plain {team: "#hex"} dicts, which seaborn, Plotly, Altair, Bokeh and PyPalettes all accept."""

from __future__ import annotations

from typing import Any

import polars as pl

from sdvplot import _index
from sdvplot._resolve import _unpack, resolve

_COLUMNS = {"primary": "color_primary", "secondary": "color_secondary"}


def _column(which: str) -> str:
    if which not in _COLUMNS:
        raise ValueError(f"which must be one of {sorted(_COLUMNS)}, got {which!r}")
    return _COLUMNS[which]


def _colors(league: str, column: str) -> dict[str, str]:
    t = _index.team_table().filter(pl.col("league") == league)
    return {tid: c for tid, c in t.select("team_id", column).iter_rows() if c}


def palette(league: str, which: str = "primary", teams: Any = None, season: Any = None) -> dict[Any, str]:
    """{team: "#hex"} for a league. Without teams, keys are canonical abbreviations; with teams, keys are the
    caller's own values (so they match a seaborn hue column or a Plotly color column exactly)."""
    column = _column(which)
    colors = _colors(league, column)
    if teams is None:
        t = _index.team_table().filter(pl.col("league") == league)
        return {abbr or tid: colors[tid] for tid, abbr in t.select("team_id", "abbr").iter_rows() if tid in colors}
    values, _ = _unpack(teams)
    distinct = [v for v in dict.fromkeys(values) if v is not None]
    ids = resolve(distinct, league, season=season)
    return {v: colors[i] for v, i in zip(distinct, ids, strict=True) if i is not None and i in colors}


def team_colors(teams: Any, league: str, which: str = "primary", season: Any = None) -> Any:
    """One "#hex" (or None) per team value, in the same container the values came in."""
    column = _column(which)
    colors = _colors(league, column)
    values, wrap = _unpack(teams)
    ids = resolve(values, league, season=season)
    return wrap([colors.get(i) if i is not None else None for i in ids])

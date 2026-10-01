"""Turn whatever team identifiers a user has into canonical (league, team_id) keys, never guessing."""

from __future__ import annotations

import functools
import numbers
import warnings
from collections.abc import Callable, Sequence
from typing import Any

import polars as pl

from sdvplot import _index
from sdvplot._errors import SdvplotWarning, UnresolvedTeamError
from sdvplot._normalize import _is_na, norm_season, norm_value

# The order "auto" tries id systems in; the first system with a candidate decides
PRIORITY: tuple[str, ...] = (
    "team_id",
    "espn",
    "espn_abbr",
    "nhl",
    "nflverse",
    "mlbstats",
    "nba_api",
    "hockeytech",
    "ncaa",
    "pff",
    "cricinfo",
    "cfbd",
    "bref",
    "sportsipy",
    "fangraphs",
    "sdvplotr",  # sdvplotR's clean_team_abbrs keys: after every id system, so it only fills gaps (R43)
    "name",
)
_AMBIGUOUS = object()
Candidates = list[tuple[str, int | None, int | None]]


@functools.cache
def _lookup(league: str) -> dict[str, dict[str, Candidates]]:
    """id_system -> normalized value -> [(team_id, valid_from, valid_to)] for one league."""
    out: dict[str, dict[str, Candidates]] = {}
    for r in _index.alias_table().filter(pl.col("league") == league).iter_rows(named=True):
        key = norm_value(r["value"])
        if key is not None:
            out.setdefault(r["id_system"], {}).setdefault(key, []).append(
                (r["team_id"], r["valid_from"], r["valid_to"])
            )
    return out


_index.on_reload(_lookup.cache_clear)


def _covers(lo: int | None, hi: int | None, season: int) -> bool:
    return (lo is None or season >= lo) and (hi is None or season <= hi)


def _match(key: str, season: int | None, systems: Sequence[str], table: dict[str, dict[str, Candidates]]) -> Any:
    """The team_id for one key, None if unknown, _AMBIGUOUS if the deciding system names several teams.

    With a season, a first pass only considers aliases whose range covers it, so a reused code such as "LA" goes
    to the team that used it that season; a second pass ignores ranges, so a unique code still resolves when the
    season is outside its range (a modern abbreviation used on old data)."""
    for in_season in (True, False) if season is not None else (False,):
        for system in systems:
            cands = table.get(system, {}).get(key)
            if not cands:
                continue
            if in_season:
                assert season is not None
                cands = [c for c in cands if _covers(c[1], c[2], season)]
                if not cands:
                    continue
            ids = {c[0] for c in cands}
            return next(iter(ids)) if len(ids) == 1 else _AMBIGUOUS
    return None


def _scalar(values: Any) -> tuple[bool, Any]:
    """(True, the value) for one value, 0-d numpy arrays included (np.array("KC") is "KC"); else (False, values)."""
    if getattr(values, "ndim", None) == 0 and hasattr(values, "item"):
        values = values.item()
    # numbers.Number covers numpy scalars such as np.int64
    one = values is None or isinstance(values, (str, bytes, numbers.Number)) or type(values).__name__ == "NAType"
    return one, values


def one_team(team: Any, fn: str) -> Any:
    """team as a scalar, or a TypeError naming fn: the mark functions answer for one team at a time."""
    one, value = _scalar(team)
    if not one:
        raise TypeError(f"{fn}() takes one team, got {type(team).__name__}; use resolve() for several")
    return value


def _unpack(values: Any) -> tuple[list[Any], Callable[[list[Any]], Any]]:
    """values as a list, plus a function that wraps a same-length result back into the caller's container."""
    one, values = _scalar(values)
    if one:
        return [values], lambda out: out[0]
    if isinstance(values, (list, tuple)):
        return list(values), list
    if hasattr(values, "tolist") and not hasattr(values, "to_list"):  # numpy arrays
        return list(values.tolist()), list
    return _unpack_series(values)


def _unpack_series(values: Any) -> tuple[list[Any], Callable[[list[Any]], Any]]:
    """A pandas/polars (or any narwhals-supported) Series in; a same-library String Series of results out."""
    import narwhals as nw

    try:
        s = nw.from_native(values, series_only=True)
    except TypeError as e:
        raise TypeError(
            f"resolve() takes a scalar, list, tuple, numpy array or a pandas/polars Series, got {type(values).__name__}"
        ) from e
    backend = nw.get_native_namespace(s)
    # Capture the original index for pandas-like Series
    original_input = values
    idx = nw.maybe_get_index(s)

    def wrap_result(out: list[Any]) -> Any:
        result = nw.new_series(s.name, out, nw.String(), backend=backend).to_native()
        # Restore the index for pandas-like objects
        if idx is not None and hasattr(result, "index"):
            result.index = original_input.index
        return result

    return s.to_list(), wrap_result


def _seasons(season: Any, n: int) -> list[int | None]:
    one, season = _scalar(season)
    if one or _is_na(season):
        return [norm_season(season)] * n
    items, _ = _unpack(season)
    if len(items) != n:
        raise ValueError(f"season has {len(items)} values but there are {n} teams")
    return [norm_season(s) for s in items]


def _report(unresolved: dict[str, str], league: str, strict: bool) -> None:
    shown = ", ".join(f"{v!r} ({why})" for v, why in unresolved.items())
    msg = f"{len(unresolved)} value(s) did not resolve to a {league} team: {shown}"
    if strict:
        raise UnresolvedTeamError(msg)
    warnings.warn(
        msg + ". Use sdvplot.suggest() for candidates, or strict=True to raise.", SdvplotWarning, stacklevel=3
    )


def resolve(values: Any, league: str, season: Any = None, id_system: str = "auto", strict: bool = False) -> Any:
    """Canonical team_id(s) for team values in one league.

    Args:
        values: a scalar, list/tuple, numpy array, or pandas/polars Series of team identifiers in any supported
            id system (ESPN ids/abbreviations, nflverse, MLB Stats, nba_api, HockeyTech, CFBD names, sdvplotR's
            keys, ...). NHL stats API ids overlap ESPN's, so "auto" reads a bare number as the ESPN id: pass
            id_system="nhl" for them (tri-codes such as "NJD" resolve either way).
        league: the SDV league key, e.g. "nfl", "cfb", "ohl". Required: the same abbreviation means different
            teams in different leagues.
        season: one season for all values, or one per value. Picks the right team for a reused code.
        id_system: "auto" (try PRIORITY in order) or one system name.
        strict: raise UnresolvedTeamError instead of warning when a value does not resolve.

    Returns:
        The same shape as values: a str or None, a list, or a Series of the caller's library.
    """
    _index.check_league(league)
    if id_system != "auto" and id_system not in PRIORITY:
        raise ValueError(f"unknown id_system {id_system!r}; use 'auto' or one of {list(PRIORITY)}")
    systems = PRIORITY if id_system == "auto" else (id_system,)
    items, wrap = _unpack(values)
    seasons = _seasons(season, len(items))
    table = _lookup(league)
    out: list[str | None] = []
    unresolved: dict[str, str] = {}
    memo: dict[tuple[str, int | None], Any] = {}
    for value, s in zip(items, seasons, strict=True):
        key = norm_value(value)
        if key is None:
            out.append(None)
            continue
        if (key, s) not in memo:
            memo[(key, s)] = _match(key, s, systems, table)
        hit = memo[(key, s)]
        if hit is None or hit is _AMBIGUOUS:
            unresolved[str(value)] = "ambiguous" if hit is _AMBIGUOUS else "unknown"
            out.append(None)
        else:
            out.append(hit)
    if unresolved:
        _report(unresolved, league, strict)
    return wrap(out)


def suggest(value: Any, league: str, n: int = 5) -> list[tuple[str, str]]:
    """Up to n (team_id, name) candidates for a value that did not resolve, best first. It never picks one:
    similar names can be different teams ("Bethany (KS)" and "Bethany (WV)")."""
    import difflib

    _index.check_league(league)
    key = norm_value(value)
    if key is None:
        return []
    merged: dict[str, list[str]] = {}
    for system in _lookup(league).values():
        for k, cands in system.items():
            merged.setdefault(k, []).extend(c[0] for c in cands)
    names = dict(_index.teams(league).select("team_id", "name").iter_rows())
    out: list[tuple[str, str]] = []
    for k in difflib.get_close_matches(key, list(merged), n=n * 3, cutoff=0.6):
        for tid in merged[k]:
            if tid not in {t for t, _ in out}:
                out.append((tid, names.get(tid, tid)))
    return out[:n]

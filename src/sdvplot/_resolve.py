"""Turn whatever team identifiers a user has into canonical (league, team_id) keys, never guessing."""

from __future__ import annotations

import functools
import numbers
import warnings
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

from sdvplot import _index
from sdvplot._errors import SdvplotWarning, UnresolvedTeamError
from sdvplot._normalize import _is_na, norm_season, norm_value

if TYPE_CHECKING:
    import polars as pl
else:
    from sdvplot._lazy import pl

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
# Systems "auto" never tries, only an explicit id_system: NHL stats API ids 1-28 are other teams' ESPN ids (R49)
EXPLICIT_ONLY: tuple[str, ...] = ("nhl_id",)
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


@functools.cache
def _latest(league: str) -> int | None:
    """The latest season any of the league's id-system aliases names (a range's end, else its start); None if none
    is dated. A value given without a season is read in this season first: the code's current holder."""
    a = _index.alias_table().filter((pl.col("league") == league) & (pl.col("id_system") != "mark"))
    latest = a.select(pl.max_horizontal(pl.col("valid_from").max(), pl.col("valid_to").max())).item()
    return None if latest is None else int(latest)


_index.on_reload(_latest.cache_clear)


def _covers(lo: int | None, hi: int | None, season: int) -> bool:
    return (lo is None or season >= lo) and (hi is None or season <= hi)


def _match(
    key: str,
    season: int | None,
    systems: Sequence[str],
    table: dict[str, dict[str, Candidates]],
    latest: int | None = None,
) -> Any:
    """The team_id for one key, None if unknown, _AMBIGUOUS if the deciding system names several teams.

    With a season, a first pass only considers aliases whose range covers it, so a reused code such as "LA" goes
    to the team that used it that season. Then, or first without a season, a pass reads the ``latest`` season, so a
    code two franchises used (KCA: the 1955-67 Kansas City Athletics, the Royals since) means its current holder.
    A last pass ignores ranges, so a unique code still resolves when no range covers the season (a modern
    abbreviation used on old data)."""
    for when in [*(s for s in dict.fromkeys((season, latest)) if s is not None), None]:
        for system in systems:
            cands = table.get(system, {}).get(key)
            if not cands:
                continue
            if when is not None:
                cands = [c for c in cands if _covers(c[1], c[2], when)]
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
        kind = getattr(values.dtype, "kind", "")
        if kind in ("m", "M"):
            import numpy as np  # importable: values is a numpy array

            if np.datetime_data(values.dtype)[0] in ("ns", "ps", "fs", "as"):
                # tolist() turns sub-microsecond datetime64/timedelta64 (pandas' default) into integers
                values = values.astype(f"{kind}8[us]")
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


def resolve(values: Any, league: str, *, season: Any = None, id_system: str = "auto", strict: bool = False) -> Any:
    """Canonical team_id(s) for team values in one league.

    Accepts ids and names from any supported source (ESPN, nflverse, MLB Stats, nba_api, HockeyTech, CFBD, sdvplotR) and
    returns the bundled index's canonical team_id, in the same container the values came in. Values that do not resolve
    come back as None with one SdvplotWarning, or raise with ``strict=True``.

    Args:
        values: A scalar, list/tuple, numpy array, or pandas/polars Series of team identifiers in any supported id
            system. NHL stats API ids overlap ESPN's, so "auto" never reads a number as one: pass
            ``id_system="nhl_id"`` for them (NHL tri-codes such as "NJD" resolve under "auto").
        league: The SDV league key, e.g. "nfl", "cfb", "ohl". Required: the same abbreviation means different teams in
            different leagues.
        season: One season for all values, or one per value. Picks the right team for a reused code; without one,
            a reused code means its current holder (KCA: the Royals, not the 1955-67 Kansas City Athletics).
        id_system: "auto" (try the priority order) or one system name.
        strict: Raise UnresolvedTeamError instead of warning when a value does not resolve.

    Returns:
        str | list | Series | None: The same shape as ``values``: a team_id string (or None), a list, or a Series of the
        caller's library.

    Raises:
        TypeError: If ``values`` is not a scalar, list, tuple, numpy array, or pandas/polars Series.
        ValueError: If ``league`` or ``id_system`` is unknown, or
            ``season`` is not a year (or a list whose length does not match the teams).
        UnresolvedTeamError: If ``strict=True`` and a value does not resolve.

    Example:
        ::

            import sdvplot

            sdvplot.resolve("LV", "nfl")                  # '13'
            sdvplot.resolve(["KC", "SF"], "nfl")          # ['12', '25']

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    _index.check_league(league)
    _systems(id_system)
    items, wrap = _unpack(values)
    out, unresolved = _resolve_ids(items, league, _seasons(season, len(items)), id_system)
    if unresolved:
        _report(unresolved, league, strict)
    return wrap(out)


def _systems(id_system: str) -> tuple[str, ...]:
    if id_system != "auto" and id_system not in PRIORITY + EXPLICIT_ONLY:
        raise ValueError(f"unknown id_system {id_system!r}; use 'auto' or one of {list(PRIORITY + EXPLICIT_ONLY)}")
    return PRIORITY if id_system == "auto" else (id_system,)


def _resolve_ids(
    items: list[Any], league: str, seasons: list[int | None], id_system: str
) -> tuple[list[str | None], dict[str, str]]:
    """resolve() without the report: the ids (None where a value does not resolve), and each unresolved value with
    why ("unknown" or "ambiguous"). The caller decides whether to warn."""
    _index.check_league(league)
    systems = _systems(id_system)
    table, latest = _lookup(league), _latest(league)
    out: list[str | None] = []
    unresolved: dict[str, str] = {}
    memo: dict[tuple[str, int | None], Any] = {}
    for value, s in zip(items, seasons, strict=True):
        key = norm_value(value)
        if key is None:
            out.append(None)
            continue
        if (key, s) not in memo:
            memo[(key, s)] = _match(key, s, systems, table, latest)
        hit = memo[(key, s)]
        if hit is None or hit is _AMBIGUOUS:
            unresolved[str(value)] = "ambiguous" if hit is _AMBIGUOUS else "unknown"
            out.append(None)
        else:
            out.append(hit)
    return out, unresolved


def suggest(value: Any, league: str, *, n: int = 5) -> list[tuple[str, str]]:
    """Up to n (team_id, name) candidates for a value that did not resolve, best first.

    It never picks one for you: similar names can be different teams ("Bethany (KS)" and "Bethany (WV)").

    Args:
        value: The team value that failed to resolve.
        league: The SDV league key, e.g. "nfl".
        n: The most candidates to return.

    Returns:
        list[tuple[str, str]]: ``(team_id, name)`` pairs, best match first; empty when nothing is close.

    Raises:
        ValueError: If ``league`` is unknown.

    Example:
        ::

            import sdvplot

            sdvplot.suggest("Kansas Cty Chiefs", "nfl", n=2)   # [('12', 'Kansas City Chiefs')]

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
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

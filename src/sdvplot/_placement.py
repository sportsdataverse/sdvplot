"""From the caller's (x, y, teams) to the marks an adapter draws: one validation and resolution step for every adapter.

Every adapter calls check_height, check_alpha and place, then only draws. That keeps the shared contract (resolution,
warn and skip, pandas/polars parity, height) in one place instead of one copy per library.
"""

from __future__ import annotations

import math
import numbers
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from sdvplot._errors import InputError, warn
from sdvplot._headshots import headshot_url
from sdvplot._marks import select_mark
from sdvplot._normalize import norm_value
from sdvplot._resolve import _resolve_ids, _seasons, _unpack, resolve_marks

if TYPE_CHECKING:
    from sdvplot._types import HeadshotIdSystem, IdSystem

KINDS = ("logo", "wordmark", "headshot")


@dataclass(frozen=True)
class Placement:
    """One mark to draw: whose it is, where, and which image."""

    team_id: str  # canonical team id; the player id for headshots; the path for place_images
    x: Any  # the caller's x value (number, category or datetime), read positionally
    y: Any
    url: str  # archive_url of the selected mark, or the headshot URL
    aspect: float | None  # width / height from the manifest row; None for headshots
    mark: dict[str, Any] | None  # the selected manifest row; None for headshots


def _real(value: Any) -> bool:
    return isinstance(value, numbers.Real) and not isinstance(value, bool) and not math.isnan(value)


def check_height(height: Any) -> float:
    """``height`` as a float, or ValueError unless it is a fraction of the plot height in (0, 1]."""
    if not _real(height) or not 0 < height <= 1:
        raise InputError(f"height is a fraction of the plot height in (0, 1], got {height!r}")
    return float(height)


def check_kind(kind: Any) -> str:
    """``kind`` (an axis verb's ``mark_type``), or InputError unless it is one of KINDS."""
    if kind not in KINDS:
        raise InputError(f"kind must be one of {list(KINDS)}, got {kind!r}")
    return str(kind)


def check_alpha(alpha: Any) -> float:
    """``alpha`` as a float, or ValueError unless it is an opacity in [0, 1]."""
    if not _real(alpha) or not 0 <= alpha <= 1:
        raise InputError(f"alpha is an opacity in [0, 1], got {alpha!r}")
    return float(alpha)


def _missing(value: Any) -> bool:
    if value is None or type(value).__name__ in ("NAType", "NaTType"):
        return True
    return isinstance(value, float) and math.isnan(value)


def _warn_skipped(reason: str, values: list[Any]) -> None:
    if values:
        shown = ", ".join(repr(v) for v in values[:10]) + (f" and {len(values) - 10} more" if len(values) > 10 else "")
        warn(f"skipped {len(values)} point(s) {reason}: {shown}")


def place(
    x: Any,
    y: Any,
    teams: Any,
    *,
    league: str,
    season: Any = None,
    kind: str = "logo",
    variant: str = "default",
    id_system: str = "auto",
    strict: bool = False,
    _warn: bool = True,
) -> list[Placement]:
    """The marks to draw for each (x, y, team), in input order, skipping (with one warning per reason) the points
    whose team is unknown, whose x or y is missing, or that have no mark.

    ``x``, ``y`` and ``teams`` are read positionally (a pandas index is ignored). For ``kind="headshot"``, ``teams``
    holds player ids, ``season`` is ignored and ``id_system`` must be ``"espn"``, ``"gsis"`` or ``"league"`` (as in
    ``headshot_url``; ``"auto"`` means ``"espn"``); otherwise ``strict=True`` raises UnresolvedTeamError for a team that
    does not resolve, as ``resolve`` does. ``_warn=False`` skips the same points without warning, for an adapter that
    already warned for them (no process-wide warning filter is touched, so it is thread-safe).
    """
    skipped = _warn_skipped if _warn else lambda reason, values: None
    check_kind(kind)
    if kind == "headshot" and id_system == "auto":
        id_system = "espn"  # the axis verbs' default; a headshot id is an ESPN athlete id unless told otherwise
    xs, _ = _unpack(x)
    ys, _ = _unpack(y)
    ts, _ = _unpack(teams)
    if not len(xs) == len(ys) == len(ts):
        raise ValueError(f"x, y and teams must have the same length, got {len(xs)}, {len(ys)} and {len(ts)}")
    out: list[Placement] = []
    missing_xy: list[Any] = []
    if kind == "headshot":
        no_image: list[Any] = []
        for xi, yi, pid in zip(xs, ys, ts, strict=True):
            if _missing(pid):
                continue
            if _missing(xi) or _missing(yi):
                missing_xy.append(pid)
                continue
            # id_system is a team or a headshot id system by kind; the callee validates it
            url = headshot_url(pid, league, id_system=cast("HeadshotIdSystem", id_system))
            if url is None:
                no_image.append(pid)
                continue
            # the id the URL was built from: headshot_url reads an espn or league id through norm_value, so an id that
            # went through a float ("3139477.0") is 3139477; gsis ids (nfl "gsis" or "league") are looked up as given
            key = norm_value(pid) if id_system == "espn" or (id_system == "league" and league != "nfl") else None
            out.append(Placement(key or str(pid).strip(), xi, yi, url, None, None))
        skipped("with no headshot", no_image)
    else:
        seasons = _seasons(season, len(ts))
        if _warn or strict:  # one warning for unknown values, or the strict error
            ids = resolve_marks(ts, league, season=seasons, id_system=cast("IdSystem", id_system), strict=strict)
        else:
            ids, _ = _resolve_ids(ts, league, seasons, id_system, marks=True)
        rows: dict[tuple[str, int | None], dict[str, Any] | None] = {}
        no_mark: list[Any] = []
        for xi, yi, raw, team_id, s in zip(xs, ys, ts, ids, seasons, strict=True):
            if team_id is None:
                continue  # unknown or null: the resolver already warned
            if _missing(xi) or _missing(yi):
                missing_xy.append(raw)
                continue
            if (team_id, s) not in rows:
                rows[(team_id, s)] = select_mark(team_id, league, s, variant, kind)
            row = rows[(team_id, s)]
            if row is None:
                no_mark.append(raw)
                continue
            w, h = row.get("width"), row.get("height")
            aspect = float(w) / float(h) if w and h else None
            out.append(Placement(team_id, xi, yi, str(row["archive_url"]), aspect, row))
        skipped(f"with no {kind} archived", no_mark)
    skipped("with a missing x or y", missing_xy)
    return out


def place_images(x: Any, y: Any, paths: Any, *, _warn: bool = True) -> list[Placement]:
    """``place`` for arbitrary images: one Placement per (x, y, path), keyed by the path (a local file or URL).

    A null path is skipped silently (as a null team is); a missing x or y is skipped with one warning (none with
    ``_warn=False``, as ``place``).
    """
    paths = os.fspath(paths) if isinstance(paths, os.PathLike) else paths  # one pathlib.Path is one point
    xs, ys, ps = _unpack(x)[0], _unpack(y)[0], _unpack(paths)[0]
    if not len(xs) == len(ys) == len(ps):
        raise ValueError(f"x, y and paths must have the same length, got {len(xs)}, {len(ys)} and {len(ps)}")
    out: list[Placement] = []
    missing_xy: list[Any] = []
    for xi, yi, path in zip(xs, ys, ps, strict=True):
        if _missing(path):
            continue
        if _missing(xi) or _missing(yi):
            missing_xy.append(path)
            continue
        out.append(Placement(str(path), xi, yi, str(path), None, None))
    if _warn:
        _warn_skipped("with a missing x or y", missing_xy)
    return out

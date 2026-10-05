"""From the caller's (x, y, teams) to the marks an adapter draws: one validation and resolution step for every adapter.

Every adapter calls check_height, check_alpha and place, then only draws. That keeps the shared contract (resolution,
warn and skip, pandas/polars parity, height) in one place instead of one copy per library.
"""

from __future__ import annotations

import math
import numbers
import warnings
from dataclasses import dataclass
from typing import Any

from sdvplot._errors import SdvplotWarning
from sdvplot._headshots import headshot_url
from sdvplot._marks import select_mark
from sdvplot._normalize import norm_value
from sdvplot._resolve import _seasons, _unpack, resolve

KINDS = ("logo", "wordmark", "headshot")


@dataclass(frozen=True)
class Placement:
    """One mark to draw: whose it is, where, and which image."""

    team_id: str  # canonical team id; the player id for headshots
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
        raise ValueError(f"height is a fraction of the plot height in (0, 1], got {height!r}")
    return float(height)


def check_alpha(alpha: Any) -> float:
    """``alpha`` as a float, or ValueError unless it is an opacity in [0, 1]."""
    if not _real(alpha) or not 0 <= alpha <= 1:
        raise ValueError(f"alpha is an opacity in [0, 1], got {alpha!r}")
    return float(alpha)


def _missing(value: Any) -> bool:
    if value is None or type(value).__name__ in ("NAType", "NaTType"):
        return True
    return isinstance(value, float) and math.isnan(value)


def _warn_skipped(reason: str, values: list[Any]) -> None:
    if values:
        shown = ", ".join(repr(v) for v in values[:10]) + (f" and {len(values) - 10} more" if len(values) > 10 else "")
        warnings.warn(f"skipped {len(values)} point(s) {reason}: {shown}", SdvplotWarning, stacklevel=3)


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
) -> list[Placement]:
    """The marks to draw for each (x, y, team), in input order, skipping (with one warning per reason) the points
    whose team is unknown, whose x or y is missing, or that have no mark.

    ``x``, ``y`` and ``teams`` are read positionally (a pandas index is ignored). For ``kind="headshot"``, ``teams``
    holds player ids and ``id_system`` must be ``"espn"`` or ``"gsis"`` (as in ``headshot_url``).
    """
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}, got {kind!r}")
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
            url = headshot_url(pid, league, id_system=id_system)
            if url is None:
                no_image.append(pid)
                continue
            # the id the URL was built from: headshot_url reads an espn id through norm_value, so an id that went
            # through a float ("3139477.0") is 3139477; gsis ids are looked up as given
            key = norm_value(pid) if id_system == "espn" else None
            out.append(Placement(key or str(pid).strip(), xi, yi, url, None, None))
        _warn_skipped("with no headshot", no_image)
    else:
        seasons = _seasons(season, len(ts))
        ids = resolve(ts, league, season=seasons, id_system=id_system)  # one warning for unknown values
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
        _warn_skipped(f"with no {kind} archived", no_mark)
    _warn_skipped("with a missing x or y", missing_xy)
    return out

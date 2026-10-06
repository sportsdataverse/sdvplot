"""Soccer event coordinates from any provider's frame to the pitch surface("soccer") draws: the port of sdvplotR's
sdv_pitch_coords()."""

from __future__ import annotations

import csv
from functools import lru_cache
from importlib import resources

import numpy as np
from numpy.typing import NDArray

Floats = NDArray[np.float64]

FIXED = ("opta", "wyscout", "statsbomb", "uefa", "impect")
PHYSICAL = ("tracab", "skillcorner", "secondspectrum", "metrica")
ALIASES = {"statsperform": "opta"}
PROVIDERS = (*FIXED, "espn", *PHYSICAL, *ALIASES)


@lru_cache(maxsize=1)
def _table() -> dict[tuple[str, str], tuple[float, ...]]:
    """The shared landmark table (byte-identical to sdvplotR's inst/extdata/pitch_landmarks.csv): x from the defended
    goal line to the attacked one, y from the attacker's right touchline to the left one."""
    text = resources.files("sdvplot").joinpath("data", "pitch_landmarks.csv").read_text(encoding="utf-8")
    rows: dict[tuple[str, str], list[tuple[int, float]]] = {}
    for r in csv.DictReader(line for line in text.splitlines() if not line.startswith("#")):
        rows.setdefault((r["provider"], r["axis"]), []).append((int(r["i"]), float(r["value"])))
    return {k: tuple(v for _, v in sorted(vals)) for k, vals in rows.items()}


def _physical(provider: str, length: float, width: float) -> tuple[Floats, Floats]:
    """A tracking provider's landmarks on the venue's ``length`` x ``width`` m pitch, in its own units: the Laws of the
    Game's fixed distances (six-yard line 5.5 m, spot 11 m, box 16.5 m deep; goal 7.32 m, six-yard box 18.32 m and box
    40.32 m wide). The same arithmetic as sdvplotR's physical_landmarks()."""
    along = np.array([0, 5.5, 11, 16.5, length / 2, length - 16.5, length - 11, length - 5.5, length], dtype=float)
    half = width / 2
    across = np.array(
        [0, half - 20.16, half - 9.16, half - 3.66, half + 3.66, half + 9.16, half + 20.16, width], dtype=float
    )
    if provider == "tracab":
        return (along - length / 2) * 100, (across - half) * 100
    if provider == "metrica":
        return along / length, 1 - across / width
    return along - length / 2, across - half


def _landmarks(provider: str, dims: tuple[float, float] | None) -> tuple[Floats, Floats]:
    """The x and y landmarks of ``provider`` (a canonical key); ``dims`` = (length, width) for tracking providers."""
    if provider in PHYSICAL:
        if dims is None:
            raise ValueError(f"{provider!r} needs the pitch's length and width")
        return _physical(provider, *dims)
    t = _table()
    return np.array(t[(provider, "x")], dtype=float), np.array(t[(provider, "y")], dtype=float)


def _interp(v: Floats, src: Floats, dst: Floats) -> Floats:
    """Piecewise-linear from ``src`` landmarks to ``dst``, extending the end segments beyond both ends (numpy.interp
    would clamp). The same index (findInterval's) and the same arithmetic as sdvplotR's interp_landmarks(), so the two
    packages agree to the last bit; NaN stays NaN."""
    order = np.argsort(src, kind="stable")
    src, dst = src[order], dst[order]
    j = np.clip(np.searchsorted(src, v, side="right") - 1, 0, len(src) - 2)
    out: Floats = dst[j] + (dst[j + 1] - dst[j]) * ((v - src[j]) / (src[j + 1] - src[j]))
    return out

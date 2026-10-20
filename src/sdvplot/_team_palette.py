"""Team colors for a chart background: each readable against it (3:1, WCAG 1.4.11) and distinct from the teams before
it (CIE76 ΔE). A line-for-line port of sdvplot-js's ``team-palette.ts``; tests/test_team_palette.py holds it to that
module's output on every NBA, NFL, MLB and NHL team on three backgrounds (tests/fixtures/deckgl_shared.json)."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from sdvplot._contrast import contrast, hex6, mix, on_color
from sdvplot._errors import warn

MIN_CONTRAST = 3  # WCAG 1.4.11 (non-text contrast): a graphical object needs 3:1 against what is next to it
# The smallest CIE76 ΔE two teams' colors may sit apart: 20, the largest value sdvplot-js measured (2026-10-18) to
# leave every NBA, NFL, MLB and NHL team distinct with no warning on #181a1b, #000000 and #ffffff (team-palette.ts).
MIN_DELTA_E = 20
_STEP = 0.05  # the step, as a fraction of the way to the target color, of the readable and lightness mixes

Lab = tuple[float, float, float]

# JavaScript's Math.cbrt: math.cbrt from Python 3.11, else t ** (1 / 3) (t is positive where it is used); the shared
# fixture's palettes come out the same either way (checked with both)
_cbrt: Callable[[float], float] = getattr(math, "cbrt", lambda t: t ** (1 / 3))


def _lin(v: int) -> float:
    s = v / 255
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


def _f(t: float) -> float:
    return _cbrt(t) if t > 216 / 24389 else ((24389 / 27) * t) / 116 + 16 / 116


def _lab(color: str) -> Lab:
    """CIE Lab (D65) of a hex color."""
    n = int(hex6(color, drop_alpha=True)[1:], 16)
    r, g, b = _lin(n >> 16), _lin((n >> 8) & 255), _lin(n & 255)
    x = _f((0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047)
    y = _f(0.2126 * r + 0.7152 * g + 0.0722 * b)
    z = _f((0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883)
    return (116 * y - 16, 500 * (x - y), 200 * (y - z))


def _finv(t: float) -> float:
    return t**3 if t > 6 / 29 else 3 * (6 / 29) ** 2 * (t - 4 / 29)


def _round(x: float) -> int:
    """JavaScript's Math.round (half up), not Python's round (half to even)."""
    f = math.floor(x)
    return f + 1 if x - f >= 0.5 else f


def _gamma(v: float) -> str:
    c = min(1.0, max(0.0, v))  # out of gamut: clipped, and the hex is what gets measured
    s = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return f"{_round(s * 255):02x}"


def _from_lab(lab: Lab) -> str:
    """The hex color of a CIE Lab (D65) triple, clipped to sRGB."""
    l_, a, b = lab
    fy = (l_ + 16) / 116
    x, y, z = 0.95047 * _finv(fy + a / 500), _finv(fy), 1.08883 * _finv(fy - b / 200)
    return (
        f"#{_gamma(3.2406 * x - 1.5372 * y - 0.4986 * z)}{_gamma(-0.9689 * x + 1.8758 * y + 0.0415 * z)}"
        f"{_gamma(0.0557 * x - 0.204 * y + 1.057 * z)}"
    )


def _dist(p: Lab, q: Lab) -> float:
    return math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2])


def delta_e(a: str, b: str) -> float:
    """CIE76 ΔE: the Euclidean distance of two colors in Lab."""
    return _dist(_lab(a), _lab(b))


# The synthetic search grid around a team color, in LCh: lightness, hue and chroma steps, in team-palette.ts's order.
# ponytail: a fixed grid of about 5,000 points per base color, scanned only for a team whose brand colors both clash.
_L_STEPS = [(1 if k % 2 == 0 else -1) * 4 * math.ceil(k / 2) for k in range(25)]  # 0, -4, 4, ... ±48
_H_STEPS = [(1 if k % 2 == 0 else -1) * 10 * math.ceil(k / 2) for k in range(36)]  # 0, -10, 10, ... 180
_C_STEPS = [0, -15, 15, -30, 30, 45]


def _nearby(base: str) -> list[str]:
    """Colors near ``base``: its lightness, hue and chroma stepped, each clipped to sRGB."""
    l_, a, b = _lab(base)
    c = math.hypot(a, b)
    h = math.atan2(b, a)
    out = []
    for dl in _L_STEPS:
        for dh in _H_STEPS:
            for dc in _C_STEPS:
                cc = max(0.0, c + dc)
                hh = h + (dh * math.pi) / 180
                out.append(_from_lab((min(100.0, max(0.0, l_ + dl)), cc * math.cos(hh), cc * math.sin(hh))))
    return out


def _mixes(c: str, target: str) -> list[str]:
    """``c`` mixed STEP, 2 STEP, ... of the way to ``target`` (the steps accumulated, as team-palette.ts's loop)."""
    out, t = [], _STEP
    while t < 1:
        out.append(mix(c, target, t))
        t += _STEP
    return out


def readable(c: str, alt: str | None, bg: str) -> str:
    """``c``, else ``alt``, else ``c`` mixed towards the background's ink until it reaches 3:1 against ``bg``."""
    if contrast(c, bg) >= MIN_CONTRAST:
        return c
    if alt is not None and contrast(alt, bg) >= MIN_CONTRAST:
        return alt
    ink = on_color(bg)
    return next((m for m in _mixes(c, ink) if contrast(m, bg) >= MIN_CONTRAST), ink)


def team_palette(
    colors: Sequence[str],
    alts: Sequence[str | None],
    background: str,
    labels: Sequence[str] | None = None,
) -> list[str]:
    """One color per team for a chart on ``background``, in order: each readable against it, and at least
    ``MIN_DELTA_E`` from every earlier team's color. A team whose readable color is too close to an earlier one tries
    its other color (made readable); failing that, the colors near both (lightness, hue in LCh and chroma stepped)
    that are 3:1 and distinct, taking the one closest to the team's brand color (ΔE; the first generated on a tie).
    Only when none is left does it keep the readable color and warn once. Deterministic, and a color already readable
    and distinct is returned as it is."""
    names = list(labels) if labels is not None else [f"#{i + 1}" for i in range(len(colors))]
    bg = hex6(background)
    ink = on_color(bg)
    out: list[str] = []
    labs: list[Lab] = []

    def clash(c: str) -> int:
        p = _lab(c)
        return next((j for j, q in enumerate(labs) if _dist(p, q) < MIN_DELTA_E), -1)

    def ok(c: str) -> bool:
        return contrast(c, bg) >= MIN_CONTRAST and clash(c) < 0

    def keep(c: str) -> None:
        out.append(c)
        labs.append(_lab(c))

    for i, color in enumerate(colors):
        alt = alts[i] if i < len(alts) else None
        first = readable(color, alt, bg)
        if clash(first) < 0:
            keep(first)
            continue
        second = None if alt is None else readable(alt, None, bg)
        if second is not None and ok(second):
            keep(second)
            continue
        # the synthetic candidates, the one nearest the brand color first
        pool = [first]
        for to_ink, to_bg in zip(_mixes(first, ink), _mixes(first, bg), strict=True):
            pool += [to_ink, to_bg]
        pool += _nearby(first)
        if second is not None:
            pool += _nearby(second)
        brand = _lab(color)
        pick, best, seen = None, math.inf, set()
        for c in pool:
            if c in seen:
                continue
            seen.add(c)
            d = _dist(_lab(c), brand)
            if d < best and ok(c):
                pick, best = c, d
        if pick is not None:
            keep(pick)
            continue
        j = clash(first)
        warn(
            f"{names[i]} ({first}) stays within ΔE {MIN_DELTA_E} of {names[j]} ({out[j]}) on {bg}: no readable color "
            "of it is distinct"
        )
        keep(first)
    return out

"""Color readability, ported from sdvplotR (R/utils-theme.R): WCAG luminance and contrast, a readable ink, mixing."""

from __future__ import annotations

_HEX = set("0123456789abcdefABCDEF")


def hex6(color: str) -> str:
    """A color as lowercase ``#rrggbb``: accepts ``#rgb``, ``rgb``, ``#rrggbb`` and ``#rrggbbaa`` (alpha dropped)."""
    c = str(color).strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) == 8:
        c = c[:6]
    if len(c) != 6 or not set(c) <= _HEX:
        raise ValueError(f"not a hex color: {color!r}")
    return "#" + c.lower()


def luminance(color: str) -> float:
    """WCAG relative luminance, 0 (black) to 1 (white)."""
    c = hex6(color)
    rgb = [int(c[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio between two colors, 1 (same) to 21 (black on white)."""
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def on_color(background: str) -> str:
    """Black or white, whichever reads better on ``background`` (sdvplotR's ``.theme_on_color``)."""
    return "#000000" if contrast("#000000", background) >= contrast("#ffffff", background) else "#ffffff"


def mix(a: str, b: str, t: float) -> str:
    """The color ``t`` of the way from ``a`` to ``b`` in sRGB (``t`` in [0, 1])."""
    if not 0 <= t <= 1:
        raise ValueError(f"t must be in [0, 1], got {t!r}")
    ca, cb = hex6(a), hex6(b)
    out = [round(int(ca[i : i + 2], 16) * (1 - t) + int(cb[i : i + 2], 16) * t) for i in (1, 3, 5)]
    return "#" + "".join(f"{v:02x}" for v in out)

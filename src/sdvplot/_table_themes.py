"""The surveyed table-style registry (``data/table_themes.json``): resolve one theme, or list them."""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass
from functools import cache
from importlib import resources
from typing import Any, Literal

from sdvplot._errors import InputError

__all__ = ["TableThemeSpec", "sdv_table_themes", "table_theme_spec"]

# Same values and semantics as shoot.py ``palette()`` and sdvtables' registry.ts, so every language agrees.
_DEFAULTS = {
    "bg": "#ffffff",
    "text": "#222222",
    "muted": "#666666",
    "accent": "#c70000",
    "rule": "#222222",
    "hline": "#e5e5e5",
    "stripe": "#f5f5f5",
    "summaryBg": "#f0f0f0",
    "link": "#1a5fb4",
    "pos": "#17692f",
    "neg": "#a1231b",
    "posBg": "#e3f3e6",
    "negBg": "#fbe5e4",
    "heatLow": "#f8696b",
    "heatMid": "#fcfcff",
    "heatHigh": "#63be7b",
}
_DARK_DEFAULTS = {  # light fallbacks are unreadable on a dark ground
    "text": "#e8e8e8",
    "muted": "#a0a6ad",
    "rule": "#e8e8e8",
    "hline": "#2c3138",
    "stripe": "#1c2026",
    "summaryBg": "#2a2f36",
    "link": "#8ab4f8",
    "pos": "#5fd08a",
    "neg": "#ff8a80",
    "posBg": "#123522",
    "negBg": "#3d1614",
    "bg": "#14171c",
}
_REACTABLE_PORTS = ("espn", "fivethirtyeight", "pff")


@dataclass(frozen=True)
class TableThemeSpec:
    """One resolved registry theme: fonts, sizes, a full palette and structure with every ``{key}`` substituted."""

    id: str
    source: str
    category: str
    fonts: dict[str, Any]
    sizes: dict[str, Any]
    palette: dict[str, str]
    structure: dict[str, Any]
    dark_policy: str


@cache
def _registry() -> dict[str, Any]:
    text = resources.files("sdvplot").joinpath("data", "table_themes.json").read_text(encoding="utf-8")
    return dict(json.loads(text)["themes"])


def _palette(spec: dict[str, Any], mode: str) -> dict[str, str]:
    p: dict[str, str | None] = {**_DEFAULTS, **(_DARK_DEFAULTS if mode == "dark" else {})}
    p.update({k: v for k, v in (spec.get(mode) or {}).items() if v})
    p["page"] = p.get("page") or p["bg"]
    p["labelBg"] = p.get("labelBg") or p["bg"]
    p["labelColor"] = p.get("labelColor") or p["muted"]
    return {k: str(v) for k, v in p.items()}


def _border(css: str | None, palette: dict[str, str]) -> str:
    """``css`` with each ``{key}`` taken from the palette, else its default, else ``#888888``; empty is ``none``."""
    if not css:
        return "none"
    return re.sub(r"\{(\w+)\}", lambda m: palette.get(m.group(1)) or _DEFAULTS.get(m.group(1), "#888888"), css)


def table_theme_spec(name: str, mode: Literal["light", "dark"] = "light") -> TableThemeSpec:
    """Resolve a surveyed table theme (e.g. ``datagolf``, ``wikipedia``, ``nejm``) by its source name.

    Args:
        name: The theme id, as listed by ``sdv_table_themes()``. ``"espn"``, ``"fivethirtyeight"`` and ``"pff"``
            are reactablefmtr ports (``reactable_sdv_theme``), not registry ids; the surveyed look of those sites
            is ``"espn-site"``, ``"fivethirtyeight-site"`` and ``"pff-site"``.
        mode: ``"light"`` or ``"dark"``. Missing palette keys take the shared defaults.

    Returns:
        The frozen spec, with the palette complete and every ``{key}`` in the structure's border strings replaced.

    Raises:
        InputError: For an unknown name (with up to 3 close matches), a reactablefmtr name, an unknown ``mode``, or
            ``mode="dark"`` on a light-only theme (naming three dark-capable themes in the same category).

    Example:
        ::

            from sdvplot import table_theme_spec
            spec = table_theme_spec("datagolf", "dark")
            print(spec.palette["bg"])

    See Also:
        sdv_table_themes: list the available ids ;
        reactable_sdv_theme: reactablefmtr's own 27 themes
    """
    reg = _registry()
    if mode not in ("light", "dark"):
        raise InputError(f"mode must be 'light' or 'dark', not {mode!r}")
    if name not in reg:
        if name in _REACTABLE_PORTS:
            raise InputError(
                f'{name!r} is a reactablefmtr port, not a registry theme: use reactable_sdv_theme("{name}"), '
                f"or {name + '-site'!r} for the surveyed site look"
            )
        close = difflib.get_close_matches(name, reg, n=3)
        hint = f"; did you mean {', '.join(map(repr, close))}?" if close else ""
        raise InputError(f"unknown table theme {name!r}{hint} (see sdv_table_themes())")
    s = reg[name]
    if mode == "dark" and (s["darkPolicy"] == "none" or not s.get("dark")):
        alt = sorted(i for i, t in reg.items() if t["category"] == s["category"] and t["darkPolicy"] != "none")[:3]
        raise InputError(
            f"theme {name!r} is light-only; dark-capable themes in category {s['category']!r}: "
            f"{', '.join(alt) or '(none)'}"
        )
    pal = _palette(s, mode)
    structure = {k: _border(v, pal) if isinstance(v, str) else v for k, v in s["structure"].items()}
    return TableThemeSpec(
        id=name,
        source=s["source"],
        category=s["category"],
        fonts=dict(s["fonts"]),
        sizes=dict(s["sizes"]),
        palette=pal,
        structure=structure,
        dark_policy=s["darkPolicy"],
    )


def sdv_table_themes(mode: str | None = None, category: str | None = None) -> list[dict[str, str]]:
    """List the surveyed table themes, optionally only those usable in a mode or in one category.

    Args:
        mode: ``"dark"`` keeps only dark-capable themes; ``"light"`` or ``None`` keeps all.
        category: Keep only this category (e.g. ``"sports"``).

    Returns:
        One dict per theme with ``id``, ``source``, ``category`` and ``dark_policy``.

    Raises:
        InputError: If ``mode`` is not ``None``, ``"light"`` or ``"dark"``.

    Example:
        ::

            from sdvplot import sdv_table_themes
            print(len(sdv_table_themes(mode="dark")))

    See Also:
        table_theme_spec: resolve one theme
    """
    if mode not in (None, "light", "dark"):
        raise InputError(f"mode must be 'light' or 'dark', not {mode!r}")
    return [
        {"id": i, "source": s["source"], "category": s["category"], "dark_policy": s["darkPolicy"]}
        for i, s in _registry().items()
        if not (mode == "dark" and s["darkPolicy"] == "none") and (category is None or s["category"] == category)
    ]

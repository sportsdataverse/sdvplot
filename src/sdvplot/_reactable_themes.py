"""reactablefmtr's 27 table themes as ``reactable.Theme`` objects, plus a theme built from a team's colors.

The values are reactablefmtr's own, exported from its installed source by ``tools/export_reactablefmtr_themes.R`` into
``data/reactablefmtr_themes.json``: each theme with a sentinel ``"@<arg>@"`` wherever an argument lands, and the
argument defaults. A theme is built by swapping the sentinels for the caller's values (or the defaults).
"""

from __future__ import annotations

import difflib
import json
import re
from functools import cache
from importlib import resources
from typing import Any

from sdvplot._errors import InputError, requires_extra

with requires_extra("reactable"):
    from reactable import Theme

from sdvplot._colors import team_colors
from sdvplot._contrast import hex6, mix, on_color
from sdvplot._table_themes import _font_stack, _registry, table_theme_spec
from sdvplot._types import IdSystem

__all__ = ["reactable_sdv_args", "reactable_sdv_theme", "reactable_sdv_theme_team"]

_SENTINEL = re.compile(r"@([a-z_]+)@")
_DARK_FMTR = ("cyborg", "dark", "darkly", "hoverdark", "midnight", "midnightblue", "slate", "superhero")


@cache
def _themes() -> dict[str, Any]:
    text = resources.files("sdvplot").joinpath("data", "reactablefmtr_themes.json").read_text(encoding="utf-8")
    return dict(json.loads(text)["themes"])


THEME_NAMES: tuple[str, ...] = tuple(sorted(_themes()))


def _fill(value: Any, args: dict[str, Any]) -> Any:
    """``value`` with every sentinel replaced by its argument: a whole-string sentinel keeps the argument's type."""
    if isinstance(value, dict):
        filled = {k: _fill(v, args) for k, v in value.items()}
        return {k: v for k, v in filled.items() if v is not None}  # a None argument drops its key, as R drops NULL
    if isinstance(value, str):
        whole = _SENTINEL.fullmatch(value)
        if whole:
            return args[whole.group(1)]
        return _SENTINEL.sub(lambda m: str(args[m.group(1)]), value)
    return value


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _theme(props: dict[str, Any]) -> Theme:
    return Theme(**{_snake(k): v for k, v in props.items()})


def reactable_sdv_theme(
    name: str,
    *,
    mode: str = "light",
    font_size: float | None = None,
    font_color: str | None = None,
    header_font_size: float | None = None,
    header_font_color: str | None = None,
    background_color: str | None = None,
    cell_padding: float | str | None = None,
    centered: bool = False,
    **theme_args: Any,
) -> Theme:
    """One of reactablefmtr's 27 table themes, or any of the 122 surveyed registry themes (``sdv_table_themes()``).

    A reactablefmtr name wins over a registry id. ``"espn"``, ``"fivethirtyeight"`` and ``"pff"`` are the
    reactablefmtr ports; the surveyed look of those sites is ``"espn-site"``, ``"fivethirtyeight-site"`` and
    ``"pff-site"``. A registry theme is built from its palette, fonts and sizes: the text, background, hairline,
    stripe and hover colors, the header label style, the body font and the cell padding.

    Pass the result to ``Reactable(theme=...)``. (``reactable.options.theme`` would set it for every table in the
    session, so the theme is returned rather than set.) The themes do not load a font: give
    ``reactable_sdv_frame(font=...)`` a Google font for that.

    Args:
        name: The theme: "cerulean", "clean", "cosmo", "cyborg", "dark", "darkly", "default", "espn",
            "fivethirtyeight", "flatly", "hoverdark", "hoverlight", "journal", "lux", "midnight", "midnightblue",
            "minty", "no_lines", "nytimes", "pff", "sandstone", "sanfran", "slate", "spacelab", "sunrise",
            "superhero" or "void"; or a registry id such as "wikipedia", "datagolf" or "nejm".
        mode: "light" (default) or "dark". A reactablefmtr theme has no dark variant, so "dark" is accepted only for
            the themes that are dark already ("cyborg", "dark", "darkly", "hoverdark", "midnight", "midnightblue",
            "slate", "superhero") and raises for the rest. A registry theme raises when it is light-only.
        font_size: The body font size in pixels; None for the theme's.
        font_color: The body text color; None for the theme's.
        header_font_size: The header font size in pixels; None for the theme's.
        header_font_color: The header text color; None for the theme's. "hoverdark" and "hoverlight" have none.
        background_color: The table background; None for the theme's (most light themes have none: the page shows).
        cell_padding: The cell padding, pixels or a CSS string; None for the theme's.
        centered: Center cell content vertically (useful with images).
        **theme_args: The theme's own extra arguments, by their reactablefmtr names: "nytimes" ``border_color``,
            ``border_width``; "sanfran" ``cell_color``, ``cell_border_width``, ``cell_border_color``,
            ``pagination_color``; "void" ``border_color``, ``border_width``, ``header_border_color``,
            ``header_border_width``.

    Returns:
        reactable.Theme: The theme.

    Raises:
        InputError: (a ValueError) If ``name`` is neither a reactablefmtr theme nor a registry id (close matches
            are named), ``mode`` is not "light" or "dark", ``mode="dark"`` is asked of a light theme, ``centered``
            is not a bool, or an argument is not one the theme takes.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_theme

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [12, 10, 9]})
            Reactable(df, theme=reactable_sdv_theme("espn"))
            Reactable(df, theme=reactable_sdv_theme("midnight", font_size=13, centered=True))
            Reactable(df, theme=reactable_sdv_theme("wikipedia"))

    See Also:
        Equivalent of reactablefmtr::espn, reactablefmtr::nytimes, reactablefmtr::fivethirtyeight and the other
        reactablefmtr themes: https://kcuilla.github.io/reactablefmtr/reference/index.html#themes
    """
    if mode not in ("light", "dark"):
        raise InputError(f"mode must be 'light' or 'dark', not {mode!r}")
    if not isinstance(centered, bool):
        raise InputError(f"centered must be True or False, got {centered!r}")
    spec = _themes().get(name)
    if spec is None:
        if theme_args:
            raise InputError(f"theme {name!r} takes no theme-specific arguments: {', '.join(sorted(theme_args))}")
        return _registry_theme(name, mode, font_size, font_color, header_font_size, header_font_color,
                               background_color, cell_padding, centered)  # fmt: skip
    if mode == "dark" and name not in _DARK_FMTR:
        raise InputError(f"reactablefmtr theme {name!r} has no dark variant; the dark ones are {', '.join(_DARK_FMTR)}")
    given = {"font_size": font_size, "font_color": font_color, "header_font_size": header_font_size,
             "header_font_color": header_font_color, "background_color": background_color,
             "cell_padding": cell_padding}  # fmt: skip
    given = {k: v for k, v in {**given, **theme_args}.items() if v is not None}
    defaults = spec["defaults"]
    unknown = sorted(set(given) - set(defaults))
    if unknown:
        raise InputError(
            f"theme {name!r} has no argument {', '.join(unknown)}; its arguments are {', '.join(defaults)}"
        )
    args = {**defaults, **given}
    props = dict(spec["theme"])
    if centered:
        props["cellStyle"] = spec["centered_cell_style"]
    return _theme(_fill(props, args))


def _registry_theme(
    name: str,
    mode: str,
    font_size: float | None,
    font_color: str | None,
    header_font_size: float | None,
    header_font_color: str | None,
    background_color: str | None,
    cell_padding: float | str | None,
    centered: bool,
) -> Theme:
    if name not in _registry() and name not in ("espn", "fivethirtyeight", "pff"):
        close = difflib.get_close_matches(name, [*_registry(), *THEME_NAMES], n=3)
        hint = f" (did you mean {', '.join(map(repr, close))}?)" if close else ""
        raise InputError(
            f"unknown theme {name!r}{hint}; the reactablefmtr themes are {', '.join(THEME_NAMES)}, "
            "or give a registry id (see sdv_table_themes())"
        )
    sp = table_theme_spec(name, mode)  # type: ignore[arg-type]  # mode is validated by the caller
    pal, fonts, sizes, st = sp.palette, sp.fonts, sp.sizes, sp.structure
    bg = background_color or pal["bg"]
    ink = font_color or pal["text"]
    pad = cell_padding if cell_padding is not None else f"{sizes['padY']}px {sizes['padX']}px"
    head: dict[str, Any] = {
        "background": pal["labelBg"],
        "color": header_font_color or pal["labelColor"],
        "fontWeight": fonts["labelWeight"],
        "textTransform": st["labelTransform"],
        "letterSpacing": st["labelTracking"],
        "fontFamily": _font_stack(fonts["label"]),
        "borderBottom": st["labelBorderBottom"],
        "fontSize": header_font_size if header_font_size is not None else sizes["label"],
    }
    props: dict[str, Any] = {
        "color": ink,
        "background_color": bg,
        "border_color": pal["hline"],
        "striped_color": pal["stripe"],
        # palette colours only: a caller override may be a CSS name (``"white"``), which mix() cannot blend
        "highlight_color": mix(pal["bg"], pal["text"], 0.06),
        "cell_padding": f"{pad}px" if isinstance(pad, (int, float)) else pad,
        "style": {
            "fontFamily": _font_stack(fonts["body"]),
            "fontSize": font_size if font_size is not None else sizes["body"],
        },
        "header_style": head,
        "table_style": {"borderTop": st["tableBorderTop"]},
    }
    if centered:
        props["cell_style"] = {"display": "flex", "flexDirection": "column", "justifyContent": "center"}
    return Theme(**props)


def reactable_sdv_args(name: str, *, mode: str = "light") -> dict[str, Any]:
    """The ``Reactable`` keyword arguments that make a table look like a registry or reactablefmtr theme.

    Args:
        name: A reactablefmtr theme or a registry id, as in ``reactable_sdv_theme``.
        mode: "light" or "dark", as in ``reactable_sdv_theme``.

    Returns:
        dict: ``theme`` (a ``reactable.Theme``), ``striped``, ``highlight`` (always True), ``bordered`` (the
        theme draws column rules) and ``compact`` (its cell padding is 4 pixels or less). A reactablefmtr theme
        returns its own ``Theme`` with the other keys at reactable's defaults.

    Raises:
        InputError: (a ValueError) As ``reactable_sdv_theme``.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_args

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [12, 10, 9]})
            Reactable(df, **reactable_sdv_args("wikipedia"))
            Reactable(df, **reactable_sdv_args("datagolf", mode="dark"))

    See Also:
        reactable_sdv_theme: just the ``Theme``
    """
    theme = reactable_sdv_theme(name, mode=mode)
    if name in _themes():
        return {"theme": theme, "striped": False, "highlight": True, "bordered": False, "compact": False}
    sp = table_theme_spec(name, mode)  # type: ignore[arg-type]
    return {
        "theme": theme,
        "striped": bool(sp.structure["stripe"]),
        "highlight": True,
        "bordered": sp.structure["colRule"] != "none",
        "compact": sp.sizes["padY"] <= 4,
    }


def reactable_sdv_theme_team(
    team: Any,
    league: str,
    *,
    font_size: float | None = 15,
    font_color: str | None = None,
    header_font_size: float | None = 15,
    header_font_color: str | None = None,
    background_color: str | None = None,
    cell_padding: float | str | None = 6,
    centered: bool = False,
    season: Any = None,
    id_system: IdSystem = "auto",
) -> Theme:
    """A table theme in a team's colors: the header filled with the primary color over a rule in the secondary,
    stripes, hover and the current page button tinted with the primary, and every text color readable on its fill.

    Args:
        team: The team, any value ``resolve`` accepts (an abbreviation, a name, an id).
        league: The SDV league key, e.g. "nfl".
        font_size: The body font size in pixels.
        font_color: The body text color as a hex color; None for black or white, whichever reads better on the
            background.
        header_font_size: The header font size in pixels.
        header_font_color: The header text color as a hex color; None for black or white, whichever reads better on
            the primary.
        background_color: The table background as a hex color; None for white (the page shows through).
        cell_padding: The cell padding, pixels or a CSS string.
        centered: Center cell content vertically (useful with images).
        season: The season whose colors to use; None for today's.
        id_system: The id system of ``team``, as in ``resolve``.

    Returns:
        reactable.Theme: The theme.

    Raises:
        InputError: (a ValueError) If ``league`` or ``id_system`` is unknown, ``centered`` is not a bool, or
            ``background_color``, ``font_color`` or ``header_font_color`` is not a hex color.
        UnresolvedTeamError: (a ValueError) If ``team`` does not resolve.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_theme_team

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [12, 10, 9]})
            Reactable(df, theme=reactable_sdv_theme_team("KC", "nfl"))

    See Also:
        sdvplot's addition to the reactablefmtr themes (reactablefmtr::espn and friends):
        https://kcuilla.github.io/reactablefmtr/reference/index.html#themes
    """
    if not isinstance(centered, bool):
        raise InputError(f"centered must be True or False, got {centered!r}")
    colors = {"background_color": background_color, "font_color": font_color, "header_font_color": header_font_color}
    try:  # validate every caller color up front, so a bad one fails here with InputError, not deep inside mix()
        background_color, font_color, header_font_color = (None if v is None else hex6(v) for v in colors.values())
    except ValueError:
        bad = next(k for k, v in colors.items() if v is not None and not _is_hex(v))
        raise InputError(f"{bad} must be a hex color such as '#1a1a1a', got {colors[bad]!r}") from None
    kw: dict[str, Any] = {"season": season, "id_system": id_system, "strict": True}
    primary = hex6(str(team_colors(league, team, which="primary", **kw)))
    secondary = team_colors(league, team, which="secondary", **kw)
    rule = hex6(secondary) if secondary else primary
    if rule == primary:
        rule = on_color(primary)  # a rule in the header's own color would vanish
    page = background_color if background_color is not None else "#ffffff"
    ink = font_color or on_color(page)
    tint = mix(page, primary, 0.12)  # stripes and hover: light enough that the body ink still reads
    head_ink = header_font_color or on_color(primary)
    props: dict[str, Any] = {
        "color": ink,
        "backgroundColor": background_color,
        "borderColor": mix(page, ink, 0.15),
        "stripedColor": tint,
        "highlightColor": mix(page, primary, 0.2),
        "cellPadding": cell_padding,
        "tableStyle": {"fontSize": font_size},
        "headerStyle": {
            "backgroundColor": primary,
            "color": head_ink,
            "fontSize": header_font_size,
            "borderBottom": f"3px solid {rule}",
        },  # fmt: skip
        "groupHeaderStyle": {"backgroundColor": primary, "color": head_ink},
        "rowSelectedStyle": {"backgroundColor": tint},
        "pageButtonCurrentStyle": {"backgroundColor": primary, "color": head_ink},
        "pageButtonHoverStyle": {"backgroundColor": tint, "color": ink},
    }
    if centered:
        props["cellStyle"] = {"display": "flex", "flexDirection": "column", "justifyContent": "center"}
    return _theme(_fill(props, {}))


def _is_hex(value: Any) -> bool:
    try:
        hex6(value)
    except ValueError:
        return False
    return True

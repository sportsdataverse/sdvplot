"""reactablefmtr's 27 table themes as ``reactable.Theme`` objects, plus a theme built from a team's colors.

The values are reactablefmtr's own, exported from its installed source by ``tools/export_reactablefmtr_themes.R`` into
``data/reactablefmtr_themes.json``: each theme with a sentinel ``"@<arg>@"`` wherever an argument lands, and the
argument defaults. A theme is built by swapping the sentinels for the caller's values (or the defaults).
"""

from __future__ import annotations

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
from sdvplot._types import IdSystem

__all__ = ["reactable_sdv_theme", "reactable_sdv_theme_team"]

_SENTINEL = re.compile(r"@([a-z_]+)@")


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
    font_size: float | None = None,
    font_color: str | None = None,
    header_font_size: float | None = None,
    header_font_color: str | None = None,
    background_color: str | None = None,
    cell_padding: float | str | None = None,
    centered: bool = False,
    **theme_args: Any,
) -> Theme:
    """One of reactablefmtr's 27 table themes, with reactablefmtr's own colors, fonts, borders and paddings.

    Pass the result to ``Reactable(theme=...)``. (``reactable.options.theme`` would set it for every table in the
    session, so the theme is returned rather than set.) The themes do not load a font: give
    ``reactable_sdv_frame(font=...)`` a Google font for that.

    Args:
        name: The theme: "cerulean", "clean", "cosmo", "cyborg", "dark", "darkly", "default", "espn",
            "fivethirtyeight", "flatly", "hoverdark", "hoverlight", "journal", "lux", "midnight", "midnightblue",
            "minty", "no_lines", "nytimes", "pff", "sandstone", "sanfran", "slate", "spacelab", "sunrise",
            "superhero" or "void".
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
        InputError: (a ValueError) If ``name`` is not one of the 27 themes (the message lists them), ``centered`` is
            not a bool, or an argument is not one the theme takes.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_theme

            df = pd.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [12, 10, 9]})
            Reactable(df, theme=reactable_sdv_theme("espn"))
            Reactable(df, theme=reactable_sdv_theme("midnight", font_size=13, centered=True))

    See Also:
        Equivalent of reactablefmtr::espn, reactablefmtr::nytimes, reactablefmtr::fivethirtyeight and the other
        reactablefmtr themes: https://kcuilla.github.io/reactablefmtr/reference/index.html#themes
    """
    spec = _themes().get(name)
    if spec is None:
        raise InputError(f"unknown theme {name!r}; the themes are {', '.join(THEME_NAMES)}")
    if not isinstance(centered, bool):
        raise InputError(f"centered must be True or False, got {centered!r}")
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
        font_color: The body text color; None for black or white, whichever reads better on the background.
        header_font_size: The header font size in pixels.
        header_font_color: The header text color; None for black or white, whichever reads better on the primary.
        background_color: The table background as a hex color; None for white (the page shows through).
        cell_padding: The cell padding, pixels or a CSS string.
        centered: Center cell content vertically (useful with images).
        season: The season whose colors to use; None for today's.
        id_system: The id system of ``team``, as in ``resolve``.

    Returns:
        reactable.Theme: The theme.

    Raises:
        InputError: (a ValueError) If ``league`` or ``id_system`` is unknown, ``centered`` is not a bool, or
            ``background_color`` is not a hex color.
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
    kw: dict[str, Any] = {"season": season, "id_system": id_system, "strict": True}
    primary = hex6(str(team_colors(league, team, which="primary", **kw)))
    secondary = team_colors(league, team, which="secondary", **kw)
    rule = hex6(secondary) if secondary else primary
    if rule == primary:
        rule = on_color(primary)  # a rule in the header's own color would vanish
    page = hex6(background_color) if background_color is not None else "#ffffff"
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

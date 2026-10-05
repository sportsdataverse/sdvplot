"""reactable-py columns (``pip install sdvplot[reactable]``), ported from sdvplotR's ``reactable_sdv_*`` functions.

Each function returns ``reactable.Column`` objects for ``Reactable(columns=[...])``; pass the column's ``id`` (and any
other ``Column`` argument) as keywords. reactable-py runs the cell functions when the ``Reactable`` is built, so an
unknown value warns then, once per distinct value per column.
"""

from __future__ import annotations

import html
import math
import numbers
from typing import Any

from sdvplot._errors import InputError, requires_extra

with requires_extra("reactable"):
    import narwhals as nw
    from reactable import Column
    from reactable.models import CellInfo

from sdvplot._colors import team_colors
from sdvplot._contrast import hex6
from sdvplot._normalize import norm_season
from sdvplot._placement import KINDS, _missing, check_alpha
from sdvplot._tables import check_px, img_tag, mark_html
from sdvplot._types import IdSystem, Which

__all__ = [
    "reactable_sdv_cols_label",
    "reactable_sdv_headshots",
    "reactable_sdv_logos",
    "reactable_sdv_team_color_bar",
    "reactable_sdv_team_color_bg",
    "reactable_sdv_wordmarks",
]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)


def _image_column(
    kind: str,
    league: str,
    height: Any,
    *,
    season: Any = None,
    variant: str = "default",
    include_name: bool = False,
    default_img: str | None = None,
    id_system: str = "auto",
    strict: bool = False,
    column_kwargs: dict[str, Any],
) -> Column:
    h = check_px(height)
    norm_season(season, league=league)  # one season for the column: fail now, not inside reactable
    rendered: dict[str, str] = {}

    def cell(info: CellInfo) -> str:
        value = info.value
        if _missing(value):
            return ""
        key = str(value)
        if key not in rendered:  # resolve each distinct value once: one warning per unknown value
            (img,) = mark_html([value], league=league, kind=kind, height=h, season=season, variant=variant,
                               id_system=id_system, strict=strict, include_name=include_name)  # fmt: skip
            text = html.escape(key)
            if img is None and default_img is not None:
                img = img_tag(default_img, h, key, margin=include_name)
            rendered[key] = text if img is None else img + (text if include_name else "")
        return rendered[key]

    return Column(**{"html": True, **column_kwargs, "cell": cell})


def reactable_sdv_logos(
    *,
    league: str,
    variant: str = "default",
    height: Any = 30,
    default_img: str | None = None,
    season: Any = None,
    include_name: bool = False,
    id_system: IdSystem = "auto",
    strict: bool = False,
    **column_kwargs: Any,
) -> Column:
    """A reactable column that shows each cell's team as its logo.

    Args:
        league: The SDV league key, e.g. "nfl".
        variant: "default", "dark", or a named variant from ``marks()``.
        height: The image height in pixels.
        default_img: An image URL for values that do not resolve; None keeps their text.
        season: One season whose marks every cell shows; None for today's.
        include_name: Keep the cell's text after the logo.
        id_system: The id system of the column's values, as in ``resolve``: "auto" tries each in order; NHL stats
            ids need "nhl_id".
        strict: Raise UnresolvedTeamError (when the ``Reactable`` is built) instead of warning when a value does not
            resolve.
        **column_kwargs: Passed to ``reactable.Column``: ``id`` (the data column, required by reactable), ``name``,
            ``width``, ...

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer.

    Raises:
        ValueError: If ``height`` is not a number of pixels of at least 1, ``season`` is not one year, or ``id_system``
            is unknown.
        UnresolvedTeamError: If ``strict=True`` and a value does not resolve, when the ``Reactable`` is built.

    Example:
        ::

            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_logos
            import pandas as pd

            df = pd.DataFrame(
                {
                    "team": ["KC", "BUF", "BAL"],
                    "espn_id": ["3139477", "3918298", "3916387"],
                    "wins": [12, 10, 9],
                }
            )

            Reactable(df, columns=[reactable_sdv_logos(league="nfl", id="team", name="")])

    See Also:
        Ported from sdvplotR ``reactable_sdv_logos()``:
        https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_images.html
    """
    return _image_column("logo", league, height, season=season, variant=variant, include_name=include_name,
                         default_img=default_img, id_system=id_system, strict=strict,
                         column_kwargs=column_kwargs)  # fmt: skip


def reactable_sdv_wordmarks(
    *,
    league: str,
    variant: str = "default",
    height: Any = 30,
    default_img: str | None = None,
    season: Any = None,
    include_name: bool = False,
    id_system: IdSystem = "auto",
    strict: bool = False,
    **column_kwargs: Any,
) -> Column:
    """A reactable column that shows each cell's team as its wordmark.

    Args:
        league: The SDV league key, e.g. "nfl".
        variant: "default", "dark", or a named variant from ``marks()``.
        height: The image height in pixels.
        default_img: An image URL for values that do not resolve; None keeps their text.
        season: One season whose marks every cell shows; None for today's.
        include_name: Keep the cell's text after the wordmark.
        id_system: The id system of the column's values, as in ``resolve``: "auto" tries each in order; NHL stats
            ids need "nhl_id".
        strict: Raise UnresolvedTeamError (when the ``Reactable`` is built) instead of warning when a value does not
            resolve.
        **column_kwargs: Passed to ``reactable.Column`` (``id`` is required by reactable).

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer.

    Raises:
        ValueError: If ``height`` is not a number of pixels of at least 1, ``season`` is not one year, or ``id_system``
            is unknown.
        UnresolvedTeamError: If ``strict=True`` and a value does not resolve, when the ``Reactable`` is built.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_wordmarks

            df = pd.DataFrame(
                {
                    "team": ["KC", "BUF", "BAL"],
                    "espn_id": ["3139477", "3918298", "3916387"],
                    "wins": [12, 10, 9],
                }
            )

            Reactable(df, columns=[reactable_sdv_wordmarks(league="nfl", id="team")])

    See Also:
        Ported from sdvplotR ``reactable_sdv_wordmarks()``:
        https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_images.html
    """
    return _image_column("wordmark", league, height, season=season, variant=variant, include_name=include_name,
                         default_img=default_img, id_system=id_system, strict=strict,
                         column_kwargs=column_kwargs)  # fmt: skip


def reactable_sdv_headshots(
    *,
    league: str,
    height: Any = 40,
    default_img: str | None = None,
    id_system: str = "espn",
    **column_kwargs: Any,
) -> Column:
    """A reactable column that shows each cell's player id as the player's headshot.

    Args:
        league: The SDV league key, e.g. "nfl".
        height: The image height in pixels.
        default_img: An image URL for ids without a headshot; None keeps their text.
        id_system: "espn" (ESPN athlete ids) or "gsis" (NFL), as in ``headshot_url``.
        **column_kwargs: Passed to ``reactable.Column`` (``id`` is required by reactable).

    Returns:
        reactable.Column: The column, with ``html=True`` and a cell renderer.

    Raises:
        ValueError: If ``height`` is not a number of pixels of at least 1.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_headshots

            df = pd.DataFrame(
                {
                    "team": ["KC", "BUF", "BAL"],
                    "espn_id": ["3139477", "3918298", "3916387"],
                    "wins": [12, 10, 9],
                }
            )

            Reactable(df, columns=[reactable_sdv_headshots(league="nfl", id="espn_id", name="")])

    See Also:
        Ported from sdvplotR ``reactable_sdv_headshots()``:
        https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_images.html
    """
    return _image_column("headshot", league, height, default_img=default_img, id_system=id_system,
                         column_kwargs=column_kwargs)  # fmt: skip


def reactable_sdv_cols_label(
    data: Any,
    *,
    league: str,
    variant: str = "default",
    height: Any = 30,
    season: Any = None,
    mark_type: str = "logo",
    id_system: IdSystem = "auto",
    strict: bool = False,
    **column_kwargs: Any,
) -> list[Column]:
    """One reactable column per team-named column of ``data`` (a ``KC`` column, a ``BUF`` column, ...), its header
    the team's mark.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable``. Pass only the team-named columns
            (``df[["KC", "BUF"]]``) to avoid a warning for the others.
        league: The SDV league key, e.g. "nfl".
        variant: "default", "dark", or a named variant from ``marks()``.
        height: The image height in pixels.
        season: One season whose marks to show; None for today's.
        mark_type: "logo" or "wordmark".
        id_system: The id system of the column names, as in ``resolve``: "auto" tries each in order; NHL stats ids
            need "nhl_id".
        strict: Raise UnresolvedTeamError instead of warning when a column name does not resolve.
        **column_kwargs: Passed to every ``reactable.Column``.

    Returns:
        list[reactable.Column]: A column (``id`` = the column name, an empty ``name``, the mark as ``header``) for each
        column whose name resolves; the others are left out, with one SdvplotWarning.

    Raises:
        InputError: (a ValueError) If ``mark_type`` is not "logo"/"wordmark".
        ValueError: If ``height`` is not a number of pixels of at least 1, ``season`` is not one year, or ``id_system``
            is unknown.
        UnresolvedTeamError: If ``strict=True`` and a column name does not resolve.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_cols_label

            df = pd.DataFrame(
                {
                    "team": ["KC", "BUF", "BAL"],
                    "espn_id": ["3139477", "3918298", "3916387"],
                    "wins": [12, 10, 9],
                }
            )

            Reactable(df, columns=reactable_sdv_cols_label(df, league="nfl"))

    See Also:
        Ported from sdvplotR ``reactable_sdv_cols_label()``:
        https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_cols_label.html
    """
    h = check_px(height)
    if mark_type not in KINDS[:2]:
        raise InputError(f"mark_type must be 'logo' or 'wordmark', got {mark_type!r}")
    names = list(nw.from_native(data, eager_only=True).columns)
    imgs = mark_html(names, league=league, kind=mark_type, height=h, season=season, variant=variant,
                     id_system=id_system, strict=strict)  # fmt: skip
    return [
        Column(**{"name": "", "html": True, **column_kwargs, "id": name, "header": img})
        for name, img in zip(names, imgs, strict=True)
        if img is not None
    ]


def _row_colors(
    data: Any, team_col: str, league: str, which: Which, na_color: str, id_system: IdSystem, strict: bool
) -> tuple[Any, list[str]]:
    frame = nw.from_native(data, eager_only=True)
    if team_col not in frame.columns:
        raise ValueError(f"column {team_col!r} not found in data; columns are {frame.columns}")
    colors = team_colors(league, frame[team_col].to_list(), which=which, id_system=id_system, strict=strict)
    return frame, [c or na_color for c in colors]


def reactable_sdv_team_color_bar(
    data: Any,
    team_col: str,
    *,
    league: str,
    which: Which = "primary",
    max_value: float | None = None,
    na_color: str = "#b3b3b3",
    id_system: IdSystem = "auto",
    strict: bool = False,
    **column_kwargs: Any,
) -> Column:
    """A reactable column whose cells hold a bar in the row's team color, as long as the value's share of the maximum.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable`` (each row's team is read from it).
        team_col: The column of ``data`` holding the teams.
        league: The SDV league key, e.g. "nfl".
        which: "primary" or "secondary" team color.
        max_value: The value that fills the whole cell; None for the column's maximum.
        na_color: The CSS color for teams that do not resolve or have no color.
        id_system: The id system of ``team_col``, as in ``resolve``: "auto" tries each in order; NHL stats ids need
            "nhl_id".
        strict: Raise UnresolvedTeamError instead of warning when a team does not resolve.
        **column_kwargs: Passed to ``reactable.Column``; ``id`` names the styled column.

    Returns:
        reactable.Column: The column, with a ``style`` function.

    Raises:
        ValueError: If ``team_col`` is not a column of ``data``, ``which`` is not "primary"/"secondary", or
            ``id_system`` is unknown.
        UnresolvedTeamError: If ``strict=True`` and a team does not resolve.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_team_color_bar

            df = pd.DataFrame(
                {
                    "team": ["KC", "BUF", "BAL"],
                    "espn_id": ["3139477", "3918298", "3916387"],
                    "wins": [12, 10, 9],
                }
            )

            Reactable(df, columns=[reactable_sdv_team_color_bar(df, "team", league="nfl", id="wins")])

    See Also:
        Ported from sdvplotR ``reactable_sdv_team_color_bar()``:
        https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_team_color.html
    """
    frame, colors = _row_colors(data, team_col, league, which, na_color, id_system, strict)
    tops: dict[str, float] = {}

    def top(column: str) -> float:
        if column not in tops:
            values = [float(v) for v in frame[column].to_list() if isinstance(v, numbers.Real) and not _missing(v)]
            tops[column] = max_value if max_value is not None else max(values, default=math.nan)
        return tops[column]

    def bar(info: CellInfo) -> dict[str, str]:
        value, t = info.value, top(info.column_name)
        ok = isinstance(value, numbers.Real) and not _missing(value) and math.isfinite(t) and t != 0
        pct = round(100 * value / t, 1) if ok else 0
        c = colors[info.row_index]
        return {"background-image": f"linear-gradient(90deg, {c} {pct:g}%, transparent {pct:g}%)"}

    return Column(**{**column_kwargs, "style": bar})


def reactable_sdv_team_color_bg(
    data: Any,
    team_col: str,
    *,
    league: str,
    which: Which = "primary",
    alpha: float = 0.15,
    na_color: str = "#b3b3b3",
    id_system: IdSystem = "auto",
    strict: bool = False,
    **column_kwargs: Any,
) -> Column:
    """A reactable column whose cells are filled with the row's team color, mostly transparent.

    Args:
        data: The pandas or polars DataFrame passed to ``Reactable`` (each row's team is read from it).
        team_col: The column of ``data`` holding the teams.
        league: The SDV league key, e.g. "nfl".
        which: "primary" or "secondary" team color.
        alpha: The fill's opacity, 0 to 1.
        na_color: The hex color for teams that do not resolve or have no color.
        id_system: The id system of ``team_col``, as in ``resolve``: "auto" tries each in order; NHL stats ids need
            "nhl_id".
        strict: Raise UnresolvedTeamError instead of warning when a team does not resolve.
        **column_kwargs: Passed to ``reactable.Column``; ``id`` names the styled column.

    Returns:
        reactable.Column: The column, with a ``style`` function.

    Raises:
        ValueError: If ``team_col`` is not a column of ``data``, ``which`` is not "primary"/"secondary", ``alpha`` is
            outside [0, 1], ``na_color`` is not a hex color, or ``id_system`` is unknown.
        UnresolvedTeamError: If ``strict=True`` and a team does not resolve.

    Example:
        ::

            import pandas as pd
            from reactable import Reactable
            from sdvplot.reactable import reactable_sdv_team_color_bg

            df = pd.DataFrame(
                {
                    "team": ["KC", "BUF", "BAL"],
                    "espn_id": ["3139477", "3918298", "3916387"],
                    "wins": [12, 10, 9],
                }
            )

            Reactable(df, columns=[reactable_sdv_team_color_bg(df, "team", league="nfl", id="team")])

    See Also:
        Ported from sdvplotR ``reactable_sdv_team_color_bg()``:
        https://sdvplotR.sportsdataverse.org/reference/reactable_sdv_team_color.html
    """
    a = check_alpha(alpha)
    _, colors = _row_colors(data, team_col, league, which, na_color, id_system, strict)
    fills = [f"{hex6(c, drop_alpha=True)}{round(a * 255):02x}" for c in colors]  # alpha replaces any in na_color

    def fill(info: CellInfo) -> dict[str, str]:
        return {"background-color": fills[info.row_index]}

    return Column(**{**column_kwargs, "style": fill})

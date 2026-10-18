"""plottable columns of team logos, wordmarks and player headshots."""

from __future__ import annotations

import re
import warnings
from typing import Any

from sdvplot._errors import requires_extra

with requires_extra("plottable"):
    from plottable import ColumnDefinition

from sdvplot._contrast import contrast
from sdvplot._placement import place
from sdvplot._surface import _has_font
from sdvplot._table_themes import _generic_family, table_theme_spec
from sdvplot.matplotlib import _image

__all__ = ["headshot_column", "logo_column", "plottable_sdv_theme"]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)


def _cell(kind: str, league: str, season: Any, variant: str, id_system: str) -> Any:
    def draw(ax: Any, value: Any, **_: Any) -> None:
        ax.set_axis_off()
        placements = place([0.0], [0.0], [value], league=league, season=season, kind=kind, variant=variant,
                           id_system=id_system)  # fmt: skip
        if placements:
            ax.imshow(_image(placements[0]))
            ax.set_aspect("equal")
            ax._sdvplot_cell = placements[0].team_id

    return draw


def logo_column(
    name: str,
    *,
    league: str,
    season: Any = None,
    variant: str = "default",
    mark_type: str = "logo",
    id_system: str = "auto",
    **column_definition_kwargs: Any,
) -> ColumnDefinition:
    """A plottable column that shows each row's team as its logo (or wordmark).

    Args:
        name: The data column holding the teams.
        league: The SDV league key, e.g. "nfl".
        season: One season for every row.
        variant: "default", "dark", or a named variant from ``marks()``.
        mark_type: "logo" or "wordmark".
        id_system: The id system of the column's values.
        **column_definition_kwargs: Passed to ``plottable.ColumnDefinition`` (``title``, ``width``, ``group``, ...).

    Returns:
        plottable.ColumnDefinition: The column definition; an unknown team leaves its cell blank, with an
        SdvplotWarning.

    Raises:
        InputError: (a ValueError) When the table is drawn, if ``mark_type`` is not "logo" or "wordmark", ``league``,
            ``id_system`` or ``variant`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows
            for the league (the column definition itself is built without checking them).
        OfflineError: When the table is drawn, if the logo manifest or a mark's image is neither cached nor downloadable
            (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it
            sends a file that does not match the manifest's sha256, or one PIL cannot decode).
        UnsafeDownloadError: (an OSError) When the table is drawn, if a download is refused: larger than the byte cap,
            past the deadline, or redirected away from https.
        UnsafeCachePathError: (a ValueError) When the table is drawn, if the manifest's sha256 or extension for a mark
            would put the file outside the cache directory.
        OptionalDependencyError: When the table is drawn, if a mark is an SVG and the ``svg`` extra is not installed.

    Example:
        ::

            from plottable import Table
            from sdvplot.plottable import logo_column
            import pandas as pd

            df = pd.DataFrame(
                {
                    "team": ["KC", "BUF", "BAL"],
                    "espn_id": ["3139477", "3918298", "3916387"],
                    "wins": [12, 10, 9],
                }
            )

            Table(df, column_definitions=[logo_column("team", league="nfl", title="")])

    See Also:
        plottable: https://plottable.readthedocs.io/
    """
    draw = _cell(mark_type, league, season, variant, id_system)
    return ColumnDefinition(name=name, plot_fn=draw, **column_definition_kwargs)


def headshot_column(
    name: str, *, league: str, id_system: str = "espn", **column_definition_kwargs: Any
) -> ColumnDefinition:
    """A plottable column that shows each row's player as a headshot.

    Args:
        name: The data column holding the player ids.
        league: The SDV league key, e.g. "nfl".
        id_system: "espn" (ESPN athlete ids), "gsis" (NFL) or "league" (the league's own player id: nfl gsis, NBA and
            WNBA Stats ids, MLBAM, NHL), as in ``headshot_url``.
        **column_definition_kwargs: Passed to ``plottable.ColumnDefinition``.

    Returns:
        plottable.ColumnDefinition: The column definition; an unknown id leaves its cell blank, with an SdvplotWarning.

    Raises:
        InputError: (a ValueError) When the table is drawn, if ``league`` has no ESPN headshots or ``id_system`` is not
            valid for it.
        OfflineError: When the table is drawn, if a headshot, or with ``id_system="gsis"`` the nflverse player table, is
            neither cached nor downloadable (a DownloadError, also an OSError, for an HTTP error status).
        UnsafeDownloadError: (an OSError) When the table is drawn, if a download is refused: larger than the byte cap,
            past the deadline, or redirected away from https.

    Example:
        ::

            import pandas as pd
            from plottable import Table
            from sdvplot.plottable import headshot_column

            df = pd.DataFrame(
                {
                    "team": ["KC", "BUF", "BAL"],
                    "espn_id": ["3139477", "3918298", "3916387"],
                    "wins": [12, 10, 9],
                }
            )

            Table(df, column_definitions=[headshot_column("espn_id", league="nfl", title="")])

    See Also:
        sdvplotR geom_nfl_headshots(): https://sdvplotR.sportsdataverse.org/ ;
        sdvplot.plottable.logo_column: the same with team logos
    """
    draw = _cell("headshot", league, None, "default", id_system)
    return ColumnDefinition(name=name, plot_fn=draw, **column_definition_kwargs)


_warned_fonts: set[str] = set()  # families already warned about in this process
_LINESTYLES = {
    "solid": "-",
    "dotted": ":",
    "dashed": "--",
}  # "double" and the rest draw solid: matplotlib has no double


def _divider(css: str) -> dict[str, Any] | None:
    """A matplotlib line spec from a resolved CSS border ("1px dotted #ccc"), or None for "none"."""
    m = re.fullmatch(r"([\d.]+)px\s+(\w+)\s+(\S+)", css.strip())
    if not m:
        return None
    return {"linewidth": float(m.group(1)) * 0.75, "linestyle": _LINESTYLES.get(m.group(2), "-"), "color": m.group(3)}


def _family(family: str) -> str:
    """``family`` if matplotlib has it, else its generic fallback with one UserWarning per family per process."""
    if _has_font(family):
        return family
    fallback = _generic_family(family)
    if family not in _warned_fonts:
        _warned_fonts.add(family)
        warnings.warn(
            f"font {family!r} is not installed for matplotlib; using the {fallback!r} family instead",
            UserWarning,
            stacklevel=3,
        )
    return fallback


def plottable_sdv_theme(name: str, *, mode: str = "light") -> dict[str, Any]:
    """The ``plottable.Table`` keywords that style a table like one of the 122 surveyed themes.

    Args:
        name: The theme id, as listed by ``sdv_table_themes()`` (see ``table_theme_spec``).
        mode: ``"light"`` or ``"dark"``; dark raises on a light-only theme.

    Returns:
        dict: Keywords for ``Table`` (``textprops``, ``row_dividers``, ``row_divider_kw``, ``col_label_divider``,
        ``col_label_divider_kw``, ``col_label_cell_kw``, ``footer_divider``, ``footer_divider_kw``,
        ``column_border_kw``, ``odd_row_color``, ``even_row_color``) plus ``facecolor``, which ``Table`` does not
        accept: pop it and apply it with ``fig.set_facecolor`` (and ``ax.set_facecolor``). ``col_label_cell_kw`` is
        the header fill (the theme's ``labelBg``), empty unless body text keeps 3:1 contrast on it: plottable styles
        header text with the body ``textprops``, so ``labelColor`` and ``labelWeight`` cannot be applied. A body font
        matplotlib cannot find falls back to its generic family (serif, monospace or sans-serif) with one UserWarning
        per family per process.

    Raises:
        InputError: As ``table_theme_spec``: an unknown name or mode, or ``mode="dark"`` on a light-only theme.

    Example:
        ::

            import matplotlib.pyplot as plt
            import pandas as pd
            from plottable import Table
            from sdvplot.plottable import plottable_sdv_theme

            kw = plottable_sdv_theme("fangraphs")
            fig, ax = plt.subplots()
            fig.set_facecolor(kw.pop("facecolor"))
            Table(pd.DataFrame({"team": ["KC", "BUF"], "wins": [12, 10]}), ax=ax, **kw)

    See Also:
        sdvplot.table_theme_spec: the resolved spec ;
        sdvplot.reactable.reactable_sdv_theme: the same themes for reactable
    """
    spec = table_theme_spec(name, mode)  # type: ignore[arg-type]
    pal, st = spec.palette, spec.structure
    row, head, foot, col = (_divider(st[k]) for k in ("rowRule", "labelBorderBottom", "tableBorderBottom", "colRule"))
    label_bg = pal.get("labelBg")
    # plottable's col_label_cell_kw goes to the header Rectangle only: header text takes the body textprops, so the
    # theme's labelColor/labelWeight cannot be applied. Fill the header only where body text stays readable on it.
    header = (
        {"facecolor": label_bg} if label_bg and label_bg != pal["bg"] and contrast(label_bg, pal["text"]) >= 3 else {}
    )
    return {
        "textprops": {
            "fontfamily": _family(spec.fonts["body"]),
            "fontsize": spec.sizes["body"] * 0.75,
            "fontweight": spec.fonts["bodyWeight"],
            "color": pal["text"],
        },
        "row_dividers": row is not None,
        "row_divider_kw": row or {},
        "col_label_cell_kw": header,
        "col_label_divider": head is not None,
        "col_label_divider_kw": head or {},
        "footer_divider": foot is not None,
        "footer_divider_kw": foot or {},
        "column_border_kw": col or {},
        "odd_row_color": pal["stripe"] if st["stripe"] else None,
        "even_row_color": None,
        "facecolor": pal["bg"],
    }

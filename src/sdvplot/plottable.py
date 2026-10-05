"""plottable columns of team logos, wordmarks and player headshots."""

from __future__ import annotations

from typing import Any

from sdvplot._errors import requires_extra

with requires_extra("plottable"):
    from plottable import ColumnDefinition

from sdvplot._placement import place
from sdvplot.matplotlib import _image

__all__ = ["headshot_column", "logo_column"]


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
        id_system: "espn" or "gsis" (NFL), as in ``headshot_url``.
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

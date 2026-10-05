"""What the table adapters share (sdvplot.great_tables, sdvplot.reactable): pixel heights and a mark's ``<img>`` markup.

No table library is imported here, so either adapter works without the other installed.
"""

from __future__ import annotations

import html
import math
import numbers
from typing import Any

import polars as pl

from sdvplot import _index
from sdvplot._errors import InputError
from sdvplot._normalize import norm_season
from sdvplot._placement import place


def _position(row: Any) -> Any:
    return int(row) if isinstance(row, numbers.Integral) and not isinstance(row, bool) else row


def row_positions(rows: Any) -> Any:
    """A great_tables row selection with numpy integers made plain ``int``s.

    great_tables' row resolver silently skips any position that is not an ``int``, so ``rows=[np.int64(1)]`` (or a
    numpy array of positions) would select nothing. Expressions, callables and ``None`` pass through unchanged.
    """
    if isinstance(rows, numbers.Integral) and not isinstance(rows, bool):
        return [int(rows)]
    if getattr(rows, "ndim", None) == 1 and hasattr(rows, "tolist"):  # a numpy array of positions
        rows = rows.tolist()
    if isinstance(rows, (list, tuple)):
        return [_position(r) for r in rows]
    return rows


def check_px(height: Any) -> float:
    """``height`` as a float, or ValueError unless it is a finite number of pixels, at least 1."""
    if isinstance(height, bool) or not isinstance(height, numbers.Real) or not math.isfinite(height) or height <= 0:
        raise InputError(f"height is the image height in pixels, a number > 0, got {height!r}")
    if height < 1:  # a plot's height is a fraction of the plot; a table's is pixels, so 0.1 would draw a 0.1 px image
        raise InputError(
            f"height is the image height in pixels for a table (such as 30), got {height!r}; a fraction of the plot "
            "height is the unit for plots, not tables"
        )
    return float(height)


def img_tag(src: str, height: float, alt: str, *, team: str | None = None, margin: bool = False) -> str:
    """An ``<img>`` ``height`` pixels tall; ``team`` adds the ``data-sdvplot-team`` attribute the test hooks read."""
    style = f"height:{height:g}px;vertical-align:middle" + (";margin-right:0.35em" if margin else "")
    data = f' data-sdvplot-team="{html.escape(team)}"' if team is not None else ""
    return f'<img src="{html.escape(src)}" style="{style}" alt="{html.escape(alt)}"{data}>'


def mark_html(
    values: list[Any],
    *,
    league: str,
    kind: str,
    height: float,
    season: Any = None,
    variant: str = "default",
    id_system: str = "auto",
    strict: bool = False,
    include_name: bool = False,
) -> list[str | None]:
    """The ``<img>`` of each value's mark, or None where there is none (one SdvplotWarning for those, from place()).

    ``season`` is one season for every value (sdvplotR's rule for tables); a list of seasons is a ValueError. The alt
    text is the team's name from the bundled index (the player id for headshots).
    """
    s = norm_season(season)
    n = len(values)
    placed = place(list(range(n)), [0] * n, values, league=league, season=s, kind=kind, variant=variant,
                   id_system=id_system, strict=strict)  # fmt: skip
    names: dict[str, str] = {}
    if kind != "headshot":
        rows = _index.team_table().filter(pl.col("league") == league).select("team_id", "name").iter_rows()
        names = {tid: name for tid, name in rows if name}
    out: list[str | None] = [None] * n
    for p in placed:
        out[p.x] = img_tag(p.url, height, names.get(p.team_id, p.team_id), team=p.team_id, margin=include_name)
    return out

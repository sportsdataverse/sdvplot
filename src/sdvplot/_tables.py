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
from sdvplot._normalize import norm_season
from sdvplot._placement import place


def check_px(height: Any) -> float:
    """``height`` as a float, or ValueError unless it is a positive, finite number of pixels."""
    if isinstance(height, bool) or not isinstance(height, numbers.Real) or not math.isfinite(height) or height <= 0:
        raise ValueError(f"height is the image height in pixels, a number > 0, got {height!r}")
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
    include_name: bool = False,
) -> list[str | None]:
    """The ``<img>`` of each value's mark, or None where there is none (one SdvplotWarning for those, from place()).

    ``season`` is one season for every value (sdvplotR's rule for tables); a list of seasons is a ValueError. The alt
    text is the team's name from the bundled index (the player id for headshots).
    """
    s = norm_season(season)
    n = len(values)
    placed = place(list(range(n)), [0] * n, values, league=league, season=s, kind=kind, variant=variant,
                   id_system=id_system)  # fmt: skip
    names: dict[str, str] = {}
    if kind != "headshot":
        rows = _index.team_table().filter(pl.col("league") == league).select("team_id", "name").iter_rows()
        names = {tid: name for tid, name in rows if name}
    out: list[str | None] = [None] * n
    for p in placed:
        out[p.x] = img_tag(p.url, height, names.get(p.team_id, p.team_id), team=p.team_id, margin=include_name)
    return out

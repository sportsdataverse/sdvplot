"""Choosing a team's mark from the manifest: season, variant, then source preference."""

from __future__ import annotations

import warnings
from typing import Any

import polars as pl

from sdvplot._errors import SdvplotWarning
from sdvplot._manifest import load_manifest
from sdvplot._resolve import resolve

# Official sources first, then archived copies, then derived crops (sdv-assets source names)
SOURCE_RANK: dict[str, int] = {
    "espn": 0,
    "nflverse": 1,
    "nhl": 1,
    "mlbstatic": 1,
    "fox": 1,
    "hockeytech": 2,
    "cricinfo": 2,
    "ncaa.com": 3,
    "nwhl.co": 4,
    "shiftstats": 4,
    "wayback": 4,
    "aaf.com": 5,
    "aaf-strip-crop": 6,
}


def marks(team: Any, league: str, *, id_system: str = "auto") -> pl.DataFrame:
    """Every archived mark for one team, best first (see select_mark for the rule)."""
    team_id = resolve(team, league, id_system=id_system, strict=True)
    m = load_manifest().filter(
        (pl.col("level") == "team") & (pl.col("league") == league) & (pl.col("entity_id") == team_id)
    )
    return (
        m.with_columns(
            pl.col("source").replace_strict(SOURCE_RANK, default=5, return_dtype=pl.Int8).alias("source_rank"),
            pl.col("valid_to").is_null().alias("_open"),
        )
        .sort(
            by=["source_rank", "_open", "valid_to", "first_seen"],
            descending=[False, True, True, True],
            nulls_last=True,
        )
        .drop("_open")
    )


def select_mark(
    team: Any, league: str, season: Any = None, variant: str = "default", mark_type: str = "logo"
) -> dict[str, Any] | None:
    """The best mark: requested variant then "default"; season-covering rows first (explicit ranges before
    open-ended ones), else any row; within a set, official sources and current marks first."""
    from sdvplot._normalize import norm_season

    s = norm_season(season)
    m = marks(team, league).filter(pl.col("mark_type") == mark_type)
    for v in dict.fromkeys([variant, "default"]):
        rows = m.filter(pl.col("variant") == v)
        if s is not None:
            covering = rows.filter(
                (pl.col("valid_from").is_null() | (pl.col("valid_from") <= s))
                & (pl.col("valid_to").is_null() | (pl.col("valid_to") >= s))
            )
            dated = covering.filter(pl.col("valid_from").is_not_null() | pl.col("valid_to").is_not_null())
            for df in (dated, covering):
                if df.height:
                    return df.row(0, named=True)
        if rows.height:
            return rows.row(0, named=True)
    return None


def logo_url(
    team: Any, league: str, season: Any = None, variant: str = "default", mark_type: str = "logo"
) -> str | None:
    """The CDN URL of the team's mark (what web libraries and great_tables embed), or None with a warning."""
    row = select_mark(team, league, season, variant, mark_type)
    if row is None:
        warnings.warn(f"no {mark_type} archived for {team!r} ({league})", SdvplotWarning, stacklevel=2)
        return None
    return str(row["archive_url"])

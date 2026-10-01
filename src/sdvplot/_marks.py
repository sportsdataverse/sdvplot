"""Choosing a team's mark from the manifest: season, variant, then source preference."""

from __future__ import annotations

import warnings
from typing import Any

import polars as pl

from sdvplot import _index
from sdvplot._errors import SdvplotWarning
from sdvplot._manifest import load_manifest
from sdvplot._normalize import norm_season
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


def _union(col: str, bound: pl.Expr) -> pl.Expr:
    """One side of the union of several ranges: null (unbounded) if any range is unbounded there."""
    return pl.when(pl.col(col).is_null().any()).then(None).otherwise(bound).alias(f"_alias_{col}")


def _mark_aliases(league: str) -> pl.DataFrame:
    """key ("source:entity_id", normalized like every alias value) -> canonical team_id, unique mappings only, with
    the season range of the mapping (R36: an old-abbreviation mark is dated by its relocation alias)."""
    return (
        _index.alias_table()
        .filter((pl.col("league") == league) & (pl.col("id_system") == "mark"))
        .with_columns(pl.col("value").str.strip_chars().str.to_lowercase().alias("_key"))
        .group_by("_key")
        .agg(
            pl.col("team_id").first(),
            pl.col("team_id").n_unique().alias("_n"),
            _union("valid_from", pl.col("valid_from").min()),
            _union("valid_to", pl.col("valid_to").max()),
        )
        .filter(pl.col("_n") == 1)
        .drop("_n")
    )


def marks(team: Any, league: str, season: Any = None, *, id_system: str = "auto") -> pl.DataFrame:
    """Every archived mark for one team, best first (see select_mark for the rule).

    Manifest entity ids are per-source, so rows reach a team only through its "mark" aliases; rows without a
    unique mapping are dropped, never matched on the raw id. valid_from/valid_to are each row's effective range:
    the manifest's, else the mark alias's (R36)."""
    team_id = resolve(team, league, season=season, id_system=id_system, strict=True)
    m = (
        load_manifest()
        .filter((pl.col("level") == "team") & (pl.col("league") == league))
        .with_columns(
            pl.concat_str(pl.col("source"), pl.lit(":"), pl.col("entity_id"))
            .str.strip_chars()
            .str.to_lowercase()
            .alias("_key")
        )
        .join(_mark_aliases(league), on="_key", how="inner")
        .filter(pl.col("team_id") == team_id)
        .with_columns(
            pl.coalesce("valid_from", "_alias_valid_from").alias("valid_from"),
            pl.coalesce("valid_to", "_alias_valid_to").alias("valid_to"),
        )
        .drop("_key", "_alias_valid_from", "_alias_valid_to")
    )
    return (
        m.with_columns(
            pl.col("source").replace_strict(SOURCE_RANK, default=5, return_dtype=pl.Int8).alias("source_rank"),
            pl.col("valid_to").is_null().alias("_open"),
        )
        .sort(
            by=["source_rank", "_open", "valid_to", "first_seen", "valid_from", "sha256"],
            descending=[False, True, True, True, True, False],
            nulls_last=True,
        )
        .drop("_open")
    )


def select_mark(
    team: Any, league: str, season: Any = None, variant: str = "default", mark_type: str = "logo"
) -> dict[str, Any] | None:
    """The best mark: requested variant, then "default", then any variant; season-covering rows first (explicit
    ranges before open-ended ones), else any row; within a set, official sources and current marks first.
    An unknown or ambiguous team gives None with the resolver's warning."""
    s = norm_season(season)
    team_id = resolve(team, league, season=s)
    if team_id is None:
        return None
    m = marks(team_id, league, s, id_system="team_id").filter(pl.col("mark_type") == mark_type)
    # sorted best-first, so the unfiltered frame's first row is the best of any variant
    for rows in (m.filter(pl.col("variant") == variant), m.filter(pl.col("variant") == "default"), m):
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
    team_id = resolve(team, league, season=season)
    if team_id is None:
        return None
    row = select_mark(team_id, league, season, variant, mark_type)
    if row is None:
        warnings.warn(f"no {mark_type} archived for {team!r} ({league})", SdvplotWarning, stacklevel=2)
        return None
    return str(row["archive_url"])

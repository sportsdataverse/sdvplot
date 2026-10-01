"""Choosing a team's mark from the manifest: season, variant, then source preference."""

from __future__ import annotations

import warnings
from typing import Any

import polars as pl

from sdvplot import _index
from sdvplot._errors import SdvplotWarning
from sdvplot._manifest import load_manifest
from sdvplot._normalize import norm_season
from sdvplot._resolve import _covers, one_team, resolve

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


MARK_TYPES = ("logo", "wordmark")


def _check_mark_type(mark_type: str) -> None:
    if mark_type not in MARK_TYPES:
        raise ValueError(f"mark_type must be one of {list(MARK_TYPES)}, got {mark_type!r}")


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


# league -> (the loaded manifest frame, its rows mapped and ranked). _manifest caches that frame per path+mtime, so
# a refreshed manifest is a new object and rebuilds; an index reload clears it (R45)
_RANKED: dict[str, tuple[pl.DataFrame, pl.DataFrame]] = {}
_index.on_reload(_RANKED.clear)


def _ranked(league: str) -> pl.DataFrame:
    """Every team-level manifest row of one league that maps to one canonical team, with its effective range,
    best first; marks() only filters it on team_id."""
    manifest = load_manifest()
    hit = _RANKED.get(league)
    if hit is not None and hit[0] is manifest:
        return hit[1]
    m = (
        manifest.filter((pl.col("level") == "team") & (pl.col("league") == league))
        .with_columns(
            pl.concat_str(pl.col("source"), pl.lit(":"), pl.col("entity_id"))
            .str.strip_chars()
            .str.to_lowercase()
            .alias("_key")
        )
        .join(_mark_aliases(league), on="_key", how="inner")
        .with_columns(
            pl.coalesce("valid_from", "_alias_valid_from").alias("valid_from"),
            pl.coalesce("valid_to", "_alias_valid_to").alias("valid_to"),
        )
        .drop("_key", "_alias_valid_from", "_alias_valid_to")
    )
    ranked = (
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
    _RANKED[league] = (manifest, ranked)
    return ranked


def marks(team: Any, league: str, season: Any = None, *, id_system: str = "auto") -> pl.DataFrame:
    """Every archived mark for one team, best first.

    Manifest entity ids are per-source, so rows reach a team only through its "mark" aliases; rows without a unique
    mapping are dropped, never matched on the raw id. ``valid_from``/``valid_to`` are each row's effective range: the
    manifest's, else the mark alias's.

    Args:
        team: One team identifier (abbreviation, name, ESPN id, ...).
        league: The SDV league key, e.g. "nfl".
        season: A season year, used to resolve a reused code.
        id_system: "auto" or one id-system name, as in ``resolve``.

    Returns:
        polars.DataFrame: One row per archived mark (logos and wordmarks, every variant and source) with its
        ``variant``, ``mark_type``, ``archive_url`` and ``source_rank``.

    Raises:
        TypeError: If ``team`` is not a single value.
        ValueError: If ``league`` or ``id_system`` is unknown.
        UnresolvedTeamError: If the team does not resolve.

    Example:
        ::

            import sdvplot

            sdvplot.marks("KC", "nfl").shape   # (19, 21)

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    team_id = resolve(one_team(team, "marks"), league, season=season, id_system=id_system, strict=True)
    return _ranked(league).filter(pl.col("team_id") == team_id)


def select_mark(
    team: Any, league: str, season: Any = None, variant: str = "default", mark_type: str = "logo"
) -> dict[str, Any] | None:
    """The best mark: the requested variant; then, keeping its polarity (R44), "default" and an on_light variant
    ("on_light", "*_on_light"), or for "dark" an on_dark variant and then "default"; then any variant. Within each,
    season-covering rows first (explicit ranges before open-ended ones), else any row; within a set, official
    sources and current marks first. An unknown or ambiguous team gives None with the resolver's warning."""
    _check_mark_type(mark_type)
    s = norm_season(season)
    team_id = resolve(one_team(team, "select_mark"), league, season=s)
    if team_id is None:
        return None
    # a team has tens of rows: choosing in Python costs less than one polars filter per step (R45)
    rows = [r for r in marks(team_id, league, s, id_system="team_id").to_dicts() if r["mark_type"] == mark_type]
    side = "dark" if variant == "dark" else "light"

    def polarity(v: str) -> bool:
        return v == f"on_{side}" or v.endswith(f"_on_{side}")

    def requested(v: str) -> bool:
        return v == variant

    def default(v: str) -> bool:
        return v == "default"

    order = [requested, polarity, default] if side == "dark" else [requested, default, polarity]
    # sorted best-first, so the first row of any set is its best
    for keep in [*order, None]:
        found = [r for r in rows if keep is None or keep(r["variant"])]
        if s is not None:
            covering = [r for r in found if _covers(r["valid_from"], r["valid_to"], s)]
            dated = [r for r in covering if r["valid_from"] is not None or r["valid_to"] is not None]
            for df in (dated, covering):
                if df:
                    return df[0]
        if found:
            return found[0]
    return None


def logo_url(
    team: Any, league: str, season: Any = None, variant: str = "default", mark_type: str = "logo"
) -> str | None:
    """The CDN URL of a team's logo or wordmark, chosen for the season.

    Picks the archived mark whose season range covers ``season`` (relocated franchises get their era's mark), then the
    requested variant, then the most authoritative source. Unknown teams return None with one SdvplotWarning.

    Args:
        team: One team identifier (abbreviation, name, ESPN id, ...).
        league: The SDV league key, e.g. "nfl", "cfb", "nhl".
        season: A season year; None picks the current mark.
        variant: "default", "dark", or a named variant from ``marks()``.
        mark_type: "logo" or "wordmark".

    Returns:
        str | None: The archive URL (content-addressed, immutable), or None when no mark exists.

    Raises:
        TypeError: If ``team`` is not a single value.
        ValueError: If ``league`` is unknown or ``mark_type`` is not "logo"/"wordmark".

    Example:
        ::

            import sdvplot

            sdvplot.logo_url("KC", "nfl")   # 'https://sdv.nyc3.cdn.digitaloceanspaces.com/assets/public/sha256/3d/3d77....png'

    See Also:
        sdvplotR ``logo_url``: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    _check_mark_type(mark_type)
    team_id = resolve(one_team(team, "logo_url"), league, season=season)
    if team_id is None:
        return None
    row = select_mark(team_id, league, season, variant, mark_type)
    if row is None:
        warnings.warn(f"no {mark_type} archived for {team!r} ({league})", SdvplotWarning, stacklevel=2)
        return None
    return str(row["archive_url"])

"""Choosing a team's mark from the manifest: variant, then season within each variant, then source preference."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, Any

from sdvplot import _index
from sdvplot._cache import MEMORY_CACHES
from sdvplot._errors import InputError, UnresolvedTeamError, warn
from sdvplot._manifest import load_manifest
from sdvplot._normalize import norm_season
from sdvplot._resolve import _covers, one_team, resolve
from sdvplot._types import IdSystem, MarkType

if TYPE_CHECKING:
    import polars as pl
else:
    from sdvplot._lazy import pl

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
        raise InputError(f"mark_type must be one of {list(MARK_TYPES)}, got {mark_type!r}")


# (the manifest frame, every variant it holds): rebuilt when a refreshed manifest is a new object, as _RANKED is. The
# frame is held weakly here and in _RANKED, so a refreshed or cleared one is freed (_manifest keeps only the latest)
_VARIANTS: list[tuple[weakref.ref[pl.DataFrame], frozenset[str]]] = []


def _check_variant(variant: str, league: str) -> None:
    """A variant no mark in the archive has is a typo, not one this team lacks (that falls back): ValueError listing
    the league's variants. "default" and "dark" are always valid."""
    if variant in ("default", "dark"):
        return
    manifest = load_manifest()
    if not _VARIANTS or _VARIANTS[0][0]() is not manifest:
        _VARIANTS[:] = [(weakref.ref(manifest), frozenset(manifest["variant"].drop_nulls().to_list()))]
    if not isinstance(variant, str) or variant not in _VARIANTS[0][1]:  # a list would be unhashable in the set
        _index.check_league(league)
        known = sorted({"default", "dark", *_ranked(league)["variant"].drop_nulls().to_list()})
        raise InputError(f"unknown variant {variant!r}: no mark in the archive has it; {league} marks come in {known}")


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


# league -> (the loaded manifest frame, weakly; its rows mapped and ranked). _manifest caches that frame per
# path+mtime, so a refreshed manifest is a new object and rebuilds; an index reload clears it (R45)
_RANKED: dict[str, tuple[weakref.ref[pl.DataFrame], pl.DataFrame]] = {}
_index.on_reload(_RANKED.clear)
# league -> (its ranked table, that table's rows as dicts by team_id, filled per team on first use): select_mark's
# lookup, a dict hit instead of a polars filter per call
_TEAM_ROWS: dict[str, tuple[pl.DataFrame, dict[str, list[dict[str, Any]]]]] = {}
for _clear in (_VARIANTS.clear, _RANKED.clear, _TEAM_ROWS.clear):
    MEMORY_CACHES.append(_clear)  # clear_cache() also drops what was built from the manifest it deletes


def _ranked(league: str) -> pl.DataFrame:
    """Every team-level manifest row of one league that maps to one canonical team, with its effective range,
    best first; marks() only filters it on team_id."""
    manifest = load_manifest()
    hit = _RANKED.get(league)
    if hit is not None and hit[0]() is manifest:
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
        .with_columns(  # the intersection of the row's range and its alias's (null = unbounded on that side)
            pl.max_horizontal("valid_from", "_alias_valid_from").alias("valid_from"),
            pl.min_horizontal("valid_to", "_alias_valid_to").alias("valid_to"),
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
    _RANKED[league] = (weakref.ref(manifest), ranked)
    return ranked


def _team_rows(team_id: str, league: str) -> list[dict[str, Any]]:
    """``_ranked(league)``'s rows for one team as dicts, best first; computed once per team per manifest load."""
    ranked = _ranked(league)
    hit = _TEAM_ROWS.get(league)
    if hit is None or hit[0] is not ranked:
        hit = _TEAM_ROWS[league] = (ranked, {})
    if team_id not in hit[1]:
        hit[1][team_id] = ranked.filter(pl.col("team_id") == team_id).to_dicts()
    return hit[1][team_id]


def marks(team: Any, league: str, *, season: Any = None, id_system: IdSystem = "auto") -> pl.DataFrame:
    """Every archived mark for one team, best first.

    Manifest entity ids are per-source, so rows reach a team only through its "mark" aliases; rows without a unique
    mapping are dropped, never matched on the raw id. ``valid_from``/``valid_to`` are each row's effective range: the
    manifest's, narrowed by the mark alias's (an open side takes the alias's).

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
        UnresolvedTeamError: If the team is null or does not resolve.
        OfflineError: If the logo manifest cannot be downloaded and no cached copy exists.

    Example:
        ::

            import sdvplot

            sdvplot.marks("KC", "nfl").shape   # (19, 21)

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    team_id = resolve(one_team(team, "marks"), league, season=season, id_system=id_system, strict=True)
    if team_id is None:  # a null team: strict resolve() lets nulls through as None
        raise UnresolvedTeamError(f"marks() needs a team, got {team!r}")
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
    _check_variant(variant, league)
    team_id = resolve(one_team(team, "select_mark"), league, season=s)
    if team_id is None:
        return None
    # a team has tens of rows: choosing in Python costs less than one polars filter per step (R45); the rows are
    # shared with _TEAM_ROWS, so the chosen one is handed out as a copy
    rows = [r for r in _team_rows(team_id, league) if r["mark_type"] == mark_type]
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
                    return dict(df[0])
        if found:
            return dict(found[0])
    return None


def logo_url(
    team: Any, league: str, *, season: Any = None, variant: str = "default", mark_type: MarkType = "logo"
) -> str | None:
    """The CDN URL of a team's logo or wordmark, chosen for the season.

    Picks the requested variant (falling back to a default or polarity variant), then within each variant the archived
    mark whose season range covers ``season`` (relocated franchises get their era's mark), then the most
    authoritative source. Unknown teams return None with one SdvplotWarning.

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
        ValueError: If ``league`` is unknown, ``mark_type`` is not "logo"/"wordmark", ``variant`` is a name no mark in
            the archive has (a typo; the message lists the league's variants), or ``season`` is out of range.
        OfflineError: If the logo manifest cannot be downloaded and no cached copy exists.

    Example:
        ::

            import sdvplot

            sdvplot.logo_url("KC", "nfl")   # 'https://sdv.nyc3.cdn.digitaloceanspaces.com/assets/public/sha256/3d/3d77....png'

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    _check_mark_type(mark_type)
    _check_variant(variant, league)
    team_id = resolve(one_team(team, "logo_url"), league, season=season)
    if team_id is None:
        return None
    row = select_mark(team_id, league, season, variant, mark_type)
    if row is None:
        warn(f"no {mark_type} archived for {team!r} ({league})")
        return None
    return str(row["archive_url"])

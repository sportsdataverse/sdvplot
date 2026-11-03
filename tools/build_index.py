"""Build the bundled team index (src/sdvplot/data) from the data-raw snapshots. Pure and deterministic: the same
data-raw always gives byte-equal frames. --check exits 1 when the committed index is out of date (run in CI).

Usage: uv run python tools/build_index.py [--check]
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections.abc import Callable
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
from fetch_sources import (  # noqa: E402
    ESPN_COLLEGE,
    ESPN_PLACEHOLDER,
    ESPN_SCHOOL_IDS,
    IDENTITY_SOURCES,
    LEAGUE_IDENTITY_SOURCES,
)
from sdvplot._index import ALIAS_SCHEMA, TEAM_SCHEMA  # noqa: E402
from sdvplot._normalize import norm_value  # noqa: E402  (sdvplotr keys compare as resolve() does)
from sdvplot._resolve import PRIORITY  # noqa: E402  (the R50 tri-code fallback follows resolve()'s order)

# The 13 junior and minor HockeyTech leagues the archive added in 2026-11 (sdv-py's sportsdataverse.hockeytech keys)
HOCKEYTECH_JUNIOR_MINOR = ["sphl", "chl", "bchl", "ajhl", "sjhl", "ojhl", "cchl", "gojhl", "mhl", "nojhl", "vijhl",
                           "kijhl", "mjhl"]  # fmt: skip
# A colorblind-safe qualitative palette for teams no source gives colors for (flagged color_source="fallback")
FALLBACK = [
    "#4e79a7",
    "#f28e2b",
    "#e15759",
    "#76b7b2",
    "#59a14f",
    "#edc948",
    "#b07aa1",
    "#ff9da7",
    "#9c755f",
    "#bab0ac",
]


# A row's range (valid_from, valid_to) meets another's (_from, _to); null is unbounded on that side
OVERLAPS = (pl.col("_from").is_null() | pl.col("valid_to").is_null() | (pl.col("_from") <= pl.col("valid_to"))) & (
    pl.col("_to").is_null() | pl.col("valid_from").is_null() | (pl.col("_to") >= pl.col("valid_from"))
)


def _csv(raw: Path, name: str) -> pl.DataFrame:
    return pl.read_csv(raw / name, infer_schema_length=0)  # all text: ids keep their exact form


def _hex(col: str) -> pl.Expr:
    """A color as "#rrggbb", or null for "NULL", blanks and anything that is not six hex digits."""
    c = pl.col(col).str.strip_chars().str.strip_chars_start("#").str.to_lowercase()
    return pl.when(c.str.contains(r"^[0-9a-f]{6}$")).then(pl.lit("#") + c).otherwise(None)


def _espn_colors(prefix: str) -> list[pl.Expr]:
    """ESPN's color and alternate_color as {prefix}_primary and {prefix}_secondary, both null where they are ESPN's
    stand-in (fetch_sources.ESPN_PLACEHOLDER: black alone, or with its stock red) and not the team's colors."""
    black, alts = ESPN_PLACEHOLDER
    p, s = _hex("color"), _hex("alternate_color")
    stand_in = (p == f"#{black}") & (s.is_null() | s.is_in([f"#{a}" for a in alts if a]))
    return [pl.when(~stand_in).then(e).alias(f"{prefix}_{side}") for e, side in ((p, "primary"), (s, "secondary"))]


def _norm(e: pl.Expr) -> pl.Expr:
    return e.str.strip_chars().str.to_lowercase()


def _fallback(league: str, team_id: str, offset: int) -> str:
    h = int(hashlib.sha256(f"{league}:{team_id}".encode()).hexdigest(), 16)
    return FALLBACK[(h + offset) % len(FALLBACK)]


def espn_teams(raw: Path) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """ESPN's teams list plus the teams its scoreboards use that the index would lack, missing from the list or from
    the archive (data-raw/espn_unlisted_teams.csv), as (all ESPN teams, the snapshot's teams of their own, second
    ids). A snapshot id whose name and abbreviation are a listed team's in the league is that team under a second id
    (women's college hockey's Minnesota State: 24059 beside 2364), returned as (league, team_id, espn_id); any other
    is a team of its own (Delaware, 48; SUNY Morrisville, 126813, listed but not archived). A listed team keeps its
    list row."""
    listed = _csv(raw, "espn_teams.csv")
    path = raw / "espn_unlisted_teams.csv"
    extra = _csv(raw, path.name) if path.exists() else listed.clear()
    keys = ["league", "display_name", "abbreviation"]
    twins = (
        extra.select(*keys, pl.col("team_id").alias("espn_id"))
        .join(listed.select(*keys, "team_id"), on=keys)
        .filter(pl.col("espn_id") != pl.col("team_id"))
    )
    assert not twins["espn_id"].is_duplicated().any(), f"an unlisted ESPN id matches several listed teams: {twins}"
    own = extra.join(twins.select("league", pl.col("espn_id").alias("team_id")), on=["league", "team_id"], how="anti")
    new = own.join(listed, on=["league", "team_id"], how="anti")
    own = pl.concat([new, listed.join(own, on=["league", "team_id"], how="semi")])  # a listed team: its list row
    return pl.concat([listed, new]), own, twins.select("league", "team_id", "espn_id")


def espn_school_colors(raw: Path, listed: pl.DataFrame) -> pl.DataFrame:
    """ESPN colors beyond a team's teams-list row, as (league, team_id, ep_primary, ep_secondary), from ESPN's entries:
    the teams lists (``listed``) and the per-team endpoint's rows (data-raw/espn_colors.csv), stand-ins dropped. In
    order: the team's own entry; the entry with its id in another ESPN_SCHOOL_IDS league at the same location (one
    school, one id); then, in ESPN_COLLEGE order, the college entry with exactly its display name and location, a name
    no other entry of either league has (college baseball and softball number their teams apart from the school, so
    this is how they reach it). No own entry, no colors."""
    entry = ["espn_league", "espn_id", "display_name", "location", "color", "alternate_color"]
    path = raw / "espn_colors.csv"
    ep = _csv(raw, path.name) if path.exists() else pl.DataFrame(schema=dict.fromkeys(["team_id", *entry], pl.String))
    entries = (
        pl.concat(
            [
                listed.select(pl.col("league").alias("espn_league"), pl.col("team_id").alias("espn_id"), *entry[2:]),
                ep.select("espn_league", pl.col("team_id").alias("espn_id"), *entry[2:]),
            ]
        )
        .with_columns(
            *_espn_colors("ep"), _norm(pl.col("display_name")).alias("_name"), _norm(pl.col("location")).alias("_loc")
        )
        # an entry with colors first, then the teams list's (stable: which name a colorless id keeps never depends on
        # how the rows happen to be ordered)
        .sort("espn_league", "espn_id", pl.col("ep_primary").is_null(), maintain_order=True)
        .unique(["espn_league", "espn_id"], keep="first", maintain_order=True)
    )
    own = entries.select(
        pl.col("espn_league").alias("league"), pl.col("espn_id").alias("team_id"), "_name", "_loc", "ep_primary",
        "ep_secondary", pl.lit(0).alias("_rank"),
    )  # fmt: skip
    colored = entries.drop_nulls("ep_primary")

    def ranked(leagues: list[str], start: int) -> pl.DataFrame:
        return pl.DataFrame({"espn_league": leagues, "_rank": range(start, start + len(leagues))})

    school = (
        own.filter(pl.col("league").is_in(ESPN_SCHOOL_IDS))
        .drop("ep_primary", "ep_secondary", "_rank")
        .join(colored, left_on=["team_id", "_loc"], right_on=["espn_id", "_loc"])
        .join(ranked(ESPN_SCHOOL_IDS, 1), on="espn_league")
    )
    unique_name = entries.group_by("espn_league", "_name").len().filter(pl.col("len") == 1).drop("len")
    named = (
        own.filter(pl.col("league").is_in(ESPN_COLLEGE))
        .drop("ep_primary", "ep_secondary", "_rank")
        .join(unique_name, left_on=["league", "_name"], right_on=["espn_league", "_name"], how="semi")
        .join(colored.join(unique_name, on=["espn_league", "_name"], how="semi"), on=["_name", "_loc"])
        .join(ranked(ESPN_COLLEGE, 1 + len(ESPN_SCHOOL_IDS)), on="espn_league")
    )
    cols = ["league", "team_id", "ep_primary", "ep_secondary", "_rank"]
    return (
        pl.concat([part.filter(pl.col("espn_league") != pl.col("league")).select(cols) for part in (school, named)])
        .vstack(own.select(cols).cast({"_rank": pl.Int64}))
        .drop_nulls("ep_primary")
        .sort("league", "team_id", "_rank")
        .unique(["league", "team_id"], keep="first", maintain_order=True)
        .drop("_rank")
    )


def logo_colors(raw: Path) -> pl.DataFrame:
    """Colors derived from each team's logo (data-raw/logo_colors.csv, tools/fetch_sources.py logo_colors), as
    (league, team_id, logo_primary, logo_secondary): the last resort, for a team no source publishes colors for."""
    cols = ["league", "team_id", "logo_primary", "logo_secondary"]
    if not (raw / "logo_colors.csv").exists():
        return pl.DataFrame(schema=dict.fromkeys(cols, pl.String))
    lc = _csv(raw, "logo_colors.csv")
    return lc.select(
        "league", "team_id", _hex("primary").alias("logo_primary"), _hex("secondary").alias("logo_secondary")
    )


def f1_teams(raw: Path) -> pl.DataFrame:
    """F1 constructors' Jolpica names and OpenF1 colors (data-raw/f1_teams.csv, tools/fetch_sources.py f1_team_rows),
    as (league, team_id, f1_name, of1_primary, of1_secondary): OpenF1 gives one color, so no secondary."""
    cols = ["league", "team_id", "f1_name", "of1_primary", "of1_secondary"]
    if not (raw / "f1_teams.csv").exists():
        return pl.DataFrame(schema=dict.fromkeys(cols, pl.String))
    return _csv(raw, "f1_teams.csv").select(
        pl.lit("f1").alias("league"),
        "team_id",
        pl.col("name").alias("f1_name"),
        _hex("color").alias("of1_primary"),
        pl.lit(None, pl.String).alias("of1_secondary"),
    )


# Color sources by precedence, as (color_source, column prefix): the first with a primary gives both colors, so one
# source's secondary never sits beside another's primary
COLOR_SOURCES = [("nflverse", "nflv"), ("espn", "espn"), ("espn", "ep"), ("openf1", "of1"), ("logo", "logo")]


def _first_source(value: Callable[[str, str], pl.Expr]) -> pl.Expr:
    e: pl.Expr = pl.lit(None, pl.String)
    for name, prefix in reversed(COLOR_SOURCES):
        e = pl.when(pl.col(f"{prefix}_primary").is_not_null()).then(value(name, prefix)).otherwise(e)
    return e


# Soccer is one pooled league of ESPN club ids. A domestic league's competition slug is a country code, optional
# qualifiers and its tier number (eng.1, eng.w.1, usa.usl.1, usa.ncaa.m.1), or one of the leagues ESPN names instead
# of numbering; cups, super cups, promotion playoffs and the confederations' and FIFA's competitions (eng.fa,
# eng.league_cup, fra.1.promotion.relegation, uefa.champions, fifa.world) are none. A team in a World Cup or its
# qualifying (men's, women's, youth) is a national team: no club plays in one.
SOCCER_LEAGUE = r"^[a-z]{3}(\.[a-z]+)*\.\d+$"
SOCCER_NAMED_LEAGUES = ["usa.nwsl", "usa.usl.l1", "can.w.nsl"]
SOCCER_NATIONAL = r"^fifa\.(w?world|wwc|w?worldq|wcq|wwcq)(\.|$)"


def soccer_competitions(raw: Path) -> pl.DataFrame:
    """data-raw/soccer_competitions.csv (sdv-assets' side manifest: each competition's latest season and the clubs ESPN
    lists in it), one row per (competition, club), with ``_domestic`` and ``_national`` flags from the slug."""
    cols = ["league", "competition", "season", "team_id", "competition_name", "_domestic", "_national"]
    if not (raw / "soccer_competitions.csv").exists():
        return pl.DataFrame(schema=dict.fromkeys(cols, pl.String)).cast({"season": pl.Int32, "_domestic": pl.Boolean,
                                                                         "_national": pl.Boolean})  # fmt: skip
    c = pl.col("competition")
    return (
        _csv(raw, "soccer_competitions.csv")
        .with_columns(
            pl.lit("soccer").alias("league"),
            pl.col("season").cast(pl.Int32),
            (c.str.contains(SOCCER_LEAGUE) | c.is_in(SOCCER_NAMED_LEAGUES)).alias("_domestic"),
            c.str.contains(SOCCER_NATIONAL).alias("_national"),
        )
        .select(cols)
        .unique(["competition", "team_id"], maintain_order=True)
    )


def soccer_leagues(sc: pl.DataFrame) -> pl.DataFrame:
    """(league, team_id, conference_id, conference): a club's domestic league, the league competition it was seen in
    in its latest season (slug and ESPN's name: "eng.1", "English Premier League"). A club in several that season gets
    none, never a guess."""
    d = sc.filter("_domestic").filter(pl.col("season") == pl.col("season").max().over("team_id"))
    return d.filter(pl.len().over("team_id") == 1).select(
        "league",
        "team_id",
        pl.col("competition").alias("conference_id"),
        pl.col("competition_name").alias("conference"),
    )


def build_teams(raw: Path) -> pl.DataFrame:
    all_espn, unlisted, _ = espn_teams(raw)
    base = _csv(raw, "manifest_teams.csv")
    # a scoreboard team the archive does not know is a team too (identity, no mark); its league's program
    programs = base.group_by("league").agg(pl.col("program").unique())
    new = unlisted.join(base, on=["league", "team_id"], how="anti").join(programs, on="league")
    assert (new["program"].list.len() == 1).all(), f"no single program for {new['league'].unique().to_list()}"
    new = new.select("league", "team_id", pl.col("display_name").alias("name"), pl.col("program").list.first())
    base = pl.concat([base, new])
    espn = all_espn.select(
        "league",
        "team_id",
        pl.col("abbreviation").alias("abbr"),
        pl.col("short_display_name").alias("short_name"),
        "location",
        *_espn_colors("espn"),
    )
    # nflverse also lists relocated codes (OAK, SD, STL) and LAR on the current team's ESPN logo; the curated file
    # names their canonical code, so only the current code is kept
    hist = _csv(raw, "curated/historical_abbrs.csv")
    old = hist.filter((pl.col("id_system") == "nflverse") & (pl.col("value") != pl.col("canonical")))["value"]
    nfl = (
        _csv(raw, "nflverse_teams.csv")
        .filter(~pl.col("team_abbr").is_in(old.to_list()))
        .with_columns(
            pl.col("team_logo_espn")
            .str.extract(r"/nfl/500(?:-dark)?/([a-z]+)\.png", 1)  # CAR's nflverse logo is the 500-dark one
            .str.to_uppercase()
            .alias("espn_abbr")
        )
    )
    espn_nfl = espn.filter(pl.col("league") == "nfl").select("team_id", pl.col("abbr").alias("espn_abbr"))
    nflv = nfl.join(espn_nfl, on="espn_abbr", how="inner").select(
        pl.lit("nfl").alias("league"),
        "team_id",
        pl.col("team_abbr").alias("nflv_abbr"),
        _hex("team_color").alias("nflv_primary"),
        _hex("team_color2").alias("nflv_secondary"),
    )
    assert not nflv["team_id"].is_duplicated().any(), f"several current nflverse codes per ESPN team: {nflv}"
    unmatched = sorted(set(nfl["team_abbr"]) - set(nflv["nflv_abbr"]))
    assert nflv.height == nfl.height and not unmatched, f"current nflverse teams with no ESPN team: {unmatched}"
    sc = soccer_competitions(raw)
    groups = pl.concat(
        [_csv(raw, "groups_latest.csv").select("league", "team_id", "conference_id", "conference"), soccer_leagues(sc)]
    )
    national = sc.filter("_national").select("league", "team_id", pl.lit("national").alias("_national")).unique()
    base = base.join(national, on=["league", "team_id"], how="left").with_columns(
        pl.coalesce("_national", "program").alias("program")
    )
    t = (
        base.join(espn, on=["league", "team_id"], how="left")
        .join(nflv, on=["league", "team_id"], how="left")
        .join(groups, on=["league", "team_id"], how="left")
        .join(espn_school_colors(raw, all_espn), on=["league", "team_id"], how="left")
        .join(f1_teams(raw), on=["league", "team_id"], how="left")
        .join(logo_colors(raw), on=["league", "team_id"], how="left")
        .join(current_extra_abbrs(raw), on=["league", "team_id"], how="left")
    )
    assert not t.select("league", "team_id").is_duplicated().any(), "a source repeats a (league, team_id)"
    t = t.with_columns(
        pl.coalesce("nflv_abbr", "abbr", "extra_abbr").alias("abbr"),
        pl.coalesce("f1_name", "name").alias("name"),
        _first_source(lambda name, _: pl.lit(name)).fill_null("fallback").alias("color_source"),
        _first_source(lambda _, p: pl.col(f"{p}_primary")).alias("color_primary"),
        _first_source(lambda _, p: pl.col(f"{p}_secondary")).alias("color_secondary"),
    ).with_columns(  # a secondary is a second color: one equal to the primary is none
        pl.when(pl.col("color_secondary") != pl.col("color_primary")).then(pl.col("color_secondary"))
    )
    return _fill_fallback(t).select(list(TEAM_SCHEMA)).cast(TEAM_SCHEMA).sort("league", "team_id")


def current_extra_abbrs(raw: Path) -> pl.DataFrame:
    """(league, team_id, extra_abbr): a team's current code in data-raw/espn_abbrs.csv (open-ended, valid_to empty),
    for the teams ESPN's teams lists omit (UTRGV, the Core API basketball teams), whose ``abbr`` the list cannot give.
    Only a fallback after the list's own code; a team with several current codes gets none."""
    cols = {"league": pl.String, "team_id": pl.String, "extra_abbr": pl.String}
    if not (raw / "espn_abbrs.csv").exists():
        return pl.DataFrame(schema=cols)
    return (
        _csv(raw, "espn_abbrs.csv")
        .filter(pl.col("valid_to").is_null() & pl.col("abbreviation").is_not_null())
        .group_by("league", "team_id")
        .agg(pl.col("abbreviation").unique())
        .filter(pl.col("abbreviation").list.len() == 1)
        .select("league", "team_id", pl.col("abbreviation").list.first().alias("extra_abbr"))
    )


def _fill_fallback(t: pl.DataFrame) -> pl.DataFrame:
    """The placeholder colors: a row with no primary takes both from the fixed palette (color_source "fallback")."""
    return t.with_columns(
        pl.struct("league", "team_id", "color_primary")
        .map_elements(lambda r: r["color_primary"] or _fallback(r["league"], r["team_id"], 0), return_dtype=pl.String)
        .alias("color_primary"),
        # R38: a fallback secondary only beside a fallback primary; a source primary keeps a null secondary
        pl.struct("league", "team_id", "color_secondary", "color_source")
        .map_elements(
            lambda r: (
                _fallback(r["league"], r["team_id"], 1) if r["color_source"] == "fallback" else r["color_secondary"]
            ),
            return_dtype=pl.String,
        )
        .alias("color_secondary"),
    )


# The conference, league and division rows sdvplot owns (sdvplotR's logo_ref rows, frozen when sdvplotR dropped it, plus
# the pro leagues' and the NCAA's): one line per (row, mark), the mark named by its manifest key
NON_TEAM_ROWS = "curated/non_team_rows.csv"
MARK_KEY = ["level", "mark_league", "source", "entity_id"]


def conference_rows(raw: Path, teams: pl.DataFrame) -> pl.DataFrame:
    """The conference and league rows (data-raw/curated/non_team_rows.csv: sdvplotR's college conferences, the AFC, NFC
    and NFL; the MLB, NBA, WNBA, NHL, AAF and NCAA rows, their pro conferences and the NHL's division marks) as index
    rows whose ``program`` is "conference" or "league" (a division mark's row is a "conference" one), shown only by
    teams(include_conferences=True). The id is the row's key, its short name ("SEC", "Big 12", "AFC", "East"): never a
    number, so it meets no team id. ``conference_id`` is the group slug the league's team rows carry for the same
    conference, so a team joins its conference row on it (a retired conference, the WAC, a division, a league has none);
    ``conference`` is a conference row's own full name. Colors are cbbplotR's (``color_source`` "cbbplotR", sdvplotR's
    values), the placeholder rule where the file has none; a secondary equal to the primary is none, as for teams. The
    rows get NO resolver aliases, only the "mark" ones of ``conference_mark_aliases`` and the "conference" ones of
    ``conference_aliases`` (id systems resolve() never reads): resolve() never answers a conference key unless asked
    for it (cfb's "MAC" is the Mid-American Conference and Macalester)."""
    path = raw / NON_TEAM_ROWS
    if not path.exists():
        return teams.clear()
    c = _csv(raw, NON_TEAM_ROWS).drop(*MARK_KEY, "valid_from", "valid_to").unique(maintain_order=True)
    assert not c.select("league", "team_id").is_duplicated().any(), f"{path.name}: a row's lines disagree: {c}"
    primary, secondary = _hex("color_primary"), _hex("color_secondary")
    out = c.select(
        "league",
        "team_id",
        pl.col("team_id").alias("abbr"),
        "name",
        "short_name",
        pl.lit(None, pl.String).alias("location"),
        "program",
        "conference_id",
        pl.when(pl.col("program") == "conference").then(pl.col("name")).alias("conference"),
        primary.alias("color_primary"),
        pl.when(secondary != primary).then(secondary).alias("color_secondary"),
        pl.when(primary.is_not_null()).then(pl.col("color_source")).otherwise(pl.lit("fallback")).alias("color_source"),
    )
    assert set(out["program"]) <= {"conference", "league"}, f"unknown program in {path.name}: {set(out['program'])}"
    unknown = out.join(teams.select("league").unique(), on="league", how="anti")["league"].to_list()
    assert not unknown, f"{path.name} names a league with no teams: {unknown}"
    slugs = teams.select("league", "conference_id").drop_nulls().unique()
    stray = out.drop_nulls("conference_id").join(slugs, on=["league", "conference_id"], how="anti")
    assert stray.height == 0, f"{path.name}: a conference_id no team row carries: {stray.select('league', 'team_id')}"
    assert out.join(teams, on=["league", "team_id"], how="semi").height == 0, "a conference key is a team id"
    return _fill_fallback(out).select(list(TEAM_SCHEMA)).cast(TEAM_SCHEMA).sort("league", "team_id")


def conference_mark_aliases(raw: Path, conf: pl.DataFrame) -> pl.DataFrame:
    """The conference and league rows' "mark" aliases: each line of data-raw/curated/non_team_rows.csv names a manifest
    row by its key ``level, mark_league, source, entity_id``, the alias value "level:league:source:entity_id" the
    runtime builds for every non-team manifest row (_marks._ranked), so a row reaches its mark's every variant (the
    dark 500-dark/8.png beside sec.png) and no key meets a team's "source:entity_id". ESPN files one conference logo
    under several leagues with a different group id each (sec.png: cfb 8, mbb and wbb 23), and some once, under
    "ncaa" (the WAC, the MAAC, the NCAA's own): the line names the one it means. ``valid_from`` / ``valid_to`` date the
    alias (the NHL's 2024 All-Star teams). Every named mark must be in data-raw/manifest_conferences.csv (the
    manifest's conference, league and division rows): one the archive lacks fails the build."""
    path = raw / "manifest_conferences.csv"
    if conf.is_empty() or not path.exists():
        return pl.DataFrame(schema=ALIAS_SCHEMA)
    lines = _csv(raw, NON_TEAM_ROWS)
    m = _csv(raw, path.name).select(*MARK_KEY[:1], pl.col("league").alias("mark_league"), *MARK_KEY[2:]).unique()
    missing = lines.join(m, on=MARK_KEY, how="anti").select("league", "team_id", *MARK_KEY)
    assert missing.height == 0, f"marks the archive has no copy of: {missing.rows()}"
    return (
        lines.select(
            "league",
            pl.lit("mark").alias("id_system"),
            pl.concat_str(pl.col(MARK_KEY), separator=":").alias("value"),
            "team_id",
            pl.col("valid_from").cast(pl.Int32),
            pl.col("valid_to").cast(pl.Int32),
        )
        .unique()
        .cast(ALIAS_SCHEMA)
    )


def conference_aliases(raw: Path, conf: pl.DataFrame) -> pl.DataFrame:
    """sdvplotR's other keys for its conference and league rows: the data-raw/sdvplotr_abbr_mapping.csv rows whose
    canon is a row's key ("SOUTHEASTERN CONFERENCE" and "SEC" -> SEC, "B1G" -> Big Ten, "PAC-10" -> Pac-12, "AMERICAN
    FOOTBALL CONFERENCE" -> AFC), as id system "conference" aliases of that row. Only the mark functions read them
    (_resolve._non_team, after every team alias), never resolve(). A key equal to the row's own key adds nothing, and
    one naming several rows of a league drops."""
    path = raw / "sdvplotr_abbr_mapping.csv"
    if conf.is_empty() or not path.exists():
        return pl.DataFrame(schema=ALIAS_SCHEMA)
    norm = {c: pl.col(c).map_elements(norm_value, return_dtype=pl.String).alias(f"_{c}") for c in ("key", "canon")}
    m = (
        _csv(raw, path.name)
        .join(conf.select(pl.col("league").alias("sport"), pl.col("team_id").alias("canon")), on=["sport", "canon"])
        .with_columns(*norm.values())
        .filter((pl.col("_key") != pl.col("_canon")) & (pl.col("canon").n_unique().over("sport", "_key") == 1))
    )
    return _alias(m, pl.col("sport"), "conference", "key", "canon").unique().cast(ALIAS_SCHEMA)


def _alias(df: pl.DataFrame, league: pl.Expr | str, system: str, value: str, team_id: str = "team_id") -> pl.DataFrame:
    lg = pl.lit(league) if isinstance(league, str) else league
    return df.select(
        lg.alias("league"),
        pl.lit(system).alias("id_system"),
        pl.col(value).alias("value"),
        pl.col(team_id).alias("team_id"),
        pl.lit(None, pl.Int32).alias("valid_from"),
        pl.lit(None, pl.Int32).alias("valid_to"),
    )


def nhl_aliases(nhl: pl.DataFrame, espn: pl.DataFrame) -> pl.DataFrame:
    """NHL stats API tri-codes (id_system "nhl", in PRIORITY) and numeric ids ("nhl_id", only when named: NHL ids
    1-28 are other teams' ESPN ids, R49): -> franchise -> the ESPN team with that nickname (R43). Franchises ESPN no
    longer lists (the Coyotes, the pre-war clubs) find none. The API gives no seasons, so the range is null."""
    espn_nhl = espn.filter(pl.col("league") == "nhl").select(
        "team_id", pl.col("nickname").alias("franchise_common_name")
    )
    j = nhl.join(espn_nhl, on="franchise_common_name")
    return pl.concat([_alias(j, "nhl", "nhl", "tri_code"), _alias(j, "nhl", "nhl_id", "nhl_id")])


def _nhl_by_tri_code(nhl: pl.DataFrame, espn: pl.DataFrame, aliases: pl.DataFrame) -> pl.DataFrame:
    """For marks only (R50): an NHL team whose franchise ESPN no longer lists (the Coyotes) goes to the team its
    tri-code resolves to through the user-facing aliases, the first PRIORITY system that knows it naming one team
    (ARI/PHX -> Utah, as sdvplotR). The alias has no range, so each mark keeps its manifest range."""
    espn_nicknames = espn.filter(pl.col("league") == "nhl").select(pl.col("nickname").alias("franchise_common_name"))
    orphans = nhl.join(espn_nicknames, on="franchise_common_name", how="anti")
    rank = pl.DataFrame({"id_system": list(PRIORITY), "_rank": range(len(PRIORITY))})
    first = (
        aliases.filter(pl.col("league") == "nhl")
        .join(rank, on="id_system")
        .select(_norm(pl.col("value")).alias("_key"), "team_id", "_rank")
        .filter(pl.col("_rank") == pl.col("_rank").min().over("_key"))
        .group_by("_key")
        .agg(pl.col("team_id").unique())
        .filter(pl.col("team_id").list.len() == 1)
        .with_columns(pl.col("team_id").list.first())
    )
    j = orphans.with_columns(_norm(pl.col("tri_code")).alias("_key")).join(first, on="_key")
    return pl.concat([_alias(j, "nhl", "nhl", "tri_code"), _alias(j, "nhl", "nhl_id", "nhl_id")])


def sdvplotr_aliases(
    am: pl.DataFrame, hist: pl.DataFrame, aliases: pl.DataFrame, conf_keys: pl.DataFrame
) -> pl.DataFrame:
    """sdvplotR's keys (R43) in match_team_abbrs()'s order (sdvplotR #55): resolve_historical_abbr()'s table first,
    its target looked up in clean_team_abbrs()'s abbr_mapping, then abbr_mapping for every other key, so a relocation
    key wins over an alias of the same name. A key goes to the team its canonical abbreviation names today: the
    current nflverse alias in the NFL, the current espn_abbr alias elsewhere. A canon naming no team or several drops,
    and so does a key the name system gives several teams: sdvplotR keeps the first of a shared name ("NEW YORK"),
    sdvplot never guesses. A canon that is a conference or league row's key (``conf_keys``: sport, canon) is that
    row's, never a team's (conference_aliases): cfb's "MID-AMERICAN CONFERENCE" is not Macalester, whose code is MAC."""
    am = am.join(conf_keys, on=["sport", "canon"], how="anti")
    hist = hist.join(
        am.select("sport", pl.col("key").alias("canon"), pl.col("canon").alias("_to")),
        on=["sport", "canon"],
        how="left",
    ).select("sport", "key", pl.coalesce("_to", "canon").alias("canon"))
    am = am.join(hist, on=["sport", "key"], how="anti")
    system = pl.when(pl.col("league") == "nfl").then(pl.lit("nflverse")).otherwise(pl.lit("espn_abbr"))
    canon = (
        aliases.filter((pl.col("id_system") == system) & pl.col("valid_to").is_null())
        .group_by("league", pl.col("value").alias("canon"))
        .agg(pl.col("team_id").unique())
        .filter(pl.col("team_id").list.len() == 1)
        .with_columns(pl.col("team_id").list.first())
    )
    key = pl.col("value").map_elements(norm_value, return_dtype=pl.String).alias("_key")
    shared = (
        aliases.filter(pl.col("id_system") == "name")
        .group_by("league", key)
        .agg(pl.col("team_id").n_unique().alias("n"))
        .filter(pl.col("n") > 1)
    )
    out = (
        pl.concat([am, hist])
        .rename({"sport": "league", "key": "value"})
        .join(canon, on=["league", "canon"])
        .with_columns(key)
        .join(shared, on=["league", "_key"], how="anti")
    )
    return _alias(out, pl.col("league"), "sdvplotr", "value")  # date_reused_codes dates a key another team held


def mark_aliases(
    marks: pl.DataFrame, teams: pl.DataFrame, aliases: pl.DataFrame, nhl: pl.DataFrame, espn: pl.DataFrame
) -> pl.DataFrame:
    """The `mark` crosswalk (Rulings R19, R25). A manifest row's entity_id is the id of its *source*, so each row maps
    to a canonical team by its source's rule. One row per (league, source, value="source:entity_id"), with n = the
    number of teams the key maps to; team_id and the season range (R36) are set only when n == 1."""
    src, lg = pl.col("source"), pl.col("league")
    identity = (
        src.is_in(sorted(IDENTITY_SOURCES)) & ((src != "espn") | pl.col("entity_id").str.contains(r"^\d+$"))
    ) | src.replace_strict(LEAGUE_IDENTITY_SOURCES, default=None).eq_missing(lg)
    system = (
        pl.when(identity)
        .then(pl.lit(None, pl.String))
        .when((src == "nflverse") | ((src == "espn") & (lg == "nfl")))
        .then(pl.lit("nflverse"))
        .when(src == "espn")
        .then(pl.lit("espn_abbr"))  # abbreviation-keyed ESPN logos (R32): curated espn_abbr rows
        .when((src == "mlbstatic") & (lg == "mlb"))
        .then(pl.lit("mlbstats"))
        .when(src == "nwhl.co")
        .then(pl.lit("name"))  # an upload id, not a team id: only the name identifies the team
        .when((src == "nhl") & pl.col("entity_id").str.contains(r"^\d+$"))
        .then(pl.lit("nhl_id"))
        .when(src == "nhl")
        .then(pl.lit("nhl"))  # a tri-code
    )
    m = marks.with_row_index("_row").with_columns(
        pl.col("valid_from", "valid_to").cast(pl.Int32),
        pl.concat_str(src, pl.lit(":"), pl.col("entity_id")).alias("value"),
        identity.alias("_identity"),
        system.alias("id_system"),
        _norm(pl.when(src == "nwhl.co").then(pl.col("entity_name")).otherwise(pl.col("entity_id"))).alias("_key"),
    )
    nhl_xw = pl.concat([nhl_aliases(nhl, espn), _nhl_by_tri_code(nhl, espn, aliases.cast(ALIAS_SCHEMA))])
    known = teams.select("league", "team_id")
    lookup = (
        pl.concat([aliases.cast(ALIAS_SCHEMA), nhl_xw.cast(ALIAS_SCHEMA)])
        .join(known, on=["league", "team_id"], how="semi")
        .select(
            "league",
            "id_system",
            _norm(pl.col("value")).alias("_key"),
            "team_id",
            pl.col("valid_from").alias("_from"),
            pl.col("valid_to").alias("_to"),
        )
    )
    # R25: a row with a range takes the dated (relocation) aliases over that range, else any alias over it; a row
    # without one takes the current alias (open-ended), else any. A key whose rows still name several teams gets none.
    has_range = pl.col("valid_from").is_not_null() | pl.col("valid_to").is_not_null()
    dated = pl.col("_from").is_not_null() | pl.col("_to").is_not_null()
    preferred = pl.when(has_range).then(dated & OVERLAPS).otherwise(pl.col("_to").is_null())
    via = (
        m.join(lookup, on=["league", "id_system", "_key"])
        # R40: an abbreviation-keyed ESPN logo outside the NFL maps only through a dated (curated relocation) alias,
        # never a current espn_abbr: a code a current team now holds would otherwise re-create the R36 tie
        .filter((pl.col("id_system") != "espn_abbr") | dated)
        .filter(pl.when(has_range).then(OVERLAPS).otherwise(True) & (preferred | ~preferred.any().over("_row")))
    )
    # R36: a mark reached through a relocation alias (one that ends) carries that alias's range; identity rows,
    # current abbreviations and the NHL crosswalk carry none
    historic = pl.col("_to").is_not_null()
    via = via.with_columns(
        pl.when(historic).then(pl.col("_from")).alias("_mfrom"), pl.when(historic).then(pl.col("_to")).alias("_mto")
    )
    ident = m.filter("_identity").with_columns(
        pl.col("entity_id").alias("team_id"),
        pl.lit(None, pl.Int32).alias("_mfrom"),
        pl.lit(None, pl.Int32).alias("_mto"),
    )
    keys = ["league", "source", "value"]
    cols = [*keys, "team_id", "_mfrom", "_mto"]
    cands = pl.concat([ident.select(cols), via.select(cols)]).join(known, on=["league", "team_id"], how="semi")
    # one key, several ranges for its one team: their union (null = unbounded)
    per_key = cands.group_by(keys).agg(
        pl.col("team_id").n_unique().alias("n"),
        pl.col("team_id").min(),
        pl.when(pl.col("_mfrom").is_null().any()).then(None).otherwise(pl.col("_mfrom").min()).alias("valid_from"),
        pl.when(pl.col("_mto").is_null().any()).then(None).otherwise(pl.col("_mto").max()).alias("valid_to"),
    )
    one = pl.col("n") == 1
    return (
        m.select(keys)
        .unique()
        .join(per_key, on=keys, how="left")
        .with_columns(
            pl.col("n").fill_null(0),
            *[pl.when(one).then(pl.col(c)).alias(c) for c in ("team_id", "valid_from", "valid_to")],
        )
        .sort(keys)
    )


def curated_mark_ranges(mark: pl.DataFrame, curated: pl.DataFrame) -> pl.DataFrame:
    """Season ranges for mark keys whose archived dates are wrong at their source (data-raw/curated/mark_ranges.csv,
    each with its reason): the key's alias takes the curated range, which narrows the manifest rows' own at runtime
    (marks()). A curated key that maps to no single team fails the build."""
    c = curated.select(
        "league", pl.col("mark").alias("value"), pl.col("valid_from", "valid_to").cast(pl.Int32), _curated=pl.lit(True)
    )
    missing = c.join(mark, on=["league", "value"], how="anti")
    assert missing.height == 0, f"curated mark ranges for keys with no mark alias: {missing.rows()}"
    return (
        mark.join(c, on=["league", "value"], how="left", suffix="_c")
        .with_columns(
            pl.when("_curated").then(pl.col(f"{side}_c")).otherwise(pl.col(side)).alias(side)
            for side in ("valid_from", "valid_to")
        )
        .select(mark.columns)
    )


def _report_marks(mk: pl.DataFrame) -> None:
    print(f"mark aliases: {mk.filter(pl.col('n') == 1).height} of {mk.height} manifest keys map to one team")
    bad = (
        mk.filter(pl.col("n") != 1)
        .group_by("league", "source")
        .agg(
            (pl.col("n") == 0).sum().alias("unmapped"),
            (pl.col("n") > 1).sum().alias("ambiguous"),
            pl.col("value").sort(),
        )
    )
    for r in bad.sort("league", "source").iter_rows(named=True):
        shown = ", ".join(r["value"][:8]) + (", ..." if len(r["value"]) > 8 else "")
        print(f"  {r['league']}/{r['source']}: {r['unmapped']} unmapped, {r['ambiguous']} ambiguous ({shown})")


def build_aliases(raw: Path, teams: pl.DataFrame, conf: pl.DataFrame) -> pl.DataFrame:
    espn, _, twins = espn_teams(raw)
    parts = [
        _alias(teams, pl.col("league"), "team_id", "team_id"),
        _alias(espn, pl.col("league"), "espn", "team_id"),
        _alias(twins, pl.col("league"), "espn", "espn_id"),
        _alias(espn, pl.col("league"), "espn_abbr", "abbreviation"),
        *[_alias(espn, pl.col("league"), "name", c) for c in ("display_name", "short_display_name", "location")],
        _alias(_csv(raw, "manifest_teams.csv"), pl.col("league"), "name", "name"),
        _alias(f1_teams(raw), "f1", "name", "f1_name"),
    ]
    if (raw / "espn_abbrs.csv").exists():
        parts.append(espn_extra_aliases(_csv(raw, "espn_abbrs.csv"), espn))
    by_league = {
        "hockeytech": ["pwhl", "ahl", "echl", "ohl", "whl", "qmjhl", "ushl", *HOCKEYTECH_JUNIOR_MINOR],
        "mlbstats": ["milb"],
        "pff": ["aaf"],
        "cricinfo": ["cricket"],
    }
    for system, leagues in by_league.items():
        parts.append(_alias(teams.filter(pl.col("league").is_in(leagues)), pl.col("league"), system, "team_id"))
    # curated codes (nflverse relocations, ESPN's historical abbreviations): canonical = the team's abbr today
    hist = _csv(raw, "curated/historical_abbrs.csv").join(
        teams.select("league", "team_id", "abbr"),
        left_on=["league", "canonical"],
        right_on=["league", "abbr"],
        how="inner",
    )
    assert hist.height == _csv(raw, "curated/historical_abbrs.csv").height, "a curated canonical names no single team"
    parts.append(
        hist.select(
            "league",
            "id_system",
            "value",
            "team_id",
            pl.col("valid_from").cast(pl.Int32),
            pl.col("valid_to").cast(pl.Int32),
        )
    )
    parts.append(_alias(teams.filter(pl.col("league") == "nfl"), "nfl", "nflverse", "abbr"))
    # cfbd: CFBD team ids are ESPN ids
    cfbd = _csv(raw, "cfbd_teams.csv")
    if cfbd.height:
        names = cfbd.with_columns(pl.col("alternate_names").str.split("|")).explode(
            "alternate_names", empty_as_null=True
        )
        parts += [
            _alias(cfbd, "cfb", "cfbd", "school"),
            _alias(cfbd.drop_nulls("abbreviation"), "cfb", "cfbd", "abbreviation"),
            _alias(
                names.drop_nulls("alternate_names").filter(pl.col("alternate_names") != ""),
                "cfb",
                "cfbd",
                "alternate_names",
            ),
        ]
    # nba_api: join on nickname (unique per league; abbreviations differ, e.g. GS vs GSW)
    nba = _csv(raw, "nba_api_teams.csv")
    if nba.height:
        espn_nba = espn.filter(pl.col("league") == "nba").select(
            "team_id", pl.col("short_display_name").alias("nickname")
        )
        j = nba.join(espn_nba, on="nickname", how="inner")
        assert j.height == nba.height, (
            f"nba_api teams unmatched by nickname: {sorted(set(nba['nickname']) - set(j['nickname']))}"
        )
        parts += [_alias(j, "nba", "nba_api", "nba_api_id"), _alias(j, "nba", "nba_api", "abbreviation")]
    # MLB Stats API: big-league teams join on the full name (R8: teamName "D-backs" vs ESPN "Diamondbacks");
    # MiLB ids are the sdv-assets milb team ids
    mlb = _csv(raw, "mlbstats_teams.csv")
    franchises = None  # MLB Stats API history joined to today's ESPN teams: the MLB Sports Reference codes use it
    if mlb.height:
        espn_mlb = espn.filter(pl.col("league") == "mlb").select("team_id", pl.col("display_name").alias("name"))
        mlb1 = mlb.filter(pl.col("sport_id") == "1")
        big = mlb1.join(espn_mlb, on="name", how="inner")
        assert big.height == mlb1.height, (
            f"MLB Stats teams unmatched to ESPN: {sorted(set(mlb1['name']) - set(big['name']))}"
        )
        milb = mlb.filter(pl.col("sport_id") != "1").with_columns(pl.col("mlbstats_id").alias("team_id"))
        parts += [
            _alias(milb, "milb", "mlbstats", c) for c in ("mlbstats_id", "abbreviation", "team_code", "file_code")
        ]
        franchises = mlb_franchise_history(_csv(raw, "mlbstats_history.csv"), big)
        parts.append(mlb_aliases(big, franchises))
    fg = _csv(raw, "curated/fangraphs_abbrs.csv")
    if fg.height:
        mlb_abbr = teams.filter(pl.col("league") == "mlb").select("team_id", pl.col("abbr").alias("espn_abbr"))
        j = fg.join(mlb_abbr, on="espn_abbr", how="inner")
        assert j.height == fg.height, (
            f"FanGraphs codes with no ESPN team: {sorted(set(fg['espn_abbr']) - set(j['espn_abbr']))}"
        )
        parts.append(_alias(j, "mlb", "fangraphs", "fangraphs"))
    if (raw / "ncaa_cfb_xwalk.csv").exists():
        parts.append(_alias(_csv(raw, "ncaa_cfb_xwalk.csv"), "cfb", "ncaa", "ncaa_id"))
    if (raw / "sr_codes.csv").exists():
        parts += _sr_aliases(_csv(raw, "sr_codes.csv"), espn, franchises)
    parts.append(nhl_aliases(_csv(raw, "nhl_teams.csv"), espn))
    known = teams.select("league", "team_id")
    a = (
        pl.concat([p.cast(ALIAS_SCHEMA) for p in parts], how="vertical")
        .drop_nulls(["value", "team_id"])
        .join(known, on=["league", "team_id"], how="semi")
    )
    if (raw / "sdvplotr_abbr_mapping.csv").exists():  # last: its keys go through the aliases above
        conf_keys = conf.select(pl.col("league").alias("sport"), pl.col("team_id").alias("canon"))
        sdvr = sdvplotr_aliases(
            _csv(raw, "sdvplotr_abbr_mapping.csv"), _csv(raw, "sdvplotr_historical.csv"), a, conf_keys
        )
        a = pl.concat([a, sdvr.cast(ALIAS_SCHEMA)])
    a = date_reused_codes(a)
    mk = mark_aliases(_csv(raw, "manifest_marks.csv"), known, a, _csv(raw, "nhl_teams.csv"), espn)
    _report_marks(mk)
    mark = mk.filter(pl.col("n") == 1).select(
        "league", pl.lit("mark").alias("id_system"), "value", "team_id", "valid_from", "valid_to"
    )
    if (raw / "curated" / "mark_ranges.csv").exists():
        mark = curated_mark_ranges(mark, _csv(raw, "curated/mark_ranges.csv"))
    # every soccer competition a club was seen in (UCL, cups, fifa.world), dated by that competition's season: id
    # system "competition", value = the slug. resolve() never reads it (_resolve._MARKS_ONLY)
    competition = soccer_competitions(raw).select(
        "league",
        pl.lit("competition").alias("id_system"),
        pl.col("competition").alias("value"),
        "team_id",
        pl.col("season").alias("valid_from"),
        pl.col("season").alias("valid_to"),
    )
    competition = competition.join(known, on=["league", "team_id"], how="semi")
    a = pl.concat([a, mark.cast(ALIAS_SCHEMA), competition.cast(ALIAS_SCHEMA)])
    return a.unique().sort("league", "id_system", "value", "team_id", "valid_from", "valid_to", nulls_last=True)


def espn_extra_aliases(extra: pl.DataFrame, espn: pl.DataFrame) -> pl.DataFrame:
    """ESPN abbreviations and names from outside the teams list (data-raw/espn_abbrs.csv): the per-team endpoint's,
    which scores and standings use (college baseball's NCSU where the list says NCST), and each season's scoreboard
    codes, dated. Left out: a code the list gives another team of the league (the list's team keeps it) and one the
    file gives two teams over overlapping seasons (ESPN's softball CEN is Centre and Central Baptist)."""
    key = _norm(pl.col("abbreviation")).alias("_key")
    holders = espn.select("league", key, pl.col("team_id").alias("_other")).drop_nulls("_key")
    e = extra.with_columns(key, pl.col("valid_from", "valid_to").cast(pl.Int32))
    other = e.select("league", "_key", pl.col("team_id").alias("_other"), pl.col("valid_from").alias("_from"),
                     pl.col("valid_to").alias("_to"))  # fmt: skip
    clash = pl.concat(
        [
            e.join(holders, on=["league", "_key"]).select("league", "_key", "team_id", "_other"),
            e.join(other, on=["league", "_key"]).filter(OVERLAPS).select("league", "_key", "team_id", "_other"),
        ]
    ).filter(pl.col("_other") != pl.col("team_id"))
    e = e.join(clash.select("league", "_key", "team_id").unique(), on=["league", "_key", "team_id"], how="anti")
    return pl.concat(
        [
            e.select(
                "league",
                pl.lit(system).alias("id_system"),
                pl.col(col).alias("value"),
                "team_id",
                "valid_from",
                "valid_to",
            )  # fmt: skip
            for system, col in (("espn_abbr", "abbreviation"), ("name", "display_name"))
        ]
    )


def date_reused_codes(a: pl.DataFrame) -> pl.DataFrame:
    """An undated ESPN abbreviation, NHL stats code or id, or sdvplotR key that a dated alias gives another team
    (MIL: the Braves 1953-65 in the MLB Stats API; WSH: Baseball-Reference's first Senators, 1901-60; sdvplotR's KCA,
    the 1955-67 Kansas City Athletics'; the NHL's WIN and team 33, the 1979-96 Jets, curated to the Coyotes' line)
    starts the season after that team's last, so a season of the earlier era goes to the earlier team; the code
    without a season still means today's team."""
    key = _norm(pl.col("value")).alias("_key")
    undated = pl.col("valid_from").is_null() & pl.col("valid_to").is_null()
    current = pl.col("id_system").is_in(["espn_abbr", "sdvplotr", "nhl", "nhl_id"]) & undated
    since = (
        a.filter((pl.col("id_system") != "espn_abbr") & pl.col("valid_to").is_not_null())
        .select("league", key, pl.col("team_id").alias("_other"), "valid_to")
        .join(a.filter(current).select("league", key, "team_id"), on=["league", "_key"])
        .filter(pl.col("_other") != pl.col("team_id"))
        .group_by("league", "_key", "team_id")
        .agg((pl.col("valid_to").max() + 1).alias("_since"))
    )
    return (
        a.with_columns(key, current.alias("_current"))
        .join(since, on=["league", "_key", "team_id"], how="left")
        .with_columns(pl.when("_current").then(pl.col("_since")).otherwise(pl.col("valid_from")).alias("valid_from"))
        .drop("_key", "_current", "_since")
    )


def mlb_franchise_history(hist: pl.DataFrame, big: pl.DataFrame) -> pl.DataFrame:
    """The MLB Stats API history (data-raw/mlbstats_history.csv) on today's ESPN teams: API ids are franchise ids, so
    each run of seasons a code or name was used goes to the franchise's ESPN team. A run that reaches the latest
    season is current: it stays open (valid_to null)."""
    last = hist["valid_to"].cast(pl.Int32).max()
    return hist.join(big.select("mlbstats_id", "team_id"), on="mlbstats_id").with_columns(
        pl.col("valid_from").cast(pl.Int32),
        pl.when(pl.col("valid_to").cast(pl.Int32) < last).then(pl.col("valid_to").cast(pl.Int32)).alias("valid_to"),
    )


def mlb_aliases(big: pl.DataFrame, franchises: pl.DataFrame) -> pl.DataFrame:
    """MLB Stats API codes of the big-league teams. Abbreviations and teamCodes carry the seasons the API used them,
    so a reused code goes to the franchise that held it that season (WAS: the Senators who became the Twins to 1960,
    the ones who became the Rangers 1961-71). teamCode and fileCode are the API's internal keys: one that spells an
    abbreviation the API gave another franchise in a season the key's own range covers is dropped, so a published
    abbreviation never names a team that only used it as a key that season. A key that only follows the other run
    keeps its dates: the Royals' "kca" from 1968 (the Kansas City Athletics' KCA ends in 1967), the Nationals' "was"
    from 2005. A fileCode has no range, so it meets every run."""
    owners = franchises.select(
        _norm(pl.col("abbreviation")).alias("_key"),
        pl.col("team_id").alias("_owner"),
        pl.col("valid_from").alias("_from"),
        pl.col("valid_to").alias("_to"),
    ).unique()
    big = big.with_columns(pl.lit(None, pl.Int32).alias("valid_from"), pl.lit(None, pl.Int32).alias("valid_to"))

    def keys_only(df: pl.DataFrame, col: str) -> pl.DataFrame:
        k = df.with_columns(_norm(pl.col(col)).alias("_key"))
        clash = k.join(owners, on="_key").filter((pl.col("_owner") != pl.col("team_id")) & OVERLAPS)
        return k.join(clash.select(col, "team_id", "valid_from").unique(), on=[col, "team_id", "valid_from"],
                      how="anti", nulls_equal=True)  # fmt: skip

    def dated(df: pl.DataFrame, col: str) -> pl.DataFrame:
        return df.select(
            pl.lit("mlb").alias("league"), pl.lit("mlbstats").alias("id_system"), pl.col(col).alias("value"),
            "team_id", "valid_from", "valid_to",
        )  # fmt: skip

    return pl.concat(
        [
            _alias(big, "mlb", "mlbstats", "mlbstats_id"),
            _alias(keys_only(big, "file_code"), "mlb", "mlbstats", "file_code"),
            dated(franchises, "abbreviation"),
            dated(keys_only(franchises, "team_code"), "team_code"),
        ]
    )


def _sr_aliases(sr: pl.DataFrame, espn: pl.DataFrame, franchises: pl.DataFrame | None = None) -> list[pl.DataFrame]:
    """Sports Reference codes (pybaseball bref, sportsipy), one row per code (R47): a code maps to the ESPN team whose
    display name equals the code's latest SR team name; its range is the seasons SR used it. Defunct franchises do
    not match and drop. MLB codes go through the MLB Stats API history instead (``franchises``): to the franchise
    that carried the code's latest SR name in its last season, so PHA, KCA or SEP reach today's team and the 1901
    Milwaukee Brewers (MLA) reach the Orioles, not today's Brewers."""
    sr = sr.with_columns(pl.col("valid_from", "valid_to").cast(pl.Int32))
    names = espn.select("league", "team_id", pl.col("display_name").alias("team_name"))
    j = sr.filter(pl.col("league") != "mlb").join(names, on=["league", "team_name"], how="inner")
    if franchises is not None:
        runs = franchises.select(pl.col("name").alias("team_name"), "team_id", pl.col("valid_from").alias("_from"),
                                 pl.col("valid_to").alias("_to"))  # fmt: skip
        mlb = sr.filter(pl.col("league") == "mlb").join(runs, on="team_name")
        on_run = (pl.col("valid_to") >= pl.col("_from")) & (
            pl.col("_to").is_null() | (pl.col("valid_to") <= pl.col("_to"))
        )
        j = pl.concat([j, mlb.filter(on_run).select(j.columns).unique()])
    return [
        j.select(
            "league",
            pl.lit(system).alias("id_system"),
            pl.col("team_code").alias("value"),
            "team_id",
            "valid_from",
            "valid_to",
        )
        for system in ("bref", "sportsipy")
    ]


def stamp(teams: pl.DataFrame, aliases: pl.DataFrame) -> str:
    """INDEX_VERSION (R37): a digest of the built frames, so it moves with the content (build logic included) and
    not with input bytes such as a Windows autocrlf checkout."""
    return hashlib.sha256((teams.write_csv() + aliases.write_csv()).encode("utf-8")).hexdigest()[:12]


def build(raw: Path) -> tuple[pl.DataFrame, pl.DataFrame, str]:
    teams = build_teams(raw)
    conf = conference_rows(raw, teams)
    aliases = build_aliases(raw, teams, conf)  # from the team rows only: a conference row is never a resolver candidate
    # a conference row's only aliases are "mark" (its logos) and "conference" ones; resolve() reads neither id system
    aliases = pl.concat([aliases, conference_mark_aliases(raw, conf), conference_aliases(raw, conf)]).sort(
        "league", "id_system", "value", "team_id", "valid_from", "valid_to", nulls_last=True
    )
    teams = pl.concat([teams, conf])
    return teams, aliases, stamp(teams, aliases)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--raw", type=Path, default=ROOT / "data-raw")
    p.add_argument("--out", type=Path, default=ROOT / "src" / "sdvplot" / "data")
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)
    teams, aliases, version = build(args.raw)
    if args.check:
        try:
            committed = [pl.read_parquet(args.out / f"{name}.parquet") for name in ("teams", "aliases")]
            # equals() compares values only (Int32 == Int64), and the stamp carries no dtype: compare schemas too
            same = (
                all(c.schema == b.schema and c.equals(b) for c, b in zip(committed, (teams, aliases), strict=True))
                and (args.out / "INDEX_VERSION").read_text(encoding="utf-8").strip() == version
            )
        except FileNotFoundError:
            same = False
        print("index is current" if same else "index is OUT OF DATE: run uv run python tools/build_index.py")
        return 0 if same else 1
    args.out.mkdir(parents=True, exist_ok=True)
    teams.write_parquet(args.out / "teams.parquet")
    aliases.write_parquet(args.out / "aliases.parquet")
    (args.out / "INDEX_VERSION").write_text(version + "\n", encoding="utf-8", newline="\n")  # LF on Windows too
    print(f"wrote {teams.height} teams, {aliases.height} aliases, index {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

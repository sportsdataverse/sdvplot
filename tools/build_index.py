"""Build the bundled team index (src/sdvplot/data) from the data-raw snapshots. Pure and deterministic: the same
data-raw always gives byte-equal frames. --check exits 1 when the committed index is out of date (run in CI).

Usage: uv run python tools/build_index.py [--check]
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tools")]
from fetch_sources import IDENTITY_SOURCES  # noqa: E402  (the team universe and the mark crosswalk share it)
from sdvplot._index import ALIAS_SCHEMA, TEAM_SCHEMA  # noqa: E402
from sdvplot._normalize import norm_value  # noqa: E402  (sdvplotr keys compare as resolve() does)
from sdvplot._resolve import PRIORITY  # noqa: E402  (the R50 tri-code fallback follows resolve()'s order)

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


def _csv(raw: Path, name: str) -> pl.DataFrame:
    return pl.read_csv(raw / name, infer_schema_length=0)  # all text: ids keep their exact form


def _hex(col: str) -> pl.Expr:
    """A color as "#rrggbb", or null for "NULL", blanks and anything that is not six hex digits."""
    c = pl.col(col).str.strip_chars().str.strip_chars_start("#").str.to_lowercase()
    return pl.when(c.str.contains(r"^[0-9a-f]{6}$")).then(pl.lit("#") + c).otherwise(None)


def _norm(e: pl.Expr) -> pl.Expr:
    return e.str.strip_chars().str.to_lowercase()


def _fallback(league: str, team_id: str, offset: int) -> str:
    h = int(hashlib.sha256(f"{league}:{team_id}".encode()).hexdigest(), 16)
    return FALLBACK[(h + offset) % len(FALLBACK)]


def build_teams(raw: Path) -> pl.DataFrame:
    base = _csv(raw, "manifest_teams.csv")
    espn = _csv(raw, "espn_teams.csv").select(
        "league",
        "team_id",
        pl.col("abbreviation").alias("abbr"),
        pl.col("short_display_name").alias("short_name"),
        "location",
        _hex("color").alias("espn_primary"),
        _hex("alternate_color").alias("espn_secondary"),
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
    groups = _csv(raw, "groups_latest.csv").select("league", "team_id", "conference_id", "conference")
    t = (
        base.join(espn, on=["league", "team_id"], how="left")
        .join(nflv, on=["league", "team_id"], how="left")
        .join(groups, on=["league", "team_id"], how="left")
    )
    assert not t.select("league", "team_id").is_duplicated().any(), "a source repeats a (league, team_id)"
    t = t.with_columns(
        pl.coalesce("nflv_abbr", "abbr").alias("abbr"),
        pl.when(pl.col("nflv_primary").is_not_null())
        .then(pl.lit("nflverse"))
        .when(pl.col("espn_primary").is_not_null())
        .then(pl.lit("espn"))
        .otherwise(pl.lit("fallback"))
        .alias("color_source"),
        pl.coalesce("nflv_primary", "espn_primary").alias("color_primary"),
        pl.coalesce("nflv_secondary", "espn_secondary").alias("color_secondary"),
    )
    t = t.with_columns(
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
    return t.select(list(TEAM_SCHEMA)).cast(TEAM_SCHEMA).sort("league", "team_id")


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


def sdvplotr_aliases(am: pl.DataFrame, hist: pl.DataFrame, aliases: pl.DataFrame) -> pl.DataFrame:
    """sdvplotR's keys (R43): clean_team_abbrs()'s abbr_mapping, then resolve_historical_abbr()'s table where
    abbr_mapping lacks the key, its target looked up in abbr_mapping again (sdvplotR's order). A key goes to the team
    its canonical abbreviation names today: the current nflverse alias in the NFL, the current espn_abbr alias
    elsewhere. A canon naming no team or several drops, and so does a key the name system gives several teams:
    sdvplotR keeps the first of a shared name ("NEW YORK"), sdvplot never guesses."""
    hist = (
        hist.join(am, on=["sport", "key"], how="anti")
        .join(
            am.select("sport", pl.col("key").alias("canon"), pl.col("canon").alias("_to")),
            on=["sport", "canon"],
            how="left",
        )
        .select("sport", "key", pl.coalesce("_to", "canon").alias("canon"))
    )
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
    # sdvplotR's keys have no seasons: one a dated alias gives to another team (KCA, the 1955-67 Kansas City
    # Athletics in the MLB Stats API and Baseball-Reference, the Royals in sdvplotR) cannot say which era it means
    dated = aliases.filter(pl.col("valid_from").is_not_null() | pl.col("valid_to").is_not_null())
    clash = (
        out.join(dated.select("league", key, pl.col("team_id").alias("_other")), on=["league", "_key"])
        .filter(pl.col("_other") != pl.col("team_id"))
        .select("league", "_key")
    )
    out = out.join(clash.unique(), on=["league", "_key"], how="anti")
    return _alias(out, pl.col("league"), "sdvplotr", "value")


def mark_aliases(
    marks: pl.DataFrame, teams: pl.DataFrame, aliases: pl.DataFrame, nhl: pl.DataFrame, espn: pl.DataFrame
) -> pl.DataFrame:
    """The `mark` crosswalk (Rulings R19, R25). A manifest row's entity_id is the id of its *source*, so each row maps
    to a canonical team by its source's rule. One row per (league, source, value="source:entity_id"), with n = the
    number of teams the key maps to; team_id and the season range (R36) are set only when n == 1."""
    src, lg = pl.col("source"), pl.col("league")
    identity = (
        src.is_in(sorted(IDENTITY_SOURCES)) & ((src != "espn") | pl.col("entity_id").str.contains(r"^\d+$"))
    ) | ((src == "mlbstatic") & (lg == "milb"))
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
    overlaps = (pl.col("_from").is_null() | pl.col("valid_to").is_null() | (pl.col("_from") <= pl.col("valid_to"))) & (
        pl.col("_to").is_null() | pl.col("valid_from").is_null() | (pl.col("_to") >= pl.col("valid_from"))
    )
    dated = pl.col("_from").is_not_null() | pl.col("_to").is_not_null()
    preferred = pl.when(has_range).then(dated & overlaps).otherwise(pl.col("_to").is_null())
    via = (
        m.join(lookup, on=["league", "id_system", "_key"])
        # R40: an abbreviation-keyed ESPN logo outside the NFL maps only through a dated (curated relocation) alias,
        # never a current espn_abbr: a code a current team now holds would otherwise re-create the R36 tie
        .filter((pl.col("id_system") != "espn_abbr") | dated)
        .filter(pl.when(has_range).then(overlaps).otherwise(True) & (preferred | ~preferred.any().over("_row")))
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


def build_aliases(raw: Path, teams: pl.DataFrame) -> pl.DataFrame:
    espn = _csv(raw, "espn_teams.csv")
    parts = [
        _alias(teams, pl.col("league"), "team_id", "team_id"),
        _alias(espn, pl.col("league"), "espn", "team_id"),
        _alias(espn, pl.col("league"), "espn_abbr", "abbreviation"),
        *[_alias(espn, pl.col("league"), "name", c) for c in ("display_name", "short_display_name", "location")],
        _alias(_csv(raw, "manifest_teams.csv"), pl.col("league"), "name", "name"),
    ]
    if (raw / "espn_abbrs.csv").exists():
        parts.append(espn_extra_aliases(_csv(raw, "espn_abbrs.csv"), espn))
    by_league = {
        "hockeytech": ["pwhl", "ahl", "echl", "ohl", "whl", "qmjhl", "ushl"],
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
    a = date_reused_codes(
        pl.concat([p.cast(ALIAS_SCHEMA) for p in parts], how="vertical")
        .drop_nulls(["value", "team_id"])
        .join(known, on=["league", "team_id"], how="semi")
    )
    if (raw / "sdvplotr_abbr_mapping.csv").exists():  # last: its keys go through the aliases above
        sdvr = sdvplotr_aliases(_csv(raw, "sdvplotr_abbr_mapping.csv"), _csv(raw, "sdvplotr_historical.csv"), a)
        a = pl.concat([a, sdvr.cast(ALIAS_SCHEMA)])
    mk = mark_aliases(_csv(raw, "manifest_marks.csv"), known, a, _csv(raw, "nhl_teams.csv"), espn)
    _report_marks(mk)
    mark = mk.filter(pl.col("n") == 1).select(
        "league", pl.lit("mark").alias("id_system"), "value", "team_id", "valid_from", "valid_to"
    )
    a = pl.concat([a, mark.cast(ALIAS_SCHEMA)])
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
    overlaps = (pl.col("_from").is_null() | pl.col("valid_to").is_null() | (pl.col("_from") <= pl.col("valid_to"))) & (
        pl.col("_to").is_null() | pl.col("valid_from").is_null() | (pl.col("_to") >= pl.col("valid_from"))
    )
    clash = pl.concat(
        [
            e.join(holders, on=["league", "_key"]).select("league", "_key", "team_id", "_other"),
            e.join(other, on=["league", "_key"]).filter(overlaps).select("league", "_key", "team_id", "_other"),
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
    """An undated ESPN abbreviation that a dated alias gives another team (MIL: the Braves 1953-65 in the MLB Stats
    API; WSH: Baseball-Reference's first Senators, 1901-60) starts the season after that team's last, so a season of
    the earlier era goes to the earlier team; the code without a season still means today's team."""
    key = _norm(pl.col("value")).alias("_key")
    current = (pl.col("id_system") == "espn_abbr") & pl.col("valid_from").is_null() & pl.col("valid_to").is_null()
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
    abbreviation the API gave another franchise (the Royals' teamCode "kca", the 1955-67 Kansas City Athletics' KCA)
    is dropped, so a published abbreviation never names a team that only used it as a key."""
    owners = franchises.select(_norm(pl.col("abbreviation")).alias("_key"), pl.col("team_id").alias("_owner")).unique()

    def keys_only(df: pl.DataFrame, col: str) -> pl.DataFrame:
        k = df.with_columns(_norm(pl.col(col)).alias("_key"))
        clash = k.join(owners, on="_key").filter(pl.col("_owner") != pl.col("team_id")).select("_key", "team_id")
        return k.join(clash.unique(), on=["_key", "team_id"], how="anti")

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
    aliases = build_aliases(raw, teams)
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

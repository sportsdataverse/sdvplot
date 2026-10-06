"""sdvplotR parity (spec §1, R43) against the SHIPPED index: a clean_team_abbrs() key resolves to the team its
canonical abbreviation does, and a resolve_historical_abbr() key to its franchise today."""

import os
from pathlib import Path

import polars as pl
import pytest

import sdvplot

pytestmark = [pytest.mark.real_index, pytest.mark.filterwarnings("ignore::sdvplot._errors.SdvplotWarning")]
RAW = Path(__file__).parents[1] / "data-raw"
# The keys that still miss, each with its reason (final-fix-report.md, F1). A new gap fails the test.
KNOWN_GAPS = {
    # a place several teams share: sdvplotR keeps its first team, sdvplot never guesses
    ("mlb", "CHICAGO"),
    ("mlb", "LOS ANGELES"),
    ("mlb", "NEW YORK"),
    ("nfl", "LOS ANGELES"),
    ("nfl", "NEW YORK"),
    ("nhl", "NEW YORK"),
    ("cfb", "CHARLOTTE"),  # CFBD names two teams "Charlotte", and cfbd decides before sdvplotr
}
# ESPN's cfb teams list omits UTRGV (292); its per-team endpoint's RGV is in data-raw/espn_abbrs.csv, so sdvplotR's
# UTRGV and TEXAS-RIO GRANDE VALLEY keys resolve through their canonical RGV (tests/test_real_index.py).


def _csv(name):
    return pl.read_csv(RAW / name, infer_schema_length=0)


def test_abbr_mapping_keys_resolve_like_their_canonical_abbreviation():
    am = _csv("sdvplotr_abbr_mapping.csv")
    agree, has, gaps, wrong = 0, 0, set(), []
    for lg in sorted(set(am["sport"])):
        sub = am.filter(pl.col("sport") == lg)
        got, want = sdvplot.resolve(sub["key"], lg).to_list(), sdvplot.resolve(sub["canon"], lg).to_list()
        for key, g, w in zip(sub["key"], got, want, strict=True):
            if w is None:  # a conference, or a team sdvplot has no abbreviation for
                continue
            has += 1
            if g == w:
                agree += 1
            elif g is None:
                gaps.add((lg, key))
            else:
                wrong.append((lg, key, g, w))
    assert wrong == []
    assert gaps <= KNOWN_GAPS, sorted(gaps - KNOWN_GAPS)
    assert agree / has >= 0.99


# A relocation key another team holds today. sdvplotR follows the franchise (WIN, the original Jets, gives Utah);
# sdvplot gives the code's current holder unless a season says otherwise (the KCA / WAS rule, #89,
# tests/test_real_index.py), so the two agree only for a season of the original team's. A new such key fails the test.
REUSED_RELOCATION_KEYS = {("nhl", "WIN"): 1990}


def test_historical_keys_resolve_to_the_franchise_today():
    am = {(r["sport"], r["key"]): r["canon"] for r in _csv("sdvplotr_abbr_mapping.csv").iter_rows(named=True)}
    for r in _csv("sdvplotr_historical.csv").iter_rows(named=True):
        lg, key = r["sport"], r["key"]
        # match_team_abbrs() since sdvplotR #55: the relocation table first, then its target through abbr_mapping
        canon = am.get((lg, r["canon"]), r["canon"])
        season = REUSED_RELOCATION_KEYS.get((lg, key))
        assert sdvplot.resolve(key, lg, season=season) == sdvplot.resolve(canon, lg) is not None, (lg, key, canon)
        if season is not None:  # the documented divergence: without a season, the code means today's holder
            assert sdvplot.resolve(key, lg) != sdvplot.resolve(canon, lg), (lg, key, canon)


def test_team_colors_agree_where_both_hold_a_real_one():  # parity audit 2026-10-05, 4b
    # sdvplotR #63 reads sdvplot's colours for the teams ESPN gives none (its `logo` rows), so those agree by
    # construction; the rest both read from ESPN or nflverse. A secondary ESPN repeats as the primary is null here.
    r = pl.read_csv(Path(__file__).parent / "fixtures" / "sdvplotr_team_colors.csv", infer_schema_length=0)
    py = pl.concat([sdvplot.teams(lg) for lg in sorted(set(r["sport"]))])
    assert r.schema["espn_team_id"] == py.schema["team_id"] == pl.String
    j = r.join(py, left_on=["sport", "espn_team_id"], right_on=["league", "team_id"])
    assert j.height == r.height  # every sdvplotR team is in the index
    both = j.filter(pl.col("color_source").is_not_null() & (pl.col("color_source_right") != "fallback"))
    assert both.height == r.height
    lower = {c: pl.col(c).str.to_lowercase() for c in ("color1", "color2", "color_primary", "color_secondary")}
    differ = both.filter(
        (lower["color1"] != lower["color_primary"])
        | (
            pl.col("color2").is_not_null()
            & pl.col("color_secondary").is_not_null()
            & (lower["color2"] != lower["color_secondary"])
        )
    )
    assert differ.select("sport", "team_abbr", "color1", "color2", "color_primary", "color_secondary").rows() == []
    assert both.filter(pl.col("color_source") != pl.col("color_source_right")).select("sport", "team_abbr").rows() == []


@pytest.mark.parametrize(
    ("league", "value", "name"),
    [
        *[
            ("nfl", k, n)
            for k, n in [
                ("BLT", "Baltimore Ravens"),
                ("CLV", "Cleveland Browns"),
                ("HST", "Houston Texans"),
                ("ARZ", "Arizona Cardinals"),
                ("JAC", "Jacksonville Jaguars"),
                ("LVR", "Las Vegas Raiders"),
                ("WFT", "Washington Commanders"),
            ]
        ],
        *[
            ("nhl", k, n)
            for k, n in [
                ("NJD", "New Jersey Devils"),
                ("TBL", "Tampa Bay Lightning"),
                ("LAK", "Los Angeles Kings"),
                ("SJS", "San Jose Sharks"),
                ("VEG", "Vegas Golden Knights"),
                ("UTA", "Utah Mammoth"),
            ]
        ],
        ("nba", "SEA", "Oklahoma City Thunder"),
        ("nba", "NJN", "Brooklyn Nets"),
        ("mlb", "MON", "Washington Nationals"),
        ("mlb", "FLA", "Miami Marlins"),
        ("cfb", "San José State", "San José State Spartans"),
        ("cfb", "San Jose State", "San José State Spartans"),
        ("nhl", "Montréal Canadiens", "Montreal Canadiens"),
    ],
)
def test_named_examples(league, value, name):
    team_id = sdvplot.resolve(value, league)
    assert sdvplot.teams(league).filter(pl.col("team_id") == team_id)["name"].to_list() == [name]


# sdvplotR's season logos (sport, key, season probed) that sdvplot picks differently (final-fix-report.md, F1, R50):
# NHL marks with the same or touching ranges, which the two break differently (two Coyotes marks for 2022-2024,
# KCS/CLR 1977, TSP/TOR 1927, Utah 2025)
LOGO_DIFFERENCES = {
    ("nhl", "ARI", 2022),
    ("nhl", "CGY", 1987),
    ("nhl", "CGY", 2007),
    ("nhl", "DAL", 2017),
    ("nhl", "KCS", 1975),
    ("nhl", "KCS", 1977),
    ("nhl", "MNS", 1988),
    ("nhl", "TOR", 1927),
    ("nhl", "TOR", 1985),
    ("nhl", "TOR", 2002),
    ("nhl", "TSP", 1927),
    ("nhl", "UTA", 2025),
    ("nhl", "UTAH", 2025),
}


@pytest.mark.skipif(os.environ.get("SDVPLOT_LIVE_TESTS") != "1", reason="network: set SDVPLOT_LIVE_TESTS=1")
def test_live_season_logos_match_sdvplotr(tmp_path, monkeypatch):
    from sdvplot import _manifest

    monkeypatch.setenv("SDVPLOT_CACHE_DIR", str(tmp_path))
    _manifest._read.cache_clear()
    lh = pl.read_csv(Path(__file__).parent / "fixtures" / "sdvplotr_logo_history.csv", infer_schema_length=0)
    same, differ = 0, set()
    for r in lh.iter_rows(named=True):
        season = (int(r["season_from"]) + int(r["season_to"])) // 2
        variant = "default" if r["variant"] == "primary" else r["variant"]
        url = sdvplot.logo_url(r["key"], r["sport"], season=season, variant=variant)
        if url == r["url"]:
            same += 1
        elif url is not None:  # None: a defunct club sdvplot does not carry (Montreal Maroons, Charlotte Sting)
            differ.add((r["sport"], r["key"], season))
    assert differ <= LOGO_DIFFERENCES, sorted(differ - LOGO_DIFFERENCES)
    assert same >= 327  # of 401 at R50


@pytest.mark.skipif(os.environ.get("SDVPLOT_LIVE_TESTS") != "1", reason="network: set SDVPLOT_LIVE_TESTS=1")
def test_live_coyotes_era_logos(tmp_path, monkeypatch):  # R50
    from sdvplot import _manifest
    from sdvplot._marks import select_mark

    monkeypatch.setenv("SDVPLOT_CACHE_DIR", str(tmp_path))
    _manifest._read.cache_clear()
    lh = pl.read_csv(Path(__file__).parent / "fixtures" / "sdvplotr_logo_history.csv", infer_schema_length=0)
    ari = lh.filter((pl.col("key") == "ARI") & (pl.col("season_from") == "2015") & (pl.col("variant") == "primary"))
    assert sdvplot.logo_url("ARI", "nhl", season=2017) == ari["url"].item()  # sdvplotR's Coyotes mark
    current = select_mark("UTA", "nhl")  # no season: Utah's current mark, not a Coyotes one
    assert (current["source"], current["entity_id"], current["valid_to"]) == ("espn", "129764", None)

"""Pins against the SHIPPED index (R46): a data refresh that drops a join or a curated row fails here. No network,
except the gated live test at the end."""

import os
import warnings
from pathlib import Path

import polars as pl
import pytest

import sdvplot
from sdvplot import _index
from sdvplot._resolve import EXPLICIT_ONLY, PRIORITY

pytestmark = pytest.mark.real_index


def test_this_module_reads_the_shipped_index():
    assert _index.index_version() != "fixture" and sdvplot.teams().height > 5000


def test_the_readme_and_get_started_examples():
    assert sdvplot.resolve(["LV", "OAK", "Las Vegas Raiders"], "nfl") == ["13", "13", "13"]
    assert sdvplot.palette("nfl", teams=["LV", "KC"]) == {"LV": "#000000", "KC": "#e31837"}
    # logo_url("OAK", season=2010) picks the Oakland mark through its dated mark alias
    oak = _index.alias_table().filter((pl.col("id_system") == "mark") & (pl.col("value") == "espn:OAK"))
    assert oak.select("team_id", "valid_from", "valid_to").rows() == [("13", 1960, 2019)]


def test_palette_never_merges_teams_that_share_an_abbreviation():  # KSU: Kansas State (264), Kennesaw State (307)
    with pytest.warns(sdvplot.SdvplotWarning, match="KSU, LIN, PAC") as w:
        p = sdvplot.palette("ncaa_baseball")
    assert len(w) == 1
    assert len(p) == sdvplot.teams("ncaa_baseball")["color_primary"].is_not_null().sum()
    assert "KSU" not in p and p["264"] == "#633194" and p["307"] == "#bab0ac"


@pytest.mark.parametrize("id_system", PRIORITY + EXPLICIT_ONLY)
def test_every_id_system_has_aliases(id_system):  # build_index skips an empty or missing source silently
    assert _index.alias_table().filter(pl.col("id_system") == id_system).height > 0


@pytest.mark.parametrize(
    ("code", "season", "team"),
    [
        ("OAK", None, "13"),
        ("OAK", 2010, "13"),
        ("OAK", 1975, "13"),
        ("LV", 2020, "13"),
        ("SD", None, "24"),
        ("SD", 2010, "24"),
        ("LAC", 2020, "24"),
        ("STL", None, "14"),
        ("STL", 2010, "14"),
        ("LA", 2020, "14"),
        ("LA", None, "14"),
    ],
)
def test_nfl_relocation_codes_with_and_without_seasons(code, season, team):
    assert sdvplot.resolve(code, "nfl", season=season) == team


@pytest.mark.parametrize(("code", "team"), [("KCR", "7"), ("TBR", "30"), ("SDP", "25"), ("SFG", "26"), ("WSN", "20")])
def test_fangraphs_codes(code, team):
    assert sdvplot.resolve(code, "mlb", id_system="fangraphs") == sdvplot.resolve(code, "mlb") == team


@pytest.mark.parametrize(("code", "team"), [("KCR", "7"), ("TBR", "30")])
def test_baseball_reference_codes(code, team):
    assert sdvplot.resolve(code, "mlb", id_system="bref") == team


@pytest.mark.parametrize(
    ("code", "season", "team"),
    [
        ("KCA", 1960, "11"),  # the Kansas City Athletics (1955-67): the Athletics, in every season
        ("KCA", 1990, "11"),
        ("KCA", None, "11"),
        ("PHA", 1930, "11"),  # the Philadelphia Athletics (1901-54)
        ("PHA", None, "11"),
        ("BSN", 1948, "15"),  # the Boston Braves
        ("MLN", 1957, "15"),  # the Milwaukee Braves (Baseball-Reference)
        ("BRO", 1955, "19"),  # the Brooklyn Dodgers
        ("NYG", 1954, "26"),  # the New York Giants
        ("SEP", 1969, "8"),  # the Seattle Pilots: the Brewers
        ("SLB", 1944, "1"),  # the St. Louis Browns: the Orioles
        ("MLA", 1901, "1"),  # the 1901 Milwaukee Brewers: the Orioles too, not today's Brewers
        ("WS1", 1924, "9"),  # the Senators who became the Twins (an MLB Stats API teamCode)
        ("WS2", 1965, "13"),  # ... and the ones who became the Rangers
        ("WAS", 1924, "9"),
        ("WAS", 1965, "13"),
        ("WSA", 1965, "13"),
        ("MON", 1994, "20"),
        ("CAL", 1980, "3"),
        ("ANA", 2002, "3"),
        ("FLA", 2003, "28"),
        ("TBD", 2005, "30"),
        ("OAK", 1990, "11"),
        ("MIL", 1960, "15"),  # today's ESPN codes another franchise held first: the Milwaukee Braves
        ("MIL", 1901, "1"),
        ("MIL", 1990, "8"),
        ("MIL", None, "8"),
        ("SEA", 1969, "8"),  # the Seattle Pilots
        ("SEA", None, "12"),
        ("WSH", 1950, "9"),  # Baseball-Reference's first Senators
        ("WSH", 2010, "20"),
    ],
)
def test_mlb_historical_codes_reach_their_franchise(code, season, team):
    assert sdvplot.resolve(code, "mlb", season=season) == team


def test_no_mlb_id_system_gives_kca_to_the_royals():  # the Royals' teamCode is "kca"; sdvplotR maps KCA to KC
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", sdvplot.SdvplotWarning)
        got = {s: sdvplot.resolve("KCA", "mlb", season=1990, id_system=s) for s in PRIORITY}
    assert "7" not in got.values() and got["mlbstats"] == got["bref"] == "11"


def test_baseball_reference_codes_go_to_the_franchise_not_a_namesake():
    assert sdvplot.resolve("MLA", "mlb", id_system="bref") == "1"  # was today's Brewers (8) by name
    assert sdvplot.resolve("WSH", "mlb", season=1950, id_system="bref") == "9"  # Baseball-Reference's first Senators


def test_an_mlb_code_two_franchises_used_needs_a_season():
    with pytest.warns(sdvplot.SdvplotWarning, match="WAS"):
        assert sdvplot.resolve("WAS", "mlb") is None  # the Senators of 1901-60 and of 1961-71


def test_cfbd_school_names():
    assert sdvplot.resolve(["Alabama", "Miami (OH)"], "cfb", id_system="cfbd") == ["333", "193"]
    assert sdvplot.resolve(["Alabama", "Miami (OH)"], "cfb") == ["333", "193"]


def test_nba_api_ids():
    assert sdvplot.resolve([1610612747, "1610612747"], "nba") == ["13", "13"]  # the Lakers
    assert sdvplot.resolve(1610612747, "nba", id_system="nba_api") == "13"


@pytest.mark.skipif(os.environ.get("SDVPLOT_LIVE_TESTS") != "1", reason="network: set SDVPLOT_LIVE_TESTS=1")
def test_live_readme_logo_examples(tmp_path, monkeypatch):
    from sdvplot import _manifest

    monkeypatch.setenv("SDVPLOT_CACHE_DIR", str(tmp_path))
    _manifest._read.cache_clear()
    oak = sdvplot.marks("OAK", "nfl", 2010)  # the README's "Oakland-era mark"
    assert sdvplot.logo_url("OAK", "nfl", season=2010) == oak.filter(oak["entity_id"] == "OAK")["archive_url"][0]
    assert max(sdvplot.logo_image("LV", "nfl", size=128).size) == 128


def test_wnba_san_antonio_codes_carry_their_own_eras():  # M6: sdvplotR's Silver Stars / Stars eras
    a = _index.alias_table().filter(
        (pl.col("league") == "wnba")
        & pl.col("id_system").is_in(["espn_abbr", "mark"])
        & pl.col("value").is_in(["SAS", "SA", "espn:SAS", "espn:SA"])
    )
    assert sorted(a.select("value", "team_id", "valid_from", "valid_to").rows()) == [
        ("SA", "17", 2014, 2017),
        ("SAS", "17", 2003, 2013),
        ("espn:SA", "17", 2014, 2017),
        ("espn:SAS", "17", 2003, 2013),
    ]


def test_nhl_stats_ids_answer_only_when_named():  # R49: NHL ids 1-28 are other teams' ESPN ids
    with pytest.warns(sdvplot.SdvplotWarning, match="'24'"):
        assert sdvplot.resolve(24, "nhl") is None  # ESPN 24, the inactive Coyotes: never Anaheim (NHL id 24)
    with pytest.warns(sdvplot.SdvplotWarning):
        assert sdvplot.resolve([1, 6, 52, 55], "nhl") == ["1", "6", None, None]  # ESPN ids, as before R43
    assert sdvplot.resolve(1, "nhl", id_system="nhl_id") == "11"  # NHL id 1: the Devils
    assert sdvplot.resolve([1, 6, 52, 55], "nhl", id_system="nhl_id") == ["11", "1", "28", "124292"]
    assert sdvplot.resolve("NJD", "nhl") == "11"  # tri-codes stay under auto


def test_coyotes_marks_reach_utah_with_their_own_ranges():  # R50
    m = _index.alias_table().filter((pl.col("id_system") == "mark") & pl.col("value").is_in(["nhl:27", "nhl:53"]))
    assert sorted(m.select("value", "team_id", "valid_from", "valid_to").rows()) == [
        ("nhl:27", "129764", None, None),
        ("nhl:53", "129764", None, None),
    ]


@pytest.mark.parametrize(
    ("league", "codes", "ids"),
    [
        ("ncaa_baseball", ["NCSU", "MIZ", "UCR", "KENN"], ["95", "91", "67", "307"]),
        ("ncaa_softball", ["AF", "UPST", "WGA", "QUC"], ["567", "807", "129696", "1254"]),
    ],
)
def test_espn_college_abbreviations_from_the_team_endpoint(league, codes, ids):  # the teams list says NCST, MIZZ, ...
    assert sdvplot.resolve(codes, league) == ids


def test_espn_team_endpoint_abbreviations_never_name_another_team():
    """Every abbreviation of data-raw/espn_abbrs.csv resolves to its team, or to the team ESPN's teams list gives it
    (the per-team endpoint calls LSU Alexandria "LSU"), or to None where ESPN gives it to several teams."""
    raw = pl.read_csv(Path(__file__).parents[1] / "data-raw" / "espn_abbrs.csv", infer_schema_length=0)
    listed = pl.read_csv(Path(__file__).parents[1] / "data-raw" / "espn_teams.csv", infer_schema_length=0)
    for (league,), rows in raw.group_by("league"):
        holder = {
            (r["abbreviation"] or "").upper(): r["team_id"]
            for r in listed.filter(pl.col("league") == league).iter_rows(named=True)
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", sdvplot.SdvplotWarning)
            got = sdvplot.resolve(rows["abbreviation"], league)
        for r, g in zip(rows.iter_rows(named=True), got, strict=True):
            assert g in (r["team_id"], holder.get(r["abbreviation"].upper()), None), (league, r, g)


@pytest.mark.parametrize(
    ("league", "code", "season", "team"),
    [
        ("ufl", "BIR", 2024, "126073"),  # the 2024-25 codes, from ESPN's scoreboards (its teams list is 2026's)
        ("ufl", "ARL", 2025, "112647"),
        ("ufl", "MEM", 2024, "129043"),
        ("ufl", "MIC", 2025, "125957"),
        ("ufl", "SA", 2024, "126746"),
        ("ufl", "HOU", 2024, "126075"),
        ("ufl", "Houston Roughnecks", 2025, "126075"),
        ("xfl", "DC", 2020, "112646"),
        ("xfl", "DAL", 2020, "112647"),
        ("xfl", "ARL", 2023, "112647"),
        ("xfl", "HOU", 2023, "112648"),
        ("xfl", "LA", 2020, "112649"),
        ("xfl", "NY", 2020, "112650"),
        ("xfl", "STL", 2023, "112651"),
        ("xfl", "SEA", 2020, "112652"),
        ("xfl", "TB", 2020, "112653"),
        ("xfl", "SA", 2023, "126746"),
        ("xfl", "VGS", 2023, "126747"),
        ("xfl", "ORL", 2023, "126748"),
    ],
)
def test_ufl_and_xfl_season_codes(league, code, season, team):
    assert sdvplot.resolve(code, league, season=season) == team


def test_ufl_season_codes_carry_their_seasons():
    a = _index.alias_table().filter(
        (pl.col("league") == "ufl") & (pl.col("id_system") == "espn_abbr") & (pl.col("value") == "ARL")
    )
    assert a.select("team_id", "valid_from", "valid_to").rows() == [("112647", 2024, 2025)]

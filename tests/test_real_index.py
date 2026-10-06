"""Pins against the SHIPPED index (R46): a data refresh that drops a join or a curated row fails here. No network,
except the gated live test at the end."""

import os
import re
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
    assert "KSU" not in p and p["264"] == "#633194" and p["307"] == "#fdbb30"  # 307: the school's ESPN gold, by name


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
        ("KCA", 1960, "11"),  # the Kansas City Athletics (1955-67): the Athletics
        ("KCA", 1990, "7"),  # from 1968 the Royals' (MLB Stats teamCode, Lahman, sdvplotR)
        ("KCA", 2025, "7"),
        ("KCA", None, "7"),  # no season: the code's current holder
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
        ("WAS", 1950, "9"),  # the Senators who became the Twins
        ("WAS", 1965, "13"),  # the Senators who became the Rangers
        ("WAS", 2024, "20"),  # from 2005 the Nationals (MLB Stats teamCode "was", Lahman, sdvplotR)
        ("WAS", None, "20"),
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


def test_mlb_stats_codes_carry_the_seasons_the_api_used_them():  # the Royals' teamCode is "kca" from 1968
    assert sdvplot.resolve("KCA", "mlb", season=1960, id_system="mlbstats") == "11"
    assert sdvplot.resolve("KCA", "mlb", season=1990, id_system="mlbstats") == "7"
    assert sdvplot.resolve("WAS", "mlb", season=2010, id_system="mlbstats") == "20"


def test_baseball_reference_codes_go_to_the_franchise_not_a_namesake():
    assert sdvplot.resolve("MLA", "mlb", id_system="bref") == "1"  # was today's Brewers (8) by name
    assert sdvplot.resolve("WSH", "mlb", season=1950, id_system="bref") == "9"  # Baseball-Reference's first Senators


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
    oak = sdvplot.marks("OAK", "nfl", season=2010)  # the README's "Oakland-era mark"
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


# The NHL stats API files the original Jets (team 33, WIN, 1979-80 to 1995-96) under today's Jets' franchise. The team
# that played those seasons became the Coyotes (1996) and its line is Utah's, as sdvplotR's resolve_historical_abbr()
# says; today's Jets are the relocated Thrashers (2011-12 on). Seasons are the year they end, as everywhere in the index.
@pytest.mark.parametrize(
    ("value", "id_system", "season", "team"),
    [
        ("WIN", "auto", 1980, "129764"),  # the original Jets' first season: Utah's line
        ("WIN", "auto", 1990, "129764"),
        ("WIN", "auto", 1996, "129764"),  # their last
        ("WIN", "auto", 2012, "28"),  # today's Jets' first season
        ("WIN", "auto", 2015, "28"),
        ("WIN", "auto", None, "28"),  # no season: the code's current holder (the KCA / WAS rule)
        ("WPG", "auto", 1990, "28"),  # today's code is never the original Jets'
        ("33", "nhl_id", 1990, "129764"),  # the NHL's team id for the original Jets, dated the same way
        ("33", "nhl_id", 2015, "28"),
        ("33", "nhl_id", None, "28"),
    ],
)
def test_the_original_winnipeg_jets_resolve_by_season(value, id_system, season, team):
    assert sdvplot.resolve(value, "nhl", season=season, id_system=id_system) == team


def test_the_original_jets_marks_reach_utah_over_their_seasons():  # the archive's nhl:33 logos, 1980-1996
    from sdvplot._marks import select_mark

    m = _index.alias_table().filter((pl.col("id_system") == "mark") & (pl.col("value") == "nhl:33"))
    assert m.select("team_id", "valid_from", "valid_to").rows() == [("129764", 1980, 1996)]
    assert select_mark("WIN", "nhl", 1985)["entity_id"] == "33"
    assert select_mark("WPG", "nhl", 2020)["entity_id"] != "33"


@pytest.mark.parametrize("value", ["UTRGV", "TEXAS-RIO GRANDE VALLEY", "UT Rio Grande Valley", "RGV"])
def test_utrgv_resolves_in_college_football(value):  # ESPN's cfb teams list omits 292; its per-team endpoint says RGV
    assert sdvplot.resolve(value, "cfb") == "292"


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


def test_utah_marks_split_at_the_mammoth():  # NHL seasons are end years: 2025 is 2024-25
    a = _index.alias_table().filter(
        (pl.col("league") == "nhl") & (pl.col("id_system") == "mark") & pl.col("value").is_in(["nhl:59", "nhl:68"])
    )
    assert sorted(a.select("value", "team_id", "valid_from", "valid_to").rows()) == [
        ("nhl:59", "129764", None, None),  # the Utah Hockey Club's marks keep the archive's 2025-2025
        ("nhl:68", "129764", 2026, None),  # the Utah Mammoth's start in 2025-26, not 2024-25 as the NHL dates them
    ]


@pytest.mark.skipif(os.environ.get("SDVPLOT_LIVE_TESTS") != "1", reason="network: set SDVPLOT_LIVE_TESTS=1")
def test_live_utah_logo_by_season(tmp_path, monkeypatch):
    from sdvplot import _manifest
    from sdvplot._marks import select_mark

    monkeypatch.setenv("SDVPLOT_CACHE_DIR", str(tmp_path))
    _manifest._read.cache_clear()
    for variant in ("default", "dark"):
        assert select_mark("UTA", "nhl", 2025, variant)["entity_id"] == "59"  # the Utah Hockey Club, 2024-25
        assert select_mark("UTA", "nhl", 2026, variant)["entity_id"] == "68"  # the Utah Mammoth, 2025-26 on


def test_womens_college_hockey_ids_espn_game_data_uses():  # ESPN scoreboards use ids its teams list lacks
    assert sdvplot.resolve(["24059", 24059, "2364"], "ncaa_whockey") == ["2364"] * 3  # Minnesota State's second id
    assert sdvplot.resolve(["48", "DEL", "Delaware Blue Hens"], "ncaa_whockey") == ["48"] * 3
    delaware = sdvplot.teams("ncaa_whockey").filter(pl.col("team_id") == "48").row(0, named=True)
    assert (delaware["name"], delaware["abbr"]) == ("Delaware Blue Hens", "DEL")
    marks = _index.alias_table().filter(
        (pl.col("league") == "ncaa_whockey") & (pl.col("id_system") == "mark") & (pl.col("team_id") == "48")
    )
    assert marks.height == 0  # the archive has no Delaware mark, and none is made up


def test_mens_college_hockey_ids_espn_game_data_uses():  # SUNY Morrisville and Maryville play listed teams
    assert sdvplot.resolve(["126813", "132633"], "ncaa_mhockey") == ["126813", "132633"]
    assert sdvplot.resolve("Maryville (Mo) Saints", "ncaa_mhockey") == "132633"
    assert sdvplot.resolve("SUNY Morrisville Mustangs", "ncaa_mhockey") == "126813"  # ESPN-listed, not archived


# Team colors by source, measured on the October 2026 snapshots: (published, i.e. nflverse or ESPN; logo-derived) per
# league. A refresh that loses a source's rows fails here.
COLOR_FLOORS = {
    "aaf": (0, 8), "ahl": (0, 61), "cfb": (383, 304), "cricket": (0, 111), "echl": (0, 59), "mbb": (356, 10),
    "milb": (0, 286), "mlb": (30, 0), "nba": (30, 0), "nbagl": (29, 3), "ncaa_baseball": (370, 44),
    "ncaa_mhockey": (53, 55), "ncaa_softball": (358, 57), "ncaa_whockey": (30, 18), "nfl": (32, 0), "nhl": (32, 0),
    "ohl": (0, 27), "phf": (0, 8), "pwhl": (0, 12), "qmjhl": (0, 30), "soccer": (2125, 506), "ufl": (11, 0),
    "usfl": (0, 9), "ushl": (0, 17), "wbb": (354, 10), "whl": (0, 23), "wnba": (15, 0), "xfl": (7, 4),
}  # fmt: skip


def test_colors_are_hex_and_a_secondary_is_a_second_color():
    t = sdvplot.teams()
    assert set(t["color_source"]) == {"nflverse", "espn", "logo", "fallback"}
    assert t["color_primary"].str.contains(r"^#[0-9a-f]{6}$").all()
    assert t["color_secondary"].drop_nulls().str.contains(r"^#[0-9a-f]{6}$").all()
    assert t.filter(pl.col("color_secondary") == pl.col("color_primary")).height == 0


@pytest.mark.parametrize("league", sorted(COLOR_FLOORS))
def test_color_coverage_per_league(league):
    published, logo = COLOR_FLOORS[league]
    source = sdvplot.teams(league)["color_source"]
    assert source.is_in(["nflverse", "espn"]).sum() >= published
    assert (source != "fallback").sum() >= published + logo


def test_a_fallback_color_only_where_no_source_has_one():
    # two scoreboard-only teams: no archived logo, and ESPN gives their ids no color in any sport
    fallback = sdvplot.teams().filter(pl.col("color_source") == "fallback")
    assert fallback.select("league", "team_id").rows() == [("ncaa_mhockey", "126813"), ("ncaa_mhockey", "132633")]


@pytest.mark.parametrize(
    ("league", "team", "colors"),
    [
        ("soccer", "10", ("#c60000", "#000000", "espn")),  # Huracán, from ESPN's per-team endpoint
        ("ncaa_mhockey", "103", ("#8c2232", "#dbcca6", "espn")),  # Boston College: its school id in basketball
        ("ncaa_baseball", "102", ("#ce0e2d", "#ffffff", "espn")),  # Rutgers: baseball's list says black; by name
        ("soccer", "10207", ("#c92639", "#cda922", "logo")),  # Al Ahly: ESPN's stand-in black and red
        ("cfb", "2097", ("#ff4713", "#2e1811", "logo")),  # Campbell: ESPN's black alone in every sport
        ("ohl", "7", ("#fcb721", "#1e242f", "logo")),  # Barrie Colts: HockeyTech publishes no colors
    ],
)
def test_colors_by_source(league, team, colors):
    row = sdvplot.teams(league).filter(pl.col("team_id") == team)
    assert row.select("color_primary", "color_secondary", "color_source").row(0) == colors


def test_espn_colors_from_another_sport_come_only_from_school_keyed_leagues():
    # college baseball and softball number their own teams: an id there is not the school's id in football
    ec = pl.read_csv(Path(__file__).parents[1] / "data-raw" / "espn_colors.csv", infer_schema_length=0)
    cross = ec.filter(pl.col("league") != pl.col("espn_league"))
    school = {"cfb", "mbb", "wbb", "ncaa_mhockey", "ncaa_whockey"}
    assert cross.height > 0 and set(cross["league"]) <= school and set(cross["espn_league"]) <= school


def test_logo_colors_agree_with_published_ones_where_both_exist():
    """The logo method, measured where a team also has published colors: its primary is within RGB distance 60 of
    one of them for 68% of 4,214 teams, and 94% of the 139 in the five big leagues (ESPN's small-college and soccer
    colors are often a shade the logo does not use)."""
    logo = pl.read_csv(Path(__file__).parents[1] / "data-raw" / "logo_colors.csv", infer_schema_length=0)
    both = (
        sdvplot.teams().filter(pl.col("color_source").is_in(["nflverse", "espn"])).join(logo, on=["league", "team_id"])
    )

    def rgb(c):
        return [int(c[i : i + 2], 16) for i in (1, 3, 5)]

    def near(a, b):
        return b is not None and sum((x - y) ** 2 for x, y in zip(rgb(a), rgb(b), strict=True)) < 60**2

    ok = pl.Series([near(r["primary"], r["color_primary"]) or near(r["primary"], r["color_secondary"])
                    for r in both.iter_rows(named=True)])  # fmt: skip
    big = both["league"].is_in(["nfl", "nba", "mlb", "nhl", "wnba"])
    assert both.height >= 4200 and ok.mean() >= 0.67 and ok.filter(big).mean() >= 0.94


def test_team_colors_and_palette_read_nhl_stats_ids_when_named():  # S11: once wrong colors, silently
    devils_bruins_leafs = sdvplot.team_colors("nhl", ["NJD", "BOS", "TOR"])
    assert sdvplot.team_colors("nhl", [1, 6, 10], id_system="nhl_id") == devils_bruins_leafs
    assert sdvplot.palette("nhl", [1, 6, 10], id_system="nhl_id") == dict(
        zip([1, 6, 10], devils_bruins_leafs, strict=True)
    )
    assert sdvplot.team_colors("nhl", [1, 6, 10]) != devils_bruins_leafs  # "auto" reads them as ESPN ids


def test_the_plotnine_scales_and_pygal_style_read_nhl_stats_ids_when_named():  # re-audit F1
    pytest.importorskip("plotnine")
    pytest.importorskip("pygal")
    from sdvplot.plotnine import scale_color_sdv, scale_fill_sdv
    from sdvplot.pygal import team_style

    devils_bruins_leafs = sdvplot.team_colors("nhl", ["NJD", "BOS", "TOR"])
    ids = ["1", "6", "10"]
    for scale in (scale_color_sdv, scale_fill_sdv):
        assert scale("nhl", id_system="nhl_id").map(ids, limits=ids) == devils_bruins_leafs
        with pytest.raises(TypeError):  # which is keyword-only, as in palette() and team_colors()
            scale("nhl", "secondary")
    assert list(team_style(ids, league="nhl", id_system="nhl_id").colors[:3]) == devils_bruins_leafs
    with pytest.raises(sdvplot.UnresolvedTeamError):
        team_style(["NOPE"], league="nhl", strict=True)


def test_merge_stack_keeps_missouris_gold_readable_as_sdvplotr_does():  # sdvplotR #55's test, on the shipped index
    pytest.importorskip("great_tables")
    from great_tables import GT

    from sdvplot._contrast import contrast
    from sdvplot.great_tables import gt_merge_stack_team_color, gt_theme_midnight, gt_theme_terminal

    def inks(gt):
        return re.findall(r"font-weight:bold;color:(#[0-9a-fA-F]{6});font-size:12px", gt.as_raw_html())

    df = pl.DataFrame({"team": ["MIZ", "WVU"], "mascot": ["Tigers", "Mountaineers"]})
    # Missouri's gold primary measures 1.8:1 on white; its black secondary passes
    light = inks(gt_merge_stack_team_color(GT(df), "team", "mascot", "team", league="cfb"))
    assert light[0] == sdvplot.team_colors("cfb", "MIZ", which="secondary") == "#000000"
    assert light[1] == sdvplot.team_colors("cfb", "WVU", which="secondary") == "#002855"
    # on a dark table the golds pass and stay
    dark = gt_merge_stack_team_color(GT(df), "team", "mascot", "team", league="cfb", background="#1e1e1e")
    assert inks(dark) == ["#f1b82d", "#eaaa00"] == sdvplot.team_colors("cfb", ["MIZ", "WVU"])
    # a theme applied first sets the background the ink is checked against
    for theme in (gt_theme_midnight, gt_theme_terminal):
        tbl = theme(GT(df))
        bg = str(tbl._options.table_background_color.value)
        got = inks(gt_merge_stack_team_color(tbl, "team", "mascot", "team", league="cfb"))
        assert got == ["#f1b82d", "#eaaa00"] and all(contrast(i, bg) >= 4.5 for i in got)


RAW = Path(__file__).parents[1] / "data-raw"


# sdvplotR's include_conferences (parity audit gap #2): 89 college conferences plus the AFC, NFC and NFL
def test_conference_rows_are_sdvplotrs_opt_in_and_never_teams():
    everything = sdvplot.teams(include_conferences=True)
    conf = everything.filter(pl.col("program").is_in(_index.NON_TEAM))
    assert conf.group_by("league").len().sort("league").rows() == [("cfb", 25), ("mbb", 32), ("nfl", 3), ("wbb", 32)]
    assert conf.filter(pl.col("program") == "league")["abbr"].to_list() == ["NFL"]
    assert sdvplot.teams().height + conf.height == everything.height and sdvplot.teams("cfb").height == 687
    assert not sdvplot.teams()["program"].is_in(_index.NON_TEAM).any()
    # the id is R's key (the short name), never a team id; a team's conference_id is its conference row's
    assert conf["team_id"].str.contains(r"^[0-9]+$").sum() == 0 and (conf["team_id"] == conf["abbr"]).all()
    sec = conf.filter((pl.col("league") == "cfb") & (pl.col("abbr") == "SEC")).row(0, named=True)
    assert sec["conference_id"] == "cfb:sec" and sec["conference"] == "Southeastern Conference"
    assert sdvplot.teams("cfb").filter(pl.col("conference_id") == "cfb:sec").height == 16
    retired = conf.filter((pl.col("program") == "conference") & pl.col("conference_id").is_null())
    assert retired.select("league", "abbr").rows() == [("cfb", "WAC"), ("mbb", "WAC"), ("wbb", "WAC")]  # ESPN: UAC now
    # opt-in everywhere: no alias, so no resolution and no palette key; cfb's MAC is still Macalester
    assert _index.alias_table().join(conf.select("league", "team_id"), on=["league", "team_id"], how="semi").height == 0
    with pytest.warns(sdvplot.SdvplotWarning, match="'SEC'"):
        assert sdvplot.resolve("SEC", "cfb") is None
    assert sdvplot.resolve("MAC", "cfb") == "2359" and "SEC" not in sdvplot.palette("cfb")
    assert set(everything["color_source"]) == {"nflverse", "espn", "logo", "cbbplotR", "fallback"}
    assert everything["color_primary"].str.contains(r"^#[0-9a-f]{6}$").all()
    assert everything.filter(pl.col("color_secondary") == pl.col("color_primary")).height == 0


def test_conference_colors_are_the_sdvplotr_snapshots_cbbplotr_values():
    r = pl.read_csv(RAW / "sdvplotr_conferences.csv", infer_schema_length=0).select(
        pl.col("sport").alias("league"), pl.col("team_abbr").alias("team_id"), pl.col("type").alias("r_type"),
        pl.col("color1").str.to_lowercase().alias("r1"), pl.col("color2").str.to_lowercase().alias("r2"),
    )  # fmt: skip
    conf = sdvplot.teams(include_conferences=True).filter(pl.col("program").is_in(_index.NON_TEAM))
    j = conf.join(r, on=["league", "team_id"], how="inner")
    assert j.height == conf.height == 92 and (j["program"] == j["r_type"]).all()
    colored = j.filter(pl.col("r1").is_not_null())
    assert colored.height == 85 and (colored["color_source"] == "cbbplotR").all()
    assert (colored["color_primary"] == colored["r1"]).all()
    assert (colored["color_secondary"] == colored.select(pl.when(pl.col("r2") != pl.col("r1")).then("r2"))["r2"]).all()
    none = j.filter(pl.col("r1").is_null())  # the AFC, NFC, NFL, the independents, the MVFC and the Pioneer
    assert none.height == 7 and (none["color_source"] == "fallback").all() and none["color_primary"].is_not_null().all()

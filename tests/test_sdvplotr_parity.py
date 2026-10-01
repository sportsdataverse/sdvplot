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
    ("mlb", "CHICAGO"), ("mlb", "LOS ANGELES"), ("mlb", "NEW YORK"),
    ("nfl", "LOS ANGELES"), ("nfl", "NEW YORK"), ("nhl", "NEW YORK"),
    ("cfb", "CHARLOTTE"),  # CFBD names two teams "Charlotte", and cfbd decides before sdvplotr
    # ESPN's teams list has no UTRGV, so its abbreviation names no team in sdvplot
    ("cfb", "UTRGV"), ("cfb", "TEXAS-RIO GRANDE VALLEY"),
}


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


def test_historical_keys_resolve_to_the_franchise_today():
    am = {(r["sport"], r["key"]): r["canon"] for r in _csv("sdvplotr_abbr_mapping.csv").iter_rows(named=True)}
    for r in _csv("sdvplotr_historical.csv").iter_rows(named=True):
        lg, key = r["sport"], r["key"]
        canon = am.get((lg, key)) or am.get((lg, r["canon"]), r["canon"])  # sdvplotR's two passes
        assert sdvplot.resolve(key, lg) == sdvplot.resolve(canon, lg) is not None, (lg, key, canon)


@pytest.mark.parametrize(
    ("league", "value", "name"),
    [
        *[("nfl", k, n) for k, n in [("BLT", "Baltimore Ravens"), ("CLV", "Cleveland Browns"), ("HST", "Houston Texans"),
                                     ("ARZ", "Arizona Cardinals"), ("JAC", "Jacksonville Jaguars"),
                                     ("LVR", "Las Vegas Raiders"), ("WFT", "Washington Commanders")]],
        *[("nhl", k, n) for k, n in [("NJD", "New Jersey Devils"), ("TBL", "Tampa Bay Lightning"),
                                     ("LAK", "Los Angeles Kings"), ("SJS", "San Jose Sharks"),
                                     ("VEG", "Vegas Golden Knights"), ("UTA", "Utah Mammoth")]],
        ("nba", "SEA", "Oklahoma City Thunder"), ("nba", "NJN", "Brooklyn Nets"),
        ("mlb", "MON", "Washington Nationals"), ("mlb", "FLA", "Miami Marlins"),
        ("cfb", "San José State", "San José State Spartans"), ("cfb", "San Jose State", "San José State Spartans"),
        ("nhl", "Montréal Canadiens", "Montreal Canadiens"),
    ],
)
def test_named_examples(league, value, name):
    team_id = sdvplot.resolve(value, league)
    assert sdvplot.teams(league).filter(pl.col("team_id") == team_id)["name"].to_list() == [name]


def test_nhl_api_ids_need_their_id_system():
    # NHL stats API id 1 is the Devils; "auto" reads a bare number as the ESPN id first (1 = Boston)
    assert sdvplot.resolve(1, "nhl", id_system="nhl") == sdvplot.resolve("NJD", "nhl") == "11"
    assert sdvplot.resolve(1, "nhl") == "1"


# sdvplotR's season logos that sdvplot picks differently (final-fix-report.md, F1): the Coyotes' codes resolve to
# Utah, whose marks sdvplot shows (the NHL franchise has no ESPN team, so no Coyotes mark maps); the others are NHL
# marks with the same or touching ranges (KCS/CLR 1977, TSP/TOR 1927, Utah 2025), which the two break differently
LOGO_DIFFERENCES = {
    ("nhl", k) for k in ("ARI", "PHX", "CGY", "DAL", "KCS", "MNS", "TOR", "TSP", "UTA", "UTAH")
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
            differ.add((r["sport"], r["key"]))
    assert differ <= LOGO_DIFFERENCES, sorted(differ - LOGO_DIFFERENCES)
    assert same >= 317  # of 401 at R43

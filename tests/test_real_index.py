"""Pins against the SHIPPED index (R46): a data refresh that drops a join or a curated row fails here. No network,
except the gated live test at the end."""

import os

import polars as pl
import pytest

import sdvplot
from sdvplot import _index

pytestmark = pytest.mark.real_index


def test_this_module_reads_the_shipped_index():
    assert _index.index_version() != "fixture" and sdvplot.teams().height > 5000


def test_the_readme_and_get_started_examples():
    assert sdvplot.resolve(["LV", "OAK", "Las Vegas Raiders"], "nfl") == ["13", "13", "13"]
    assert sdvplot.palette("nfl", teams=["LV", "KC"]) == {"LV": "#000000", "KC": "#e31837"}
    # logo_url("OAK", season=2010) picks the Oakland mark through its dated mark alias
    oak = _index.alias_table().filter((pl.col("id_system") == "mark") & (pl.col("value") == "espn:OAK"))
    assert oak.select("team_id", "valid_from", "valid_to").rows() == [("13", 1960, 2019)]


@pytest.mark.parametrize(
    ("code", "season", "team"),
    [
        ("OAK", None, "13"), ("OAK", 2010, "13"), ("OAK", 1975, "13"), ("LV", 2020, "13"),
        ("SD", None, "24"), ("SD", 2010, "24"), ("LAC", 2020, "24"),
        ("STL", None, "14"), ("STL", 2010, "14"), ("LA", 2020, "14"), ("LA", None, "14"),
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
    a = _index.alias_table().filter((pl.col("league") == "wnba") & pl.col("value").is_in(["SAS", "SA", "espn:SAS", "espn:SA"]))
    assert sorted(a.select("value", "team_id", "valid_from", "valid_to").rows()) == [
        ("SA", "17", 2014, 2017), ("SAS", "17", 2003, 2013), ("espn:SA", "17", 2014, 2017), ("espn:SAS", "17", 2003, 2013)
    ]

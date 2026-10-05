import polars as pl
import pytest

import sdvplot._index as idx


def test_teams_returns_the_whole_index_or_one_league():
    assert idx.teams().height == 10
    nfl = idx.teams("nfl")
    assert nfl["team_id"].to_list() == ["13", "14", "24"]
    assert nfl.schema["team_id"] == pl.String  # ids are strings, never ints


def test_editing_the_returned_frame_in_place_leaves_the_index_intact():
    idx.teams().drop_in_place("abbr")
    assert "abbr" in idx.teams().columns


def test_alias_ranges_are_int32_and_nullable():
    a = idx.alias_table()
    assert a.schema["valid_from"] == pl.Int32
    assert a.filter(pl.col("value") == "OAK")["valid_to"].to_list() == [2019]


def test_index_version_reads_the_stamp_file():
    assert idx.index_version() == "fixture"


def test_reload_hooks_run_on_reload():
    seen = []
    idx.on_reload(lambda: seen.append(1))
    idx.reload_index()
    assert seen == [1]


@pytest.mark.real_index
def test_the_index_directory_is_looked_up_once(monkeypatch):  # re-audit finding 1: check_league runs per call
    idx.check_league("nfl")

    def fail(*args):
        raise AssertionError("importlib.resources was asked again")

    monkeypatch.setattr(idx.resources, "files", fail)
    idx.check_league("nfl")

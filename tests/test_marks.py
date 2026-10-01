import pandas as pd
import polars as pl
import pytest

from sdvplot import _marks
from sdvplot._errors import SdvplotWarning, UnresolvedTeamError


@pytest.fixture(autouse=True)
def _manifest(manifest):  # the fixture manifest from tests/conftest.py
    return manifest


def test_marks_lists_every_candidate_for_the_team_only():
    m = _marks.marks("LV", "nfl")
    assert set(m["sha256"].str.slice(0, 1)) == {"1", "2", "3", "4"}  # not the conference mark, not the Rams


def test_current_logo_without_a_season():
    assert _marks.logo_url("LV", "nfl") == "https://cdn/1111.png"


def test_season_picks_the_dated_mark():
    assert _marks.logo_url("OAK", "nfl", season=2010) == "https://cdn/3333.png"


def test_a_season_with_no_dated_mark_falls_back_to_the_current_one():
    assert _marks.logo_url("LV", "nfl", season=2024) == "https://cdn/1111.png"


def test_variant_and_mark_type():
    assert _marks.logo_url("LV", "nfl", variant="dark") == "https://cdn/2222.png"
    assert _marks.logo_url("LV", "nfl", mark_type="wordmark") == "https://cdn/4444.png"


def test_a_missing_variant_falls_back_to_default():
    assert _marks.logo_url("LV", "nfl", variant="does-not-exist") == "https://cdn/1111.png"


def test_espn_outranks_a_newer_wayback_copy():
    assert _marks.logo_url("LAR", "nfl") == "https://cdn/6666.png"


def test_no_mark_at_all_returns_none_with_a_warning():
    with pytest.warns(SdvplotWarning, match="no logo"):
        assert _marks.logo_url("LAC", "nfl") is None


def test_marks_is_strict_about_the_team():
    with pytest.raises(UnresolvedTeamError):
        _marks.marks("XXX", "nfl")


@pytest.mark.parametrize("team", [None, float("nan"), "", pd.NA])
def test_marks_of_a_null_team_raises(team):
    with pytest.raises(UnresolvedTeamError, match="needs a team"):
        _marks.marks(team, "nfl")


def test_an_unmapped_foreign_id_row_is_never_returned():
    # nhl source, entity_id "13" collides with ESPN id 13 but has no "mark" alias
    assert "9" * 64 not in set(_marks.marks("LV", "nfl")["sha256"])
    assert _marks.logo_url("LV", "nfl", season=2010) == "https://cdn/3333.png"


def test_the_season_reaches_the_resolver():
    assert _marks.logo_url("LA", "nfl", season=1990) == "https://cdn/3333.png"


def test_an_unknown_team_returns_none_with_the_resolver_warning():
    with pytest.warns(SdvplotWarning) as w:
        assert _marks.logo_url("XXX", "nfl") is None
    assert len(w) == 1
    with pytest.warns(SdvplotWarning):
        assert _marks.select_mark("XXX", "nfl") is None


def test_a_team_with_only_a_non_default_variant_gets_it():
    assert _marks.logo_url("KC", "mlb") == "https://cdn/aaaa.png"


def test_ties_break_on_the_later_valid_from():
    m = _marks.marks("KC", "mlb").filter(pl.col("variant") == "tie")
    assert m["valid_from"].to_list() == [2010, 2000]


def test_a_mark_alias_range_dates_an_open_ended_row():
    # R36: espn:STL and espn:14 are both open-ended espn rows; the STL row's alias ends in 2015
    assert _marks.logo_url("LAR", "nfl") == "https://cdn/6666.png"
    assert _marks.logo_url("LAR", "nfl", season=2010) == "https://cdn/0000.png"
    assert _marks.logo_url("LAR", "nfl", season=2024) == "https://cdn/6666.png"
    stl = _marks.marks("LAR", "nfl").filter(pl.col("entity_id") == "STL").row(0, named=True)
    assert (stl["valid_from"], stl["valid_to"]) == (None, 2015)  # marks() shows the effective range


@pytest.mark.parametrize("fn", ["marks", "select_mark", "logo_url", "logo_image"])
@pytest.mark.parametrize("teams", [["LV", "LAR"], ("LV",), pl.Series(["LV"])])
def test_one_team_functions_reject_several_teams(fn, teams):  # M3
    from sdvplot import _images

    f = getattr(_images if fn == "logo_image" else _marks, fn)
    with pytest.raises(TypeError, match=rf"{fn}\(\) takes one team"):
        f(teams, "nfl")


def test_a_zero_d_numpy_array_is_one_team():  # M3: np.array("LV") must not split into characters
    import numpy as np

    assert _marks.logo_url(np.array("LV"), "nfl") == "https://cdn/1111.png"
    assert _marks.marks(np.array(13), "nfl").height == 4


def test_the_any_variant_fallback_keeps_the_requested_polarity():  # F2 (R44): MLB wordmarks are on_light/on_dark
    # the Chargers' wordmarks: on_dark, on_light and a newer grayscale; no default, no dark
    assert _marks.logo_url("LAC", "nfl", mark_type="wordmark") == "https://cdn/d2.png"  # on_light
    assert _marks.logo_url("LAC", "nfl", variant="dark", mark_type="wordmark") == "https://cdn/d1.png"  # on_dark
    assert _marks.logo_url("LAC", "nfl", variant="grayscale", mark_type="wordmark") == "https://cdn/d3.png"


def test_the_ranked_league_frame_is_built_once_per_manifest_and_index(manifest):  # F3 (R45)
    from sdvplot import _index

    first = _marks._ranked("nfl")
    assert _marks._ranked("nfl") is first  # logo_url per point only filters this frame
    _index.reload_index()
    assert _marks._ranked("nfl") is not first and _marks._ranked("nfl").equals(first)

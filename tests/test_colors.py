import pandas as pd
import pytest

from sdvplot._colors import palette, team_colors
from sdvplot._errors import SdvplotWarning


def test_palette_for_a_whole_league_is_keyed_by_abbreviation():
    assert palette("nfl") == {"LV": "#000000", "LAR": "#003594", "LAC": "#0080c6"}


def test_palette_keys_teams_that_share_an_abbreviation_by_team_id_with_one_warning():  # never guess which KSU
    with pytest.warns(SdvplotWarning, match="shared by several ncaa_baseball teams are keyed by team_id: KSU") as w:
        assert palette("ncaa_baseball") == {"264": "#633194", "307": "#bab0ac"}
    assert len(w) == 1


def test_palette_keys_are_the_callers_own_values_for_seaborn_hue():
    assert palette("nfl", teams=["OAK", "Los Angeles Rams"], season=2018) == {
        "OAK": "#000000",
        "Los Angeles Rams": "#003594",
    }


def test_secondary_colors_and_bad_which():
    assert palette("mlb", which="secondary") == {"KC": "#bd9b60"}
    with pytest.raises(ValueError, match="which must be one of"):
        palette("mlb", which="tertiary")


def test_team_colors_keeps_the_container():
    out = team_colors(pd.Series(["LV", "LAC"], name="t"), "nfl")
    assert isinstance(out, pd.Series) and list(out) == ["#000000", "#0080c6"]


def test_unresolved_teams_get_no_color_and_one_warning():
    with pytest.warns(SdvplotWarning):
        assert team_colors(["LV", "XXX"], "nfl") == ["#000000", None]


def test_fallback_colors_are_returned_like_any_other():
    assert palette("ohl") == {"KIT": "#4e79a7"}


def test_palette_takes_a_season_per_row():  # M1: teams are de-duplicated with their seasons, not alone
    df = pd.DataFrame({"team": ["LA", "LA", "OAK", "OAK", "LA"], "season": [2020, 2021, 1990, 1990, 2022]})
    assert palette("nfl", teams=df["team"], season=df["season"]) == {"LA": "#003594", "OAK": "#000000"}
    # a value two teams wore across the seasons keeps the color of its first row's team
    assert palette("nfl", teams=["LA", "LA"], season=[1990, 2020]) == {"LA": "#000000"}

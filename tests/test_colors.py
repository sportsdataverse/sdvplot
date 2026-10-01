import pandas as pd
import pytest

from sdvplot._colors import palette, team_colors
from sdvplot._errors import SdvplotWarning


def test_palette_for_a_whole_league_is_keyed_by_abbreviation():
    assert palette("nfl") == {"LV": "#000000", "LAR": "#003594", "LAC": "#0080c6"}


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

import numpy as np
import pytest

from sdvplot._errors import SdvplotWarning, UnresolvedTeamError
from sdvplot._resolve import resolve


def test_abbreviation_name_and_id_resolve_to_the_same_team():
    assert resolve("LV", "nfl") == "13"
    assert resolve("Las Vegas Raiders", "nfl") == "13"
    assert resolve("13", "nfl") == "13"


def test_ids_as_int_str_float_or_numpy_resolve_the_same():  # Review Focus 1
    assert {resolve(v, "nfl") for v in (13, "13", 13.0, np.int64(13), " 13 ")} == {"13"}


def test_case_and_whitespace_do_not_matter():
    assert resolve("  lv ", "nfl") == "13"


def test_historical_abbreviation_resolves_without_a_season():
    assert resolve("OAK", "nfl") == "13"


def test_a_reused_code_needs_the_season():
    assert resolve("LA", "nfl", season=1990) == "13"  # the Los Angeles Raiders
    assert resolve("LA", "nfl", season=2020) == "14"  # the Rams
    with pytest.warns(SdvplotWarning, match="ambiguous"):
        assert resolve("LA", "nfl") is None  # two teams used LA: never guess


def test_season_outside_every_range_still_resolves_a_unique_code():
    assert resolve("STL", "nfl", season=2020) == "14"


def test_auto_takes_the_first_system_with_a_match_in_priority_order():
    assert resolve("Miami", "cfb") == "2390"  # cfbd outranks the ambiguous name entries


def test_explicit_id_system_is_honoured_and_can_be_ambiguous():
    with pytest.warns(SdvplotWarning, match="ambiguous"):
        assert resolve("Miami", "cfb", id_system="name") is None


def test_unknown_values_warn_once_listing_all_of_them():
    with pytest.warns(SdvplotWarning) as rec:
        out = resolve(["LV", "XXX", "YYY", "XXX"], "nfl")
    assert out == ["13", None, None, None]
    assert len(rec) == 1 and "'XXX'" in str(rec[0].message) and "'YYY'" in str(rec[0].message)


def test_strict_raises():
    with pytest.raises(UnresolvedTeamError, match="XXX"):
        resolve("XXX", "nfl", strict=True)


def test_unknown_league_is_a_clear_error():
    with pytest.raises(ValueError, match="unknown league 'xfl'"):
        resolve("LV", "xfl")


def test_lists_and_tuples_keep_their_length_and_order():
    assert resolve(("LAC", "LAR"), "nfl") == ["24", "14"]


def test_warning_lists_every_unresolved_value():
    unknown = [f"U{i}" for i in range(1, 26)]  # 25 distinct unknown values
    with pytest.warns(SdvplotWarning) as rec:
        resolve(unknown, "nfl")
    msg = str(rec[0].message)
    # Assert the warning message contains all 25 unresolved values
    for val in unknown:
        assert f"'{val}'" in msg


def test_a_zero_d_numpy_array_is_a_scalar():  # M3
    assert resolve(np.array("LV"), "nfl") == "13" and resolve(np.array(13), "nfl") == "13"


def test_priority_places_nhl_after_espn_abbr_and_sdvplotr_last_before_name():  # F1 (R43)
    from sdvplot._resolve import PRIORITY

    assert PRIORITY.index("nhl") == PRIORITY.index("espn_abbr") + 1
    assert PRIORITY[-2:] == ("sdvplotr", "name")
    assert "nhl_id" not in PRIORITY  # R49: NHL stats ids answer only when named

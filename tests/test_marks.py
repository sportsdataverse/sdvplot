import pytest

from sdvplot import _marks
from sdvplot._errors import SdvplotWarning, UnresolvedTeamError


@pytest.fixture(autouse=True)
def _manifest(manifest):  # the fixture manifest from tests/test_manifest.py, via conftest re-export
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

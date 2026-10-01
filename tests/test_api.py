import pytest

import sdvplot
from sdvplot import _marks

PUBLIC = {
    "resolve",
    "suggest",
    "teams",
    "palette",
    "team_colors",
    "logo_url",
    "logo_image",
    "marks",
    "headshot_url",
    "versions",
    "clear_cache",
    "add_logos",
    "add_wordmarks",
    "add_headshots",
    "axis_logos",
    "SdvplotWarning",
    "UnresolvedTeamError",
    "OfflineError",
    "OptionalDependencyError",
    "UnsupportedTargetError",
    "__version__",
}


def test_the_public_api_is_exactly_the_spec():
    assert set(sdvplot.__all__) == PUBLIC
    for name in PUBLIC:
        assert hasattr(sdvplot, name), name


def test_versions_reports_package_index_and_manifest(cache):
    v = sdvplot.versions()
    assert v["sdvplot"] == sdvplot.__version__ and v["index"] == "fixture" and v["manifest_last_modified"] is None


UNKNOWN_LEAGUE = [
    lambda: sdvplot.resolve("LV", "xfl"),
    lambda: sdvplot.palette("xfl"),
    lambda: sdvplot.palette("xfl", teams=["LV"]),
    lambda: sdvplot.team_colors(["LV"], "xfl"),
    lambda: sdvplot.teams("xfl"),
    lambda: sdvplot.suggest("LV", "xfl"),
    lambda: sdvplot.marks("LV", "xfl"),
    lambda: sdvplot.logo_url("LV", "xfl"),
]


@pytest.mark.parametrize("call", UNKNOWN_LEAGUE)
def test_an_unknown_league_is_the_same_clear_error_everywhere(call):  # M2
    with pytest.raises(ValueError, match=r"unknown league 'xfl'; known leagues: \['cfb', 'mlb', 'nfl', 'ohl'\]"):
        call()


@pytest.mark.parametrize(
    "call", [lambda: sdvplot.resolve("LV", "nfl", id_system="espnn"), lambda: sdvplot.marks("LV", "nfl", id_system="x")]
)
def test_an_unknown_id_system_lists_the_valid_ones(call):  # M2
    with pytest.raises(ValueError, match=r"unknown id_system .*'auto'.*'espn_abbr'"):
        call()


@pytest.mark.parametrize("fn", [sdvplot.logo_url, sdvplot.logo_image, _marks.select_mark])
def test_an_unknown_mark_type_is_an_error(fn):  # M2
    with pytest.raises(ValueError, match=r"mark_type must be one of \['logo', 'wordmark'\], got 'helmet'"):
        fn("LV", "nfl", mark_type="helmet")

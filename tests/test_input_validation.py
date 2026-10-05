"""Bad input says what is wrong, and where: out-of-range seasons, unknown variants, misspelled table columns, and
warnings that point at the caller's line."""

import datetime
import warnings

import pytest

import sdvplot
from sdvplot import _index
from sdvplot._errors import SdvplotWarning


def _caught(call):
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        call()
    return [w for w in rec if issubclass(w.category, SdvplotWarning)]


# --- seasons -------------------------------------------------------------------------------------------------------


def test_the_season_bounds_are_the_ones_the_index_holds():
    # the fixture index dates aliases from 1982 (the Los Angeles Raiders) to 2020 (LV)
    assert _index.season_bounds() == (1982, max(2020, datetime.date.today().year + 1))


@pytest.mark.real_index
def test_the_shipped_index_holds_seasons_from_1871():
    lo, hi = _index.season_bounds()
    assert lo == 1871 and hi >= datetime.date.today().year + 1


@pytest.mark.parametrize("season", [-1, 0, 20, 1850, 1981, 3000, [2010, 20]])
def test_a_season_outside_the_index_is_an_error_naming_the_bounds(season):
    lo, hi = _index.season_bounds()
    with pytest.raises(
        sdvplot.InputError, match=rf"season -?\d+ is outside the seasons sdvplot knows \({lo} to {hi}\)"
    ):
        sdvplot.resolve(["LV", "LAR"], "nfl", season=season)


@pytest.mark.parametrize(
    "call",
    [
        lambda s: sdvplot.team_colors("nfl", "LV", season=s),
        lambda s: sdvplot.palette("nfl", ["LV"], season=s),
        lambda s: sdvplot.logo_url("LV", "nfl", season=s),
        lambda s: sdvplot.marks("LV", "nfl", season=s),
    ],
)
def test_every_season_argument_is_checked(manifest, call):
    with pytest.raises(ValueError, match="outside the seasons"):
        call(20)


def test_this_season_and_the_next_are_always_accepted(manifest):
    year = datetime.date.today().year
    assert sdvplot.resolve("LV", "nfl", season=year + 1) == "13"  # past the index's last dated alias
    assert sdvplot.resolve("LA", "nfl", season=1990) == "13"  # inside it


def test_a_split_season_names_the_ending_year():
    with pytest.raises(ValueError, match=r"got '2020-21'; for a split season pass its ending year \(2021"):
        sdvplot.resolve("LV", "nfl", season="2020-21")


def test_a_season_of_the_wrong_type_blames_season_not_values():
    pd = pytest.importorskip("pandas")
    with pytest.raises(TypeError, match="season must be a year, or one per team, got Timestamp"):
        sdvplot.resolve("LV", "nfl", season=pd.Timestamp("2020-09-10"))


# --- variants ------------------------------------------------------------------------------------------------------


def test_an_unknown_variant_is_an_error_listing_the_leagues_variants(manifest):
    known = r"\['dark', 'default', 'grayscale', 'on_dark', 'on_light'\]"  # the fixture manifest's nfl variants
    with pytest.raises(
        ValueError, match=r"unknown variant 'bogus': no mark in the archive has it; nfl marks come in " + known
    ):
        sdvplot.logo_url("LV", "nfl", variant="bogus")


def test_a_variant_this_team_lacks_still_falls_back(manifest):
    assert sdvplot.logo_url("LV", "nfl", variant="grayscale") == sdvplot.logo_url("LV", "nfl")
    assert sdvplot.logo_url("LV", "nfl", variant="dark") is not None  # "default" and "dark" are always valid


def test_an_adapter_rejects_an_unknown_variant(mark_images):
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    try:
        with pytest.raises(sdvplot.InputError, match="unknown variant 'bogus'"):
            sdvplot.add_logos(ax, [1], [1], ["LV"], league="nfl", variant="bogus")
    finally:
        plt.close(fig)


# --- warnings point at the caller ----------------------------------------------------------------------------------


def test_warnings_from_public_verbs_name_the_callers_line(manifest):
    calls = [
        lambda: sdvplot.resolve("XYZ", "nfl"),
        lambda: sdvplot.team_colors("nfl", ["LV", "XYZ"]),
        lambda: sdvplot.palette("nfl", ["XYZ"]),
        lambda: sdvplot.logo_url("XYZ", "nfl"),
    ]
    for call in calls:
        rec = _caught(call)
        assert rec and {w.filename for w in rec} == {__file__}, [(w.filename, w.lineno) for w in rec]


def test_an_adapter_warning_names_the_callers_line(mark_images):
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    try:
        rec = _caught(lambda: sdvplot.add_logos(ax, [1, 2], [1, 2], ["LV", "XYZ"], league="nfl"))
    finally:
        plt.close(fig)
    assert len(rec) == 1 and rec[0].filename == __file__


def test_warn_walks_out_of_any_depth_of_sdvplot_frames():
    from sdvplot import _errors

    def from_sdvplot(depth):  # pretend to be sdvplot code, nested `depth` deep
        code = "def f(n):\n    return f(n - 1) if n else warn('deep')\n"
        ns = {"warn": _errors.warn}
        exec(compile(code, _errors._PACKAGE + "_fake.py", "exec"), ns)
        ns["f"](depth)

    for depth in (0, 3, 10):
        rec = _caught(lambda d=depth: from_sdvplot(d))
        assert [w.filename for w in rec] == [__file__], depth


# --- table columns -------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("backend", ["pandas", "polars"])
@pytest.mark.parametrize("columns", ["teamz", ["team", "teamz"]])
def test_a_misspelled_table_column_is_the_same_error_on_pandas_and_polars(manifest, backend, columns):
    great_tables = pytest.importorskip("great_tables")
    frame = pytest.importorskip(backend).DataFrame({"team": ["LV"]})
    with pytest.raises(ValueError, match=r"column\(s\) \['teamz'\] not in the table; its columns are \['team'\]"):
        sdvplot.add_logos(great_tables.GT(frame), columns, league="nfl")

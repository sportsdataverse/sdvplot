"""Bad input says what is wrong, and where: out-of-range seasons, unknown variants, misspelled table columns, and
warnings that point at the caller's line."""

import datetime
import warnings

import pytest

import sdvplot
from sdvplot import _index
from sdvplot._errors import InputError, SdvplotWarning
from sdvplot._normalize import norm_season


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


@pytest.mark.real_index
def test_a_leagues_own_first_season_comes_from_its_dated_aliases():
    first = {league: _index.season_bounds(league)[0] for league in ("nfl", "nba", "wnba", "xfl", "ufl", "mlb")}
    assert first == {"nfl": 1920, "nba": 1947, "wnba": 1997, "xfl": 2020, "ufl": 2024, "mlb": 1871}
    # the NHL's aliases only open ranges (its 2026 renames), which date no start: it keeps the index's floor
    assert _index.season_bounds("nhl") == _index.season_bounds("cfb") == _index.season_bounds()


@pytest.mark.real_index
@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda: sdvplot.logo_url("OAK", "nfl", season=1900), r"season 1900 .* for nfl \(1920 to \d{4}\)"),
        (lambda: sdvplot.resolve("LVA", "wnba", season=1950), r"season 1950 .* for wnba \(1997 to \d{4}\)"),
        (lambda: sdvplot.resolve("DAL", "xfl", season=1950), r"season 1950 .* for xfl \(2020 to \d{4}\)"),
        (lambda: sdvplot.team_colors("nba", ["BOS"], season=[1871]), r"season 1871 .* for nba \(1947 to \d{4}\)"),
        # below every league's first season (MLB's 1871): still the NFL's own range, not the index's
        (lambda: sdvplot.resolve("KC", "nfl", season=1850), r"season 1850 .* for nfl \(1920 to \d{4}\)"),
    ],
)
def test_a_season_before_the_leagues_first_is_an_error(call, message):
    # 1900 is inside the index's range (MLB's 1871 on), but not the NFL's: the audit's own example
    with pytest.raises(sdvplot.InputError, match=message):
        call()


@pytest.mark.real_index
def test_in_range_seasons_across_leagues_stay_silent():
    cases = [("CHI", "nfl", 1920), ("KC", "nfl", 1963), ("BOS", "nba", 1990), ("MIN", "wnba", 1999),
             ("DAL", "xfl", 2020), ("NYY", "mlb", 1990), ("TOR", "nhl", 1927), ("Alabama", "cfb", 1950),
             ("BHAM", "ufl", 2024)]  # fmt: skip
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for value, league, season in cases:
            assert sdvplot.resolve(value, league, season=season) is not None, (value, league, season)


def test_the_bounds_are_built_once_per_index_load(monkeypatch):
    # norm_season runs for every season value: the bounds must not re-read the index (or importlib.resources) per call
    _index.season_bounds()

    def fail():
        raise AssertionError("data_dir() read again")

    monkeypatch.setattr(_index, "data_dir", fail)
    assert [norm_season(2020), norm_season("2021", league="nfl")] == [2020, 2021]


@pytest.mark.parametrize("season", [-1, 0, 20, 1850, 1981, 3000, [2010, 20]])
def test_a_season_outside_the_index_is_an_error_naming_the_bounds(season):
    # the league's own bounds, in the first error: not the index's, then the league's on a retry
    lo, hi = _index.season_bounds("nfl")
    with pytest.raises(
        sdvplot.InputError, match=rf"season -?\d+ is outside the seasons sdvplot knows for nfl \({lo} to {hi}\)"
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
    with pytest.raises(InputError, match=r"got '2020-21'; for a split season pass its ending year \(2021"):
        sdvplot.resolve("LV", "nfl", season="2020-21")
    with pytest.raises(InputError, match="season must be a year such as 2020"):  # N2: one season, checked directly
        norm_season("2020-21")


def test_a_season_of_the_wrong_type_blames_season_not_values():
    pd = pytest.importorskip("pandas")
    with pytest.raises(InputError, match="season must be a year, or one per team, got Timestamp"):  # N2
        sdvplot.resolve("LV", "nfl", season=pd.Timestamp("2020-09-10"))
    with pytest.raises(InputError, match="season has 2 values but there are 1 teams"):
        sdvplot.resolve(["LV"], "nfl", season=[2020, 2021])


# --- sizes and counts (N2: every shared input check is an InputError) -----------------------------------------------


@pytest.mark.parametrize("size", [0, -5, 4097, 2.5, True, "64"])
def test_logo_image_size_is_an_int_from_1_to_4096(size):
    with pytest.raises(InputError, match=rf"size is the longest side in pixels, an int from 1 to 4096, got {size!r}"):
        sdvplot.logo_image("LV", "nfl", size=size)


@pytest.mark.parametrize("n", [0, -1, 2.5, True])
def test_suggest_n_is_an_int_of_at_least_1(n):
    with pytest.raises(InputError, match=rf"n is the most candidates to return, an int of at least 1, got {n!r}"):
        sdvplot.suggest("Kansas", "nfl", n=n)


# --- variants ------------------------------------------------------------------------------------------------------


def test_an_unknown_variant_is_an_error_listing_the_leagues_variants(manifest):
    known = r"\['dark', 'default', 'grayscale', 'on_dark', 'on_light'\]"  # the fixture manifest's nfl variants
    with pytest.raises(
        ValueError, match=r"unknown variant 'bogus': no mark in the archive has it; nfl marks come in " + known
    ):
        sdvplot.logo_url("LV", "nfl", variant="bogus")


@pytest.mark.parametrize("variant", [["dark"], ("dark",), None, 3])
def test_a_variant_that_is_not_a_string_is_the_same_error(manifest, variant):
    with pytest.raises(
        sdvplot.InputError, match=r"unknown variant .*: no mark in the archive has it; nfl marks come in"
    ):
        sdvplot.logo_url("LV", "nfl", variant=variant)


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


TABLE_CALLS = {
    "gt_percentile_bar": lambda gt: _sgt().gt_percentile_bar(gt, "zzz"),
    "gt_wrap_labels": lambda gt: _sgt().gt_wrap_labels(gt, "zzz"),
    "gt_sdv_logos locations": lambda gt: _sgt().gt_sdv_logos(gt, "team", league="nfl", locations=_loc().body("zzz")),
    "gt_color_pills": lambda gt: _sgt().gt_color_pills(gt, "zzz"),
}


def _sgt():
    pytest.importorskip("great_tables")
    import sdvplot.great_tables as sgt

    return sgt


def _loc():
    from great_tables import loc

    return loc


@pytest.mark.parametrize("backend", ["pandas", "polars"])
@pytest.mark.parametrize("call", TABLE_CALLS.values(), ids=TABLE_CALLS.keys())
def test_every_table_helper_rejects_a_misspelled_column_on_both_backends(manifest, backend, call):
    great_tables = pytest.importorskip("great_tables")
    frame = pytest.importorskip(backend).DataFrame({"team": ["LV"], "pct": [50]})
    with pytest.raises(ValueError, match=r"column\(s\) \['zzz'\] not in the table; its columns are \['team', 'pct'\]"):
        call(great_tables.GT(frame))

"""The cfbplotR-era sdvplotR functions, ported: teams(division=), aliases(), clean_names(), team_factor(), alt_colors
and add_athlete_id(). The parity tests hold the shipped index to sdvplotR's answers on the same index version
(tests/fixtures/sdvplotr_*.csv, written by tools/export_cfbplotr_parity.R); the rest run on the fixture index."""

import hashlib
import os
from pathlib import Path

import pandas as pd
import polars as pl
import pytest

import sdvplot
from sdvplot import _headshots, _index

FIXTURES = Path(__file__).parent / "fixtures"


def _csv(name: str) -> pl.DataFrame:
    return pl.read_csv(FIXTURES / name, infer_schema=False)  # every cell as text, "" as null


def _same_index() -> None:
    """The parity fixtures answer for one index version: a rebuilt index needs them exported again (with sdvplotR's
    snapshot at the same version), so they skip rather than compare two indexes."""
    want = _csv("sdvplotr_cfbplotr_meta.csv")["index_version"][0]
    if _index.index_version() != want:
        pytest.skip(
            f"the R fixtures answer for index {want}, sdvplot bundles {_index.index_version()}: rerun "
            "tools/export_cfbplotr_parity.R once sdvplotR's snapshot is at the same version"
        )


@pytest.mark.real_index
@pytest.mark.filterwarnings("ignore::sdvplot._errors.SdvplotWarning")
def test_teams_division_matches_sdvplotr():
    _same_index()
    want = _csv("sdvplotr_divisions.csv")
    assert want.height > 4000
    for (league, division), rows in want.group_by("league", "division", maintain_order=True):
        if rows["team_id"].to_list() == ["<error>"]:  # sdvplotR errors: no divisions for the league in the index
            with pytest.raises(sdvplot.InputError):
                sdvplot.teams(league, division=division.split("+"))
            continue
        got = sdvplot.teams(league, division=division.split("+"))["team_id"].to_list()
        assert sorted(got) == sorted(rows["team_id"].drop_nulls().to_list()), (league, division)


@pytest.mark.real_index
def test_aliases_are_sdvplotr_aliases_row_for_row():
    _same_index()
    want = _csv("sdvplotr_aliases_digest.csv")
    a = sdvplot.aliases()
    assert sorted(a["league"].unique().to_list()) == sorted(want["league"].to_list())
    for league, rows, md5 in want.iter_rows():
        x = sdvplot.aliases(league)
        lines = sorted("\t".join("" if v is None else str(v) for v in r) for r in x.iter_rows())
        assert (x.height, hashlib.md5("\n".join(lines).encode()).hexdigest()) == (int(rows), md5), league


@pytest.mark.real_index
@pytest.mark.filterwarnings("ignore::sdvplot._errors.SdvplotWarning")
def test_clean_names_matches_sdvplotr():
    _same_index()
    want = _csv("sdvplotr_clean_names.csv")
    for (league, numeric, column), rows in want.group_by("league", "numeric", "column", maintain_order=True):
        values = rows["value"].to_list()
        if numeric == "TRUE":  # R passed numbers (13, 4e6, 1.5, NA): the kept ones come back as id text
            values = [None if v is None else float(v) for v in values]
        assert sdvplot.clean_names(values, league, column=column) == rows["keep"].to_list(), (league, column)
        got = sdvplot.clean_names(values, league, column=column, keep_non_matches=False)
        assert got == rows["drop"].to_list(), (league, column)
    # the sample covers every id system resolve() reads in the four leagues, a miss and an ambiguous name
    assert want.filter(pl.col("drop").is_null()).height > 0


@pytest.mark.real_index
@pytest.mark.filterwarnings("ignore::sdvplot._errors.SdvplotWarning")
def test_team_factor_matches_sdvplotr():
    _same_index()
    want = _csv("sdvplotr_team_factor.csv")
    for (case, league), rows in want.group_by("case", "league", maintain_order=True):
        part = {k: rows.filter(pl.col("kind") == k)["value"].to_list() for k in ("input", "number", "value", "level")}
        f = sdvplot.team_factor(part["input"] or [float(v) for v in part["number"]], league)
        assert f.to_list() == part["value"], case
        assert f.dtype.categories.to_list() == part["level"], case


@pytest.mark.real_index
def test_alt_colors_match_sdvplotr_scales():
    _same_index()
    want = _csv("sdvplotr_alt_colors.csv")
    for (league, which, alts), rows in want.group_by("league", "which", "alt_colors", maintain_order=True):
        values = rows["value"].to_list()
        assert sdvplot.team_colors(league, values, which=which) == rows["color"].to_list()
        swapped = sdvplot.team_colors(league, values, which=which, alt_colors=alts.split("|"))
        assert swapped == rows["alt_color"].to_list(), (league, which)
        assert sdvplot.palette(league, values, which=which, alt_colors=alts.split("|")) == dict(
            zip(values, rows["alt_color"].to_list(), strict=True)
        )
    assert (want["color"] != want["alt_color"]).sum() > 0  # the swap is exercised, not vacuous


def _r_rosters(monkeypatch, tmp_path):
    """add_athlete_id reading the roster rows sdvplotR read (the files' own rows whose name is an input's), each
    season written as the parquet file it downloads, at sdvplotR's latest season: the match needs no other row, so
    this is the R run's match, offline, through the same parquet reader."""
    ro = _csv("sdvplotr_athlete_rosters.csv").with_columns(pl.col("season").cast(pl.Int64))
    paths = {}
    for (season,), r in ro.group_by("season", maintain_order=True):
        paths[season] = tmp_path / f"cfb_rosters_{season}.parquet"
        r.drop("season").write_parquet(paths[season])
    monkeypatch.setattr(
        _headshots,
        "_roster",
        lambda league, season: _headshots._roster_rows(str(paths[season]), 0.0, season) if season in paths else (),
    )
    latest = int(_csv("sdvplotr_athlete_ids.csv")["latest_season"][0])
    monkeypatch.setattr(_headshots, "_latest_roster_season", lambda: latest)


def _players() -> pl.DataFrame:
    return _csv("sdvplotr_athlete_ids.csv").with_columns(pl.col("season").cast(pl.Int64))


@pytest.mark.real_index
@pytest.mark.filterwarnings("ignore::sdvplot._errors.SdvplotWarning")
def test_add_athlete_id_matches_sdvplotr(monkeypatch, tmp_path):
    _same_index()
    _r_rosters(monkeypatch, tmp_path)
    want = _players()
    x = want.select("player_name", "team", "season")
    got = sdvplot.add_athlete_id(x, "player_name", headshot_urls=True)
    assert got["athlete_id"].to_list() == want["athlete_id"].to_list()
    assert got["headshot_url"].to_list() == want["headshot_url"].to_list()
    name_only = sdvplot.add_athlete_id(x.select("player_name"), "player_name")
    assert name_only["athlete_id"].to_list() == want["athlete_id_name_only"].to_list()
    with_season = sdvplot.add_athlete_id(x.select("player_name", "season"), "player_name")
    assert with_season["athlete_id"].to_list() == want["athlete_id_name_season"].to_list()
    assert want["athlete_id"].null_count() < want.height  # real matches, not an all-null pass


@pytest.mark.real_index
@pytest.mark.filterwarnings("ignore::sdvplot._errors.SdvplotWarning")
@pytest.mark.skipif(not os.environ.get("SDVPLOT_LIVE_TESTS"), reason="network: SDVPLOT_LIVE_TESTS=1")
def test_add_athlete_id_matches_sdvplotr_on_the_live_rosters():
    _same_index()
    want = _players()
    got = sdvplot.add_athlete_id(want.select("player_name", "team", "season"), "player_name", headshot_urls=True)
    assert got["athlete_id"].to_list() == want["athlete_id"].to_list()
    assert got["headshot_url"].to_list() == want["headshot_url"].to_list()


# --- the fixture index ---------------------------------------------------------------------------------------------


def test_teams_division_needs_a_league_and_a_known_division():
    with pytest.raises(sdvplot.InputError, match="division needs a league"):
        sdvplot.teams(division="FBS")
    with pytest.raises(sdvplot.InputError, match="division must be one or more of"):
        sdvplot.teams("cfb", division="D1")
    with pytest.raises(sdvplot.InputError, match="division must be one or more of"):
        sdvplot.teams("cfb", division=[])
    with pytest.raises(sdvplot.InputError, match="college football tiers"):
        sdvplot.teams("nfl", division="P5")
    with pytest.raises(sdvplot.InputError, match="has no 'cfb' divisions"):  # the fixture index has none
        sdvplot.teams("cfb", division="FBS")


def test_teams_division_tiers_come_from_conferences():
    with pytest.warns(sdvplot.SdvplotWarning, match="no teams in"):  # the fixture has no Big Ten, Big 12, ...
        p4 = sdvplot.teams("cfb", division="P4")
    assert sorted(p4["team_id"].to_list()) == ["2390", "333"]  # SEC Alabama, ACC Miami
    conf = sdvplot.teams("cfb", division="Conference")
    assert conf["program"].is_in(["conference", "league"]).all()


def test_aliases_is_the_alias_table():
    a = sdvplot.aliases("nfl")
    assert a.columns == ["league", "id_system", "value", "team_id", "valid_from", "valid_to"]
    assert set(a["league"]) == {"nfl"} and a.height == _index.alias_table().filter(pl.col("league") == "nfl").height
    sdvplot.aliases().clear()  # a copy: never the cached frame
    assert sdvplot.aliases().height == _index.alias_table().height
    with pytest.raises(sdvplot.InputError, match="unknown league"):
        sdvplot.aliases("xfl")


def test_clean_names_keeps_or_drops_what_does_not_resolve():
    assert sdvplot.clean_names(["LV", "nope", 13.0], "nfl") == ["Las Vegas", "nope", "Las Vegas"]
    assert sdvplot.clean_names("LV", "nfl", column="name") == "Las Vegas Raiders"
    assert sdvplot.clean_names([14.0, None], "mlb") == ["14", None]  # kept as id text, never "14.0"
    with pytest.warns(sdvplot.SdvplotWarning, match="1 value"):
        assert sdvplot.clean_names(["LV", "nope"], "nfl", keep_non_matches=False) == ["Las Vegas", None]
    with pytest.raises(sdvplot.UnresolvedTeamError):
        sdvplot.clean_names(["nope"], "nfl", strict=True)
    s = sdvplot.clean_names(pd.Series(["LV", "nope"], index=[7, 9]), "nfl", column="abbr")
    assert s.to_list() == ["LV", "nope"] and s.index.to_list() == [7, 9]
    with pytest.raises(sdvplot.InputError, match="column must be one of"):
        sdvplot.clean_names("LV", "nfl", column="school")


def test_team_factor_orders_by_abbreviation():
    with pytest.warns(sdvplot.SdvplotWarning, match="did not resolve"):
        f = sdvplot.team_factor(["LV", "LAR", "nope", "LAC", "LV"], "nfl")
    assert f.dtype == pl.Enum(["LAC", "LAR", "LV"])
    assert f.to_list() == ["LV", "LAR", None, "LAC", "LV"]
    p = sdvplot.team_factor(pd.Series(["LV", "LAR"], index=[4, 2], name="team"), "nfl")
    assert p.cat.categories.to_list() == ["LAR", "LV"] and p.cat.ordered and p.index.to_list() == [4, 2]


def test_alt_colors_swap_to_the_other_color():
    assert sdvplot.team_colors("nfl", ["LV", "LAR"], alt_colors="LV") == ["#a5acaf", "#003594"]
    assert sdvplot.team_colors("nfl", "LV", which="secondary", alt_colors=["Las Vegas Raiders"]) == "#000000"
    assert sdvplot.palette("nfl", alt_colors="LAR")["LAR"] == "#ffa300"


def test_add_athlete_id_checks_its_arguments():
    df = pl.DataFrame({"player": ["A B"]})
    with pytest.raises(ValueError, match="rosters for"):
        sdvplot.add_athlete_id(df, "player", league="nfl")
    with pytest.raises(ValueError, match="already has an athlete_id"):
        sdvplot.add_athlete_id(df.with_columns(athlete_id=pl.lit("1")), "player")
    with pytest.raises(ValueError, match="name_col must name a column"):
        sdvplot.add_athlete_id(df, "name")
    with pytest.raises(TypeError, match="DataFrame"):
        sdvplot.add_athlete_id(["A B"], "player")


def test_add_athlete_id_warns_offline_and_keeps_every_row(monkeypatch):
    monkeypatch.setattr(_headshots, "_roster", lambda league, season: ())
    df = pd.DataFrame({"player": ["A B", "C D"]}, index=[3, 5])
    with pytest.warns(sdvplot.SdvplotWarning, match="could not read"):
        out = sdvplot.add_athlete_id(df, "player")
    assert out["athlete_id"].isna().all() and out.index.to_list() == [3, 5]


def test_add_athlete_id_leaves_an_ambiguous_name_null(monkeypatch):
    rows = ((2021, "1", "Chris Johnson", "Alabama", "u1"), (2021, "2", "Chris Johnson", "Miami", "u2"))
    monkeypatch.setattr(_headshots, "_roster", lambda league, season: rows if season == 2021 else ())
    df = pl.DataFrame({"name": [" chris JOHNSON", "Chris Johnson"], "season": [2021, 2021]})
    with pytest.warns(sdvplot.SdvplotWarning, match="2 row"):
        assert sdvplot.add_athlete_id(df, "name")["athlete_id"].to_list() == [None, None]
    by_team = df.with_columns(team=pl.Series(["Miami", None]))  # no team: matches no one, is not ambiguous
    assert sdvplot.add_athlete_id(by_team, "name")["athlete_id"].to_list() == ["2", None]


def test_the_plotnine_scales_take_alt_colors():
    pytest.importorskip("plotnine")
    from sdvplot.plotnine import scale_color_sdv, scale_fill_sdv

    assert scale_fill_sdv("nfl", alt_colors=["LV"]).map(["LV", "LAR"], limits=["LV", "LAR"]) == ["#a5acaf", "#003594"]
    s = scale_color_sdv("nfl", which="secondary", alt_colors="LAR")
    assert s.map(["LV", "LAR"], limits=["LV", "LAR"]) == ["#a5acaf", "#003594"]


def test_add_athlete_id_skips_a_missing_pandas_team(monkeypatch):
    rows = ((2021, "1", "Chris Johnson", None, None),)  # a roster row with no team must not meet a NaN team
    monkeypatch.setattr(_headshots, "_roster", lambda league, season: rows if season == 2021 else ())
    df = pd.DataFrame({"name": ["Chris Johnson"], "team": [float("nan")], "season": [2021]})
    assert sdvplot.add_athlete_id(df, "name")["athlete_id"].isna().all()

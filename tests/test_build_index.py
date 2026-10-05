import importlib.util
from pathlib import Path

import polars as pl
import pytest

from sdvplot import _index

spec = importlib.util.spec_from_file_location("build_index", Path(__file__).parents[1] / "tools" / "build_index.py")
bi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bi)


def _raw(tmp_path):
    raw = tmp_path / "data-raw"
    (raw / "curated").mkdir(parents=True, exist_ok=True)
    files = {
        "manifest_teams.csv": "league,team_id,name,program\nnfl,13,Las Vegas Raiders,pro\nohl,7,Kitchener Rangers,junior\n"
        "mlb,7,Kansas City Royals,pro\n",
        "manifest_marks.csv": "league,source,entity_id,entity_name,valid_from,valid_to\n"
        "nfl,espn,13,Las Vegas Raiders,,\nnfl,nflverse,OAK,Oakland Raiders,,\nnfl,espn,99,Nobody,,\n",
        "espn_teams.csv": "league,team_id,abbreviation,display_name,short_display_name,location,nickname,color,alternate_color\n"
        "nfl,13,LV,Las Vegas Raiders,Raiders,Las Vegas,Raiders,000000,a5acaf\n"
        "mlb,7,KC,Kansas City Royals,Royals,Kansas City,Royals,004687,NULL\n",
        "nflverse_teams.csv": "team_abbr,team_name,team_nick,team_color,team_color2,team_logo_espn\n"
        "LV,Las Vegas Raiders,Raiders,#000000,#A5ACAF,https://a.espncdn.com/i/teamlogos/nfl/500/lv.png\n"
        "OAK,Oakland Raiders,Raiders,#000000,#A5ACAF,https://a.espncdn.com/i/teamlogos/nfl/500/lv.png\n",
        "cfbd_teams.csv": "team_id,school,abbreviation,alternate_names\n",
        "nba_api_teams.csv": "nba_api_id,abbreviation,nickname,full_name\n",
        "nhl_teams.csv": "nhl_id,franchise_id,tri_code,full_name,franchise_full_name,franchise_common_name\n",
        "mlbstats_teams.csv": "sport_id,mlbstats_id,abbreviation,team_code,file_code,team_name,name\n",
        "mlbstats_history.csv": "mlbstats_id,abbreviation,team_code,name,valid_from,valid_to\n",
        "groups_latest.csv": "league,team_id,season,conference_id,conference\nnfl,13,2026,nfl:afc-west,AFC West\n",
        "curated/historical_abbrs.csv": "league,id_system,value,canonical,valid_from,valid_to\nnfl,nflverse,OAK,LV,,2019\n",
        "curated/fangraphs_abbrs.csv": "fangraphs,espn_abbr\n",
    }
    for name, text in files.items():
        (raw / name).write_text(text, encoding="utf-8", newline="")  # LF on every OS, like the eol=lf checkout
    return raw


def test_build_produces_the_runtime_schema_and_resolvable_aliases(tmp_path):
    teams, aliases, version = bi.build(_raw(tmp_path))
    assert teams.schema == pl.Schema(_index.TEAM_SCHEMA) and aliases.schema == pl.Schema(_index.ALIAS_SCHEMA)
    lv = teams.filter(pl.col("team_id") == "13").row(0, named=True)
    assert (lv["abbr"], lv["color_primary"], lv["color_source"], lv["conference"]) == (
        "LV",
        "#000000",
        "nflverse",
        "AFC West",
    )
    oak = aliases.filter(pl.col("value") == "OAK").row(0, named=True)
    assert (oak["team_id"], oak["valid_to"]) == ("13", 2019)
    assert {"team_id", "espn", "espn_abbr", "name", "nflverse", "mark"} <= set(aliases["id_system"])
    marks = aliases.filter(pl.col("id_system") == "mark")
    # R36: a relocation-derived mark alias carries the curated range; an identity one has none
    assert sorted(marks.select("value", "team_id", "valid_from", "valid_to").rows()) == [
        ("espn:13", "13", None, None),
        ("nflverse:OAK", "13", None, 2019),
    ]
    assert len(version) == 12


def test_teams_without_source_colors_get_a_flagged_deterministic_fallback(tmp_path):
    teams, _, _ = bi.build(_raw(tmp_path))
    kit = teams.filter(pl.col("league") == "ohl").row(0, named=True)
    assert kit["color_source"] == "fallback" and kit["color_primary"].startswith("#")
    assert kit["color_secondary"].startswith("#") and kit["color_secondary"] != kit["color_primary"]
    # R38: a source primary never gets an invented secondary
    kc = teams.filter(pl.col("league") == "mlb").row(0, named=True)
    assert (kc["color_source"], kc["color_primary"], kc["color_secondary"]) == ("espn", "#004687", None)
    assert bi.build(_raw(tmp_path))[0].equals(teams)  # deterministic


def test_hex_nulls_placeholders_and_lowercases():
    df = pl.DataFrame({"c": ["NULL", None, "A5ACAF", "#000000", "zzzzzz", "fff"]})
    assert df.select(bi._hex("c")).to_series().to_list() == [None, None, "#a5acaf", "#000000", None, None]


def test_check_mode_detects_drift(tmp_path, monkeypatch):
    raw = _raw(tmp_path)
    out = tmp_path / "data"
    assert bi.main(["--raw", str(raw), "--out", str(out)]) == 0
    assert bi.main(["--raw", str(raw), "--out", str(out), "--check"]) == 0
    (raw / "manifest_teams.csv").write_text("league,team_id,name,program\nnfl,13,Raiders,pro\n")
    assert bi.main(["--raw", str(raw), "--out", str(out), "--check"]) == 1


def test_check_mode_detects_dtype_only_drift(tmp_path):  # equals() alone calls Int32 == Int64 the same
    raw = _raw(tmp_path)
    out = tmp_path / "data"
    assert bi.main(["--raw", str(raw), "--out", str(out)]) == 0
    aliases = pl.read_parquet(out / "aliases.parquet")
    aliases.with_columns(pl.col("valid_from").cast(pl.Int64)).write_parquet(out / "aliases.parquet")
    assert bi.main(["--raw", str(raw), "--out", str(out), "--check"]) == 1


# The mark crosswalk (Ruling R19 build half, R25): one test per source rule
MARK_COLS = ["league", "source", "entity_id", "entity_name", "valid_from", "valid_to"]
NHL_COLS = ["nhl_id", "franchise_id", "tri_code", "full_name", "franchise_full_name", "franchise_common_name"]


def _text(rows, cols):
    return pl.DataFrame(rows, schema=dict.fromkeys(cols, pl.String), orient="row")


def _crosswalk(marks, teams, aliases=(), nhl=(), espn=(), ranges=False):
    out = bi.mark_aliases(
        _text(marks, MARK_COLS),
        _text(teams, ["league", "team_id"]),
        pl.DataFrame(list(aliases), schema=_index.ALIAS_SCHEMA, orient="row"),
        _text(nhl, NHL_COLS),
        _text(espn, ["league", "team_id", "nickname"]),
    )
    if ranges:
        return {r[0]: r[1:] for r in out.select("value", "team_id", "valid_from", "valid_to").rows()}
    return dict(out.select("value", "team_id").rows())


def test_mark_identity_rows_map_to_their_own_id_when_the_team_exists():
    got = _crosswalk(
        [
            ("nfl", "espn", "13", "Las Vegas Raiders", None, None),
            ("milb", "mlbstatic", "102", "Round Rock Express", None, None),
            ("ohl", "hockeytech", "7", "Kitchener Rangers", None, None),
            ("nfl", "espn", "99", "Nobody", None, None),
        ],
        [("nfl", "13"), ("milb", "102"), ("ohl", "7")],
    )
    assert got == {"espn:13": "13", "mlbstatic:102": "102", "hockeytech:7": "7", "espn:99": None}


def test_mark_espn_abbreviation_rows_map_through_nflverse_or_curated_espn_abbr():
    got = _crosswalk(
        [
            ("nfl", "espn", "OAK", "OAK", None, None),
            ("wnba", "espn", "DET", "DET", None, None),
            ("wnba", "espn", "HOU", "HOU", None, None),
        ],
        [("nfl", "13"), ("wnba", "3")],
        aliases=[("nfl", "nflverse", "OAK", "13", None, 2019), ("wnba", "espn_abbr", "DET", "3", 1998, 2009)],
    )
    assert got == {"espn:OAK": "13", "espn:DET": "3", "espn:HOU": None}
    # R36: one key, two ranges for the same team -> their union
    split = [("wnba", "espn_abbr", "DET", "3", 1998, 2003), ("wnba", "espn_abbr", "DET", "3", 2004, 2009)]
    got = _crosswalk([("wnba", "espn", "DET", "DET", None, None)], [("wnba", "3")], aliases=split, ranges=True)
    assert got == {"espn:DET": ("3", 1998, 2009)}


def test_mark_nflverse_rows_map_through_nflverse_aliases():
    aliases = [
        ("nfl", "nflverse", "LV", "13", None, None),
        ("nfl", "nflverse", "LA", "14", None, None),  # the current abbreviation, as the build writes it
        ("nfl", "nflverse", "LA", "14", 2016, None),
        ("nfl", "nflverse", "LA", "13", 1982, 1994),
        ("nfl", "nflverse", "STL", "14", None, 2015),
    ]
    teams = [("nfl", "13"), ("nfl", "14")]
    # no range: the current abbreviation decides ("LA" today is the Rams)
    got = _crosswalk([("nfl", "nflverse", c, c, None, None) for c in ("LV", "LA", "STL")], teams, aliases)
    assert got == {"nflverse:LV": "13", "nflverse:LA": "14", "nflverse:STL": "14"}
    # R36: current abbreviations keep a null range; a relocation code carries its alias range
    got = _crosswalk([("nfl", "nflverse", c, c, None, None) for c in ("LA", "STL")], teams, aliases, ranges=True)
    assert got == {"nflverse:LA": ("14", None, None), "nflverse:STL": ("14", None, 2015)}
    # a range: the relocation aliases over that range decide
    assert _crosswalk([("nfl", "nflverse", "LA", "Los Angeles Raiders", "1982", "1994")], teams, aliases) == {
        "nflverse:LA": "13"
    }


def test_mark_mlbstatic_in_mlb_maps_through_mlbstats_ids_never_raw():
    got = _crosswalk(
        [("mlb", "mlbstatic", "147", "New York Yankees", None, None), ("mlb", "mlbstatic", "1", "Nobody", None, None)],
        [("mlb", "1"), ("mlb", "10")],
        aliases=[("mlb", "mlbstats", "147", "10", None, None), ("mlb", "mlbstats", "NYY", "10", None, None)],
    )
    assert got == {"mlbstatic:147": "10", "mlbstatic:1": None}  # "1" is the Orioles' ESPN id, not an MLB Stats id


def test_mark_nhl_rows_map_through_the_franchise_common_name():
    got = _crosswalk(
        [
            ("nhl", "nhl", "1", "NJD", None, None),
            ("nhl", "nhl", "32", "QUE", None, None),
            ("nhl", "nhl", "53", "ARI", None, None),
            ("nhl", "nhl", "EDM", "EDM", None, None),
        ],
        [("nhl", "1"), ("nhl", "11"), ("nhl", "17"), ("nhl", "6")],
        nhl=[
            ("1", "23", "NJD", "New Jersey Devils", "New Jersey Devils", "Devils"),
            ("32", "27", "QUE", "Quebec Nordiques", "Colorado Avalanche", "Avalanche"),
            ("53", "28", "ARI", "Arizona Coyotes", "Arizona Coyotes", "Coyotes"),
            ("22", "25", "EDM", "Edmonton Oilers", "Edmonton Oilers", "Oilers"),
        ],
        espn=[("nhl", "1", "Bruins"), ("nhl", "11", "Devils"), ("nhl", "17", "Avalanche"), ("nhl", "6", "Oilers")],
    )
    # NHL id 1 is New Jersey (ESPN 11), never ESPN 1 (Boston); the Coyotes have no ESPN team
    assert got == {"nhl:1": "11", "nhl:32": "17", "nhl:53": None, "nhl:EDM": "6"}


def test_mark_nwhl_rows_map_by_name():
    got = _crosswalk(
        [
            ("phf", "nwhl.co", "6335", "Boston Pride", "2016", "2016"),
            ("phf", "nwhl.co", "6338", "New York Riveters", "2016", "2016"),
        ],
        [("phf", "61638")],
        aliases=[("phf", "name", "Boston Pride", "61638", None, None)],
    )
    assert got == {"nwhl.co:6335": "61638", "nwhl.co:6338": None}


def test_mark_unknown_source_gets_no_alias():
    got = _crosswalk(
        [("nfl", "somewhere", "13", "Las Vegas Raiders", None, None)],
        [("nfl", "13")],
        aliases=[("nfl", "team_id", "13", "13", None, None), ("nfl", "name", "Las Vegas Raiders", "13", None, None)],
    )
    assert got == {"somewhere:13": None}


def test_mark_key_mapping_to_two_teams_gets_no_alias():
    got = _crosswalk(
        [
            ("nfl", "nflverse", "LA", "Los Angeles Rams", "2016", "2025"),
            ("nfl", "nflverse", "LA", "Los Angeles Raiders", "1982", "1994"),
            ("phf", "nwhl.co", "9", "Metropolitan Riveters", None, None),
        ],
        [("nfl", "13"), ("nfl", "14"), ("phf", "61636"), ("phf", "124984")],
        aliases=[
            ("nfl", "nflverse", "LA", "14", 2016, None),
            ("nfl", "nflverse", "LA", "13", 1982, 1994),
            ("phf", "name", "Metropolitan Riveters", "61636", None, None),
            ("phf", "name", "Metropolitan Riveters", "124984", None, None),
        ],
    )
    assert got == {"nflverse:LA": None, "nwhl.co:9": None}


def test_index_version_is_a_digest_of_the_built_frames(tmp_path):
    # R37: the stamp follows the content, not the input bytes
    teams, aliases, version = bi.build(_raw(tmp_path))
    assert version == bi.stamp(teams, aliases) == bi.stamp(teams.clone(), aliases.clone())
    changed = aliases.with_columns(
        pl.when(pl.col("value") == "OAK").then(pl.lit(2018)).otherwise("valid_to").alias("valid_to")
    )
    assert bi.stamp(teams, changed) != version
    raw = _raw(tmp_path)
    for f in raw.rglob("*.csv"):  # a Windows autocrlf checkout: same frames, same stamp
        f.write_bytes(f.read_bytes().replace(b"\n", b"\r\n"))
    assert bi.build(raw)[2] == version


def test_mark_espn_abbreviation_rows_outside_nfl_map_only_through_dated_aliases():
    # R40: "CHA" is a current team's abbreviation, but an old CHA logo must not land on it with an open range
    got = _crosswalk(
        [("wnba", "espn", "CHA", "CHA", None, None), ("wnba", "espn", "DET", "DET", None, None)],
        [("wnba", "3"), ("wnba", "99")],
        aliases=[("wnba", "espn_abbr", "CHA", "99", None, None), ("wnba", "espn_abbr", "DET", "3", 1998, 2009)],
    )
    assert got == {"espn:CHA": None, "espn:DET": "3"}


def _royals_and_athletics(raw):
    """The Royals (MLB Stats 118, ESPN 7) and the Athletics (133, ESPN 11), with the API's codes over time."""
    _add(raw, "manifest_teams.csv", "mlb,11,Athletics,pro")
    _add(raw, "espn_teams.csv", "mlb,11,ATH,Athletics,Athletics,Athletics,Athletics,003831,efb21e")
    _add(raw, "mlbstats_teams.csv", "1,118,KC,kca,kc,Royals,Kansas City Royals")
    _add(raw, "mlbstats_teams.csv", "1,133,ATH,ath,ath,Athletics,Athletics")
    for line in (
        "118,KC,kca,Kansas City Royals,1968,2026",
        "133,PHA,pha,Philadelphia Athletics,1901,1954",
        "133,KCA,kc1,Kansas City Athletics,1955,1967",
        "133,OAK,oak,Oakland Athletics,1968,2024",
        "133,ATH,ath,Athletics,2025,2026",
    ):
        _add(raw, "mlbstats_history.csv", line)


def test_sr_codes_are_read_in_their_aggregated_form(tmp_path):  # F5 (R47)
    raw = _raw(tmp_path)
    _royals_and_athletics(raw)
    (raw / "sr_codes.csv").write_text(
        "league,team_code,team_name,valid_from,valid_to\n"
        "mlb,KCR,Kansas City Royals,1969,2025\nmlb,KCA,Kansas City Athletics,1955,1967\n"
        "mlb,MLA,Milwaukee Brewers,1901,1901\n"
    )
    _, aliases, _ = bi.build(raw)
    for system in ("bref", "sportsipy"):  # MLB codes reach their franchise through the MLB Stats API history
        got = aliases.filter(pl.col("id_system") == system).select("value", "team_id", "valid_from", "valid_to")
        assert sorted(got.rows()) == [("KCA", "11", 1955, 1967), ("KCR", "7", 1969, 2025)]  # no franchise for MLA here


def test_mlb_stats_codes_are_dated_and_a_team_code_never_shadows_an_abbreviation(tmp_path):
    raw = _raw(tmp_path)
    _royals_and_athletics(raw)
    (raw / "sdvplotr_abbr_mapping.csv").write_text("sport,key,canon\nmlb,KCA,KC\nmlb,KCR,KC\n")
    (raw / "sdvplotr_historical.csv").write_text("sport,key,canon\n")
    _, aliases, _ = bi.build(raw)
    got = aliases.filter((pl.col("league") == "mlb") & (pl.col("id_system") == "mlbstats"))
    assert sorted(got.select("value", "team_id", "valid_from", "valid_to").rows(), key=str) == sorted(
        [
            ("118", "7", None, None),  # franchise ids and fileCodes: undated
            ("133", "11", None, None),
            ("kc", "7", None, None),
            ("ath", "11", None, None),
            ("KC", "7", 1968, None),  # a run that reaches the latest season stays open
            ("ATH", "11", 2025, None),
            ("ath", "11", 2025, None),
            ("PHA", "11", 1901, 1954),
            ("pha", "11", 1901, 1954),
            ("KCA", "11", 1955, 1967),
            ("kc1", "11", 1955, 1967),
            ("OAK", "11", 1968, 2024),
            ("oak", "11", 1968, 2024),
        ],
        key=str,
    )  # the Royals' teamCode "kca" spells the Kansas City Athletics' abbreviation: dropped
    sdvr = aliases.filter(pl.col("id_system") == "sdvplotr").select("value", "team_id").rows()
    assert sdvr == [("KCR", "7")]  # sdvplotR's undated KCA -> KC yields to the dated KCA


def _add(raw, name, line):
    with open(raw / name, "a") as f:
        f.write(line + "\n")


def test_nflverse_dark_logo_urls_join_to_their_espn_team(tmp_path):  # M5: CAR's nflverse logo is /nfl/500-dark/
    raw = _raw(tmp_path)
    _add(raw, "manifest_teams.csv", "nfl,29,Carolina Panthers,pro")
    _add(raw, "espn_teams.csv", "nfl,29,CAR,Carolina Panthers,Panthers,Carolina,Panthers,0085ca,000000")
    _add(
        raw,
        "nflverse_teams.csv",
        "CAR,Carolina Panthers,Panthers,#0085CA,#101820,https://a.espncdn.com/i/teamlogos/nfl/500-dark/car.png",
    )
    teams, _, _ = bi.build(raw)
    car = teams.filter(pl.col("team_id") == "29").row(0, named=True)
    assert (car["color_source"], car["color_secondary"]) == ("nflverse", "#101820")


def test_a_current_nflverse_team_with_no_espn_team_fails_the_build(tmp_path):  # M5
    raw = _raw(tmp_path)
    _add(raw, "nflverse_teams.csv", "CAR,Carolina Panthers,Panthers,#0085CA,#101820,https://example.com/car.png")
    with pytest.raises(AssertionError, match="CAR"):
        bi.build(raw)


def test_nhl_tri_codes_answer_under_auto_and_numeric_ids_only_by_name(tmp_path):  # F1 (R43), R49
    raw = _raw(tmp_path)
    _add(raw, "manifest_teams.csv", "nhl,11,New Jersey Devils,pro")
    _add(raw, "espn_teams.csv", "nhl,11,NJ,New Jersey Devils,Devils,New Jersey,Devils,ce1126,000000")
    for row in (
        "1,23,NJD,New Jersey Devils,New Jersey Devils,Devils",
        "53,28,ARI,Arizona Coyotes,Arizona Coyotes,Coyotes",
    ):
        _add(raw, "nhl_teams.csv", row)
    _, aliases, _ = bi.build(raw)
    got = aliases.filter(pl.col("id_system").is_in(["nhl", "nhl_id"]))
    # the Coyotes have no ESPN team; NHL id 1 is another team's ESPN id, so it sits in nhl_id, outside PRIORITY
    assert sorted(got.select("id_system", "value", "team_id", "valid_from", "valid_to").rows()) == [
        ("nhl", "NJD", "11", None, None),
        ("nhl_id", "1", "11", None, None),
    ]


def test_sdvplotr_keys_map_through_their_canonical_abbreviation(tmp_path):  # F1 (R43)
    raw = _raw(tmp_path)
    for tid, abbr, name in (("14", "LAR", "Los Angeles Rams"), ("24", "LAC", "Los Angeles Chargers")):
        _add(raw, "manifest_teams.csv", f"nfl,{tid},{name},pro")
        _add(
            raw,
            "espn_teams.csv",
            f"nfl,{tid},{abbr},{name},{name.split()[-1]},Los Angeles,{name.split()[-1]},000000,ffffff",
        )
    (raw / "sdvplotr_abbr_mapping.csv").write_text(
        "sport,key,canon\nnfl,LVR,LV\nnfl,LAS VEGAS,LV\nnfl,XYZ,NOPE\nnfl,LOS ANGELES,LAR\nnba,LVR,LV\n"
    )
    (raw / "sdvplotr_historical.csv").write_text("sport,key,canon\nnfl,OAK,LV\nnfl,RAI,LVR\nnfl,LVR,LAC\n")
    _, aliases, _ = bi.build(raw)
    got = aliases.filter(pl.col("id_system") == "sdvplotr").select("league", "value", "team_id").rows()
    # XYZ: no team; LOS ANGELES: two teams by name (sdvplotR keeps the first, sdvplot never guesses); nba: no team;
    # historical: OAK; RAI through abbr_mapping's LVR; LVR stays abbr_mapping's (sdvplotR's order)
    assert sorted(got) == [("nfl", "LAS VEGAS", "13"), ("nfl", "LVR", "13"), ("nfl", "OAK", "13"), ("nfl", "RAI", "13")]
    assert aliases.filter(pl.col("id_system") == "sdvplotr")["valid_from"].is_null().all()


def test_mark_nhl_rows_of_a_franchise_without_an_espn_team_follow_its_tri_code():  # R50
    # the Coyotes franchise has no ESPN team; its tri-codes resolve to Utah through the user-facing aliases
    # (sdvplotR's ARI/PHX), so its marks join Utah's with no alias range: each keeps its manifest range
    got = _crosswalk(
        [
            ("nhl", "nhl", "53", "ARI", "2015", "2021"),
            ("nhl", "nhl", "27", "PHX", "1997", "1999"),
            ("nhl", "nhl", "45", "SLE", "1934", "1935"),
        ],
        [("nhl", "129764")],
        aliases=[("nhl", "sdvplotr", "ARI", "129764", None, None), ("nhl", "sdvplotr", "PHX", "129764", None, None)],
        nhl=[
            ("53", "28", "ARI", "Arizona Coyotes", "Arizona Coyotes", "Coyotes"),
            ("27", "28", "PHX", "Phoenix Coyotes", "Arizona Coyotes", "Coyotes"),
            ("45", "3", "SLE", "St. Louis Eagles", "St. Louis Eagles", "Eagles"),
        ],
        espn=[("nhl", "129764", "Mammoth")],
        ranges=True,
    )
    assert got == {"nhl:53": ("129764", None, None), "nhl:27": ("129764", None, None), "nhl:45": (None, None, None)}


def test_a_current_espn_code_another_team_held_earlier_starts_after_it():
    rows = [
        ("mlb", "espn_abbr", "MIL", "8", None, None),  # today's Brewers
        ("mlb", "mlbstats", "MIL", "15", 1953, 1965),  # the Milwaukee Braves
        ("mlb", "mlbstats", "MIL", "8", 1970, None),
        ("mlb", "espn_abbr", "KC", "7", None, None),  # nobody else's: untouched
        ("wnba", "espn_abbr", "DET", "3", 1998, 2009),  # already dated: untouched
    ]
    a = pl.DataFrame(rows, schema=_index.ALIAS_SCHEMA, orient="row")
    got = bi.date_reused_codes(a).filter(pl.col("id_system") == "espn_abbr")
    assert sorted(got.select("value", "valid_from", "valid_to").rows()) == [
        ("DET", 1998, 2009),
        ("KC", None, None),
        ("MIL", 1966, None),
    ]


def test_espn_team_endpoint_abbreviations_add_to_the_list_but_never_take_a_listed_one(tmp_path):
    raw = _raw(tmp_path)
    for tid, abbr, name in (("95", "NCST", "NC State Wolfpack"), ("497", "LSU", "LSU Tigers")):
        _add(raw, "manifest_teams.csv", f"ncaa_baseball,{tid},{name},college")
        _add(raw, "espn_teams.csv", f"ncaa_baseball,{tid},{abbr},{name},{name},{name},{name},,")
    _add(raw, "manifest_teams.csv", "ncaa_baseball,890,LSU Alexandria,college")
    _add(raw, "espn_teams.csv", "ncaa_baseball,890,LSUA,LSU Alexandria,LSU Alexandria,LSU Alexandria,Generals,,")
    _add(raw, "manifest_teams.csv", "ncaa_baseball,302,Valparaiso Beacons,college")
    _add(raw, "espn_teams.csv", "ncaa_baseball,302,VALP,Valparaiso Beacons,Valparaiso,Valparaiso,Beacons,,")
    (raw / "espn_abbrs.csv").write_text(
        "league,team_id,abbreviation,display_name,valid_from,valid_to\n"
        "ncaa_baseball,95,NCSU,NC State Wolfpack,,\nncaa_baseball,890,LSU,LSU Alexandria,,\n"
        "ncaa_baseball,497,LSU,LSU Tigers,,\nncaa_baseball,302,VAL,Valparaiso Beacons,,\n"
        "ncaa_baseball,851,VAL,Valdosta State Blazers,,\n"  # 851 is not in the index; VAL still names two teams
    )
    _, aliases, _ = bi.build(raw)
    got = aliases.filter((pl.col("league") == "ncaa_baseball") & (pl.col("id_system") == "espn_abbr"))
    assert sorted(got.select("value", "team_id").rows()) == [
        ("LSU", "497"),  # the list's LSU; LSU Alexandria's per-team "LSU" is left out
        ("LSUA", "890"),
        ("NCST", "95"),
        ("NCSU", "95"),  # added beside the list's NCST
        ("VALP", "302"),
    ]


def test_curated_mark_ranges_date_their_key_and_fail_on_an_unknown_one():
    mark = pl.DataFrame(
        {"league": ["nhl", "nhl"], "id_system": ["mark"] * 2, "value": ["nhl:59", "nhl:68"], "team_id": ["129764"] * 2,
         "valid_from": [None, None], "valid_to": [None, None]},
        schema_overrides={"valid_from": pl.Int32, "valid_to": pl.Int32},
    )  # fmt: skip
    curated = pl.DataFrame({"league": ["nhl"], "mark": ["nhl:68"], "valid_from": ["2026"], "valid_to": [None]})
    got = bi.curated_mark_ranges(mark, curated)
    assert got.columns == mark.columns
    assert sorted(got.select("value", "valid_from", "valid_to").rows()) == [
        ("nhl:59", None, None),
        ("nhl:68", 2026, None),
    ]
    with pytest.raises(AssertionError, match="nhl:99"):
        bi.curated_mark_ranges(mark, curated.with_columns(pl.lit("nhl:99").alias("mark")))

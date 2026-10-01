import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("fetch_sources", Path(__file__).parents[1] / "tools" / "fetch_sources.py")
fs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fs)


def test_espn_rows_flatten_the_team_payload():
    payload = {"sports": [{"leagues": [{"teams": [{"team": {
        "id": "13", "abbreviation": "LV", "displayName": "Las Vegas Raiders", "shortDisplayName": "Raiders",
        "location": "Las Vegas", "name": "Raiders", "color": "000000", "alternateColor": "a5acaf"}}]}]}]}
    assert fs.espn_rows("nfl", payload) == [{
        "league": "nfl", "team_id": "13", "abbreviation": "LV", "display_name": "Las Vegas Raiders",
        "short_display_name": "Raiders", "location": "Las Vegas", "nickname": "Raiders",
        "color": "000000", "alternate_color": "a5acaf"}]


def _row(source, entity_id, name, last_seen, league="nfl", level="team", program="pro", **kw):
    return {"level": level, "league": league, "source": source, "entity_id": entity_id, "entity_name": name,
            "program": program, "last_seen": last_seen, "variant": "default", "url": "u", "valid_from": "",
            "valid_to": "", **kw}


def test_manifest_teams_keep_the_latest_name_per_team():
    rows = [
        _row("espn", "13", "Oakland Raiders", "2026-09-01"),
        _row("espn", "13", "Las Vegas Raiders", "2026-10-01"),
        _row("espn", "8", "AFC West", "2026-10-01", level="conference", program=""),
    ]
    assert fs.manifest_team_rows(rows) == [{"league": "nfl", "team_id": "13", "name": "Las Vegas Raiders", "program": "pro"}]


def test_manifest_teams_come_from_identity_keyed_sources_only():
    rows = [
        _row("espn", "1", "Boston Bruins", "2026-09-01", league="nhl"),
        _row("nhl", "1", "New Jersey Devils", "2026-10-01", league="nhl"),
        _row("nflverse", "LV", "Las Vegas Raiders", "2026-10-01"),
        _row("mlbstatic", "108", "Los Angeles Angels", "2026-10-01", league="mlb"),
        _row("mlbstatic", "400", "Durham Bulls", "2026-10-01", league="milb"),
    ]
    assert fs.manifest_team_rows(rows) == [
        {"league": "milb", "team_id": "400", "name": "Durham Bulls", "program": "pro"},
        {"league": "nhl", "team_id": "1", "name": "Boston Bruins", "program": "pro"},
    ]


def test_manifest_mark_rows_dedupe_variants_and_skip_non_teams():
    rows = [
        _row("nhl", "1", "New Jersey Devils", "2026-10-01", league="nhl", variant="dark", url="a"),
        _row("nhl", "1", "New Jersey Devils", "2026-10-01", league="nhl", variant="default", url="b"),
        _row("nhl", "1", "New Jersey Devils", "2026-10-01", league="nhl", valid_from="2000", valid_to="2010"),
        _row("espn", "8", "AFC West", "2026-10-01", level="conference"),
    ]
    assert fs.manifest_mark_rows(rows) == [
        {"league": "nhl", "source": "nhl", "entity_id": "1", "entity_name": "New Jersey Devils",
         "valid_from": "", "valid_to": ""},
        {"league": "nhl", "source": "nhl", "entity_id": "1", "entity_name": "New Jersey Devils",
         "valid_from": "2000", "valid_to": "2010"},
    ]


def test_nhl_rows_join_teams_to_franchises():
    teams = {"data": [{"id": 32, "franchiseId": 27, "fullName": "Quebec Nordiques", "triCode": "QUE", "leagueId": 133}]}
    fran = {"data": [{"id": 27, "fullName": "Colorado Avalanche", "teamCommonName": "Avalanche", "teamPlaceName": "Colorado"}]}
    assert fs.nhl_rows(teams, fran) == [{
        "nhl_id": "32", "franchise_id": "27", "tri_code": "QUE", "full_name": "Quebec Nordiques",
        "franchise_full_name": "Colorado Avalanche", "franchise_common_name": "Avalanche"}]


def test_ncaa_crosswalk_rows():
    assert fs.ncaa_rows({"113180": "2657"}) == [{"league": "cfb", "ncaa_id": "113180", "team_id": "2657"}]

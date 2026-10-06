import importlib.util
import json
from pathlib import Path

import pytest
import requests

spec = importlib.util.spec_from_file_location("fetch_sources", Path(__file__).parents[1] / "tools" / "fetch_sources.py")
fs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fs)


def test_espn_rows_flatten_the_team_payload():
    payload = {
        "sports": [
            {
                "leagues": [
                    {
                        "teams": [
                            {
                                "team": {
                                    "id": "13",
                                    "abbreviation": "LV",
                                    "displayName": "Las Vegas Raiders",
                                    "shortDisplayName": "Raiders",
                                    "location": "Las Vegas",
                                    "name": "Raiders",
                                    "color": "000000",
                                    "alternateColor": "a5acaf",
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }
    assert fs.espn_rows("nfl", payload) == [
        {
            "league": "nfl",
            "team_id": "13",
            "abbreviation": "LV",
            "display_name": "Las Vegas Raiders",
            "short_display_name": "Raiders",
            "location": "Las Vegas",
            "nickname": "Raiders",
            "color": "000000",
            "alternate_color": "a5acaf",
        }
    ]


def _row(source, entity_id, name, last_seen, league="nfl", level="team", program="pro", **kw):
    return {
        "level": level,
        "league": league,
        "source": source,
        "entity_id": entity_id,
        "entity_name": name,
        "program": program,
        "last_seen": last_seen,
        "variant": "default",
        "url": "u",
        "valid_from": "",
        "valid_to": "",
        **kw,
    }


def test_manifest_teams_keep_the_latest_name_per_team():
    rows = [
        _row("espn", "13", "Oakland Raiders", "2026-09-01"),
        _row("espn", "13", "Las Vegas Raiders", "2026-10-01"),
        _row("espn", "8", "AFC West", "2026-10-01", level="conference", program=""),
    ]
    assert fs.manifest_team_rows(rows) == [
        {"league": "nfl", "team_id": "13", "name": "Las Vegas Raiders", "program": "pro"}
    ]


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
        {
            "league": "nhl",
            "source": "nhl",
            "entity_id": "1",
            "entity_name": "New Jersey Devils",
            "valid_from": "",
            "valid_to": "",
        },
        {
            "league": "nhl",
            "source": "nhl",
            "entity_id": "1",
            "entity_name": "New Jersey Devils",
            "valid_from": "2000",
            "valid_to": "2010",
        },
    ]


def test_nhl_rows_join_teams_to_franchises():
    teams = {"data": [{"id": 32, "franchiseId": 27, "fullName": "Quebec Nordiques", "triCode": "QUE", "leagueId": 133}]}
    fran = {
        "data": [
            {"id": 27, "fullName": "Colorado Avalanche", "teamCommonName": "Avalanche", "teamPlaceName": "Colorado"}
        ]
    }
    assert fs.nhl_rows(teams, fran) == [
        {
            "nhl_id": "32",
            "franchise_id": "27",
            "tri_code": "QUE",
            "full_name": "Quebec Nordiques",
            "franchise_full_name": "Colorado Avalanche",
            "franchise_common_name": "Avalanche",
        }
    ]


def test_ncaa_crosswalk_rows():
    assert fs.ncaa_rows({"113180": "2657"}) == [{"league": "cfb", "ncaa_id": "113180", "team_id": "2657"}]


def test_write_refuses_an_empty_snapshot(tmp_path):
    import pytest

    with pytest.raises(RuntimeError, match="espn_teams"):
        fs._write("espn_teams", [], ["a"], tmp_path)
    assert not list(tmp_path.glob("*.csv"))


def test_a_failed_run_leaves_the_committed_snapshots_untouched(tmp_path, monkeypatch):
    import argparse

    import pytest

    out = tmp_path / "data-raw"
    out.mkdir()
    (out / "espn_teams.csv").write_text("old\n")

    def boom(args, stage):
        fs._write("manifest_teams", [{"a": "1"}], ["a"], stage)  # an early source succeeded...
        raise RuntimeError("nhl: 404")  # ...a later one failed

    monkeypatch.setattr(fs, "OUT", out)
    monkeypatch.setattr(fs, "fetch_all", boom)
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", lambda self: argparse.Namespace())
    with pytest.raises(RuntimeError, match="nhl"):
        fs.main()
    assert (out / "espn_teams.csv").read_text() == "old\n"
    assert [f.name for f in out.glob("*.csv")] == ["espn_teams.csv"]


def test_manifest_teams_espn_identity_needs_a_numeric_id():
    rows = [
        _row("espn", "13", "Las Vegas Raiders", "2026-10-01"),
        _row("espn", "OAK", "OAK", "2026-10-01"),
        _row("fox", "bandits", "Birmingham Stallions", "2026-10-01", league="usfl"),
    ]
    assert fs.manifest_team_rows(rows) == [
        {"league": "nfl", "team_id": "13", "name": "Las Vegas Raiders", "program": "pro"},
        {"league": "usfl", "team_id": "bandits", "name": "Birmingham Stallions", "program": "pro"},
    ]


def test_manifest_teams_prefer_the_current_name_not_the_last_row():
    rows = [
        _row("hockeytech", "307", "Hartford Wolf Pack", "2026-10-01", league="ahl", valid_from="2013", valid_to=""),
        _row("hockeytech", "307", "Connecticut Whale", "2026-10-01", league="ahl", valid_from="2010", valid_to="2013"),
        _row(
            "hockeytech", "2", "Acadie-Bathurst Titan", "2026-10-01", league="qmjhl", valid_from="2011", valid_to="2020"
        ),
        _row(
            "hockeytech",
            "2",
            "Acadie-Bathurst, Titan",
            "2026-10-01",
            league="qmjhl",
            valid_from="2000",
            valid_to="2010",
        ),
    ]
    expected = {"307": "Hartford Wolf Pack", "2": "Acadie-Bathurst Titan"}
    for ordered in (rows, rows[::-1]):  # input order must not matter
        assert {r["team_id"]: r["name"] for r in fs.manifest_team_rows(ordered)} == expected


def test_sr_codes_are_written_aggregated_per_code():  # F5 (R47): never the per-season private capture
    sr = [
        {"league": "mlb", "site": "bref", "team_code": "KCR", "team_name": "Kansas City Royals", "season": "2025"},
        {"league": "mlb", "site": "bref", "team_code": "KCR", "team_name": "Kansas City Royals", "season": "1969"},
        {"league": "mlb", "site": "bref", "team_code": "FLA", "team_name": "Florida Marlins", "season": "1993"},
        {"league": "mlb", "site": "bref", "team_code": "FLA", "team_name": "Florida Marlins", "season": "2011"},
        {"league": "mlb", "site": "bref", "team_code": "FLA", "team_name": "Miami Marlins", "season": "2011"},
    ]
    assert sorted(fs.sr_code_rows(sr), key=lambda r: r["team_code"]) == [
        {"league": "mlb", "team_code": "FLA", "team_name": "Miami Marlins", "valid_from": 1993, "valid_to": 2011},
        {"league": "mlb", "team_code": "KCR", "team_name": "Kansas City Royals", "valid_from": 1969, "valid_to": 2025},
    ]


def test_snapshots_are_written_as_utf8_under_an_ascii_locale(tmp_path):
    import os
    import subprocess
    import sys

    tool = Path(__file__).parents[1] / "tools" / "fetch_sources.py"
    code = (
        "import importlib.util, pathlib, sys;"
        f"spec = importlib.util.spec_from_file_location('fs', r'{tool}');"
        "fs = importlib.util.module_from_spec(spec); spec.loader.exec_module(fs);"
        f"fs._write('t', [{{'league': 'cfb', 'name': 'San Jos\\u00e9 State'}}], ['league', 'name'], pathlib.Path(r'{tmp_path}'))"
    )
    env = {**os.environ, "LC_ALL": "C", "LANG": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"}
    subprocess.run([sys.executable, "-c", code], check=True, env=env)
    assert "San José State".encode() in (tmp_path / "t.csv").read_bytes()


def test_snapshots_use_lf_line_endings(tmp_path):
    fs._write("t", [{"a": "1"}, {"a": "2"}], ["a"], tmp_path)  # same call shape as Task 0's test
    assert b"\r\n" not in (tmp_path / "t.csv").read_bytes()


def test_mlbstats_history_keeps_runs_of_todays_franchises():
    def t(i, abbr, code, name):
        return {"id": i, "abbreviation": abbr, "teamCode": code, "name": name}

    seasons = {
        1967: [t(133, "KCA", "kc1", "Kansas City Athletics"), t(1520, "KCM", "kcm", "Kansas City Monarchs")],
        1968: [t(133, "OAK", "oak", "Oakland Athletics")],
        1969: [t(133, "OAK", "oak", "Oakland Athletics"), t(118, "KC", "kca", "Kansas City Royals")],
        1970: [t(133, "KCA", "kc1", "Kansas City Athletics"), t(118, "KC", "kca", "Kansas City Royals")],
    }  # 1970's KCA is made up: a code that comes back starts a new run
    rows = fs.mlbstats_history_rows(seasons)
    assert set(rows[0]) == set(fs.MLB_HISTORY_COLUMNS)
    assert sorted(tuple(r.values()) for r in rows) == [
        ("118", "KC", "kca", "Kansas City Royals", 1969, 1970),
        ("133", "KCA", "kc1", "Kansas City Athletics", 1967, 1967),
        ("133", "KCA", "kc1", "Kansas City Athletics", 1970, 1970),
        ("133", "OAK", "oak", "Oakland Athletics", 1968, 1969),
    ]  # the Monarchs, absent from the latest season, have no ESPN team


def test_espn_team_abbr_rows_skip_placeholders():
    team = {"team": {"id": "95", "abbreviation": "NCSU", "displayName": "NC State Wolfpack"}}
    assert fs.espn_team_abbr_row("ncaa_baseball", team) == {
        "league": "ncaa_baseball",
        "team_id": "95",
        "abbreviation": "NCSU",
        "display_name": "NC State Wolfpack",
        "valid_from": "",
        "valid_to": "",
    }
    assert fs.espn_team_abbr_row("ncaa_baseball", {"team": {"id": "1153", "displayName": "TBD"}}) is None


def test_espn_team_abbrs_cover_the_endpoint_leagues_and_the_listed_unlisted_teams(monkeypatch):
    seen = []

    class Response:
        def __init__(self, url):
            self.url = url

        def json(self):
            tid = self.url.rsplit("/", 1)[1]
            return {"team": {"id": tid, "abbreviation": {"95": "NCSU", "292": "RGV"}[tid], "displayName": tid}}

    def get(s, url, **kw):
        seen.append(url)
        return Response(url)

    monkeypatch.setattr(fs, "_get", get)
    espn = [{"league": "ncaa_baseball", "team_id": "95"}, {"league": "cfb", "team_id": "2"}]  # cfb: not a list league
    rows = fs.fetch_espn_team_abbrs(None, "site.api.espn.com", espn)
    assert [(r["league"], r["team_id"], r["abbreviation"]) for r in rows] == [
        ("ncaa_baseball", "95", "NCSU"),
        ("cfb", "292", "RGV"),  # ESPN_TEAM_ENDPOINT_TEAMS: UTRGV, which the cfb teams list omits
    ]
    assert seen == [
        "https://site.api.espn.com/apis/site/v2/sports/baseball/college-baseball/teams/95",
        "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/292",
    ]


def test_espn_season_abbr_rows_keep_each_code_with_its_seasons():
    def board(*teams):
        competitors = [{"team": {"id": i, "abbreviation": a, "displayName": n}} for i, a, n in teams]
        return {"events": [{"competitions": [{"competitors": competitors}]}]}

    boards = {
        2024: board(("112647", "ARL", "Arlington Renegades"), ("126075", "HOU", "Houston Roughnecks")),
        2025: board(("112647", "ARL", "Arlington Renegades"), ("126075", "HOU", "Houston Roughnecks")),
        2026: board(("112647", "DAL", "Dallas Renegades"), ("126075", "HOU", "Houston Gamblers")),
        2027: {"events": []},  # a season not played yet
    }
    assert sorted(tuple(r.values()) for r in fs.espn_season_abbr_rows("ufl", boards)) == [
        ("ufl", "112647", "ARL", "Arlington Renegades", 2024, 2025),
        ("ufl", "112647", "DAL", "Dallas Renegades", 2026, 2026),
        ("ufl", "126075", "HOU", "Houston Gamblers", 2026, 2026),
        ("ufl", "126075", "HOU", "Houston Roughnecks", 2024, 2025),
    ]


def test_unlisted_team_ids_are_the_scoreboard_ids_the_list_lacks():
    def board(*ids):
        return {"events": [{"competitions": [{"competitors": [{"team": {"id": i}} for i in ids]}]}]}

    boards = [board("2364", "24059"), board("48", "-2"), {"events": []}]
    assert fs.unlisted_team_ids(boards, {"2364"}) == ["24059", "48"]  # "-2" is ESPN's TBD placeholder


def test_espn_color_targets_are_espn_keyed_teams_the_list_gives_no_color():
    manifest = [
        _row("espn", "103", "Boston College Eagles", "2026-10-01", league="ncaa_mhockey"),  # listed, no color
        _row("espn", "13", "Las Vegas Raiders", "2026-10-01"),  # listed with a color
        _row("espn", "10", "Huracan", "2026-10-01", league="soccer"),  # not listed (soccer has no teams list)
        _row("ncaa.com", "77", "Some College", "2026-10-01", league="soccer"),  # an NCAA id, not ESPN's
        _row("espn", "88", "Twin", "2026-10-01", league="cfb"),
        _row("ncaa.com", "88", "Twin", "2026-10-01", league="cfb"),  # an id two sources key may be two teams
        _row("espn", "1", "England", "2026-10-01", league="cricket"),  # no ESPN cricket team endpoint
        _row("hockeytech", "7", "Kitchener Rangers", "2026-10-01", league="ohl"),
    ]
    listed = [
        {"league": "ncaa_mhockey", "team_id": "103", "color": "", "alternate_color": ""},
        {"league": "nfl", "team_id": "13", "color": "000000", "alternate_color": "a5acaf"},
    ]
    unlisted = [{"league": "ncaa_whockey", "team_id": "48", "color": "NULL", "alternate_color": "NULL"}]  # ESPN id
    assert fs.espn_color_targets(manifest, unlisted, listed) == [
        ("ncaa_mhockey", "103"),
        ("ncaa_whockey", "48"),
        ("soccer", "10"),
    ]


def _response(status, body):
    r = requests.Response()
    r.status_code, r._content, r.url = status, json.dumps(body).encode(), "https://x"
    return r


class _Session:
    """Answers each ".../sports/<sport>/<league>/teams/<id>" from a dict of (status, body) lists, last one repeating."""

    def __init__(self, answers):
        self.answers, self.asked = answers, []

    def get(self, url, timeout=None):
        key = url.split("/sports/", 1)[1]
        self.asked.append(key)
        queue = self.answers.get(key, [(400, {"code": 400})])
        return _response(*(queue.pop(0) if len(queue) > 1 else queue[0]))


def _team(team_id, color=None, alt=None, location="Boston College"):
    return {"team": {"id": team_id, "displayName": f"{location} Eagles", "location": location, "color": color,
                     "alternateColor": alt}}  # fmt: skip


def test_espn_colors_ask_other_college_sports_only_for_a_school_its_own_sport_knows():
    s = _Session(
        {
            "hockey/mens-college-hockey/teams/103": [(200, _team("103"))],  # no color in its own sport
            "football/college-football/teams/103": [(200, _team("103"))],
            "basketball/mens-college-basketball/teams/103": [(200, _team("103", "8c2232", "dbcca6"))],
            "basketball/womens-college-basketball/teams/103": [(200, _team("103", "ffffff"))],  # never asked
            "basketball/mens-college-basketball/teams/5": [(200, _team("5", "123456"))],  # 5 is unknown in hockey
        }
    )
    rows = fs.fetch_espn_colors(s, "h", [("ncaa_mhockey", "103"), ("ncaa_mhockey", "5")])
    assert [(r["espn_league"], r["color"]) for r in rows] == [("ncaa_mhockey", None), ("cfb", None), ("mbb", "8c2232")]
    assert not any(k.endswith("/5") and "hockey" not in k for k in s.asked)  # no own row: no other sport asked
    assert "basketball/womens-college-basketball/teams/103" not in s.asked


def test_espn_colors_never_take_another_teams_payload_and_skip_an_empty_answer():
    s = _Session(
        {
            "soccer/all/teams/10": [(200, _team("11", "c60000"))],  # ESPN answering with another id
            "soccer/all/teams/12": [(200, {})],  # site.web: 200 without a team for an unknown id
            "football/xfl/teams/112646": [(200, _team("112646", "c8102e", "a2aaad", "D.C."))],
        }
    )
    rows = fs.fetch_espn_colors(s, "h", [("soccer", "10"), ("soccer", "12"), ("xfl", "112646")])
    assert [(r["league"], r["team_id"], r["color"], r["alternate_color"]) for r in rows] == [
        ("xfl", "112646", "c8102e", "a2aaad")
    ]


def test_espn_colors_retry_a_passing_403_and_raise_a_lasting_one(monkeypatch):
    monkeypatch.setattr(fs.time, "sleep", lambda _: None)
    s = _Session({"soccer/all/teams/10": [(403, {}), (429, {}), (200, _team("10", "c60000", "000000"))]})
    assert fs.fetch_espn_colors(s, "h", [("soccer", "10")])[0]["color"] == "c60000"
    s = _Session({"soccer/all/teams/10": [(403, {})]})
    with pytest.raises(requests.HTTPError):  # a failed fetch is never recorded as a team without colors
        fs.fetch_espn_colors(s, "h", [("soccer", "10")])
    assert len(s.asked) == 5


def _logo(*bands, size=(100, 100)):
    """An RGBA image of vertical bands, each (share of the width, (r, g, b, a))."""
    from PIL import Image

    img = Image.new("RGBA", size, (0, 0, 0, 0))
    x = 0
    for share, color in bands:
        w = round(share * size[0])
        img.paste(color, (x, 0, x + w, size[1]))
        x += w
    return img


def test_logo_colors_rank_colors_before_neutrals_and_skip_edges_and_shades():
    red, navy, gold, black, white = (200, 16, 46, 255), (12, 35, 64, 255), (255, 182, 18, 255), (0, 0, 0, 255), (
        255, 255, 255, 255)  # fmt: skip
    # mostly white fill and a black outline, with red and navy: the colors win, the larger first
    assert fs.logo_colors(_logo((0.4, white), (0.2, black), (0.25, red), (0.15, navy))) == ("#c8102e", "#0c2340")
    # one color: the dark neutral before white
    assert fs.logo_colors(_logo((0.5, white), (0.2, black), (0.3, gold))) == ("#ffb612", "#000000")
    # a shade of the primary is the same color; a 1% sliver is an edge blend; transparent pixels are no color
    shade = (210, 26, 56, 255)
    assert fs.logo_colors(_logo((0.6, red), (0.3, shade), (0.01, navy), (0.09, (0, 255, 0, 10)))) == ("#c8102e", None)
    # black and white only
    assert fs.logo_colors(_logo((0.7, white), (0.3, black))) == ("#000000", "#ffffff")
    assert fs.logo_colors(_logo((1.0, (0, 0, 0, 0)))) is None


def test_espn_stand_in_colors_are_not_a_teams():
    assert not fs.espn_has_color("000000", None) and not fs.espn_has_color("#000000", "NULL")
    assert not fs.espn_has_color("000000", "C60000") and not fs.espn_has_color("000000", "000000")
    assert not fs.espn_has_color("", "ffffff") and not fs.espn_has_color("zzzzzz", None)
    assert fs.espn_has_color("000000", "ffffff") and fs.espn_has_color("c60000", None)
    listed = [{"league": "cfb", "team_id": "2", "color": "000000", "alternate_color": ""}]  # a stand-in: a target
    manifest = [_row("espn", "2", "Campbell Fighting Camels", "2026-10-01", league="cfb")]
    assert fs.espn_color_targets(manifest, [], listed) == [("cfb", "2")]


def test_espn_colors_never_ask_college_baseball_ids_in_another_sport():  # its ids are not the school's
    s = _Session(
        {
            "baseball/college-baseball/teams/102": [(200, _team("102"))],  # known, no color of its own
            "basketball/mens-college-basketball/teams/102": [(200, _team("102", "ce0e2d"))],
        }
    )
    assert [r["espn_league"] for r in fs.fetch_espn_colors(s, "h", [("ncaa_baseball", "102")])] == ["ncaa_baseball"]
    assert s.asked == ["baseball/college-baseball/teams/102"]

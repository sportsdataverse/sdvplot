import importlib.util
from pathlib import Path

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

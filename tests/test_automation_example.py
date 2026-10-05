"""examples/automation/sdvplot_social.py, offline: the CLI, the manifest, image sizes, the offseason fallbacks, the
player-of-the-game rules, the dry-run and the Bluesky request sequence (a fake HTTP session; nothing is sent)."""

import datetime as dt
import importlib.util
import json
import random
from pathlib import Path

import polars as pl
import pytest
from PIL import Image

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("sdvplot_social", ROOT / "examples" / "automation" / "sdvplot_social.py")
social = importlib.util.module_from_spec(spec)
spec.loader.exec_module(social)

DAY = dt.date(2026, 9, 27)
TODAY = dt.date.today().isoformat()


# ---------------------------------------------------------------------------------------------------------------------
# CLI


def test_each_subcommand_parses_with_its_defaults():
    lb = social.parse_args(["leaderboard", "--league", "nfl"])
    assert (lb.command, lb.size, lb.top, lb.stat, lb.season, lb.out) == (
        "leaderboard",
        "square",
        None,
        None,
        None,
        "out",
    )
    gd = social.parse_args(["gameday", "--league", "nba", "--date", "2026-09-27", "--max-games", "3"])
    assert (gd.date, gd.max_games) == (DAY, 3)
    assert social.parse_args(["gameday", "--league", "nba"]).date == dt.date.today() - dt.timedelta(days=1)
    po = social.parse_args(["post", "--manifest", "m.json"])
    assert (po.network, po.post) == ("bluesky", False)  # dry-run unless --post


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["leaderboard"],
        ["leaderboard", "--league", "xfl"],
        ["leaderboard", "--league", "nfl", "--top", "0"],
        ["leaderboard", "--league", "nfl", "--size", "tall"],
        ["gameday", "--league", "nfl", "--date", "Sunday"],
        ["gameday", "--league", "nfl", "--max-games", "0"],
        ["post"],
        ["post", "--manifest", "m.json", "--network", "x"],
    ],
)
def test_bad_arguments_exit_with_usage(argv, capsys):
    with pytest.raises(SystemExit) as e:
        social.parse_args(argv)
    assert e.value.code == 2
    assert "usage:" in capsys.readouterr().err


# ---------------------------------------------------------------------------------------------------------------------
# gameday and leaderboard with small frames in place of the ESPN data


def _game(game_id, away, home, away_score, home_score):
    names = {"13": ("LV", "Las Vegas", "Raiders"), "14": ("LAR", "Los Angeles", "Rams")}
    game = {"game_id": game_id, "status": "Final", "phase": "regular-season", "note": ""}
    for side, team, score in (("away", away, away_score), ("home", home, home_score)):
        abbr, location, name = names[team]
        game |= {f"{side}_id": team, f"{side}_abbr": abbr, f"{side}_location": location, f"{side}_name": name,
                 f"{side}_score": score, f"{side}_rank": None}  # fmt: skip
    return game


def _box(game_id):
    rows = [
        {"game_id": game_id, "team_id": "13", "athlete_id": "3139477", "has_headshot": True, "name": "Star Passer",
         "position": "QB", "score": 30.5, "lines": ["24/31 · 300 PASS YDS · 3 TD"]},
        {"game_id": game_id, "team_id": "13", "athlete_id": "4241479", "has_headshot": True, "name": "Backup",
         "position": "RB", "score": 4.0, "lines": ["5 CAR · 20 RUSH YDS"]},
        {"game_id": game_id, "team_id": "14", "athlete_id": "1", "has_headshot": False, "name": "Loser Great",
         "position": "WR", "score": 99.0, "lines": ["15 REC · 300 REC YDS"]},
    ]  # fmt: skip
    return pl.DataFrame(rows, schema=social.BOX_SCHEMA)


@pytest.fixture
def gameday_data(monkeypatch):
    games = pl.DataFrame([_game("1", "14", "13", 17, 24), _game("2", "13", "14", 10, 3)])
    note = "No NFL games finished on Monday, Sep 28, 2026, so these are from Sunday, Sep 27, 2026."
    monkeypatch.setattr(social, "fetch_games", lambda league, day: (DAY, games, note))
    monkeypatch.setattr(social, "fetch_box", lambda league, game_id: _box(game_id))
    return note


def _manifest(out):
    manifest = json.loads((out / TODAY / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == 1 and manifest["date"] == TODAY
    for post in manifest["posts"]:
        assert set(post) == {"thread", "league", "kind", "caption", "hashtags", "images"}
        assert 1 <= len(post["images"]) <= 4 and post["hashtags"] == ["NFL", "sdvplot"]
        for image in post["images"]:
            assert set(image) == {"path", "alt", "width", "height"} and image["alt"]
            with Image.open(out / TODAY / image["path"]) as im:
                assert im.size == (image["width"], image["height"])
    return manifest


def test_gameday_writes_score_cards_a_player_card_and_the_manifest(
    tmp_path, gameday_data, mark_images, headshot_images
):
    assert social.main(["gameday", "--league", "nfl", "--date", "2026-09-28", "--out", str(tmp_path)]) == 0
    (post,) = _manifest(tmp_path)["posts"]
    assert (post["thread"], post["kind"]) == ("nfl-20260927", "gameday")
    sizes = [(i["width"], i["height"]) for i in post["images"]]
    assert sizes == [(1080, 1080), (1200, 675), (1200, 675)]  # the player card first, then a card per game
    assert post["images"][0]["path"] == "nfl-20260927-player-of-the-game.png"
    assert [i["path"] for i in post["images"][1:]] == ["nfl-20260927-lar-at-lv.png", "nfl-20260927-lv-at-lar.png"]
    # the best score on a WINNING team (the loser's 99 does not count), and the offseason note, are in the caption
    assert "Player of the game: Star Passer" in post["caption"] and gameday_data in post["caption"]
    assert "Los Angeles Rams 17, Las Vegas Raiders 24" in post["images"][1]["alt"]


def test_a_rerun_replaces_its_thread_and_keeps_the_others(tmp_path, gameday_data, mark_images, headshot_images):
    out = tmp_path / TODAY
    out.mkdir()
    other = {"thread": "nba-leaders-points", "league": "nba", "kind": "leaderboard", "caption": "c", "hashtags": [],
             "images": []}  # fmt: skip
    stale = {**other, "thread": "nfl-20260927", "league": "nfl", "kind": "gameday"}
    (out / "manifest.json").write_text(json.dumps({"version": 1, "date": TODAY, "posts": [other, stale]}))
    for _ in range(2):
        social.main(["gameday", "--league", "nfl", "--out", str(tmp_path)])
    posts = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["posts"]
    assert [p["thread"] for p in posts] == ["nba-leaders-points", "nfl-20260927"]
    assert posts[1]["images"]  # the fresh post, not the stale one


def test_more_than_four_images_thread_over_several_posts(tmp_path, monkeypatch, mark_images, headshot_images):
    games = pl.DataFrame([{**_game(str(i), "14", "13", 17, 24), "phase": "post-season"} for i in range(5)])
    monkeypatch.setattr(social, "fetch_games", lambda league, day: (DAY, games, None))
    monkeypatch.setattr(social, "fetch_box", lambda league, game_id: _box(game_id))
    social.main(["gameday", "--league", "nfl", "--out", str(tmp_path)])
    posts = _manifest(tmp_path)["posts"]
    assert [len(p["images"]) for p in posts] == [4, 2] and {p["thread"] for p in posts} == {"nfl-20260927"}
    assert posts[1]["caption"] == "More NFL final scores, Sunday, Sep 27, 2026 (2/2)."
    assert posts[0]["caption"].startswith("NFL postseason final scores, Sunday, Sep 27, 2026. Player of")


LEADERS = pl.DataFrame(
    {"rank": [1, 2, 2], "athlete_id": ["3139477", "4241479", "9"], "has_headshot": [True, True, False],
     "name": ["Star Passer", "Second", "Tied Second"], "position": ["QB", "QB", "QB"], "team_id": ["13", "14", "14"],
     "display": ["1,882", "999", "999"]},
    schema=social.LEADERS_SCHEMA,
)  # fmt: skip
META = {"season": 2025, "stat": "passingYards", "stat_label": "Passing Yards", "abbr": "YDS", "to_date": False,
        "note": "No 2026 regular-season leaders yet, so these are 2025."}  # fmt: skip


def test_leaderboard_manifest_names_the_season_and_the_fallback(tmp_path, monkeypatch):
    seen = {}

    def fake_image(frame, meta, league, size, today, path):
        seen["size"] = size
        w, h = social.SIZES[size]
        Image.new("RGB", (w, h)).save(path)
        return {"path": path.name, "width": w, "height": h}

    monkeypatch.setattr(social, "fetch_leaders", lambda league, stat, season, top: (LEADERS.head(top), META))
    monkeypatch.setattr(social, "leaderboard_image", fake_image)
    assert social.main(["leaderboard", "--league", "nfl", "--size", "landscape", "--out", str(tmp_path)]) == 0
    (post,) = _manifest(tmp_path)["posts"]
    assert seen["size"] == "landscape" and post["thread"] == "nfl-leaders-passingyards-landscape"
    assert post["images"][0]["path"] == "nfl-leaders-passingyards-landscape.png"
    assert post["caption"].startswith("NFL Passing Yards leaders, 2025 regular season (final): Star Passer leads")
    assert META["note"] in post["caption"]
    assert "1. Star Passer 1,882; 2. Second 999; 2. Tied Second 999" in post["images"][0]["alt"]


@pytest.mark.render
def test_leaderboard_image_is_a_square_social_png(tmp_path, cache, manifest, headshot_images):
    from tests.test_gt_export_render import _chrome_starts

    if not _chrome_starts():
        pytest.skip("needs Chrome or Chromium (nokap could not start one)")
    image = social.leaderboard_image(LEADERS, META, "nfl", "square", DAY, tmp_path / "t.png")
    assert (image["width"], image["height"]) == (1080, 1080)
    with Image.open(tmp_path / "t.png") as im:
        assert im.size == (1080, 1080)


def test_no_data_is_an_error_message_not_a_traceback(monkeypatch, capsys):
    def nothing(*args):
        raise social.NoData("no finished nfl games on or before 2026-09-27")

    monkeypatch.setattr(social, "fetch_games", nothing)
    assert social.main(["gameday", "--league", "nfl"]) == 1
    assert capsys.readouterr().err == "error: no finished nfl games on or before 2026-09-27\n"


# ---------------------------------------------------------------------------------------------------------------------
# Offseason-safe data: the most recent date or season with data


def _scoreboard(events=(), calendar=(), start="2025-09-01"):
    return {
        "leagues": [{"season": {"startDate": f"{start}T07:00Z"}, "calendar": list(calendar)}],
        "events": list(events),
    }


def _event(game_id, completed=True, name="STATUS_FINAL"):
    teams = [{"homeAway": side, "score": str(s), "team": {"id": t, "abbreviation": a, "location": loc, "name": n},
              "curatedRank": {"current": r}}
             for side, s, t, a, loc, n, r in (("away", 3, "14", "LAR", "Los Angeles", "Rams", 99),
                                              ("home", 7, "13", "LV", "Las Vegas", "Raiders", 4))]  # fmt: skip
    status = {"type": {"completed": completed, "name": name, "shortDetail": "Final/OT"}}
    return {
        "id": game_id,
        "season": {"slug": "post-season"},
        "competitions": [{"status": status, "competitors": teams}],
    }


def test_finals_keeps_finished_games_and_flattens_them():
    raw = _scoreboard([_event("1"), _event("2", completed=False), _event("3", name="STATUS_CANCELED")])
    (game,) = social.finals(raw)
    assert game["game_id"] == "1" and (game["away_score"], game["home_score"]) == (3, 7)
    assert (game["away_rank"], game["home_rank"], game["status"], game["phase"]) == (None, 4, "Final/OT", "post-season")


def test_fetch_games_walks_back_through_the_calendar(monkeypatch):
    calendar = ["2026-06-01T07:00Z", "2026-06-05T07:00Z", "2026-06-08T07:00Z", "2026-07-01T07:00Z"]
    payloads = {
        dt.date(2026, 6, 20): _scoreboard(calendar=calendar),  # the requested day: nothing finished
        dt.date(2026, 6, 8): _scoreboard([_event("9", completed=False)], calendar),  # postponed
        dt.date(2026, 6, 5): _scoreboard([_event("7")], calendar),
    }
    asked = []
    monkeypatch.setattr(social, "scoreboard", lambda league, day: asked.append(day) or payloads[day])
    day, games, note = social.fetch_games("nba", dt.date(2026, 6, 20))
    assert day == dt.date(2026, 6, 5) and games["game_id"].to_list() == ["7"]
    assert asked == [dt.date(2026, 6, 20), dt.date(2026, 6, 8), dt.date(2026, 6, 5)]
    assert note == "No NBA games finished on Saturday, Jun 20, 2026, so these are from Friday, Jun 5, 2026."


def test_fetch_games_steps_back_a_season_and_reads_football_weeks(monkeypatch):
    weeks = [{"label": "Postseason", "entries": [{"startDate": "2026-02-02T08:00Z", "endDate": "2026-02-10T07:59Z"}]}]
    payloads = {
        dt.date(2026, 8, 1): _scoreboard(calendar=[{"label": "Week 1", "entries": [
            {"startDate": "2026-09-08T07:00Z", "endDate": "2026-09-15T06:59Z"}]}], start="2026-07-01"),
        dt.date(2026, 6, 30): _scoreboard(calendar=weeks),  # the season before
        dt.date(2026, 2, 8): _scoreboard([_event("sb")], weeks),
    }  # fmt: skip
    monkeypatch.setattr(social, "scoreboard", lambda league, day: payloads.get(day, _scoreboard(calendar=weeks)))
    day, games, note = social.fetch_games("nfl", dt.date(2026, 8, 1))
    assert day == dt.date(2026, 2, 8) and games["game_id"].to_list() == ["sb"] and "Feb 8, 2026" in note


def test_fetch_games_gives_up_with_no_data(monkeypatch):
    monkeypatch.setattr(social, "scoreboard", lambda league, day: _scoreboard())
    with pytest.raises(social.NoData, match="no finished nfl games"):
        social.fetch_games("nfl", DAY)


def test_fetch_leaders_falls_back_a_season_and_says_so(monkeypatch):
    from sportsdataverse.errors import NoDataError

    ref = "http://x/seasons/{y}/{kind}/{i}?lang=en"

    def leaders(season, season_type, return_parsed):
        if season == 2027:
            raise NoDataError("none yet")
        rows = [
            {
                "value": v,
                "displayValue": d,
                "athlete": {"$ref": ref.format(y=season, kind="athletes", i=i)},
                "team": {"$ref": ref.format(y=season, kind="teams", i=t)},
            }
            for v, d, i, t in ((33.48, "33.5", "11", "13"), (31.1, "31.1", "12", "14"), (31.1, "31.1", "13", "14"))
        ]
        return {"categories": [{"name": "pointsPerGame", "displayName": "Points Per Game", "abbreviation": "PTS",
                                "leaders": rows}]}  # fmt: skip

    def player_core(athlete_id, return_parsed):
        return {"displayName": f"Player {athlete_id}", "position": {"abbreviation": "G"},
                **({"headshot": {"href": "x"}} if athlete_id != "13" else {})}  # fmt: skip

    fns = {"season_type_leaders": leaders, "player_core": player_core}
    monkeypatch.setattr(social, "espn", lambda league, name: fns[name])
    monkeypatch.setattr(social, "current_season", lambda league: (2027, False))
    frame, meta = social.fetch_leaders("nba", "pointspergame", top=3)
    assert frame.schema == pl.Schema(social.LEADERS_SCHEMA)
    assert frame["rank"].to_list() == [1, 2, 2] and frame["team_id"].to_list() == ["13", "14", "14"]
    assert frame["has_headshot"].to_list() == [True, True, False]
    assert (meta["season"], meta["stat"], meta["to_date"]) == (2026, "pointsPerGame", False)
    assert meta["note"] == "No 2026-27 regular-season leaders yet, so these are 2025-26."
    with pytest.raises(social.NoData, match="categories: pointsPerGame"):
        social.fetch_leaders("nba", "goals")


# ---------------------------------------------------------------------------------------------------------------------
# Player-of-the-game rules


def test_the_player_of_the_game_rules():
    hoops = {"points": "30", "fieldGoalsMade-fieldGoalsAttempted": "11-20", "freeThrowsMade-freeThrowsAttempted": "6-8",
             "offensiveRebounds": "2", "defensiveRebounds": "8", "rebounds": "10", "steals": "3", "assists": "5",
             "blocks": "1", "fouls": "2", "turnovers": "4"}  # fmt: skip
    score, lines = social.basketball(hoops)
    assert score == pytest.approx(30 + 4.4 - 14 - 0.8 + 1.4 + 2.4 + 3 + 3.5 + 0.7 - 0.8 - 4)
    assert lines == ["30 PTS · 10 REB · 5 AST · 3 STL"]
    qb = {"passing.completions/passingAttempts": "20/30", "passing.passingYards": "250",
          "passing.passingTouchdowns": "2", "passing.interceptions": "1", "rushing.rushingAttempts": "3",
          "rushing.rushingYards": "8", "rushing.rushingTouchdowns": "0"}  # fmt: skip
    assert social.football(qb) == (pytest.approx(10 + 8 - 2 + 0.8), ["20/30 · 250 PASS YDS · 2 TD · 1 INT"])
    goalie = {"goalies.saves": "30", "goalies.goalsAgainst": "1", "goalies.savePct": ".968"}
    assert social.hockey(goalie) == (pytest.approx(2.25), ["30 SAVES · 1 GA · .968 SV%"])
    pitcher = {"pitching.fullInnings.partInnings": "6.2", "pitching.strikeouts": "8", "pitching.earnedRuns": "1",
               "pitching.hits": "4", "pitching.walks": "2"}  # fmt: skip
    assert social.baseball(pitcher)[0] == pytest.approx(20 / 2 + 4 - 1.5 - 3)  # 6.2 innings is 20 outs
    assert social.num({"x": "7-15"}, "x", 1) == 15 and social.num({}, "x") == 0


# ---------------------------------------------------------------------------------------------------------------------
# post: dry-run, limits and the Bluesky request sequence


def _post_manifest(tmp_path, n_images=5, caption="NFL final scores, Sunday, Sep 27, 2026."):
    images = []
    for i in range(n_images):
        Image.new("RGB", (120, 68), (i * 40, 30, 30)).save(tmp_path / f"{i}.png")
        images.append({"path": f"{i}.png", "alt": f"card {i}", "width": 120, "height": 68})
    posts = [{"thread": "nfl-20260927", "league": "nfl", "kind": "gameday", "caption": caption if i == 0 else "More",
              "hashtags": ["NFL", "sdvplot"], "images": images[i : i + 4]} for i in range(0, n_images, 4)]  # fmt: skip
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"version": 1, "date": TODAY, "posts": posts}))
    return path


class FakeResponse:
    def __init__(self, status, body, headers=None):
        self.status_code, self.body, self.headers = status, body, headers or {}

    def json(self):
        if self.body is None:
            raise ValueError("no JSON")
        return self.body


class FakeHTTP:
    """Answers each XRPC method from a queue of responses and records every request."""

    def __init__(self, **queues):
        self.queues, self.calls = queues, []

    def post(self, url, headers=None, timeout=None, json=None, data=None):
        method = url.rsplit("/", 1)[1]
        self.calls.append({"method": method, "url": url, "headers": headers, "json": json, "data": data})
        queue = self.queues[method]
        return queue.pop(0) if len(queue) > 1 else queue[0]


def _bluesky_http(**overrides):
    queues = {
        "com.atproto.server.createSession": [FakeResponse(200, {"accessJwt": "jwt-token", "did": "did:plc:me"})],
        "com.atproto.repo.uploadBlob": [FakeResponse(200, {"blob": {"$type": "blob", "ref": "b"}})],
        "com.atproto.repo.createRecord": [FakeResponse(200, {"uri": "at://me/1", "cid": "c1"}),
                                          FakeResponse(200, {"uri": "at://me/2", "cid": "c2"})],
    }  # fmt: skip
    return FakeHTTP(**{**queues, **overrides})


@pytest.fixture
def creds(monkeypatch):
    monkeypatch.setenv("BSKY_HANDLE", "me.bsky.social")
    monkeypatch.setenv("BSKY_APP_PASSWORD", "app-secret-1234")
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("BSKY_SERVICE", raising=False)


def test_dry_run_prints_the_posts_and_sends_nothing(tmp_path, monkeypatch, capsys, creds):
    def no_network(*args, **kwargs):
        raise AssertionError("a dry-run must not open a session")

    monkeypatch.setattr(social.requests, "Session", no_network)
    assert social.main(["post", "--manifest", str(_post_manifest(tmp_path))]) == 0
    out = capsys.readouterr().out
    assert out.startswith(f"[dry-run] 2 post(s) from {tmp_path / 'manifest.json'}; nothing sent")
    assert "NFL final scores, Sunday, Sep 27, 2026.\n\n#NFL #sdvplot" in out
    assert "  [image] 0.png 120x68" in out and "    alt: card 4" in out
    assert "app-secret" not in out


def test_bluesky_posts_a_thread_with_alt_text_and_hashtag_facets(tmp_path, capsys, creds):
    http = _bluesky_http()
    social.run_post(social.parse_args(["post", "--manifest", str(_post_manifest(tmp_path)), "--post"]), session=http)
    methods = [c["method"].rsplit(".", 1)[1] for c in http.calls]
    assert methods == ["createSession"] + ["uploadBlob"] * 4 + ["createRecord", "uploadBlob", "createRecord"]
    login = http.calls[0]
    assert login["url"] == "https://bsky.social/xrpc/com.atproto.server.createSession"
    assert login["json"] == {"identifier": "me.bsky.social", "password": "app-secret-1234"}
    assert "Authorization" not in login["headers"]
    assert all(c["headers"]["Authorization"] == "Bearer jwt-token" for c in http.calls[1:])
    upload = http.calls[1]
    assert upload["headers"]["Content-Type"] == "image/png" and upload["data"] == (tmp_path / "0.png").read_bytes()
    first, second = (c["json"] for c in http.calls if c["method"].endswith("createRecord"))
    assert (first["repo"], first["collection"]) == ("did:plc:me", "app.bsky.feed.post")
    record = first["record"]
    assert record["text"] == "NFL final scores, Sunday, Sep 27, 2026.\n\n#NFL #sdvplot"
    start = len(record["text"].encode()) - len("#NFL #sdvplot")
    assert record["facets"][0] == {"index": {"byteStart": start, "byteEnd": start + 4},
                                   "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": "NFL"}]}  # fmt: skip
    images = record["embed"]["images"]
    assert record["embed"]["$type"] == "app.bsky.embed.images" and len(images) == 4
    assert images[0] == {"image": {"$type": "blob", "ref": "b"}, "alt": "card 0",
                         "aspectRatio": {"width": 120, "height": 68}}  # fmt: skip
    assert "reply" not in record
    root = {"uri": "at://me/1", "cid": "c1"}
    assert second["record"]["reply"] == {"root": root, "parent": root}  # the thread's second post replies to the first
    out = capsys.readouterr()
    assert "posted at://me/1" in out.out and "app-secret" not in out.out + out.err and "jwt-token" not in out.out


def test_bluesky_waits_out_a_rate_limit_then_retries(tmp_path, monkeypatch, creds):
    slept = []
    monkeypatch.setattr(social.time, "sleep", slept.append)
    monkeypatch.setattr(social.time, "time", lambda: 1000.0)
    limited = FakeResponse(429, {"error": "RateLimitExceeded"}, {"ratelimit-reset": "1012"})
    ok = FakeResponse(200, {"blob": {"ref": "b"}})
    http = _bluesky_http(**{"com.atproto.repo.uploadBlob": [limited, ok]})
    social.run_post(social.parse_args(["post", "--manifest", str(_post_manifest(tmp_path, 1)), "--post"]), http)
    assert slept == [12.0]
    assert [c["method"] for c in http.calls].count("com.atproto.repo.uploadBlob") == 2


def test_bluesky_errors_name_the_call_but_never_the_credentials(tmp_path, capsys, creds, monkeypatch):
    http = _bluesky_http(**{"com.atproto.server.createSession": [
        FakeResponse(401, {"error": "AuthenticationRequired", "message": "Invalid identifier or password"})]})  # fmt: skip
    monkeypatch.setattr(social.requests, "Session", lambda: http)
    assert social.main(["post", "--manifest", str(_post_manifest(tmp_path, 1)), "--post"]) == 1
    err = capsys.readouterr().err
    assert err == (
        "error: com.atproto.server.createSession: HTTP 401 AuthenticationRequired Invalid identifier or password\n"
    )
    with pytest.raises(social.PostError, match=r"uploadBlob: HTTP 502$"):  # a body that is not JSON
        social.run_post(
            social.parse_args(["post", "--manifest", str(_post_manifest(tmp_path, 1)), "--post"]),
            _bluesky_http(**{"com.atproto.repo.uploadBlob": [FakeResponse(502, None)]}),
        )


def test_posting_needs_credentials_and_never_runs_in_sdvplots_ci(tmp_path, monkeypatch, capsys, creds):
    manifest = str(_post_manifest(tmp_path, 1))
    monkeypatch.setattr(social.requests, "Session", lambda: pytest.fail("no session may open"))
    monkeypatch.setenv("GITHUB_REPOSITORY", "sportsdataverse/sdvplot")
    assert social.main(["post", "--manifest", manifest, "--post"]) == 1
    assert "refusing to post from sportsdataverse/sdvplot's own CI" in capsys.readouterr().err
    monkeypatch.delenv("GITHUB_REPOSITORY")
    monkeypatch.delenv("BSKY_APP_PASSWORD")
    assert social.main(["post", "--manifest", manifest, "--post"]) == 1
    assert "set BSKY_HANDLE and BSKY_APP_PASSWORD" in capsys.readouterr().err


def test_posts_bluesky_would_refuse_are_caught_before_sending(tmp_path):
    path = _post_manifest(tmp_path, 4)
    manifest = json.loads(path.read_text())
    post = manifest["posts"][0]
    with pytest.raises(ValueError, match="has 5 images"):
        social.check_post({**post, "images": post["images"] + post["images"][:1]}, tmp_path)
    with pytest.raises(ValueError, match="has no alt text"):
        social.check_post({**post, "images": [{**post["images"][0], "alt": ""}]}, tmp_path)
    with pytest.raises(ValueError, match="is not in"):
        social.check_post({**post, "images": [{**post["images"][0], "path": "gone.png"}]}, tmp_path)
    long = {**post, "caption": "é" * 400}  # a long caption is shortened to fit, keeping the hashtags
    text = social.post_text(long)
    assert social.graphemes(text) <= 300 and text.endswith("…\n\n#NFL #sdvplot")
    social.check_post(long, tmp_path)
    assert social.graphemes("é\U0001f44d️") == 2  # a combining accent and a variation selector add nothing


def test_an_image_over_bluesky_s_limit_is_sent_as_jpeg(tmp_path, monkeypatch):
    path = tmp_path / "big.png"
    Image.frombytes("RGB", (256, 256), random.Random(1).randbytes(256 * 256 * 3)).save(path)  # noise: a big PNG
    assert social.image_bytes(path) == (path.read_bytes(), "image/png")
    monkeypatch.setattr(social, "MAX_BLOB", path.stat().st_size // 2)
    data, mime = social.image_bytes(path)
    assert mime == "image/jpeg" and len(data) <= social.MAX_BLOB and data[:2] == bytes([0xFF, 0xD8])
    monkeypatch.setattr(social, "MAX_BLOB", 100)
    with pytest.raises(ValueError, match="over 1 MB even as a JPEG"):
        social.image_bytes(path)

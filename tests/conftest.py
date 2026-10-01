"""A small, hand-written team index every test runs against, so tests never touch the real generated index."""

from pathlib import Path

import polars as pl
import pytest
import requests

from sdvplot import _cache, _index, _manifest

TEAMS = [
    # league, team_id, abbr, name, short_name, location, program, conference_id, conference, primary, secondary, color_source
    (
        "nfl",
        "13",
        "LV",
        "Las Vegas Raiders",
        "Raiders",
        "Las Vegas",
        "pro",
        "nfl:afc-west",
        "AFC West",
        "#000000",
        "#a5acaf",
        "nflverse",
    ),
    (
        "nfl",
        "14",
        "LAR",
        "Los Angeles Rams",
        "Rams",
        "Los Angeles",
        "pro",
        "nfl:nfc-west",
        "NFC West",
        "#003594",
        "#ffa300",
        "nflverse",
    ),
    (
        "nfl",
        "24",
        "LAC",
        "Los Angeles Chargers",
        "Chargers",
        "Los Angeles",
        "pro",
        "nfl:afc-west",
        "AFC West",
        "#0080c6",
        "#ffc20e",
        "nflverse",
    ),
    (
        "mlb",
        "7",
        "KC",
        "Kansas City Royals",
        "Royals",
        "Kansas City",
        "pro",
        "mlb:al-central",
        "AL Central",
        "#004687",
        "#bd9b60",
        "espn",
    ),
    (
        "cfb",
        "333",
        "ALA",
        "Alabama Crimson Tide",
        "Crimson Tide",
        "Alabama",
        "football",
        "cfb:sec",
        "Southeastern Conference",
        "#9e1b32",
        "#ffffff",
        "espn",
    ),
    (
        "cfb",
        "2390",
        "MIA",
        "Miami Hurricanes",
        "Hurricanes",
        "Miami",
        "football",
        "cfb:acc",
        "Atlantic Coast Conference",
        "#005030",
        "#f47321",
        "espn",
    ),
    (
        "cfb",
        "193",
        "M-OH",
        "Miami (OH) RedHawks",
        "RedHawks",
        "Miami (OH)",
        "football",
        "cfb:mac",
        "Mid-American Conference",
        "#c3142d",
        "#ffffff",
        "espn",
    ),
    (
        "ohl",
        "7",
        "KIT",
        "Kitchener Rangers",
        "Rangers",
        "Kitchener",
        "junior",
        None,
        None,
        "#4e79a7",
        "#f28e2b",
        "fallback",
    ),
]
ALIASES = [
    # league, id_system, value, team_id, valid_from, valid_to
    ("nfl", "team_id", "13", "13", None, None),
    ("nfl", "team_id", "14", "14", None, None),
    ("nfl", "team_id", "24", "24", None, None),
    ("nfl", "espn_abbr", "LV", "13", None, None),
    ("nfl", "espn_abbr", "LAR", "14", None, None),
    ("nfl", "espn_abbr", "LAC", "24", None, None),
    ("nfl", "nflverse", "OAK", "13", None, 2019),
    ("nfl", "nflverse", "LV", "13", 2020, None),
    ("nfl", "nflverse", "SD", "24", None, 2016),
    ("nfl", "nflverse", "LAC", "24", 2017, None),
    ("nfl", "nflverse", "STL", "14", None, 2015),
    ("nfl", "nflverse", "LA", "14", 2016, None),
    ("nfl", "nflverse", "LA", "13", 1982, 1994),  # the Los Angeles Raiders: "LA" needs a season
    ("nfl", "mark", "espn:13", "13", None, None),
    ("nfl", "mark", "nflverse:OAK", "13", None, None),
    ("nfl", "mark", "nflverse:LV", "13", None, None),
    ("nfl", "mark", "wayback:14", "14", None, None),
    ("nfl", "mark", "espn:14", "14", None, None),
    ("nfl", "name", "Las Vegas Raiders", "13", None, None),
    ("nfl", "name", "Los Angeles Rams", "14", None, None),
    ("mlb", "team_id", "7", "7", None, None),
    ("mlb", "espn_abbr", "KC", "7", None, None),
    ("mlb", "fangraphs", "KCR", "7", None, None),
    ("mlb", "mark", "espn:7", "7", None, None),
    ("cfb", "team_id", "333", "333", None, None),
    ("cfb", "team_id", "2390", "2390", None, None),
    ("cfb", "team_id", "193", "193", None, None),
    ("cfb", "cfbd", "Alabama", "333", None, None),
    ("cfb", "cfbd", "Miami", "2390", None, None),
    ("cfb", "cfbd", "Miami (OH)", "193", None, None),
    ("cfb", "name", "Miami", "2390", None, None),
    ("cfb", "name", "Miami", "193", None, None),  # ambiguous on purpose
    ("ohl", "team_id", "7", "7", None, None),
    ("ohl", "hockeytech", "7", "7", None, None),
]


@pytest.fixture(autouse=True)
def fixture_index(tmp_path, monkeypatch):
    data = tmp_path / "index"
    data.mkdir()
    pl.DataFrame(TEAMS, schema=list(_index.TEAM_SCHEMA), orient="row").cast(_index.TEAM_SCHEMA).write_parquet(
        data / "teams.parquet"
    )
    pl.DataFrame(ALIASES, schema=list(_index.ALIAS_SCHEMA), orient="row").cast(_index.ALIAS_SCHEMA).write_parquet(
        data / "aliases.parquet"
    )
    (data / "INDEX_VERSION").write_text("fixture\n")
    monkeypatch.setattr(_index, "data_dir", lambda: data)
    _index.reload_index()
    yield data
    _index.reload_index()


class FakeResponse:
    def __init__(self, status=200, body=b"", headers=None):
        self.status_code, self.content, self.headers = status, body, headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            err = requests.HTTPError(f"HTTP {self.status_code}")
            err.response = self
            raise err


class FakeSession:
    """Serves queued responses (or raises queued exceptions) in order and records each request's headers and timeout."""

    def __init__(self, *responses):
        self.responses, self.calls, self.timeouts = list(responses), [], []
        self.headers = {}

    def get(self, url, headers=None, timeout=None):
        self.calls.append((url, headers or {}))
        self.timeouts.append(timeout)
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


@pytest.fixture
def cache(tmp_path, monkeypatch):
    root = tmp_path / "cache"
    monkeypatch.setenv("SDVPLOT_CACHE_DIR", str(root))
    _cache._warned.clear()
    return root


FIXTURE = Path(__file__).parent / "fixtures" / "marks.csv"


@pytest.fixture
def manifest(cache, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, FIXTURE.read_bytes(), {"ETag": '"m1"'})))
    _manifest._read.cache_clear()
    return _manifest.load_manifest()

"""A small, hand-written team index every test runs against, so tests never touch the real generated index."""

import functools
import hashlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
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
    # two teams sharing one abbreviation, as in the shipped index: palette() must not pick one
    (
        "ncaa_baseball",
        "264",
        "KSU",
        "Kansas State Wildcats",
        "Kansas St",
        "Kansas State",
        "mens",
        None,
        None,
        "#633194",
        None,
        "espn",
    ),
    (
        "ncaa_baseball",
        "307",
        "KSU",
        "Kennesaw State Owls",
        "Kennesaw St",
        "Kennesaw State",
        "mens",
        None,
        None,
        "#bab0ac",
        "#4e79a7",
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
    ("nfl", "mark", "espn:24", "24", None, None),
    ("nfl", "mark", "espn:STL", "14", None, 2015),  # an old-abbreviation logo, dated by its relocation alias (R36)
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
    ("ncaa_baseball", "team_id", "264", "264", None, None),
    ("ncaa_baseball", "team_id", "307", "307", None, None),
    ("ncaa_baseball", "espn_abbr", "KSU", "264", None, None),
    ("ncaa_baseball", "espn_abbr", "KSU", "307", None, None),
]


def pytest_configure(config: pytest.Config) -> None:
    # Not in pyproject's filterwarnings: pytest imports a named category while parsing the ini file, which imported
    # sdvplot before pytest-cov started and left every import-time line unmeasured.
    config.addinivalue_line("filterwarnings", "error::sdvplot._errors.SdvplotWarning")
    _daemon_pipe_readers()


def _daemon_pipe_readers() -> None:
    """kaleido's browser driver (choreographer) reads Chrome's stderr through logistro's pipe reader, a non-daemon
    thread that ends only when every write end of the pipe closes. choreographer closes its own copy only after the
    browser closes, so a Chrome that will not close (a loaded machine) leaves the reader blocked forever and pytest
    hangs after printing its summary. As daemon threads, the readers can no longer keep the run alive."""
    # ponytail: patches a third-party module global for the test run only; drop it once choreographer closes the pipe
    # in a finally (choreographer 1.4.0 browser_async.close / browser_sync.close).
    try:
        from logistro import _api
    except ImportError:  # no kaleido in this environment
        return
    _api.Thread = functools.partial(threading.Thread, daemon=True)  # type: ignore[assignment,misc]


@pytest.fixture(autouse=True)
def fixture_index(request, tmp_path, monkeypatch):
    """The fixture index, unless the test is marked real_index (tests/test_real_index.py): then the shipped one."""
    if request.node.get_closest_marker("real_index"):
        _index.reload_index()
        yield _index.data_dir()
        _index.reload_index()
        return
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

    def iter_content(self, chunk_size=1):
        for i in range(0, len(self.content), chunk_size):
            yield self.content[i : i + chunk_size]

    def close(self):
        pass

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

    def get(self, url, headers=None, timeout=None, stream=False, allow_redirects=True):
        assert allow_redirects is False, "sdvplot must follow redirects itself (https-only)"
        self.calls.append((url, headers or {}))
        self.timeouts.append(timeout)
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


def slow_download(bodies, calls):
    """A _download that takes 0.05 s and records each URL, so threads that all miss the cache overlap."""

    def fake(url, headers, max_bytes):
        calls.append(url)
        time.sleep(0.05)
        return FakeResponse(200, bodies[url]), bodies[url]

    return fake


def in_threads(fn, n=8):
    """fn() in n threads released together; re-raises the first exception (an SdvplotWarning is one in tests)."""
    barrier = threading.Barrier(n)

    def run(_):
        barrier.wait()
        return fn()

    with ThreadPoolExecutor(n) as ex:
        return list(ex.map(run, range(n)))


@pytest.fixture
def cache(tmp_path, monkeypatch):
    root = tmp_path / "cache"
    monkeypatch.setenv("SDVPLOT_CACHE_DIR", str(root))
    _cache._warned.clear()
    for clear in _cache.MEMORY_CACHES:  # decoded images from an earlier test's cache directory
        clear()
    return root


FIXTURE = Path(__file__).parent / "fixtures" / "marks.csv"


@pytest.fixture
def manifest(cache, monkeypatch):
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, FIXTURE.read_bytes(), {"ETag": '"m1"'})))
    _manifest._read.cache_clear()
    return _manifest.load_manifest()


def seed_image(path, size=(50, 50), color=(200, 30, 40, 255)):
    """Write a solid PNG at path (a cache location), so the code under test finds it without downloading."""
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, color).save(path, format="PNG")
    return path


@pytest.fixture
def mark_images(manifest, cache):
    """Every fixture-manifest mark as a cached PNG, 1/10 of the manifest's width and height (so aspect ratios hold)."""
    rows = pl.read_csv(FIXTURE, schema_overrides={"entity_id": pl.Utf8})
    for sha, ext, w, h in rows.select("sha256", "ext", "width", "height").iter_rows():
        tint = hashlib.md5(sha.encode()).digest()[:3]  # a color per mark, so a swapped logo shows in baselines
        path = seed_image(cache / "images" / sha[:2] / f"{sha}.{ext}", size=(w // 10, h // 10), color=(*tint, 255))
        _cache._intact.add(str(path.resolve()))  # the fixture shas are made up: count the seeded files as verified
    return cache


PLAYERS = ("3139477", "4241479")  # ESPN athlete ids used by the headshot tests


@pytest.fixture
def headshot_images(cache):
    """The PLAYERS' NFL headshots as cached, fresh PNGs, so add_headshots never downloads.

    150 x 109 is ESPN's measured 600 x 436 (``sdvplot._web.HEADSHOT_ASPECT``) at a quarter of the size.
    """
    import hashlib
    import json
    import time

    from sdvplot._headshots import headshot_url

    for pid in PLAYERS:
        url = headshot_url(pid, "nfl")
        key = hashlib.sha256(url.encode()).hexdigest()
        path = seed_image(cache / "urlimages" / key[:2] / key, size=(150, 109))
        _cache._meta_path(path).write_text(json.dumps({"fetched_at": time.time()}))
    return cache


# The sdist ships src/ and tests/ but not the repository's tooling, data-raw/, docs/ or examples/. Tests that read those
# paths are repo-only: a module that fails at import is left out of collection, any other test is skipped, and only when
# its input is absent, so the repository itself still runs every one of them.
_ROOT = Path(__file__).parents[1]
_NEEDS_AT_IMPORT = {  # module -> a path it reads while importing
    "test_automation_example.py": "examples",
    "test_build_index.py": "tools",
    "test_fetch_sources.py": "tools",
    "test_gen_docs.py": "tools",
    "test_submodule_examples.py": "tools",
    "test_home_figures.py": "tools",
    "test_notebooks.py": "tools",
}
_NEEDS_AT_RUN = {  # test id prefix -> a path it reads when it runs
    "tests/test_commit_msg_hook.py": "tools",
    "tests/test_compat_matrix.py::test_every_test_the_compatibility_page_names_exists": "docs",
    "tests/test_gt_themes.py::test_every_theme_has_a_ported_row_in_the_parity_table": "docs",
    "tests/test_real_index.py::test_espn_team_endpoint_abbreviations_never_name_another_team": "data-raw",
    "tests/test_real_index.py::test_espn_colors_from_another_sport_come_only_from_school_keyed_leagues": "data-raw",
    "tests/test_real_index.py::test_logo_colors_agree_with_published_ones_where_both_exist": "data-raw",
    "tests/test_sdvplotr_parity.py": "data-raw",
    "tests/test_repo_files.py::test_sdv_py_dotfiles_exist_and_parse": "CLAUDE.md",
    "tests/test_repo_files.py::test_docs_changelog_mirrors_the_root_changelog": "docs",
    "tests/test_repo_files.py::test_contributor_files_exist": "CLAUDE.md",
}
collect_ignore = [name for name, need in _NEEDS_AT_IMPORT.items() if not (_ROOT / need).exists()]


def pytest_collection_modifyitems(config, items):
    for item in items:
        for prefix, need in _NEEDS_AT_RUN.items():
            if item.nodeid.startswith(prefix) and not (_ROOT / need).exists():
                item.add_marker(pytest.mark.skip(reason=f"repo-only: needs {need}/ (not in the sdist)"))

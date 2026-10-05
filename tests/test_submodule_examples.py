"""Run every public function's Example, top-level and submodule (the half of the docstring gate that executes code).

``tools/gen_docs.py --check`` checks the submodule Examples statically (syntax and undefined names); this runs them and
the top-level functions' Examples. Each runs
with a cache directory of its own, seeded with the marks, headshots and images the examples draw (seeded_cache), the
network blocked, a scratch working directory and a time limit, so each example runs to its end offline and the result
does not depend on the developer's warm cache. Anything that still cannot run offline is listed in TOLERATED with a
reason; an unlisted skip, or a tolerated example that raises AssertionError, NameError or SyntaxError, fails.
"""

import contextlib
import hashlib
import importlib.util
import inspect
import json
import signal
import socket
import sys
import time
from pathlib import Path

import polars as pl
import pytest

pytest.importorskip("docstring_parser")  # the docs group; the OS and lowest-direct jobs do not install it
pytest.importorskip("ruff")  # the static example check runs `python -m ruff`

import sdvplot  # noqa: E402
from sdvplot import _cache, _manifest  # noqa: E402
from sdvplot._errors import OfflineError  # noqa: E402
from sdvplot._headshots import headshot_url  # noqa: E402
from tests.conftest import FakeResponse, FakeSession, seed_image  # noqa: E402

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("gen_docs", ROOT / "tools" / "gen_docs.py")
gd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd)

EXAMPLE_TIMEOUT = 20  # seconds; enforced with setitimer, which Windows lacks (there an example is not time-limited)


class NetworkBlocked(OSError):
    """Raised by the blocker for any socket call an example makes."""


class ExampleTimeout(BaseException):  # BaseException: an example's own `except Exception` must not swallow it
    pass


NETWORK = (NetworkBlocked, OfflineError)
BROWSER = (Exception,)  # great_tables renders through headless Chrome; whatever it raises without one is tolerated
NEVER_TOLERATED = (AssertionError, NameError, SyntaxError)

_BROWSER = "renders through a headless browser, which CI and many machines lack"
# "<submodule>.<name>" -> (the exceptions that excuse it, why). Every skip must be listed.
TOLERATED: dict[str, tuple[tuple[type[BaseException], ...], str]] = {
    "great_tables.gt_grid": (BROWSER, _BROWSER),
    "great_tables.gt_save_batch": (BROWSER, _BROWSER),
    "great_tables.gt_save_crop": (BROWSER, _BROWSER),
    "great_tables.gt_social_crop": (BROWSER, _BROWSER),
}
# Both harness examples draw real marks; tests/test_matplotlib.py and tests/test_table_contract.py run the harnesses on
# the fixture marks, and test_contract_examples_pass_on_fixture_marks below runs these two examples the same way.
FIXTURE_BACKED = {"testing.check_adapter_contract", "testing.check_table_adapter_contract"}
# "<submodule>.<name>" for a submodule's function; a top-level function's is keyed by its bare name
TOP_LEVEL = {
    n: ex
    for n in sdvplot.__all__
    if callable(fn := getattr(sdvplot, n))
    and not isinstance(fn, type)
    and (ex := gd._example(inspect.getdoc(fn) or ""))
}
EXAMPLES = {**gd.submodule_examples(), **TOP_LEVEL}
# What the examples draw, seeded into each one's cache: a logo and a wordmark for every NFL team of the shipped index,
# the headshots of these ESPN athlete ids, these URL images and these rows of nflverse's player table (gsis id, ESPN id,
# headshot; copied from the live table, 2026-10-05). An example that needs more stops at a blocked network call and
# fails: seed what it needs here.
SEEDED_LEAGUE = "nfl"
SEEDED_PLAYERS = ("3139477", "3918298", "3916387")
SEEDED_PLAYER_ROWS = (
    ("00-0033873", "3139477", "https://static.www.nfl.com/image/upload/f_auto,q_auto/league/wdckwtob1lybvkmxnf7p"),
)
SEEDED_URLS = (
    "https://example.com/banner.png",
    "https://www.python.org/static/img/python-logo.png",
    "https://www.python.org/static/favicon.ico",
)


@pytest.fixture
def seeded_cache(cache, monkeypatch):
    """The cache with SEEDED_*: a manifest of made-up marks (served once by a fake session), every image as a fresh,
    verified PNG and the player-table rows as a fresh parquet, so no example downloads."""
    rows = []
    for team_id, name, program in sdvplot.teams(SEEDED_LEAGUE).select("team_id", "name", "program").iter_rows():
        for mark_type, w, h in (("logo", 500, 500), ("wordmark", 500, 200)):
            sha = hashlib.sha256(f"{SEEDED_LEAGUE}:{team_id}:{mark_type}".encode()).hexdigest()
            rows.append({"level": "team", "league": SEEDED_LEAGUE, "entity_id": team_id, "entity_name": name,
                         "program": program, "mark_type": mark_type, "variant": "default", "valid_from": None,
                         "valid_to": None, "source": "espn", "url": f"https://x/{sha}.png", "sha256": sha,
                         "ext": "png", "bytes": 100, "width": w, "height": h, "archive_url": f"https://cdn/{sha}.png",
                         "first_seen": "2026-09-26", "last_seen": "2026-10-01"})  # fmt: skip
            path = seed_image(cache / "images" / sha[:2] / f"{sha}.png", size=(w // 10, h // 10))
            _cache._intact.add(str(path.resolve()))  # made-up shas: count the seeded files as verified
    body = pl.DataFrame(rows).write_csv().encode()
    with monkeypatch.context() as m:  # only for this download: an example's own downloads must reach the blocker
        m.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, body, {"ETag": '"seeded"'})))
        _manifest._read.cache_clear()
        _manifest.load_manifest()
    players = cache / "nflverse" / "players.parquet"
    players.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(SEEDED_PLAYER_ROWS, schema=["gsis_id", "espn_id", "headshot"], orient="row").write_parquet(players)
    _cache._meta_path(players).write_text(json.dumps({"fetched_at": time.time()}))
    for url in [*(headshot_url(p, SEEDED_LEAGUE) for p in SEEDED_PLAYERS), *SEEDED_URLS]:
        key = hashlib.sha256(url.encode()).hexdigest()
        path = seed_image(cache / "urlimages" / key[:2] / key, size=(150, 109))
        _cache._meta_path(path).write_text(json.dumps({"fetched_at": time.time()}))
    return cache


def run_example(code: str, root: Path, monkeypatch, *, timeout: float = EXAMPLE_TIMEOUT) -> BaseException | None:
    """Run ``code`` offline, with ``root`` as the working directory and cache; return what it raised, or None."""
    cache = root / "cache"
    monkeypatch.setenv(_cache.CACHE_ENV, str(cache))
    monkeypatch.setenv("MPLBACKEND", "Agg")
    monkeypatch.chdir(root)
    _cache._warned.clear()
    for clear in _cache.MEMORY_CACHES:
        clear()

    def blocked(*_a, **_k):
        raise NetworkBlocked("network disabled while running a docstring example")

    for target, name in [(socket.socket, "connect"), (socket.socket, "connect_ex"), (socket, "getaddrinfo"),
                         (socket, "create_connection"), (socket, "gethostbyname")]:  # fmt: skip
        monkeypatch.setattr(target, name, blocked)
    # a keep-alive connection pooled by an earlier (live) test sends without connect or getaddrinfo: block sdvplot's
    # downloads at their one entry point too
    monkeypatch.setattr(_cache, "_session", blocked)

    def on_alarm(*_a):
        raise ExampleTimeout(f"timed out after {timeout} s")

    ns: dict[str, object] = {"__name__": "__example__"}
    timed = hasattr(signal, "setitimer")
    if timed:
        old = signal.signal(signal.SIGALRM, on_alarm)
        signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        import warnings

        with contextlib.redirect_stdout(open(root / "stdout.txt", "w")), warnings.catch_warnings():  # noqa: SIM115
            warnings.simplefilter("ignore")
            exec(compile(code, "<example>", "exec"), ns)  # noqa: S102
    except BaseException as e:  # noqa: BLE001  the caller classifies it
        return e
    finally:
        if timed:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old)
        if "matplotlib.pyplot" in sys.modules:
            sys.modules["matplotlib.pyplot"].close("all")
    return None


def failure(key: str, exc: BaseException | None, tolerated=TOLERATED) -> str | None:
    """Why ``exc`` (what example ``key`` raised) fails the gate, or None when it passes."""
    if isinstance(exc, ExampleTimeout):
        return f"{key}: {exc}"
    entry = tolerated.get(key)
    if exc is None:
        if entry and entry[0] is not BROWSER:
            return f"{key}: ran clean, so its TOLERATED entry is stale; remove it"
        return None
    if entry and isinstance(exc, entry[0]) and not isinstance(exc, NEVER_TOLERATED):
        return None
    hint = " (unlisted skip: seed what it fetches in seeded_cache, or list it in TOLERATED with a reason)"
    return f"{key}: {type(exc).__name__}: {exc}{hint if isinstance(exc, NETWORK) else ''}"


@pytest.mark.real_index
@pytest.mark.parametrize("key", sorted(set(EXAMPLES) - FIXTURE_BACKED))
def test_the_example_runs_offline(key, monkeypatch, seeded_cache):
    why = failure(key, run_example(EXAMPLES[key], seeded_cache.parent, monkeypatch))
    assert why is None, why


@pytest.mark.parametrize("key", sorted(FIXTURE_BACKED))
def test_contract_examples_pass_on_fixture_marks(key, tmp_path, monkeypatch, manifest, mark_images, headshot_images):
    root = mark_images.parent  # the fixture's cache holds the seeded marks: use its directory as the cache
    exc = run_example(EXAMPLES[key], root, monkeypatch)
    assert exc is None, f"{key}: {type(exc).__name__}: {exc}"


def test_every_tolerated_entry_names_a_real_example():
    assert set(TOLERATED) <= set(EXAMPLES)


# the runner and the classification, on small examples


def _run(code, tmp_path, monkeypatch, **kw):
    return run_example(code, tmp_path, monkeypatch, **kw)


def test_an_example_that_runs_clean_passes(tmp_path, monkeypatch):
    assert failure("a.b", _run("total = 1 + 1", tmp_path, monkeypatch), {}) is None


def test_a_name_error_after_a_network_call_is_caught_statically():
    code = "import socket\nsocket.create_connection(('example.com', 80))\nundefined_name\n"
    errors = gd._static_example_errors({"a.b": code})
    assert len(errors) == 1 and "undefined_name" in errors[0] and "line 3" in errors[0]


def test_a_syntax_error_is_caught_statically():
    errors = gd._static_example_errors({"a.b": "x = (\n"})
    assert len(errors) == 1 and errors[0].startswith("sdvplot.a.b: Example:")


def test_a_blocked_network_call_is_a_listed_skip_only_when_listed(tmp_path, monkeypatch):
    exc = _run("import socket\nsocket.create_connection(('example.com', 80))", tmp_path, monkeypatch)
    assert isinstance(exc, NetworkBlocked)
    assert "unlisted skip" in (failure("a.b", exc, {}) or "")
    assert failure("a.b", exc, {"a.b": (NETWORK, "needs the network")}) is None


@pytest.mark.parametrize("call", ["connect_ex", "getaddrinfo", "gethostbyname"])
def test_every_socket_entry_point_is_blocked(call, tmp_path, monkeypatch):
    args = {"connect_ex": "s.connect_ex(('127.0.0.1', 9))", "getaddrinfo": "socket.getaddrinfo('example.com', 80)",
            "gethostbyname": "socket.gethostbyname('example.com')"}  # fmt: skip
    exc = _run(f"import socket\ns = socket.socket()\n{args[call]}", tmp_path, monkeypatch)
    assert isinstance(exc, NetworkBlocked)


def test_a_pooled_connection_cannot_bypass_the_blocker(tmp_path, monkeypatch):
    # an earlier live test leaves a session whose pooled keep-alive connection needs no connect: stand in for it
    class Pooled:
        def get(self, *_a, **_k):
            return "served from a pooled connection"

    monkeypatch.setitem(_cache.__dict__, "SESSION", Pooled())
    exc = _run("from sdvplot import _cache\n_cache._session().get('https://example.com')", tmp_path, monkeypatch)
    assert isinstance(exc, NetworkBlocked)


def test_a_missing_file_fails_it_is_not_a_network_skip(tmp_path, monkeypatch):
    exc = _run("open('nope-does-not-exist.csv')", tmp_path, monkeypatch)
    assert isinstance(exc, FileNotFoundError) and not isinstance(exc, NetworkBlocked)
    assert failure("a.b", exc, {"a.b": (NETWORK, "x")}) is not None


def test_an_assertion_error_fails_even_for_a_tolerated_example(tmp_path, monkeypatch):
    exc = _run("assert 1 == 2, 'rule 1 broken'", tmp_path, monkeypatch)
    assert "rule 1 broken" in (failure("a.b", exc, {"a.b": (BROWSER, "x")}) or "")


@pytest.mark.skipif(not hasattr(signal, "setitimer"), reason="no setitimer on this platform (Windows): no time limit")
def test_an_infinite_loop_is_reported_as_a_timeout_not_a_hang(tmp_path, monkeypatch):
    exc = _run("while True:\n    pass", tmp_path, monkeypatch, timeout=1)
    assert isinstance(exc, ExampleTimeout)
    assert "timed out" in (failure("a.b", exc, {"a.b": (BROWSER, "x")}) or "")


def test_a_timeout_cannot_be_swallowed_by_the_example(tmp_path, monkeypatch):
    if not hasattr(signal, "setitimer"):
        pytest.skip("no setitimer on this platform")
    exc = _run(
        # a call in the loop: CPython 3.10 does not run signal handlers in a loop that makes no calls
        "import time\nwhile True:\n    try:\n        time.sleep(0.01)\n    except Exception:\n        pass",
        tmp_path,
        monkeypatch,
        timeout=1,
    )
    assert isinstance(exc, ExampleTimeout)


def test_a_stale_tolerated_entry_fails(tmp_path, monkeypatch):
    assert "stale" in (failure("a.b", _run("x = 1", tmp_path, monkeypatch), {"a.b": (NETWORK, "x")}) or "")


def test_an_example_runs_against_an_empty_cache_of_its_own_and_clear_cache_leaves_the_real_one(tmp_path, monkeypatch):
    real = tmp_path / "real"
    (real / "images").mkdir(parents=True)
    (real / "images" / "keep").write_text("x")
    monkeypatch.setenv(_cache.CACHE_ENV, str(real))
    code = "import sdvplot\nfrom sdvplot import _cache\nassert not any(_cache.cache_dir().rglob('*'))\nsdvplot.clear_cache()\n"
    root = tmp_path / "scratch"
    root.mkdir()
    assert _run(code, root, monkeypatch) is None
    assert (real / "images" / "keep").exists()

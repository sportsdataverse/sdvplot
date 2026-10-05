"""Run every public submodule Example (the half of the docstring gate that executes code).

``tools/gen_docs.py --check`` checks the Examples statically (syntax and undefined names); this runs them. Each runs
with an empty cache directory of its own, the network blocked, a scratch working directory and a time limit, so the
result does not depend on the developer's warm cache. Anything that cannot run offline is listed in TOLERATED with a
reason; an unlisted skip, or a tolerated example that raises AssertionError, NameError or SyntaxError, fails.
"""

import contextlib
import importlib.util
import signal
import socket
import sys
from pathlib import Path

import pytest

pytest.importorskip("docstring_parser")  # the docs group; the OS and lowest-direct jobs do not install it
pytest.importorskip("ruff")  # the static example check runs `python -m ruff`

from sdvplot import _cache  # noqa: E402
from sdvplot._errors import OfflineError  # noqa: E402

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

_MARKS = "needs the network: its marks are not cached (the cache is empty)"
_BROWSER = "renders through a headless browser, which CI and many machines lack"
# "<submodule>.<name>" -> (the exceptions that excuse it, why). Every skip must be listed.
TOLERATED: dict[str, tuple[tuple[type[BaseException], ...], str]] = {
    "altair.add_logos": (NETWORK, _MARKS),
    "altair.add_wordmarks": (NETWORK, _MARKS),
    "altair.axis_logos": (NETWORK, _MARKS),
    "altair.logo_layer": (NETWORK, _MARKS),
    "bokeh.add_logos": (NETWORK, _MARKS),
    "bokeh.add_wordmarks": (NETWORK, _MARKS),
    "folium.add_logos": (NETWORK, _MARKS),
    "folium.add_wordmarks": (NETWORK, _MARKS),
    "great_tables.add_logos": (NETWORK, _MARKS),
    "great_tables.add_wordmarks": (NETWORK, _MARKS),
    "great_tables.gt_sdv_cols_label": (NETWORK, _MARKS),
    "great_tables.gt_sdv_logos": (NETWORK, _MARKS),
    "great_tables.gt_sdv_wordmarks": (NETWORK, _MARKS),
    "great_tables.gt_theme_sdv": (NETWORK, _MARKS),
    "holoviews.add_logos": (NETWORK, _MARKS),
    "holoviews.add_wordmarks": (NETWORK, _MARKS),
    "matplotlib.add_headshots": (NETWORK, _MARKS),
    "matplotlib.add_logos": (NETWORK, _MARKS),
    "matplotlib.add_wordmarks": (NETWORK, _MARKS),
    "matplotlib.axis_logos": (NETWORK, _MARKS),
    "matplotlib.team_tiers": (NETWORK, _MARKS),
    "matplotlib.title_image": (NETWORK, _MARKS),
    "plotly.add_logos": (NETWORK, _MARKS),
    "plotly.add_wordmarks": (NETWORK, _MARKS),
    "plotly.axis_logos": (NETWORK, _MARKS),
    "plotnine.title_image": (NETWORK, _MARKS),
    "plottable.headshot_column": (NETWORK, _MARKS),
    "plottable.logo_column": (NETWORK, _MARKS),
    "pygal.add_logos": (NETWORK, _MARKS),
    "pygal.add_wordmarks": (NETWORK, _MARKS),
    "reactable.reactable_sdv_logos": (NETWORK, _MARKS),
    "reactable.reactable_sdv_wordmarks": (NETWORK, _MARKS),
    "great_tables.gt_grid": (BROWSER, _BROWSER),
    "great_tables.gt_save_batch": (BROWSER, _BROWSER),
    "great_tables.gt_save_crop": (BROWSER, _BROWSER),
    "great_tables.gt_social_crop": (BROWSER, _BROWSER),
}
# Both harness examples draw real marks; tests/test_matplotlib.py and tests/test_table_contract.py run the harnesses on
# the fixture marks, and test_contract_examples_pass_on_fixture_marks below runs these two examples the same way.
FIXTURE_BACKED = {"testing.check_adapter_contract", "testing.check_table_adapter_contract"}
EXAMPLES = gd.submodule_examples()


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
    hint = " (unlisted skip: add it to TOLERATED with a reason)" if isinstance(exc, NETWORK) else ""
    return f"{key}: {type(exc).__name__}: {exc}{hint}"


@pytest.mark.real_index
@pytest.mark.parametrize("key", sorted(set(EXAMPLES) - FIXTURE_BACKED))
def test_the_example_runs_offline(key, tmp_path, monkeypatch):
    why = failure(key, run_example(EXAMPLES[key], tmp_path, monkeypatch))
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

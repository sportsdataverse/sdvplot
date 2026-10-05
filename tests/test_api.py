import importlib
import inspect
import pkgutil
import sys
import typing

import pytest

import sdvplot
from sdvplot import _dispatch, _errors, _marks, _placement, _tables

PUBLIC = {
    "resolve",
    "suggest",
    "teams",
    "palette",
    "team_colors",
    "logo_url",
    "logo_image",
    "marks",
    "headshot_url",
    "versions",
    "clear_cache",
    "add_logos",
    "add_wordmarks",
    "add_headshots",
    "axis_logos",
    "surface",
    "court_coords",
    "SdvplotWarning",
    "SdvplotDeprecationWarning",
    "SdvplotError",
    "InputError",
    "UnresolvedTeamError",
    "OfflineError",
    "DownloadError",
    "IntegrityError",
    "OptionalDependencyError",
    "UnsupportedTargetError",
    "UnsafeDownloadError",
    "UnsafeCachePathError",
    "__version__",
}


def test_the_public_api_is_exactly_the_spec():
    assert set(sdvplot.__all__) == PUBLIC
    for name in PUBLIC:
        assert hasattr(sdvplot, name), name


def test_versions_reports_package_index_and_manifest(cache):
    v = sdvplot.versions()
    assert v["sdvplot"] == sdvplot.__version__ and v["index"] == "fixture" and v["manifest_last_modified"] is None


UNKNOWN_LEAGUE = [
    lambda: sdvplot.resolve("LV", "xfl"),
    lambda: sdvplot.palette("xfl"),
    lambda: sdvplot.palette("xfl", teams=["LV"]),
    lambda: sdvplot.team_colors("xfl", ["LV"]),
    lambda: sdvplot.teams("xfl"),
    lambda: sdvplot.suggest("LV", "xfl"),
    lambda: sdvplot.marks("LV", "xfl"),
    lambda: sdvplot.logo_url("LV", "xfl"),
]


@pytest.mark.parametrize("call", UNKNOWN_LEAGUE)
def test_an_unknown_league_is_the_same_clear_error_everywhere(call):  # M2
    with pytest.raises(
        ValueError, match=r"unknown league 'xfl'; known leagues: \['cfb', 'mlb', 'ncaa_baseball', 'nfl', 'ohl'\]"
    ):
        call()


@pytest.mark.parametrize(
    "call", [lambda: sdvplot.resolve("LV", "nfl", id_system="espnn"), lambda: sdvplot.marks("LV", "nfl", id_system="x")]
)
def test_an_unknown_id_system_lists_the_valid_ones(call):  # M2
    with pytest.raises(ValueError, match=r"unknown id_system .*'auto'.*'espn_abbr'"):
        call()


@pytest.mark.parametrize("fn", [sdvplot.logo_url, sdvplot.logo_image, _marks.select_mark])
def test_an_unknown_mark_type_is_an_error(fn):  # M2
    with pytest.raises(ValueError, match=r"mark_type must be one of \['logo', 'wordmark'\], got 'helmet'"):
        fn("LV", "nfl", mark_type="helmet")


ERRORS = {
    sdvplot.UnresolvedTeamError: ValueError,
    sdvplot.OfflineError: RuntimeError,
    sdvplot.DownloadError: OSError,
    sdvplot.IntegrityError: OSError,
    sdvplot.OptionalDependencyError: ImportError,
    sdvplot.UnsupportedTargetError: TypeError,
    sdvplot.UnsafeCachePathError: ValueError,
    sdvplot.UnsafeDownloadError: OSError,
    sdvplot.InputError: ValueError,
}


@pytest.mark.parametrize(("error", "builtin"), ERRORS.items())
def test_every_error_is_an_sdvplot_error_and_keeps_its_builtin(error, builtin):
    with pytest.raises(sdvplot.SdvplotError):
        raise error("x")
    with pytest.raises(builtin):  # existing `except ValueError` (etc.) code keeps working
        raise error("x")


def test_every_error_class_in_the_package_subclasses_sdvplot_error():
    # enumerates the module, so an error class added later cannot be missed
    errors = [
        c
        for c in vars(_errors).values()
        if isinstance(c, type) and issubclass(c, Exception) and not issubclass(c, Warning)
    ]
    assert set(ERRORS) | {sdvplot.SdvplotError} <= set(errors)
    for c in errors:
        assert issubclass(c, sdvplot.SdvplotError), c


def test_a_raised_sdvplot_error_is_caught_by_the_base():
    with pytest.raises(sdvplot.SdvplotError, match="did not resolve"):
        sdvplot.resolve("XYZ", "nfl", strict=True)


# every public submodule, found rather than listed: a new one cannot skip the checks below
SUBMODULES = sorted(m.name for m in pkgutil.iter_modules(sdvplot.__path__) if not m.name.startswith("_"))
# the optional library each adapter module needs: the registered adapters, plus the two column helpers. Any other
# submodule (sdvplot.testing, or a new one) is imported unguarded, so it cannot hide behind a skip
LIBRARY = {"reactable": "reactable", "plottable": "plottable"}
for _a in _dispatch.ADAPTERS.values():
    _name = _a.module.split(".")[1]
    if _name not in LIBRARY or _a.package == _name:  # seaborn also routes to sdvplot.matplotlib
        LIBRARY[_name] = _a.package


def _submodule(name):
    """sdvplot.<name>, skipping (as each adapter's own tests do) when its optional library is not installed."""
    if name in LIBRARY:
        pytest.importorskip(LIBRARY[name])
    return importlib.import_module(f"sdvplot.{name}")


def test_the_submodules_are_found():
    assert {"matplotlib", "great_tables", "testing", "pygal"} <= set(SUBMODULES)


@pytest.mark.parametrize("name", SUBMODULES)
def test_a_public_submodule_shows_only_its_all(name):
    mod = _submodule(name)
    # what dir(), tab completion and `import *` show: no numpy, no imported helpers, no test hooks
    assert {n for n in dir(mod) if not n.startswith("_")} == set(mod.__all__)
    for n in mod.__all__:
        value = getattr(mod, n)
        # a Literal alias (sdvplot.typing) cannot carry a docstring; its module docstring documents it
        assert not n.startswith("_") and (inspect.getdoc(value) or typing.get_origin(value) is typing.Literal), n
    # a function or class the module defines is either exported or private (underscore)
    own = {
        n
        for n, v in vars(mod).items()
        if not n.startswith("_") and (inspect.isfunction(v) or inspect.isclass(v)) and v.__module__ == mod.__name__
    }
    assert own <= set(mod.__all__), own - set(mod.__all__)


# Past its leading "what" arguments (the target and data, a table and its columns) a public function's arguments are
# keyword-only, so a later release can add or reorder options without silently rebinding a positional value (N1).
MAX_POSITIONAL = 4
# Functions allowed more positional arguments, each with its reason. Empty: none needs more today.
POSITIONAL_ALLOWLIST: dict[str, int] = {}


@pytest.mark.parametrize("name", ["", *SUBMODULES])
def test_public_functions_take_at_most_four_positional_arguments(name):
    mod = _submodule(name) if name else sdvplot
    over = {}
    for n in mod.__all__:
        fn = getattr(mod, n)
        if not inspect.isfunction(fn):
            continue
        params = inspect.signature(fn).parameters.values()
        count = sum(p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) for p in params)
        if count > POSITIONAL_ALLOWLIST.get(f"{mod.__name__}.{n}", MAX_POSITIONAL):
            over[n] = count
    assert not over, f"put a bare * after the leading arguments of {over}"


def test_the_top_level_shows_only_its_all_and_the_submodules():
    shown = {n for n in dir(sdvplot) if not n.startswith("_")}
    assert shown - set(sdvplot.__all__) <= set(SUBMODULES), shown - set(sdvplot.__all__) - set(SUBMODULES)
    assert "version" not in shown and "PackageNotFoundError" not in shown


ADAPTERS = ["matplotlib", "plotnine", "plotly", "altair", "bokeh", "holoviews", "folium", "pygal"]


@pytest.mark.parametrize("name", ADAPTERS)
def test_the_adapter_modules_keep_their_test_hooks_private(name):
    mod = _submodule(name)
    assert callable(mod._drawn_marks) and isinstance(mod._SUPPORTS_AXIS_LOGOS, bool)
    assert not hasattr(mod, "drawn_marks") and not hasattr(mod, "SUPPORTS_AXIS_LOGOS")


def test_the_table_adapter_keeps_its_test_hooks_private():
    gt = _submodule("great_tables")
    assert callable(gt._drawn_cells) and callable(gt._rendered_html) and not hasattr(gt, "drawn_cells")


# the core verbs: the leading arguments stay positional, every other one is keyword-only
POSITIONAL = {
    sdvplot.resolve: ["values", "league"],
    sdvplot.suggest: ["value", "league"],
    sdvplot.teams: ["league"],
    sdvplot.palette: ["league", "teams"],
    sdvplot.team_colors: ["league", "teams"],
    sdvplot.logo_url: ["team", "league"],
    sdvplot.logo_image: ["team", "league"],
    sdvplot.marks: ["team", "league"],
    sdvplot.headshot_url: ["player_id", "league"],
    sdvplot.surface: ["league", "team"],
    sdvplot.court_coords: ["data"],
}


@pytest.mark.parametrize(("fn", "positional"), POSITIONAL.items(), ids=lambda v: getattr(v, "__name__", ""))
def test_core_verbs_take_secondary_arguments_by_keyword_only(fn, positional):
    params = inspect.signature(fn).parameters.values()
    assert [p.name for p in params if p.kind is p.POSITIONAL_OR_KEYWORD] == positional
    assert all(p.kind in (p.KEYWORD_ONLY, p.VAR_KEYWORD) for p in params if p.name not in positional)


@pytest.mark.parametrize(
    "call",
    [
        lambda: sdvplot.resolve("OAK", "nfl", 1990),
        lambda: sdvplot.logo_url("OAK", "nfl", 1990),
        lambda: sdvplot.marks("OAK", "nfl", 1990),
        lambda: sdvplot.suggest("Raidrs", "nfl", 3),
        lambda: sdvplot.palette("nfl", ["LV"], "secondary"),
        lambda: sdvplot.team_colors("nfl", "LV", "secondary"),
    ],
)
def test_a_positional_secondary_argument_is_a_type_error(call):
    with pytest.raises(TypeError, match="positional argument"):
        call()


def test_palette_and_team_colors_take_the_league_first_as_sdvplotr_does():
    # sdvplotR: sdv_color_palette(sport, teams, type) and sdv_team_colors(sport, team, type)
    assert sdvplot.palette("nfl", ["LV"]) == {"LV": "#000000"}
    assert sdvplot.team_colors("nfl", ["LV"]) == ["#000000"]
    assert sdvplot.team_colors("nfl", "LV", which="secondary") == "#a5acaf"
    with pytest.raises(sdvplot.InputError, match="unknown league 'LV'"):  # the old team-first order fails loudly
        sdvplot.team_colors("LV", "nfl")


@pytest.mark.parametrize("teams", [["LV"], ("LV",), "series"])
def test_the_old_team_colors_order_with_several_teams_names_the_new_order(teams):
    if teams == "series":
        teams = pytest.importorskip("polars").Series(["LV"])
    message = r"league must be a league key such as 'nfl', got \w+; .* team_colors\(league, teams\)"
    with pytest.raises(sdvplot.InputError, match=message):
        sdvplot.team_colors(teams, "nfl")


@pytest.mark.parametrize("teams", ["secondary", "primary", ["LV", "secondary"]])
def test_a_color_slot_passed_as_teams_shows_the_keyword_form(teams):
    # pre-0.1, palette(league, "secondary") meant which="secondary"; now it would silently match no team
    slot = "secondary" if "secondary" in teams else "primary"
    message = (
        rf"'{slot}' is a color slot, not a team; pass it by keyword: palette\(league, teams=\.\.\., which=\"{slot}\"\)"
    )
    with pytest.raises(sdvplot.InputError, match=message):
        sdvplot.palette("nfl", teams)


# every shared argument check raises an SdvplotError that is still the builtin a caller already catches
INPUT_ERRORS = {
    "unknown league": lambda: sdvplot.team_colors("nfll", "KC"),
    "league not a string": lambda: sdvplot.resolve("KC", ["nfl"]),
    "which": lambda: sdvplot.palette("nfl", which="tertiary"),
    "id_system": lambda: sdvplot.resolve("KC", "nfl", id_system="nflfastr"),
    "mark_type": lambda: sdvplot.logo_url("KC", "nfl", mark_type="helmet"),
    "color slot as a team": lambda: sdvplot.palette("nfl", "secondary"),
    "height": lambda: _placement.check_height(1.5),
    "alpha": lambda: _placement.check_alpha(-1),
    "kind": lambda: _placement.place([1], [1], ["LV"], league="nfl", kind="helmet"),
    "pixels": lambda: _tables.check_px(0.5),
    "headshot league": lambda: sdvplot.headshot_url("1", "ohl"),
    "headshot id_system": lambda: sdvplot.headshot_url("1", "nba", id_system="gsis"),
}


@pytest.mark.parametrize("call", INPUT_ERRORS.values(), ids=INPUT_ERRORS.keys())
def test_argument_checks_raise_an_input_error(call):
    with pytest.raises(sdvplot.InputError) as info:
        call()
    assert isinstance(info.value, sdvplot.SdvplotError) and isinstance(info.value, ValueError)


@pytest.mark.parametrize("name", ADAPTERS)
def test_a_wrong_target_is_an_unsupported_target_error(name):
    mod = _submodule(name)
    with pytest.raises(sdvplot.UnsupportedTargetError) as info:
        mod.add_logos(object(), [1], [1], ["LV"], league="nfl")
    assert isinstance(info.value, TypeError)


def _adapter_modules():
    return sorted({a.module for a in _dispatch.ADAPTERS.values()})


def test_the_front_door_docstring_tells_plots_from_tables():
    doc = " ".join(inspect.getdoc(sdvplot.add_logos).split())
    assert "Every adapter takes the same arguments" not in doc
    plots = [m for m in _adapter_modules() if m != "sdvplot.great_tables"]
    for m in plots:  # every plot adapter is named where the docstring says what a plot takes
        assert m.split(".")[1].lower() in doc.lower(), m
    gt = _submodule("great_tables")
    table = inspect.signature(gt.add_logos).parameters
    assert "columns" in table and f"pixels (default {table['height'].default})" in doc


@pytest.mark.parametrize("module", _adapter_modules())
def test_the_axis_logos_docstring_matches_the_adapters(module):
    doc = " ".join(inspect.getdoc(sdvplot.axis_logos).split())
    drawing, raising = doc.split("have no axis logos")[0].rsplit(".", 1)
    name = module.split(".")[1]
    mod = _submodule(name)
    key = name.replace("_", "").lower()
    if mod._SUPPORTS_AXIS_LOGOS:
        assert key in drawing.replace("_", "").lower(), module
        kw = {p.name for p in inspect.signature(mod.axis_logos).parameters.values() if p.kind is p.KEYWORD_ONLY}
        assert {"league", "season", "height", "variant", "mark_type", "id_system"} <= kw, module
    else:
        assert key in raising.replace("_", "").lower(), module
        with pytest.raises(sdvplot.UnsupportedTargetError):
            mod.axis_logos(object(), "x", league="nfl")


# S11: every function that resolves teams takes resolve()'s id_system and strict and passes them through. "LV" resolves
# under "auto" (espn_abbr) but is no "name", so id_system="name" proves the id system arrives, and strict that it raises.
TEAM_RESOLVERS = {  # the call, and what it returns for a team that does not resolve
    "team_colors": (lambda **kw: sdvplot.team_colors("nfl", ["LV"], **kw), [None]),
    "palette": (lambda **kw: sdvplot.palette("nfl", ["LV"], **kw), {}),
    "logo_url": (lambda **kw: sdvplot.logo_url("LV", "nfl", **kw), None),
    "logo_image": (lambda **kw: sdvplot.logo_image("LV", "nfl", **kw), None),
}


@pytest.mark.parametrize(("call", "unresolved"), TEAM_RESOLVERS.values(), ids=TEAM_RESOLVERS.keys())
def test_team_resolving_functions_pass_id_system_and_strict_to_the_resolver(call, unresolved):
    with pytest.raises(sdvplot.UnresolvedTeamError, match="'LV'"):
        call(id_system="name", strict=True)
    with pytest.warns(sdvplot.SdvplotWarning, match="did not resolve"):
        assert call(id_system="name") == unresolved
    with pytest.raises(sdvplot.InputError, match="unknown id_system"):
        call(id_system="espnn")


# S6: each adapter submodule's library and the extra that installs it. Every public submodule but testing and typing
# needs one, so a new adapter cannot skip this check.
EXTRAS = {
    "matplotlib": ("matplotlib", "mpl"),
    "plotnine": ("plotnine", "plotnine"),
    "plottable": ("plottable", "plottable"),
    "plotly": ("plotly", "plotly"),
    "altair": ("altair", "altair"),
    "bokeh": ("bokeh", "bokeh"),
    "holoviews": ("holoviews", "holoviews"),
    "folium": ("folium", "folium"),
    "pygal": ("pygal", "pygal"),
    "reactable": ("reactable", "reactable"),
    "great_tables": ("great_tables", "tables"),
}


def test_every_adapter_submodule_names_its_extra():
    assert set(EXTRAS) == set(SUBMODULES) - {"testing", "typing"}


@pytest.mark.parametrize("name", EXTRAS)
def test_importing_an_adapter_without_its_library_names_the_extra(monkeypatch, name):
    library, extra = EXTRAS[name]
    for mod in [m for m in sys.modules if m == library or m.startswith(library + ".")] + [library]:
        monkeypatch.setitem(sys.modules, mod, None)  # None in sys.modules: importing it raises ModuleNotFoundError
    for mod in [m for m in sys.modules if m == f"sdvplot.{name}" or m.startswith(f"sdvplot.{name}.")]:
        monkeypatch.delitem(sys.modules, mod)  # restored afterwards, as are the libraries
    with pytest.raises(sdvplot.OptionalDependencyError, match=rf'pip install "sdvplot\[{extra}\]"') as exc:
        importlib.import_module(f"sdvplot.{name}")
    assert isinstance(exc.value, ModuleNotFoundError) and exc.value.name.split(".")[0] == library


def test_the_front_door_passes_the_adapters_missing_extra_error_through(monkeypatch):
    go = pytest.importorskip("plotly.graph_objects")
    fig = go.Figure()
    for mod in [m for m in sys.modules if m == "plotly" or m.startswith("plotly.")]:
        monkeypatch.setitem(sys.modules, mod, None)
    monkeypatch.delitem(sys.modules, "sdvplot.plotly", raising=False)
    with pytest.raises(sdvplot.OptionalDependencyError, match=r'pip install "sdvplot\[plotly\]"'):
        sdvplot.add_logos(fig, [1], [1], ["LV"], league="nfl")

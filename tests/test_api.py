import importlib
import inspect

import pytest

import sdvplot
from sdvplot import _dispatch, _errors, _marks

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
    "SdvplotError",
    "UnresolvedTeamError",
    "OfflineError",
    "OptionalDependencyError",
    "UnsupportedTargetError",
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
    sdvplot.OptionalDependencyError: ImportError,
    sdvplot.UnsupportedTargetError: TypeError,
    _errors.UnsafeCachePathError: ValueError,
    _errors.UnsafeDownloadError: OSError,
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


SUBMODULES = [
    "matplotlib", "plotnine", "plotly", "altair", "bokeh", "holoviews", "folium", "pygal", "reactable", "plottable",
    "testing", "great_tables",
]  # fmt: skip


@pytest.mark.parametrize("name", SUBMODULES)
def test_a_public_submodule_shows_only_its_all(name):
    mod = importlib.import_module(f"sdvplot.{name}")
    # what dir(), tab completion and `import *` show: no numpy, no imported helpers, no test hooks
    assert {n for n in dir(mod) if not n.startswith("_")} == set(mod.__all__)
    for n in mod.__all__:
        assert not n.startswith("_") and inspect.getdoc(getattr(mod, n)), n
    # a function or class the module defines is either exported or private (underscore)
    own = {
        n
        for n, v in vars(mod).items()
        if not n.startswith("_") and (inspect.isfunction(v) or inspect.isclass(v)) and v.__module__ == mod.__name__
    }
    assert own <= set(mod.__all__), own - set(mod.__all__)


def test_the_adapter_modules_keep_their_test_hooks_private():
    for name in ("matplotlib", "plotnine", "plotly", "altair", "bokeh", "holoviews", "folium", "pygal"):
        mod = importlib.import_module(f"sdvplot.{name}")
        assert callable(mod._drawn_marks) and isinstance(mod._SUPPORTS_AXIS_LOGOS, bool)
        assert not hasattr(mod, "drawn_marks") and not hasattr(mod, "SUPPORTS_AXIS_LOGOS")
    gt = importlib.import_module("sdvplot.great_tables")
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
    with pytest.raises(ValueError, match="unknown league 'LV'"):  # the old team-first order fails loudly
        sdvplot.team_colors("LV", "nfl")


def _adapter_modules():
    return sorted({a.module for a in _dispatch.ADAPTERS.values()})


def test_the_front_door_docstring_tells_plots_from_tables():
    doc = " ".join(inspect.getdoc(sdvplot.add_logos).split())
    assert "Every adapter takes the same arguments" not in doc
    plots = [m for m in _adapter_modules() if m != "sdvplot.great_tables"]
    for m in plots:  # every plot adapter is named where the docstring says what a plot takes
        assert m.split(".")[1].lower() in doc.lower(), m
    gt = importlib.import_module("sdvplot.great_tables")
    table = inspect.signature(gt.add_logos).parameters
    assert "columns" in table and f"pixels (default {table['height'].default})" in doc


def test_the_axis_logos_docstring_matches_the_adapters():
    doc = " ".join(inspect.getdoc(sdvplot.axis_logos).split())
    drawing, raising = doc.split("have no axis logos")[0].rsplit(".", 1)
    for m in _adapter_modules():
        mod = importlib.import_module(m)
        name = m.split(".")[1].replace("_", "").lower()
        if mod._SUPPORTS_AXIS_LOGOS:
            assert name in drawing.replace("_", "").lower(), m
            kw = {p.name for p in inspect.signature(mod.axis_logos).parameters.values() if p.kind is p.KEYWORD_ONLY}
            assert {"league", "season", "height", "variant", "mark_type", "id_system"} <= kw, m
        else:
            assert name in raising.replace("_", "").lower(), m
            with pytest.raises(TypeError):
                mod.axis_logos(object(), "x", league="nfl")

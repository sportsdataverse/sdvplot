import importlib

import pytest

pytest.importorskip("sportypy")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import sdvplot  # noqa: E402
import sdvplot.matplotlib as smpl  # noqa: E402
from sdvplot import _surface  # noqa: E402
from sdvplot._errors import OptionalDependencyError  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


@pytest.mark.parametrize("league", sorted(_surface.SURFACES))
def test_every_color_key_exists_on_its_sportypy_surface(league):
    sport, cls_name = _surface.SURFACES[league]
    defaults = getattr(importlib.import_module(f"sportypy.surfaces.{sport}"), cls_name)().feature_colors
    assert set(_surface.color_updates(sport, "#123456", "#abcdef")) <= set(defaults)


def test_basketball_ink_reads_on_the_team_color():
    assert _surface.color_updates("basketball", "#000000", None)["restricted_arc"] == "#ffffff"
    assert _surface.color_updates("basketball", "#ffc20e", None)["restricted_arc"] == "#000000"


def test_hockey_uses_the_secondary_color_when_the_primary_vanishes_on_ice():
    assert _surface.color_updates("hockey", "#f4f4f4", "#003594")["center_line"] == "#003594"
    assert _surface.color_updates("hockey", "#003594", "#f4f4f4")["center_line"] == "#003594"
    assert _surface.color_updates("hockey", "#f4f4f4", None)["center_line"] == "#f4f4f4"


def test_baseball_and_soccer_take_no_team_color():
    assert _surface.color_updates("baseball", "#123456", None) == {}
    assert _surface.color_updates("soccer", "#123456", None) == {}


def test_surface_passes_the_team_colors_to_sportypy(monkeypatch):
    import sportypy.surfaces.football as football

    seen = {}

    class Recording(football.NFLField):
        def __init__(self, **kw):
            seen.update(kw)
            super().__init__(**kw)

    monkeypatch.setattr(football, "NFLField", Recording)
    ax = sdvplot.surface("nfl", "LV", color_updates={"defensive_endzone": "#ff0000"})
    assert ax is not None
    assert seen["color_updates"] == {"offensive_endzone": "#000000", "defensive_endzone": "#ff0000"}


def test_surface_draws_the_center_logo(mark_images):
    ax = sdvplot.surface("nfl", "LV", center_logo=True)
    assert [m[:4] for m in smpl.drawn_marks(ax)] == [("13", 0.0, 0.0, 0.25)]


def test_an_unknown_league_lists_the_supported_ones():
    with pytest.raises(ValueError, match=r"no sportypy surface for league 'cricket'; supported: \['aaf'"):
        sdvplot.surface("cricket")


def test_a_missing_sportypy_names_the_extra(monkeypatch):
    def gone(name, *a, **k):
        raise ModuleNotFoundError(name, name="sportypy")

    monkeypatch.setattr(_surface.importlib, "import_module", gone)
    with pytest.raises(OptionalDependencyError, match=r"pip install sdvplot\[surfaces\]"):
        sdvplot.surface("nfl")

import importlib

import pytest

pytest.importorskip("sportypy")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import sdvplot  # noqa: E402
import sdvplot.matplotlib as smpl  # noqa: E402
from sdvplot import _surface  # noqa: E402
from sdvplot._errors import InputError, OptionalDependencyError  # noqa: E402

SURFACES_BEFORE_2_3 = [  # the keys sdvplot drew before sportyR 2.3.0 (pwhl re-pointed to its own rink)
    "nfl", "aaf", "ufl", "usfl", "xfl", "cfb", "nba", "nbagl", "wnba", "mbb", "wbb", "mlb", "milb", "ncaa_baseball",
    "nhl", "whl", "pwhl", "ahl", "echl", "ohl", "qmjhl", "ushl", "phf", "ncaa_mhockey", "ncaa_whockey", "soccer", "fiba",
]  # fmt: skip


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


# The SDV surface-key table, shared with sdvplot-js (src/surfaces.ts SURFACES) and sdvplotR (surface_map): each key's
# sport and sportypy league code (sportyR's, which spells "little league" with a space)
SURFACE_TABLE = {
    **dict.fromkeys(["nfl", "aaf", "ufl", "usfl", "xfl"], ("football", "nfl")),
    "cfb": ("football", "ncaa"),
    "cfl": ("football", "cfl"),
    "nfhs_football": ("football", "nfhs11"),
    "nba": ("basketball", "nba"),
    "nbagl": ("basketball", "nba g league"),
    "wnba": ("basketball", "wnba"),
    "mbb": ("basketball", "ncaa"),
    "wbb": ("basketball", "ncaa"),
    "fiba": ("basketball", "fiba"),
    "nfhs_basketball": ("basketball", "nfhs"),
    "mlb": ("baseball", "mlb"),
    "milb": ("baseball", "milb"),
    "ncaa_baseball": ("baseball", "ncaa"),
    "little_league": ("baseball", "little_league"),
    "pony": ("baseball", "pony"),
    "nfhs_baseball": ("baseball", "nfhs"),
    "ncaa_softball": ("softball", "ncaa"),
    "nhl": ("hockey", "nhl"),
    "whl": ("hockey", "nhl"),
    "pwhl": ("hockey", "pwhl"),
    "ahl": ("hockey", "ahl"),
    "echl": ("hockey", "echl"),
    "ohl": ("hockey", "ohl"),
    "qmjhl": ("hockey", "qmjhl"),
    "ushl": ("hockey", "ushl"),
    "phf": ("hockey", "phf"),
    "iihf": ("hockey", "iihf"),
    "nwhl": ("hockey", "nwhl"),
    "ncaa_mhockey": ("hockey", "ncaa"),
    "ncaa_whockey": ("hockey", "ncaa"),
    "soccer": ("soccer", "fifa"),
    "fifa": ("soccer", "fifa"),
    "epl": ("soccer", "epl"),
    "mls": ("soccer", "mls"),
    "nwsl": ("soccer", "nwsl"),
    "ncaa_soccer": ("soccer", "ncaa"),
    "nll": ("lacrosse", "nll"),
    "pll": ("lacrosse", "pll"),
    "world_lacrosse": ("lacrosse", "world lacrosse"),
    "ncaa_mlacrosse": ("lacrosse", "ncaam"),
    "ncaa_wlacrosse": ("lacrosse", "ncaaw"),
    "usa_mlacrosse": ("lacrosse", "usam"),
    "usa_wlacrosse": ("lacrosse", "usaw"),
    **{k: ("tennis", k) for k in ["atp", "wta", "itf", "ita", "usta"]},
    "ncaa_tennis": ("tennis", "ncaa"),
    "fivb": ("volleyball", "fivb"),
    "usa_volleyball": ("volleyball", "usa volleyball"),
    "ncaa_volleyball": ("volleyball", "ncaa"),
    "wcf": ("curling", "wcf"),
    "curling_canada": ("curling", "curling canada"),
}


def test_the_surface_keys_are_the_shared_sdv_table():
    assert len(SURFACE_TABLE) == 59
    assert set(_surface.SURFACES) == set(SURFACE_TABLE)


@pytest.mark.parametrize("league", sorted(SURFACE_TABLE))
def test_each_key_draws_its_sportyr_league(league, capsys):
    sport, code = SURFACE_TABLE[league]
    drawing = _surface._drawing(league)
    assert _surface.SURFACES[league][0] == sport
    assert drawing.league_code == code
    assert capsys.readouterr().out == ""  # sportypy's NWHLRink prints a rename notice


@pytest.mark.parametrize("league", sorted(set(SURFACE_TABLE) - set(SURFACES_BEFORE_2_3)))
def test_every_new_key_draws(league):
    assert sdvplot.surface(league).patches


@pytest.mark.real_index
def test_the_keys_without_team_identities_are_the_ones_not_in_the_index():
    from sdvplot import _index

    assert set(_surface.SURFACES) - _index._leagues(str(_index.data_dir())) == _surface.NO_TEAMS


@pytest.mark.parametrize("league", ["atp", "nll", "epl", "wcf", "fivb", "iihf", "cfl", "little_league"])
def test_a_team_on_a_key_without_team_identities_is_refused(league):
    with pytest.raises(InputError, match=f"no team identities for '{league}'"):
        sdvplot.surface(league, "KC")


@pytest.mark.real_index
def test_ncaa_softball_draws_the_field_in_a_teams_identity(monkeypatch):
    import sdvplot.matplotlib

    seen = {}
    monkeypatch.setattr(sdvplot.matplotlib, "add_logos", lambda ax, x, y, teams, **kw: seen.update(teams=teams, **kw))
    ax = sdvplot.surface("ncaa_softball", "1140", center_logo=True)  # Clemson
    assert ax.patches  # the softball field
    assert seen["teams"] == ["1140"] and seen["league"] == "ncaa_softball"
    assert sdvplot.team_colors("ncaa_softball", "1140") == "#f35b0f"
    assert sdvplot.resolve("1140", "ncaa_softball") == "1140"


def test_pwhl_draws_its_own_rink_without_the_nhl_trapezoid():
    pwhl, nhl = _surface._drawing("pwhl"), _surface._drawing("nhl")
    assert type(pwhl).__name__ == "PWHLRink"
    assert pwhl.rink_params["has_trapezoid"] is False and nhl.rink_params["has_trapezoid"] is True


@pytest.mark.parametrize("league", sorted(set(_surface.SURFACES) - _surface.NO_TEAMS))
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


@pytest.mark.parametrize("sport", ["baseball", "soccer", "softball", "lacrosse", "tennis", "volleyball", "curling"])
def test_sports_without_a_team_painting_take_no_team_color(sport):
    assert _surface.color_updates(sport, "#123456", None) == {}


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
    assert [m[:4] for m in smpl._drawn_marks(ax)] == [("13", 0.0, 0.0, pytest.approx(0.25))]


def test_an_unknown_league_lists_the_supported_ones():
    with pytest.raises(ValueError, match=r"no sportypy surface for league 'cricket'; supported: \['aaf'"):
        sdvplot.surface("cricket")


def test_a_missing_sportypy_names_the_extra(monkeypatch):
    def gone(name, *a, **k):
        raise ModuleNotFoundError(name, name="sportypy")

    monkeypatch.setattr(_surface.importlib, "import_module", gone)
    with pytest.raises(OptionalDependencyError, match=r"pip install sdvplot\[surfaces\]"):
        sdvplot.surface("nfl")


def test_the_center_logo_draws_above_every_surface_feature(mark_images):
    ax = sdvplot.surface("nfl", "LV", center_logo=True)
    (logo,) = [a for a in ax.artists if hasattr(a, "_sdvplot_mark")]
    others = [a.get_zorder() for a in ax.get_children() if a is not logo]
    assert logo.get_zorder() > max(others)


@pytest.mark.parametrize("league", sorted(lg for lg, (sport, _) in _surface.SURFACES.items() if sport == "football"))
def test_football_fields_log_no_missing_font(league, caplog):
    # sportypy numbers football yard lines in Clarendon-Regular, which it does not ship: matplotlib logged
    # "findfont: Font family 'Clarendon-Regular' not found" for every number it measured
    with caplog.at_level("WARNING", logger="matplotlib.font_manager"):
        sdvplot.surface(league).figure.canvas.draw()
    assert not [r for r in caplog.records if "Clarendon" in r.getMessage()]


def test_a_number_font_the_caller_names_wins(monkeypatch):
    seen = {}
    real = importlib.import_module("sportypy.surfaces.football").NFLField

    def spy(**kwargs):
        seen.update(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(importlib.import_module("sportypy.surfaces.football"), "NFLField", spy)
    sdvplot.surface("nfl", field_updates={"number_font": "DejaVu Serif"})
    assert seen["field_updates"]["number_font"] == "DejaVu Serif"


@pytest.mark.parametrize("league", ["nhl", "nba"])
def test_a_rink_or_court_does_not_walk_every_polygon_segment(league, monkeypatch):
    # sportypy draws its circles and arcs as 10,000-point polygons and matplotlib's add_patch walked every segment as a
    # Bezier curve to find the data limits: ~1.3 M segments, 16-19 s per rink or court
    from matplotlib.path import Path

    walked = 0
    walk = Path.iter_bezier

    def counting(self, **kwargs):
        nonlocal walked
        for segment in walk(self, **kwargs):
            walked += 1
            yield segment

    monkeypatch.setattr(Path, "iter_bezier", counting)
    sdvplot.surface(league)
    assert walked < 1_000


def test_polygon_limits_are_matplotlibs_own():
    import contextlib

    import numpy as np
    from matplotlib.patches import Circle, Polygon
    from matplotlib.transforms import Affine2D

    theta = np.linspace(0, 2 * np.pi, 500)
    xy = np.column_stack([3 + 2 * np.cos(theta), -1 + np.sin(theta)])
    bounds = []
    for fast in (False, True):
        _, ax = plt.subplots()
        with _surface._polygon_limits(ax) if fast else contextlib.nullcontext():
            ax.add_patch(Polygon(xy, closed=True))
            ax.add_patch(Polygon(xy * 2, closed=False, transform=Affine2D().rotate_deg(30) + ax.transData))
            ax.add_patch(Polygon(xy[:1] + 50))  # one vertex: no segment, so no limits
            ax.add_patch(Circle((10, 10), 1))  # Bezier curves: matplotlib's own walk
        assert "_update_patch_limits" not in vars(ax)
        bounds.append(ax.dataLim.bounds)
    assert bounds[0] == bounds[1]


def test_polygon_limits_send_an_empty_coded_path_to_matplotlib():
    # an empty StepPatch has a codes array with nothing in it; reading codes[0] raised IndexError
    from matplotlib.patches import StepPatch

    _, ax = plt.subplots()
    with _surface._polygon_limits(ax):
        ax.add_patch(StepPatch([], [0]))


def test_polygon_limits_restore_an_updater_the_axes_already_had():
    _, ax = plt.subplots()
    seen = []

    def own(patch):
        seen.append(patch)

    ax._update_patch_limits = own
    with _surface._polygon_limits(ax), _surface._polygon_limits(ax):  # nested: the outer override survives too
        pass
    assert vars(ax)["_update_patch_limits"] is own
    with _surface._polygon_limits(ax):
        from matplotlib.patches import Circle

        ax.add_patch(Circle((0, 0), 1))  # not a polygon: the Axes' own updater gets it
    assert len(seen) == 1


def test_soccer_defaults_to_a_105_by_68_pitch_and_pitch_updates_win(monkeypatch):
    import sportypy.surfaces.soccer as soccer

    seen = {}

    class Spy(soccer.FIFAPitch):
        def __init__(self, **kwargs):
            seen.update(kwargs)
            super().__init__(**kwargs)

    monkeypatch.setattr(soccer, "FIFAPitch", Spy)
    sdvplot.surface("soccer")
    assert seen["pitch_updates"] == {"pitch_length": 105, "pitch_width": 68}
    sdvplot.surface("soccer", pitch_updates={"pitch_length": 110})
    assert seen["pitch_updates"] == {"pitch_length": 110, "pitch_width": 68}


def test_the_soccer_pitch_is_drawn_at_105_by_68():
    _, xhi = sdvplot.surface("soccer").get_xlim()
    assert 52.5 < xhi < 60  # FIFA's 120 x 90 maximum would put the goal line at 60


def test_fiba_draws_and_refuses_a_team():
    _, xhi = sdvplot.surface("fiba").get_xlim()
    assert 14 < xhi < 20  # a 28 m court
    with pytest.raises(InputError, match="no team identities for 'fiba'"):
        sdvplot.surface("fiba", "ESP")

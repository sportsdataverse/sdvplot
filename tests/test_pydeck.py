"""sdvplot.pydeck: layer props for pydeck (tests/test_pydeck_shared.py holds them to sdvplot-js's ./deckgl)."""

import math
import re
from pathlib import Path

import polars as pl
import pytest

pydeck = pytest.importorskip("pydeck")  # sdvplot.pydeck needs it at import, as every adapter needs its library

import sdvplot  # noqa: E402
import sdvplot.pydeck as sdeck  # noqa: E402
from sdvplot._contrast import contrast  # noqa: E402
from sdvplot._team_palette import MIN_CONTRAST, MIN_DELTA_E, delta_e, team_palette  # noqa: E402
from tests.test_pydeck_shared import shared_manifest  # noqa: E402, F401  (a fixture)

ROOT = Path(__file__).parents[1]
# Real rows: the first shots of game 7 of the 2024 Stanley Cup Final (NHL api-web play-by-play, feet from centre ice)
# and France's first completed passes of the 2018 World Cup final (StatsBomb open data through SPADL, metres; France
# is ESPN soccer team 478), as in tests/fixtures/deckgl_shared.json.
SHOTS = [
    {"event_id": 251, "team": "EDM", "x": 82, "y": -3},
    {"event_id": 55, "team": "FLA", "x": -81, "y": 30},
    {"event_id": 81, "team": "EDM", "x": 64, "y": 4},
]
PASSES = [
    {"team": "478", "start_x": 54.68750000000001, "start_y": 6.375, "end_x": 56.4375, "end_y": 1.2750000000000057},
    {"team": "478", "start_x": 22.3125, "start_y": 9.775000000000006, "end_x": 6.5625, "end_y": 31.875},
]
ARC = {"x": "start_x", "y": "start_y", "xend": "end_x", "yend": "end_y", "team": "team", "league": "soccer"}
FRANCE = {**ARC, "id_system": "team_id"}
LOGOS = {"x": "x", "y": "y", "team": "team", "league": "nhl"}


def rgba(color):
    return [int(color[i : i + 2], 16) for i in (1, 3, 5)] + [int(color[7:9], 16) if len(color) == 9 else 255]


def hexed(c):
    return "#" + "".join(f"{v:02x}" for v in c[:3])


pytestmark = pytest.mark.real_index


def test_logos_sit_at_each_rows_xy_as_auto_packed_icons_centred(shared_manifest):  # noqa: F811
    props = sdeck.logo_icon_layer(SHOTS, **LOGOS)
    assert props["type"] == "IconLayer"
    data = props["data"]
    assert [d["position"] for d in data] == [[82, -3], [-81, 30], [64, 4]]
    edm, fla = sdvplot.logo_url("EDM", "nhl"), sdvplot.logo_url("FLA", "nhl")
    assert [d["icon"]["url"] for d in data] == [edm, fla, edm]
    # the archive's EDM and FLA logos are 500 x 500: the atlas cell keeps that aspect, 128 px tall
    assert data[0]["icon"] == {"url": edm, "width": 128, "height": 128, "anchorY": 64, "mask": False}
    assert [d["team"] for d in data] == sdvplot.resolve(["EDM", "FLA", "EDM"], "nhl")
    assert [d["index"] for d in data] == [0, 1, 2]
    rest = {k: v for k, v in props.items() if k not in ("type", "data")}
    assert rest == {"id": "sdvplot-logos", "get_position": "position", "get_icon": "icon", "get_size": 32,
                    "size_units": "'pixels'", "opacity": 1.0}  # fmt: skip


def test_a_polars_or_pandas_frame_gives_the_same_props_as_rows(shared_manifest):  # noqa: F811
    pd = pytest.importorskip("pandas")
    want = sdeck.logo_icon_layer(SHOTS, **LOGOS)
    assert sdeck.logo_icon_layer(pl.DataFrame(SHOTS), **LOGOS) == want
    assert sdeck.logo_icon_layer(pd.DataFrame(SHOTS), **LOGOS) == want


def test_a_season_column_is_read_per_row(shared_manifest):  # noqa: F811
    rows = [{**r, "season": 2024} for r in SHOTS]
    assert sdeck.logo_icon_layer(rows, **LOGOS, season="season") == sdeck.logo_icon_layer(SHOTS, **LOGOS, season=2024)


def test_size_is_px_and_alpha_the_opacity_and_both_are_checked(shared_manifest):  # noqa: F811
    props = sdeck.logo_icon_layer(SHOTS, **LOGOS, size=48, alpha=0.5, id="shots")
    assert (props["id"], props["get_size"], props["opacity"]) == ("shots", 48, 0.5)
    for size in (0.1, 0, math.nan):
        with pytest.raises(sdvplot.InputError, match="px"):
            sdeck.logo_icon_layer(SHOTS, **LOGOS, size=size)
    with pytest.raises(sdvplot.InputError, match="alpha"):
        sdeck.logo_icon_layer(SHOTS, **LOGOS, alpha=2)


def test_a_team_with_no_logo_is_left_out_with_one_warning(shared_manifest):  # noqa: F811
    with pytest.warns(sdvplot.SdvplotWarning, match="did not resolve") as rec:
        props = sdeck.logo_icon_layer([{"team": "XXX", "x": 1, "y": 1}, *SHOTS], **LOGOS)
    assert len(rec) == 1
    assert [d["index"] for d in props["data"]] == [1, 2, 3]


def test_strict_raises_for_a_team_that_does_not_resolve(shared_manifest):  # noqa: F811
    with pytest.raises(sdvplot.UnresolvedTeamError, match="'XXX'"):
        sdeck.logo_icon_layer([{"team": "XXX", "x": 1, "y": 1}], **LOGOS, strict=True)
    with pytest.raises(sdvplot.UnresolvedTeamError, match="'XXX'"):
        sdeck.pass_arc_layer([{"team": "XXX", "start_x": 1, "start_y": 1, "end_x": 2, "end_y": 2}], **ARC, strict=True)


def test_a_row_with_a_missing_x_is_left_out_with_one_warning(shared_manifest):  # noqa: F811
    with pytest.warns(sdvplot.SdvplotWarning, match="missing x or y") as rec:
        props = sdeck.logo_icon_layer([*SHOTS, {"team": "FLA", "x": None, "y": 2}], **LOGOS)
    assert len(rec) == 1
    assert [d["index"] for d in props["data"]] == [0, 1, 2]


def test_a_column_not_in_the_rows_is_an_input_error():
    with pytest.raises(sdvplot.InputError, match="'xc'"):
        sdeck.logo_icon_layer(SHOTS, **{**LOGOS, "x": "xc"})
    with pytest.raises(sdvplot.InputError, match="'xc'"):
        sdeck.pass_arc_layer(pl.DataFrame(PASSES), **{**FRANCE, "x": "xc"})


def test_arcs_run_from_xy_to_their_end_primary_at_the_source_secondary_at_the_target():
    props = sdeck.pass_arc_layer(PASSES, **FRANCE)
    assert props["type"] == "ArcLayer"
    data = props["data"]
    assert [[d["source"], d["target"]] for d in data] == [
        [[r["start_x"], r["start_y"]], [r["end_x"], r["end_y"]]] for r in PASSES
    ]
    (primary,) = sdvplot.team_colors("soccer", ["478"], id_system="team_id")
    (secondary,) = sdvplot.team_colors("soccer", ["478"], which="secondary", id_system="team_id")
    assert all(d["sourceColor"] == rgba(primary) and d["targetColor"] == rgba(secondary) for d in data)
    assert [d["team"] for d in data] == ["478", "478"]
    rest = {k: v for k, v in props.items() if k not in ("type", "data")}
    assert rest == {"id": "sdvplot-arcs", "get_source_position": "source", "get_target_position": "target",
                    "get_source_color": "sourceColor", "get_target_color": "targetColor", "get_width": 2,
                    "width_units": "'pixels'", "opacity": 1.0}  # fmt: skip


def test_which_secondary_swaps_the_ends_and_tilt_and_width_are_checked():
    props = sdeck.pass_arc_layer(PASSES, **FRANCE, which="secondary", tilt=90, width=3)
    (primary,) = sdvplot.team_colors("soccer", ["478"], id_system="team_id")
    assert props["data"][0]["targetColor"] == rgba(primary)
    assert (props["get_tilt"], props["get_width"]) == (90, 3)
    with pytest.raises(sdvplot.InputError, match="tilt"):
        sdeck.pass_arc_layer(PASSES, **FRANCE, tilt=91)
    with pytest.raises(sdvplot.InputError, match="width"):
        sdeck.pass_arc_layer(PASSES, **FRANCE, width=0)
    assert sdeck.pass_arc_layer(PASSES, **FRANCE, height=0.3)["get_height"] == 0.3
    assert "get_height" not in sdeck.pass_arc_layer(PASSES, **FRANCE)
    with pytest.raises(sdvplot.InputError, match="height"):
        sdeck.pass_arc_layer(PASSES, **FRANCE, height=-1)
    with pytest.raises(sdvplot.InputError, match="which"):
        sdeck.pass_arc_layer(PASSES, **FRANCE, which="tertiary")


def test_dark_mode_keeps_every_color_readable_through_the_shared_palette():
    background = "#181a1b"
    props = sdeck.pass_arc_layer(PASSES, **FRANCE, background=background)
    source, target = (hexed(props["data"][0][k]) for k in ("sourceColor", "targetColor"))
    (primary,) = sdvplot.team_colors("soccer", ["478"], id_system="team_id")
    (secondary,) = sdvplot.team_colors("soccer", ["478"], which="secondary", id_system="team_id")
    assert contrast(primary, background) < MIN_CONTRAST  # France's navy on a dark chart
    assert source == team_palette([primary], [secondary], background)[0]
    assert target == team_palette([secondary], [primary], background)[0]
    assert all(contrast(c, background) >= MIN_CONTRAST for c in (source, target))


def test_teams_keep_one_color_each_and_stay_distinct():
    rows = [
        {"team": "GS", "x": 0, "y": 0, "xe": 1, "ye": 1},
        {"team": "LAL", "x": 0, "y": 0, "xe": 2, "ye": 2},
        {"team": "GS", "x": 0, "y": 0, "xe": 3, "ye": 3},
    ]
    props = sdeck.pass_arc_layer(rows, x="x", y="y", xend="xe", yend="ye", team="team", league="nba",
                                 background="#181a1b")  # fmt: skip
    src = [hexed(d["sourceColor"]) for d in props["data"]]
    assert src[0] == src[2]
    assert delta_e(src[0], src[1]) >= MIN_DELTA_E


def test_an_unknown_team_takes_the_fallback_and_a_missing_end_is_left_out():
    rows = [
        {"team": "XXX", "start_x": 1, "start_y": 1, "end_x": 2, "end_y": 2},
        {"team": "478", "start_x": 1, "start_y": None, "end_x": 2, "end_y": 2},
        *PASSES,
    ]
    with pytest.warns(sdvplot.SdvplotWarning) as rec:
        props = sdeck.pass_arc_layer(rows, **FRANCE)
    assert len(rec) == 2
    assert any("missing coordinate" in str(w.message) for w in rec)
    assert any("did not resolve" in str(w.message) for w in rec)
    data = props["data"]
    assert [d["index"] for d in data] == [0, 2, 3]
    assert (data[0]["sourceColor"], data[0]["team"]) == ([128, 128, 128, 255], "XXX")


def test_where_only_one_of_a_teams_colors_reads_both_ends_take_it_and_where_both_read_they_differ():
    def ends(background):
        d = sdeck.pass_arc_layer(PASSES, **FRANCE, background=background)["data"][0]
        return hexed(d["sourceColor"]), hexed(d["targetColor"])

    source, target = ends("#195f0c")  # sportypy's default grass: France's navy is under 3:1 (the documented caveat)
    assert source == target
    source, target = ends("#4a7f3a")  # a mid-tone grass: navy and mint both read, so the arcs show their direction
    assert source != target
    assert all(contrast(c, "#4a7f3a") >= MIN_CONTRAST for c in (source, target))


def test_an_unresolved_team_takes_the_fallback_as_given_and_stays_out_of_the_palette():
    background = "#7a7a7a"  # a grey on which the fallback grey does not read: the palette would have moved it
    rows = [{"team": "XXX", "start_x": 1, "start_y": 1, "end_x": 2, "end_y": 2}, *PASSES]
    with pytest.warns(sdvplot.SdvplotWarning) as rec:
        props = sdeck.pass_arc_layer(rows, **FRANCE, background=background)
    assert not any(re.search(r"\b(None|null)\b", str(w.message)) for w in rec)
    data = props["data"]
    assert data[0]["sourceColor"] == data[0]["targetColor"] == [128, 128, 128, 255]
    (primary,) = sdvplot.team_colors("soccer", ["478"], id_system="team_id")
    (secondary,) = sdvplot.team_colors("soccer", ["478"], which="secondary", id_system="team_id")
    assert hexed(data[1]["sourceColor"]) == team_palette([primary], [secondary], background)[0]


def test_an_unresolved_team_is_named_by_its_value_as_text_as_sdvplot_js_names_it():
    rows = [
        {"team": None, "start_x": 1, "start_y": 1, "end_x": 2, "end_y": 2},
        {"team": 123456.0, "start_x": 1, "start_y": 1, "end_x": 2, "end_y": 2},  # a float id, as pandas leaves one
    ]
    with pytest.warns(sdvplot.SdvplotWarning, match="did not resolve"):
        props = sdeck.pass_arc_layer(rows, **FRANCE)
    assert [d["team"] for d in props["data"]] == ["", "123456"]
    assert all(d["sourceColor"] == [128, 128, 128, 255] for d in props["data"])


def _sportypy_rink():
    from sportypy.surfaces.hockey import HockeyRink

    return HockeyRink(league_code="nhl")


def test_the_rink_is_cartesian_polygons_in_sportypys_order_and_colors():
    pytest.importorskip("sportypy")
    props = sdeck.surface_layer("hockey", "nhl")
    assert props["type"] == "PolygonLayer"
    assert {k: v for k, v in props.items() if k not in ("type", "data")} == {
        "id": "sdvplot-surface", "get_polygon": "polygon", "get_fill_color": "fillColor",
        "coordinate_system": "'cartesian'", "filled": True, "stroked": False,
    }  # fmt: skip
    data = props["data"]
    shown = sorted(
        ((f.plot_kwargs["zorder"], i, f) for i, f in enumerate(_sportypy_rink()._features) if f.visible),
        key=lambda t: t[:2],
    )
    # one row per closed loop, in sportypy's order: the same features (a faceoff circle's two half rings are two rows)

    def runs(names):
        return [n for i, n in enumerate(names) if i == 0 or n != names[i - 1]]

    snake = [re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", type(f).__name__).lower() for *_, f in shown]
    assert runs([d["name"] for d in data]) == runs(snake)
    assert data[0]["name"] == "defensive_zone" and data[-1]["name"] == "penalty_box_outline"
    assert any(d["name"] == "odzone_faceoff_circle" for d in data)  # ODZoneFaceoffCircle, snake-cased
    # the goal frame fill is translucent (#a5acaf4d): its alpha survives
    assert next(d for d in data if d["name"] == "goal_frame_fill")["fillColor"] == [165, 172, 175, 77]


def test_a_faceoff_circles_two_half_rings_are_two_closed_loops():
    pytest.importorskip("sportypy")
    rows = [d for d in sdeck.surface_layer("hockey", "nhl")["data"] if d["name"] == "odzone_faceoff_circle"]
    assert len(rows) == 8  # four circles, two half rings each: sportypy draws each circle as one path of both
    assert all(r["polygon"][-1] == r["polygon"][0] for r in rows)
    left, right = ([p[0] for p in r["polygon"]] for r in rows[:2])
    assert max(left) <= min(right) + 1e-9  # each half on its own side of the circle's centre


def test_tolerance_thins_sportypys_arcs_and_zero_keeps_every_point():
    pytest.importorskip("sportypy")
    every = sum(len(f._translate_feature()) for f in _sportypy_rink()._features if f.visible)
    kept = sum(len(d["polygon"]) for d in sdeck.surface_layer("hockey", "nhl", tolerance=0)["data"])
    thin = sum(len(d["polygon"]) for d in sdeck.surface_layer("hockey", "nhl")["data"])
    assert kept == every
    assert thin < every / 50  # 1.2 million points to about 16,000
    with pytest.raises(sdvplot.InputError, match="tolerance"):
        sdeck.surface_layer("hockey", "nhl", tolerance=-1)


LEAGUE_OF = {"baseball": "mlb", "basketball": "nba", "curling": "wcf", "football": "nfl", "hockey": "nhl",
             "soccer": "fifa", "tennis": "atp"}  # fmt: skip


def _area(polygon):
    n = len(polygon)
    return abs(sum(polygon[i][0] * polygon[i - 1][1] - polygon[i - 1][0] * polygon[i][1] for i in range(n))) / 2


@pytest.mark.parametrize(
    ("sport", "tolerance"), [*((s, None) for s in LEAGUE_OF), ("hockey", 0.25)], ids=lambda v: str(v)
)
def test_thinning_keeps_every_loops_area_within_5_percent(sport, tolerance):
    # thin features (a 2-inch goal line, a curling centre line, a foul line, a faceoff ring) keep their corners and
    # width: before the per-loop cap and the long-segment ends, some lost half their area, or all of it
    pytest.importorskip("sportypy")
    full = sdeck.surface_layer(sport, LEAGUE_OF[sport], tolerance=0)["data"]
    thin = sdeck.surface_layer(sport, LEAGUE_OF[sport], tolerance=tolerance)["data"]
    assert [d["name"] for d in thin] == [d["name"] for d in full]
    off = [
        (a["name"], round(abs(_area(b["polygon"]) - _area(a["polygon"])) / _area(a["polygon"]), 3))
        for a, b in zip(full, thin, strict=True)
        if _area(a["polygon"]) > 1e-9 and abs(_area(b["polygon"]) - _area(a["polygon"])) > 0.05 * _area(a["polygon"])
    ]
    assert off == []


def test_sportypys_own_arguments_pass_through_and_a_hidden_feature_is_left_out():
    pytest.importorskip("sportypy")
    props = sdeck.surface_layer("hockey", "nhl", color_updates={"boards": "#ff4c00", "referee_crease": "#00000000"})
    data = props["data"]
    assert next(d for d in data if d["name"] == "boards")["fillColor"] == rgba("#ff4c00")
    assert not any(d["name"] == "referee_crease" for d in data)
    pitch = sdeck.surface_layer("soccer", "fifa", pitch_updates={"pitch_length": 105, "pitch_width": 68})
    assert max(p[0] for d in pitch["data"] for p in d["polygon"]) == pytest.approx(55.2)


def test_an_unknown_sport_or_league_is_an_input_error():
    pytest.importorskip("sportypy")
    with pytest.raises(sdvplot.InputError, match="lacrosse"):
        sdeck.surface_layer("lacrosse", "nll")
    with pytest.raises(sdvplot.InputError, match="'xyz'"):
        sdeck.surface_layer("hockey", "xyz")


def test_deck_fits_an_orthographic_view_to_a_surface_and_draws_the_marks_in_its_frame(shared_manifest):  # noqa: F811
    pytest.importorskip("sportypy")
    rink = sdeck.surface_layer("hockey", "nhl")
    logos = sdeck.logo_icon_layer(SHOTS, **LOGOS)
    d = sdeck.deck(rink, logos, height=300, width=600)
    assert isinstance(d, pydeck.Deck)
    (view,) = d.views
    assert view.type == "OrthographicView" and view.flip_y is False
    state = d.initial_view_state
    assert state.target == pytest.approx([0, 0.45835, 0], abs=1e-4)  # the centre: y from -47.9 (penalty boxes) to 48.8
    assert state.zoom == pytest.approx(math.log2(600 / 200.8334))  # the 200.8 ft rink fills the 600 px width
    assert [layer.type for layer in d.layers] == ["PolygonLayer", "IconLayer"]
    # pydeck strips the quotes: deck.gl gets the constant "cartesian", not an expression ("@@=...")
    assert all('"coordinateSystem": "cartesian"' in layer.to_json() for layer in d.layers)


def test_deck_without_a_surface_is_a_map_fitted_to_the_positions(shared_manifest):  # noqa: F811
    # Rogers Place and Amerant Bank Arena, by longitude and latitude
    rows = [{"team": "EDM", "x": -113.4977, "y": 53.5469}, {"team": "FLA", "x": -80.3256, "y": 26.1584}]
    d = sdeck.deck(sdeck.logo_icon_layer(rows, **LOGOS))
    assert d.views is None or d.views == [] or d.views[0].type == "MapView"
    assert -113.5 < d.initial_view_state.longitude < -80.3
    assert 26.1 < d.initial_view_state.latitude < 53.6
    assert isinstance(d.layers[0], pydeck.Layer)
    with pytest.raises(sdvplot.InputError, match="at least one layer"):
        sdeck.deck()


def test_the_pydeck_floor_is_the_version_the_lock_tests():
    (floor,) = re.findall(r'^pydeck = \["pydeck>=([\d.]+)"\]', (ROOT / "pyproject.toml").read_text(), re.M)
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    (locked,) = re.findall(r'^name = "pydeck"\nversion = "([\d.]+)"', lock, re.M)
    assert floor == locked == "0.9.3"  # 2026-07-02, the newest pydeck at least two weeks old on 2026-10-18

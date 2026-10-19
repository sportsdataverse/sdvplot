"""sdvplot.perspective: the Perspective viewer config and the logo column, on real data (the 2024 NFL regular season's
offense by team, tests/fixtures/nfl_2024_team_epa.csv) and the shipped index. What Perspective 5.5.1 does with each key
was checked in Chromium (the cookbook renders it); these tests pin the dicts and frames that sdvplot hands it."""

import re
from pathlib import Path

import pandas as pd
import polars as pl
import pytest

pytest.importorskip("perspective")

import sdvplot  # noqa: E402
from sdvplot import InputError, SdvplotWarning, UnresolvedTeamError, table_theme_spec  # noqa: E402
from sdvplot._contrast import contrast  # noqa: E402
from sdvplot._team_palette import delta_e  # noqa: E402
from sdvplot.perspective import perspective_logo_column, perspective_sdv_config  # noqa: E402

pytestmark = pytest.mark.real_index
EPA = pl.read_csv(Path(__file__).parent / "fixtures" / "nfl_2024_team_epa.csv")  # posteam, plays, epa_per_play, ...
GRADIENT = re.compile(r"^linear-gradient\(to right, (#[0-9a-f]{6}(?:, #[0-9a-f]{6})*)\)$")


def _colors(css):
    m = GRADIENT.match(css)
    assert m, css
    return m.group(1).split(", ")


def test_the_grid_fills_each_team_cell_in_the_order_perspective_first_draws_it():
    # the Datagrid gives a string column's palette to its values in the order it draws them: the frame's row order
    frame = EPA.sort("epa_per_play", descending=True)
    cfg = perspective_sdv_config(frame, team_col="posteam", league="nfl")
    assert cfg["plugin"] == "Datagrid" and cfg["theme"] == "Pro Light"
    team = cfg["columns_config"]["posteam"]
    assert team["bg_mode"] == "series"
    colors = _colors(team["bg_color"])
    order = frame["posteam"].to_list()
    assert len(colors) == 32 and order[0] == "BAL"
    # each color is that team's own (made readable and distinct on Pro Light's #ffffff): Baltimore's purple is first
    assert colors[0] == sdvplot.team_colors("nfl", "BAL")
    assert all(contrast(c, "#ffffff") >= 3 for c in colors)
    assert min(delta_e(a, b) for i, a in enumerate(colors) for b in colors[:i]) >= 20


def test_a_chart_colors_split_series_in_sorted_order_and_the_color_slot_in_the_frames_order():
    frame = EPA.sort("epa_per_play", descending=True)
    cfg = perspective_sdv_config(frame, team_col="posteam", league="nfl", plugin="Y Bar")
    # the view is the caller's: split_by the team for bars and lines, or the team column in a scatter's Color slot
    # (a scatter's split_by draws a panel per team). Perspective sorts split values, but gives a Color slot's
    # categories their colors in the order it meets them: the rows' order. Checked in Chromium on 5.5.1.
    assert cfg["plugin"] == "Y Bar" and "split_by" not in cfg and "plugin_config" not in cfg
    assert set(cfg["columns_config"]) == {"posteam", "plays", "epa_per_play", "success_rate"}
    values = {k: _colors(v["palette"]) for k, v in cfg["columns_config"].items() if k != "posteam"}
    assert len({tuple(p) for p in values.values()}) == 1  # one palette on every value column
    ascending = values["epa_per_play"]
    by_appearance = _colors(cfg["columns_config"]["posteam"]["palette"])
    color = dict(zip(sorted(frame["posteam"]), ascending, strict=True))
    assert by_appearance == [color[t] for t in frame["posteam"]]
    # a team keeps one color whatever the frame's order: the grid's fill is the same mapping
    grid = _colors(
        perspective_sdv_config(frame, team_col="posteam", league="nfl")["columns_config"]["posteam"]["bg_color"]
    )
    assert grid == by_appearance
    shuffled = perspective_sdv_config(EPA.sort("plays"), team_col="posteam", league="nfl", plugin="Y Bar")
    assert _colors(shuffled["columns_config"]["plays"]["palette"]) == ascending
    assert ascending[0] == sdvplot.team_colors("nfl", "ARI")


def test_dark_mode_keeps_every_team_3_to_1_on_pro_dark():
    cfg = perspective_sdv_config(EPA, team_col="posteam", league="nfl", plugin="Y Line", mode="dark")
    assert cfg["theme"] == "Pro Dark"
    colors = _colors(cfg["columns_config"]["epa_per_play"]["palette"])
    assert all(contrast(c, "#242526") >= 3 for c in colors)  # Pro Dark's --psp--background-color
    light = _colors(perspective_sdv_config(EPA, team_col="posteam", league="nfl", plugin="Y Line")["columns_config"]
                    ["epa_per_play"]["palette"])  # fmt: skip
    assert colors != light


def test_a_background_overrides_the_perspective_theme_one():
    cfg = perspective_sdv_config(EPA, team_col="posteam", league="nfl", plugin="Y Bar", background="#14171c")
    assert all(contrast(c, "#14171c") >= 3 for c in _colors(cfg["columns_config"]["plays"]["palette"]))


def test_a_registry_theme_sets_the_grid_fonts_and_the_sign_colors():
    spec = table_theme_spec("datagolf")
    cfg = perspective_sdv_config(EPA, team_col="posteam", league="nfl", theme="datagolf")
    assert cfg["plugin_config"] == {"font_family": spec.fonts["body"], "font_size": spec.sizes["body"]}
    neg, pos = spec.palette["neg"], spec.palette["pos"]
    for col in ("plays", "epa_per_play", "success_rate"):
        assert cfg["columns_config"][col]["fg_color"] == f"linear-gradient(to right, {neg} 0%, {pos} 100%)"
    dark = perspective_sdv_config(EPA, team_col="posteam", league="nfl", theme="datagolf", mode="dark")
    assert dark["theme"] == "Pro Dark"
    assert dark["columns_config"]["plays"]["fg_color"] != cfg["columns_config"]["plays"]["fg_color"]


def test_a_numeric_font_of_its_own_goes_on_the_numeric_columns():
    tid = next(t["id"] for t in sdvplot.sdv_table_themes() if (f := table_theme_spec(t["id"]).fonts).get("numeric")
               and f["numeric"] != f.get("body"))  # fmt: skip
    spec = table_theme_spec(tid)
    cfg = perspective_sdv_config(EPA, team_col="posteam", league="nfl", theme=tid)
    assert (
        cfg["columns_config"]["epa_per_play"]["font_family"] == spec.fonts["numeric"]
    )  # Perspective quotes it as one name
    assert "font_family" not in cfg["columns_config"]["posteam"]


def test_without_a_theme_there_are_no_fonts_and_no_sign_colors():
    cfg = perspective_sdv_config(EPA, team_col="posteam", league="nfl")
    assert "plugin_config" not in cfg and set(cfg["columns_config"]) == {"posteam"}


def test_polars_and_pandas_give_the_same_config():
    want = perspective_sdv_config(EPA, team_col="posteam", league="nfl", theme="datagolf")
    assert perspective_sdv_config(EPA.to_pandas(), team_col="posteam", league="nfl", theme="datagolf") == want


def test_a_team_that_does_not_resolve_takes_the_fallback_with_one_warning():
    frame = pl.concat([EPA.head(3), pl.DataFrame({"posteam": ["XFL", "USFL"], "plays": [1, 2]}).cast(
        {"plays": pl.UInt32})], how="diagonal_relaxed")  # fmt: skip
    with pytest.warns(SdvplotWarning, match="did not resolve") as rec:
        cfg = perspective_sdv_config(frame, team_col="posteam", league="nfl")
    assert len([w for w in rec if issubclass(w.category, SdvplotWarning)]) == 1
    colors = _colors(cfg["columns_config"]["posteam"]["bg_color"])
    assert colors[3:] == ["#808080", "#808080"]  # kept out of the palette: the real teams' colors do not move
    assert colors[:3] == _colors(perspective_sdv_config(EPA.head(3), team_col="posteam", league="nfl")
                                 ["columns_config"]["posteam"]["bg_color"])  # fmt: skip
    with pytest.raises(UnresolvedTeamError, match="XFL"):
        perspective_sdv_config(frame, team_col="posteam", league="nfl", strict=True)


def test_id_system_and_season_reach_the_resolver():
    with pytest.warns(SdvplotWarning, match="did not resolve"):
        cfg = perspective_sdv_config(EPA.head(2), team_col="posteam", league="nfl", id_system="name")
    assert _colors(cfg["columns_config"]["posteam"]["bg_color"]) == ["#808080", "#808080"]
    with pytest.raises(InputError, match="unknown id_system"):
        perspective_sdv_config(EPA, team_col="posteam", league="nfl", id_system="espnn")
    with pytest.raises(InputError):
        perspective_sdv_config(EPA, team_col="posteam", league="nfl", season=1850)


def test_null_team_values_take_no_color():
    frame = pl.DataFrame({"posteam": ["KC", None, "BUF", "KC"], "epa": [0.1, 0.2, 0.3, 0.4]})
    cfg = perspective_sdv_config(frame, team_col="posteam", league="nfl")
    assert len(_colors(cfg["columns_config"]["posteam"]["bg_color"])) == 2


def test_integer_team_ids_are_not_given_a_grid_fill():
    # Perspective rejects a series fill on a number column; ESPN ids stay numbers (never cast to strings here)
    frame = pl.DataFrame({"team_id": [12, 2], "wins": [15, 13]})  # ESPN ids: Kansas City 12, Buffalo 2
    assert perspective_sdv_config(frame, team_col="team_id", league="nfl")["columns_config"] == {}
    bar = perspective_sdv_config(frame, team_col="team_id", league="nfl", plugin="Y Bar")
    colors = _colors(bar["columns_config"]["wins"]["palette"])
    assert colors == _colors(perspective_sdv_config(pl.DataFrame({"t": ["BUF", "KC"]}), team_col="t", league="nfl")
                             ["columns_config"]["t"]["bg_color"])  # fmt: skip


def test_bad_arguments_raise():
    with pytest.raises(InputError, match="no column 'team'"):
        perspective_sdv_config(EPA, team_col="team", league="nfl")
    with pytest.raises(InputError, match="mode"):
        perspective_sdv_config(EPA, team_col="posteam", league="nfl", mode="dim")
    with pytest.raises(InputError, match="unknown table theme"):
        perspective_sdv_config(EPA, team_col="posteam", league="nfl", theme="datagolff")
    with pytest.raises(InputError, match="no column 'logo'"):
        perspective_sdv_config(EPA, team_col="posteam", league="nfl", logo_col="logo")


# ---- the logo column -----------------------------------------------------------------------------------------------


def test_the_logo_column_sits_after_the_team_and_holds_each_teams_logo_url(manifest):
    frame = EPA.filter(pl.col("posteam").is_in(["LV", "LA"]))
    out = perspective_logo_column(frame, "posteam", league="nfl")
    assert isinstance(out, pl.DataFrame)
    assert out.columns == ["posteam", "posteam_logo", "plays", "epa_per_play", "success_rate"]
    assert out.schema["posteam_logo"] == pl.String
    urls = dict(zip(out["posteam"], out["posteam_logo"], strict=True))
    assert urls == {"LA": sdvplot.logo_url("LA", "nfl"), "LV": sdvplot.logo_url("LV", "nfl")}
    assert urls["LV"] == "https://cdn/1111.png"


def test_a_team_with_no_logo_gets_null_and_one_warning(manifest):
    frame = EPA.filter(pl.col("posteam").is_in(["LV", "KC", "BUF"]))
    with pytest.warns(SdvplotWarning, match="no logo archived") as rec:
        out = perspective_logo_column(frame, "posteam", league="nfl", name="logo")
    assert len([w for w in rec if issubclass(w.category, SdvplotWarning)]) == 1
    assert dict(zip(out["posteam"], out["logo"], strict=True)) == {
        "BUF": None,
        "KC": None,
        "LV": "https://cdn/1111.png",
    }


def test_the_logo_column_keeps_the_frames_library_and_its_rows(manifest):
    frame = EPA.filter(pl.col("posteam").is_in(["LV", "LA"])).to_pandas()
    frame.index = [10, 20]
    out = perspective_logo_column(frame, "posteam", league="nfl")
    assert isinstance(out, pd.DataFrame) and list(out.index) == [10, 20]
    assert out["posteam_logo"].tolist() == [sdvplot.logo_url(t, "nfl") for t in frame["posteam"]]


def test_the_logo_column_resolves_each_distinct_team_once(manifest, monkeypatch):
    from sdvplot import perspective as mod

    seen = []
    real = mod.place
    monkeypatch.setattr(mod, "place", lambda x, y, teams, **kw: seen.append(list(teams)) or real(x, y, teams, **kw))
    frame = pl.DataFrame({"posteam": ["LV", "LV", "LA", "LV"]})
    out = perspective_logo_column(frame, "posteam", league="nfl")
    assert seen == [["LV", "LA"]] and out["posteam_logo"].null_count() == 0


def test_the_logo_column_name_must_be_new(manifest):
    with pytest.raises(InputError, match="already has a column 'plays'"):
        perspective_logo_column(EPA, "posteam", league="nfl", name="plays")
    with pytest.raises(InputError, match="no column 'team'"):
        perspective_logo_column(EPA, "team", league="nfl")


def test_the_logo_column_strict_raises(manifest):
    with pytest.raises(UnresolvedTeamError, match="XFL"):
        perspective_logo_column(pl.DataFrame({"t": ["LV", "XFL"]}), "t", league="nfl", strict=True)


def test_the_config_shows_the_logo_column_as_a_link(manifest):
    # Perspective 5.5's Datagrid draws no images: a URL column's one format is a link
    frame = perspective_logo_column(EPA.filter(pl.col("posteam").is_in(["LV", "LA"])), "posteam", league="nfl")
    cfg = perspective_sdv_config(frame, team_col="posteam", league="nfl", logo_col="posteam_logo")
    assert cfg["columns_config"]["posteam_logo"] == {"link": True}
    chart = perspective_sdv_config(frame, team_col="posteam", league="nfl", logo_col="posteam_logo", plugin="Y Bar")
    assert "posteam_logo" not in chart["columns_config"]


def test_two_values_naming_one_team_share_its_color():
    frame = pl.DataFrame({"team": ["LA", "Los Angeles Rams", "SF"], "wins": [10, 10, 6]})  # nflverse code, ESPN name
    got = _colors(perspective_sdv_config(frame, team_col="team", league="nfl")["columns_config"]["team"]["bg_color"])
    alone = _colors(perspective_sdv_config(frame.slice(1), team_col="team", league="nfl")["columns_config"]["team"]
                    ["bg_color"])  # fmt: skip
    assert got[0] == got[1] == alone[0] and got[2] == alone[1]


def test_the_perspective_floor_is_the_version_the_lock_tests():
    root = Path(__file__).parents[1]
    (floor,) = re.findall(
        r'^perspective = \["perspective-python\[jupyter\]>=([\d.]+);', (root / "pyproject.toml").read_text(), re.M
    )
    (locked,) = re.findall(
        r'^name = "perspective-python"\nversion = "([\d.]+)"', (root / "uv.lock").read_text(encoding="utf-8"), re.M
    )
    assert floor == locked == "5.5.1"  # 2026-09-18, the newest perspective-python at least two weeks old on 2026-10-19

import json

import polars as pl
import pytest

pytest.importorskip("reactable")
import htmltools  # noqa: E402
from reactable import Reactable, Theme  # noqa: E402
from reactable.tags import to_widget  # noqa: E402

import sdvplot  # noqa: E402
from sdvplot._contrast import contrast  # noqa: E402
from sdvplot._errors import InputError, UnresolvedTeamError  # noqa: E402
from sdvplot.reactable import (  # noqa: E402
    reactable_sdv_frame,
    reactable_sdv_icon_legend,
    reactable_sdv_legend,
    reactable_sdv_theme,
    reactable_sdv_theme_team,
)

# Spot values printed by R from reactablefmtr 2.1.0, each theme with its defaults (`unclass(espn())$headerStyle$color`
# and so on; None: R leaves the property out). Regenerating data/reactablefmtr_themes.json must keep these.
# fmt: off
R_SPOT = {
    "cerulean": {"color": "#141415", "stripedColor": "#e9ecef", "cellPadding": 6, "tableStyle.fontSize": 14, "headerStyle.color": "#cfe9f7", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": "#3ba9e8"},
    "clean": {"color": "#222222", "stripedColor": "#e0e0e0", "cellPadding": 6, "tableStyle.fontSize": 14, "headerStyle.color": "#222222", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": None},
    "cosmo": {"color": "#141415", "stripedColor": "white", "cellPadding": 6, "tableStyle.fontSize": 14, "headerStyle.color": "#ffffff", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": "#373a3c"},
    "cyborg": {"color": "#888888", "stripedColor": "#282828", "cellPadding": 6, "tableStyle.fontSize": 14, "headerStyle.color": "#7b7b7b", "headerStyle.fontSize": "15px", "headerStyle.backgroundColor": "#060606"},
    "dark": {"color": "#FFFFFF", "stripedColor": "#303030", "cellPadding": 6, "tableStyle.fontSize": 15, "headerStyle.color": "#FFFFFF", "headerStyle.fontSize": 16, "headerStyle.backgroundColor": "#252525"},
    "darkly": {"color": "#ffffff", "stripedColor": "#adb5bd", "cellPadding": 6, "tableStyle.fontSize": 14, "headerStyle.color": "#afbdcc", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": "#375a7f"},
    "default": {"color": "#333333", "stripedColor": None, "cellPadding": 6, "tableStyle.fontSize": 15, "headerStyle.color": "#333333", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": None},
    "espn": {"color": "#6C6D6F", "stripedColor": "#fafafa", "cellPadding": 7, "tableStyle.fontSize": 12, "headerStyle.color": "#48494a", "headerStyle.fontSize": 11, "headerStyle.backgroundColor": None},
    "fivethirtyeight": {"color": "#222222", "stripedColor": "#dddddd", "cellPadding": 5, "tableStyle.fontSize": 14, "headerStyle.color": "#000000", "headerStyle.fontSize": 12, "headerStyle.backgroundColor": None},
    "flatly": {"color": "#212529", "stripedColor": "#ecf0f1", "cellPadding": 6, "tableStyle.fontSize": 14, "headerStyle.color": "#ffffff", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": "#2c3e50"},
    "hoverdark": {"color": "#222222", "stripedColor": "#D6D6D6", "cellPadding": 4, "tableStyle.fontSize": 15, "headerStyle.color": None, "headerStyle.fontSize": 15, "headerStyle.backgroundColor": None},
    "hoverlight": {"color": "#ffffff", "stripedColor": "lightgrey", "cellPadding": 4, "tableStyle.fontSize": 15, "headerStyle.color": None, "headerStyle.fontSize": 15, "headerStyle.backgroundColor": None},
    "journal": {"color": "#222222", "stripedColor": "#eeeeee", "cellPadding": 6, "tableStyle.fontSize": 14, "headerStyle.color": "#fad9d8", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": "#ef8683"},
    "lux": {"color": "#8c8c8c", "stripedColor": "#dadada", "cellPadding": 6, "tableStyle.fontSize": 14, "headerStyle.color": "#7f7f7f", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": "#1a1a1a"},
    "midnight": {"color": "#727272", "stripedColor": "#00468c", "cellPadding": 6, "tableStyle.fontSize": 15, "headerStyle.color": "#666666", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": "#000000"},
    "midnightblue": {"color": "#bababa", "stripedColor": "#00468c", "cellPadding": 6, "tableStyle.fontSize": 15, "headerStyle.color": "lightgrey", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": "#001021"},
    "minty": {"color": "#9a9a9a", "stripedColor": "#ededed", "cellPadding": 6, "tableStyle.fontSize": 15, "headerStyle.color": "#c9e7de", "headerStyle.fontSize": 16, "headerStyle.backgroundColor": "#78c2ad"},
    "no_lines": {"color": "#222222", "stripedColor": "lightgrey", "cellPadding": 6, "tableStyle.fontSize": 14, "headerStyle.color": "#222222", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": None},
    "nytimes": {"color": "#333333", "stripedColor": "#e7e7e7", "cellPadding": 5, "tableStyle.fontSize": 13, "headerStyle.color": "#999999", "headerStyle.fontSize": 11, "headerStyle.backgroundColor": None},
    "pff": {"color": "#878e94", "stripedColor": "#f9f9fb", "cellPadding": 4, "tableStyle.fontSize": 16, "headerStyle.color": "#ffffff", "headerStyle.fontSize": 12, "headerStyle.backgroundColor": "#595d63"},
    "sandstone": {"color": "#3e3f3a", "stripedColor": "#ededed", "cellPadding": 6, "tableStyle.fontSize": 15, "headerStyle.color": "#7c7a78", "headerStyle.fontSize": 16, "headerStyle.backgroundColor": "#f8f5f0"},
    "sanfran": {"color": "#222222", "stripedColor": "lightgrey", "cellPadding": 6, "tableStyle.fontSize": 14, "headerStyle.color": "#212121", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": None},
    "slate": {"color": "#aaaaaa", "stripedColor": "#464a4d", "cellPadding": 6, "tableStyle.fontSize": 15, "headerStyle.color": "#97999b", "headerStyle.fontSize": 16, "headerStyle.backgroundColor": "#3a3f44"},
    "spacelab": {"color": "#8e8e8e", "stripedColor": "#dadada", "cellPadding": 6, "tableStyle.fontSize": 14, "headerStyle.color": "#8e8e8e", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": "#ededed"},
    "sunrise": {"color": "#8069ff", "stripedColor": "lightblue", "cellPadding": 6, "tableStyle.fontSize": 15, "headerStyle.color": "#8069ff", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": "#fffa85"},
    "superhero": {"color": "#ebebeb", "stripedColor": "#4a5969", "cellPadding": 6, "tableStyle.fontSize": 14, "headerStyle.color": "#ebebeb", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": "#4e5d6c"},
    "void": {"color": "#222222", "stripedColor": "lightgrey", "cellPadding": 6, "tableStyle.fontSize": 14, "headerStyle.color": "transparent", "headerStyle.fontSize": 15, "headerStyle.backgroundColor": None},
}
# fmt: on
THEMES = sorted(R_SPOT)


def _get(props, path):
    for key in path.split("."):
        if not isinstance(props, dict) or key not in props:
            return None
        props = props[key]
    return props


def test_there_are_27_themes():
    assert len(THEMES) == 27


@pytest.mark.parametrize("name", THEMES)
def test_every_theme_builds_with_reactablefmtrs_values(name):
    theme = reactable_sdv_theme(name)
    assert isinstance(theme, Theme)
    props = theme.to_props()
    for path, expected in R_SPOT[name].items():
        assert _get(props, path) == expected, (name, path)
    assert "@" not in json.dumps(props)  # every sentinel was filled
    Reactable(pl.DataFrame({"team": ["KC"], "wins": [12]}), theme=theme)  # reactable accepts it


def test_arguments_override_the_theme_like_r():
    # R: unclass(nytimes(font_size = 20, border_color = "#000000", centered = TRUE)) -> 20, "#000000", "flex"
    props = reactable_sdv_theme("nytimes", font_size=20, border_color="#000000", centered=True).to_props()
    assert props["tableStyle"]["fontSize"] == 20
    assert props["borderColor"] == "#000000"
    assert props["cellStyle"]["display"] == "flex"
    assert "cellStyle" not in reactable_sdv_theme("nytimes").to_props()


def test_a_sentinel_inside_a_string_is_filled():
    # R void(): headerStyle borderBottom = paste0(header_border_width, "px solid ", header_border_color)
    props = reactable_sdv_theme("void", header_border_width=2, header_border_color="#ff0000").to_props()
    assert props["headerStyle"]["borderBottom"] == "2px solid #ff0000"


def test_background_color_given_and_left_out():
    assert "backgroundColor" not in reactable_sdv_theme("espn").to_props()  # R: background_color = NULL
    assert reactable_sdv_theme("espn", background_color="#f0f0f0").to_props()["backgroundColor"] == "#f0f0f0"


def test_unknown_theme_raises_with_the_list():
    with pytest.raises(InputError, match="unknown theme 'bbc'.*cerulean.*void"):
        reactable_sdv_theme("bbc")


def test_an_argument_the_theme_does_not_take_raises():
    with pytest.raises(InputError, match="has no argument header_font_color"):
        reactable_sdv_theme("hoverdark", header_font_color="#000000")
    with pytest.raises(InputError, match="has no argument border_color"):
        reactable_sdv_theme("espn", border_color="#000000")
    with pytest.raises(InputError, match="centered"):
        reactable_sdv_theme("espn", centered="yes")


@pytest.mark.parametrize(
    ("team", "league"), [("LV", "nfl"), ("LAR", "nfl"), ("LAC", "nfl"), ("KC", "mlb")]
)  # the fixture index
def test_team_theme_uses_the_team_colors_with_readable_ink(team, league):
    primary = sdvplot.team_colors(league, team)
    props = reactable_sdv_theme_team(team, league).to_props()
    header = props["headerStyle"]
    assert header["backgroundColor"] == primary.lower()
    assert contrast(header["color"], header["backgroundColor"]) >= 4.5
    assert contrast(props["color"], props["stripedColor"]) >= 4.5  # body text on the tinted stripes
    assert contrast(props["color"], "#ffffff") >= 4.5
    assert props["pageButtonCurrentStyle"] == {"backgroundColor": header["backgroundColor"], "color": header["color"]}


def test_team_theme_rams_values():
    props = reactable_sdv_theme_team("LAR", "nfl").to_props()
    assert props["headerStyle"]["backgroundColor"] == "#003594"
    assert props["headerStyle"]["color"] == "#ffffff"
    assert props["headerStyle"]["borderBottom"] == "3px solid #ffa300"  # the secondary
    assert props["color"] == "#000000"


def test_team_theme_on_a_dark_background_flips_the_ink():
    props = reactable_sdv_theme_team("LAR", "nfl", background_color="#111111").to_props()
    assert props["color"] == "#ffffff"
    assert contrast(props["color"], props["stripedColor"]) >= 4.5


def test_team_theme_unknown_team_raises():
    with pytest.raises(UnresolvedTeamError):
        reactable_sdv_theme_team("NOPE", "nfl")


def _table():
    return Reactable(pl.DataFrame({"team": ["KC", "BUF"], "wins": [12, 10]}))


def _walk(tag):
    yield tag
    for child in getattr(tag, "children", []):
        yield from _walk(child)


def test_frame_puts_the_furniture_around_the_table():
    table = _table()
    legend = reactable_sdv_legend(colors=["#ffffff", "#000000"])
    framed = reactable_sdv_frame(table, title="AFC", subtitle="2025", source="Data: sdv", legend=legend)
    assert isinstance(framed, htmltools.TagList)
    (div,) = framed
    kinds = [c.name if isinstance(c, htmltools.Tag) else c for c in div.children]
    assert kinds == ["h1", "h2", table, "div", "p"]
    assert div.children[0].children[0] == "AFC"
    assert "font-size:32px" in div.children[0].attrs["style"]
    assert "font-size:24px" in div.children[1].attrs["style"]
    assert "font-size:16px" in div.children[4].attrs["style"]


def test_frame_optional_parts_and_align():
    table = _table()
    (div,) = reactable_sdv_frame(table)
    assert list(div.children) == [table] and "style" not in div.attrs
    (div,) = reactable_sdv_frame(table, title="x", align="right")
    assert "text-align:right" in div.children[0].attrs["style"]
    with pytest.raises(InputError, match="align"):
        reactable_sdv_frame(table, align="middle")


def test_frame_font_loads_the_google_font_for_the_whole_frame():
    (div,) = reactable_sdv_frame(_table(), title="x", font="Roboto Condensed")
    assert div.attrs["style"] == "font-family:Roboto Condensed, sans-serif"
    style = div.children[0]
    assert style.name == "style"
    assert list(style.children) == [
        "@import url(https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700);"
    ]
    with pytest.raises(InputError, match="font"):
        reactable_sdv_frame(_table(), font="x;y:z")


def test_frame_converts_to_one_widget_react_can_render():
    legend = reactable_sdv_icon_legend(icons=["circle", "star"], colors="#ff0000", labels=["a", "b"])
    framed = reactable_sdv_frame(_table(), title="T", source="S", font="Poppins", legend=legend)
    # React refuses children on a void element, and the widget state is JSON: no <link>/<img>, only plain strings
    for tag in _walk(framed[0]):
        if isinstance(tag, htmltools.Tag):
            assert tag.name not in {"link", "img", "br", "meta", "input"}
            assert all(type(c) is str or isinstance(c, (htmltools.Tag, Reactable)) for c in tag.children)
    assert to_widget(framed) is not None
    bundle, _ = framed._repr_mimebundle_()
    assert "application/vnd.jupyter.widget-view+json" in bundle


def test_style_strings_hold_one_colon_per_declaration():
    # reactable's to_widget splits a style on ";" then ":" and raises on a declaration with a second colon
    legend = reactable_sdv_legend(colors=["#d7191c", "#1a9641"], bins=3, labels=[1, 2, 3], title="t", footer="f")
    framed = reactable_sdv_frame(_table(), title="T", subtitle="S", source="X", font="Poppins", legend=legend)
    for tag in _walk(framed[0]):
        if isinstance(tag, htmltools.Tag) and "style" in tag.attrs:
            assert all(decl.count(":") == 1 for decl in tag.attrs["style"].split(";") if decl)


def _swatches(legend):
    return [t for t in _walk(legend) if isinstance(t, htmltools.Tag) and t.name == "span"]


def test_legend_bins_ramp_the_colors():
    legend = reactable_sdv_legend(colors=["#000000", "#ffffff"], bins=3, labels=["lo", "mid", "hi"], title="T")
    assert [s.attrs["style"].split("background:")[1] for s in _swatches(legend)] == ["#000000", "#808080", "#ffffff"]
    assert "lo" in str(legend) and "T" in str(legend)
    assert len(_swatches(reactable_sdv_legend(colors=["#000", "#fff", "#f00"]))) == 3


def test_legend_bad_args_raise():
    with pytest.raises(InputError, match="colors"):
        reactable_sdv_legend(colors=[])
    with pytest.raises(InputError, match="bins"):
        reactable_sdv_legend(colors=["#000000"], bins=1)
    with pytest.raises(InputError, match="labels"):
        reactable_sdv_legend(colors=["#000000", "#ffffff"], labels=["a"])


def test_icon_legend_draws_svg_shapes():
    legend = reactable_sdv_icon_legend(
        icons=["circle", "square"], colors=["#1a9641", "#d7191c"], labels=["won", "lost"]
    )
    html = str(legend)
    assert '<circle cx="8" cy="8" r="7" fill="#1a9641">' in html and 'fill="#d7191c"' in html
    assert "won" in html and "lost" in html
    with pytest.raises(InputError, match="unknown icon 'heart'"):
        reactable_sdv_icon_legend(icons="heart", colors="#000000", labels=["x"])
    with pytest.raises(InputError, match="one entry per label"):
        reactable_sdv_icon_legend(icons=["circle"], colors="#000000", labels=["x", "y"])

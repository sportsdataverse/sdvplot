import warnings

import pandas as pd
import polars as pl
import pytest

pytest.importorskip("reactable")
from reactable import Column, Reactable  # noqa: E402
from reactable.models import CellInfo  # noqa: E402

import sdvplot  # noqa: E402
from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.reactable import (  # noqa: E402
    reactable_sdv_cols_label,
    reactable_sdv_headshots,
    reactable_sdv_logos,
    reactable_sdv_team_color_bar,
    reactable_sdv_team_color_bg,
    reactable_sdv_wordmarks,
)

LV_IMG = (
    '<img src="https://cdn/1111.png" style="height:30px;vertical-align:middle" alt="Las Vegas Raiders" '
    'data-sdvplot-team="13">'
)


def _frame(kind, data):
    return (
        pl.DataFrame(data) if kind == "polars" else pd.DataFrame(data, index=[10 + i for i in range(len(data["team"]))])
    )


FRAMES = pytest.mark.parametrize("kind", ["polars", "pandas"])


def _built(table, column_id):
    """A Reactable runs cell and style functions when it is built; this is a column's built cells or styles."""
    return next(c for c in table.columns if c.id == column_id)


def test_a_logo_column_renders_img_tags(manifest):
    col = reactable_sdv_logos(league="nfl", id="team")
    assert isinstance(col, Column) and col.html is True and col.id == "team"
    assert col.cell(CellInfo("LV", 0, "team")) == LV_IMG
    assert col.cell(CellInfo(None, 1, "team")) == ""


def test_an_unknown_value_keeps_its_text_and_warns_once(manifest):
    col = reactable_sdv_logos(league="nfl", id="team")
    with pytest.warns(SdvplotWarning, match="'<XXX>'"):
        assert col.cell(CellInfo("<XXX>", 0, "team")) == "&lt;XXX&gt;"
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert col.cell(CellInfo("<XXX>", 5, "team")) == "&lt;XXX&gt;"  # the same value again: no second warning


def test_default_img_and_include_name(manifest):
    col = reactable_sdv_logos(league="nfl", default_img="https://x/none.png", include_name=True, id="team")
    assert col.cell(CellInfo("LV", 0, "team")).endswith('data-sdvplot-team="13">LV')
    with pytest.warns(SdvplotWarning):
        assert col.cell(CellInfo("XXX", 0, "team")).startswith('<img src="https://x/none.png"')


@FRAMES
def test_a_reactable_built_from_pandas_or_polars_renders_every_row(manifest, kind):
    df = _frame(kind, {"team": ["LV", "LAR"], "w": [1, 2]})
    table = Reactable(df, columns=[reactable_sdv_logos(league="nfl", id="team", height=24)])
    cells = _built(table, "team").cell
    assert 'data-sdvplot-team="13"' in cells[0] and 'data-sdvplot-team="14"' in cells[1]
    assert all("height:24px" in c for c in cells)


def test_wordmarks_and_headshots(manifest):
    assert "https://cdn/4444.png" in reactable_sdv_wordmarks(league="nfl", id="t").cell(CellInfo("LV", 0, "t"))
    shot = reactable_sdv_headshots(league="nfl", id="p").cell(CellInfo("3139477", 0, "p"))
    assert f'src="{sdvplot.headshot_url("3139477", "nfl")}"' in shot and "height:40px" in shot


@pytest.mark.parametrize("bad", [0, -1, "30px"])
def test_height_is_positive_pixels(bad):
    with pytest.raises(ValueError, match="pixels"):
        reactable_sdv_logos(league="nfl", height=bad, id="team")


@FRAMES
def test_cols_label_gives_team_named_columns_a_mark_header(manifest, kind):
    df = _frame(kind, {"team": ["x"], "LV": [1], "LAR": [2]})
    with pytest.warns(SdvplotWarning, match="'team'"):
        cols = reactable_sdv_cols_label(df, league="nfl", width=60)
    assert [(c.id, c.name, c.width) for c in cols] == [("LV", "", 60), ("LAR", "", 60)]
    assert cols[0].header == LV_IMG and cols[0].html is True
    Reactable(df, columns=cols)  # builds


@FRAMES
def test_team_color_bar_fills_by_share_of_the_max(kind):
    df = _frame(kind, {"team": ["LV", "LAR", "XXX"], "wins": [10, 5, None]})
    with pytest.warns(SdvplotWarning, match="'XXX'"):
        col = reactable_sdv_team_color_bar(df, "team", league="nfl", id="wins")
    styles = _built(Reactable(df, columns=[col]), "wins").style
    assert styles == [
        {"background-image": "linear-gradient(90deg, #000000 100%, transparent 100%)"},
        {"background-image": "linear-gradient(90deg, #003594 50%, transparent 50%)"},
        {"background-image": "linear-gradient(90deg, #b3b3b3 0%, transparent 0%)"},
    ]
    col = reactable_sdv_team_color_bar(df[:2] if kind == "polars" else df.iloc[:2], "team", league="nfl", max_value=40)
    assert col.style(CellInfo(10, 0, "wins")) == {
        "background-image": "linear-gradient(90deg, #000000 25%, transparent 25%)"
    }


@FRAMES
def test_team_color_bg_is_a_translucent_team_fill(kind):
    df = _frame(kind, {"team": ["LAR"], "wins": [5]})
    col = reactable_sdv_team_color_bg(df, "team", league="nfl", which="secondary", id="team")
    assert _built(Reactable(df, columns=[col]), "team").style == [{"background-color": "#ffa30026"}]
    with pytest.raises(ValueError, match="alpha"):
        reactable_sdv_team_color_bg(df, "team", league="nfl", alpha=2)
    with pytest.raises(ValueError, match="'club' not found"):
        reactable_sdv_team_color_bg(df, "club", league="nfl")

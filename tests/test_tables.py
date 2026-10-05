import math

import pytest

from sdvplot._errors import SdvplotWarning
from sdvplot._tables import check_px, img_tag, mark_html


@pytest.mark.parametrize(("given", "want"), [(30, 30.0), (24.5, 24.5), (1, 1.0)])
def test_check_px_accepts_positive_pixels(given, want):
    assert check_px(given) == want


@pytest.mark.parametrize("bad", [0, -5, "30px", None, True, math.nan, math.inf])
def test_check_px_rejects_anything_else(bad):
    with pytest.raises(ValueError, match="pixels"):
        check_px(bad)


@pytest.mark.parametrize("fraction", [0.1, 0.5, 0.999])
def test_a_fractional_table_height_is_an_error_that_names_the_unit(fraction):
    # a plot's height is a fraction of the plot; on a table 0.1 would draw a 0.1 px image
    with pytest.raises(ValueError, match=r"pixels for a table \(such as 30\).*fraction of the plot height"):
        check_px(fraction)


@pytest.mark.parametrize("verb", ["add_logos", "add_wordmarks", "add_headshots"])
def test_the_front_door_rejects_a_fractional_height_on_a_table(manifest, verb):
    pl = pytest.importorskip("polars")
    great_tables = pytest.importorskip("great_tables")
    import sdvplot

    gt = great_tables.GT(pl.DataFrame({"team": ["LV"]}))
    with pytest.raises(ValueError, match="pixels for a table"):
        getattr(sdvplot, verb)(gt, "team", league="nfl", height=0.1)


def test_img_tag_escapes_and_marks_the_team():
    tag = img_tag('https://cdn/a.png?x="1"', 24, "Texas A&M", team="245")
    assert tag == (
        '<img src="https://cdn/a.png?x=&quot;1&quot;" style="height:24px;vertical-align:middle" '
        'alt="Texas A&amp;M" data-sdvplot-team="245">'
    )
    assert "margin-right:0.35em" in img_tag("u", 30, "x", margin=True)
    assert "data-sdvplot-team" not in img_tag("u", 30, "x")


def test_mark_html_resolves_each_value_and_names_the_team(manifest):
    with pytest.warns(SdvplotWarning, match="'XXX'"):
        out = mark_html(["LV", "XXX", 14], league="nfl", kind="logo", height=30)
    assert out[1] is None
    assert 'src="https://cdn/1111.png"' in out[0] and 'alt="Las Vegas Raiders"' in out[0]
    assert 'data-sdvplot-team="14"' in out[2] and 'src="https://cdn/6666.png"' in out[2]


def test_mark_html_takes_one_season_only(manifest):
    assert "https://cdn/3333.png" in mark_html(["LV"], league="nfl", kind="logo", height=30, season=2010)[0]
    with pytest.raises(ValueError, match="season"):
        mark_html(["LV", "LAR"], league="nfl", kind="logo", height=30, season=[2010, 2011])  # not one per value

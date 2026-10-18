import pandas as pd
import pytest

pytest.importorskip("plottable")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from plottable import Table  # noqa: E402

from sdvplot import plottable as sp  # noqa: E402
from sdvplot import sdv_table_themes, table_theme_spec  # noqa: E402
from sdvplot.plottable import plottable_sdv_theme  # noqa: E402


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    sp._warned_fonts.clear()
    monkeypatch.setattr(sp, "_has_font", lambda f: True)  # the font tests below patch it again
    yield
    plt.close("all")


def test_text_color_and_stripe_follow_the_spec():
    spec = table_theme_spec("fangraphs")
    kw = plottable_sdv_theme("fangraphs")
    assert kw["textprops"]["color"] == spec.palette["text"]
    assert kw["facecolor"] == spec.palette["bg"]
    for tid in (t["id"] for t in sdv_table_themes()):
        s = table_theme_spec(tid)
        want = s.palette["stripe"] if s.structure["stripe"] else None
        assert plottable_sdv_theme(tid)["odd_row_color"] == want


def test_header_fill_is_label_bg_and_rendered():
    spec = table_theme_spec("basketball-reference")
    kw = plottable_sdv_theme("basketball-reference")
    assert spec.palette["labelBg"] != spec.palette["bg"]
    assert kw["col_label_cell_kw"] == {"facecolor": spec.palette["labelBg"]}
    fig, ax = plt.subplots()
    kw.pop("facecolor")
    tbl = Table(pd.DataFrame({"a": [1]}), ax=ax, **kw)
    patch = tbl.col_label_row.cells[0].rectangle_patch
    assert matplotlib.colors.to_hex(patch.get_facecolor()) == spec.palette["labelBg"].lower()


def test_dashed_maps_to_dashes_and_double_to_solid():
    assert sp._divider("1px dashed #abcdef") == {"linewidth": 0.75, "linestyle": "--", "color": "#abcdef"}
    assert sp._divider("3px double #000000")["linestyle"] == "-"
    assert sp._divider("none") is None


def test_row_rule_maps_to_dividers():
    for tid in (t["id"] for t in sdv_table_themes()):
        rule = table_theme_spec(tid).structure["rowRule"]
        kw = plottable_sdv_theme(tid)
        assert kw["row_dividers"] is (rule != "none")
        if "dotted" in rule:
            assert kw["row_divider_kw"]["linestyle"] == ":"
    kw = next(
        plottable_sdv_theme(t["id"])
        for t in sdv_table_themes()
        if "1px solid" in table_theme_spec(t["id"]).structure["rowRule"]
    )
    assert kw["row_divider_kw"]["linewidth"] == 0.75


def test_uninstalled_font_falls_back_with_one_warning(monkeypatch):
    monkeypatch.setattr(sp, "_has_font", lambda f: False)
    with pytest.warns(UserWarning, match="not installed") as rec:
        a = plottable_sdv_theme("fangraphs")
        b = plottable_sdv_theme("fangraphs")
    assert len([w for w in rec if "not installed" in str(w.message)]) == 1
    assert a["textprops"]["fontfamily"] == b["textprops"]["fontfamily"] == "sans-serif"


@pytest.mark.parametrize("tid", [t["id"] for t in sdv_table_themes()])
def test_every_theme_renders(tid):
    kw = plottable_sdv_theme(tid)
    fig, ax = plt.subplots()
    bg = kw.pop("facecolor")
    fig.set_facecolor(bg)
    tbl = Table(pd.DataFrame({"a": [1, 2], "b": [3, 4]}), ax=ax, **kw)
    assert matplotlib.colors.to_hex(fig.get_facecolor()) == bg.lower()
    assert len(tbl.rows) == 2 and ax.texts

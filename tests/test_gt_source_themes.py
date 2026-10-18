import importlib.util
import re
import sys
from pathlib import Path

import polars as pl
import pytest

pytest.importorskip("great_tables")
from great_tables import GT  # noqa: E402

import sdvplot.great_tables as sgt  # noqa: E402
from sdvplot._errors import InputError  # noqa: E402
from sdvplot._table_themes import sdv_table_themes, table_theme_spec  # noqa: E402
from sdvplot.great_tables._marks import DENSITY  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DF = pl.DataFrame({"team": ["KC", "BUF", "BAL"], "wins": [12, 10, 9]})


def html(name, **kw):
    return sgt.gt_theme_source(GT(DF, id="t").tab_header("T", "S"), name, **kw).as_raw_html()


def generator():
    spec = importlib.util.spec_from_file_location("gen_gt_shortcuts", ROOT / "tools" / "gen_gt_shortcuts.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gen_gt_shortcuts"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_economist_carries_its_title_font_and_label_rule_color():
    sp = table_theme_spec("economist")
    out = html("economist")
    assert sp.fonts["title"] in out
    assert re.search(r"#0d0d0d", out, re.I)  # labelBorderBottom's color
    assert sp.structure["labelBorderBottom"] in out


def test_named_shortcut_equals_gt_theme_source():
    a = sgt.gt_theme_datagolf(GT(DF, id="t")).as_raw_html()
    assert a == sgt.gt_theme_source(GT(DF, id="t"), "datagolf").as_raw_html()
    d = sgt.gt_theme_datagolf(GT(DF, id="t"), mode="dark", density="compact").as_raw_html()
    assert d == sgt.gt_theme_source(GT(DF, id="t"), "datagolf", mode="dark", density="compact").as_raw_html()


def test_shortcuts_are_in_sync_with_curated():
    gen = generator()
    assert gen.main(["--check"]) == 0
    assert len(gen.CURATED) == 20
    for i in gen.CURATED:
        assert gen.shortcut_name(i) in sgt.__all__


def test_generated_file_is_lf():
    assert b"\r" not in (ROOT / "src" / "sdvplot" / "great_tables" / "_gt_shortcuts.py").read_bytes()


@pytest.mark.parametrize("theme", [t["id"] for t in sdv_table_themes()])
def test_every_registry_theme_renders_its_fonts_ground_and_stripe(theme):
    sp = table_theme_spec(theme)
    out = html(theme).lower()
    assert sp.fonts["body"].lower() in out
    assert sp.fonts["label"].lower() in out
    assert sp.palette["bg"].lower() in out
    assert ("tr:nth-child(even) td.gt_row" in out) == bool(sp.structure["stripe"])


def table_font_rule(out, tid="t"):
    """The font-family of the stylesheet rule ``#t .gt_table`` that comes last (ours, after gt's own)."""
    return re.findall(rf"#{tid} \.gt_table \{{[^}}]*?font-family: ([^;]*);", out)[-1]


def test_faces_fall_back_to_their_generic_family():
    out = html("aer")  # Source Serif 4 title and body
    assert '"Source Serif 4", serif' in out
    assert table_font_rule(out).startswith('"Source Serif 4", serif, system-ui')
    mono = next(i for i in (t["id"] for t in sdv_table_themes()) if "mono" in table_theme_spec(i).fonts["body"].lower())
    body = table_theme_spec(mono).fonts["body"]
    assert table_font_rule(html(mono)).startswith(f'"{body}", monospace, system-ui')


@pytest.mark.parametrize("theme", [t["id"] for t in sdv_table_themes()])
def test_no_family_is_quoted_as_one_name(theme):
    out = html(theme)
    assert "'\"" not in out  # great_tables single-quotes a font name that holds a comma: one bogus family
    assert table_font_rule(out).startswith(f'"{table_theme_spec(theme).fonts["body"]}", ')


def test_dark_and_density_apply():
    dark = html("datagolf", mode="dark").lower()
    assert table_theme_spec("datagolf", "dark").palette["bg"].lower() in dark
    body = table_theme_spec("economist").sizes["body"]
    for density in ("compact", "social"):
        k = DENSITY[density]["body"] / DENSITY["comfortable"]["body"]
        assert f"font-size: {float(round(body * k, 1))}px" in html("economist", density=density)


def test_errors():
    with pytest.raises(InputError, match="light-only"):
        html("nejm", mode="dark")
    with pytest.raises(InputError):
        html("datagolff")
    with pytest.raises(ValueError, match="density"):
        html("economist", density="roomy")
    with pytest.raises(TypeError):
        sgt.gt_theme_source(DF, "economist")


def test_stripe_lands_on_the_second_data_row():
    # one parity across adapters (sdvtables, gt/sdvplotR, itables, plottable): data rows 2, 4, ... are striped
    bs4 = pytest.importorskip("bs4")
    theme = next(t["id"] for t in sdv_table_themes() if table_theme_spec(t["id"]).structure["stripe"])
    out = html(theme)
    sel = re.search(r"([^{}]*nth-child\([^)]*\)[^{}]*)\{", out).group(1).strip()
    soup = bs4.BeautifulSoup(out, "html.parser")
    striped = set(map(id, soup.select(sel)))
    rows = soup.select("#t tbody tr")
    assert [any(id(td) in striped for td in tr.find_all("td")) for tr in rows] == [False, True, False]

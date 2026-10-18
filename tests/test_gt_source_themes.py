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
def test_every_registry_theme_renders_its_font_and_ground(theme):
    sp = table_theme_spec(theme)
    out = html(theme).lower()
    assert sp.fonts["body"].lower() in out
    assert sp.palette["bg"].lower() in out


def test_dark_and_density_apply():
    dark = html("datagolf", mode="dark").lower()
    assert table_theme_spec("datagolf", "dark").palette["bg"].lower() in dark
    assert html("economist", density="social") != html("economist")


def test_errors():
    with pytest.raises(InputError, match="light-only"):
        html("nejm", mode="dark")
    with pytest.raises(InputError):
        html("datagolff")
    with pytest.raises(ValueError, match="density"):
        html("economist", density="roomy")
    with pytest.raises(TypeError):
        sgt.gt_theme_source(DF, "economist")

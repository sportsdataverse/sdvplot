import re

import pytest

pytest.importorskip("itables")

from sdvplot import InputError, sdv_table_themes, table_theme_spec  # noqa: E402
from sdvplot.itables import itables_sdv_theme  # noqa: E402

IDS = [t["id"] for t in sdv_table_themes()]


def _rules(css):
    return [r for r in css.split("}") if r.strip()]


def test_css_carries_the_spec_colours_and_is_scoped():
    spec = table_theme_spec("basketball-reference")
    css = itables_sdv_theme("basketball-reference")["css"]
    assert spec.palette["labelBg"] in css and spec.palette["hline"] in css
    assert "@import url(" in css and "thead th" in css and "tbody td" in css


@pytest.mark.parametrize("tid", IDS)
def test_every_rule_is_scoped_and_classes_follow_the_spec(tid):
    spec = table_theme_spec(tid)
    out = itables_sdv_theme(tid)
    assert set(out) == {"classes", "style", "css"}
    body = re.sub(r"@import[^\n]*\n", "", out["css"])
    assert all(r.strip().startswith("#sdv-itable") for r in _rules(body))
    assert ("tr:nth-child(odd)" in body) is bool(spec.structure["stripe"])
    cls = out["classes"].split()
    assert ("compact" in cls) is (spec.sizes["padY"] <= 4)
    assert ("stripe" in cls) is bool(spec.structure["stripe"])


def test_table_id_scopes_and_is_validated():
    css = itables_sdv_theme("datagolf", table_id="t1")["css"]
    assert "#t1 thead th" in css and "#sdv-itable" not in css
    for bad in ("", "1a", "a b", "a{}", "a.b"):
        with pytest.raises(InputError, match="table_id"):
            itables_sdv_theme("datagolf", table_id=bad)


def test_dark_on_a_light_only_theme_raises_and_dark_changes_colours():
    with pytest.raises(InputError, match="nejm"):
        itables_sdv_theme("nejm", mode="dark")
    dark = next(t for t in IDS if table_theme_spec(t).dark_policy != "none")
    assert itables_sdv_theme(dark, mode="dark")["css"] != itables_sdv_theme(dark)["css"]


def test_the_options_are_real_show_keywords():
    from itables.typing import ITableOptions

    assert {"classes", "style", "table_id"} <= set(ITableOptions.__annotations__)

from __future__ import annotations

import pandas as pd
import pytest

pytest.importorskip("reactable")

from reactable import Reactable, Theme  # noqa: E402

from sdvplot import sdv_table_themes, table_theme_spec  # noqa: E402
from sdvplot._errors import InputError  # noqa: E402
from sdvplot.reactable import reactable_sdv_args, reactable_sdv_theme  # noqa: E402

_IDS = [t if isinstance(t, str) else t["id"] for t in sdv_table_themes()]


def _modes(i: str) -> list[str]:
    out = ["light"]
    try:
        table_theme_spec(i, "dark")
        out.append("dark")
    except InputError:
        pass
    return out


CASES = [(i, m) for i in _IDS for m in _modes(i)]


def test_fmtr_theme_unchanged():
    assert reactable_sdv_theme("cerulean").to_props() == reactable_sdv_theme("cerulean", mode="light").to_props()


def test_wikipedia_mapping():
    spec = table_theme_spec("wikipedia")
    t = reactable_sdv_theme("wikipedia")
    assert t.border_color == spec.palette["hline"]
    assert t.header_style["background"] == spec.palette["labelBg"]
    assert t.style["fontFamily"].startswith('"Arimo", ')
    assert reactable_sdv_args("wikipedia")["bordered"] is True


def test_guardian_striped_follows_spec():
    spec = table_theme_spec("guardian")
    assert reactable_sdv_args("guardian")["striped"] == spec.structure["stripe"]


def test_overrides_apply():
    t = reactable_sdv_theme("wikipedia", font_color="#123456", background_color="#fafafa", cell_padding=9)
    assert t.color == "#123456" and t.background_color == "#fafafa" and t.cell_padding == "9px"


def test_named_colour_overrides_keep_the_name():
    # mix() only blends hex: the hover colour comes from the palette, so a CSS name override must not raise
    t = reactable_sdv_theme("wikipedia", background_color="white", font_color="black")
    assert t.background_color == "white" and t.color == "black"
    assert t.highlight_color.startswith("#")


def test_dark_on_light_only_raises():
    with pytest.raises(InputError, match="light-only"):
        reactable_sdv_theme("nejm", mode="dark")


def test_dark_on_light_fmtr_raises_naming_dark_ones():
    with pytest.raises(InputError, match="cyborg"):
        reactable_sdv_theme("cerulean", mode="dark")


def test_dark_on_dark_fmtr_ok():
    assert reactable_sdv_theme("cyborg", mode="dark").to_props() == reactable_sdv_theme("cyborg").to_props()


@pytest.mark.parametrize(("name", "mode"), CASES)
def test_every_registry_theme_builds(name, mode):
    args = reactable_sdv_args(name, mode=mode)
    assert isinstance(args["theme"], Theme)
    Reactable(pd.DataFrame({"a": [1, 2]}), **args)

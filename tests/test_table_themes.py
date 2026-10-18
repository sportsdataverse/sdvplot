import json
from importlib import resources

import pytest

import sdvplot
from sdvplot import InputError, sdv_table_themes, table_theme_spec

REG = json.loads(resources.files("sdvplot").joinpath("data", "table_themes.json").read_text(encoding="utf-8"))["themes"]


def test_dark_palette_comes_from_the_registry():
    assert table_theme_spec("datagolf", "dark").palette["bg"] == REG["datagolf"]["dark"]["bg"]


def test_light_only_theme_in_dark_names_three_alternatives():
    with pytest.raises(InputError, match=r"moneypuck.*light-only.*: \w[\w-]*, [\w-]+, [\w-]+$"):
        table_theme_spec("moneypuck", "dark")
    dark = sorted(i for i, t in REG.items() if t["darkPolicy"] != "none")[:3]
    with pytest.raises(InputError, match="nejm.*light-only.*no dark-capable themes in category 'journal'; try: ") as e:
        table_theme_spec("nejm", "dark")  # journal has no dark-capable theme: fall back to any category
    assert str(e.value).endswith(", ".join(dark))


def test_nested_structure_is_a_copy_of_the_cached_registry():
    tid, key = next((t, k) for t, s in REG.items() for k, v in s["structure"].items() if isinstance(v, list) and v)
    first = table_theme_spec(tid).structure[key]
    want = json.loads(json.dumps(first))
    first.append("junk")
    assert table_theme_spec(tid).structure[key] == want


def test_misspelling_suggests_the_close_match():
    with pytest.raises(InputError, match="datagolf"):
        table_theme_spec("datagolff")


@pytest.mark.parametrize("name", ["espn", "fivethirtyeight", "pff"])
def test_reactablefmtr_names_point_at_the_site_id_and_the_port(name):
    with pytest.raises(InputError) as e:
        table_theme_spec(name)
    assert f"{name}-site" in str(e.value) and f'reactable_sdv_theme("{name}")' in str(e.value)


def test_bad_mode():
    with pytest.raises(InputError, match="mode"):
        table_theme_spec("datagolf", "sepia")  # type: ignore[arg-type]


def test_no_unresolved_placeholder_in_any_theme_or_mode():
    for tid, s in REG.items():
        for mode in ("light", "dark"):
            if mode == "dark" and s["darkPolicy"] == "none":
                continue
            spec = table_theme_spec(tid, mode)  # type: ignore[arg-type]
            assert spec.id == tid
            for k, v in spec.structure.items():
                assert not (isinstance(v, str) and "{" in v), (tid, mode, k, v)


def test_missing_palette_key_falls_back_to_the_default():
    from sdvplot import _table_themes as t

    assert t._border("1px solid {summaryBg}", {"bg": "#fff"}) == "1px solid #f0f0f0"
    assert t._border("1px solid {nope}", {}) == "1px solid #888888"
    assert t._border("none", {}) == "none" and t._border(None, {}) == "none"


def test_listing_filters():
    dark = [s for s in REG.values() if s["darkPolicy"] != "none"]
    assert len(sdv_table_themes(mode="dark")) == len(dark)
    assert len(sdv_table_themes()) == len(REG) == 122
    cats = {s["category"] for s in REG.values()}
    assert sum(len(sdv_table_themes(category=c)) for c in cats) == 122
    assert set(sdv_table_themes()[0]) == {"id", "source", "category", "dark_policy"}


def test_exported():
    assert "table_theme_spec" in sdvplot.__all__ and "sdv_table_themes" in sdvplot.__all__


def test_font_stack_picks_a_generic_from_the_name():
    from sdvplot._table_themes import _font_stack

    assert _font_stack("Arimo") == '"Arimo", sans-serif'
    assert _font_stack("Source Serif 4") == '"Source Serif 4", serif'
    assert _font_stack("Source Sans 3") == '"Source Sans 3", sans-serif'
    assert _font_stack("JetBrains Mono") == '"JetBrains Mono", monospace'
    assert _font_stack(None) == "sans-serif"


# the same two lists are asserted in sdvtables and sdvplotR, so the three heuristics agree on every registry face
REGISTRY_SERIF = {
    "Crimson Text", "Fraunces", "Gelasio", "Libre Bodoni", "Libre Caslon Display", "Libre Caslon Text", "Lora",
    "Newsreader", "Playfair Display", "Roboto Slab", "Source Serif 4", "Spectral", "Tinos",
}  # fmt: skip
REGISTRY_MONO = {"Courier Prime", "DM Mono", "IBM Plex Mono", "JetBrains Mono", "Roboto Mono"}


def test_every_registry_face_gets_the_shared_generic_family():
    from sdvplot._table_themes import _font_stack, _generic_family

    faces = {v for t in REG.values() for v in t["fonts"].values() if isinstance(v, str)}
    assert {f for f in faces if _generic_family(f) == "serif"} == REGISTRY_SERIF
    assert {f for f in faces if _generic_family(f) == "monospace"} == REGISTRY_MONO
    assert _font_stack(table_theme_spec("evolving-hockey").fonts["body"]) == '"Crimson Text", serif'
    assert _font_stack(table_theme_spec("gtextras-dot-matrix").fonts["body"]) == '"Courier Prime", monospace'

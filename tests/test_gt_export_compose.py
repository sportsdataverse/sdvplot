"""gt_grid and gt_stack_tables: the composed HTML, and the file path with a fake renderer."""

import pandas as pd
import polars as pl
import pytest

pytest.importorskip("great_tables")
from great_tables import GT, md  # noqa: E402
from PIL import Image  # noqa: E402

import sdvplot.great_tables._export as ex  # noqa: E402
from sdvplot.great_tables._export import gt_grid, gt_stack_tables  # noqa: E402
from tests.gt_export_fakes import BLACK, forbid_render, img  # noqa: E402

DF = pl.DataFrame({"team": ["LV", "LAR"], "wins": [10, 8]})
STACK = "font-family:system-ui, -apple-system, sans-serif;"


def _two():
    return [GT(pl.DataFrame({"a": [1]})).tab_header(title="A"), GT(pd.DataFrame({"b": [2]}, index=[7]))]


def test_grid_lays_tables_out_in_columns():
    grid = gt_grid(_two(), ncol=3, gap=10, align="bottom")
    html = str(grid)
    assert (
        "grid-template-columns: repeat(3, max-content); gap: 10px; align-items: end; justify-content: center;" in html
    )
    assert html.count('class="gt_table"') == 2
    assert "safe center" not in html  # no heading or footer: no wrapper
    assert hasattr(grid, "_repr_html_")  # displays in a notebook


def test_grid_heading_and_split_caption_use_sdvplotr_defaults():
    html = str(gt_grid(_two(), title="T", caption=md("**c**"), source_note="Data: x", caption_rule=True))
    title = STACK + "font-size:28px;color:#111111;font-weight:700;text-align:center;margin-bottom:12px;"
    assert f'<div style="{title}">T</div>' in html  # no subtitle: the title carries its gap (12, not 4)
    caption = (
        STACK + "font-size:12px;color:#8A8A8A;font-weight:400;text-align:center;margin-top:10px;padding-bottom:6px;"
        "border-bottom:1px solid #8A8A8A;"
    )
    assert f'<div style="{caption}"><strong>c</strong></div>' in html
    assert (
        f'<div style="{STACK}font-size:12px;color:#8A8A8A;font-weight:400;text-align:right;margin-top:6px;">Data: x'
        in html
    )
    assert "display: flex; justify-content: center; justify-content: safe center; overflow-x: auto;" in html


def test_style_overrides_keep_the_other_defaults_and_load_the_google_font():
    html = str(
        gt_stack_tables(
            _two(),
            title="T",
            subtitle="S",
            title_style={"font": "Oswald", "size": 34, "transform": "uppercase", "italic": True, "margin_bottom": -2},
            subtitle_style={"color": "#8A8A8A", "spacing": "0.1em"},
        )
    )
    assert (
        "font-family:&apos;Oswald&apos;, system-ui, -apple-system, sans-serif;font-size:34px;color:#111111;"
        "font-weight:700;font-style:italic;text-transform:uppercase;text-align:center;margin-bottom:-2px;"
    ) in html
    assert (
        "font-size:16px;color:#8A8A8A;font-weight:400;letter-spacing:0.1em;text-align:center;margin-bottom:12px;"
        in html
    )
    assert 'href="https://fonts.googleapis.com/css2?family=Oswald:wght@100..900&amp;display=swap"' in html


def test_unknown_style_key_is_an_error():
    with pytest.raises(ValueError, match=r"title_style has unknown key\(s\) \['colour'\]"):
        gt_grid(_two(), title="T", title_style={"colour": "red"})


def test_grid_labels_recycle_and_take_markdown():
    html = str(gt_grid(_two() + _two()[:1], labels=["East", md("*West*")]))
    label = STACK + "font-size:12px;color:#555555;font-weight:600;text-align:left;margin-bottom:6px;"
    assert html.count(f'<div style="{label}">East</div>') == 2 and html.count("<em>West</em>") == 1


def test_grid_label_font_loads_without_a_heading():  # sdvplotR drops the link here; sdvplot keeps it
    html = str(gt_grid(_two(), labels="x", label_style={"font": "Roboto Slab"}))
    assert "family=Roboto+Slab:wght@100..900" in html


def test_stack_aligns_in_a_column():
    assert "flex-direction: column; gap: 16px; align-items: center;" in str(gt_stack_tables(_two()))
    assert "gap: 4px; align-items: flex-start;" in str(gt_stack_tables(_two(), align="left", gap=4))


def test_tables_accept_a_dict_of_tables():  # gt_theme_preview() returns one
    assert str(gt_grid(dict(zip("ab", _two(), strict=True)))).count('class="gt_table"') == 2


@pytest.mark.parametrize(
    ("call", "error", "match"),
    [
        (lambda: gt_grid(GT(DF)), TypeError, "wrap a single table"),
        (lambda: gt_grid([]), ValueError, "non-empty"),
        (lambda: gt_stack_tables(), ValueError, "non-empty"),
        (lambda: gt_grid([GT(DF), DF]), TypeError, r"item\(s\) \[1\]"),
        (lambda: gt_grid([GT(DF)], ncol=0), ValueError, "ncol"),
        (lambda: gt_grid([GT(DF)], align="middle"), ValueError, "align"),
        (lambda: gt_stack_tables([GT(DF)], align="top"), ValueError, "align"),
        (lambda: gt_grid([GT(DF)], file="grid.txt"), ValueError, "image extension"),
        (lambda: gt_stack_tables([GT(DF)], file="stack.png", bg="nope"), ValueError, "color"),
    ],
)
def test_composition_checks_its_arguments_before_rendering(monkeypatch, call, error, match):
    forbid_render(monkeypatch)
    with pytest.raises(error, match=match):
        call()


@pytest.mark.parametrize("compose", [gt_grid, gt_stack_tables])
def test_composed_file_renders_the_wrapper_then_trims_and_pads(compose, monkeypatch, tmp_path):
    pages = []

    def render(page, zoom):
        pages.append((page, zoom))
        return img(80, 50, "#fbfaf7", blocks=[(8, 8, 60, 30, "black")])

    monkeypatch.setattr(ex, "_render_html", render)
    out = tmp_path / "composed.png"
    assert compose(_two(), file=out, bg="#FBFAF7", whitespace=4, zoom=3) == out
    with Image.open(out) as im:
        assert im.size == (68, 38) and im.getpixel((0, 0)) == (251, 250, 247) and im.getpixel((4, 4)) == BLACK
    page, zoom = pages[0]
    assert zoom == 3 and page.count('class="gt_table"') == 2
    assert '<div id="sdvplot-page" style="display: inline-block; padding: 8px; background-color: #FBFAF7;">' in page

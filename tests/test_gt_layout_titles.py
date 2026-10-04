import base64
import datetime
import re
from urllib.parse import unquote

import polars as pl
import pytest

pytest.importorskip("great_tables")
from great_tables import GT  # noqa: E402

from sdvplot.great_tables import gt_set_font, gt_title_header, gt_watermark  # noqa: E402
from tests.gt_frames import KINDS, frame  # noqa: E402

DATA = {"team": ["LV", "LAR", "KC"], "wins": [10, 8, 12]}


@pytest.mark.parametrize("kind", KINDS)
def test_title_header_stacks_kicker_title_subtitle_and_date(kind):
    gt = gt_title_header(
        GT(frame(kind, DATA)), "Week 5", subtitle="Power ranking", kicker="NFL", date=datetime.date(2026, 7, 1)
    )
    h = gt.as_raw_html()
    assert '<div style="font-size:0.75em;color:#C84630;font-weight:700;letter-spacing:0.08em;' in h
    assert 'text-transform:uppercase;margin-bottom:0.15em;">NFL</div>' in h
    assert '<div style="font-size:0.85em;color:#8A8A8A;font-weight:400;margin-top:0.15em;">July 01, 2026</div>' in h
    assert h.index(">NFL<") < h.index(">Week 5<") < h.index(">Power ranking<") < h.index("July 01, 2026")


def test_title_header_styles_load_google_fonts_and_reject_unknown_keys():
    gt = GT(pl.DataFrame(DATA))
    h = gt_title_header(gt, "Week 5", title_style={"font": "Oswald", "size": 30, "italic": True}).as_raw_html()
    assert "<div style=\"font-family:'Oswald', sans-serif;font-size:30px;font-style:italic;\">Week 5</div>" in h
    assert "fonts.googleapis.com/css2?family=Oswald" in h
    assert "July" not in h  # no date line unless asked
    with pytest.raises(ValueError, match="unknown style key"):
        gt_title_header(gt, "Week 5", title_style={"colour": "red"})


def test_every_function_refuses_raw_data():
    with pytest.raises(TypeError, match=r"wrap a data frame with GT\(df\)"):
        gt_title_header(pl.DataFrame(DATA), "Week 5")


@pytest.mark.parametrize("kind", KINDS)
def test_set_font_reaches_every_part_of_the_table(kind):
    gt = (
        GT(frame(kind, DATA), rowname_col="team")
        .tab_header("Title", "Subtitle")
        .tab_spanner("record", ["wins"])
        .tab_source_note("source")
    )
    h = gt_set_font(gt, "Roboto Condensed", weight=600).as_raw_html()
    assert "fonts.googleapis.com/css2?family=Roboto+Condensed" in h
    styled = re.findall(r'<(t[dh])[^>]*class="([^"]*)"[^>]*style="font-family: Roboto Condensed;font-weight: 600;"', h)
    styled += re.findall(r'<(t[dh]) style="font-family: Roboto Condensed;font-weight: 600;" class="([^"]*)"', h)
    classes = " ".join(c for _, c in styled)
    for part in ["gt_title", "gt_subtitle", "gt_column_spanner_outer", "gt_col_heading", "gt_stub", "gt_sourcenote"]:
        assert part in classes, part
    assert sum(1 for tag, c in styled if c == "gt_row gt_right") == 3  # every body cell


def test_set_font_can_use_an_installed_font():
    h = gt_set_font(GT(pl.DataFrame(DATA)), "Georgia", from_google_font=False, style="italic").as_raw_html()
    assert "font-family: Georgia;font-style: italic;" in h
    assert "fonts.googleapis.com" not in h


@pytest.mark.parametrize("kind", KINDS)
def test_text_watermark_sits_behind_the_body(kind):
    gt = gt_watermark(GT(frame(kind, DATA)), text="DRAFT <1>")
    table_id = gt._options.table_id.value
    assert re.fullmatch(r"[a-z]{10}", table_id)
    h = gt.as_raw_html()
    m = re.search(rf"#{table_id} \.gt_table_body \{{ background-image: url\('data:image/svg\+xml,([^']*)'\);", h)
    svg = unquote(m.group(1))
    assert 'fill-opacity="0.06"' in svg and ">DRAFT &lt;1&gt;</text>" in svg
    assert "background-position: center; background-size: 60% auto; }" in h


def test_a_steep_text_watermark_sizes_by_height_and_keeps_the_table_id():
    gt = gt_watermark(GT(pl.DataFrame(DATA), id="mine"), text="SDV", angle=-80)
    h = gt.as_raw_html()
    assert "#mine .gt_table_body { background-image:" in h
    assert "background-size: auto 60%; }" in h
    assert "transform%3D%22rotate%28-80" in h


def test_image_watermark_embeds_the_file(tmp_path):
    png = tmp_path / "mark.png"
    png.write_bytes(b"\x89PNG fake")
    h = gt_watermark(GT(pl.DataFrame(DATA), id="t"), image=png, opacity=0.1).as_raw_html()
    payload = base64.b64encode(b"\x89PNG fake").decode()
    assert f"#t .gt_table_body {{ background-image: url('data:image/png;base64,{payload}');" in h
    assert "background-size: 60% auto; opacity: 0.1; }" in h


def test_watermark_argument_errors(tmp_path):
    gt = GT(pl.DataFrame(DATA))
    with pytest.raises(ValueError, match="exactly one"):
        gt_watermark(gt)
    with pytest.raises(ValueError, match="exactly one"):
        gt_watermark(gt, text="x", image="y.png")
    with pytest.raises(FileNotFoundError):
        gt_watermark(gt, image=tmp_path / "missing.png")
    bmp = tmp_path / "mark.bmp"
    bmp.write_bytes(b"BM")
    with pytest.raises(ValueError, match="PNG, JPEG, SVG or GIF"):
        gt_watermark(gt, image=bmp)

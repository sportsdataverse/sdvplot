import re

import numpy as np
import polars as pl
import pytest

pytest.importorskip("great_tables")
from great_tables import GT, html  # noqa: E402

from sdvplot.great_tables import gt_marginalia, gt_scale_note, gt_social_tag  # noqa: E402
from tests.gt_frames import KINDS, frame  # noqa: E402

DATA = {"team": ["LV", "KC"], "note": ["Lost the QB in week 3", "Won out"], "pay": [254_000_000, 268_500_000]}


def source_notes(gt):
    notes = re.findall(r'class="gt_sourcenote"[^>]*>(.*?)</td>', gt.as_raw_html(), re.S)
    return [re.sub(r'^<span class="gt_from_md">(.*)</span>$', r"\1", n.strip(), flags=re.S) for n in notes]


@pytest.mark.parametrize("kind", KINDS)
def test_marginalia_mutes_italicizes_and_rules_the_notes(kind):
    h = gt_marginalia(GT(frame(kind, DATA)), "note").as_raw_html()
    style = "color: #737373;font-size: 0.92em;font-style: italic; border-left: 1px solid #d1d1d1 !important;"
    assert f'<td style="{style}" class="gt_row gt_left">Lost the QB in week 3</td>' in h
    assert '<col style="width:220px;"/>' in h
    assert 'id="note"></th>' in h  # the label is blanked


def test_marginalia_reads_a_dark_background_and_keeps_options():
    gt = GT(pl.DataFrame(DATA)).tab_options(table_background_color="#1a1a17")
    h = gt_marginalia(gt, "note", width="30%", label="Notes", italic=False, rule=False, align="right").as_raw_html()
    assert '<td style="color: #8c8c8b;font-size: 0.92em;font-style: normal;" class="gt_row gt_right">Won out</td>' in h
    assert '<col style="width:30%;"/>' in h and 'id="note">Notes</th>' in h
    with pytest.raises(ValueError, match="matched no columns"):
        gt_marginalia(gt, [])


@pytest.mark.parametrize("kind", KINDS)
def test_scale_note_divides_and_discloses(kind):
    gt = gt_scale_note(GT(frame(kind, DATA)), "pay", divisor=1e6, decimals=1, where="both")
    h = gt.as_raw_html()
    assert '<td class="gt_row gt_right">254.0</td>' in h and '<td class="gt_row gt_right">268.5</td>' in h
    assert 'id="pay">pay (millions)</th>' in h
    assert source_notes(gt) == ["Figures in millions."]


def test_scale_note_unnamed_divisor_label_only_and_html_labels():
    gt = GT(pl.DataFrame(DATA)).cols_label(pay=html("<b>Pay</b>"))
    out = gt_scale_note(gt, "pay", divisor=2500, where="label", use_seps=False)
    h = out.as_raw_html()
    assert 'id="pay"><b>Pay</b> (÷2,500)</th>' in h and ">107400</td>" in h
    assert source_notes(out) == []
    assert source_notes(gt_scale_note(gt, "pay", divisor=2500)) == ["Figures divided by 2,500."]
    assert source_notes(gt_scale_note(gt, "pay", note="In $000s")) == ["In $000s"]
    for bad in (0, True, "1000"):
        with pytest.raises(ValueError, match="non-zero number"):
            gt_scale_note(gt, "pay", divisor=bad)


def test_numpy_numbers_are_numbers():
    gt = GT(pl.DataFrame(DATA), id="t")
    numpy_note = gt_scale_note(gt, "pay", divisor=np.int64(1000)).as_raw_html()
    assert numpy_note == gt_scale_note(gt, "pay", divisor=1000).as_raw_html()
    assert '<col style="width:180px;"/>' in gt_marginalia(gt, "note", width=np.int64(180)).as_raw_html()


@pytest.mark.parametrize("kind", KINDS)
def test_social_tag_puts_icons_before_handles(kind):
    gt = gt_social_tag(GT(frame(kind, DATA)), {"gh": "sportsdataverse", "web": "sportsdataverse.org"})
    (note,) = source_notes(gt)
    assert note.startswith("<div style='text-align:right;'><span style='display:inline-flex; align-items:center;")
    assert note.count("<svg ") == 2 and note.count('class="fa"') == 2  # one Font Awesome icon per account
    assert "</svg>sportsdataverse</span> | <span" in note and "</svg>sportsdataverse.org</span></div>" in note
    assert 'style="fill:currentColor;height:0.9em;' in note


def test_social_tag_stacks_colors_and_styles():
    gt = GT(pl.DataFrame(DATA))
    out = gt_social_tag(gt, {"x": "@sdv", "IG": "sdv"}, stack=True, icon_color="#ff0000", text_size="11px",
                        text_weight=600, align="left")  # fmt: skip
    (note,) = source_notes(out)
    assert note.startswith("<div style='text-align:left; font-size:11px; font-weight:600;'>")
    assert note.count('style="fill:#ff0000;') == 2 and "</span><br><span" in note
    with pytest.raises(ValueError, match=r"'no-such-icon' was not found in your installed faicons \(\d"):
        gt_social_tag(gt, {"no-such-icon": "sdv"})
    with pytest.raises(ValueError, match="mapping of platform to handle"):
        gt_social_tag(gt, {})
    with pytest.raises(ValueError, match="align must be one of"):  # R pastes any string into the CSS
        gt_social_tag(gt, {"gh": "sdv"}, align="middle")


def test_social_tag_with_a_caption_goes_through_gt_538_caption():
    out = gt_social_tag(GT(pl.DataFrame(DATA)), {"gh": "sportsdataverse"}, caption="Data: SDV", rule_color="#cccccc")
    h = out.as_raw_html()
    assert "Data: SDV" in h and "</svg>sportsdataverse</span>" in h
    assert h.index("Data: SDV") < h.index("</svg>sportsdataverse")

import re

import pytest

pytest.importorskip("great_tables")
from great_tables import GT  # noqa: E402

from sdvplot._contrast import mix, on_color  # noqa: E402
from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.great_tables import gt_color_pills, gt_color_ranks, gt_indicator_boxes  # noqa: E402
from sdvplot.great_tables._cells import _natural  # noqa: E402
from tests.gt_html import body_rows, frame  # noqa: E402

CARS = {"car": ["Mazda", "Datsun", "Fiat"], "mpg": [21.0, 18.5, 30.2], "hp": [110, 175, 66]}
RED, GREEN = "#C84630", "#5DA271"


@pytest.fixture(params=["pandas", "polars"])
def lib(request):
    return request.param


def pill(cell_html):
    """(background, text color, width, label) of a rendered pill, or None for a cell without one."""
    m = re.search(r"width: (\S+); .*?background-color: (#\w+); color: (#\w+);.*?'>(.*?)</span>", cell_html)
    return None if m is None else (m.group(2), m.group(3), m.group(1), m.group(4))


def column(gt, j):
    return [row[j][1] for row in body_rows(gt)]


def test_pills_fill_by_value_on_the_domain_with_readable_ink(lib):
    out = gt_color_pills(GT(frame(lib, CARS)), "hp", domain=(50, 200))
    got = [pill(c) for c in column(out, 2)]
    for (fill, ink, width, text), value in zip(got, CARS["hp"], strict=True):
        assert fill == mix(RED, GREEN, (value - 50) / 150)
        assert ink == on_color(fill) and width == "3ch" and text == str(value)
    assert "border-radius: 10px" in column(out, 2)[0] and "height: 25px; line-height: 25px" in column(out, 2)[0]


def test_pills_share_one_domain_but_size_each_column_on_its_own(lib):
    out = gt_color_pills(GT(frame(lib, CARS)), ["mpg", "hp"], domain=(0, 200))
    assert [pill(c)[2] for c in column(out, 1)] == ["4ch"] * 3  # "18.5" is the widest mpg
    assert [pill(c)[2] for c in column(out, 2)] == ["3ch"] * 3
    assert pill(column(out, 1)[0])[0] == mix(RED, GREEN, 21 / 200)


def test_pills_without_a_domain_warn_and_use_the_observed_range(lib):
    with pytest.warns(SdvplotWarning, match=r"observed range \(18.5 to 175\)"):
        out = gt_color_pills(GT(frame(lib, CARS)), ["mpg", "hp"])
    assert out._sdvplot_scale["domain"] == (18.5, 175.0)
    assert pill(column(out, 2)[1])[0] == mix(RED, GREEN, 1.0)


def test_pills_by_rank_rank_each_column_against_itself(lib):
    out = gt_color_pills(GT(frame(lib, CARS)), "hp", fill_type="rank", domain=(1, 3), digits=0)
    # descending: 175 ranks 1 (the palette's first color), 110 ranks 2, 66 ranks 3
    assert [pill(c)[0] for c in column(out, 2)] == [mix(RED, GREEN, 0.5), mix(RED, GREEN, 0), mix(RED, GREEN, 1)]
    assert [pill(c)[3] for c in column(out, 2)] == ["110", "175", "66"]
    tied = gt_color_pills(GT(frame(lib, {"x": [5, 5, 1]})), "x", fill_type="rank", rank_order="asc", domain=(1, 3))
    assert [pill(c)[0] for c in column(tied, 0)] == [mix(RED, GREEN, 0.75)] * 2 + [mix(RED, GREEN, 0)]


def test_pills_stay_with_their_rows_when_groups_reorder_the_table(lib):
    data = {"conf": ["West", "East", "West", "East"], "team": ["A", "B", "C", "D"], "pts": [10, 20, 30, 40]}
    gt = GT(frame(lib, data), rowname_col="team", groupname_col="conf").row_group_order(["East", "West"])
    out = gt_color_pills(gt, "pts", domain=(0, 40))
    # rendered order is East (B, D) then West (A, C): each pill must still carry its own row's value and color
    got = [pill(row[0][1]) for row in body_rows(out)]
    assert [g[3] for g in got] == ["20", "40", "10", "30"]
    assert [g[0] for g in got] == [mix(RED, GREEN, v / 40) for v in (20, 40, 10, 30)]


def test_pills_only_on_chosen_rows_and_missing_values(lib):
    data = {"car": ["a", "b", "c"], "hp": [110, None, 66]}
    out = gt_color_pills(GT(frame(lib, data)), "hp", rows=[0, 1], domain=(50, 200))
    cells = column(out, 1)
    assert pill(cells[0]) is not None and cells[1] == "" and pill(cells[2]) is None
    with_na = column(gt_color_pills(GT(frame(lib, data)), "hp", domain=(50, 200), na_color="#DDDDDD"), 1)
    assert pill(with_na[1]) == ("#DDDDDD", "#000000", "3ch", "")


def test_pills_format_values_like_sdvplotr(lib):
    money = gt_color_pills(
        GT(frame(lib, {"pay": [1234567.891, 2000000.0]})), "pay", domain=(0, 3e6), digits=2, format_type="currency"
    )
    assert [pill(c)[3] for c in column(money, 0)] == ["$1,234,567.89", "$2,000,000.00"]
    share = gt_color_pills(
        GT(frame(lib, {"p": [0.123, 0.5]})), "p", domain=(0, 1), format_type="percent", suffix=" pts"
    )
    assert [pill(c)[3] for c in column(share, 0)] == ["12.3% pts", "50% pts"]


def test_pills_outside_the_domain_are_grey_with_one_warning(lib):
    with pytest.warns(SdvplotWarning, match=r"2 value\(s\) fall outside the domain"):
        out = gt_color_pills(GT(frame(lib, CARS)), "hp", domain=(100, 150))
    assert [pill(c)[0] for c in column(out, 2)] == [mix(RED, GREEN, 0.2), "#808080", "#808080"]


def test_pills_record_the_scale_on_a_copy_and_it_survives_later_calls(lib):
    gt = GT(frame(lib, CARS))
    out = gt_color_pills(gt, ["mpg", "hp"], palette=["#000000", "#FFFFFF"], domain=[0, 200], reverse=True)
    assert "_sdvplot_scale" not in gt.__dict__
    expected = {
        "columns": ["mpg", "hp"],
        "palette": ["#000000", "#FFFFFF"],
        "domain": (0.0, 200.0),
        "reverse": True,
        "pal_type": "discrete",
    }
    assert out._sdvplot_scale == expected
    assert out.tab_header("Later").opt_row_striping()._sdvplot_scale == expected
    assert pill(column(out, 2)[0])[0] == mix("#FFFFFF", "#000000", 110 / 200)  # reversed


@pytest.mark.parametrize(
    ("value", "r_format"),
    [
        (21.0, "21"),
        (3.14159265, "3.141593"),
        (1234567.8, "1234568"),
        (123456789.5, "123456790"),
        (0.1 + 0.2, "0.3"),
        (1e-8, "0.00000001"),
        (100000.0, "100000"),
        (1e15, "1000000000000000"),
        (-2.5, "-2.5"),
    ],
)
def test_natural_numbers_print_like_r_format(value, r_format):
    # the right-hand side is R 4.6.1's format(value, trim = TRUE, scientific = FALSE), which sdvplotR's labels use
    assert _natural(value) == r_format


def test_pills_reject_named_palettes_and_unknown_options(lib):
    gt = GT(frame(lib, CARS))
    with pytest.raises(ValueError, match="list of hex colors"):
        gt_color_pills(gt, "hp", palette="viridis", domain=(0, 1))
    with pytest.raises(ValueError, match="not a hex color"):
        gt_color_pills(gt, "hp", palette=["red", "blue"], domain=(0, 1))
    with pytest.raises(ValueError, match="pal_type"):
        gt_color_pills(gt, "hp", pal_type="sequential", domain=(0, 1))
    with pytest.raises(ValueError, match="fill_type"):
        gt_color_pills(gt, "hp", fill_type="value", domain=(0, 1))


RANKED = {"team": ["A", "B", "C", "D", "E"], "off": [1, 2, 3, 4, 5], "def": [5.0, 2.5, 1.0, 3.0, None]}
FIVE = ["#3D8B6E", "#9DC5A7", "#EDE0CC", "#DB9070", "#BE4D3A"]


def fills(gt, j):
    return [re.search(r"background-color: (#\w+)", s).group(1).lower() if s else None for s, _ in
            (row[j] for row in body_rows(gt))]  # fmt: skip


def test_color_ranks_match_the_shared_ramp_across_columns(lib):
    out = gt_color_ranks(GT(frame(lib, RANKED)), ["off", "def"])
    # the domain is shared (1 to 5), so every stop lands on a palette color; 2.5 sits halfway between two stops
    assert fills(out, 1) == [c.lower() for c in FIVE]
    assert fills(out, 2) == [FIVE[4].lower(), mix(FIVE[1], FIVE[2], 0.5), FIVE[0].lower(), FIVE[2].lower(), "#ffffff"]
    assert out._sdvplot_scale == {
        "columns": ["off", "def"],
        "palette": FIVE,
        "domain": (1.0, 5.0),
        "reverse": False,
        "pal_type": "discrete",
    }


def test_color_ranks_rows_domain_and_reverse(lib):
    out = gt_color_ranks(GT(frame(lib, RANKED)), "off", rows=[0, 4], domain=(1, 10), palette=["#000000", "#FFFFFF"])
    assert fills(out, 1) == ["#000000", None, None, None, mix("#000000", "#FFFFFF", 4 / 9)]
    rev = gt_color_ranks(
        GT(frame(lib, RANKED)), "off", palette=["#000000", "#FFFFFF"], reverse=True, pal_type="continuous"
    )
    assert fills(rev, 1)[0] == "#ffffff" and rev._sdvplot_scale["reverse"] is True
    assert rev._sdvplot_scale["pal_type"] == "continuous"
    with pytest.raises(ValueError, match="list of hex colors"):
        gt_color_ranks(GT(frame(lib, RANKED)), "off", palette="viridis")


ROSTER = {"player": ["A", "B", "C"], "starter": [1, 0, 1], "injured": [0, None, 1], "minutes": [31.25, 12.0, 0.5]}


def box(cell_html):
    m = re.search(r"width:(\S+); height:(\S+); .*?background-color: (#\w+); color: (#\w+);.*?'>(.*?)</span>", cell_html)
    return m.groups()


def test_indicator_boxes_fill_the_yes_values_and_center_the_columns(lib):
    out = gt_indicator_boxes(GT(frame(lib, ROSTER)), key_columns=["player", "minutes"])
    assert [box(c)[2] for c in column(out, 1)] == ["#FCCF10", "#EEEEEE", "#FCCF10"]
    assert [box(c)[2] for c in column(out, 2)] == ["#EEEEEE", "#EEEEEE", "#FCCF10"]  # a missing value is color_no
    assert box(column(out, 1)[0]) == ("20px", "20px", "#FCCF10", "#000000", "")
    assert column(out, 3) == ["31.25", "12.0", "0.5"]  # a key column is untouched
    centered = re.findall(r'<td class="gt_row (gt_\w+)">', out.as_raw_html())
    assert centered[:4] == ["gt_left", "gt_center", "gt_center", "gt_right"]


def test_indicator_boxes_show_text_with_formats_a_rule_and_a_border(lib):
    out = gt_indicator_boxes(
        GT(frame(lib, ROSTER)),
        columns="minutes",
        indicator_rule=lambda x: x > 10,
        show_text=True,
        per_column_formats={"minutes": {"digits": 1, "suffix": "m"}},
        border_color="#333333",
    )
    got = [box(c) for c in column(out, 3)]
    assert [g[4] for g in got] == ["31.2m", "12.0m", "0.5m"]
    assert [g[2] for g in got] == ["#FCCF10", "#FCCF10", "#EEEEEE"]
    assert got[0][0] == "50px" and "border: 0.25px solid #333333;" in column(out, 3)[0]


def test_indicator_boxes_rules_that_take_the_column_and_missing_values(lib):
    def rule(x, col):
        return x >= (1 if col == "starter" else 2)

    out = gt_indicator_boxes(
        GT(frame(lib, ROSTER)),
        columns=["starter", "injured"],
        indicator_rule=rule,
        color_na="#999999",
        show_text=True,
        show_na_as_na=True,
    )
    assert [box(c)[2] for c in column(out, 1)] == ["#FCCF10", "#EEEEEE", "#FCCF10"]
    assert [box(c)[2] for c in column(out, 2)] == ["#EEEEEE", "#999999", "#EEEEEE"]
    assert box(column(out, 2)[1])[4] == "NA"
    only_yes = gt_indicator_boxes(GT(frame(lib, ROSTER)), columns="starter", show_text=True, show_only="yes")
    assert [box(c)[4] for c in column(only_yes, 1)] == ["1", "", "1"]


def test_indicator_boxes_refuse_both_selections_and_unknown_show_only(lib):
    gt = GT(frame(lib, ROSTER))
    with pytest.raises(ValueError, match="not both"):
        gt_indicator_boxes(gt, columns="starter", key_columns="player")
    with pytest.raises(ValueError, match="show_only"):
        gt_indicator_boxes(gt, columns="starter", show_only="maybe")

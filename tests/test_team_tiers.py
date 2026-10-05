"""team_tiers (sdvplotR sdv_team_tiers): the shared prep in sdvplot._tiers, then the matplotlib and plotnine plots."""

import itertools

import pandas as pd
import polars as pl
import pytest

mpl = pytest.importorskip("matplotlib")
mpl.use("Agg")
mpl.rcParams["figure.max_open_warning"] = 0
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from matplotlib.colors import to_hex  # noqa: E402
from matplotlib.text import Annotation  # noqa: E402

import sdvplot.matplotlib as smpl  # noqa: E402
from sdvplot import _tiers  # noqa: E402
from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot._tiers import prepare  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _frame(lib=pd, **cols):
    return lib.DataFrame(cols)


def _boxes(ax):
    """The drawn logos' window extents."""
    if not hasattr(ax.figure.canvas, "get_renderer"):  # a plotnine figure comes without a renderer
        FigureCanvasAgg(ax.figure)
    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()
    return [a.get_window_extent(renderer) for a in ax.artists if hasattr(a, "_sdvplot_mark")]


def _fits(ax):
    """32 logos drawn, none overlapping another or leaving the panel."""
    boxes, panel = _boxes(ax), ax.bbox
    inside = all(panel.x0 <= b.x0 and b.x1 <= panel.x1 and panel.y0 <= b.y0 and b.y1 <= panel.y1 for b in boxes)
    return len(boxes) == 32 and inside and not any(a.overlaps(b) for a, b in itertools.combinations(boxes, 2))


def _thirty_two():
    """32 logos in 5 tiers (7, 7, 6, 6, 6), as sdvplotR's example deals the NFL; the fixture's two square logos
    stand in for the 32 real ones, which are all square (500 x 500) in the archive."""
    tiers = [1] * 7 + [2] * 7 + [3] * 6 + [4] * 6 + [5] * 6
    return pd.DataFrame({"tier_no": tiers, "team": ["LV", "LAR"] * 16})


# ---- shared prep ------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("lib", [pd, pl])
def test_prep_ranks_teams_in_data_order_within_each_tier(lib):
    t = prepare(_frame(lib, tier_no=[2, 1, 2, 1], team=["LAR", "LV", "LV", "LAR"]), "nfl")
    assert list(zip(t.y, t.x, t.team_ids, strict=True)) == [(2, 1, "14"), (1, 1, "13"), (2, 2, "13"), (1, 2, "14")]
    assert t.labels == ["LAR", "LV", "LV", "LAR"]


def test_prep_presort_orders_by_team_within_tier_and_overrides_tier_rank():
    t = prepare(_frame(tier_no=[1, 1], team=["LV", "LAR"], tier_rank=[1, 2]), "nfl", presort=True)
    assert list(zip(t.labels, t.x, strict=True)) == [("LAR", 1), ("LV", 2)]


def test_prep_uses_a_given_tier_rank():
    t = prepare(_frame(tier_no=[1, 1], team=["LV", "LAR"], tier_rank=[3, 1]), "nfl")
    assert t.x == [3, 1] and t.xlim == pytest.approx((0.9, 3.1))


def test_prep_names_every_missing_column():
    with pytest.raises(ValueError, match=r"tier_no.*team"):
        prepare(_frame(rank=[1]), "nfl")
    with pytest.raises(ValueError, match="team"):
        prepare(_frame(tier_no=[1]), "nfl")


def test_prep_takes_only_a_data_frame():
    with pytest.raises(TypeError):
        prepare({"tier_no": [1], "team": ["LV"]}, "nfl")


def test_prep_needs_numeric_tiers():
    with pytest.raises(TypeError, match="tier_no"):
        prepare(_frame(tier_no=["a"], team=["LV"]), "nfl")


def test_prep_tier_lines_bound_every_tier_unless_told_otherwise():
    data = _frame(tier_no=[1, 2, 3], team=["LV", "LAR", "LV"])
    assert prepare(data, "nfl").lines == [0.5, 1.5, 2.5, 3.5]
    assert prepare(data, "nfl", no_line_below_tier=[2]).lines == [0.5, 1.5, 3.5]
    assert prepare(data, "nfl", no_line_below_tier=2).lines == [0.5, 1.5, 3.5]


def test_prep_tier_labels_wrap_like_strwrap_15():
    # R: strwrap("What are they doing?", 15) -> "What are they" "doing?"; strwrap("abcdefghij klmn", 15) splits
    # (lines stay under 15 characters); a word longer than the width is kept whole.
    desc = {1: "What are they doing?", 2: "abcdefghij klmn", 3: "abcdefghijklmnopq"}
    t = prepare(_frame(tier_no=[1, 2, 3, 4], team=["LV"] * 4), "nfl", tier_desc=desc)
    assert t.breaks == [1, 2, 3, 4]
    assert t.break_labels == ["What are they\ndoing?", "abcdefghij\nklmn", "abcdefghijklmnopq", ""]


def test_prep_default_tier_descriptions_are_sdvplotrs():
    t = prepare(_frame(tier_no=[1, 2, 3, 4, 5, 6], team=["LV"] * 6), "nfl")
    assert t.break_labels == ["Elite", "Very Good", "Medium", "Bad", "What are they\ndoing?", ""]


def test_prep_tier_desc_keys_may_be_strings_as_in_r():
    assert prepare(_frame(tier_no=[1], team=["LV"]), "nfl", tier_desc={"1": "Top"}).break_labels == ["Top"]


def test_prep_limits_put_the_top_tier_first_and_pad_like_ggplot():
    t = prepare(_frame(tier_no=[1, 3, 3], team=["LV", "LAR", "LV"]), "nfl")
    assert t.ylim == pytest.approx((0.4, 3.6))  # (top, bottom): +-0.5 around the tiers, plus expansion(add = 0.1)
    assert t.xlim == pytest.approx((0.95, 2.05))  # ranks 1..2, expanded 5% like a ggplot continuous scale
    assert prepare(_frame(tier_no=[1], team=["LV"]), "nfl").xlim == pytest.approx((0.5, 1.5))  # zero range: +-0.5


def test_prep_skips_an_unknown_team_with_one_warning_and_keeps_its_slot():
    with pytest.warns(SdvplotWarning) as rec:
        t = prepare(_frame(tier_no=[1, 1, 1], team=["LV", "XXX", "LAR"]), "nfl")
    assert len(rec) == 1
    assert list(zip(t.labels, t.x, strict=True)) == [("LV", 1), ("LAR", 3)]  # as sdvplotR: ranked before cleaning
    assert t.xlim == pytest.approx((0.9, 3.1))


@pytest.mark.parametrize("lib", [pd, pl])
def test_prep_skips_a_null_team_quietly_and_a_null_tier_with_one_warning(lib):
    t = prepare(_frame(lib, tier_no=[1, 1], team=["LV", None]), "nfl")
    assert t.labels == ["LV"]
    with pytest.warns(SdvplotWarning, match="missing tier_no") as rec:
        t = prepare(_frame(lib, tier_no=[1.0, None], team=["LV", "LAR"]), "nfl")
    assert len(rec) == 1 and t.labels == ["LV"] and t.breaks == [1]


def test_prep_title_height_and_alpha():
    data = _frame(tier_no=[1], team=["LV"])
    t = prepare(data, "nfl")
    assert (t.title, t.subtitle, t.caption) == ("NFL Team Tiers", "created with the #sdvplot Tiermaker", None)
    assert t.height == _tiers.DEFAULT_HEIGHT and t.alpha == 0.8
    assert prepare(data, "nfl", title="Mine", subtitle=None).title == "Mine"
    with pytest.raises(ValueError, match="height"):
        prepare(data, "nfl", height=0)
    with pytest.raises(ValueError, match="alpha"):
        prepare(data, "nfl", alpha=2)


# ---- matplotlib --------------------------------------------------------------------------------------------------


def test_matplotlib_tiers_draw_each_logo_at_its_rank_and_tier(mark_images):
    fig = smpl.team_tiers(_frame(tier_no=[1, 2, 2], team=["LV", "LV", "LAR"]), "nfl")
    (ax,) = fig.axes
    marks = smpl.drawn_marks(ax)
    assert [m[:3] for m in marks] == [("13", 1, 1), ("13", 1, 2), ("14", 2, 2)]
    assert [m[3] for m in marks] == pytest.approx([_tiers.DEFAULT_HEIGHT] * 3)  # a measured height
    assert ax.get_ylim() == pytest.approx((2.6, 0.4))  # tier 1 on top
    assert list(ax.get_yticks()) == [1, 2] and [t.get_text() for t in ax.get_yticklabels()] == ["Elite", "Very Good"]
    assert sorted(line.get_ydata()[0] for line in ax.lines) == [0.5, 1.5, 2.5]
    assert to_hex(fig.get_facecolor()) == to_hex(ax.get_facecolor()) == _tiers.BG


def test_matplotlib_tiers_titles(mark_images):
    fig = smpl.team_tiers(_frame(tier_no=[1], team=["LV"]), "nfl", caption="data: nflverse")
    texts = {t.get_text(): t for t in fig.axes[0].texts if isinstance(t, Annotation)}
    texts[fig.axes[0].get_title(loc="left")] = fig.axes[0]._left_title
    assert set(texts) == {"NFL Team Tiers", "created with the #sdvplot Tiermaker", "data: nflverse"}
    assert to_hex(texts["NFL Team Tiers"].get_color()) == "#ffffff"
    assert to_hex(texts["data: nflverse"].get_color()) == _tiers.MUTED
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    title, sub = (
        texts["NFL Team Tiers"].get_window_extent(r),
        texts["created with the #sdvplot Tiermaker"].get_window_extent(r),
    )
    assert title.y0 >= sub.y1 and title.x0 == pytest.approx(sub.x0, abs=1)  # the title sits on the subtitle


def test_matplotlib_tiers_devel_draws_team_text_not_logos():
    fig = smpl.team_tiers(_frame(tier_no=[1, 1], team=["LV", "LAR"]), "nfl", devel=True)
    ax = fig.axes[0]
    assert smpl.drawn_marks(ax) == []
    assert [(t.get_text(), t.get_position()) for t in ax.texts if not isinstance(t, Annotation)] == [
        ("LV", (1, 1)),
        ("LAR", (2, 1)),
    ]


def test_matplotlib_tiers_accept_polars(mark_images):
    fig = smpl.team_tiers(pl.DataFrame({"tier_no": [1], "team": ["LV"]}), "nfl")
    assert [m[0] for m in smpl.drawn_marks(fig.axes[0])] == ["13"]


def test_matplotlib_default_height_fits_32_logos_in_5_tiers(mark_images):
    fig = smpl.team_tiers(_thirty_two(), "nfl")
    assert tuple(fig.get_size_inches()) == tuple(mpl.rcParamsDefault["figure.figsize"])
    assert _fits(fig.axes[0])
    # and about the largest such height: the exact limit moves with the platform's font metrics (the tier labels set
    # the panel width; 0.11 overflows on Windows but fits on CI's ubuntu), so test with a margin
    assert not _fits(smpl.team_tiers(_thirty_two(), "nfl", height=_tiers.DEFAULT_HEIGHT * 1.5).axes[0])


# ---- plotnine ----------------------------------------------------------------------------------------------------


def _sp9():
    pytest.importorskip("plotnine")
    import sdvplot.plotnine as sp9

    return sp9


def test_plotnine_tiers_draw_each_logo_at_its_rank_and_tier(mark_images):
    sp9 = _sp9()
    p = sp9.team_tiers(_frame(tier_no=[1, 2, 2], team=["LV", "LV", "LAR"]), "nfl")
    marks = sp9.drawn_marks(p)
    assert [(m[0], m[1], -m[2]) for m in marks] == [("13", 1, 1), ("13", 1, 2), ("14", 2, 2)]  # y is reversed
    fig = p.draw()
    ax = fig.axes[0]
    assert [t.get_text() for t in ax.get_yticklabels()] == ["Elite", "Very Good"]
    assert ax.get_ylim() == pytest.approx((-2.6, -0.4))
    assert {t.get_text() for t in fig.texts} >= {"NFL Team Tiers", "created with the #sdvplot Tiermaker"}


def test_plotnine_tiers_devel_draws_team_text(mark_images):
    sp9 = _sp9()
    fig = sp9.team_tiers(_frame(tier_no=[1, 1], team=["LV", "LAR"]), "nfl", devel=True).draw()
    assert [t.get_text() for t in fig.axes[0].texts] == ["LV", "LAR"]
    assert smpl.drawn_marks(fig.axes[0]) == []


def test_plotnine_tiers_accept_polars_and_warn_once_for_unknown_teams(mark_images):
    sp9 = _sp9()
    with pytest.warns(SdvplotWarning) as rec:
        p = sp9.team_tiers(pl.DataFrame({"tier_no": [1, 1], "team": ["LV", "XXX"]}), "nfl")
    assert len(rec) == 1
    assert [m[0] for m in sp9.drawn_marks(p)] == ["13"]


def test_plotnine_default_height_fits_32_logos_in_5_tiers(mark_images):
    sp9 = _sp9()
    assert _fits(sp9.team_tiers(_thirty_two(), "nfl").draw().axes[0])


# ---- review round -------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("lib", [pd, pl])
def test_prep_r_style_keys_survive_a_null_tier(lib):
    # pandas turns a column with a NaN into floats: str(1.0) is "1.0", not R's "1"
    with pytest.warns(SdvplotWarning):
        t = prepare(
            _frame(lib, tier_no=[1, 2, None], team=["LV", "LAR", "LV"]), "nfl", tier_desc={"1": "Top", "2": "Next"}
        )
    assert t.break_labels == ["Top", "Next"] and t.breaks == [1, 2]
    assert all(type(b) is int for b in t.breaks)


@pytest.mark.parametrize("lib", [pd, pl])
def test_prep_presort_puts_a_null_team_last(lib):
    # "lv" sorts after "None" as text: a missing team must not take a slot mid-tier (R's arrange puts NA last)
    t = prepare(_frame(lib, tier_no=[1, 1, 1], team=["lv", None, "LAR"]), "nfl", presort=True)
    assert list(zip(t.labels, t.x, strict=True)) == [("LAR", 1), ("LV", 2)]
    assert t.xlim == pytest.approx((0.9, 3.1))


def test_prep_devel_labels_are_the_resolved_abbreviations():
    t = prepare(_frame(tier_no=[1, 1, 1], team=["Las Vegas Raiders", "lar", "14"]), "nfl")
    assert t.labels == ["LV", "LAR", "LAR"]


def test_matplotlib_tier_title_is_1_2_times_the_subtitle(mark_images):
    fig = smpl.team_tiers(_frame(tier_no=[1], team=["LV"]), "nfl")
    ax = fig.axes[0]
    (title,) = [t for t in ax.texts if isinstance(t, Annotation) and t.get_text() == "NFL Team Tiers"]
    assert title.get_fontsize() == pytest.approx(1.2 * ax._left_title.get_fontsize())  # sdvplotR: rel(1.2)


def test_one_warning_per_skip_reason_in_both_adapters(mark_images):
    data = _frame(tier_no=[1, 1, 2], team=["LV", "XXX", "LAC"])  # an unknown team; a team with no logo archived
    with pytest.warns(SdvplotWarning) as rec:
        smpl.team_tiers(data, "nfl")
    assert sorted("archived" in str(w.message) for w in rec) == [False, True]

    sp9 = _sp9()
    with pytest.warns(SdvplotWarning) as built:
        p = sp9.team_tiers(data, "nfl")
    assert len(built) == 1  # the unknown team, when built
    with pytest.warns(SdvplotWarning, match="archived") as drawn:
        p.draw()
    assert len(drawn) == 1  # the missing logo, once per render

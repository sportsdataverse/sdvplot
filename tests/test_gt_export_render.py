"""Wave D in a real headless Chrome (great_tables gtsave and nokap), plus the public names.

Tests marked `render` skip when nokap cannot start a browser (no Chrome/Chromium, or a sandbox that blocks it).
"""

import functools
import tempfile
from pathlib import Path

import polars as pl
import pytest

pytest.importorskip("great_tables")
from great_tables import GT  # noqa: E402
from PIL import Image  # noqa: E402

import sdvplot.great_tables as sgt  # noqa: E402
from sdvplot.great_tables import gt_grid, gt_save_batch, gt_save_crop, gt_social_crop, gt_stack_tables  # noqa: E402
from tests.gt_export_fakes import MAGENTA, size  # noqa: E402


@functools.cache
def _chrome_starts():
    try:
        import nokap

        with tempfile.TemporaryDirectory() as tmp:
            nokap.from_html("<p>x</p>", Path(tmp) / "probe.png", selector="p")
        return True
    except Exception:
        return False


@pytest.fixture(autouse=True)
def _skip_render_without_chrome(request):
    if request.node.get_closest_marker("render") and not _chrome_starts():
        pytest.skip("needs Chrome or Chromium (nokap could not start one)")


def _table():
    return GT(pl.DataFrame({"team": ["LV", "LAR", "LAC"], "wins": [10, 8, 5]})).tab_header(title="Wins")


def test_the_export_functions_are_public():
    names = {"gt_save_crop", "gt_save_batch", "gt_social_crop", "gt_grid", "gt_stack_tables"}
    assert names <= set(sgt.__all__)
    assert all(getattr(sgt, n).__module__ == "sdvplot.great_tables._export" for n in names)


@pytest.mark.render
def test_render_save_crop_trims_the_page_and_pads_in_bg(tmp_path):
    out = gt_save_crop(_table(), tmp_path / "t.png", bg="#ff00ff", whitespace=12)
    with Image.open(out) as im:
        rgb = im.convert("RGB")
    edges = [(0, 0), (rgb.width - 1, rgb.height - 1), (11, 11), (rgb.width - 12, rgb.height - 12)]
    assert [rgb.getpixel(p) for p in edges] == [MAGENTA] * 4
    inner = rgb.crop((12, 12, rgb.width - 12, rgb.height - 12))
    colors = {c for _, c in inner.getcolors(1 << 20)}
    assert MAGENTA not in colors and any(sum(c) < 200 for c in colors)  # dark text inside, no bg left inside


@pytest.mark.render
def test_render_zoom_scales_the_table():
    one, two = (gt_save_crop(_table(), zoom=z, whitespace=0) for z in (1, 2))
    assert abs(two.width - 2 * one.width) <= 4 and abs(two.height - 2 * one.height) <= 4


@pytest.mark.render
def test_render_social_crop_meets_the_ratio():
    im = gt_social_crop(_table(), aspect_ratio="16:9")
    assert abs(im.width / im.height - 16 / 9) < 0.01


@pytest.mark.render
def test_render_grid_and_stack_compose_side_by_side_and_down(tmp_path):
    tables = [_table(), _table()]
    one = gt_save_crop(tables[0], whitespace=0)
    across = size(gt_grid(tables, ncol=2, file=tmp_path / "g.png", whitespace=0))
    down = size(gt_stack_tables(tables, file=tmp_path / "s.png", whitespace=0))
    assert across[0] > 1.8 * one.width and across[1] < 1.3 * one.height
    assert down[1] > 1.8 * one.height and down[0] < 1.3 * one.width


@pytest.mark.render
def test_render_grid_on_a_colored_bg_is_trimmed_evenly(tmp_path):
    out = gt_grid([_table(), GT(pl.DataFrame({"a": [1]}))], file=tmp_path / "g.png", bg="#ff00ff", whitespace=10)
    with Image.open(out) as im:
        rgb = im.convert("RGB")
    inner = rgb.crop((10, 10, rgb.width - 10, rgb.height - 10))
    iw, ih = inner.size
    for edge in [(0, 0, iw, 1), (0, ih - 1, iw, ih), (0, 0, 1, ih), (iw - 1, 0, iw, ih)]:
        assert any(c != MAGENTA for _, c in inner.crop(edge).getcolors(1 << 16))  # content on every edge


@pytest.mark.render
def test_render_batch_matches_widths(tmp_path):
    df = pl.DataFrame({"g": ["short", "a much longer group value"], "v": [1, 2]})
    paths = gt_save_batch(df, "g", lambda d, v: GT(d).tab_header(title=str(v)), "t-{group}.png", tmp_path, quiet=True)
    assert len({size(p)[0] for p in paths}) == 1


@pytest.mark.render
@pytest.mark.parametrize("all_important", [False, True], ids=["as_raw_html", "notebook repr"])
@pytest.mark.parametrize("theme_first", [False, True])
def test_render_kenpom_bands_rows_and_leaves_a_fill_on_top(tmp_path, all_important, theme_first):
    df = pl.DataFrame({"team": ["LV", "LAR", "LAC", "KC"], "conf": ["W", "W", "W", "W"], "wins": [10, 8, 5, 15]})

    def fill(gt):
        return gt.data_color(columns="wins", palette=["#FF00FF", "#FF00FF"])

    gt = GT(df, groupname_col="conf", id="kp")
    gt = fill(sgt.gt_theme_kenpom(gt)) if theme_first else sgt.gt_theme_kenpom(fill(gt))
    html = gt.as_raw_html(make_page=True, all_important=all_important)
    import nokap

    with Image.open(nokap.from_html(html, tmp_path / "kp.png", selector="#kp table")) as im:
        colors = {c for _, c in im.convert("RGB").getcolors(1 << 20)}
    assert {MAGENTA, (0xF2, 0xFA, 0xFD), (0xE5, 0xEC, 0xF9)} <= colors  # the fill and both bands


@pytest.mark.render
@pytest.mark.parametrize(
    ("helper", "covered"),
    [
        (lambda gt: sgt.gt_color_ranks(gt, "rk", palette=["#FF00FF", "#FF00FF"]), True),  # data_color: plain fills
        (lambda gt: sgt.gt_color_results(gt, "res", win_color="#FF00FF", loss_color="#FF00FF"), False),  # !important
        (lambda gt: sgt.gt_color_pills(gt, "rk", palette=["#FF00FF", "#FF00FF"], domain=[1, 4]), False),  # own span
    ],
    ids=["gt_color_ranks", "gt_color_results", "gt_color_pills"],
)
def test_render_notebook_stripes_cover_only_plain_fills(tmp_path, helper, covered):
    # in VS Code and Positron great_tables' repr marks its stylesheet !important, so a stripe beats a plain inline fill
    import warnings

    import nokap

    df = pl.DataFrame({"team": ["LV", "LAR", "LAC", "KC"], "res": ["W", "L", "W", "L"], "rk": [1, 2, 3, 4]})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # the striping warning, tested offline
        gt = helper(GT(df, id="st").opt_row_striping())
    shot = nokap.from_html(gt.as_raw_html(make_page=True, all_important=True), tmp_path / "s.png", selector="#st table")
    with Image.open(shot) as im:
        rgb = im.convert("RGB")
    bands = [rgb.crop((0, rgb.height * k // 5, rgb.width, rgb.height * (k + 1) // 5)) for k in range(1, 5)]
    magenta = [sum(n for n, c in band.getcolors(1 << 20) if c == MAGENTA) for band in bands]
    filled = [n > max(magenta) / 2 for n in magenta]  # a covered row keeps a sliver of its neighbor's fill
    assert filled == ([True, False, True, False] if covered else [True] * 4)


NAVY = (0x00, 0x22, 0x44)


@pytest.mark.render
@pytest.mark.parametrize(
    "helper",
    [
        lambda gt: sgt.gt_color_results(gt, "res", win_color="#002244"),  # white ink by default
        lambda gt: sgt.gt_bold_rows(gt, rows=[0, 1, 2, 3], text_color="white", highlight_color="#002244"),
        lambda gt: sgt.gt_spotlight(gt, rows=[0, 1, 2, 3], fill="#002244", text_color="white", dim_color=None),
        lambda gt: sgt.gt_highlight_cells(
            gt, ["team", "res"], lambda s: s.is_not_null(), fill="#002244", text_color="white"
        ),  # fmt: skip
    ],
    ids=["gt_color_results", "gt_bold_rows", "gt_spotlight", "gt_highlight_cells"],
)
def test_render_vscode_stripes_leave_the_text_color_paired_with_a_fill(tmp_path, helper):
    # the VS Code/Positron repr (all_important) made the stripes' text color beat a helper's plain one on rows 2 and 4:
    # white ink on a navy fill turned the stripe's dark gray
    import nokap

    df = pl.DataFrame({"team": ["LVLVLV", "LARLAR", "LACLAC", "KCKCKC"], "res": ["W", "W", "W", "W"]})
    gt = helper(GT(df, id="ink").opt_row_striping())
    shot = nokap.from_html(
        gt.as_raw_html(make_page=True, all_important=True), tmp_path / "i.png", selector="#ink table"
    )
    with Image.open(shot) as im:
        rgb = im.convert("RGB")
    column = [rgb.getpixel((3, y)) == NAVY for y in range(rgb.height)]
    rows = []  # the navy rows, top to bottom, as (first y, last y)
    for y, navy in enumerate(column):
        if navy and (not rows or rows[-1][1] != y - 1):
            rows.append((y, y))
        elif navy:
            rows[-1] = (rows[-1][0], y)
    inked = [
        any(min(c) >= 235 for _, c in rgb.crop((0, top + 2, rgb.width, bottom - 1)).getcolors(1 << 20))
        for top, bottom in rows
    ]
    assert inked == [True] * 4, rows


@pytest.mark.render
def test_render_kenpom_bands_alternate_over_data_rows_around_summary_rows(tmp_path):
    # a group's summary row is a <tr> in the body: counted as a data row, it shifted the bands of the next group
    import nokap

    df = pl.DataFrame({"team": ["LV", "KC", "BUF", "MIA"], "conf": ["W", "W", "E", "E"], "w": [1, 2, 3, 4]})
    gt = GT(df, groupname_col="conf", rowname_col="team", id="kps").summary_rows(fns={"Sum": pl.col("w").sum()})
    shot = nokap.from_html(
        sgt.gt_theme_kenpom(gt).as_raw_html(make_page=True), tmp_path / "k.png", selector="#kps table"
    )
    with Image.open(shot) as im:
        rgb = im.convert("RGB")
    x = rgb.width - 4  # inside the last body column, clear of its text
    runs = []  # the band color of each data row, top to bottom
    for y in range(rgb.height):
        c = rgb.getpixel((x, y))
        if c in ((0xF2, 0xFA, 0xFD), (0xE5, 0xEC, 0xF9)) and (not runs or runs[-1][1] != y - 1 or runs[-1][0] != c):
            runs.append([c, y])
        elif runs and runs[-1][0] == c and runs[-1][1] == y - 1:
            runs[-1][1] = y
    assert [c for c, _ in runs] == [(0xF2, 0xFA, 0xFD), (0xE5, 0xEC, 0xF9)] * 2

"""gt_save_batch, with a fake renderer in place of headless Chrome."""

from pathlib import Path

import pandas as pd
import polars as pl
import pytest

pytest.importorskip("great_tables")
from great_tables import GT  # noqa: E402
from PIL import Image  # noqa: E402

import sdvplot.great_tables._export as ex  # noqa: E402
from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.great_tables._export import gt_save_batch  # noqa: E402
from tests.gt_export_fakes import BLACK, WHITE, fake_render, forbid_render, size  # noqa: E402


def test_batch_writes_one_image_per_group_at_one_width(monkeypatch, tmp_path, capsys):
    calls = fake_render(monkeypatch, [(40, 30), (60, 20)])
    df = pl.DataFrame({"conf": ["North / East", "South"], "w": [1, 2]})
    paths = gt_save_batch(df, "conf", lambda d, v: GT(d), "net-{group}.png", tmp_path / "out", whitespace=5)
    assert paths == [str(tmp_path / "out" / "net-north-east.png"), str(tmp_path / "out" / "net-south.png")]
    assert [size(p) for p in paths] == [(70, 40), (70, 30)]  # both padded to the widest table (60) + 2 * 5
    with Image.open(paths[0]) as im:
        assert im.getpixel((14, 5)) == WHITE and im.getpixel((15, 5)) == BLACK  # the narrow one is centered
    assert [c[1:] for c in calls] == [(2, 5), (2, 5)]
    err = capsys.readouterr().err
    assert "Building 'North / East'" in err and "Wrote 2 file(s)" in err


def test_batch_without_match_width_keeps_each_width(monkeypatch, tmp_path):
    fake_render(monkeypatch, [(40, 30), (60, 20)])
    df = pl.DataFrame({"g": ["a", "b"], "w": [1, 2]})
    paths = gt_save_batch(df, "g", lambda d, v: GT(d), "{group}.png", tmp_path, match_width=False, whitespace=5)
    assert [size(p) for p in paths] == [(50, 40), (70, 30)]


def test_batch_gives_fn_each_groups_rows_in_the_callers_frame_type(monkeypatch, tmp_path):
    fake_render(monkeypatch, [(10, 10)] * 4)
    seen = {}

    def build(d, value):
        seen[value] = d
        return GT(d)

    df = pd.DataFrame({"g": ["b", None, "a", "b"], "v": [1, 2, 3, 4]}, index=[10, 11, 12, 13])
    paths = gt_save_batch(df, "g", build, "{group}.png", tmp_path, quiet=True)
    assert [Path(p).name for p in paths] == ["b.png", "a.png"]  # first-appearance order; the missing value skipped
    assert (
        isinstance(seen["b"], pd.DataFrame) and seen["b"]["v"].tolist() == [1, 4] and list(seen["b"].index) == [10, 13]
    )
    gt_save_batch(pl.from_pandas(df), "g", build, "{group}.png", tmp_path, quiet=True)
    assert isinstance(seen["a"], pl.DataFrame) and seen["a"]["v"].to_list() == [3]


def test_batch_refuses_groups_that_share_a_file_name(monkeypatch, tmp_path):
    forbid_render(monkeypatch)
    df = pl.DataFrame({"g": ["North/East", "north east"], "v": [1, 2]})
    with pytest.raises(ValueError, match="net-north-east.png"):
        gt_save_batch(df, "g", lambda d, v: GT(d), "net-{group}.png", tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_batch_skips_a_failing_group_and_warns_once(monkeypatch, tmp_path):
    fake_render(monkeypatch, [(10, 10)])

    def build(d, value):
        if value == "bad":
            raise KeyError("no column")
        return "not a table" if value == "notgt" else GT(d)

    df = pl.DataFrame({"g": ["ok", "bad", "notgt"], "v": [1, 2, 3]})
    with pytest.warns(SdvplotWarning, match=r"2 group\(s\) failed") as record:
        paths = gt_save_batch(df, "g", build, "{group}.png", tmp_path, quiet=True)
    assert [Path(p).name for p in paths] == ["ok.png"]
    assert len(record) == 1
    message = str(record[0].message)
    assert "bad: 'no column'" in message and "notgt: fn's return value must be a great_tables GT, not str" in message


def test_batch_raises_when_no_group_builds(monkeypatch, tmp_path):
    forbid_render(monkeypatch)
    df = pl.DataFrame({"g": ["a", "b"], "v": [1, 2]})
    with pytest.raises(RuntimeError, match="No group built successfully"):
        gt_save_batch(df, "g", lambda d, v: 1 / 0, "{group}.png", tmp_path, quiet=True)


def test_batch_stops_when_no_browser_can_start(monkeypatch, tmp_path):
    import nokap

    calls = []

    def render(gt, zoom, expand):
        calls.append(gt)
        raise nokap.ChromeNotFoundError()

    monkeypatch.setattr(ex, "_render_gt", render)
    df = pl.DataFrame({"g": ["a", "b", "c"], "v": [1, 2, 3]})
    with pytest.raises(nokap.ChromeNotFoundError):
        gt_save_batch(df, "g", lambda d, v: GT(d), "{group}.png", tmp_path, quiet=True)
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"group": "nope"}, ValueError, "group must name one column"),
        ({"file": "net.png"}, ValueError, r"must contain \{group\}"),
        ({"file": "net-{group}"}, ValueError, "image extension"),
        ({"fn": "build"}, TypeError, "fn must be a function"),
        ({"data": [1, 2]}, TypeError, "Unsupported"),
        ({"data": pl.DataFrame({"g": [None, None]}, schema={"g": pl.String})}, ValueError, "no non-missing"),
        ({"bg": "nope"}, ValueError, "color"),
        ({"whitespace": -5}, ValueError, "whitespace"),
        ({"zoom": 0}, ValueError, "zoom"),
        ({"zoom": "2"}, ValueError, "zoom"),
    ],
)
def test_batch_checks_its_arguments_before_rendering(monkeypatch, tmp_path, kwargs, error, match):
    forbid_render(monkeypatch)
    args = {"data": pl.DataFrame({"g": ["a"]}), "group": "g", "fn": lambda d, v: GT(d), "file": "{group}.png"}
    with pytest.raises(error, match=match):
        gt_save_batch(**{**args, **kwargs}, dir=tmp_path)

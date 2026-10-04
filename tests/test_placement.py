import math

import numpy as np
import pandas as pd
import polars as pl
import pytest

from sdvplot._errors import SdvplotWarning
from sdvplot._placement import Placement, check_alpha, check_height, place


@pytest.mark.parametrize("ok", [0.01, 0.1, 1, 1.0, np.float64(0.5)])
def test_check_height_accepts_a_fraction(ok):
    assert check_height(ok) == float(ok)


@pytest.mark.parametrize("bad", [0, -0.1, 1.5, True, math.nan, "0.1", None])
def test_check_height_rejects_everything_else(bad):
    with pytest.raises(ValueError, match="fraction of the plot height"):
        check_height(bad)


@pytest.mark.parametrize("bad", [-0.1, 1.01, False, math.nan, None])
def test_check_alpha_rejects_out_of_range(bad):
    with pytest.raises(ValueError, match="opacity"):
        check_alpha(bad)


def test_place_resolves_selects_and_keeps_order(manifest):
    out = place([10.0, 20.0], [-3.0, -7.0], ["LV", "LAR"], league="nfl")
    assert [(p.team_id, p.x, p.y, p.url) for p in out] == [
        ("13", 10.0, -3.0, "https://cdn/1111.png"),
        ("14", 20.0, -7.0, "https://cdn/6666.png"),
    ]
    assert all(isinstance(p, Placement) and p.aspect == 1.0 and p.mark is not None for p in out)


def test_place_reads_pandas_by_position_not_label(manifest):
    s = pd.Series
    out = place(
        s([10.0, 20.0], index=[5, 6]), s([-3.0, -7.0], index=[5, 6]), s(["LV", "LAR"], index=[5, 6]), league="nfl"
    )
    assert [(p.team_id, p.x, p.y) for p in out] == [("13", 10.0, -3.0), ("14", 20.0, -7.0)]
    lout = place(pl.Series([10.0, 20.0]), pl.Series([-3.0, -7.0]), pl.Series(["LV", "LAR"]), league="nfl")
    assert [(p.team_id, p.x, p.y) for p in lout] == [("13", 10.0, -3.0), ("14", 20.0, -7.0)]


def test_place_takes_the_aspect_from_the_manifest(manifest):
    (p,) = place([0], [0], ["LV"], league="nfl", kind="wordmark")
    assert p.url == "https://cdn/4444.png" and p.aspect == pytest.approx(2.5)


def test_place_skips_an_unknown_team_with_its_own_xy(manifest):
    with pytest.warns(SdvplotWarning):
        out = place([10.0, 20.0], [-3.0, -7.0], ["XXX", "LV"], league="nfl")
    assert [(p.team_id, p.x, p.y) for p in out] == [("13", 20.0, -7.0)]


def test_place_skips_missing_positions_once(manifest):
    with pytest.warns(SdvplotWarning, match=r"skipped 2 point\(s\) with a missing x or y") as w:
        out = place([None, 20.0, math.nan], [-3.0, -7.0, 1.0], ["LV", "LAR", "LV"], league="nfl")
    assert [p.team_id for p in out] == ["14"]
    assert len([x for x in w if "missing x or y" in str(x.message)]) == 1


def test_place_skips_a_team_with_no_mark(manifest):
    with pytest.warns(SdvplotWarning, match="with no logo archived"):
        assert place([0], [0], ["7"], league="ohl") == []


def test_place_rejects_unequal_lengths(manifest):
    with pytest.raises(ValueError, match="same length, got 2, 1 and 2"):
        place([1, 2], [1], ["LV", "LAR"], league="nfl")


def test_place_rejects_an_unknown_kind(manifest):
    with pytest.raises(ValueError, match="kind must be one of"):
        place([1], [1], ["LV"], league="nfl", kind="banner")


def test_place_uses_one_season_per_point(manifest):
    out = place([1, 2], [1, 2], ["LV", "LV"], league="nfl", season=[2010, 2024])
    assert [p.url for p in out] == ["https://cdn/3333.png", "https://cdn/1111.png"]


def test_place_headshots_use_player_ids():
    out = place([1.0], [2.0], ["3139477"], league="nfl", kind="headshot", id_system="espn")
    assert out == [
        Placement(
            "3139477",
            1.0,
            2.0,
            "https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/3139477.png",
            None,
            None,
        )
    ]
    with pytest.warns(SdvplotWarning, match="with no headshot"):
        assert place([1.0], [2.0], ["not-an-id"], league="nfl", kind="headshot", id_system="espn") == []

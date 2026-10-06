"""pitch_coords (the port of sdvplotR's sdv_pitch_coords): any soccer provider's frame to the 105 x 68 pitch."""

import hashlib
from importlib import resources
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import pytest

import sdvplot
from sdvplot import _pitch

FIXTURES = Path(__file__).parent / "fixtures"
MPL_KEYS = {"metrica": "metricasports"}  # mplsoccer's own name for the pitch
SHA256 = "5e6b0b1181b80a338775ac6b3c9318c8154452f018b2e85ec3a7c5440723ed3d"  # the same pin as sdvplotR's test


def test_the_landmark_table_is_the_shared_hash_pinned_copy():
    data = resources.files("sdvplot").joinpath("data", "pitch_landmarks.csv").read_bytes()
    assert hashlib.sha256(data).hexdigest() == SHA256


def test_each_fixed_provider_has_9_ascending_x_and_8_y_landmarks():
    for p in _pitch.FIXED:
        x, y = _pitch._landmarks(p, None)
        assert len(x) == 9 and len(y) == 8 and bool((np.diff(x) > 0).all()), p
    assert _pitch._landmarks("impect", None)[0].tolist() == [-52.5, -47, -41.5, -36, 0, 36, 41.5, 47, 52.5]
    assert _pitch._landmarks("statsbomb", None)[1].tolist() == [80, 62, 50, 44, 36, 30, 18, 0]


def test_physical_landmarks_reproduce_mplsoccer_and_keep_regulation_boxes():
    x, y = _pitch._physical("tracab", 105, 68)
    assert x.tolist() == pytest.approx([-5250, -4700, -4150, -3600, 0, 3600, 4150, 4700, 5250])
    assert y.tolist() == pytest.approx([-3400, -2016, -916, -366, 366, 916, 2016, 3400])
    mx, my = _pitch._physical("metrica", 105, 68)
    assert mx.tolist() == pytest.approx([v / 105 for v in (0, 5.5, 11, 16.5, 52.5, 88.5, 94, 99.5, 105)])
    assert [my[0], my[-1]] == pytest.approx([1, 0])  # Metrica's y = 0 is the top touchline: the attacker's left
    wx, wy = _pitch._physical("tracab", 100, 64)
    assert [wx[0], wx[3], wx[4]] == pytest.approx([-5000, -3350, 0])
    assert [wy[0], wy[1]] == pytest.approx([-3200, -2016])  # the box is 40.32 m wide on any pitch


def test_interp_hits_landmarks_interpolates_and_extrapolates_beyond_both_ends():
    src, dst = np.array([0.0, 10, 20]), np.array([-1.0, 0, 4])
    assert _pitch._interp(np.array([0.0, 5, 10, 15, 20]), src, dst).tolist() == [-1, -0.5, 0, 2, 4]
    assert _pitch._interp(np.array([-10.0, 30]), src, dst).tolist() == [-2, 8]  # end-segment slopes: never clamped
    out = _pitch._interp(np.array([np.nan, 5.0]), src, dst)
    assert np.isnan(out[0]) and out[1] == -0.5
    assert _pitch._interp(np.array([], dtype=float), src, dst).tolist() == []
    assert _pitch._interp(np.array([0.0, 20]), np.array([20.0, 10, 0]), dst).tolist() == [4, -1]  # descending


def _events() -> pl.DataFrame:
    return pl.read_csv(
        FIXTURES / "espn_soccer_events.csv",
        schema_overrides={"event_id": pl.Utf8, "play_id": pl.Utf8, "side": pl.Utf8},
    )


@pytest.mark.parametrize("lib", [pd, pl])
def test_opta_landmarks_land_on_the_regulation_landmarks(lib):
    out = sdvplot.pitch_coords(
        lib.DataFrame({"x": [88.5, 83, 50, 100, 0], "y": [50.0, 21.1, 100, 45.2, 0]}), provider="opta"
    )
    assert type(out) is lib.DataFrame
    assert list(out.columns) == ["x", "y", "pitch_x", "pitch_y"]
    assert list(out["pitch_x"]) == pytest.approx([41.5, 36, 0, 52.5, -52.5])
    assert list(out["pitch_y"]) == pytest.approx([0, -20.16, 34, -3.66, -34], abs=1e-12)


def test_statsbomb_y_zero_is_the_attackers_left():
    out = sdvplot.pitch_coords(pl.DataFrame({"x": [108, 120, 60], "y": [40, 0, 80]}), provider="statsbomb")
    assert out["pitch_x"].to_list() == pytest.approx([41.5, 52.5, 0])
    assert out["pitch_y"].to_list() == pytest.approx([0, 34, -34], abs=1e-12)


def test_aliases_case_custom_columns_and_replaced_outputs():
    shots = pl.DataFrame({"x": [88.5, 17], "y": [50.0, 78.9]})
    assert sdvplot.pitch_coords(shots, provider="statsperform").equals(sdvplot.pitch_coords(shots, provider="opta"))
    assert sdvplot.pitch_coords(shots, provider="Opta").equals(sdvplot.pitch_coords(shots, provider="opta"))
    named = sdvplot.pitch_coords(pl.DataFrame({"px": [88.5], "py": [50]}), provider="opta", x="px", y="py")
    assert named.columns == ["px", "py", "pitch_x", "pitch_y"]
    assert [named["pitch_x"][0], named["pitch_y"][0]] == pytest.approx([41.5, 0], abs=1e-12)
    replaced = sdvplot.pitch_coords(pl.DataFrame({"x": [88.5], "y": [50], "pitch_x": ["old"]}), provider="opta")
    assert replaced.columns == ["x", "y", "pitch_x", "pitch_y"]
    assert replaced["pitch_x"].to_list() == pytest.approx([41.5])


def test_flip_turns_rows_half_a_turn():
    d = pl.DataFrame({"x": [88.5, 88.5], "y": [21.1, 21.1], "away": [False, True]})
    out = sdvplot.pitch_coords(d, provider="opta", flip="away")
    assert out["pitch_x"].to_list() == pytest.approx([41.5, -41.5])
    assert out["pitch_y"].to_list() == pytest.approx([-20.16, 20.16])
    assert sdvplot.pitch_coords(d, provider="opta", flip=True)["pitch_x"].to_list() == pytest.approx([-41.5, -41.5])
    assert sdvplot.pitch_coords(d, provider="opta", flip=False)["pitch_x"].to_list() == pytest.approx([41.5, 41.5])
    with pytest.raises(ValueError, match="does not have"):
        sdvplot.pitch_coords(d, provider="opta", flip="nope")
    with pytest.raises(ValueError, match="no missing values"):
        sdvplot.pitch_coords(d.with_columns(away=pl.Series([True, None])), provider="opta", flip="away")
    with pytest.raises(ValueError, match="True/False"):
        sdvplot.pitch_coords(d.with_columns(away=pl.Series([1, 0])), provider="opta", flip="away")
    with pytest.raises(TypeError, match="flip must be"):
        sdvplot.pitch_coords(d, provider="opta", flip=[True, False])


@pytest.mark.parametrize(
    ("kwargs", "exc", "match"),
    [
        ({"provider": "optaa"}, ValueError, "provider must be one of"),
        ({"provider": 1}, TypeError, "provider must be a string"),
        ({"provider": "opta", "pitch_length": 105}, ValueError, "only apply to tracking providers"),
        ({"provider": "tracab"}, ValueError, "needs pitch_length and pitch_width"),
        ({"provider": "tracab", "pitch_length": 80, "pitch_width": 68}, ValueError, "from 90 to 120"),
        ({"provider": "tracab", "pitch_length": 105, "pitch_width": "68"}, ValueError, "from 45 to 90"),
        ({"provider": "tracab", "pitch_length": True, "pitch_width": 68}, ValueError, "from 90 to 120"),
        ({"provider": "opta", "x": "y"}, ValueError, "must name different columns"),
        ({"provider": "opta", "y": 3}, TypeError, "single column name"),
    ],
)
def test_arguments_are_validated(kwargs, exc, match):
    with pytest.raises(exc, match=match):
        sdvplot.pitch_coords(pl.DataFrame({"x": [1.0], "y": [2.0]}), **kwargs)


def test_bad_data_raises_like_court_coords():
    with pytest.raises(TypeError, match="pandas or polars DataFrame"):
        sdvplot.pitch_coords({"x": [1], "y": [2]}, provider="opta")
    with pytest.raises(ValueError, match=r"missing column\(s\) \['y'\]"):
        sdvplot.pitch_coords(pl.DataFrame({"x": [1.0]}), provider="opta")
    with pytest.raises(ValueError, match="not numbers"):
        sdvplot.pitch_coords(pl.DataFrame({"x": ["a"], "y": ["2"]}), provider="opta")
    with pytest.raises(TypeError, match="must be numeric"):
        sdvplot.pitch_coords(pl.DataFrame({"x": [True], "y": [2.0]}), provider="opta")


@pytest.mark.parametrize("lib", [pd, pl])
def test_empty_frames_keep_float_output_columns(lib):
    empty = lib.DataFrame({"x": np.array([], dtype=float), "y": np.array([], dtype=float)})
    out = sdvplot.pitch_coords(empty, provider="opta")
    assert len(out) == 0 and list(out.columns) == ["x", "y", "pitch_x", "pitch_y"]
    if lib is pl:
        assert out.schema["pitch_x"] == pl.Float64 and out.schema["pitch_y"] == pl.Float64
    else:
        assert str(out["pitch_x"].dtype).lower().startswith("float")


def test_missing_values_stay_null_and_never_become_nan():
    out = sdvplot.pitch_coords(pl.DataFrame({"x": [None, 88.5], "y": [50.0, None]}), provider="opta")
    assert out["pitch_x"].to_list() == [None, pytest.approx(41.5)]
    assert out["pitch_y"][1] is None
    assert out["pitch_x"].is_nan().sum() == 0 and out["pitch_y"].is_nan().sum() == 0
    pd_out = sdvplot.pitch_coords(pd.DataFrame({"x": [None, 88.5], "y": [50.0, None]}), provider="opta")
    assert pd_out["pitch_x"].isna().tolist() == [True, False]


def test_integers_number_strings_and_off_pitch_points():
    ints = sdvplot.pitch_coords(pl.DataFrame({"x": [100, 50], "y": [0, 100]}), provider="opta")
    assert ints["pitch_x"].to_list() == pytest.approx([52.5, 0])
    assert ints["pitch_y"].to_list() == pytest.approx([-34, 34])
    strs = sdvplot.pitch_coords(pl.DataFrame({"x": ["88.5", "50"], "y": ["50", "100"]}), provider="opta")
    assert strs["pitch_x"].to_list() == pytest.approx([41.5, 0])
    off = sdvplot.pitch_coords(pl.DataFrame({"x": [-0.5], "y": [101.0]}), provider="opta")
    assert off["pitch_x"][0] < -52.5 and off["pitch_y"][0] > 34  # extrapolated, not clamped


def test_espn_every_penalty_lands_on_the_spot():
    out = sdvplot.pitch_coords(_events(), provider="espn")
    pens = out.filter(pl.col("type").str.starts_with("Penalty"))
    assert pens.height >= 10
    assert ((pens["pitch_x"] - 41.5).abs() < 0.5).all() and (pens["pitch_y"].abs() < 1).all()


def test_espn_side_of_the_box_matches_the_sign_of_pitch_y():
    out = sdvplot.pitch_coords(_events(), provider="espn").filter(pl.col("side").is_not_null())
    assert out.height >= 20
    assert ((out["side"] == "left") == (out["pitch_y"] > 0)).all()


def test_espn_zero_zero_is_no_location_but_one_zero_axis_is_real():
    d = pl.DataFrame({"field_position_x": [0.0, 0.0, 0.23], "field_position_y": [0.0, 0.4, 0.5]})
    out = sdvplot.pitch_coords(d, provider="espn")
    assert out["pitch_x"][0] is None and out["pitch_y"][0] is None
    assert out["pitch_x"][1] == pytest.approx(52.5) and out["pitch_y"][1] > 0
    assert [out["pitch_x"][2], out["pitch_y"][2]] == pytest.approx([41.5, 0], abs=1e-9)
    events = sdvplot.pitch_coords(_events(), provider="espn")
    zeros = events.filter((pl.col("field_position_x") == 0) & (pl.col("field_position_y") == 0))
    assert zeros.height > 0 and zeros["pitch_x"].null_count() == zeros.height


def test_tracking_providers_convert_from_the_venues_real_size():
    d = pl.DataFrame({"x": [4150.0, 0, -5250, 5400], "y": [0.0, 3400, -2016, 0]})
    out = sdvplot.pitch_coords(d, provider="tracab", pitch_length=105, pitch_width=68)
    assert out["pitch_x"].to_list() == pytest.approx([41.5, 0, -52.5, 54])  # 5400 cm: past the goal line
    assert out["pitch_y"].to_list() == pytest.approx([0, 34, -20.16, 0], abs=1e-12)
    m = sdvplot.pitch_coords(
        pl.DataFrame({"x": [0.5], "y": [0.0]}), provider="metrica", pitch_length=105, pitch_width=68
    )
    assert [m["pitch_x"][0], m["pitch_y"][0]] == pytest.approx([0, 34], abs=1e-12)
    v = sdvplot.pitch_coords(
        pl.DataFrame({"x": [39.0], "y": [0.0]}), provider="skillcorner", pitch_length=100, pitch_width=64
    )
    assert v["pitch_x"][0] == pytest.approx(41.5)  # 11 m from a 100 m pitch's goal line is still the spot


def _mplsoccer():
    try:  # not importorskip(exc_type=): that needs pytest 8.2, and the floor mplsoccer fails to import on newer matplotlib
        import mplsoccer
    except ImportError:
        pytest.skip("mplsoccer is not importable")
    return mplsoccer


def _grid(x, y):
    def mid(v):
        s = np.sort(v)
        return (s[:-1] + s[1:]) / 2

    xs = np.unique(np.concatenate([x, mid(x)]))
    ys = np.unique(np.concatenate([y, mid(y)]))
    gx, gy = np.meshgrid(xs, ys)
    return gx.ravel(), gy.ravel()


@pytest.mark.parametrize("provider", ["opta", "wyscout", "statsbomb", "uefa", "impect"])
def test_fixed_providers_agree_with_mplsoccer(provider):
    mplsoccer = _mplsoccer()
    gx, gy = _grid(*_pitch._landmarks(provider, None))
    std = mplsoccer.Standardizer(pitch_from=MPL_KEYS.get(provider, provider), pitch_to="uefa")
    tx, ty = std.transform(gx, gy)
    ours = sdvplot.pitch_coords(pl.DataFrame({"x": gx, "y": gy}), provider=provider)
    # Standardizer's 105 x 68 frame has its origin bottom-left with +y on the attacker's left; ours is centered
    np.testing.assert_allclose(ours["pitch_x"].to_numpy(), np.asarray(tx) - 52.5, rtol=0, atol=1e-9)
    np.testing.assert_allclose(ours["pitch_y"].to_numpy(), np.asarray(ty) - 34, rtol=0, atol=1e-9)


@pytest.mark.parametrize(
    ("provider", "length", "width", "atol"),
    [("tracab", 105, 68, 1e-9), ("tracab", 100, 64, 1e-9), ("skillcorner", 105, 68, 1e-9), ("metrica", 105, 68, 0.01)],
)
def test_tracking_providers_agree_with_mplsoccer(provider, length, width, atol):
    # atol 0.01 m for Metrica: mplsoccer rounds Metrica's landmark fractions to 4 decimals (up to 0.5 cm)
    mplsoccer = _mplsoccer()
    gx, gy = _grid(*_pitch._physical(provider, length, width))
    std = mplsoccer.Standardizer(
        pitch_from=MPL_KEYS.get(provider, provider), pitch_to="uefa", length_from=length, width_from=width
    )
    tx, ty = std.transform(gx, gy)
    ours = sdvplot.pitch_coords(
        pl.DataFrame({"x": gx, "y": gy}), provider=provider, pitch_length=length, pitch_width=width
    )
    np.testing.assert_allclose(ours["pitch_x"].to_numpy(), np.asarray(tx) - 52.5, rtol=0, atol=atol)
    np.testing.assert_allclose(ours["pitch_y"].to_numpy(), np.asarray(ty) - 34, rtol=0, atol=atol)


def test_matches_sdvplotr_on_a_grid_of_every_provider():
    """sdvplotR's sdv_pitch_coords() on landmarks, midpoints, off-pitch points and flipped rows of every provider
    (tools/export_parity_extras.R): the two packages share the table and the arithmetic, so they agree exactly."""
    theirs = pl.read_csv(
        FIXTURES / "sdvplotr_pitch_coords.csv",
        schema_overrides={"flip": pl.Boolean, "pitch_length": pl.Float64, "pitch_width": pl.Float64},
        null_values="NA",
    )
    keys = ["provider", "pitch_length", "pitch_width"]
    for (provider, length, width), group in theirs.group_by(keys, maintain_order=True):
        sizes = {} if length is None else {"pitch_length": length, "pitch_width": width}
        ours = sdvplot.pitch_coords(
            group.select("x", "y", "flip"), provider=provider, x="x", y="y", flip="flip", **sizes
        )
        for col in ("pitch_x", "pitch_y"):
            np.testing.assert_allclose(
                ours[col].to_numpy(), group[col].to_numpy(), rtol=0, atol=1e-12, err_msg=f"{provider} {col}"
            )

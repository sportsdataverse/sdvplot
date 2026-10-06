"""pitch_coords (the port of sdvplotR's sdv_pitch_coords): any soccer provider's frame to the 105 x 68 pitch."""

import hashlib
from importlib import resources
from pathlib import Path

import numpy as np
import pytest

from sdvplot import _pitch

FIXTURES = Path(__file__).parent / "fixtures"
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

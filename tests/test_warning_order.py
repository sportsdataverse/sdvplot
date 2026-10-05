"""Warnings that list values list them in the order the values first appear, whatever the hash seed: the weekly docs
render prints them, and a reordering rewrites the page. Each run is a fresh interpreter with its own PYTHONHASHSEED."""

import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.real_index

SCRIPT = """
import warnings
import pandas as pd
import polars as pl
import sdvplot
from sdvplot import _tiers

values = ["ZZZ9", "LV", "AAA9", "MMM9", "ZZZ9", "QQQ9", "XYZ9", "BBB9", "KKK9", "CCC9"]
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    for v in (values, pd.Series(values), pl.Series(values)):
        sdvplot.resolve(v, "nfl")  # unknown values
    sdvplot.resolve(["KSU", "LIN", "PAC"], "ncaa_baseball")  # ambiguous values
    sdvplot.palette("nfl", teams=values)
    sdvplot.palette("ncaa_baseball")  # the shared abbreviations
    _tiers.prepare(pd.DataFrame({"tier_no": [1, None, 2, None], "team": ["LV", "QQQ9", "KC", "AAA9"]}), "nfl")
for w in caught:
    print(w.message)
print(sdvplot.suggest("Kansas", "ncaa_baseball", n=8))
"""


def _run(seed):
    env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, "-c", SCRIPT], env=env, capture_output=True, text=True, check=True).stdout


def test_listed_values_keep_first_appearance_order_under_any_hash_seed():
    one, two = _run("1"), _run("2")
    assert one == two
    first = one.splitlines()[0]
    assert "'ZZZ9' (unknown), 'AAA9' (unknown), 'MMM9' (unknown), 'QQQ9' (unknown), 'XYZ9'" in first
    assert "skipped 2 point(s) with a missing tier_no or tier_rank: 'QQQ9', 'AAA9'" in one

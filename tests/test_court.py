"""court_coords (the port of sdvplotR's sdv_court_coords): the stats.nba.com legacy shot frame to sportypy's court."""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import pytest

import sdvplot

FIXTURES = Path(__file__).parent / "fixtures"
SHOTS = FIXTURES / "nba_shotchartdetail_2023.csv"  # real stats.nba.com shotchartdetail rows (see the README)


def _shots(**kw):
    return pl.read_csv(SHOTS, schema_overrides={"game_id": pl.Utf8}, **kw)


@pytest.mark.parametrize("lib", [pd, pl])
def test_the_sdvplotr_cases_convert_to_the_sportypy_frame(lib):
    out = sdvplot.court_coords(lib.DataFrame({"x_legacy": [0, -220, 220, 0], "y_legacy": [0.0, 0.0, 0.0, 237.5]}))
    assert type(out) is lib.DataFrame
    assert list(out["court_x"]) == [-41.75, -41.75, -41.75, -18.0]
    assert list(out["court_y"]) == [0.0, -22.0, 22.0, 0.0]


def test_custom_column_names_are_honored():
    out = sdvplot.court_coords(pl.DataFrame({"LOC_X": [-220], "LOC_Y": [0]}), x="LOC_X", y="LOC_Y")
    assert out.row(0, named=True) == {"LOC_X": -220, "LOC_Y": 0, "court_x": -41.75, "court_y": -22.0}


@pytest.mark.parametrize("data", [{"x_legacy": [1], "y_legacy": [2]}, [[1, 2]], pl.Series("x_legacy", [1])])
def test_data_must_be_a_data_frame(data):
    with pytest.raises(TypeError, match="data must be a pandas or polars DataFrame"):
        sdvplot.court_coords(data)


def test_a_lazy_frame_is_not_a_data_frame():
    with pytest.raises(TypeError, match="data must be a pandas or polars DataFrame"):
        sdvplot.court_coords(pl.LazyFrame({"x_legacy": [1], "y_legacy": [2]}))


@pytest.mark.parametrize("bad", [None, ["x_legacy", "y_legacy"], 1])
def test_x_and_y_are_single_column_names(bad):
    df = pl.DataFrame({"x_legacy": [0], "y_legacy": [0]})
    with pytest.raises(TypeError, match="x must be a single column name"):
        sdvplot.court_coords(df, x=bad)
    with pytest.raises(TypeError, match="y must be a single column name"):
        sdvplot.court_coords(df, y=bad)


def test_x_and_y_must_name_different_columns():
    with pytest.raises(ValueError, match="x and y must name different columns, not both 'LOC_X'"):
        sdvplot.court_coords(pl.DataFrame({"LOC_X": [-224], "LOC_Y": [39]}), x="LOC_X", y="LOC_X")


def test_missing_columns_are_named_with_the_stats_api_hint():
    with pytest.raises(ValueError, match=r"data is missing column\(s\) \['y_legacy'\].*x='LOC_X', y='LOC_Y'"):
        sdvplot.court_coords(pl.DataFrame({"x_legacy": [0]}))
    with pytest.raises(ValueError, match=r"missing column\(s\) \['x_legacy', 'y_legacy'\]"):
        sdvplot.court_coords(pd.DataFrame({"a": [1]}))


@pytest.mark.parametrize("lib", [pd, pl])
def test_string_columns_holding_numbers_are_coerced(lib):
    out = sdvplot.court_coords(lib.DataFrame({"x_legacy": ["-224", " 240"], "y_legacy": ["39", "29"]}))
    assert list(out["court_y"]) == [-22.4, 24.0] and list(out["court_x"]) == [-41.75 + 3.9, -41.75 + 2.9]


@pytest.mark.parametrize("bad", ["abc", "", "NA", "NaN"])
def test_strings_that_are_not_numbers_raise_naming_them(bad):
    df = pl.DataFrame({"x_legacy": [bad, "240"], "y_legacy": ["39", "29"]})
    with pytest.raises(ValueError, match=f"column 'x_legacy' has values that are not numbers: \\['{bad}'\\]"):
        sdvplot.court_coords(df)


@pytest.mark.parametrize(
    "column",
    [pl.Series([True, False]), pl.Series(["-224", "240"], dtype=pl.Categorical), pd.Categorical(["-224", "240"])],
    ids=["boolean", "polars categorical", "pandas categorical"],
)
def test_booleans_and_categoricals_are_type_errors(column):
    df = (pl if isinstance(column, pl.Series) else pd).DataFrame({"x_legacy": column, "y_legacy": [39, 29]})
    with pytest.raises(TypeError, match="column 'x_legacy' must be numeric or strings of numbers"):
        sdvplot.court_coords(df)


def test_nulls_stay_null():
    out = sdvplot.court_coords(pl.DataFrame({"x_legacy": [-224, None], "y_legacy": [39, None]}))
    assert out["court_y"].to_list() == [-22.4, None] and out["court_x"].null_count() == 1
    pdf = sdvplot.court_coords(pd.DataFrame({"x_legacy": ["-224", None], "y_legacy": [39.0, float("nan")]}))
    assert pdf["court_y"].iloc[0] == -22.4 and pdf["court_y"].isna().iloc[1] and pdf["court_x"].isna().iloc[1]


@pytest.mark.parametrize(
    "df",
    [pl.DataFrame({"x_legacy": [None, None], "y_legacy": [None, None]}), pd.DataFrame({"x_legacy": [None, None],
                                                                                       "y_legacy": [None, None]})],
    ids=["polars Null", "pandas object"],
)  # fmt: skip
def test_an_all_null_column_gives_null_coordinates(df):
    out = pl.from_pandas(sdvplot.court_coords(df)) if isinstance(df, pd.DataFrame) else sdvplot.court_coords(df)
    assert out.schema["court_x"] == pl.Float64 and out.schema["court_y"] == pl.Float64
    assert out["court_x"].null_count() == 2 and out["court_y"].null_count() == 2


@pytest.mark.parametrize("lib", [pd, pl])
def test_existing_court_columns_are_replaced_in_place_and_others_kept(lib):
    df = lib.DataFrame({"court_x": ["old"], "x_legacy": [-224], "y_legacy": [39], "player": ["p"], "court_y": ["old"]})
    out = sdvplot.court_coords(df)
    assert list(out.columns) == ["court_x", "x_legacy", "y_legacy", "player", "court_y"]
    assert list(out["court_x"]) == [-37.85] and list(out["court_y"]) == [-22.4]
    assert list(out["player"]) == ["p"] and list(df["court_x"]) == ["old"]  # the input is not modified


def test_a_pandas_index_is_kept():
    out = sdvplot.court_coords(pd.DataFrame({"x_legacy": [-224, 240], "y_legacy": [39, 29]}, index=[10, 20]))
    assert list(out.index) == [10, 20] and list(out["court_y"]) == [-22.4, 24.0]


def test_the_sdvplotr_real_row_sign_convention():
    # sdvplotR's pinned rows: game 0022300001 actions 71 (Left Corner 3) and 131 (Right Corner 3)
    out = sdvplot.court_coords(pl.DataFrame({"x_legacy": [-224, 240], "y_legacy": [39, 29]}))
    assert out["court_y"].to_list() == [-22.4, 24.0] and out["court_x"].to_list() == [-37.85, -38.85]


# Real stats.nba.com shotchartdetail rows (2022-23), as committed in tests/fixtures.
@pytest.mark.parametrize("as_strings", [False, True], ids=["typed", "all strings, as stats.nba.com sends them"])
def test_real_corner_threes_and_rim_shots_land_where_the_court_says(as_strings):
    shots = _shots(infer_schema=False) if as_strings else _shots()
    out = sdvplot.court_coords(shots, x="loc_x", y="loc_y")
    zone = out.partition_by("shot_zone_basic", as_dict=True)
    left, right, rim = (zone[(z,)] for z in ("Left Corner 3", "Right Corner 3", "Restricted Area"))
    assert left.height == right.height == 8 and rim.height == 8
    assert left["court_y"].min() == pytest.approx(-24.9) and left["court_y"].max() == pytest.approx(-22.1)
    assert right["court_y"].min() == pytest.approx(22.1) and right["court_y"].max() == pytest.approx(24.8)
    rim_feet = [math.hypot(cx + 41.75, cy) for cx, cy in rim.select("court_x", "court_y").iter_rows()]
    assert max(rim_feet) < 4  # the restricted area is a 4 ft arc around the basket at (-41.75, 0)
    # stats.nba.com's SHOT_DISTANCE is the floor of the distance to the basket: every row puts the basket at
    # (-41.75, 0) in the output frame
    for cx, cy, dist in out.select("court_x", "court_y", "shot_distance").iter_rows():
        assert int(dist) <= math.hypot(cx + 41.75, cy) + 1e-9 < int(dist) + 1


def test_real_rows_match_sdvplotr_exactly():
    ours = sdvplot.court_coords(_shots(), x="loc_x", y="loc_y")
    theirs = pl.read_csv(FIXTURES / "sdvplotr_court_coords.csv", schema_overrides={"game_id": pl.Utf8})
    assert ours.select("game_id", "game_event_id").equals(theirs.select("game_id", "game_event_id"))
    for col in ("court_x", "court_y"):  # bit for bit: the oracle is written at 17 significant digits
        assert ours[col].to_list() == theirs[col].to_list()


def test_the_basket_is_where_sportypy_draws_it():
    pytest.importorskip("sportypy")
    from sportypy.surfaces.basketball import NBACourt

    ring = [f for f in NBACourt()._features if type(f).__name__ == "BasketRing" and f.x_anchor < 0][0]
    pts = ring._translate_feature()
    center = pts["x"].max() - pts["y"].max()  # the ring's far edge less its radius (the near side is the connector)
    basket = sdvplot.court_coords(pl.DataFrame({"x_legacy": [0], "y_legacy": [0]}))
    assert basket["court_x"][0] == pytest.approx(center, abs=0.01) and basket["court_y"][0] == 0


def test_the_real_shots_fall_on_the_half_court_surface_draws():
    pytest.importorskip("sportypy")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    shots = sdvplot.court_coords(_shots(), x="loc_x", y="loc_y").filter(pl.col("shot_zone_basic") != "Backcourt")
    ax = sdvplot.surface("nba", display_range="defense")
    try:
        (x0, x1), (y0, y1) = sorted(ax.get_xlim()), sorted(ax.get_ylim())
        assert x1 <= 0  # the TV-left half
        assert all(x0 <= cx <= x1 and y0 <= cy <= y1 for cx, cy in shots.select("court_x", "court_y").iter_rows())
    finally:
        plt.close(ax.figure)


@pytest.mark.parametrize(
    "df",
    [pl.DataFrame({"x_legacy": pl.Series([None, None], dtype=pl.Boolean), "y_legacy": [39, 29]}),
     pd.DataFrame({"x_legacy": pd.array([None, None], dtype="boolean"), "y_legacy": [39, 29]})],
    ids=["polars Boolean", "pandas boolean"],
)  # fmt: skip
def test_an_all_null_boolean_column_gives_null_coordinates(df):
    # sdvplotR: an all-NA column, "even a logical one", gives NA coordinates (R/arrow exports write such columns)
    out = sdvplot.court_coords(df)
    out = pl.from_pandas(out) if isinstance(out, pd.DataFrame) else out
    assert out.schema["court_y"] == pl.Float64 and out["court_y"].null_count() == 2
    assert out["court_x"].to_list() == [-41.75 + 3.9, -41.75 + 2.9]


@pytest.mark.parametrize("values", [[True, None], [np.True_, "240"]], ids=["bool", "numpy bool"])
def test_booleans_in_an_object_column_are_type_errors(values):
    df = pd.DataFrame({"x_legacy": pd.Series(values, dtype=object), "y_legacy": [39, 29]})
    with pytest.raises(TypeError, match="column 'x_legacy' must be numeric or strings of numbers, not booleans"):
        sdvplot.court_coords(df)


def test_a_string_with_an_underscore_is_not_a_number():
    # Python's float() reads "1_0" as 10; R's as.numeric("1_0") is NA, so sdvplotR names it as not a number
    with pytest.raises(ValueError, match=r"column 'x_legacy' has values that are not numbers: \['1_0'\]"):
        sdvplot.court_coords(pl.DataFrame({"x_legacy": ["1_0", "240"], "y_legacy": ["39", "29"]}))

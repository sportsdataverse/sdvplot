import warnings

import pandas as pd
import polars as pl
import pytest

from sdvplot._errors import SdvplotWarning
from sdvplot._resolve import resolve


def test_polars_series_in_polars_series_out():
    out = resolve(pl.Series("team", ["LV", "LAR"]), "nfl")
    assert isinstance(out, pl.Series) and out.name == "team" and out.to_list() == ["13", "14"]


@pytest.mark.parametrize("dtype", ["object", "category", "string[pyarrow]"])
def test_pandas_series_of_any_string_dtype(dtype):  # Review Focus 5
    out = resolve(pd.Series(["LV", "LAC", "LV"], name="team", dtype=dtype), "nfl")
    assert isinstance(out, pd.Series) and len(out) == 3 and list(out) == ["13", "24", "13"]


def test_nulls_stay_null_and_are_not_reported():  # Review Focus 2
    s = pd.Series(["LV", None, float("nan"), pd.NA], dtype="object")
    with warnings.catch_warnings():
        warnings.simplefilter("error", SdvplotWarning)
        out = resolve(s, "nfl")
    assert out.iloc[0] == "13" and out.iloc[1:].isna().all()


def test_per_row_seasons_from_a_dataframe_column():  # Review Focus 3
    df = pd.DataFrame({"team": ["LA", "LA", "LA"], "season": [1990.0, 2020, "2021"]})
    assert list(resolve(df["team"], "nfl", season=df["season"])) == ["13", "14", "14"]


def test_a_season_that_is_not_a_year_is_a_clear_error():  # Review Focus 3
    with pytest.raises(ValueError, match="season must be a year"):
        resolve("LV", "nfl", season="last year")


def test_season_length_must_match():
    with pytest.raises(ValueError, match="season has 1 values but there are 2 teams"):
        resolve(["LV", "LA"], "nfl", season=[2020])


def test_unsupported_container_is_a_type_error():
    with pytest.raises(TypeError):
        resolve({"LV"}, "nfl")


def test_scalar_pd_na_season_is_treated_as_no_season():
    out = resolve(["LV", "LAC"], "nfl", season=pd.NA)
    assert out == ["13", "24"]


def test_pandas_series_result_preserves_input_index():  # Controller ruling R13
    s = pd.Series(["LV", "LAC"], index=[10, 20], name="team")
    out = resolve(s, "nfl")
    assert out.index.equals(s.index)


def test_result_aligns_on_frame_assignment_with_filtered_index():  # Controller ruling R13
    df = pd.DataFrame(
        {"team": ["LV", "LAC", "LAR"], "other": [1, 2, 3]},
        index=[10, 20, 30],
    )
    filtered = df.iloc[[0, 2]].copy()  # rows at index 10 and 30; a copy, so the assignment is not chained
    resolved = resolve(filtered["team"], "nfl")
    filtered["resolved_id"] = resolved
    assert filtered.loc[10, "resolved_id"] == "13"
    assert filtered.loc[30, "resolved_id"] == "14"

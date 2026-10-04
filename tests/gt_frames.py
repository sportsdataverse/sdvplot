"""One small table as polars and as pandas (non-default index), shared by the great_tables layout tests."""

import pandas as pd
import polars as pl

KINDS = ["polars", "pandas"]


def frame(kind, data):
    """``data`` as a polars frame, or a pandas frame whose index does not start at 0 (catches label/position mixups)."""
    if kind == "polars":
        return pl.DataFrame(data)
    n = len(next(iter(data.values())))
    return pd.DataFrame(data, index=range(100, 100 + n))

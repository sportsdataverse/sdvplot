"""Shared behaviour every adapter must have. Adapter test suites call check_adapter_contract()."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from types import ModuleType
from typing import Any

from sdvplot._errors import SdvplotWarning


def check_adapter_contract(
    adapter: ModuleType, make_target: Callable[[], Any], *, league: str = "nfl", known: tuple[str, str] = ("LV", "LAR")
) -> None:
    """Fail with an AssertionError naming the broken rule if the adapter breaks the sdvplot adapter contract."""
    import pandas as pd
    import polars as pl

    a, b = known
    # 1. known teams each get a mark
    t = make_target()
    adapter.add_logos(t, [0, 1], [0, 1], [a, b], league=league)
    assert adapter.count_marks(t) == 2, "two known teams must produce two marks"
    # 2. an unknown team is skipped with a warning, never a crash
    t = make_target()
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        try:
            adapter.add_logos(t, [0, 1], [0, 1], [a, "XXX"], league=league)
        except Exception as e:  # noqa: BLE001
            raise AssertionError(f"an unknown team must be skipped with a warning, not raise {e!r}") from e
    assert adapter.count_marks(t) == 1, "an unknown team must be skipped"
    assert any(issubclass(w.category, SdvplotWarning) for w in rec), "an unknown team must warn (SdvplotWarning)"
    # 3. pandas and polars inputs behave the same
    tp, tl = make_target(), make_target()
    adapter.add_logos(tp, pd.Series([0, 1]), pd.Series([0, 1]), pd.Series([a, b]), league=league)
    adapter.add_logos(tl, pl.Series([0, 1]), pl.Series([0, 1]), pl.Series([a, b]), league=league)
    assert adapter.count_marks(tp) == adapter.count_marks(tl) == 2, "pandas and polars inputs must behave the same"
    # 4. height is a fraction of the plot height: 0.1 works, 0 is rejected
    adapter.add_logos(make_target(), [0], [0], [a], league=league, height=0.1)
    try:
        adapter.add_logos(make_target(), [0], [0], [a], league=league, height=0)
    except ValueError:
        pass
    else:
        raise AssertionError("height must be a fraction in (0, 1]; height=0 must raise ValueError")

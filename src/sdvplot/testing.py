"""Shared behaviour every adapter must have. Adapter test suites call check_adapter_contract().

An adapter module must expose add_logos(...) and the test hook

    drawn_marks(target) -> list[tuple[str, float, float, float]]

returning one (team_id, x, y, height) tuple per drawn image, in draw order: team_id is the canonical team id
(str), x and y are the caller's position values for that image, and height is the fraction of the plot height the
adapter actually used (not the value it was asked for). The contract can fail: each rule below raises an
AssertionError whose message starts with "rule N".

1. Resolution: the canonical ids of the teams passed, at their own x/y.
2. Warn and skip: an unknown team is dropped together with its own x/y, with an SdvplotWarning, never a raise.
3. pandas/polars parity: a pandas Series with a non-default index draws the same marks as a polars Series.
4. Height semantics: height is the fraction drawn; 0 and values above 1 raise ValueError.
"""

from __future__ import annotations

import math
import warnings
from collections.abc import Callable
from types import ModuleType
from typing import Any

from sdvplot._errors import SdvplotWarning
from sdvplot._resolve import resolve


def _fail(rule: str, msg: str) -> None:
    raise AssertionError(f"{rule}: {msg}")


def _draw(
    adapter: ModuleType, make_target: Callable[[], Any], rule: str, x: Any, y: Any, teams: Any, league: str, **kw: Any
) -> tuple[list[tuple[Any, ...]], list[warnings.WarningMessage]]:
    """Run add_logos on a fresh target; return (drawn marks, warnings). A raise becomes a named AssertionError."""
    t = make_target()
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        try:
            adapter.add_logos(t, x, y, teams, league=league, **kw)
        except Exception as e:  # noqa: BLE001
            raise AssertionError(f"{rule}: add_logos raised {e!r}") from e
    return [tuple(m) for m in adapter.drawn_marks(t)], rec


def check_adapter_contract(
    adapter: ModuleType,
    make_target: Callable[[], Any],
    *,
    league: str = "nfl",
    known: tuple[str, str] = ("LV", "LAR"),
) -> None:
    """Raise an AssertionError naming the broken rule if the adapter breaks the sdvplot adapter contract."""
    import pandas as pd
    import polars as pl

    a, b = known
    id_a, id_b = resolve([a, b], league)
    want_two = [(id_a, 0, 0), (id_b, 1, 1)]

    def xyz(marks: list[tuple[Any, ...]]) -> list[tuple[Any, ...]]:
        return [m[:3] for m in marks]

    # rule 1: each team drawn once, as its canonical id, at its own x/y
    r1 = "rule 1 (resolution)"
    marks, _ = _draw(adapter, make_target, r1, [0, 1], [0, 1], [a, b], league)
    if xyz(marks) != want_two:
        _fail(r1, f"expected marks {want_two}, drew {xyz(marks)}")

    # rule 2: unknown team (placed first) dropped with its own x/y, warns, never raises
    r2 = "rule 2 (unknown team: warn and skip)"
    marks, rec = _draw(adapter, make_target, r2, [0, 1], [0, 1], ["XXX", a], league)
    if xyz(marks) != [(id_a, 1, 1)]:
        _fail(r2, f"an unknown team must be skipped with its own x/y; expected [({id_a!r}, 1, 1)], drew {xyz(marks)}")
    if not any(issubclass(w.category, SdvplotWarning) for w in rec):
        _fail(r2, "an unknown team must warn (SdvplotWarning)")
    marks, rec = _draw(adapter, make_target, r2, [0, 1], [0, 1], ["XXX", "YYY"], league)
    if marks:
        _fail(r2, f"all-unknown input must draw nothing, drew {marks}")
    if not any(issubclass(w.category, SdvplotWarning) for w in rec):
        _fail(r2, "all-unknown input must warn (SdvplotWarning)")

    # rule 3: pandas (non-default index) and polars inputs draw identical marks
    r3 = "rule 3 (pandas/polars parity)"
    pmarks, _ = _draw(
        adapter, make_target, r3,
        pd.Series([0, 1], index=[5, 6]), pd.Series([0, 1], index=[5, 6]), pd.Series([a, b], index=[5, 6]), league,
    )  # fmt: skip
    lmarks, _ = _draw(adapter, make_target, r3, pl.Series([0, 1]), pl.Series([0, 1]), pl.Series([a, b]), league)
    if xyz(pmarks) != xyz(lmarks) or xyz(lmarks) != want_two:
        _fail(r3, f"pandas (index [5, 6]) drew {xyz(pmarks)}, polars drew {xyz(lmarks)}, expected {want_two}")

    # rule 4: height is the fraction drawn; 0 and >1 are rejected
    r4 = "rule 4 (height semantics)"
    for h in (0.1, 0.25):
        marks, _ = _draw(adapter, make_target, r4, [0, 1], [0, 1], [a, b], league, height=h)
        if not marks or not all(math.isclose(m[3], h) for m in marks):
            _fail(r4, f"height={h} must be the height of every drawn mark, drew heights {[m[3] for m in marks]}")
    for bad in (0, 1.5):
        try:
            adapter.add_logos(make_target(), [0], [0], [a], league=league, height=bad)
        except ValueError:
            pass
        else:
            _fail(r4, f"height={bad} must raise ValueError (height is a fraction in (0, 1])")

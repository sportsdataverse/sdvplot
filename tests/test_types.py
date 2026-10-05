"""The Literal aliases match what the runtime accepts, and the overloads give the types they promise.

The ``TYPE_CHECKING`` block never runs: mypy checks it (this file is in ``[tool.mypy] files``), so an overload that
stops narrowing fails ``assert_type``, and a Literal that stops rejecting a typo leaves an unused ``type: ignore``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, get_args

import pytest

from sdvplot import InputError, headshot_url
from sdvplot._colors import _COLUMNS
from sdvplot._marks import MARK_TYPES
from sdvplot._resolve import EXPLICIT_ONLY, PRIORITY
from sdvplot._types import HeadshotIdSystem, IdSystem, MarkType, Which


def test_literals_match_the_runtime_vocabularies() -> None:
    assert get_args(IdSystem) == ("auto", *PRIORITY, *EXPLICIT_ONLY)
    assert get_args(Which) == tuple(_COLUMNS)
    assert get_args(MarkType) == MARK_TYPES


def test_headshot_id_systems_are_the_accepted_ones() -> None:
    for id_system in get_args(HeadshotIdSystem):
        assert headshot_url(None, "nfl", id_system=id_system) is None
    with pytest.raises(InputError):
        headshot_url(None, "nfl", id_system="nflverse")  # type: ignore[arg-type]


if TYPE_CHECKING:
    import altair as alt
    import numpy as np
    import plotly.graph_objects as go
    import polars as pl
    from great_tables import GT
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from plotnine import ggplot
    from typing_extensions import assert_type

    import sdvplot

    def _overloads(
        ax: Axes,
        fig: Figure,
        pfig: go.Figure,
        p: ggplot,
        gt: GT,
        chart: alt.Chart,
        s: pl.Series,
        a: np.ndarray[tuple[int], np.dtype[np.str_]],  # an array type with Any in it matches every overload: Any
    ) -> None:
        # resolve and team_colors: the container in is the container out (pandas ships no types: its overload is
        # only checked where pandas-stubs is installed)
        assert_type(sdvplot.resolve("KC", "nfl"), str | None)
        assert_type(sdvplot.resolve(12, "nfl"), str | None)
        assert_type(sdvplot.resolve(["KC", "SF"], "nfl"), list[str | None])
        assert_type(sdvplot.resolve(("KC", "SF"), "nfl"), list[str | None])
        assert_type(sdvplot.resolve(a, "nfl"), list[str | None])
        assert_type(sdvplot.resolve(s, "nfl"), pl.Series)
        assert_type(sdvplot.team_colors("nfl", "KC"), str | None)
        assert_type(sdvplot.team_colors("nfl", ["KC", "SF"]), list[str | None])
        assert_type(sdvplot.team_colors("nfl", s), pl.Series)

        # the front door returns the target's own type, where the adapter returns the target or one of its type
        assert_type(sdvplot.add_logos(ax, [1], [1], ["KC"], league="nfl"), Axes)
        assert_type(sdvplot.add_wordmarks(fig, [1], [1], ["KC"], league="nfl"), Figure)
        assert_type(sdvplot.add_headshots(pfig, [1], [1], ["3139477"], league="nfl"), go.Figure)
        assert_type(sdvplot.add_logos(p, "x", "y", "team", league="nfl"), ggplot)
        assert_type(sdvplot.add_logos(gt, "team", league="nfl"), GT)
        assert_type(sdvplot.axis_logos(ax, "x", league="nfl"), Axes)
        assert_type(sdvplot.axis_logos(pfig, "x", league="nfl"), go.Figure)
        assert_type(sdvplot.add_logos(chart, "x", "y", "team", league="nfl"), Any)  # a Chart comes back a LayerChart

        # a typo in a closed vocabulary is a type error
        sdvplot.resolve("KC", "nfl", id_system="espnn")  # type: ignore[call-overload]
        sdvplot.marks("KC", "nfl", id_system="espnn")  # type: ignore[arg-type]
        sdvplot.palette("nfl", which="secondry")  # type: ignore[arg-type]
        sdvplot.team_colors("nfl", ["KC"], which="secondry")  # type: ignore[call-overload]
        sdvplot.team_colors("nfl", ["KC"], id_system="espnn")  # type: ignore[call-overload]
        sdvplot.palette("nfl", ["KC"], id_system="espnn")  # type: ignore[arg-type]
        sdvplot.logo_url("KC", "nfl", id_system="espnn")  # type: ignore[arg-type]
        sdvplot.logo_image("KC", "nfl", id_system="espnn")  # type: ignore[arg-type]
        sdvplot.logo_url("KC", "nfl", mark_type="wordmrk")  # type: ignore[arg-type]
        sdvplot.logo_image("KC", "nfl", mark_type="wordmrk")  # type: ignore[arg-type]
        sdvplot.headshot_url("3139477", "nfl", id_system="nflverse")  # type: ignore[arg-type]

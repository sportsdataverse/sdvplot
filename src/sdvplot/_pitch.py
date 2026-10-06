"""Soccer event coordinates from any provider's frame to the pitch surface("soccer") draws: the port of sdvplotR's
sdv_pitch_coords()."""

from __future__ import annotations

import csv
import numbers
from functools import lru_cache
from importlib import resources
from typing import Any

import narwhals as nw
import numpy as np
from numpy.typing import NDArray

from sdvplot._court import _numeric
from sdvplot._errors import InputError

Floats = NDArray[np.float64]

FIXED = ("opta", "wyscout", "statsbomb", "uefa", "impect")
PHYSICAL = ("tracab", "skillcorner", "secondspectrum", "metrica")
ALIASES = {"statsperform": "opta"}
PROVIDERS = (*FIXED, "espn", *PHYSICAL, *ALIASES)


@lru_cache(maxsize=1)
def _table() -> dict[tuple[str, str], tuple[float, ...]]:
    """The shared landmark table (byte-identical to sdvplotR's inst/extdata/pitch_landmarks.csv): x from the defended
    goal line to the attacked one, y from the attacker's right touchline to the left one."""
    text = resources.files("sdvplot").joinpath("data", "pitch_landmarks.csv").read_text(encoding="utf-8")
    rows: dict[tuple[str, str], list[tuple[int, float]]] = {}
    for r in csv.DictReader(line for line in text.splitlines() if not line.startswith("#")):
        rows.setdefault((r["provider"], r["axis"]), []).append((int(r["i"]), float(r["value"])))
    return {k: tuple(v for _, v in sorted(vals)) for k, vals in rows.items()}


def _physical(provider: str, length: float, width: float) -> tuple[Floats, Floats]:
    """A tracking provider's landmarks on the venue's ``length`` x ``width`` m pitch, in its own units: the Laws of the
    Game's fixed distances (six-yard line 5.5 m, spot 11 m, box 16.5 m deep; goal 7.32 m, six-yard box 18.32 m and box
    40.32 m wide). The same arithmetic as sdvplotR's physical_landmarks()."""
    along = np.array([0, 5.5, 11, 16.5, length / 2, length - 16.5, length - 11, length - 5.5, length], dtype=float)
    half = width / 2
    across = np.array(
        [0, half - 20.16, half - 9.16, half - 3.66, half + 3.66, half + 9.16, half + 20.16, width], dtype=float
    )
    if provider == "tracab":
        return (along - length / 2) * 100, (across - half) * 100
    if provider == "metrica":
        return along / length, 1 - across / width
    return along - length / 2, across - half


def _landmarks(provider: str, dims: tuple[float, float] | None) -> tuple[Floats, Floats]:
    """The x and y landmarks of ``provider`` (a canonical key); ``dims`` = (length, width) for tracking providers."""
    if provider in PHYSICAL:
        if dims is None:
            raise ValueError(f"{provider!r} needs the pitch's length and width")
        return _physical(provider, *dims)
    t = _table()
    return np.array(t[(provider, "x")], dtype=float), np.array(t[(provider, "y")], dtype=float)


def _interp(v: Floats, src: Floats, dst: Floats) -> Floats:
    """Piecewise-linear from ``src`` landmarks to ``dst``, extending the end segments beyond both ends (numpy.interp
    would clamp). The same index (findInterval's) and the same arithmetic as sdvplotR's interp_landmarks(), so the two
    packages agree to the last bit; NaN stays NaN."""
    order = np.argsort(src, kind="stable")
    src, dst = src[order], dst[order]
    j = np.clip(np.searchsorted(src, v, side="right") - 1, 0, len(src) - 2)
    out: Floats = dst[j] + (dst[j + 1] - dst[j]) * ((v - src[j]) / (src[j + 1] - src[j]))
    return out


def _provider(provider: Any) -> str:
    """The canonical key for ``provider`` (case ignored, aliases resolved)."""
    if not isinstance(provider, str):
        raise TypeError(f"provider must be a string such as 'opta', got {type(provider).__name__}")
    key = provider.lower()
    if key not in PROVIDERS:
        raise InputError(f"provider must be one of {list(PROVIDERS)}, got {provider!r}")
    return ALIASES.get(key, key)


def _size(value: Any, arg: str, lo: float, hi: float) -> float:
    """One number of meters within the Laws of the Game's range (bool is not a number here; NaN fails the range)."""
    if isinstance(value, bool) or not isinstance(value, numbers.Real) or not lo <= float(value) <= hi:
        raise InputError(
            f"{arg} must be one number of meters from {lo:g} to {hi:g} (the Laws of the Game), not {value!r}"
        )
    return float(value)


def _dims(key: str, pitch_length: Any, pitch_width: Any) -> tuple[float, float] | None:
    if key not in PHYSICAL:
        if pitch_length is not None or pitch_width is not None:
            raise InputError(
                f"pitch_length and pitch_width only apply to tracking providers {list(PHYSICAL)}; {key!r} has a "
                "fixed frame"
            )
        return None
    if pitch_length is None or pitch_width is None:
        raise InputError(
            f"{key!r} needs pitch_length and pitch_width: the venue's size in meters (a regulation international "
            "pitch is 105 x 68)"
        )
    return _size(pitch_length, "pitch_length", 90, 120), _size(pitch_width, "pitch_width", 45, 90)


def _flip(flip: Any, frame: Any) -> NDArray[np.bool_]:
    n = len(frame)
    if flip is None:
        return np.zeros(n, dtype=bool)
    if isinstance(flip, (bool, np.bool_)):
        return np.full(n, bool(flip))
    if isinstance(flip, str):
        if flip not in frame.columns:
            raise InputError(f"flip names column {flip!r}, which data does not have")
        s = frame[flip]
        if s.dtype != nw.Boolean or s.null_count():
            raise InputError(
                f"column {flip!r} must be True/False with no missing values: it says which rows attack the other way"
            )
        return np.array(s.to_list(), dtype=bool)
    raise TypeError(f"flip must be None, True/False, or the name of a boolean column, got {type(flip).__name__}")


def _floats(series: Any) -> Floats:
    """A narwhals Float64 Series as numpy floats, nulls as NaN."""

    out: Floats = series.fill_null(float("nan")).to_numpy().astype(float)
    return out


def pitch_coords(
    data: Any,
    *,
    provider: str,
    x: str | None = None,
    y: str | None = None,
    flip: bool | str | None = None,
    pitch_length: float | None = None,
    pitch_width: float | None = None,
) -> Any:
    """Convert soccer event coordinates from any provider's frame to the pitch ``surface("soccer")`` draws.

    Opta and Wyscout run 0-100 on both axes and are not to scale, StatsBomb uses 120 x 80, tracking providers use
    meters or centimeters from the center spot, and ESPN reports the distance from the attacked goal as a fraction of
    half the pitch. This converts any of them to one frame: meters, origin at the center spot, a regulation 105 x 68 m
    pitch, attacking toward +x, with +y on the attacker's left. The conversion is piecewise-linear between pitch
    landmarks (goal line, six-yard line, penalty spot, box edge and halfway line along the pitch; touchline, box side,
    six-yard side and post across it), so a shot on the edge of an Opta box lands on the edge of the regulation box;
    points beyond the outermost landmark are extrapolated, not clamped. The landmarks come from mplsoccer and ship in
    ``sdvplot/data/pitch_landmarks.csv``, byte-identical to sdvplotR's.

    ESPN's frame is derived from Opta's (``opta_x = 100 - 50 * x``, ``opta_y = 100 * (1 - y)``), and ESPN's ``(0, 0)``
    "no location" becomes null. Event providers record every action as if the team attacked left to right; ``flip``
    turns rows half a turn (``pitch_x`` and ``pitch_y`` both change sign) so two teams attack opposite ends with each
    wing on its own side.

    Args:
        data: A pandas or polars DataFrame of events.
        provider: The frame of ``data``: "opta" (alias "statsperform"), "wyscout", "statsbomb", "uefa", "impect",
            "espn", "tracab" (cm), "skillcorner", "secondspectrum" (m) or "metrica" (0-1). Case is ignored.
        x: The x column; None uses the provider's usual name ("field_position_x" for ESPN, as sportsdataverse-py's
            ``espn_soccer_game_plays`` returns it; "x" otherwise).
        y: The y column; None uses "field_position_y" for ESPN, "y" otherwise.
        flip: None (no row flipped), True/False for every row, or the name of a boolean column with no missing values.
        pitch_length: The venue's length in meters (90-120), for tracking providers only.
        pitch_width: The venue's width in meters (45-90), for tracking providers only.

    Returns:
        DataFrame: ``data``'s type, with ``pitch_x`` (meters along the pitch: -52.5 is the defended goal line, 52.5
        the attacked one) and ``pitch_y`` (meters across: -34 to 34, positive = the attacker's left) added as Float64;
        existing columns of those names are replaced in place, every other column is kept. Nulls stay null.

    Raises:
        TypeError: If ``data`` is not a pandas/polars DataFrame, ``provider`` is not a string, ``x``/``y`` is not a
            string, ``flip`` has the wrong type, or a coordinate column is boolean or another non-numeric type.
        InputError: If ``provider`` is unknown, ``pitch_length``/``pitch_width`` are given to a fixed-frame provider,
            missing for a tracking one or out of range, ``x`` and ``y`` name the same column, a column is missing, a
            string is not a number, or the ``flip`` column is not boolean or has missing values.

    Example:
        ::

            import polars as pl
            import sdvplot

            shots = pl.DataFrame({"x": [88.5, 83, 50], "y": [50.0, 21.1, 100.0], "away": [False, True, False]})
            out = sdvplot.pitch_coords(shots, provider="opta", flip="away")
            out["pitch_x"].to_list()   # [41.5, -36.0, 0.0]: the spot, the far box edge, halfway

            ax = sdvplot.surface("soccer")
            ax.scatter(out["pitch_x"], out["pitch_y"], zorder=20)

    See Also:
        sdvplotR sdv_pitch_coords(): https://sdvplotR.sportsdataverse.org/ ;
        mplsoccer Standardizer: https://mplsoccer.readthedocs.io/ ;
        ggsoccer rescale_coordinates(): https://github.com/Torvaney/ggsoccer
    """
    try:
        frame = nw.from_native(data, eager_only=True)
    except TypeError:
        raise TypeError(f"data must be a pandas or polars DataFrame, got {type(data).__name__}") from None
    key = _provider(provider)
    dims = _dims(key, pitch_length, pitch_width)
    espn = key == "espn"
    x = ("field_position_x" if espn else "x") if x is None else x
    y = ("field_position_y" if espn else "y") if y is None else y
    for arg, column in (("x", x), ("y", y)):
        if not isinstance(column, str):
            raise TypeError(f"{arg} must be a single column name (a string), got {column!r}")
    if x == y:
        raise InputError(f"x and y must name different columns, not both {x!r}")
    missing = [c for c in (x, y) if c not in frame.columns]
    if missing:
        raise InputError(f"data is missing column(s) {missing}; name the coordinate columns with x=/y=")
    xs, ys = _floats(_numeric(frame, x)), _floats(_numeric(frame, y))
    rotate = _flip(flip, frame)
    if espn:
        none = (xs == 0) & (ys == 0)  # ESPN's "no location"
        xs, ys = 100 - 50 * xs, 100 * (1 - ys)
        xs[none] = ys[none] = np.nan
        key = "opta"
    mx, my = _landmarks(key, dims)
    tx, ty = _landmarks("impect", None)
    px, py = _interp(xs, mx, tx), _interp(ys, my, ty)
    px[rotate], py[rotate] = -px[rotate] + 0.0, -py[rotate] + 0.0  # + 0.0: no -0.0
    backend = nw.get_native_namespace(frame)

    def as_series(name: str, values: Floats) -> Any:
        nan = np.isnan(values)  # NaN back to null (pandas keeps NaN as its missing value)
        out = values.astype(object)
        out[nan] = None
        return nw.new_series(name, out.tolist(), nw.Float64(), backend=backend)

    return frame.with_columns(pitch_x=as_series("pitch_x", px), pitch_y=as_series("pitch_y", py)).to_native()

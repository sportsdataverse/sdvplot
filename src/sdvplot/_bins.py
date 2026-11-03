"""Hexagonal and square binning of x/y points: the port of sdvplot-js ``@sportsdataverse/sdvplot/bins``.

``hexbin`` is d3-hexbin 0.2.2's lattice (as sdvplot-js ports it), ``squarebin`` its square twin; ``binner`` picks
either from one set of options. Every bin is a ``Bin``: its centre, the input rows it holds (first-seen order) and their
link ids, plus its own id ``"x,y"``, which is the ``data-sdv-id`` sdvplot-js stamps on a drawn cell. Pure Python, so it
imports nothing heavy; ``tests/test_bins.py`` checks it against sdvplot-js's own output on 2000 real shots.
"""

from __future__ import annotations

import math
import numbers
from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from sdvplot._errors import InputError
from sdvplot._types import BinShape

SHAPES: tuple[str, ...] = ("hex", "square")
_THIRD_PI = math.pi / 3
_ANGLES = [0.0, _THIRD_PI, 2 * _THIRD_PI, 3 * _THIRD_PI, 4 * _THIRD_PI, 5 * _THIRD_PI]  # sdvplot-js hexbin.ts:6
_EQUAL_AREA = math.sqrt(1.5 * math.sqrt(3))  # a hexagon of circumradius r has the area of a square of side r * this


def _js_round(v: float) -> int:
    """JavaScript's ``Math.round``: the nearest integer, halves toward +infinity (Python's ``round`` goes to even)."""
    f = math.floor(v)
    return f + 1 if v - f >= 0.5 else f


def _js_str(v: float) -> str:
    """JavaScript's ``String(number)`` for a finite number: a bin id is byte-identical to sdvplot-js's ``${x},${y}``."""
    if v == 0:
        return "0"
    sign, digits, exp = Decimal(repr(float(v))).normalize().as_tuple()
    s = "".join(map(str, digits))
    k, n = len(s), len(s) + int(exp)  # ECMA-262 Number::toString: k digits, decimal point after the n-th
    if k <= n <= 21:
        out = s + "0" * (n - k)
    elif 0 < n <= 21:
        out = s[:n] + "." + s[n:]
    elif -6 < n <= 0:
        out = "0." + "0" * -n + s
    else:
        e = f"{'+' if n - 1 >= 0 else '-'}{abs(n - 1)}"
        out = (s if k == 1 else s[0] + "." + s[1:]) + "e" + e
    return ("-" if sign else "") + out


def _missing(v: Any) -> bool:
    """None, NaN or pandas' NA (any value that is not equal to itself, or NA's own type), without importing pandas."""
    if v is None:
        return True
    try:
        return bool(v != v)
    except TypeError:  # pandas.NA: its comparisons are NA, and bool(NA) raises
        return True


def _to_id(v: Any) -> str:
    """sdvplot-js ``toId``: JavaScript's ``String(v)``, or ``""`` (never matched) for None, NaN, NA and ``""``."""
    if _missing(v) or (isinstance(v, str) and v == ""):
        return ""
    if isinstance(v, bool) or type(v).__name__ == "bool_":  # Python and numpy booleans: JS writes true / false
        return "true" if v else "false"
    if isinstance(v, numbers.Integral):
        return str(int(v))
    if isinstance(v, numbers.Real):  # float, numpy float32 / float64: JS's shortest form ("2", not "2.0")
        return _js_str(float(v))
    return str(v)


def _positive(name: str, v: Any) -> float:
    if isinstance(v, bool) or not isinstance(v, numbers.Real) or not (math.isfinite(v) and float(v) > 0):
        raise InputError(f"{name} must be a finite number > 0, got {v!r}")
    return float(v)


@dataclass(frozen=True)
class Bin:
    """One cell with points in it: sdvplot-js's ``BinOf`` with the points as row numbers.

    Attributes:
        id: ``"x,y"``, the centre as JavaScript prints it: the ``data-sdv-id`` sdvplot-js stamps on the cell.
        x: The centre's x, in the points' units (``-0`` folded to ``0``).
        y: The centre's y.
        rows: The 0-based positions in ``x``/``y`` of the points in this cell, in input order.
        ids: The link id of each of those points: ``ids[row]`` as a string, or the row number when no ids were given.
    """

    id: str
    x: float
    y: float
    rows: tuple[int, ...]
    ids: tuple[str, ...]

    @property
    def count(self) -> int:
        """The number of points in the cell."""
        return len(self.rows)


@dataclass(frozen=True)
class Binner:
    """One lattice, either shape: what ``binner`` returns (sdvplot-js's ``Binner``).

    Attributes:
        shape: ``"hex"`` or ``"square"``.
        size: The cell size in the points' units: the hexagon's circumradius, or the square's side.
        lattice: The resolved options, ``{"radius": r}`` or ``{"shape": "square", "side": s}``: ``equal_area`` resolved
            to the side, so storing it reproduces the same cells.
    """

    shape: BinShape
    size: float
    lattice: dict[str, Any] = field(compare=False)

    def bins(self, x: Sequence[Any], y: Sequence[Any], *, ids: Sequence[Any] | None = None) -> list[Bin]:
        """Bin points on this lattice (``hexbin`` or ``squarebin``); see those for the rules."""
        return _bin(self.shape, self.size, x, y, ids)

    def cell_points(self, size: float | None = None) -> list[tuple[float, float]]:
        """The cell's vertices around (0, 0) at ``size`` (default this lattice's), as ``cell_points``."""
        return cell_points(self.shape, self.size if size is None else size)


def _bin(shape: str, size: float, x: Sequence[Any], y: Sequence[Any], ids: Sequence[Any] | None) -> list[Bin]:
    n = len(x)
    if len(y) != n:
        raise ValueError(f"x and y must have the same length, got {n} and {len(y)}")
    if ids is not None and len(ids) != n:
        raise ValueError(f"ids must have one value per point ({n}), got {len(ids)}")
    if ids is not None:
        ids = list(ids)  # by position: a pandas Series indexes by label, so a filtered or reordered one misnames points
    if shape == "hex":
        dx, dy = size * 2 * math.sin(_THIRD_PI), size * 1.5
    keys: dict[tuple[int, int], int] = {}
    centres: list[tuple[float, float]] = []
    members: list[list[int]] = []
    for row, (vx, vy) in enumerate(zip(x, y, strict=True)):
        if _missing(vx) or _missing(vy):
            continue
        px, py = float(vx), float(vy)
        if not (math.isfinite(px) and math.isfinite(py)):  # sdvplot-js skips NaN; an infinity has no cell either
            continue
        if shape == "hex":  # sdvplot-js hexbin.ts, itself d3-hexbin src/hexbin.js:23-50, step for step
            py = py / dy
            pj = _js_round(py)
            px = px / dx - (pj & 1) / 2
            pi: float = _js_round(px)
            py1 = py - pj
            if abs(py1) * 3 > 1:
                px1 = px - pi
                pi2 = pi + (-1 if px < pi else 1) / 2
                pj2 = pj + (-1 if py < pj else 1)
                px2 = px - pi2
                py2 = py - pj2
                if px1 * px1 + py1 * py1 > px2 * px2 + py2 * py2:
                    pi = pi2 + (1 if pj & 1 else -1) / 2
                    pj = pj2
            key = (int(pi), pj)
            centre = ((pi + (pj & 1) / 2) * dx + 0.0, pj * dy + 0.0)  # + 0.0 folds -0, as `|| 0` does
        else:  # sdvplot-js squarebin.ts: half-open cells, an edge point goes to the higher cell
            i, j = _js_round(px / size), _js_round(py / size)
            key = (i, j)
            centre = (i * size + 0.0, j * size + 0.0)
        at = keys.get(key)
        if at is None:
            at = keys[key] = len(members)
            centres.append(centre)
            members.append([])
        members[at].append(row)
    return [
        Bin(
            id=f"{_js_str(cx)},{_js_str(cy)}",
            x=cx,
            y=cy,
            rows=tuple(rows),
            ids=tuple(str(r) if ids is None else _to_id(ids[r]) for r in rows),
        )
        for (cx, cy), rows in zip(centres, members, strict=True)
    ]


def hexbin(x: Sequence[Any], y: Sequence[Any], *, radius: float, ids: Sequence[Any] | None = None) -> list[Bin]:
    """Bin points into pointy-top hexagons of circumradius ``radius``, in the points' own units.

    The port of sdvplot-js ``hexbin`` (itself d3-hexbin 0.2.2's): the same lattice, centres and bin order. Each point
    goes to the centre d3-hexbin picks, which is close to but not exactly the nearest: it compares two candidates in
    lattice units, so about 1-2% of points sit just outside the hexagon drawn for their bin (22 of 2000 real Brooklyn
    shots at radius 10). That is faithful to d3-hexbin and sdvplot-js; squares contain every point they bin.

    Args:
        x: The points' x values (a list, numpy array, or pandas / polars Series).
        y: The points' y values, one per x.
        radius: The hexagon's circumradius, in the points' units (a finite number > 0).
        ids: Optional link ids, one per point (e.g. a shot id column); each becomes a string, as sdvplot-js's
            ``toId`` (``None``, NaN and ``""`` become ``""``). Default: the row number.

    Returns:
        list[Bin]: The non-empty cells in first-seen order, each with ``id`` (``"x,y"``, the centre as JavaScript
        prints it), ``x``, ``y`` (``-0`` folded to ``0``), ``rows`` (the points' 0-based positions), ``ids`` and
        ``count``. A point with a missing (None), NaN or infinite coordinate is in no bin.

    Raises:
        InputError: If ``radius`` is not a finite number greater than 0.
        ValueError: If ``x``, ``y`` and ``ids`` differ in length, or a coordinate is not a number.

    Example:
        ::

            import sdvplot

            # three Brooklyn shots of 2025-26 in tenths of a foot from the hoop (sportsdataverse-data
            # nba_stats_shots): the two at the rim share a 1 ft hexagon
            bins = sdvplot.hexbin([0, -1, -44], [0, 7, 252], radius=10)
            [(b.id, b.count) for b in bins]   # [('0,0', 2), ('-43.301270189221924,255', 1)]

    See Also:
        binner: https://sdvplot.sportsdataverse.org/docs/reference/binner ;
        sdvplot-js hexbin: https://sdvplot-js.sportsdataverse.org/
    """
    return _bin("hex", _positive("hexbin radius", radius), x, y, ids)


def squarebin(x: Sequence[Any], y: Sequence[Any], *, side: float, ids: Sequence[Any] | None = None) -> list[Bin]:
    """Bin points into axis-aligned squares of side ``side``, in the points' own units.

    The port of sdvplot-js ``squarebin``. As in d3-hexbin's lattice a cell is centred on the origin, so centres are
    ``(i * side, j * side)``. Cells are half-open, ``[c - side/2, c + side/2)`` on each axis: a point exactly on an edge
    goes to the higher cell, because the cell index is JavaScript's ``Math.round(x / side)`` (halves round up, also
    below zero: -5 with side 10 is in the cell at 0).

    Args:
        x: The points' x values (a list, numpy array, or pandas / polars Series).
        y: The points' y values, one per x.
        side: The square's side, in the points' units (a finite number > 0).
        ids: Optional link ids, one per point; as in ``hexbin``. Default: the row number.

    Returns:
        list[Bin]: The non-empty cells in first-seen order, as ``hexbin`` returns them.

    Raises:
        InputError: If ``side`` is not a finite number greater than 0.
        ValueError: If ``x``, ``y`` and ``ids`` differ in length, or a coordinate is not a number.

    Example:
        ::

            import sdvplot

            # x = 5 sits on a cell edge and goes to the higher cell
            bins = sdvplot.squarebin([0, -1, 5], [0, 7, 91], side=10)
            [(b.x, b.y, b.count) for b in bins]   # [(0.0, 0.0, 1), (0.0, 10.0, 1), (10.0, 90.0, 1)]

    See Also:
        binner: https://sdvplot.sportsdataverse.org/docs/reference/binner ;
        sdvplot-js squarebin: https://sdvplot-js.sportsdataverse.org/
    """
    return _bin("square", _positive("squarebin side", side), x, y, ids)


def binner(
    *, shape: BinShape = "hex", radius: float | None = None, side: float | None = None, equal_area: bool = False
) -> Binner:
    """One binning API for both lattices, the port of sdvplot-js ``binner``.

    ``binner(radius=15)`` is d3-hexbin's lattice, ``binner(shape="square", side=15)`` squares, and
    ``binner(shape="square", radius=15, equal_area=True)`` squares of side ``15 * sqrt(3 * sqrt(3) / 2)`` (about 24.18),
    each the area of a radius-15 hexagon, so a hex and a square chart of the same data compare cell for cell.

    Args:
        shape: ``"hex"`` (the default) or ``"square"``.
        radius: The hexagon's circumradius; with ``shape="square"`` only together with ``equal_area=True``.
        side: The square's side (``shape="square"`` only).
        equal_area: With ``shape="square"`` and ``radius``: squares of the area of that hexagon.

    Returns:
        Binner: ``shape``, ``size`` (the circumradius, or the side), ``lattice`` (the resolved options:
        ``{"radius": r}`` or ``{"shape": "square", "side": s}``), ``bins(x, y, *, ids=None)`` (as ``hexbin`` /
        ``squarebin``) and ``cell_points(size=None)``.

    Raises:
        InputError: If ``shape`` is not ``"hex"`` or ``"square"``, the size is missing or not a finite number > 0,
            or the options do not name one lattice (a hexagon with ``side``, a square with both ``side`` and
            ``radius``, or ``radius`` without ``equal_area=True``).

    Example:
        ::

            import sdvplot

            b = sdvplot.binner(shape="square", radius=10, equal_area=True)
            b.size   # 16.11854897735313: the side of a square with a radius-10 hexagon's area
            [(c.id, c.count) for c in b.bins([0, -1, -44], [0, 7, 252])]

    See Also:
        hexbin: https://sdvplot.sportsdataverse.org/docs/reference/hexbin ;
        squarebin: https://sdvplot.sportsdataverse.org/docs/reference/squarebin
    """
    if shape not in SHAPES:
        raise InputError(f'binner shape must be "hex" or "square", got {shape!r}')
    if shape == "hex":
        if side is not None or equal_area:
            raise InputError("binner hex takes radius only (side and equal_area are for shape='square')")
        r = _positive("binner radius", radius)
        return Binner("hex", r, {"radius": r})
    if side is not None and radius is not None:
        raise InputError("binner square takes side, or radius with equal_area=True, not both")
    if side is None and not (radius is not None and equal_area):
        raise InputError("binner square needs side, or radius with equal_area=True")
    s = _positive("binner side", side) if side is not None else _positive("binner radius", radius) * _EQUAL_AREA
    if not math.isfinite(s):  # a huge radius times sqrt(3 * sqrt(3) / 2) overflows to infinity
        raise InputError(f"binner radius {radius!r} gives an equal-area side that is not finite")
    return Binner("square", s, {"shape": "square", "side": s})


def cell_points(shape: BinShape, size: float) -> list[tuple[float, float]]:
    """A cell's vertices around (0, 0), in the points' units, to outline a bin as a polygon.

    A pointy-top hexagon of circumradius ``size`` (d3-hexbin's vertex order, starting at the top in a y-down frame) or a
    square of side ``size``, the port of sdvplot-js ``cellPoints``. Add a bin's centre to each vertex.

    Args:
        shape: ``"hex"`` or ``"square"``.
        size: The hexagon's circumradius or the square's side (a finite number > 0).

    Returns:
        list[tuple[float, float]]: Six vertices for a hexagon, four for a square.

    Raises:
        InputError: If ``shape`` is not ``"hex"`` or ``"square"``, or ``size`` is not a finite number > 0.

    Example:
        ::

            import sdvplot

            sdvplot.cell_points("square", 10)   # [(-5.0, -5.0), (5.0, -5.0), (5.0, 5.0), (-5.0, 5.0)]
            b = sdvplot.hexbin([0, -1, -44], [0, 7, 252], radius=10)[0]
            [(b.x + dx, b.y + dy) for dx, dy in sdvplot.cell_points("hex", 10)]

    See Also:
        binner: https://sdvplot.sportsdataverse.org/docs/reference/binner
    """
    if shape not in SHAPES:
        raise InputError(f'cell_points shape must be "hex" or "square", got {shape!r}')
    s = _positive("cell_points size", size)
    if shape == "square":
        h = s / 2
        return [(-h, -h), (h, -h), (h, h), (-h, h)]
    return [(math.sin(a) * s, -math.cos(a) * s) for a in _ANGLES]


def bin_ids(bins: Sequence[Bin], n: int) -> list[str]:
    """Each point's bin id: the column that links a point layer or a table row to the cell it is drawn in.

    Every binned point is in exactly one bin, so this is the join key both ways: a selected cell's ``id`` picks its
    rows (the rows whose bin id is that id), and a selected row picks its cell.

    Args:
        bins: What ``hexbin``, ``squarebin``, ``binner(...).bins`` or an adapter's ``add_bins`` binned.
        n: The number of points that were binned (``len(x)``).

    Returns:
        list[str]: ``n`` strings: the ``id`` of the bin holding each row, or ``""`` for a row in no bin (a missing,
        NaN or infinite coordinate).

    Raises:
        ValueError: If a bin holds a row outside ``range(n)``.

    Example:
        ::

            import polars as pl
            import sdvplot

            shots = pl.DataFrame({"x": [0, -1, -44], "y": [0, 7, 252]})
            bins = sdvplot.hexbin(shots["x"], shots["y"], radius=10)
            shots.with_columns(bin_id=pl.Series(sdvplot.bin_ids(bins, shots.height)))

    See Also:
        hexbin: https://sdvplot.sportsdataverse.org/docs/reference/hexbin
    """
    out = [""] * n
    for b in bins:
        for r in b.rows:
            if not 0 <= r < n:
                raise ValueError(f"bin {b.id!r} holds row {r}, outside the {n} points")
            out[r] = b.id
    return out


def _cells(
    x: Sequence[Any],
    y: Sequence[Any],
    *,
    shape: BinShape,
    radius: float | None,
    side: float | None,
    equal_area: bool,
    ids: Sequence[Any] | None,
) -> tuple[list[Bin], list[list[tuple[float, float]]]]:
    """What every adapter's ``add_bins`` draws: the bins and each one's polygon (its vertices, in data units)."""
    b = binner(shape=shape, radius=radius, side=side, equal_area=equal_area)
    bins = b.bins(x, y, ids=ids)
    corners = b.cell_points()
    return bins, [[(c.x + dx, c.y + dy) for dx, dy in corners] for c in bins]

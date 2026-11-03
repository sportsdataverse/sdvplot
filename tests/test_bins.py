"""Hex and square bins: parity with sdvplot-js on 2000 real shots, and each adapter's add_bins and its linking."""

import json
import math
from pathlib import Path

import pytest

import sdvplot
from sdvplot import InputError, UnsupportedTargetError
from sdvplot._bins import FILL

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "sdvplotjs_bins_bkn_2000.json").read_text())
X, Y = FIXTURE["x_legacy"], FIXTURE["y_legacy"]


def _binner(options):
    """sdvplot-js binner options as sdvplot.binner keywords."""
    kw = {"shape": options.get("shape", "hex")}
    for js, py in (("radius", "radius"), ("side", "side"), ("equalArea", "equal_area")):
        if js in options:
            kw[py] = options[js]
    return sdvplot.binner(**kw)


@pytest.mark.parametrize("lattice", FIXTURE["lattices"], ids=lambda la: json.dumps(la["options"]))
def test_bins_equal_sdvplot_js_on_real_shots(lattice):
    b = _binner(lattice["options"])
    assert (b.shape, b.size, b.lattice) == (lattice["shape"], lattice["size"], lattice["lattice"])
    bins = b.bins(X, Y)
    # same cells, same first-seen order, same centres to the bit, same points in the same order, same ids
    assert [[c.x, c.y, list(c.rows)] for c in bins] == lattice["bins"]
    assert [c.id for c in bins] == lattice["ids"]
    assert sum(c.count for c in bins) == len(X)


@pytest.mark.parametrize(
    ("kwargs", "first_ids"),
    [  # the data-sdv-id sdvplot-js stamps on the first three cells of the 2000 real shots (Node 24, sdvplot-js fffc941)
        ({"radius": 10}, ["-225.16660498395402,0", "233.8268590217984,-15", "121.2435565298214,0"]),
        ({"shape": "square", "side": 10}, ["-230,0", "230,-10", "110,0"]),
        (
            {"shape": "square", "radius": 10, "equal_area": True},
            ["-225.6596856829438,0", "241.77823466029693,-16.11854897735313", "112.8298428414719,0"],
        ),
    ],
)
def test_ids_are_sdvplot_js_data_sdv_ids(kwargs, first_ids):
    # JavaScript's String(number): no trailing ".0", JS exponent rules; also what sdvplotR's port writes
    assert [c.id for c in sdvplot.binner(**kwargs).bins(X, Y)[:3]] == first_ids


@pytest.mark.parametrize("result", FIXTURE["edge"]["results"], ids=["hex", "square"])
def test_edge_cases_equal_sdvplot_js(result):
    # -0 folds into the 0 cell, a NaN coordinate is skipped, halves round toward +infinity (-5 with side 10 is at 0)
    xs, ys = ([math.nan if v is None else v for v in col] for col in zip(*FIXTURE["edge"]["points"], strict=True))
    bins = sdvplot.hexbin(xs, ys, radius=10) if "radius" in result["options"] else sdvplot.squarebin(xs, ys, side=10)
    assert [[c.x, c.y, list(c.rows)] for c in bins] == result["bins"]
    assert [c.id for c in bins] == result["ids"]
    assert all(math.copysign(1, c.x) == 1 and math.copysign(1, c.y) == 1 for c in bins if c.x == 0 or c.y == 0)


def test_cell_points_equal_sdvplot_js():
    # hexagon corners come from sin / cos, which differ in the last bit between libms (glibc, macOS, UCRT, V8):
    # equal to sdvplot-js's within 1e-12, not byte for byte (ids and centres use only sqrt and are exact)
    for shape, key in (("hex", "hex10"), ("square", "square10")):
        got = [list(p) for p in sdvplot.cell_points(shape, 10)]
        want = FIXTURE["cells"][key]
        assert len(got) == len(want)
        assert all(g == pytest.approx(w, abs=1e-12) for g, w in zip(got, want, strict=True)), shape


def test_the_documented_hexbin_quirk_holds_on_the_real_shots():
    # sdvplot-js hexbin.ts: 22 of the 2000 shots at radius 10 sit just outside their drawn hexagon; squares hold all
    def inside_hex(px, py, c, r):
        dx, dy = abs(px - c.x), abs(py - c.y)
        w = r * math.sqrt(3) / 2
        return dx <= w + 1e-9 and dy <= r - dx / math.sqrt(3) + 1e-9

    out = sum(not inside_hex(X[i], Y[i], c, 10) for c in sdvplot.hexbin(X, Y, radius=10) for i in c.rows)
    assert out == 22
    for c in sdvplot.squarebin(X, Y, side=15):
        assert all(c.x - 7.5 <= X[i] < c.x + 7.5 and c.y - 7.5 <= Y[i] < c.y + 7.5 for i in c.rows)


def test_ids_are_link_strings_and_bin_ids_is_the_join_key():
    ids = FIXTURE["game_id"]  # the release's 10-character string game ids
    bins = sdvplot.hexbin(X, Y, radius=15, ids=ids)
    assert all(c.ids == tuple(ids[r] for r in c.rows) for c in bins)
    assert sdvplot.hexbin([1, 2], [1, 2], radius=1)[0].ids == ("0",)  # default: the row number
    assert sdvplot.squarebin([0, 0, 0, 0], [0, 0, 0, 0], side=1, ids=[12, 3.0, None, math.nan])[0].ids == (
        "12", "3", "", "",
    )  # fmt: skip
    per_row = sdvplot.bin_ids(bins, len(X))
    assert all(per_row[r] == c.id for c in bins for r in c.rows)
    assert sdvplot.bin_ids(sdvplot.squarebin([0, None, math.inf], [0, 0, 0], side=1), 3) == ["0,0", "", ""]
    with pytest.raises(ValueError, match="outside the 1 points"):
        sdvplot.bin_ids(bins, 1)


def test_the_js_number_format_of_an_id():
    from sdvplot._bins import _js_str

    values = [1e-7, 1.5e-7, 1.23e22, 1e21, 0.000123, -2.5, 100.0, 1e300, -0.0, 5e-324, 1.2345678901234568e20, 0.1 + 0.2]
    # String(v) in Node 24 for each value
    js = "1e-7 1.5e-7 1.23e+22 1e+21 0.000123 -2.5 100 1e+300 0 5e-324 123456789012345680000 0.30000000000000004"
    assert " ".join(map(_js_str, values)) == js


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"shape": "tri", "radius": 1}, 'shape must be "hex" or "square"'),
        ({"radius": 0}, "radius must be a finite number > 0"),
        ({"radius": math.inf}, "radius must be a finite number > 0"),
        ({"radius": True}, "radius must be a finite number > 0"),
        ({"side": 1}, "hex takes radius only"),
        ({"radius": 1, "equal_area": True}, "hex takes radius only"),
        ({"shape": "square", "radius": 1}, "needs side, or radius with equal_area=True"),
        ({"shape": "square"}, "needs side, or radius with equal_area=True"),
        ({"shape": "square", "side": 1, "radius": 1}, "not both"),
        ({"shape": "square", "side": -1}, "side must be a finite number > 0"),
    ],
)
def test_binner_rejects_options_that_name_no_lattice(kwargs, match):
    with pytest.raises(InputError, match=match):
        sdvplot.binner(**kwargs)


def test_mismatched_lengths_are_an_error():
    with pytest.raises(ValueError, match="same length"):
        sdvplot.hexbin([1, 2], [1], radius=1)
    with pytest.raises(ValueError, match="one value per point"):
        sdvplot.squarebin([1, 2], [1, 2], side=1, ids=["a"])
    with pytest.raises(InputError, match="cell_points shape"):
        sdvplot.cell_points("tri", 1)


def test_series_inputs_bin_like_lists():
    pl = pytest.importorskip("polars")
    np = pytest.importorskip("numpy")
    want = sdvplot.hexbin(X, Y, radius=10)
    assert sdvplot.hexbin(pl.Series(X), pl.Series(Y), radius=10) == want
    assert sdvplot.hexbin(np.array(X), np.array(Y), radius=10) == want


# The adapters: every one draws binner's cells, so each test hook returns the same (id, x, y, count) per cell.
SMALL_X, SMALL_Y = X[:200], Y[:200]
SHAPES = [{"shape": "hex", "radius": 15}, {"shape": "square", "side": 15}, {"shape": "square", "radius": 15, "equal_area": True}]  # fmt: skip


def _want(opts):
    return [(c.id, c.x, c.y, c.count) for c in sdvplot.binner(**opts).bins(SMALL_X, SMALL_Y)]


@pytest.mark.parametrize("opts", SHAPES)
def test_matplotlib_add_bins(opts):
    plt = pytest.importorskip("matplotlib.pyplot")
    from sdvplot import matplotlib as sdv_mpl

    fig, ax = plt.subplots()
    assert sdvplot.add_bins(ax, SMALL_X, SMALL_Y, **opts, cmap="Blues", norm="log") is ax
    drawn = sdv_mpl._drawn_bins(ax)
    assert [d[:4] for d in drawn] == _want(opts)
    bins = sdvplot.binner(**opts).bins(SMALL_X, SMALL_Y)
    assert [d[4] for d in drawn] == [c.ids for c in bins]
    coll = ax.collections[-1]
    assert list(coll.get_array()) == [d[3] for d in drawn]
    b = sdvplot.binner(**opts)
    corners = b.cell_points(b.size * FILL[b.shape])  # drawn at add_bins' default fill
    assert coll.get_paths()[0].vertices[: len(corners)].tolist() == [[bins[0].x + a, bins[0].y + b] for a, b in corners]
    fig.colorbar(coll, ax=ax)  # the drop-in for ax.hexbin's return value
    plt.close(fig)


@pytest.mark.parametrize("opts", SHAPES)
def test_plotly_add_bins_carries_ids_and_point_ids(opts):
    go = pytest.importorskip("plotly.graph_objects")
    from sdvplot import plotly as sdv_plotly

    fig = go.Figure(go.Scatter(x=SMALL_X, y=SMALL_Y, mode="markers"))
    assert sdvplot.add_bins(fig, SMALL_X, SMALL_Y, **opts, colorscale="Blues") is fig
    drawn = sdv_plotly._drawn_bins(fig)
    assert [d[:4] for d in drawn] == _want(opts)
    bins = sdvplot.binner(**opts).bins(SMALL_X, SMALL_Y)
    assert [d[4] for d in drawn] == [c.ids for c in bins]
    assert len(fig.layout.shapes) == len(bins)
    # a selected cell's customdata selects its points on the points trace, and back
    fig.data[0].selectedpoints = [int(i) for i in drawn[0][4]]
    assert sorted(fig.data[0].selectedpoints) == sorted(bins[0].rows)
    fig.to_json()  # serializes (ragged customdata included)


@pytest.mark.parametrize("opts", SHAPES)
def test_bokeh_add_bins_links_selection_both_ways(opts):
    pytest.importorskip("bokeh")
    from bokeh.models import ColumnDataSource, CustomJS
    from bokeh.plotting import figure

    from sdvplot import bokeh as sdv_bokeh

    shots = ColumnDataSource({"x": SMALL_X, "y": SMALL_Y})
    p = figure(tools="tap,box_select", frame_height=300)
    p.scatter("x", "y", source=shots)
    assert sdvplot.add_bins(p, SMALL_X, SMALL_Y, **opts, link=shots) is p
    drawn = sdv_bokeh._drawn_bins(p)
    assert [d[:4] for d in drawn] == _want(opts)
    assert sdv_bokeh._drawn_marks(p) == []  # the bins glyph is not an image
    cells = next(r for r in p.renderers if r.name == "sdvplot_bins").data_source
    assert cells.data["rows"] == [list(c.rows) for c in sdvplot.binner(**opts).bins(SMALL_X, SMALL_Y)]
    to_points = cells.selected.js_property_callbacks["change:indices"]
    to_cells = shots.selected.js_property_callbacks["change:indices"]
    assert all(isinstance(cb, CustomJS) and cb.args == {"cells": cells, "points": shots} for cb in to_points + to_cells)
    with pytest.raises(TypeError, match="ColumnDataSource"):
        sdvplot.add_bins(p, SMALL_X, SMALL_Y, **opts, link={"x": []})
    with pytest.raises(ValueError, match="one row per point"):
        sdvplot.add_bins(p, SMALL_X, SMALL_Y, **opts, link=ColumnDataSource({"x": [1]}))


def test_bokeh_link_callbacks_behave_in_a_js_engine():
    """Run the two CustomJS bodies on plain objects in Node: one point stays one point, a cell selects its points."""
    import shutil
    import subprocess

    from sdvplot.bokeh import _CELLS_TO_POINTS, _POINTS_TO_CELLS

    node = shutil.which("node")
    if node is None:
        pytest.skip("needs node")
    script = f"""
const cells = {{ data: {{ rows: [[0, 2], [1], [3, 4]] }}, selected: {{ indices: [] }} }};
const points = {{ selected: {{ indices: [] }} }};
const toPoints = new Function("cells", "points", {json.dumps(_CELLS_TO_POINTS)});
const toCells = new Function("cells", "points", {json.dumps(_POINTS_TO_CELLS)});
const settle = () => {{ for (let k = 0; k < 4; k++) {{ toCells(cells, points); toPoints(cells, points); }} }};
const out = [];
points.selected.indices = [2]; toCells(cells, points); toPoints(cells, points); settle();
out.push([cells.selected.indices, points.selected.indices]);
cells.selected.indices = [2]; points.selected.indices = []; toPoints(cells, points); settle();
out.push([cells.selected.indices, points.selected.indices]);
cells.selected.indices = []; toPoints(cells, points); settle();
out.push([cells.selected.indices, points.selected.indices]);
console.log(JSON.stringify(out));
"""
    res = subprocess.run([node, "-e", script], capture_output=True, text=True, check=True)
    assert json.loads(res.stdout) == [[[0], [2]], [[2], [3, 4]], [[], []]]


@pytest.mark.parametrize("opts", SHAPES)
def test_altair_add_bins_draws_cells_with_a_bin_id_selection(opts):
    alt = pytest.importorskip("altair")
    from sdvplot import altair as sdv_alt

    points = alt.Chart(alt.Data(values=[{"x": a, "y": b} for a, b in zip(SMALL_X, SMALL_Y, strict=True)]))
    chart = sdvplot.add_bins(points.mark_circle().encode(x="x:Q", y="y:Q"), SMALL_X, SMALL_Y, **opts)
    assert isinstance(chart, alt.LayerChart)
    assert [d[:4] for d in sdv_alt._drawn_bins(chart)] == _want(opts)
    assert sdv_alt._drawn_marks(chart) == []
    spec = chart.to_dict()
    assert any(p["name"] == "sdvplot_bins" and p["select"]["fields"] == ["bin_id"] for p in spec.get("params", []))
    rows = chart.layer[-1].data.values
    per_cell = 3 if opts["shape"] == "hex" else 2  # a hexagon is three bands' worth of x, a square two
    assert len(rows) == per_cell * len(_want(opts))
    linked = sdvplot.add_bins(
        points.mark_circle(), SMALL_X, SMALL_Y, **opts, link=alt.selection_point(fields=["bin_id"])
    )
    assert "sdvplot_bins" in json.dumps(linked.to_dict())


def test_a_hexagon_in_altair_is_the_polygon_binner_draws():
    pytest.importorskip("altair")
    import altair as alt

    chart = sdvplot.add_bins(alt.Chart().mark_point(), [0], [0], radius=10)
    rows = chart.layer[-1].data.values
    w = 10 * math.sin(math.pi / 3)
    got = [v for r in rows for v in (r["sdvplot_x"], r["sdvplot_y"], r["sdvplot_y2"])]
    assert got == pytest.approx([-w, -5, 5, 0, -10, 10, w, -5, 5])


def test_add_bins_on_a_library_without_bins_is_an_unsupported_target():
    pytest.importorskip("great_tables")
    import polars as pl
    from great_tables import GT

    with pytest.raises(UnsupportedTargetError, match="has no add_bins"):
        sdvplot.add_bins(GT(pl.DataFrame({"a": [1]})), [0], [0], radius=1)


def test_ids_are_read_by_position_and_pandas_missing_values_are_skipped():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"x": [0.0, 1.0, 30.0, 40.0], "y": [0.0, 1.0, 30.0, 40.0], "sid": [10, 11, 12, 13]})
    rev = df.iloc[::-1]  # a reversed index: ids[r] by label would name the wrong points
    assert [b.ids for b in sdvplot.hexbin(rev.x, rev.y, radius=10, ids=rev.sid)] == [("13",), ("12",), ("11", "10")]
    kept = df[df.x != 0]  # a filtered index: no label 0
    assert [b.ids for b in sdvplot.hexbin(kept.x, kept.y, radius=10, ids=kept.sid)] == [("11",), ("12",), ("13",)]
    x = pd.Series([0.0, None, 30.0], dtype="Float64")  # pandas' NA is missing, as None and NaN are
    assert sum(b.count for b in sdvplot.hexbin(x, [0.0, 1.0, 30.0], radius=10)) == 2


def test_ids_follow_javascript_string_and_numpy_sizes_are_accepted():
    np = pytest.importorskip("numpy")
    bins = sdvplot.hexbin([0, 30], [0, 30], radius=np.int64(10), ids=[True, np.float32(2.0)])
    assert [b.ids for b in bins] == [("true",), ("2",)]  # String(true), String(2)


def test_an_equal_area_side_that_overflows_is_an_input_error():
    with pytest.raises(InputError, match="equal-area side that is not finite"):
        sdvplot.binner(shape="square", radius=1.5e308, equal_area=True)  # * 1.61 > 1.8e308


@pytest.mark.parametrize("opts", [{"radius": 1e-12}, {"radius": 1e12}, {"shape": "square", "side": 1e-12}])
def test_altair_bands_hold_at_any_cell_size(opts):
    # by vertex index: rounding x to 9 places folded a 1e-12 hexagon's three bands into one
    alt = pytest.importorskip("altair")
    chart = sdvplot.add_bins(alt.Chart().mark_point(), [0], [0], **opts)
    rows = chart.layer[-1].data.values
    xs = [r["sdvplot_x"] for r in rows]
    assert len(rows) == (3 if "radius" in opts else 2) and xs == sorted(xs) and len(set(xs)) == len(xs)
    assert all(r["sdvplot_y"] < r["sdvplot_y2"] for r in rows)


def test_plotly_add_bins_keeps_existing_shapes_and_draws_on_the_named_axes():
    go = pytest.importorskip("plotly.graph_objects")
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=1, cols=2)
    fig.add_shape(type="line", x0=0, x1=1, y0=0, y1=1)
    sdvplot.add_bins(fig, SMALL_X, SMALL_Y, shape="square", side=15, xref="x2", yref="y2")
    n = len(sdvplot.squarebin(SMALL_X, SMALL_Y, side=15))
    assert len(fig.layout.shapes) == 1 + n and fig.layout.shapes[0].type == "line"
    assert {(s.xref, s.yref) for s in fig.layout.shapes[1:]} == {("x2", "y2")}
    assert (fig.data[-1].xaxis, fig.data[-1].yaxis) == ("x2", "y2")
    one = go.Figure()
    sdvplot.add_bins(one, SMALL_X, SMALL_Y, radius=15)
    assert {(s.xref, s.yref) for s in one.layout.shapes} == {("x", "y")}  # what add_shape set by default
    with pytest.raises(ValueError, match="xref must name a x axis"):
        sdvplot.add_bins(one, SMALL_X, SMALL_Y, radius=15, xref="y")


# origin, weights, value, fill and min_count: the same names and meaning as sdvplotR's.
HOOP = (25.0, 52.5)  # a basket's coordinates


@pytest.mark.parametrize("opts", SHAPES)
def test_origin_shifts_the_lattice_so_a_centre_falls_on_it(opts):
    from sdvplot._bins import _js_str

    ox, oy = HOOP
    base = sdvplot.binner(**opts).bins(SMALL_X, SMALL_Y)
    moved = sdvplot.binner(**opts, origin=HOOP).bins([v + ox for v in SMALL_X], [v + oy for v in SMALL_Y])
    assert [c.rows for c in moved] == [c.rows for c in base]  # the points shifted with the lattice: the same cells
    assert [v for c in moved for v in (c.x, c.y)] == pytest.approx([v for c in base for v in (c.x + ox, c.y + oy)])
    assert [c.id for c in moved] == [f"{_js_str(c.x)},{_js_str(c.y)}" for c in moved]  # the absolute centre
    hit = sdvplot.binner(**opts, origin=HOOP).bins([ox], [oy])
    assert (hit[0].x, hit[0].y, hit[0].id) == (
        ox,
        oy,
        "25,52.5",
    )  # a point on the origin sits on a centre


def test_origin_reaches_hexbin_squarebin_and_the_lattice_record():
    assert sdvplot.hexbin([25], [52.5], radius=10, origin=HOOP)[0].id == "25,52.5"
    assert sdvplot.squarebin([24], [50], side=10, origin=HOOP)[0].id == "25,52.5"
    b = sdvplot.binner(shape="square", side=10, origin=HOOP)
    assert b.origin == HOOP and b.lattice == {
        "shape": "square",
        "side": 10.0,
        "origin": HOOP,
    }
    assert sdvplot.binner(radius=10).lattice == {"radius": 10.0}  # the default (0, 0) leaves the record as it was
    for bad in [(1,), (1, 2, 3), (0, math.nan), (True, 0), "ab", None]:
        with pytest.raises(InputError, match="origin"):
            sdvplot.hexbin([0], [0], radius=10, origin=bad)


def test_weights_sum_per_bin_and_default_to_the_count():
    x, y = [0, 1, 2, 40, 41], [0, 1, 2, 40, 41]
    bins = sdvplot.hexbin(x, y, radius=10, weights=[2, 3, 0.5, 1, 1])
    assert [(c.count, c.weight) for c in bins] == [(3, 5.5), (2, 2.0)]
    assert [(c.count, c.weight) for c in sdvplot.hexbin(x, y, radius=10)] == [
        (3, 3.0),
        (2, 2.0),
    ]
    # a missing or non-finite weight counts 0 and the point stays in its bin
    bins = sdvplot.squarebin(x, y, side=10, weights=[None, math.nan, math.inf, 2, -math.inf])
    assert [(c.count, c.weight) for c in bins] == [(3, 0.0), (2, 2.0)]
    assert sdvplot.binner(radius=10).bins(x, y, weights=[1] * 5)[0].weight == 3.0
    with pytest.raises(ValueError, match="weights must be >= 0"):
        sdvplot.hexbin(x, y, radius=10, weights=[1, 1, -1, 1, 1])
    with pytest.raises(ValueError, match="weights must be numbers"):
        sdvplot.hexbin(x, y, radius=10, weights=[1, "2", 1, 1, 1])
    with pytest.raises(ValueError, match="one value per point"):
        sdvplot.hexbin(x, y, radius=10, weights=[1])


def test_weights_are_read_by_position_and_pandas_na_counts_zero():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"x": [0.0, 1.0, 30.0], "y": [0.0, 1.0, 30.0], "pts": [2, 3, 3]}).iloc[::-1]
    assert [c.weight for c in sdvplot.hexbin(df.x, df.y, radius=10, weights=df.pts)] == [3.0, 5.0]
    w = pd.Series([2.0, None, 3.0], dtype="Float64")
    assert [c.weight for c in sdvplot.hexbin([0, 1, 30], [0, 1, 30], radius=10, weights=w)] == [2.0, 3.0]


WEIGHTS = [float(i % 3) for i in range(len(SMALL_X))]  # 0, 1 or 2 points a shot


def _want_weights(opts):
    return [c.weight for c in sdvplot.binner(**opts).bins(SMALL_X, SMALL_Y, weights=WEIGHTS)]


@pytest.mark.parametrize("opts", SHAPES)
def test_value_weight_colors_by_the_weights_in_every_web_and_mpl_adapter(opts):
    want = _want_weights(opts)
    assert want != [float(c[3]) for c in _want(opts)]  # the two encodings differ on these points
    plt = pytest.importorskip("matplotlib.pyplot")
    fig, ax = plt.subplots()
    sdvplot.add_bins(ax, SMALL_X, SMALL_Y, **opts, weights=WEIGHTS, value="weight")
    assert list(ax.collections[-1].get_array()) == want
    plt.close(fig)
    go = pytest.importorskip("plotly.graph_objects")
    fig = sdvplot.add_bins(go.Figure(), SMALL_X, SMALL_Y, **opts, weights=WEIGHTS, value="weight")
    assert list(fig.data[-1].marker.color) == want and fig.data[-1].marker.colorbar.title.text == "weight"
    pytest.importorskip("bokeh")
    from bokeh.plotting import figure

    p = sdvplot.add_bins(figure(), SMALL_X, SMALL_Y, **opts, weights=WEIGHTS, value="weight")
    glyph = next(r for r in p.renderers if r.name == "sdvplot_bins")
    assert glyph.data_source.data["weight"] == want and glyph.glyph.fill_color.field == "weight"
    alt = pytest.importorskip("altair")
    chart = sdvplot.add_bins(
        alt.Chart().mark_point(),
        SMALL_X,
        SMALL_Y,
        **opts,
        weights=WEIGHTS,
        value="weight",
    )
    assert chart.layer[-1].to_dict()["encoding"]["color"]["field"] == "weight"
    with pytest.raises(InputError, match="value"):
        sdvplot.add_bins(go.Figure(), SMALL_X, SMALL_Y, **opts, value="sum")


def test_default_fill_leaves_a_gap_between_squares_and_tiles_hexagons():
    plt = pytest.importorskip("matplotlib.pyplot")
    for opts, size in [
        ({"shape": "square", "side": 15}, 15.0),
        ({"shape": "hex", "radius": 15}, 30.0),
    ]:
        fig, ax = plt.subplots()
        sdvplot.add_bins(ax, SMALL_X, SMALL_Y, **opts)
        widths = {
            round(float(p.vertices[:, 0].max() - p.vertices[:, 0].min()), 9) for p in ax.collections[-1].get_paths()
        }
        if opts["shape"] == "square":
            assert max(widths) < size  # never the lattice cell's side: neighbours do not touch
            assert widths == {round(0.88 * size, 9)}
            sdvplot.add_bins(ax, SMALL_X, SMALL_Y, **opts, fill=1.0)
            assert {round(float(p.vertices[:, 0].max() - p.vertices[:, 0].min()), 9) for p in ax.collections[-1].get_paths()} == {size}  # fmt: skip
        else:
            assert widths == {round(30 * math.sin(math.pi / 3), 9)}  # a full-radius hexagon's width
        plt.close(fig)
    for bad in [0, -0.5, 1.5, math.nan, True, "big"]:
        with pytest.raises(InputError, match="fill"):
            sdvplot.add_bins(plt.subplots()[1], SMALL_X, SMALL_Y, radius=15, fill=bad)
    plt.close("all")


@pytest.mark.parametrize("opts", SHAPES)
def test_min_count_drops_sparse_cells_from_the_drawing_only(opts):
    plt = pytest.importorskip("matplotlib.pyplot")
    from sdvplot import matplotlib as sdv_mpl

    every = sdvplot.binner(**opts).bins(SMALL_X, SMALL_Y)
    assert any(c.count == 1 for c in every)
    fig, ax = plt.subplots()
    sdvplot.add_bins(ax, SMALL_X, SMALL_Y, **opts, min_count=2)
    assert [d[:4] for d in sdv_mpl._drawn_bins(ax)] == [(c.id, c.x, c.y, c.count) for c in every if c.count >= 2]
    assert sdvplot.binner(**opts).bins(SMALL_X, SMALL_Y) == every  # binning itself is unaffected
    assert sum(c.count for c in every) == len(SMALL_X)  # single attempts still count in the totals
    plt.close(fig)
    for bad in [0, 1.5, True, None]:
        with pytest.raises(InputError, match="min_count"):
            sdvplot.add_bins(ax, SMALL_X, SMALL_Y, **opts, min_count=bad)


# the new adapters: plotnine, HoloViews, folium and pygal draw the same cells


@pytest.mark.parametrize("opts", SHAPES)
def test_plotnine_add_bins_is_a_polygon_layer(opts):
    pytest.importorskip("plotnine")
    import pandas as pd
    from plotnine import aes, geom_point, ggplot

    from sdvplot import plotnine as sdv_p9

    p = ggplot(pd.DataFrame({"x": SMALL_X, "y": SMALL_Y}), aes("x", "y")) + geom_point()
    out = sdvplot.add_bins(p, SMALL_X, SMALL_Y, **opts, weights=WEIGHTS, value="weight", alpha=0.6)
    assert out is not p and len(p.layers) == 1  # a copy, as plotnine's +
    assert [d[:4] for d in sdv_p9._drawn_bins(out)] == _want(opts)
    layer = out.layers[-1]
    assert layer.mapping["fill"] == "weight" and layer.mapping["group"] == "bin_id"
    assert layer.geom.data.drop_duplicates("bin_id")["weight"].tolist() == _want_weights(opts)
    fig = out.draw()  # it renders
    import matplotlib.pyplot as plt

    plt.close(fig)
    two = sdvplot.add_bins(p, SMALL_X, SMALL_Y, **opts, min_count=2)
    assert all(d[3] >= 2 for d in sdv_p9._drawn_bins(two))


@pytest.mark.parametrize("opts", SHAPES)
def test_holoviews_add_bins_draws_the_bokeh_glyph_and_links_it(opts):
    hv = pytest.importorskip("holoviews")
    from bokeh.models import CustomJS

    from sdvplot import holoviews as sdv_hv

    hv.extension("bokeh")
    shots = hv.Points({"x": SMALL_X, "y": SMALL_Y}, ["x", "y"])
    plot = sdvplot.add_bins(shots * hv.Curve([(0, 0), (1, 1)]), SMALL_X, SMALL_Y, **opts, link=shots)
    assert [d[:4] for d in sdv_hv._drawn_bins(plot)] == _want(opts)
    fig = hv.render(plot, backend="bokeh")
    cells = next(r for r in fig.renderers if r.name == "sdvplot_bins").data_source
    callbacks = cells.selected.js_property_callbacks["change:indices"]
    assert len(callbacks) == 1 and isinstance(callbacks[0], CustomJS)
    points = callbacks[0].args["points"]
    assert len(points.data["x"]) == len(SMALL_X)  # the rendered hv.Points source, linked both ways
    assert points.selected.js_property_callbacks["change:indices"][0].args["cells"] is cells
    with pytest.raises(ValueError, match="link must be an element of target"):
        sdvplot.add_bins(shots, SMALL_X, SMALL_Y, **opts, link=hv.Points([(0, 0)]))
    with pytest.raises(InputError, match="min_count"):  # checked when called, not swallowed by the render hook
        sdvplot.add_bins(shots, SMALL_X, SMALL_Y, **opts, min_count=0)
    with pytest.raises(InputError, match="value"):
        sdvplot.add_bins(shots, SMALL_X, SMALL_Y, **opts, value="sum")


@pytest.mark.parametrize("opts", SHAPES)
def test_folium_add_bins_is_a_geojson_layer_in_degrees(opts):
    folium = pytest.importorskip("folium")
    from sdvplot import folium as sdv_folium

    lon = [-74 + v / 1000 for v in SMALL_X]
    lat = [40.8 + v / 1000 for v in SMALL_Y]
    deg = {k: (v / 1000 if k in ("radius", "side") else v) for k, v in opts.items()}
    m = folium.Map(location=[40.9, -74])
    assert sdvplot.add_bins(m, lon, lat, **deg, origin=(-74, 40.8), value="weight", weights=WEIGHTS) is m
    want = sdvplot.binner(**deg, origin=(-74, 40.8)).bins(lon, lat, weights=WEIGHTS)
    assert [d[:4] for d in sdv_folium._drawn_bins(m)] == [(c.id, c.x, c.y, c.count) for c in want]
    layer = next(c for c in m._children.values() if getattr(c, "_sdvplot_bins", False))
    feature = layer.data["features"][0]
    ring = feature["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1] and len(ring) == (7 if opts["shape"] == "hex" else 5)  # a closed [lon, lat] ring
    assert feature["properties"]["weight"] == want[0].weight
    assert layer.layer_name == "sdvplot bins" and "geo_json" in m.get_root().render()  # it renders
    assert sdv_folium._drawn_marks(m) == []
    with pytest.raises(ValueError, match="branca"):
        sdvplot.add_bins(m, lon, lat, **deg, palette="no_such_map")


@pytest.mark.parametrize("opts", SHAPES)
def test_pygal_add_bins_draws_polygons_under_the_series(opts):
    pygal = pytest.importorskip("pygal")
    from sdvplot import pygal as sdv_pygal

    chart = pygal.XY(stroke=False)
    chart.add("shots", list(zip(SMALL_X, SMALL_Y, strict=True)))
    assert sdvplot.add_bins(chart, SMALL_X, SMALL_Y, **opts, value="weight", weights=WEIGHTS) is chart
    assert [d[:4] for d in sdv_pygal._drawn_bins(chart)] == _want(opts)
    root = chart.render_tree()
    plot = next(el for el in root.iter() if el.get("class") == "plot")
    kids = [el.get("class") or "" for el in plot]
    assert kids.index("sdvplot-bins") < next(i for i, k in enumerate(kids) if k.startswith("series"))
    polygons = [el for el in root.iter() if el.get("data-sdvplot-bin") is not None]
    assert len(polygons[0].get("points").split()) == (6 if opts["shape"] == "hex" else 4)
    fills = {el.get("fill") for el in polygons}
    assert {
        "#deebf7",
        "#08519c",
    } <= fills  # the lowest and highest weight take the two ends of the ramp
    assert sdv_pygal._drawn_marks(chart) == []
    with pytest.raises(ValueError):
        sdvplot.add_bins(chart, SMALL_X, SMALL_Y, **opts, low="not a color")


# Plotly in static HTML: link_script


def test_plotly_link_script_maps_each_cell_to_its_points_trace_rows():
    go = pytest.importorskip("plotly.graph_objects")
    from sdvplot.plotly import link_script

    fig = go.Figure(go.Scatter(x=SMALL_X, y=SMALL_Y, mode="markers"))
    fig.add_trace(go.Scatter(x=[0], y=[0]))  # another trace between them
    sdvplot.add_bins(fig, SMALL_X, SMALL_Y, radius=15)
    bins = sdvplot.hexbin(SMALL_X, SMALL_Y, radius=15)
    script = link_script(fig)
    assert "var BINS = 2, POINTS = 0;" in script and '"{plot_id}"' in script
    assert f"var CELLS = {json.dumps([list(c.rows) for c in bins], separators=(',', ':'))};" in script
    for event in (
        "plotly_selected",
        "plotly_deselect",
        "plotly_hover",
        "plotly_unhover",
    ):
        assert f'gd.on("{event}"' in script
    html = fig.to_html(post_script=script, include_plotlyjs=False)
    assert 'document.getElementById("{plot_id}")' not in html and "var BINS = 2" in html  # plotly filled the id
    # ids: a points trace's customdata are the ids add_bins was given, matched as strings
    sid = [f"s{i}" for i in range(len(SMALL_X))][::-1]
    fig2 = go.Figure(go.Scatter(x=SMALL_X[::-1], y=SMALL_Y[::-1], customdata=sid, mode="markers"))
    sdvplot.add_bins(fig2, SMALL_X, SMALL_Y, radius=15, ids=[f"s{i}" for i in range(len(SMALL_X))])
    n = len(SMALL_X)
    cells = [sorted(n - 1 - r for r in c.rows) for c in bins]  # the points trace is reversed
    assert f"var CELLS = {json.dumps(cells, separators=(',', ':'))};" in link_script(fig2)
    with pytest.raises(ValueError, match="no add_bins trace"):
        link_script(go.Figure(go.Scatter(x=[0], y=[0])))
    with pytest.raises(ValueError, match="points must be"):
        link_script(fig, points=2)
    with pytest.raises(ValueError, match="bins must be"):
        link_script(fig, bins=0)


def test_plotly_link_script_behaves_in_a_js_engine():
    """Run the script on a fake plotly div in Node: a cell selects its points, a point its cells, hover highlights."""
    import shutil
    import subprocess

    go = pytest.importorskip("plotly.graph_objects")
    from sdvplot.plotly import link_script

    node = shutil.which("node")
    if node is None:
        pytest.skip("needs node")
    x, y = [0, 1, 40, 41, 80], [0, 1, 40, 41, 80]
    fig = go.Figure(go.Scatter(x=x, y=y, mode="markers"))
    sdvplot.add_bins(fig, x, y, radius=10)  # cells [0, 1], [2, 3], [4]
    script = link_script(fig).replace("{plot_id}", "plot")
    harness = f"""
const handlers = {{}}, calls = [];
const gd = {{ on: (name, fn) => {{ handlers[name] = fn; }} }};
global.document = {{ getElementById: (id) => (id === "plot" ? gd : null) }};
global.Plotly = {{ restyle: (g, update, traces) => calls.push([update.selectedpoints[0], traces]) }};
{script}
const out = [];
handlers.plotly_selected({{ points: [{{ curveNumber: 1, pointIndex: 1 }}] }}); out.push(calls.splice(0));
handlers.plotly_selected({{ points: [{{ curveNumber: 0, pointIndex: 4 }}, {{ curveNumber: 0, pointIndex: 0 }}] }});
out.push(calls.splice(0));
handlers.plotly_hover({{ points: [{{ curveNumber: 1, pointIndex: 0 }}] }}); out.push(calls.splice(0));
handlers.plotly_unhover({{ points: [{{ curveNumber: 1, pointIndex: 0 }}] }}); out.push(calls.splice(0));
handlers.plotly_deselect(); out.push(calls.splice(0));
console.log(JSON.stringify(out));
"""
    res = subprocess.run([node, "-e", harness], capture_output=True, text=True, check=True)
    assert json.loads(res.stdout) == [
        [[[1], [1]], [[2, 3], [0]]],  # cell 1 selected: its points 2 and 3
        [
            [[0, 2], [1]],
            [[4, 0], [0]],
        ],  # points 4 and 0 selected: the cells holding them
        [[[0, 1], [0]]],  # hovering cell 0 highlights its points
        [[[4, 0], [0]]],  # leaving it restores the chosen points
        [[None, [1]], [None, [0]]],  # double-click clears both
    ]

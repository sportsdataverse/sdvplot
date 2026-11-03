"""Hex and square bins: parity with sdvplot-js on 2000 real shots, and each adapter's add_bins and its linking."""

import json
import math
from pathlib import Path

import pytest

import sdvplot
from sdvplot import InputError, UnsupportedTargetError

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
    assert [list(p) for p in sdvplot.cell_points("hex", 10)] == FIXTURE["cells"]["hex10"]
    assert [list(p) for p in sdvplot.cell_points("square", 10)] == FIXTURE["cells"]["square10"]


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
    corners = sdvplot.binner(**opts).cell_points()
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
    pytest.importorskip("folium")
    import folium

    with pytest.raises(UnsupportedTargetError, match="has no add_bins"):
        sdvplot.add_bins(folium.Map(), [0], [0], radius=1)

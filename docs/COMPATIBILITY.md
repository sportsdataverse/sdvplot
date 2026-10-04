<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Compatibility with the Python dataviz gallery](#compatibility-with-the-python-dataviz-gallery)
  - [The matrix](#the-matrix)
  - [Recipes](#recipes)
    - [Cartopy: logos at longitude/latitude](#cartopy-logos-at-longitudelatitude)
    - [GeoPandas: logos at centroids](#geopandas-logos-at-centroids)
    - [NetworkX: logos on nodes](#networkx-logos-on-nodes)
    - [PyPalettes: a colormap of team colors](#pypalettes-a-colormap-of-team-colors)
    - [wordcloud: each team in its color](#wordcloud-each-team-in-its-color)
  - [Watch list: Reflex XY](#watch-list-reflex-xy)
  - [Keeping this page true](#keeping-this-page-true)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Compatibility with the Python dataviz gallery

A contributor reference: how sdvplot works with each package on
[python-graph-gallery's best dataviz packages](https://python-graph-gallery.com/best-dataviz-packages/) list
(snapshot 2026-10-04), and the test that proves it. Most of the list draws on a matplotlib Axes, so sdvplot's
matplotlib adapter serves it with no package-specific code; the rest get an adapter or team colors.

Paths:

- **adapter**: sdvplot has a module for the library (`sdvplot.<library>`), routed to by `sdvplot.add_logos(target, ...)`.
- **Axes**: the package draws on a matplotlib Axes, so `sdvplot.add_logos(ax, ...)` works on its output.
- **colors**: the package takes colors, not images; pass `sdvplot.palette()` or `sdvplot.team_colors()`.

## The matrix

| Gallery section | Package | Path | Proved by |
| --- | --- | --- | --- |
| Core | matplotlib | adapter `sdvplot.matplotlib` | `tests/test_matplotlib.py::test_the_axes_adapter_passes_the_contract` |
| Core | seaborn | adapter `sdvplot.matplotlib` | `tests/test_matplotlib.py::test_a_seaborn_grid_passes_the_contract` |
| Core | plotnine | adapter `sdvplot.plotnine` | `tests/test_plotnine.py` |
| Core, Interactivity | Plotly | adapter `sdvplot.plotly` | its contract test (sub-project 3) |
| Matplotlib extensions | PyPalettes | colors | `tests/test_compat_style.py::test_pypalettes_builds_a_colormap_from_team_colors` |
| Matplotlib extensions | pyfonts | Axes (fonts load from the network) | `tests/test_compat_style.py::test_a_pyfonts_font_and_logos_share_an_axes` (live only) |
| Matplotlib extensions | drawarrow | Axes | `tests/test_compat_text.py::test_drawarrow_arrows_join_logos` |
| Matplotlib extensions, Specific chart types | DayPlot | Axes | `tests/test_compat_charts.py::test_dayplot_calendar_cells_take_logos` |
| Matplotlib extensions | morethemes | Axes | `tests/test_compat_style.py::test_a_morethemes_theme_keeps_logos_drawing` |
| Matplotlib extensions, Specific chart types | bumplot | Axes | `tests/test_compat_charts.py::test_bumplot_lines_take_logos_at_their_last_rank` |
| Matplotlib extensions | highlight-text | Axes | `tests/test_compat_text.py::test_highlight_text_and_logos_share_an_axes` |
| Matplotlib extensions | Flexitext | Axes | `tests/test_compat_text.py::test_flexitext_and_logos_share_an_axes` |
| Geospatial | GeoPandas | Axes | `tests/test_compat_geo.py::test_geopandas_plot_takes_logos_at_centroids` |
| Geospatial | geoplot | Axes (a GeoAxes when projected: pass `transform=`) | `tests/test_compat_geo.py::test_geoplot_takes_logos_on_its_plain_and_projected_axes` |
| Geospatial | Cartopy | Axes with `transform=ccrs.PlateCarree()` | `tests/test_compat_cartopy.py::test_logos_sit_at_longitude_latitude_on_a_projected_map` |
| Geospatial | Folium | adapter `sdvplot.folium` | its contract test (sub-project 3) |
| Interactivity | Bokeh | adapter `sdvplot.bokeh` | its contract test (sub-project 3) |
| Interactivity | Altair | adapter `sdvplot.altair` | its contract test (sub-project 3) |
| Specific chart types | NetworkX | Axes | `tests/test_compat_charts.py::test_networkx_nodes_take_logos_at_their_layout_positions` |
| Specific chart types | wordcloud | colors (a `color_func`; logos make no sense in a word cloud) | `tests/test_compat_style.py::test_wordcloud_colors_each_team_with_its_own_color` |
| Specific chart types | PyWaffle | Axes (a `Waffle` Figure with one Axes) | `tests/test_compat_charts.py::test_a_pywaffle_figure_takes_logos` |
| Tables | great_tables | adapter `sdvplot.great_tables` | its tests (sub-project 4) |
| Tables | plottable | `sdvplot.plottable` columns | `tests/test_plottable.py` |

Not on the gallery list, also supported: pygal (adapter `sdvplot.pygal`, `tests/test_pygal.py`), HoloViews (adapter
`sdvplot.holoviews`, sub-project 3), sportypy surfaces (`sdvplot.surface()`, `tests/test_surface.py`) and mplsoccer
pitches (`tests/test_matplotlib.py::test_logos_draw_on_an_mplsoccer_pitch`).

## Recipes

### Cartopy: logos at longitude/latitude

A `GeoAxes`' data coordinates are the projection's, so pass the CRS your positions are in. Without it, sdvplot raises
`ValueError` rather than drawing in the wrong place. A point outside the map's extent, or behind an orthographic globe,
is not drawn.

```python
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import sdvplot

ax = plt.axes(projection=ccrs.LambertConformal())
ax.set_extent([-125, -66, 24, 50], crs=ccrs.PlateCarree())
sdvplot.add_logos(ax, [-94.48, -78.79], [39.05, 42.77], ["KC", "BUF"], league="nfl", transform=ccrs.PlateCarree())
```

geoplot with a `projection=` returns a `GeoAxes` too: use the same `transform=`.

### GeoPandas: logos at centroids

```python
centers = gdf.to_crs(3857).centroid.to_crs(4326)   # centroids in a projected CRS, back to lon/lat
ax = gdf.plot(color="#dddddd")
sdvplot.add_logos(ax, centers.x, centers.y, gdf["team"], league="nfl", height=0.1)
```

### NetworkX: logos on nodes

```python
pos = nx.spring_layout(graph, seed=7)
nx.draw(graph, pos, ax=ax)
nodes = list(graph)
sdvplot.add_logos(ax, [pos[n][0] for n in nodes], [pos[n][1] for n in nodes], nodes, league="nfl")
```

### PyPalettes: a colormap of team colors

```python
cmap = pypalettes.create_cmap(sdvplot.team_colors(["KC", "BUF"], "nfl"), cmap_type="discrete")
```

### wordcloud: each team in its color

```python
names = ["Kansas City Chiefs", "Buffalo Bills"]
color = dict(zip(names, sdvplot.team_colors(names, "nfl")))
cloud = WordCloud(color_func=lambda word, **kw: color[word]).generate_from_frequencies({"Kansas City Chiefs": 3, "Buffalo Bills": 2})
```

## Watch list: Reflex XY

[reflex-xy](https://pypi.org/project/reflex-xy/) draws WebGL charts in Reflex apps. Checked: **0.0.2** (released
2026-07-28), whose README documents no image marks or custom glyphs. Until it does, sdvplot supports it with colors
only: pass `sdvplot.palette(...)` or `sdvplot.team_colors(...)` hex strings wherever it takes a color.

**Criterion for an adapter:** a released reflex-xy version documents an image mark (a glyph that takes an image URL or
data URI) or a custom-glyph API. Re-check at every sdvplot release (`CONTRIBUTING.md`, Release), and update the version
and date above when you do.

## Keeping this page true

`tests/test_compat_matrix.py` checks that every test this page names exists. The `tests/test_compat_*.py` tests are
offline (except pyfonts, live only) and skip when their package is missing. Their packages are the `compat` dependency
group in `pyproject.toml`, which `uv sync --all-groups` installs; the geospatial ones, morethemes (it needs matplotlib 3.11) and NetworkX need Python 3.11 or
3.12, so the 3.10 CI job skips those tests.

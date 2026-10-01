# sdvplot

Team logos, wordmarks, headshots and colors for Python plots and tables, from the SportsDataverse logo archive.
The Python counterpart to [sdvplotR](https://sdvplotR.sportsdataverse.org/).

```bash
pip install sdvplot
```

## Get started

```python
import sdvplot

sdvplot.resolve(["LV", "OAK", "Las Vegas Raiders"], "nfl")      # ['13', '13', '13']
sdvplot.palette("nfl", teams=["LV", "KC"])                     # {'LV': '#000000', 'KC': '#e31837'}
sdvplot.logo_url("OAK", "nfl", season=2010)                    # the Oakland-era mark
img = sdvplot.logo_image("LV", "nfl", size=128)                # a PIL image
```

Colors work in any library that takes a `{value: color}` mapping, for example seaborn:
`sns.barplot(data=df, x="team", y="epa", hue="team", palette=sdvplot.palette("nfl", teams=df["team"]))`.

Colors marked `color_source="fallback"` are placeholders, not team colors.

## Extras

`pip install "sdvplot[mpl]"` etc.

| Extra | Adds |
| --- | --- |
| `[mpl]` | matplotlib |
| `[plotnine]` | plotnine |
| `[plotly]` | plotly |
| `[altair]` | altair |
| `[bokeh]` | bokeh |
| `[holoviews]` | holoviews |
| `[tables]` | great_tables |
| `[folium]` | folium |
| `[svg]` | resvg-py, for SVG marks |
| `[surfaces]` | sportypy and mplsoccer |
| `[all]` | everything above |

## Environment variables

- `SDVPLOT_CACHE_DIR`: cache root.
- `SDVPLOT_CACHE_TTL`: cache lifetime in days (default 7).
- `SDVPLOT_LIVE_TESTS=1`: enable the network tests.

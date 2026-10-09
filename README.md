# **sdvplot** <a href='https://sdvplot.sportsdataverse.org/'><img src='https://raw.githubusercontent.com/sportsdataverse/sdvplot/main/docs/static/img/sdvplot-logo.png' align="right" width="25%" min-width="120px" alt="sdvplot hex logo" /></a>

[![PyPI](https://img.shields.io/pypi/v/sdvplot?label=sdvplot&logo=python&style=for-the-badge)](https://pypi.org/project/sdvplot/)
[![Python](https://img.shields.io/pypi/pyversions/sdvplot?logo=python&logoColor=white&style=for-the-badge)](https://pypi.org/project/sdvplot/)
[![npm](https://img.shields.io/npm/v/@sportsdataverse/sdvplot?label=sdvplot-js&logo=npm&style=for-the-badge)](https://www.npmjs.com/package/@sportsdataverse/sdvplot)
[![Downloads](https://img.shields.io/pypi/dm/sdvplot?style=for-the-badge)](https://pypistats.org/packages/sdvplot)
[![Total downloads](https://img.shields.io/pepy/dt/sdvplot?style=for-the-badge)](https://pepy.tech/projects/sdvplot)
[![tests](https://img.shields.io/github/actions/workflow/status/sportsdataverse/sdvplot/tests.yml?branch=main&label=tests&logo=github&style=for-the-badge)](https://github.com/sportsdataverse/sdvplot/actions/workflows/tests.yml)
[![quality](https://img.shields.io/github/actions/workflow/status/sportsdataverse/sdvplot/quality.yml?branch=main&label=quality&logo=github&style=for-the-badge)](https://github.com/sportsdataverse/sdvplot/actions/workflows/quality.yml)
[![docs](https://img.shields.io/github/actions/workflow/status/sportsdataverse/sdvplot/docs-deploy.yml?branch=main&label=docs&logo=github&style=for-the-badge)](https://sdvplot.sportsdataverse.org)
[![Lifecycle: experimental](https://img.shields.io/badge/lifecycle-experimental-orange.svg?style=for-the-badge&logo=github)](https://lifecycle.r-lib.org/articles/stages.html#experimental)
[![License](https://img.shields.io/pypi/l/sdvplot?style=for-the-badge)](https://github.com/sportsdataverse/sdvplot/blob/main/LICENSE)
[![Contributors](https://img.shields.io/github/contributors/sportsdataverse/sdvplot?style=for-the-badge)](https://github.com/sportsdataverse/sdvplot/graphs/contributors)
[![Twitter Follow](https://img.shields.io/twitter/follow/SportsDataverse?color=blue&label=%40SportsDataverse&logo=x&style=for-the-badge)](https://x.com/SportsDataverse)

Team logos, wordmarks, headshots and colors for Python plots and tables, from the SportsDataverse logo archive. It
resolves team abbreviations, names and provider ids across 28 leagues and picks the right era's mark for a season. Colors
and logos work with any library through `palette()`, `team_colors()`, `logo_url()` and `logo_image()`, and the
`add_logos()`, `add_wordmarks()` and `add_headshots()` adapters draw them on matplotlib (and seaborn), plotnine, plotly,
altair, bokeh, holoviews, great_tables, folium and pygal plots, tables and maps. `sdvplot.great_tables` also ports
sdvplotR's table themes, cell styling, legends and image export, and `surface()` draws a league's field, court or rink
in a team's colors. The Python counterpart to [sdvplotR](https://sdvplotR.sportsdataverse.org/).

## **Installation**

```bash
pip install sdvplot
# or
uv add sdvplot
```

Plotting libraries are optional extras, for example
`pip install "sdvplot[mpl]"`. Each extra adds the libraries for one feature: `[svg]` lets `logo_image()`
rasterize SVG marks. With `[mpl]`, `[plotnine]`, `[plotly]`, `[altair]`, `[bokeh]`, `[holoviews]`, `[tables]`,
`[folium]` or `[pygal]`, `add_logos()`, `add_wordmarks()` and `add_headshots()` draw on that library's plots, tables and
maps; `axis_logos()` works on matplotlib, seaborn, plotnine, Plotly and Altair. `[surfaces]` is for `surface()`, and
`[reactable]` and `[plottable]` add column helpers (`sdvplot.reactable`, `sdvplot.plottable`).

| Extra | Adds |
| --- | --- |
| `[mpl]` | matplotlib |
| `[plotnine]` | plotnine |
| `[plotly]` | plotly |
| `[altair]` | altair |
| `[bokeh]` | bokeh |
| `[holoviews]` | holoviews |
| `[tables]` | great_tables |
| `[reactable]` | reactable (reactable-py) |
| `[folium]` | folium |
| `[svg]` | resvg-py, for SVG marks |
| `[surfaces]` | sportypy and mplsoccer |
| `[plottable]` | plottable |
| `[pygal]` | pygal |
| `[all]` | everything above |

### JavaScript / TypeScript

The same colors, logos, wordmarks and headshots are on npm as
[`@sportsdataverse/sdvplot`](https://www.npmjs.com/package/@sportsdataverse/sdvplot), with integrations for Observable
Plot, D3, React, Chart.js, Plotly, Vega-Lite and ECharts, plus shot charts and linked interactivity. Its siblings
[`@sportsdataverse/sporty`](https://www.npmjs.com/package/@sportsdataverse/sporty) (playing surfaces) and
[`@sportsdataverse/sdvtables`](https://www.npmjs.com/package/@sportsdataverse/sdvtables) (tables) ship from the same
[sdvplot-js repo](https://github.com/sportsdataverse/sdvplot-js). Docs for all three:
[plot.sportsdataverse.org](https://plot.sportsdataverse.org/).

```bash
npm install @sportsdataverse/sdvplot
```

## **Usage**

Team identity, colors and marks:

```python
import sdvplot

sdvplot.resolve(["LV", "OAK", "Las Vegas Raiders"], "nfl")  # ['13', '13', '13']
sdvplot.palette("nfl", teams=["LV", "KC"])  # {'LV': '#000000', 'KC': '#e31837'}
sdvplot.logo_url("OAK", "nfl", season=2010)  # the Oakland-era mark
img = sdvplot.logo_image("LV", "nfl", size=128)  # a PIL image
```

Logos on a plot, here the 2024 AFC playoff field in seed order:

```python
import matplotlib.pyplot as plt
import sdvplot

seeds = ["KC", "BUF", "BAL", "HOU", "LAC", "PIT", "DEN"]
x = list(range(1, 8))
fig, ax = plt.subplots(figsize=(8, 1.6))
sdvplot.add_logos(ax, x, [0] * 7, seeds, league="nfl", height=0.7)
ax.set(xlim=(0.5, 7.5), ylim=(-1, 1), xticks=x, yticks=[], title="2024 AFC playoff seeds")
```

Colors work in any library that takes a `{value: color}` mapping, for example seaborn:
`sns.barplot(data=df, x="team", y="epa", hue="team", palette=sdvplot.palette("nfl", teams=df["team"]))`.

`teams()` records where each team's colors come from in `color_source`: `nflverse` or `espn` when that source
publishes them, `logo` when they are derived from the team's archived logo because no source does, and `fallback` for
a placeholder that is not the team's colors (`cbbplotR` on the conference rows `teams(league, include_conferences=True)`
adds).

From the [gallery](https://sdvplot.sportsdataverse.org/docs/gallery), each drawn by sdvplot from the logo archive:

| | |
| --- | --- |
| ![NHL teams stacked by the decade their archived logos begin](https://raw.githubusercontent.com/sportsdataverse/sdvplot/main/docs/static/img/home/nhl-decades-light.png) | ![Each AFC team's two colors, their contrast ratio as the bar height, with logos on the axis](https://raw.githubusercontent.com/sportsdataverse/sdvplot/main/docs/static/img/home/afc-colors-light.png) |
| `add_logos()` as scatter points: NHL teams by the decade their archived logos begin | Each AFC team's two colors from `palette()`, their contrast as the height, `axis_logos()` on the axis |
| ![The Montreal Canadiens mark used in each season, from the logo archive](https://raw.githubusercontent.com/sportsdataverse/sdvplot/main/docs/static/img/home/montreal-eras-light.png) | ![Player headshots from five leagues drawn with add_headshots](https://raw.githubusercontent.com/sportsdataverse/sdvplot/main/docs/static/img/home/headshots-light.png) |
| One `add_logos()` call with `season=`: the mark Montreal used each season | `add_headshots()` with ESPN athlete ids, one player from each of five leagues |

## **Documentation**

The [**`sdvplot`** documentation website](https://sdvplot.sportsdataverse.org) has the
[getting started guide](https://sdvplot.sportsdataverse.org/docs/intro), the
[API reference](https://sdvplot.sportsdataverse.org/docs/reference) and the
[gallery](https://sdvplot.sportsdataverse.org/docs/gallery), plus:

**League tutorials:**
[NFL](https://sdvplot.sportsdataverse.org/docs/tutorials/leagues/nfl) ·
[CFB](https://sdvplot.sportsdataverse.org/docs/tutorials/leagues/cfb) ·
[NBA](https://sdvplot.sportsdataverse.org/docs/tutorials/leagues/nba) ·
[WNBA](https://sdvplot.sportsdataverse.org/docs/tutorials/leagues/wnba) ·
[MBB](https://sdvplot.sportsdataverse.org/docs/tutorials/leagues/mbb) ·
[WBB](https://sdvplot.sportsdataverse.org/docs/tutorials/leagues/wbb) ·
[MLB](https://sdvplot.sportsdataverse.org/docs/tutorials/leagues/mlb) ·
[NHL](https://sdvplot.sportsdataverse.org/docs/tutorials/leagues/nhl) ·
[PWHL](https://sdvplot.sportsdataverse.org/docs/tutorials/leagues/pwhl) ·
[Soccer](https://sdvplot.sportsdataverse.org/docs/tutorials/leagues/soccer) ·
[Cricket](https://sdvplot.sportsdataverse.org/docs/tutorials/leagues/cricket)

**Cookbooks:**
[Matplotlib logos](https://sdvplot.sportsdataverse.org/docs/cookbooks/matplotlib-logos) ·
[Colors and themes](https://sdvplot.sportsdataverse.org/docs/cookbooks/colors-and-themes) ·
[Tables](https://sdvplot.sportsdataverse.org/docs/cookbooks/tables) ·
[Interactive web](https://sdvplot.sportsdataverse.org/docs/cookbooks/interactive-web) ·
[plotnine](https://sdvplot.sportsdataverse.org/docs/cookbooks/plotnine) ·
[Surfaces and shot charts](https://sdvplot.sportsdataverse.org/docs/cookbooks/surfaces-and-shot-charts)

**Recipes, leaderboards and automation:**
[Head-to-head card](https://sdvplot.sportsdataverse.org/docs/recipes/head-to-head-card) ·
[CFB conference table](https://sdvplot.sportsdataverse.org/docs/recipes/cfb-conference-table) ·
[NFL weekly leaderboard](https://sdvplot.sportsdataverse.org/docs/leaderboards/nfl-weekly) ·
[Social game-day graphics](https://sdvplot.sportsdataverse.org/docs/automation)

The [changelog](https://github.com/sportsdataverse/sdvplot/blob/main/CHANGELOG.md) lists every release, and
[contributing](https://github.com/sportsdataverse/sdvplot/blob/main/CONTRIBUTING.md) covers development.

### Environment variables

- `SDVPLOT_CACHE_DIR`: cache root.
- `SDVPLOT_CACHE_TTL`: cache lifetime in days (default 7).
- `SDVPLOT_LIVE_TESTS=1`: enable the network tests.

## **Logos, trademarks and data**

Team names, logos, wordmarks and player headshots are trademarks or copyrighted works of their respective leagues,
teams, schools and other rights holders. sdvplot is not affiliated with, sponsored by or endorsed by any of them, and
using sdvplot to draw a mark grants no right to use it. The package ships no logo files: the wheel carries only an
index of team names, ids and colors, and marks are fetched at runtime from the
[SportsDataverse logo archive](https://github.com/sportsdataverse/sdv-assets), headshots from ESPN (or, for NFL gsis
ids, the URLs in nflverse's player table). Use of any mark in your own work is
governed by that owner's terms, and following them is your responsibility. The [MIT license](https://github.com/sportsdataverse/sdvplot/blob/main/LICENSE)
covers the sdvplot code only; team data belongs to its respective owners and sources.

## **The SportsDataverse**

`sdvplot` draws the pictures; the companion packages fetch the data.

| Package | Sport / Scope |
| --- | --- |
| [**sportsdataverse-py**](https://py.sportsdataverse.org/) | SportsDataverse data for Python: NFL, CFB, NBA, WNBA, MBB, WBB, MLB, NHL, PWHL, soccer and more |
| [**sdvplotR**](https://sdvplotR.sportsdataverse.org/) | The R package this one mirrors |
| [**sdvplot-js**](https://plot.sportsdataverse.org/) | The JavaScript port: `@sportsdataverse/sdvplot`, `@sportsdataverse/sporty` and `@sportsdataverse/sdvtables` on npm |
| [**sportypy**](https://sportypy.sportsdataverse.org/) | Playing-surface plots for Python |
| [**nflreadpy**](https://github.com/nflverse/nflreadpy) | nflverse data loaders for Python |
| [**sportsdataverse-R**](https://r.sportsdataverse.org/) · [**sportsdataverse.js**](https://js.sportsdataverse.org/) | R and Node.js |

See the full ecosystem at [sportsdataverse.org](https://sportsdataverse.org/).

## **Follow the [SportsDataverse](https://x.com/SportsDataverse) on X and star this repo**

[![Twitter Follow](https://img.shields.io/twitter/follow/SportsDataverse?color=blue&label=%40SportsDataverse&logo=x&style=for-the-badge)](https://x.com/SportsDataverse)
[![GitHub stars](https://img.shields.io/github/stars/sportsdataverse/sdvplot.svg?color=eee&logo=github&style=for-the-badge&label=Star%20sdvplot&maxAge=2592000)](https://github.com/sportsdataverse/sdvplot/stargazers/)

## **Our Authors**

- [Saiem Gilani](https://x.com/saiemgilani)
  <a href="https://x.com/saiemgilani" target="blank"><img src="https://img.shields.io/twitter/follow/saiemgilani?color=blue&label=%40saiemgilani&logo=x&style=for-the-badge" alt="@saiemgilani" /></a>
  <a href="https://github.com/saiemgilani" target="blank"><img src="https://img.shields.io/github/followers/saiemgilani?color=eee&logo=Github&style=for-the-badge" alt="@saiemgilani" /></a>

## **Citations**

To cite [**`sdvplot`**](https://sdvplot.sportsdataverse.org) in publications, use:

BibTeX Citation

```bibtex
@misc{gilani_2026_sdvplot,
  author = {Gilani, Saiem},
  title = {sdvplot: Team logos, wordmarks, headshots and colors for Python plots and tables},
  url = {https://sdvplot.sportsdataverse.org},
  year = {2026}
}
```

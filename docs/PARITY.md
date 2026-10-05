<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [sdvplotR parity extras](#sdvplotr-parity-extras)
  - [Ported](#ported)
  - [Team index](#team-index)
  - [Recipes](#recipes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# sdvplotR parity extras

How the sdvplotR (and ggpath) exports that the core, matplotlib-family, web and table sub-projects did not cover map to
sdvplot: a Python function where one carries real value, a recipe where a few lines of the plotting library do the job.
A contributor reference, not a docs-site page. The table ports live in [`PARITY_TABLES.md`](PARITY_TABLES.md).

| # | sdvplotR / ggpath export | sdvplot | Decision |
| --- | --- | --- | --- |
| X1 | `sdv_court_coords()` | `sdvplot.court_coords(data, x="x_legacy", y="y_legacy")` | ported (below) |
| X2 | `ggtitle_image()` + `theme_title_image()` | `sdvplot.matplotlib.title_image()`, `sdvplot.plotnine.title_image()` | ported (below) |
| X3 | `sdv_team_tiers()` | `sdvplot.matplotlib.team_tiers()`, `sdvplot.plotnine.team_tiers()` | ported (below) |
| X4 | ggpath `geom_from_path()` | `sdvplot.plotnine.geom_from_path()`, `sdvplot.matplotlib.add_images()` | ported (below) |
| X5 | ggpath `geom_mean_lines()`, `geom_median_lines()` | `sdvplot.plotnine.geom_mean_lines()`, `geom_median_lines()` | ported (below) |
| X6 | ggpath `element_path()`, `element_raster()` | recipe | not ported: `axis_logos` covers team marks |
| X7 | `team_reference()` | recipe | not ported: `teams()` and `logo_url()` / `marks()` hold the same data |
| X8 | `sdv_team_factor()` | recipe | not ported: three lines over `resolve()` |
| X9 | mean/median lines on matplotlib | recipe | not ported: `ax.axvline` is one line |

## Ported

**X1 `court_coords`.** The same arithmetic as sdvplotR (`court_x = -47 + 5.25 + y / 10`, `court_y = x / 10`) and the
same validation, on a pandas or polars frame (the same type comes back). Checked bit for bit against
`sdv_court_coords()` on 40 real `shotchartdetail` rows (`tests/fixtures/sdvplotr_court_coords.csv`). Differences:
a non-string `x`/`y` and a non-frame `data` raise `TypeError` (R raises one error class for everything); the
arguments are `x`/`y`, not `x_column`/`y_column`.

**X2 `title_image`.** One call per adapter instead of `ggtitle_image()` plus a markdown title theme: matplotlib sets
the Axes title (or a Figure's suptitle) and anchors the image to that title text, plotnine is added with `+`. A team
(with `league=`) or any image by URL or path; `height` is in points (sdvplotR: pixels in the `<img>` tag). sdvplotR
puts the image inside the title, so the pair is aligned as one; sdvplot shifts the title text by the image's width at
each draw to match (a centred title centres the pair, a left-aligned one starts with the image), through later
`set_title` calls. A second call on the same title replaces the image. Differences: an image taller than the title
line does not make the line taller (give it room with `pad=` or `y=` in matplotlib, a `plot_title` margin in
plotnine); an image by URL or path that cannot be read warns once and the title is drawn without it, while a team
logo that cannot be downloaded raises `OfflineError`, as in `add_logos`; in plotnine the image is loaded (and an
unknown team warned about) when `title_image()` is built.

**X3 `team_tiers`.** sdvplotR's arguments, look and dark theme, with `height` (a fraction of the panel height) for
`width`; matplotlib returns a Figure, plotnine a ggplot, both drawn from one preparation (`sdvplot._tiers`). As in
sdvplotR, teams are ranked before they are resolved, so an unknown team warns once and leaves its slot empty;
`presort=True` sorts a missing team last; tier labels wrap as `strwrap(label, 15)` does; `devel=True` draws the
resolved abbreviation. The default `height`, 0.1, is about the largest height at which 32 logos in 5 tiers (7,
7, 6, 6, 6) neither overlap nor leave the panel at the default 6.4 x 4.8 in figure (about sdvplotR's
`width = 0.075` npc). Differences: a tier with no `tier_desc` entry gets no label (sdvplotR shows "NA"); a null
`tier_no` or `tier_rank` is skipped with one warning; non-numeric tiers raise `TypeError`; the matplotlib title and
subtitle sit over the panel (sdvplotR: `plot.title.position = "plot"`, which the plotnine version keeps); there is
no `season`.

**X4 `geom_from_path` / `add_images`.** Images are sized like sdvplot's logo verbs: `height` is a fraction of the
panel (Axes) height, default 0.1, and the image keeps its aspect ratio. ggpath's `width`, `angle`, `hjust`, `vjust` and
`colour` aesthetics are not ported. URLs are cached like headshots; SVG files are not read. An image that cannot be
read skips its points with one `SdvplotWarning`, the verbs' rule.

**X5 `geom_mean_lines` / `geom_median_lines`.** ggpath's defaults (red, size 0.5, dashed) and its missing-value rule:
with `na_rm=False` a panel whose values include a missing one draws no line on that axis and warns; `na_rm=True` ignores
missing values. Per-panel values match ggpath 1.1.1 on the same real rows faceted by shot zone
(`tests/fixtures/ggpath_ref_lines.csv`). As ggplot2's hline/vline do, a panel gets one segment per distinct group and
line style (colour, size, linetype, alpha), all at the panel's value: one line, or one per group when a colour is
mapped. `alpha` defaults to 1 (plotnine has no `NA` alpha; an 8-digit hex color keeps its own alpha either way). As in
ggplot2, where they are position aesthetics, `x0`/`y0` go through each panel's position scale before the mean: a log
scale averages the logs, and values outside the scale's limits become missing (so `na_rm=True` leaves them out, and
`na_rm=False` draws no line). Unlike ggplot2 they do not train the scale, so a reference value outside the plotted
data's range is not brought into view.

## Team index

sdvplotR's `clean_team_abbrs()` keys resolve as their canonical abbreviation does (`tests/test_sdvplotr_parity.py`),
except where a dated source disagrees: sdvplotR's keys have no seasons, so a key that a dated alias gives another
team is dropped.

- **`KCA` (MLB).** The MLB Stats API and Baseball-Reference use it for the 1955-67 Kansas City Athletics, so sdvplot
  resolves it to the Athletics in every season; sdvplotR follows Lahman, whose `KCA` is the Royals. The Royals'
  internal MLB Stats teamCode `kca` is not an alias either.
- **`WAS` (MLB).** The MLB Stats API's abbreviation for the Senators of 1901-60 (now the Twins) and of 1961-71 (the
  Rangers); sdvplotR maps it to the Nationals (`WSH`). With a season in either range sdvplot picks that franchise;
  without one, or in another season, it is ambiguous (`None` and one `SdvplotWarning`). Use `WSH` or `WSN` for the
  Nationals.

Known gaps in the archive (recorded, not invented):

- **UFL Houston, 2024-25.** ESPN id 126075 was the Houston Roughnecks in 2024 and 2025 and is the Houston Gamblers
  from 2026, but the archive holds only the Gamblers marks for it (one undated set, one dated 2026), so any season
  gets the Gamblers logo. The archive's Roughnecks mark belongs to the XFL Roughnecks (league `xfl`, ESPN id 112648,
  2020-23); marks are looked up within a league, and nothing establishes that the UFL team used that logo, so it is
  not wired to the UFL team.

## Recipes

**X6 images as axis labels** (`element_path` / `element_raster`). Team marks: `sdvplot.axis_logos(target, "x",
league=...)`. Any other image under a matplotlib tick:

```python
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image

img = OffsetImage(Image.open("label.png"), zoom=0.2)
ax.add_artist(AnnotationBbox(img, (tick_x, 0), xycoords=ax.get_xaxis_transform(), box_alignment=(0.5, 1.0),
                             xybox=(0, -4), boxcoords="offset points", frameon=False, annotation_clip=False))
```

**X7 `team_reference`.** Identity and colors: `sdvplot.teams("nfl")` (`team_id`, `abbr`, `name`, `short_name`,
`location`, `conference`, `color_primary`, `color_secondary`). Image URLs: `sdvplot.logo_url(team, "nfl")`
(`variant="dark"`, `mark_type="wordmark"`), or every archived mark with `sdvplot.marks(team, "nfl")`.

**X8 `sdv_team_factor`.** Canonical abbreviations as a categorical whose levels are the sorted known teams; values
that are not teams become missing (with one `SdvplotWarning` from `resolve`):

```python
import pandas as pd
import sdvplot

abbr = dict(sdvplot.teams("nfl").select("team_id", "abbr").iter_rows())
cleaned = [abbr.get(i) for i in sdvplot.resolve(values, "nfl")]
team = pd.Categorical(cleaned, categories=sorted({a for a in cleaned if a}))
```

**X9 matplotlib mean/median lines.** ggpath's look on an Axes:

```python
import numpy as np

style = {"color": "red", "linestyle": "--", "linewidth": 0.5 * 72.27 / 25.4}  # ggplot2's 0.5 mm
ax.axvline(np.nanmean(x), **style)
ax.axhline(np.nanmedian(y), **style)
```

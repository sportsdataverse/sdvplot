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
| X1 | `sdv_court_coords()` | `sdvplot.court_coords(data, *, x="x_legacy", y="y_legacy")` | ported (below) |
| X2 | `ggtitle_image()` + `theme_title_image()` | `sdvplot.matplotlib.title_image()`, `sdvplot.plotnine.title_image()` | ported (below) |
| X3 | `sdv_team_tiers()` | `sdvplot.matplotlib.team_tiers()`, `sdvplot.plotnine.team_tiers()` | ported (below) |
| X4 | ggpath `geom_from_path()` | `sdvplot.plotnine.geom_from_path()`, `sdvplot.matplotlib.add_images()` | ported (below) |
| X5 | ggpath `geom_mean_lines()`, `geom_median_lines()` | `sdvplot.plotnine.geom_mean_lines()`, `geom_median_lines()` | ported (below) |
| X6 | ggpath `element_path()`, `element_raster()` | recipe | not ported: `axis_logos` covers team marks |
| X7 | `team_reference()` | recipe | not ported: `teams(include_conferences=)` and `logo_url()` / `marks()` hold the same data |
| X8 | `sdv_team_factor()` | recipe | not ported: three lines over `resolve()` |
| X9 | mean/median lines on matplotlib | recipe | not ported: `ax.axvline` is one line |
| X10 | `geom_sdv_logos()` / `geom_sdv_wordmarks()` / `geom_sdv_headshots()` aesthetics `colour`, `angle`, `hjust`, `vjust`, `width` | `sdvplot.plotnine.geom_sdv_*` | not ported (below): documented divergence, port on demand |
| X11 | `scale_color_sdv()` / `scale_fill_sdv()` `alpha`, `values`; `scale_colour_sdv()` | `sdvplot.plotnine.scale_color_sdv(alpha=)`, `scale_fill_sdv(alpha=)`, `scale_colour_sdv` | ported (below); `values` is plotnine's own `scale_color_manual(values=)` |
| X12 | `scale_x_sdv_headshots()`, `scale_y_sdv_headshots()`, `element_sdv_headshot()` | `axis_logos(target, axis, *, league, mark_type="headshot", height=0.1, id_system="auto")` on matplotlib, plotnine, Plotly and Altair | ported (below) |
| X13 | `include_conferences` (conference and league rows and marks) | `sdvplot.teams(league, include_conferences=True)` | ported (below): the 92 rows with cbbplotR colors; their marks follow once the archive holds them |
| X14 | league-id headshots (`id_type = "league"`: NBA, WNBA, MLB and NHL CDNs) | `headshot_url(..., id_system="league")` and every headshot helper | ported (below); the default id system still differs (`espn` for every league; R's NFL default is gsis) |
| X15 | `sdv_pitch_coords()` | `sdvplot.pitch_coords(data, *, provider, x=None, y=None, flip=None, pitch_length=None, pitch_width=None)` | ported (below) |

## Ported

**X1 `court_coords`.** The same arithmetic as sdvplotR (`court_x = -47 + 5.25 + y / 10`, `court_y = x / 10`) and the
same validation, on a pandas or polars frame (the same type comes back). Checked bit for bit against
`sdv_court_coords()` on 40 real `shotchartdetail` rows (`tests/fixtures/sdvplotr_court_coords.csv`). Differences:
a non-string `x`/`y` and a non-frame `data` raise `TypeError` (R raises one error class for everything); the
arguments are `x`/`y`, not `x_column`/`y_column`.

**X12 headshots as axis labels.** sdvplotR's `scale_x_sdv_headshots()` / `scale_y_sdv_headshots()` (and the
`element_sdv_headshot()` they draw with) are `axis_logos(..., mark_type="headshot")`: the same verb that puts logos
and wordmarks on a team axis reads the tick labels as player ids and draws each player's headshot at its own aspect
(ESPN serves 600 x 436), on every adapter that draws axis logos (matplotlib, plotnine, Plotly, Altair; the others
raise `UnsupportedTargetError` as for logos). An unknown id stays as text with one `SdvplotWarning`, as an unknown
team does. Differences: one verb with `mark_type` instead of two scales; `id_system` is `"espn"` (the default, also
what `"auto"` means), `"gsis"` or `"league"`, as `headshot_url` (sdvplotR defaults the NFL to GSIS ids); `height` is a fraction of the plot height, not `size` in points; on Plotly, numeric-looking
player ids need the axis declared `type="category"`, as Plotly itself would otherwise draw a linear axis.

**X15 `pitch_coords`.** One landmark table (`src/sdvplot/data/pitch_landmarks.csv`, byte-identical to sdvplotR's
`inst/extdata/pitch_landmarks.csv`; both test its SHA-256) and the same arithmetic (`searchsorted` for
`findInterval`), so sdvplot matches sdvplotR to 1e-12 on a grid of landmarks, midpoints, off-pitch points and
flipped rows of every provider (`tests/fixtures/sdvplotr_pitch_coords.csv`, from `tools/export_parity_extras.R`).
Differences: the column arguments are `x`/`y` (sdvplotR: `x_column`/`y_column`), keyword-only; nulls come back
as null in polars and NaN in plain pandas float columns; value errors raise `InputError`.

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
no `season`. `theme="light"` draws on white with dark lines and text, as sdvplotR's `theme = "light"` does (`"dark"`
is the default in both). `variant`, default `"auto"`, draws the archive's `"dark"` logo variant on the dark theme and
`"default"` on the light one; a team with no dark mark draws its default one. sdvplotR's `sdv_team_tiers()` does the
same since sdvplotR #62 (`variant = "auto"`, `R/team_tiers.R`), so dark logos (Toronto's, Iowa's, West Virginia's,
Penn State's) no longer vanish on either package's dark background; `variant="default"` reproduces the earlier look.

**X4 `geom_from_path` / `add_images`.** Images are sized like sdvplot's logo verbs: `height` is a fraction of the
panel (Axes) height, default 0.1, and the image keeps its aspect ratio. ggpath's `width`, `angle`, `hjust`, `vjust` and
`colour` aesthetics are not ported. URLs are cached like headshots; SVG files are not read. An image that cannot be
read skips its points with one `SdvplotWarning`, the verbs' rule.

**X10 `geom_sdv_*` aesthetics.** sdvplotR's `geom_sdv_logos()`, `geom_sdv_wordmarks()` and `geom_sdv_headshots()`
take ggpath's `colour` (a tint: `"b/w"` draws the mark in greyscale, any other colour tints it), `angle` (rotation in
degrees), `hjust` / `vjust` (the anchor within the image, 0.5 centred) and `width` (npc, `height` follows the aspect
ratio) as aesthetics, so each row can carry its own. `sdvplot.plotnine.geom_sdv_*` draw the mark untinted, unrotated
and centred, with one `height` parameter (a fraction of the panel height; `width` follows the aspect ratio) and `alpha`
for the whole layer; they add `variant`, `id_system` and a `season=` parameter sdvplotR has not. The aesthetics are
documented here and not ported: a tinted or rotated logo has not come up; port on demand.

**X14 league-id headshots.** `id_system="league"` is sdvplotR's `id_type = "league"`: the player id the league's own
API gives (an NBA or WNBA Stats `PERSON_ID`, as nba_api, hoopR and wehoop return it; an MLBAM id; an NHL API id; the
NFL's gsis id, where it is the same as `id_system="gsis"`), drawn from the league's CDN with the URL templates of
`league_headshot_url` (utils.R): `cdn.nba.com/headshots/nba/latest/260x190/{id}.png`, `cdn.wnba.com/headshots/wnba/
latest/260x190/{id}.png`, `img.mlbstatic.com/.../v1/people/{id}/headshot/67/current.png` and
`assets.nhle.com/mugs/nhl/latest/{id}.png`. Every headshot entry point takes it: `headshot_url`, `add_headshots` on
every adapter, `geom_sdv_headshots`, `gt_sdv_headshots`, `gt_sdv_cols_label(mark_type="headshot")`,
`reactable_sdv_headshots` and `plottable.headshot_column`. As in R, an unknown id gets the CDN's silhouette (no 404),
and a league without league-id headshots (cfb, mbb, wbb) is an `InputError` naming the ones that have them. The
remaining divergence is the default: `id_system="espn"` for every league, where R's NFL helpers read ids as gsis unless
`id_type = "espn"`. cdn.nba.com and cdn.wnba.com answer 403 to datacenter and cloud IPs, so a raster adapter drawn on
CI or a server raises `DownloadError` naming that cause (the web adapters link the URL and leave the fetch to the
browser); the live test skips on a 403.

**X11 `scale_color_sdv` / `scale_fill_sdv`.** `alpha` fades the team colors (sdvplotR applies `scales::alpha()`;
sdvplot appends the alpha byte, `#rrggbbaa`) and leaves `na_value` as given, as R leaves `na.value`; `scale_colour_sdv`
is the British alias both packages ship. R's `type` is `which` (keyword-only), `na.value = "grey50"` is
`na_value="grey"`, and R's `values` override is plotnine's own `scale_color_manual(values=)`: the sdvplot scales map
any id system and season lazily when the plot is drawn, so a fixed `values` dict is not an argument.

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

sdvplotR's `clean_team_abbrs()` keys resolve as their canonical abbreviation does (`tests/test_sdvplotr_parity.py`,
against the sdvplotR commit in `data-raw/sdvplotr_commit.txt`): 4,233 of 4,240, every miss a place several teams share
(`CHICAGO`, `NEW YORK`, CFBD's two `CHARLOTTE`s), which sdvplotR gives its first team and sdvplot never guesses. Its
`resolve_historical_abbr()` keys resolve to the franchise today, looked up as sdvplotR does since its #55 (the
relocation table first, then its target through `abbr_mapping`); the one exception is `WIN` below. Where both hold a
team's colors, they agree (sdvplotR #63 takes sdvplot's for the teams ESPN gives none). sdvplotR's keys have no seasons,
so a key that a dated source gives another team earlier starts the season after that team's last; a value given without
a season means its current holder. Two MLB codes and one NHL code show the rule:

- **`KCA`.** The MLB Stats API and Baseball-Reference use it for the 1955-67 Kansas City Athletics; the API's Royals
  teamCode `kca`, Lahman and sdvplotR use it for the Royals from 1968. sdvplot gives 1955-67 to the Athletics and
  every other season, and no season, to the Royals.
- **`WAS`.** The MLB Stats API's abbreviation for the Senators of 1901-60 (now the Twins) and 1961-71 (the Rangers),
  and the Nationals' teamCode `was` from 2005 (Lahman and sdvplotR agree). Those seasons go to those franchises; no
  season, or any other, goes to the Nationals.
- **`WIN`.** The NHL stats API's code (and team id 33) for the original Winnipeg Jets, 1979-80 to 1995-96, which it
  files under today's Jets' franchise (35). The team that played those seasons became the Phoenix Coyotes, then the
  Arizona Coyotes, whose line is Utah's (`records.nhl.com` franchise season results; the NHL consolidated the records
  into today's Jets on 2026-09-24, but the logos and colors of those seasons are the Coyotes line's). sdvplot gives the
  seasons 1980-1996 (the year a season ends, as everywhere in the index) to Utah, as sdvplotR's
  `resolve_historical_abbr()` does, and every other season, and no season, to today's Jets, the relocated Thrashers
  (2011-12 on), where sdvplotR, which has no seasons, gives a bare `WIN` to Utah; `WPG` is only today's Jets.

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
ax.add_artist(
    AnnotationBbox(
        img,
        (tick_x, 0),
        xycoords=ax.get_xaxis_transform(),
        box_alignment=(0.5, 1.0),
        xybox=(0, -4),
        boxcoords="offset points",
        frameon=False,
        annotation_clip=False,
    )
)
```

**X7 `team_reference`.** Identity and colors: `sdvplot.teams("nfl")` (`team_id`, `abbr`, `name`, `short_name`,
`location`, `conference`, `color_primary`, `color_secondary`; `include_conferences=True` adds R's `type != "team"`
rows, see X13). Image URLs: `sdvplot.logo_url(team, "nfl")` (`variant="dark"`, `mark_type="wordmark"`), or every
archived mark with `sdvplot.marks(team, "nfl")`.

**X13 `include_conferences`.** sdvplotR's `logo_ref` holds 92 rows that are not teams (`type` `"conference"` or
`"league"`: 25 CFB, 32 MBB and 32 WBB conferences, the AFC, NFC and NFL), keyed by the conference's ESPN short name,
with cbbplotR's colors and ESPN's conference logo URLs, listed by `team_reference()` / `valid_team_names()` only with
`include_conferences = TRUE` and drawn by every geom. `tools/export_sdvplotr.R` writes them to
`data-raw/sdvplotr_conferences.csv`, and `tools/build_index.py` (`conference_rows`) adds them to the one team index
after the team rows, so `teams(league, include_conferences=True)` lists them. Decision: the same table, not a second
one, because the rows share every column and the opt-in keeps every consumer unchanged; `program` carries R's `type`
(`"conference"` / `"league"`); `team_id` and `abbr` are R's key (`"SEC"`, `"Big 12"`, `"AFC"`: never a number, so no
team id is met); `conference_id` is the league's group slug where the team rows name the same conference, so a team
joins its conference row on it (the retired WAC has none; R's "Atlantic Sun Conference" and "Summit League" are the
groups snapshot's "ASUN Conference" and "The Summit League", `CONFERENCE_NAMES`); `conference` is the row's own full
name; colors are the snapshot's with `color_source` `"cbbplotR"` (85 rows), the placeholder rule for the 7 R has none
for (`"fallback"`), a secondary equal to its primary dropped as for teams (`tests/test_real_index.py`). The rows have
no aliases: `resolve()`, `palette()`, `team_colors()` and every mark helper see teams only (`team_table()`), so no
existing call changes meaning (CFB's `MAC` is Macalester, as before, not the Mid-American Conference). Not drawn yet:
the logo archive holds no conference or league marks (`data-raw/manifest_marks.csv` has no `ncaa_conf`, `afc`, `nfc`
or `leagues/nfl` entries), and sdvplot ships no live-CDN URLs, so `logo_url("SEC", "cfb")` stays `None` until the
archive adds the 92 marks the CSV's `logo_url` / `logo_dark_url` columns list; then `mark_aliases` needs the
conference rows as known ids and the resolver an opt-in for conference keys.

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

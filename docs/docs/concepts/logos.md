---
title: Logos
sidebar_label: Logos
---

# Logos

## The archive

Logos and wordmarks come from **sdv-assets**, the SportsDataverse logo archive. Its manifest lists every archived mark
with its team, mark type, variant, season range and source:

```text
https://sdv.nyc3.cdn.digitaloceanspaces.com/assets/public/manifest/marks.csv
```

The manifest has about 44,000 rows, nearly all of them team marks. sdvplot downloads it on first use and refreshes it
from the [cache](cache.md) when it goes stale.

The images are **content-addressed**: each `archive_url` is named by the file's sha256, such as
`.../assets/public/sha256/94/94de716e....png`. An image at a URL never changes, so sdvplot downloads it once, checks it
against its sha256 and keeps it.

## Listing candidates

`marks()` returns every archived mark for one team, best first. That covers logos and wordmarks, every variant and every
source:

```python
import sdvplot

m = sdvplot.marks("LV", "nfl")
m.select("entity_id", "mark_type", "variant", "source", "valid_from", "valid_to", "archive_url")
```

The columns include `mark_type` (`"logo"` or `"wordmark"`), `variant`, `source`, `ext` and `source_rank`. They also
include `valid_from` and `valid_to`, each row's effective season range, which is null when the mark is current. For the
Raiders, the `OAK` rows carry `1960`-`2019`, and the current Las Vegas rows are undated.

## How a mark is chosen

`logo_url(team, league, season=None, variant="default", mark_type="logo")` and `logo_image()` pick one row:

1. **Variant.** sdvplot tries the requested variant first, then a fallback that keeps the background polarity:
   - for `"default"` or any other named variant, `"default"` and then an on-light variant (`"on_light"` or
     `"*_on_light"`);
   - for `"dark"`, an on-dark variant (`"on_dark"` or `"*_on_dark"`) and then `"default"`;
   - then any variant.
2. **Season**, within each variant step: a dated mark whose range covers the season, then an undated (current) mark,
   else that step's best mark of any era. Without a season, the best mark wins, and current marks rank first.
3. **Source preference**, among the marks left:
   - ESPN first;
   - then league sources (nflverse, NHL, mlbstatic, FOX);
   - then HockeyTech and Cricinfo;
   - then NCAA.com;
   - then archived copies (nwhl.co, ShiftStats, Wayback);
   - then other sources;
   - derived crops (AAF) last.

   Within a source, current marks come before older ones.

MLB wordmarks show the polarity fallback. The archive has no `"default"` MLB wordmark, only `on_light` and `on_dark`
SVGs from mlbstatic:

```python
sdvplot.logo_url("NYY", "mlb", mark_type="wordmark")                  # the on_light wordmark (.svg)
sdvplot.logo_url("NYY", "mlb", mark_type="wordmark", variant="dark")  # the on_dark wordmark (.svg)
```

An unknown team gives `None` with the resolver's `SdvplotWarning`. A known team with no mark of that type also gives
`None`, and `logo_url()` warns about it. [Seasons and eras](seasons-and-eras.md) shows the season step on relocated franchises.

## The `mark` crosswalk

Manifest rows name their team with the **source's own id** (`entity_id`): `espn:13` and `espn:OAK` are both Raiders
rows, and `nflverse:LV` is a third. Those ids are not canonical team ids, so sdvplot never matches on them directly.

Instead, the bundled index has `mark` aliases that map each `source:entity_id` to one canonical `team_id`. A manifest row
reaches a team only through such an alias, and a row whose key maps to more than one team is dropped. A mark alias can
also carry a season range, which dates a row the manifest leaves undated. That is how the `espn:OAK` and
`nflverse:OAK` marks get their 1960-2019 range.

## SVG marks and web libraries

Some sources publish SVGs: mlbstatic (MLB and MiLB), the NHL, NCAA.com and ShiftStats (PHF).

- `logo_url()` returns the archive URL whatever its format. Web libraries (Plotly, Altair, Bokeh, great_tables, Folium)
  take URLs, so they need nothing else.
- `logo_image()` returns a decoded PIL image for matplotlib-style libraries. To decode an SVG it needs the `[svg]` extra
  (resvg-py), and without it it raises `OptionalDependencyError` naming `pip install sdvplot[svg]`. SVGs are rendered
  with their longest side at `size` pixels (default 512), and each rendering is cached. Raster images are only ever
  scaled down to `size`.

```python
img = sdvplot.logo_image("LV", "nfl", size=128)   # a 128x128 RGBA PIL image
```

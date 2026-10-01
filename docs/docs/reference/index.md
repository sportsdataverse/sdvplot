---
title: API reference
sidebar_label: Overview
sidebar_position: 0
---

# API reference

## Teams

- [`resolve`](resolve.md): Canonical team_id(s) for team values in one league.
- [`suggest`](suggest.md): Up to n (team_id, name) candidates for a value that did not resolve, best first.
- [`teams`](teams.md): The bundled team index: one row per (league, team_id), with names, abbreviation, conference and colors.

## Colors

- [`palette`](palette.md): A ``{team: "#hex"}`` dict for a league, ready for seaborn, Plotly, Altair, Bokeh or PyPalettes.
- [`team_colors`](team_colors.md): One "#hex" (or None) per team value, in the same container the values came in.

## Logos and headshots

- [`logo_url`](logo_url.md): The CDN URL of a team's logo or wordmark, chosen for the season.
- [`logo_image`](logo_image.md): The team's mark as a PIL image (downloaded once, then cached).
- [`marks`](marks.md): Every archived mark for one team, best first.
- [`headshot_url`](headshot_url.md): A headshot URL for one player.

## Plots and tables

- [`add_logos`](add_logos.md): Add team logos to a plot or table of any supported library.
- [`add_wordmarks`](add_wordmarks.md): Add team wordmarks to a plot or table of any supported library.
- [`add_headshots`](add_headshots.md): Add player headshots to a plot or table of any supported library.
- [`axis_logos`](axis_logos.md): Replace an axis' team labels with team logos on a plot of any supported library.

## Housekeeping

- [`versions`](versions.md): What a bug report needs: the package version, the bundled-index version, and the cached manifest's date.
- [`clear_cache`](clear_cache.md): Delete everything sdvplot has cached (manifest, images, rasterized SVGs).

## Errors and warnings

- [Errors and warnings](errors.md)

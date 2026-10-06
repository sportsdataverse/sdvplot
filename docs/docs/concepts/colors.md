---
title: Colors
sidebar_label: Colors
---

# Colors

Each team in the bundled index has a `color_primary`, a `color_secondary` and a `color_source`. sdvplot hands colors
out as plain `"#rrggbb"` strings, so no plotting library needs an adapter for them.

## `palette()`

`palette(league, teams=None, *, which="primary", season=None, id_system="auto", strict=False)` returns a
`{team: "#hex"}` dict.

**With `teams`,** the keys are your own values, exactly as you passed them. That way the dict matches a seaborn `hue`
column or a Plotly color column without any renaming:

```python
import sdvplot

sdvplot.palette("nfl", teams=["KC", "SF"])  # {'KC': '#e31837', 'SF': '#aa0000'}
sdvplot.palette("nfl", teams=["Kansas City Chiefs", 12])  # {'Kansas City Chiefs': '#e31837', 12: '#e31837'}
```

```python
import pandas as pd
import seaborn as sns

df = pd.DataFrame({"team": ["KC", "SF"], "wins": [15, 6]})  # the 2024 regular season
sns.barplot(data=df, x="team", y="wins", hue="team", palette=sdvplot.palette("nfl", teams=df["team"]))
```

**Without `teams`,** you get the whole league, keyed by canonical abbreviation. A team with no abbreviation is keyed by
its `team_id`, as in the OHL, and so is a team whose abbreviation another team of the league shares (with one
`SdvplotWarning` naming the shared abbreviations):

```python
nfl = sdvplot.palette("nfl")  # 32 entries: {'ATL': '#a71930', ...}
ohl = sdvplot.palette("ohl")  # 27 entries keyed by team_id: {'1': '#ba8748', ...}
```

Teams that do not resolve, or have no color of that kind, are left out of the dict. The usual `SdvplotWarning` names
the values that did not resolve; with `strict=True` they raise `UnresolvedTeamError` instead. `id_system` names the id
system of `teams` when "auto" would read them as another one's (NHL stats ids need `id_system="nhl_id"`), as in
[Team identity](identity.md).

The same dict works elsewhere. With `p = sdvplot.palette("nfl", teams=...)`, pass `color_discrete_map=p` to Plotly
Express, `alt.Scale(domain=list(p), range=list(p.values()))` to Altair, or the keys and values to Bokeh's `factor_cmap`.

## `team_colors()`

`team_colors(league, teams, *, which="primary", season=None, id_system="auto", strict=False)` returns one color per
value, in the container you passed (see [Team identity](identity.md#containers)). It returns `None` where a team does not
resolve or has no color:

```python
sdvplot.team_colors("nfl", ["KC", "SF"])  # ['#e31837', '#aa0000']
sdvplot.team_colors("nfl", "KC", which="secondary")  # '#ffb612'
```

## `which`

`which="primary"` reads `color_primary`, and `which="secondary"` reads `color_secondary`. Any other value raises
`InputError` (a `ValueError`).

## `color_source`

| `color_source` | Where the colors come from | Leagues (bundled index) |
|---|---|---|
| `nflverse` | nflverse's team table | the NFL |
| `espn` | ESPN: its teams lists, else its per-team endpoint by the team's ESPN id. A college team with no color in its own sport takes its school's ESPN colors from another sport: the same school id at the same location, or, for college baseball and softball (which number their teams apart from the school), an exact display name and location that no other ESPN team has | MLB, NBA, NHL, WNBA and the UFL; most teams of soccer, CFB, MBB, WBB, the NBA G League, college baseball and softball, and the XFL; about half of college hockey |
| `logo` | the two dominant colors of the team's current archived logo, for a team no source publishes colors for | the HockeyTech leagues (PWHL, AHL, ECHL, OHL, WHL, QMJHL, USHL), MiLB, cricket, the PHF, the AAF and the USFL, and the remaining teams of the leagues above |
| `cbbplotR` | [cbbplotR](https://cbbplotr.aweatherman.com/)'s conference colors, through sdvplotR, on the conference rows `teams(include_conferences=True)` adds | 85 of the 92 conference and league rows (CFB, MBB, WBB) |
| `fallback` | a placeholder | two men's college hockey teams known only from ESPN scoreboards, SUNY Morrisville and Maryville (Mo): no archived logo, and no ESPN color in any sport; the AFC, NFC, NFL and the four CFB conference rows cbbplotR has no color for |

**ESPN's stand-in colors are not a team's.** ESPN gives hundreds of newer or smaller college programs black and
nothing else, and hundreds of soccer clubs black with its stock red (`#c60000`) or black on black. sdvplot counts those
pairs as no color, so such a team takes its school's colors from another ESPN sport, or its logo's. Black beside a
color of its own is kept.

**Logo colors are derived, not published.** The opaque pixels of the team's current default logo are grouped into a
dozen colors. The largest colored group is the primary and the next clearly different one the secondary; black, grays
and then white count only when the logo has too few colors. Where a team also has published colors, the logo's primary
is close to one of them (RGB distance under 60) for 68% of 4,214 teams, and for 94% of the 139 NFL, NBA, MLB, NHL and
WNBA teams. A logo can lead with a color the team does not: the Steelers' logo is red, blue and yellow.

**Fallback colors are placeholders, not team colors.** They come from a fixed colorblind-safe palette of ten colors.
The pick is a hash of `(league, team_id)`, so a team always gets the same color, but two teams can share one.
Check `color_source` before you show colors as team identity: `logo` colors approximate the team's, `fallback` ones
are not the team's at all.

```python
sdvplot.teams("ohl").select("name", "color_primary", "color_source").head(1)
# Brantford Bulldogs  #ba8748  logo
```

A team whose source gives a primary color but no secondary has a null `color_secondary`. One source's secondary is
never paired with another source's primary, a secondary equal to its primary is dropped, and a fallback secondary is
only filled in beside a fallback primary.

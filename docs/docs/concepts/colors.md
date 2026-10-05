---
title: Colors
sidebar_label: Colors
---

# Colors

Each team in the bundled index has a `color_primary`, a `color_secondary` and a `color_source`. sdvplot hands colors
out as plain `"#rrggbb"` strings, so no plotting library needs an adapter for them.

## `palette()`

`palette(league, teams=None, *, which="primary", season=None)` returns a `{team: "#hex"}` dict.

**With `teams`,** the keys are your own values, exactly as you passed them. That way the dict matches a seaborn `hue`
column or a Plotly color column without any renaming:

```python
import sdvplot

sdvplot.palette("nfl", teams=["KC", "SF"])                    # {'KC': '#e31837', 'SF': '#aa0000'}
sdvplot.palette("nfl", teams=["Kansas City Chiefs", 12])     # {'Kansas City Chiefs': '#e31837', 12: '#e31837'}
```

```python
import seaborn as sns

sns.barplot(data=df, x="team", y="epa", hue="team", palette=sdvplot.palette("nfl", teams=df["team"]))
```

**Without `teams`,** you get the whole league, keyed by canonical abbreviation. A team with no abbreviation is keyed by
its `team_id`, as in the OHL:

```python
nfl = sdvplot.palette("nfl")    # 32 entries: {'ATL': '#a71930', ...}
ohl = sdvplot.palette("ohl")    # 27 entries keyed by team_id: {'1': '#76b7b2', ...}
```

Teams that do not resolve, or have no color of that kind, are left out of the dict. The usual `SdvplotWarning` names
the values that did not resolve.

The same dict works elsewhere. With `p = sdvplot.palette("nfl", teams=...)`, pass `color_discrete_map=p` to Plotly
Express, `alt.Scale(domain=list(p), range=list(p.values()))` to Altair, or the keys and values to Bokeh's `factor_cmap`.

## `team_colors()`

`team_colors(league, teams, *, which="primary", season=None)` returns one color per value, in the container you passed
(see [Team identity](identity.md#containers)). It returns `None` where a team does not resolve or has no color:

```python
sdvplot.team_colors("nfl", ["KC", "SF"])              # ['#e31837', '#aa0000']
sdvplot.team_colors("nfl", "KC", which="secondary")   # '#ffb612'
```

## `which`

`which="primary"` reads `color_primary`, and `which="secondary"` reads `color_secondary`. Any other value raises
`ValueError`.

## `color_source`

| `color_source` | Where the colors come from | Leagues (bundled index) |
|---|---|---|
| `nflverse` | nflverse's team table | the NFL |
| `espn` | ESPN's team endpoints | MLB, NBA, NHL, WNBA, and the ESPN-covered teams of CFB, MBB, WBB, NBA G League, NCAA baseball and softball and the UFL |
| `fallback` | a placeholder | every team no source gives colors for: all of the HockeyTech leagues, MiLB, college hockey, soccer, cricket, the PHF, the AAF, the USFL and the XFL, and the teams ESPN has no colors for in the mixed leagues above |

**Fallback colors are placeholders, not team colors.** They come from a fixed colorblind-safe palette of ten colors.
The pick is a hash of `(league, team_id)`, so a team always gets the same color, but two teams can share one.
Check `color_source` before you show fallback colors as team identity:

```python
sdvplot.teams("ohl").select("name", "color_primary", "color_source").head(3)
# Brantford Bulldogs  #76b7b2  fallback
# ...
```

A team whose source gives a primary color but no secondary has a null `color_secondary`. A fallback secondary is only
filled in beside a fallback primary.

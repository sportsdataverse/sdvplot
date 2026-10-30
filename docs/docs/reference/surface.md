---
title: surface
sidebar_label: surface
sidebar_position: 14
---

# surface

<div class="sdv-signature">

```python
surface(
    league: str,
    team: Any = None,
    *,
    season: Any = None,
    ax: Any = None,
    center_logo: bool | float = False,
    **sportypy_kwargs: Any,
) -> Any
```

</div>

Draw the league's playing surface with sportypy, in a team's colors.

## Arguments

| Name | Type | Description |
|---|---|---|
| `league` | `str` | The SDV surface key: a team league ("nfl", "nba", "nhl", "pwhl", "cfb", "mlb", "ncaa_softball", "soccer" (a 105 x 68 m pitch, the frame pitch_coords() returns), ...) or a surface without team identities ("fiba", "fifa", "epl", "cfl", "iihf", "little_league", the lacrosse "nll", "pll", "ncaa_mlacrosse", the tennis "atp", "wta", "ncaa_tennis", the volleyball "fivb", "ncaa_volleyball", the curling "wcf", "curling_canada", ...). Every sportyR surface has a key; an unknown one lists them. |
| `team` | `Any` | A team to color the surface by (end zones, lane and apron, center line and boards; baseball, softball and soccer stay in their regulation colors, so the team shows through ``center_logo``); None for the plain surface. Only for a key that is an SDV team league. |
| `season` | `Any` | The season, for teams whose colors changed. |
| `ax` | `Any` | The matplotlib Axes to draw on; None makes a new figure. |
| `center_logo` | `bool \| float` | True to draw the team's logo at center ice / court / field (0.25 of the Axes height), or a height fraction. A baseball or softball field's origin is home plate, so there the logo goes in shallow center field, as in sdvplotR: at x = 0, midway between second base (``baseline_distance * sqrt(2)``) and the center-field fence, 0.15 x ``center_field_distance`` across (True; a fraction still sets the height), from the league's field parameters and ``field_updates``. On grass (football, soccer, baseball, softball) the logo is the team's dark-background variant, as in sdvplotR. |
| `**sportypy_kwargs` | `Any` | Passed to sportypy: ``display_range``, ``xlim``, ``ylim`` and ``rotation`` go to ``draw()``; the rest (``field_updates``, ``color_updates``, ``units``, ...) to the surface class. sportypy's ``x_trans`` / ``y_trans`` only shift the data plotted through sportypy's own surface methods onto the drawn surface; they do not move the surface or its center logo (unlike sportyR and sdvplotR, where they move the surface), so data drawn on the returned Axes must be in the surface's own frame. |

## Returns

`matplotlib.axes.Axes` — The Axes sportypy drew on.

## Raises

- `InputError`: (a ValueError) If sportypy has no surface for ``league``, or ``team`` is given for a key without team identities; and, when ``team`` is given, if ``season`` is not a year or is outside the seasons sdvplot knows for the league, or ``center_logo`` is a height outside (0, 1]. Without ``team``, ``season`` and ``center_logo`` are not used.
- `OptionalDependencyError`: If the surfaces extra (sportypy 1.2 or newer) is not installed, or ``team`` and ``center_logo`` are set and the team's logo is an SVG without the ``svg`` extra.
- `OfflineError`: If ``team`` and ``center_logo`` are set and the logo manifest or the team's logo is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status; an IntegrityError when it sends a file that does not match the manifest's sha256, or one PIL cannot decode).
- `UnsafeDownloadError`: (an OSError) If ``team`` and ``center_logo`` are set and a download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If ``team`` and ``center_logo`` are set and the manifest's sha256 or extension for the logo would put the file outside the cache directory.

## Example

```python
import sdvplot

ax = sdvplot.surface("nfl", "KC", center_logo=True)
```

## See also

- [sdvplotR sdv_surface()](https://sdvplotR.sportsdataverse.org/)
- [sportypy](https://sportypy.sportsdataverse.org/)

## Surface keys

The 59 keys `league` takes, in `sdvplot._surface.SURFACES`' order: the sport, the sportypy class drawn, and whether the key is an SDV team league, which takes a `team` (its colors on a basketball court, football field or hockey rink, and its logo through `center_logo`); a key that is not refuses one. sdvplotR's `surface_map` and sdvplot-js's `surfaces.ts` use the same keys.

| Key | Sport | sportypy class | Takes a team |
|---|---|---|---|
| `nfl` | football | `sportypy.surfaces.football.NFLField` | yes |
| `aaf` | football | `sportypy.surfaces.football.NFLField` | yes |
| `ufl` | football | `sportypy.surfaces.football.NFLField` | yes |
| `usfl` | football | `sportypy.surfaces.football.NFLField` | yes |
| `xfl` | football | `sportypy.surfaces.football.NFLField` | yes |
| `cfb` | football | `sportypy.surfaces.football.NCAAField` | yes |
| `cfl` | football | `sportypy.surfaces.football.CFLField` | no |
| `nfhs_football` | football | `sportypy.surfaces.football.NFHSField` | no |
| `nba` | basketball | `sportypy.surfaces.basketball.NBACourt` | yes |
| `nbagl` | basketball | `sportypy.surfaces.basketball.NBAGLeagueCourt` | yes |
| `wnba` | basketball | `sportypy.surfaces.basketball.WNBACourt` | yes |
| `mbb` | basketball | `sportypy.surfaces.basketball.NCAACourt` | yes |
| `wbb` | basketball | `sportypy.surfaces.basketball.NCAACourt` | yes |
| `fiba` | basketball | `sportypy.surfaces.basketball.FIBACourt` | no |
| `nfhs_basketball` | basketball | `sportypy.surfaces.basketball.NFHSCourt` | no |
| `mlb` | baseball | `sportypy.surfaces.baseball.MLBField` | yes |
| `milb` | baseball | `sportypy.surfaces.baseball.MiLBField` | yes |
| `ncaa_baseball` | baseball | `sportypy.surfaces.baseball.NCAAField` | yes |
| `little_league` | baseball | `sportypy.surfaces.baseball.LittleLeagueField` | no |
| `pony` | baseball | `sportypy.surfaces.baseball.PonyField` | no |
| `nfhs_baseball` | baseball | `sportypy.surfaces.baseball.NFHSField` | no |
| `ncaa_softball` | softball | `sportypy.surfaces.softball.NCAASoftballField` | yes |
| `nhl` | hockey | `sportypy.surfaces.hockey.NHLRink` | yes |
| `whl` | hockey | `sportypy.surfaces.hockey.NHLRink` | yes |
| `pwhl` | hockey | `sportypy.surfaces.hockey.PWHLRink` | yes |
| `ahl` | hockey | `sportypy.surfaces.hockey.AHLRink` | yes |
| `echl` | hockey | `sportypy.surfaces.hockey.ECHLRink` | yes |
| `ohl` | hockey | `sportypy.surfaces.hockey.OHLRink` | yes |
| `qmjhl` | hockey | `sportypy.surfaces.hockey.QMJHLRink` | yes |
| `ushl` | hockey | `sportypy.surfaces.hockey.USHLRink` | yes |
| `phf` | hockey | `sportypy.surfaces.hockey.PHFRink` | yes |
| `iihf` | hockey | `sportypy.surfaces.hockey.IIHFRink` | no |
| `nwhl` | hockey | `sportypy.surfaces.hockey.NWHLRink` | no |
| `ncaa_mhockey` | hockey | `sportypy.surfaces.hockey.NCAARink` | yes |
| `ncaa_whockey` | hockey | `sportypy.surfaces.hockey.NCAARink` | yes |
| `soccer` | soccer | `sportypy.surfaces.soccer.FIFAPitch` | yes |
| `fifa` | soccer | `sportypy.surfaces.soccer.FIFAPitch` | no |
| `epl` | soccer | `sportypy.surfaces.soccer.EPLPitch` | no |
| `mls` | soccer | `sportypy.surfaces.soccer.MLSPitch` | no |
| `nwsl` | soccer | `sportypy.surfaces.soccer.NWSLPitch` | no |
| `ncaa_soccer` | soccer | `sportypy.surfaces.soccer.NCAAPitch` | no |
| `nll` | lacrosse | `sportypy.surfaces.lacrosse.NLLField` | no |
| `pll` | lacrosse | `sportypy.surfaces.lacrosse.PLLField` | no |
| `world_lacrosse` | lacrosse | `sportypy.surfaces.lacrosse.WorldLacrosseField` | no |
| `ncaa_mlacrosse` | lacrosse | `sportypy.surfaces.lacrosse.NCAAMLacrosseField` | no |
| `ncaa_wlacrosse` | lacrosse | `sportypy.surfaces.lacrosse.NCAAWLacrosseField` | no |
| `usa_mlacrosse` | lacrosse | `sportypy.surfaces.lacrosse.USAMLacrosseField` | no |
| `usa_wlacrosse` | lacrosse | `sportypy.surfaces.lacrosse.USAWLacrosseField` | no |
| `atp` | tennis | `sportypy.surfaces.tennis.ATPCourt` | no |
| `wta` | tennis | `sportypy.surfaces.tennis.WTACourt` | no |
| `itf` | tennis | `sportypy.surfaces.tennis.ITFCourt` | no |
| `ita` | tennis | `sportypy.surfaces.tennis.ITACourt` | no |
| `usta` | tennis | `sportypy.surfaces.tennis.USTACourt` | no |
| `ncaa_tennis` | tennis | `sportypy.surfaces.tennis.NCAACourt` | no |
| `fivb` | volleyball | `sportypy.surfaces.volleyball.FIVBCourt` | no |
| `usa_volleyball` | volleyball | `sportypy.surfaces.volleyball.USAVolleyballCourt` | no |
| `ncaa_volleyball` | volleyball | `sportypy.surfaces.volleyball.NCAACourt` | no |
| `wcf` | curling | `sportypy.surfaces.curling.WCFSheet` | no |
| `curling_canada` | curling | `sportypy.surfaces.curling.CurlingCanadaSheet` | no |

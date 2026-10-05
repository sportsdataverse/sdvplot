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
| `league` | `str` | The SDV league key, e.g. "nfl", "nba", "nhl", "cfb", "soccer". |
| `team` | `Any` | A team to color the surface by (end zones, lane and apron, center line and boards); None for the plain surface. |
| `season` | `Any` | The season, for teams whose colors changed. |
| `ax` | `Any` | The matplotlib Axes to draw on; None makes a new figure. |
| `center_logo` | `bool \| float` | True to draw the team's logo at center ice / court / field (0.25 of the Axes height), or a height fraction. |
| `**sportypy_kwargs` | `Any` | Passed to sportypy: ``display_range``, ``xlim``, ``ylim`` and ``rotation`` go to ``draw()``; the rest (``field_updates``, ``color_updates``, ``units``, ...) to the surface class. |

## Returns

`matplotlib.axes.Axes` — The Axes sportypy drew on.

## Raises

- `InputError`: (a ValueError) If sportypy has no surface for ``league``; and, when ``team`` is given, if ``season`` is not a year or is outside the seasons sdvplot knows for the league, or ``center_logo`` is a height outside (0, 1]. Without ``team``, ``season`` and ``center_logo`` are not used.
- `OptionalDependencyError`: If the surfaces extra (sportypy) is not installed, or ``team`` and ``center_logo`` are set and the team's logo is an SVG without the ``svg`` extra.
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

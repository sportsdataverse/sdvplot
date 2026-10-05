---
title: logo_image
sidebar_label: logo_image
sidebar_position: 7
---

# logo_image

<div class="sdv-signature">

```python
logo_image(
    team: Any,
    league: str,
    *,
    season: Any = None,
    variant: str = 'default',
    mark_type: Literal['logo', 'wordmark'] = 'logo',
    size: int | None = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
) -> PIL.Image.Image | None
```

</div>

The team's mark as a PIL image (downloaded once, then cached).

## Arguments

| Name | Type | Description |
|---|---|---|
| `team` | `Any` | One team identifier (abbreviation, name, ESPN id, ...). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | A season year; None picks the current mark. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `mark_type` | `Literal['logo', 'wordmark']` | "logo" or "wordmark". |
| `size` | `int \| None` | The longest side in pixels, an int from 1 to 4096. Rasters are only scaled down; SVGs are rasterized at it (default 512). |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team``, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when the team does not resolve. |

## Returns

PIL.Image.Image | None: The image, or None when the team does not resolve or has no mark.

## Raises

- `TypeError`: If ``team`` is not a single value.
- `OptionalDependencyError`: If the mark is an SVG and the ``svg`` extra is not installed.
- `OfflineError`: If the download fails and no cached copy exists.
- `DownloadError`: (an OfflineError and an OSError) If the CDN answers with an error status (a 4xx or 5xx response) and no cached copy exists.
- `IntegrityError`: (a DownloadError) If the download does not match the manifest's sha256, or is not an image PIL can decode.
- `UnsafeDownloadError`: (an OSError) If the download is refused: larger than the byte cap, past the deadline, or redirected away from https.
- `UnsafeCachePathError`: (a ValueError) If the manifest's sha256 or extension for the mark would put the file outside the cache directory.
- `InputError`: (a ValueError) If ``league`` or ``id_system`` is unknown, ``mark_type`` is not "logo"/"wordmark", ``variant`` is a name no mark in the archive has, ``season`` is not a year or is outside the seasons sdvplot knows for the league, or ``size`` is not an int from 1 to 4096.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and the team does not resolve.
- `ValueError`: If an SVG cannot be parsed; an ``InputError`` if it is more than 64 times longer than it is wide.

## Example

```python
import sdvplot

img = sdvplot.logo_image("KC", "nfl", size=64)
img.size   # (64, 64)
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

---
title: logo_url
sidebar_label: logo_url
sidebar_position: 6
---

# logo_url

<div class="sdv-signature">

```python
logo_url(
    team: Any,
    league: str,
    *,
    season: Any = None,
    variant: str = 'default',
    mark_type: Literal['logo', 'wordmark'] = 'logo',
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
    strict: bool = False,
) -> str | None
```

</div>

The CDN URL of a team's logo or wordmark, chosen for the season.

Picks the requested variant (falling back to a default or polarity variant), then within each variant the archived
mark whose season range covers ``season`` (relocated franchises get their era's mark), then the most
authoritative source. Unknown teams return None with one SdvplotWarning.

## Arguments

| Name | Type | Description |
|---|---|---|
| `team` | `Any` | One team identifier (abbreviation, name, ESPN id, ...), or a conference or league row's key ("SEC", "Big 12", "AFC", "NFL": the ``team_id`` of ``teams(league, include_conferences=True)``), read after every team alias (cfb's "MAC" is Macalester). |
| `league` | `str` | The SDV league key, e.g. "nfl", "cfb", "nhl". |
| `season` | `Any` | A season year; None picks the current mark. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `mark_type` | `Literal['logo', 'wordmark']` | "logo" or "wordmark". |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | The id system of ``team``, as in ``resolve``: "auto" tries each in order; NHL stats ids need "nhl_id". |
| `strict` | `bool` | Raise UnresolvedTeamError instead of warning when the team does not resolve. |

## Returns

str | None: The archive URL (content-addressed, immutable), or None when no mark exists.

## Raises

- `TypeError`: If ``team`` is not a single value.
- `InputError`: (a ValueError) If ``league`` or ``id_system`` is unknown, ``mark_type`` is not "logo"/"wordmark", ``variant`` is a name no mark in the archive has (a typo; the message lists the league's variants), or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `UnresolvedTeamError`: (a ValueError) If ``strict=True`` and the team does not resolve.
- `OfflineError`: If the logo manifest cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, when the CDN answers with an error status).
- `UnsafeDownloadError`: (an OSError) If the manifest download is refused: larger than the byte cap, past the deadline, or redirected away from https.

## Example

```python
import sdvplot

sdvplot.logo_url("KC", "nfl")   # 'https://sdv.nyc3.cdn.digitaloceanspaces.com/assets/public/sha256/3d/3d77....png'
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

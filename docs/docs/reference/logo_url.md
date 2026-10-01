---
title: logo_url
sidebar_label: logo_url
sidebar_position: 6
---

# `logo_url`

```python
logo_url(team: Any, league: str, season: Any = None, variant: str = 'default', mark_type: str = 'logo') -> str | None
```

The CDN URL of a team's logo or wordmark, chosen for the season.

Picks the archived mark whose season range covers ``season`` (relocated franchises get their era's mark), then the
requested variant, then the most authoritative source. Unknown teams return None with one SdvplotWarning.

## Arguments

| Name | Type | Description |
|---|---|---|
| `team` | `Any` | One team identifier (abbreviation, name, ESPN id, ...). |
| `league` | `str` | The SDV league key, e.g. "nfl", "cfb", "nhl". |
| `season` | `Any` | A season year; None picks the current mark. |
| `variant` | `str` | "default", "dark", or a named variant from ``marks()``. |
| `mark_type` | `str` | "logo" or "wordmark". |

## Returns

str | None: The archive URL (content-addressed, immutable), or None when no mark exists.

## Raises

- `TypeError`: If ``team`` is not a single value.
- `ValueError`: If ``league`` is unknown or ``mark_type`` is not "logo"/"wordmark".

## Example

```python
import sdvplot

sdvplot.logo_url("KC", "nfl")   # 'https://sdv.nyc3.cdn.digitaloceanspaces.com/assets/public/sha256/3d/3d77....png'
```

## See also

sdvplotR ``logo_url``: https://sdvplotR.sportsdataverse.org/ ; sdv-py: https://py.sportsdataverse.org/

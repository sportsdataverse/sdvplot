---
title: marks
sidebar_label: marks
sidebar_position: 8
---

# marks

<div class="sdv-signature">

```python
marks(
    team: Any,
    league: str,
    *,
    season: Any = None,
    id_system: Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id'] = 'auto',
) -> polars.dataframe.frame.DataFrame
```

</div>

Every archived mark for one team, best first.

Manifest entity ids are per-source, so rows reach a team only through its "mark" aliases; rows without a unique
mapping are dropped, never matched on the raw id. ``valid_from``/``valid_to`` are each row's effective range: the
manifest's, narrowed by the mark alias's (an open side takes the alias's).

## Arguments

| Name | Type | Description |
|---|---|---|
| `team` | `Any` | One team identifier (abbreviation, name, ESPN id, ...). |
| `league` | `str` | The SDV league key, e.g. "nfl". |
| `season` | `Any` | A season year, used to resolve a reused code. |
| `id_system` | `Literal['auto', 'team_id', 'espn', 'espn_abbr', 'nhl', 'nflverse', 'mlbstats', 'nba_api', 'hockeytech', 'ncaa', 'pff', 'cricinfo', 'cfbd', 'bref', 'sportsipy', 'fangraphs', 'sdvplotr', 'name', 'nhl_id']` | "auto" or one id-system name, as in ``resolve``. |

## Returns

`polars.DataFrame` — One row per archived mark (logos and wordmarks, every variant and source) with its ``variant``, ``mark_type``, ``archive_url`` and ``source_rank``.

## Raises

- `TypeError`: If ``team`` is not a single value.
- `InputError`: (a ValueError) If ``league`` or ``id_system`` is unknown, or ``season`` is not a year or is outside the seasons sdvplot knows for the league.
- `UnresolvedTeamError`: (a ValueError) If the team is null or does not resolve.
- `OfflineError`: If the logo manifest cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, when the CDN answers with an error status).
- `UnsafeDownloadError`: (an OSError) If the manifest download is refused: larger than the byte cap, past the deadline, or redirected away from https.

## Example

```python
import sdvplot

sdvplot.marks("KC", "nfl").shape   # (19, 21)
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

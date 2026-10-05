---
title: headshot_url
sidebar_label: headshot_url
sidebar_position: 9
---

# headshot_url

<div class="sdv-signature">

```python
headshot_url(
    player_id: Any,
    league: str,
    *,
    id_system: Literal['espn', 'gsis'] = 'espn',
) -> str | None
```

</div>

A headshot URL for one player.

## Arguments

| Name | Type | Description |
|---|---|---|
| `player_id` | `Any` | One player id: an ESPN athlete id, or an nflverse gsis id. |
| `league` | `str` | The SDV league key. "espn" ids work for nfl, nba, wnba, mlb, nhl, cfb, mbb and wbb; "gsis" is NFL only. |
| `id_system` | `Literal['espn', 'gsis']` | "espn" (ESPN athlete id, any ESPN league) or "gsis" (mapped to ESPN through nflverse's player table, preferring nflverse's own headshot). |

## Returns

str | None: The image URL, or None when the id is missing, malformed, or not in the player table.

## Raises

- `InputError`: (a ValueError) If ``league`` has no ESPN headshots or ``id_system`` is not valid for ``league``.
- `OfflineError`: If ``id_system`` is "gsis" and the nflverse player table cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, when GitHub answers with an error status).
- `UnsafeDownloadError`: (an OSError) If ``id_system`` is "gsis" and the player table download is refused: larger than the byte cap, past the deadline, or redirected away from https.

## Example

```python
import sdvplot

sdvplot.headshot_url("3139477", "nfl")
# 'https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/3139477.png'
sdvplot.headshot_url("00-0033873", "nfl", id_system="gsis")   # Patrick Mahomes, an nfl.com URL ending .png
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

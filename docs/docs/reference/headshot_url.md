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
    id_system: Literal['espn', 'gsis', 'league'] = 'espn',
) -> str | None
```

</div>

A headshot URL for one player.

## Arguments

| Name | Type | Description |
|---|---|---|
| `player_id` | `Any` | One player id: an ESPN athlete id, an nflverse gsis id, or the league's own player id. |
| `league` | `str` | The SDV league key. "espn" ids work for nfl, nba, wnba, mlb, nhl, cfb, mbb, wbb, nbagl and soccer; "gsis" is NFL only; "league" works for nfl, nba, wnba, mlb, nhl and the 20 HockeyTech leagues (pwhl, ahl, echl, ohl, whl, qmjhl, ushl, sphl, chl, bchl, ajhl, sjhl, ojhl, cchl, gojhl, mhl, nojhl, vijhl, kijhl, mjhl). ESPN files G League (nbagl) photos with the NBA's, so a G League player's ESPN id is the one ESPN uses for him in the NBA. ESPN has photos for only part of the G League and soccer rosters. F1 drivers have none: formula1.com keys its photos by its own driver reference (``MAXVER01``), not a driver number or Jolpica ``driver_id``. |
| `id_system` | `Literal['espn', 'gsis', 'league']` | "espn" (ESPN athlete id, any ESPN league), "gsis" (mapped to ESPN through nflverse's player table, preferring nflverse's own headshot), or "league" (the league's own player id, sdvplotR's ``id_type = "league"``: an NBA or WNBA Stats ``PERSON_ID`` as nba_api / hoopR / wehoop return it, an MLBAM id, an NHL API id, or the ``player_id`` of a HockeyTech feed (the 20 HockeyTech leagues above) on ``assets.leaguestat.com``, on the league's CDN; for the NFL it is the gsis id, the same as "gsis"). An unknown NBA, WNBA, MLB or NHL id gets the CDN's silhouette image; an unknown ESPN or HockeyTech id is a 404, which the adapters treat as any missing image. |

## Returns

str | None: The image URL, or None when the id is missing, malformed, or not in the player table.

## Raises

- `InputError`: (a ValueError) If ``league`` has no ESPN headshots or ``id_system`` is not valid for ``league`` ("league" names the leagues that have league-id headshots).
- `OfflineError`: If ``id_system`` is "gsis" (or "league" on "nfl") and the nflverse player table cannot be downloaded and no cached copy exists (a DownloadError, also an OSError, when GitHub answers with an error status).
- `UnsafeDownloadError`: (an OSError) If ``id_system`` is "gsis" and the player table download is refused: larger than the byte cap, past the deadline, or redirected away from https.

## Example

```python
import sdvplot

sdvplot.headshot_url("3139477", "nfl")
# 'https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/3139477.png'
sdvplot.headshot_url("00-0033873", "nfl", id_system="gsis")   # Patrick Mahomes, an nfl.com URL ending .png
sdvplot.headshot_url(2544, "nba", id_system="league")   # LeBron James by his NBA Stats PERSON_ID
# 'https://cdn.nba.com/headshots/nba/latest/260x190/2544.png'
sdvplot.headshot_url(52, "pwhl", id_system="league")   # a PWHL player by her HockeyTech player_id
# 'https://assets.leaguestat.com/pwhl/240x240/52.jpg'
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

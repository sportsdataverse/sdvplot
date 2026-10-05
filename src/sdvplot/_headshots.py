"""Player headshot URLs: ESPN athlete ids directly, nflverse gsis ids through nflverse's player table."""

from __future__ import annotations

import functools
import io
from typing import TYPE_CHECKING, Any

from sdvplot._cache import MEMORY_CACHES, fetch_cached, safe_url
from sdvplot._errors import InputError, warn
from sdvplot._normalize import norm_value
from sdvplot._types import HeadshotIdSystem

if TYPE_CHECKING:
    import polars as pl
else:
    from sdvplot._lazy import pl

ESPN_HEADSHOT_LEAGUES = {
    "nfl": "nfl",
    "nba": "nba",
    "wnba": "wnba",
    "mlb": "mlb",
    "nhl": "nhl",
    "cfb": "college-football",
    "mbb": "mens-college-basketball",
    "wbb": "womens-college-basketball",
}
NFLVERSE_PLAYERS_URL = "https://github.com/nflverse/nflverse-data/releases/download/players/players.parquet"
PLAYER_COLUMNS = ["gsis_id", "espn_id", "headshot"]


@functools.lru_cache(maxsize=1)  # keyed by mtime so a refreshed table is read again; only the current file matters
def _players(path: str, mtime: float) -> dict[str, tuple[str | None, str | None]]:
    p = pl.read_parquet(path, columns=PLAYER_COLUMNS).drop_nulls("gsis_id")
    players, bad = {}, []
    for g, e, h in p.iter_rows():
        if h and not safe_url(h):  # it would reach the web adapters' HTML: treat it as missing instead
            bad.append(h)
            h = None
        players[g] = (e, h)
    if bad:
        warn(
            f"ignored {len(bad)} nflverse headshot URL(s) that are not plain https URLs, e.g. {bad[0]!r:.100}; "
            "those players get their ESPN headshot when nflverse has their ESPN id"
        )
    return players


MEMORY_CACHES.append(_players.cache_clear)  # clear_cache() also frees the player table


def _is_valid_espn_id(normalized_id: str) -> bool:
    """Check if a normalized id is all ASCII digits, matching sdvplotR's shape validation."""
    return normalized_id.isascii() and normalized_id.isdigit()


def _espn(player_id: str, league: str) -> str | None:
    if not _is_valid_espn_id(player_id):
        return None
    slug = ESPN_HEADSHOT_LEAGUES[league]
    return f"https://a.espncdn.com/combiner/i?img=/i/headshots/{slug}/players/full/{player_id}.png"


def _transform_nfl_headshot(url: str) -> str:
    """Transform an NFL.com headshot URL.

    Replace /f_auto,q_auto/ with /t_headshot_desktop/f_auto/, then append .png if needed.
    """
    transformed = url.replace("/f_auto,q_auto/", "/t_headshot_desktop/f_auto/")
    if not transformed.endswith(".png"):
        transformed += ".png"
    return transformed


def headshot_url(player_id: Any, league: str, *, id_system: HeadshotIdSystem = "espn") -> str | None:
    """A headshot URL for one player.

    Args:
        player_id: One player id: an ESPN athlete id, or an nflverse gsis id.
        league: The SDV league key. "espn" ids work for nfl, nba, wnba, mlb, nhl, cfb, mbb and wbb; "gsis" is NFL only.
        id_system: "espn" (ESPN athlete id, any ESPN league) or "gsis" (mapped to ESPN through nflverse's player table,
            preferring nflverse's own headshot).

    Returns:
        str | None: The image URL, or None when the id is missing, malformed, or not in the player table.

    Raises:
        ValueError: If ``league`` has no ESPN headshots or ``id_system`` is not valid for ``league``.
        OfflineError: If ``id_system`` is "gsis" and the nflverse player table cannot be downloaded and no
            cached copy exists.

    Example:
        ::

            import sdvplot

            sdvplot.headshot_url("3139477", "nfl")
            # 'https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/3139477.png'
            sdvplot.headshot_url("00-0033873", "nfl", id_system="gsis")   # Patrick Mahomes, an nfl.com URL ending .png

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    # check the arguments first, so a null id never hides a bad league or id_system
    if id_system == "espn" and league not in ESPN_HEADSHOT_LEAGUES:
        raise InputError(f"no ESPN headshots for league {league!r}; supported: {sorted(ESPN_HEADSHOT_LEAGUES)}")
    if id_system != "espn" and (id_system, league) != ("gsis", "nfl"):
        raise InputError(f"id_system must be 'espn' (any league) or 'gsis' (nfl), got {id_system!r} for {league!r}")
    pid = norm_value(player_id)
    if pid is None:
        return None
    if id_system == "espn":
        return _espn(pid, league)
    path = fetch_cached(
        NFLVERSE_PLAYERS_URL,
        "nflverse/players.parquet",
        validate=lambda body: pl.read_parquet(io.BytesIO(body), columns=PLAYER_COLUMNS),
    )
    row = _players(str(path), path.stat().st_mtime).get(str(player_id).strip())
    if row is None:
        return None
    espn_id, headshot = row
    if headshot:
        return _transform_nfl_headshot(headshot)
    if espn_id:
        return _espn(espn_id, "nfl")
    return None

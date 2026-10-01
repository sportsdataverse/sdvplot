"""Player headshot URLs: ESPN athlete ids directly, nflverse gsis ids through nflverse's player table."""

from __future__ import annotations

import functools
from typing import Any

import polars as pl

from sdvplot._cache import fetch_cached
from sdvplot._normalize import norm_value

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


@functools.cache
def _players(path: str, mtime: float) -> dict[str, tuple[str | None, str | None]]:
    p = pl.read_parquet(path, columns=["gsis_id", "espn_id", "headshot"]).drop_nulls("gsis_id")
    return {g: (e, h) for g, e, h in p.iter_rows()}


def _espn(player_id: str, league: str) -> str:
    if league not in ESPN_HEADSHOT_LEAGUES:
        raise ValueError(f"no ESPN headshots for league {league!r}; supported: {sorted(ESPN_HEADSHOT_LEAGUES)}")
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


def headshot_url(player_id: Any, league: str, id_system: str = "espn") -> str | None:
    """A headshot URL for one player. id_system "espn" (ESPN athlete id, all ESPN leagues)
    or "gsis" (NFL only, mapped to ESPN through nflverse's player table, preferring
    nflverse's own headshot)."""
    pid = norm_value(player_id)
    if pid is None:
        return None
    if id_system == "espn":
        return _espn(pid, league)
    if id_system == "gsis" and league == "nfl":
        path = fetch_cached(NFLVERSE_PLAYERS_URL, "nflverse/players.parquet")
        row = _players(str(path), path.stat().st_mtime).get(str(player_id).strip())
        if row is None:
            return None
        espn_id, headshot = row
        if headshot:
            return _transform_nfl_headshot(headshot)
        if espn_id:
            return _espn(espn_id, "nfl")
        return None
    raise ValueError(f"id_system must be 'espn' (any league) or 'gsis' (nfl), got {id_system!r} for {league!r}")

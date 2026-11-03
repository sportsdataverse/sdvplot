"""Player headshot URLs: ESPN athlete ids directly, nflverse gsis ids through nflverse's player table, the leagues'
own player ids (NBA / WNBA Stats, MLBAM, NHL, HockeyTech) on their CDNs, and other providers' player ids through
sdv-reference-data's player_aliases."""

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
    # ESPN files G League photos under nba/ (nba-development/ 404s): G League and NBA athletes share one ESPN id space
    "nbagl": "nba",
    "soccer": "soccer",
}
# Headshots by the league's own player id, as sdvplotR's `league_headshot_url` (utils.R) builds them: hoopR's
# nba_player_headshot_url() / wehoop's wnba_playerheadshot() (NBA and WNBA Stats PERSON_ID), mlbplotR (MLBAM) and the
# NHL API's `headshot` for players with no current team (mugs/nhl/latest, the same image as the season/team mug). An
# unknown id gets the CDN's silhouette, not a 404. cdn.nba.com and cdn.wnba.com answer 403 to datacenter IPs (_cache).
# The NFL's league id is the gsis id: id_system="league" on "nfl" is "gsis" (sdvplotR's id_type="league" for the NFL).
# The HockeyTech leagues' player_id is the key on their stats provider's CDN (the roster feed's own player_image URL);
# the QMJHL's client code there is "lhjmq". leaguestat answers 404 for an unknown id, as ESPN does (the roster feed's
# "nophoto" placeholder is the feed's, not the CDN's).
HOCKEYTECH_HEADSHOT_URL = "https://assets.leaguestat.com/{client}/240x240/{{}}.jpg"
HOCKEYTECH_CLIENTS = {
    "pwhl": "pwhl",
    "ahl": "ahl",
    "echl": "echl",
    "ohl": "ohl",
    "whl": "whl",
    "qmjhl": "lhjmq",
    "ushl": "ushl",
    # the junior and minor leagues, each under its own key as client code
    "sphl": "sphl",
    "chl": "chl",
    "bchl": "bchl",
    "ajhl": "ajhl",
    "sjhl": "sjhl",
    "ojhl": "ojhl",
    "cchl": "cchl",
    "gojhl": "gojhl",
    "mhl": "mhl",
    "nojhl": "nojhl",
    "vijhl": "vijhl",
    "kijhl": "kijhl",
    "mjhl": "mjhl",
}
LEAGUE_HEADSHOT_URLS = {
    "nba": "https://cdn.nba.com/headshots/nba/latest/260x190/{}.png",
    "wnba": "https://cdn.wnba.com/headshots/wnba/latest/260x190/{}.png",
    "mlb": (
        "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/"
        "w_213,q_auto:best/v1/people/{}/headshot/67/current.png"
    ),
    "nhl": "https://assets.nhle.com/mugs/nhl/latest/{}.png",
    **{lg: HOCKEYTECH_HEADSHOT_URL.format(client=c) for lg, c in HOCKEYTECH_CLIENTS.items()},
}
LEAGUE_ID_LEAGUES = ("nfl", *LEAGUE_HEADSHOT_URLS)  # the leagues id_system="league" accepts
NFLVERSE_PLAYERS_URL = "https://github.com/nflverse/nflverse-data/releases/download/players/players.parquet"
PLAYER_COLUMNS = ["gsis_id", "espn_id", "headshot"]
# Other providers' player ids, mapped to ESPN athlete ids by sdv-reference-data's {league}_player_aliases (its
# CONTRACT.md; the sportsdataverse-data {league}_groups releases): the headshot is that athlete's ESPN headshot.
# sdvplotR's player_alias_sources (utils.R) lists the same.
PLAYER_ALIAS_SOURCES = {
    "nfl": ("fox", "yahoo", "cbs"),
    "cfb": ("fox", "yahoo", "cbs", "ncaa"),
    "nba": ("fox", "yahoo", "nba_stats"),
    "wnba": ("fox", "yahoo", "wnba_stats"),
    "mbb": ("fox", "yahoo", "kenpom", "ncaa"),
    "wbb": ("fox", "yahoo", "ncaa"),
}
PLAYER_ALIASES_URL = (
    "https://github.com/sportsdataverse/sportsdataverse-data/releases/download/"
    "{league}_groups/{league}_player_aliases.parquet"
)
PLAYER_ALIAS_COLUMNS = ["source", "source_player_id", "athlete_id"]
PROVIDER_ID_SYSTEMS = tuple(dict.fromkeys(s for v in PLAYER_ALIAS_SOURCES.values() for s in v))


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


@functools.lru_cache(maxsize=8)  # keyed by mtime, as _players; one league's table serves all its sources
def _player_aliases(path: str, mtime: float) -> dict[tuple[str, str], str]:
    """(source, source player id) -> ESPN athlete id. A provider id is one athlete in every season (the contract's
    cross-season rule), so the windows and teams drop out."""
    p = pl.read_parquet(path, columns=PLAYER_ALIAS_COLUMNS).drop_nulls().unique()
    return {(s, i): a for s, i, a in p.iter_rows()}


MEMORY_CACHES.append(_player_aliases.cache_clear)


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
        player_id: One player id: an ESPN athlete id, an nflverse gsis id, or the league's own player id.
        league: The SDV league key. "espn" ids work for nfl, nba, wnba, mlb, nhl, cfb, mbb, wbb, nbagl and soccer;
            "gsis" is NFL only; "league" works for nfl, nba, wnba, mlb, nhl and the 20 HockeyTech leagues
            (pwhl, ahl, echl, ohl, whl, qmjhl, ushl, sphl, chl, bchl, ajhl, sjhl, ojhl, cchl, gojhl, mhl, nojhl, vijhl,
            kijhl, mjhl). ESPN files G League (nbagl) photos with the NBA's, so a G League player's ESPN id is the one
            ESPN uses for him in the NBA. ESPN has photos for only part of the G League and soccer rosters. F1 drivers
            have none: formula1.com keys its photos by its own driver reference (``MAXVER01``), not a driver number or
            Jolpica ``driver_id``.
        id_system: "espn" (ESPN athlete id, any ESPN league), "gsis" (mapped to ESPN through nflverse's player table,
            preferring nflverse's own headshot), another provider's player id mapped to its ESPN athlete through
            sdv-reference-data's ``{league}_player_aliases`` ("fox", "yahoo" and "cbs" for nfl and cfb, "ncaa" for
            cfb, mbb and wbb, "fox" and "yahoo" for nba, wnba, mbb and wbb, "kenpom" for mbb, "nba_stats" for nba,
            "wnba_stats" for wnba), or "league" (the league's own player id, sdvplotR's
            ``id_type = "league"``: an NBA or WNBA Stats ``PERSON_ID`` as nba_api / hoopR / wehoop return it, an MLBAM
            id, an NHL API id, or the ``player_id`` of a HockeyTech feed (the 20 HockeyTech leagues above) on
            ``assets.leaguestat.com``, on the league's CDN; for the NFL it is the gsis id, the same as "gsis"). An
            unknown NBA, WNBA, MLB or NHL id gets the CDN's silhouette image; an unknown ESPN or HockeyTech id is a
            404, which the adapters treat as any missing image.

    Returns:
        str | None: The image URL, or None when the id is missing, malformed, or not in the player table.

    Raises:
        InputError: (a ValueError) If ``league`` has no ESPN headshots or ``id_system`` is not valid for ``league``
            ("league" names the leagues that have league-id headshots).
        OfflineError: If ``id_system`` is "gsis" (or "league" on "nfl"), or a provider, and the nflverse player
            table, or the league's player_aliases table, cannot be
            downloaded and no cached copy exists (a DownloadError, also an OSError, when GitHub answers with an error
            status).
        UnsafeDownloadError: (an OSError) If ``id_system`` is "gsis" and the player table download is refused: larger
            than the byte cap, past the deadline, or redirected away from https.

    Example:
        ::

            import sdvplot

            sdvplot.headshot_url("3139477", "nfl")
            # 'https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/3139477.png'
            sdvplot.headshot_url("00-0033873", "nfl", id_system="gsis")   # Patrick Mahomes, an nfl.com URL ending .png
            sdvplot.headshot_url(2544, "nba", id_system="league")   # LeBron James by his NBA Stats PERSON_ID
            # 'https://cdn.nba.com/headshots/nba/latest/260x190/2544.png'
            sdvplot.headshot_url(52, "pwhl", id_system="league")   # a PWHL player by her HockeyTech player_id
            # 'https://assets.leaguestat.com/pwhl/240x240/52.jpg'
            sdvplot.headshot_url("nba.p.3704", "nba", id_system="yahoo")   # LeBron James by his Yahoo id

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        sdv-py: https://py.sportsdataverse.org/
    """
    # check the arguments first, so a null id never hides a bad league or id_system
    if id_system == "espn" and league not in ESPN_HEADSHOT_LEAGUES:
        hint = " (use the league's own player ids with id_system='league')" if league in LEAGUE_HEADSHOT_URLS else ""
        raise InputError(f"no ESPN headshots for league {league!r}; supported: {sorted(ESPN_HEADSHOT_LEAGUES)}{hint}")
    if id_system == "league":
        if league not in LEAGUE_ID_LEAGUES:
            raise InputError(
                f"no headshots by league player id for league {league!r}; supported: {list(LEAGUE_ID_LEAGUES)} "
                "(use ESPN athlete ids with id_system='espn')"
            )
        if league == "nfl":
            id_system = "gsis"  # the NFL's league id is the gsis id
    elif id_system in PROVIDER_ID_SYSTEMS:  # a tuple: an unhashable id_system still reaches the InputError below
        if id_system not in PLAYER_ALIAS_SOURCES.get(league, ()):
            with_ids = [lg for lg, v in PLAYER_ALIAS_SOURCES.items() if id_system in v]
            raise InputError(f"id_system={id_system!r} player ids map to ESPN athletes in {with_ids} only")
    elif id_system != "espn" and (id_system, league) != ("gsis", "nfl"):
        raise InputError(
            f"id_system must be 'espn' (any league), 'gsis' (nfl), 'league' ({', '.join(LEAGUE_ID_LEAGUES)}) or a "
            f"provider ({PLAYER_ALIAS_SOURCES}), got {id_system!r} for {league!r}"
        )
    pid = norm_value(player_id)
    if pid is None:
        return None
    if id_system == "espn":
        return _espn(pid, league)
    if id_system == "league":
        return LEAGUE_HEADSHOT_URLS[league].format(pid) if _is_valid_espn_id(pid) else None  # digits, as R's grepl
    if id_system != "gsis":
        path = fetch_cached(
            PLAYER_ALIASES_URL.format(league=league),
            f"sportsdataverse-data/{league}_player_aliases.parquet",
            validate=lambda body: pl.read_parquet(io.BytesIO(body), columns=PLAYER_ALIAS_COLUMNS),
        )
        athlete = _player_aliases(str(path), path.stat().st_mtime).get((id_system, pid))
        return None if athlete is None else _espn(athlete, league)
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

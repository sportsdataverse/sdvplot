"""Snapshot every source the team index is built from into data-raw/*.csv. Runs on the droplet (network, the
CFBD key, and the private Sports Reference manifest); CI only runs the pure build (tools/build_index.py).

Usage:
    CFBD_API_KEY=... uv run python tools/fetch_sources.py \
        --sr-manifest /mnt/sdv_repos/sdv-assets-private/manifest/sr_team_seasons.csv \
        --ncaa-xwalk /mnt/sdv_repos/ncaa-mfb-football-raw/mfb/xwalk/espn_team_id.json
    uv run python tools/fetch_sources.py --colors-only   # espn_colors.csv and logo_colors.csv alone
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import shutil
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from PIL import Image

OUT = Path(__file__).resolve().parents[1] / "data-raw"
UA = {"User-Agent": "sdvplot-build (+https://github.com/sportsdataverse/sdvplot)"}
MANIFEST_URL = "https://sdv.nyc3.cdn.digitaloceanspaces.com/assets/public/manifest/marks.csv"
NHL_TEAM_URL = "https://api.nhle.com/stats/rest/en/team"
NHL_FRANCHISE_URL = "https://api.nhle.com/stats/rest/en/franchise"
ESPN_HOSTS = ["site.web.api.espn.com", "site.api.espn.com"]
# manifest sources whose entity_id IS the canonical team id (Ruling R19); mlbstatic counts only in milb
IDENTITY_SOURCES = {
    "espn",
    "ncaa.com",
    "wayback",
    "hockeytech",
    "aaf-strip-crop",
    "aaf.com",
    "fox",
    "cricinfo",
    "shiftstats",
}
NFLVERSE_TEAMS_URL = "https://github.com/nflverse/nflverse-data/releases/download/teams/teams_colors_logos.csv"
GROUPS_URL = (
    "https://github.com/sportsdataverse/sportsdataverse-data/releases/download/{league}_groups/{league}_{table}.parquet"
)
# (sdv league, ESPN sport, ESPN league) — the sdv-assets ESPN_LEAGUES list plus the college sports
ESPN_LEAGUES = [
    ("nfl", "football", "nfl"),
    ("nba", "basketball", "nba"),
    ("wnba", "basketball", "wnba"),
    ("mlb", "baseball", "mlb"),
    ("nhl", "hockey", "nhl"),
    ("cfb", "football", "college-football"),
    ("mbb", "basketball", "mens-college-basketball"),
    ("wbb", "basketball", "womens-college-basketball"),
    ("ufl", "football", "ufl"),
    ("nbagl", "basketball", "nba-development"),
    ("ncaa_baseball", "baseball", "college-baseball"),
    ("ncaa_softball", "baseball", "college-softball"),
    ("ncaa_mhockey", "hockey", "mens-college-hockey"),
    ("ncaa_whockey", "hockey", "womens-college-hockey"),
]
# ncaa_baseball / ncaa_softball are left out: their team_group_seasons parquets key teams with
# team_id_source == "ncaa_org" (0 ESPN rows). Add them once an ncaa_org -> ESPN id mapping exists.
GROUP_LEAGUES = ["nfl", "nba", "wnba", "mlb", "nhl", "cfb", "mbb", "wbb"]
MILB_SPORT_IDS = [11, 12, 13, 14, 16]
# Leagues whose teams list abbreviations differ from the ones ESPN's per-team endpoint, scores and standings use
# (college baseball: NCST in the list, NCSU everywhere else): espn_abbrs.csv keeps the per-team ones
ESPN_TEAM_ENDPOINT_LEAGUES = ["ncaa_baseball", "ncaa_softball"]
# Teams the archive holds that ESPN's teams list omits, whose per-team endpoint has the abbreviation ESPN uses
# elsewhere (UTRGV, college football from 2025: RGV): (sdv league, ESPN sport, ESPN league, team id)
ESPN_TEAM_ENDPOINT_TEAMS = [("cfb", "football", "college-football", "292")]
ESPN_ABBR_COLUMNS = ["league", "team_id", "abbreviation", "display_name", "valid_from", "valid_to"]
# Leagues whose earlier seasons' codes the teams list no longer shows (UFL 2024-25's BIR, ARL; the defunct XFL's):
# (sdv league, ESPN sport, ESPN league, first season, last season or None for the current year)
ESPN_SEASON_LEAGUES = [("ufl", "football", "ufl", 2024, None), ("xfl", "football", "xfl", 2020, 2023)]
# Leagues whose scoreboards use teams the index would lack, missing from ESPN's teams list (women's college hockey:
# Minnesota State as 24059 beside the listed 2364, Delaware) or from the archive (men's: SUNY Morrisville):
# espn_unlisted_teams.csv keeps those teams. Seasons as in ESPN_SEASON_LEAGUES.
ESPN_UNLISTED_LEAGUES = [
    ("ncaa_whockey", "hockey", "womens-college-hockey", 2025, None),
    ("ncaa_mhockey", "hockey", "mens-college-hockey", 2023, None),
]
ESPN_TEAM_COLUMNS = [
    "league",
    "team_id",
    "abbreviation",
    "display_name",
    "short_display_name",
    "location",
    "nickname",
    "color",
    "alternate_color",
]
# The per-team endpoint of the archive's ESPN-keyed teams the teams list gives no color (espn_colors.csv): the list
# leagues, plus soccer (one id space; any league slug answers for any club) and the defunct XFL. ESPN's cricket team
# endpoints answer 400 for every league, so cricket has none.
ESPN_COLOR_SLUGS = {league: (sport, el) for league, sport, el in ESPN_LEAGUES} | {
    "soccer": ("soccer", "all"),
    "xfl": ("football", "xfl"),
}
# ESPN's college sports, in the order the build asks them for a school's colors (by exact name: tools/build_index.py)
ESPN_COLLEGE = ["cfb", "mbb", "wbb", "ncaa_baseball", "ncaa_softball", "ncaa_mhockey", "ncaa_whockey"]
# The ones that key a team by its school, one id across them (Boston College is 103 in each): of the ids two of these
# lists share, 95-100% name the same location (October 2026). College baseball and softball number their own teams: of
# the 182, 107 and 108 ids they share with football and the basketball lists, none names the same location. A school
# with no color in its own sport is asked in the others, and the build keeps a color only from the same location.
ESPN_SCHOOL_IDS = ["cfb", "mbb", "wbb", "ncaa_mhockey", "ncaa_whockey"]
ESPN_COLOR_COLUMNS = ["league", "team_id", "espn_league", "display_name", "location", "color", "alternate_color"]
LOGO_COLOR_COLUMNS = ["league", "team_id", "primary", "secondary", "sha256"]


def _write(name: str, rows: list[dict], columns: list[str], out: Path) -> None:
    if not rows:
        raise RuntimeError(f"{name}: source returned no rows; refusing to write an empty snapshot")
    out.mkdir(exist_ok=True)
    rows = sorted(rows, key=lambda r: tuple(str(r.get(c, "")) for c in columns))
    with open(out / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}.csv: {len(rows)} rows")


def espn_team_row(league: str, t: dict) -> dict:
    """One ESPN team object as an espn_teams.csv row."""
    return {
        "league": league,
        "team_id": str(t["id"]),
        "abbreviation": t.get("abbreviation"),
        "display_name": t.get("displayName"),
        "short_display_name": t.get("shortDisplayName"),
        "location": t.get("location"),
        "nickname": t.get("name"),
        "color": t.get("color"),
        "alternate_color": t.get("alternateColor"),
    }


def espn_rows(league: str, payload: dict) -> list[dict]:
    return [espn_team_row(league, t["team"]) for t in payload["sports"][0]["leagues"][0]["teams"]]


def espn_team_abbr_row(league: str, payload: dict) -> dict | None:
    """One per-team endpoint payload as an espn_abbrs.csv row (current: no seasons); None for a placeholder team
    with no abbreviation (ESPN's "TBD")."""
    t = payload["team"]
    if not t.get("abbreviation"):
        return None
    return {"league": league, "team_id": str(t["id"]), "abbreviation": t["abbreviation"],
            "display_name": t.get("displayName"), "valid_from": "", "valid_to": ""}  # fmt: skip


def espn_season_abbr_rows(league: str, scoreboards: dict[int, dict]) -> list[dict]:
    """The team codes and names in a league's scoreboards, one row per (team, abbreviation, name) with the first and
    last season it appears in."""
    seen: dict[tuple, list[int]] = {}
    for season, payload in scoreboards.items():
        for event in payload.get("events", []):
            for c in event["competitions"][0]["competitors"]:
                t = c["team"]
                seen.setdefault((str(t["id"]), t.get("abbreviation"), t.get("displayName")), []).append(season)
    return [
        dict(zip(ESPN_ABBR_COLUMNS, (league, *key, min(s), max(s)), strict=True)) for key, s in seen.items() if key[1]
    ]


def fetch_espn_season_abbrs(s: requests.Session, host: str) -> list[dict]:
    """espn_season_abbr_rows for every ESPN_SEASON_LEAGUES league, from each season's scoreboard."""
    rows = []
    for league, sport, el, first, last in ESPN_SEASON_LEAGUES:
        url = f"https://{host}/apis/site/v2/sports/{sport}/{el}/scoreboard?dates={{}}&limit=1000"
        seasons = range(first, (last or dt.date.today().year) + 1)
        got = espn_season_abbr_rows(league, {y: _get(s, url.format(y)).json() for y in seasons})
        if not got:
            raise RuntimeError(f"espn: no scoreboard teams for {league}")
        rows += got
    return rows


def unlisted_team_ids(scoreboards: list[dict], listed: set[str]) -> list[str]:
    """The team ids scoreboards use that ``listed`` lacks (ESPN's "TBD" placeholders, ids <= 0, aside)."""
    ids = {
        c["team"]["id"]
        for payload in scoreboards
        for event in payload.get("events", [])
        for c in event["competitions"][0]["competitors"]
    }
    return sorted(i for i in ids if i.isdigit() and int(i) > 0 and i not in listed)


def fetch_espn_unlisted_teams(s: requests.Session, host: str, espn: list[dict], archived: list[dict]) -> list[dict]:
    """espn_teams.csv rows, from the per-team endpoint, for the ESPN_UNLISTED_LEAGUES teams the scoreboards use that
    ESPN's teams list (``espn``) or the archive (``archived``, manifest_team_rows) lacks."""
    rows = []
    for league, sport, el, first, last in ESPN_UNLISTED_LEAGUES:
        base = f"https://{host}/apis/site/v2/sports/{sport}/{el}"
        boards = [  # one month at a time: a year of men's college hockey passes the scoreboard's 1,000-event cap
            _get(s, f"{base}/scoreboard?dates={y}{m:02d}&limit=1000").json()
            for y in range(first, (last or dt.date.today().year) + 1)
            for m in range(1, 13)
        ]
        listed = {t["team_id"] for t in espn if t["league"] == league}
        listed &= {t["team_id"] for t in archived if t["league"] == league}
        rows += [
            espn_team_row(league, _get(s, f"{base}/teams/{i}").json()["team"])
            for i in unlisted_team_ids(boards, listed)
        ]
    return rows


def fetch_espn_team_abbrs(s: requests.Session, host: str, espn: list[dict]) -> list[dict]:
    """The per-team endpoint's abbreviation of every ESPN_TEAM_ENDPOINT_LEAGUES team in ``espn`` and of each
    ESPN_TEAM_ENDPOINT_TEAMS team (one request each)."""
    slugs = {league: (sport, el) for league, sport, el in ESPN_LEAGUES}
    wanted = [
        (t["league"], *slugs[t["league"]], t["team_id"]) for t in espn if t["league"] in ESPN_TEAM_ENDPOINT_LEAGUES
    ]
    rows = []
    for league, sport, el, team_id in [*wanted, *ESPN_TEAM_ENDPOINT_TEAMS]:
        payload = _get(s, f"https://{host}/apis/site/v2/sports/{sport}/{el}/teams/{team_id}").json()
        rows.append(espn_team_abbr_row(league, payload))
    return [r for r in rows if r is not None]


# ESPN's stand-in colors, not a team's: black alone (317 college football teams, 61 college baseball, 60 softball, 25
# women's and 15 men's basketball, all newer or smaller programs) or black with its stock red (282 soccer clubs from the
# per-team endpoint; 157 more black on black), measured October 2026. tools/build_index.py drops them the same way.
ESPN_PLACEHOLDER = ("000000", {"", "000000", "c60000"})  # (primary, the secondaries it comes with; "" = none)


def _hex6(color: str | None) -> str:
    """A color as six lowercase hex digits, or "" when it is not one."""
    c = str(color or "").strip().lstrip("#").lower()
    return c if re.fullmatch(r"[0-9a-f]{6}", c) else ""


def espn_has_color(color: str | None, alternate: str | None) -> bool:
    """Whether ESPN gives a team a color of its own: a valid primary that is not ESPN_PLACEHOLDER."""
    primary, alts = ESPN_PLACEHOLDER
    return bool(_hex6(color)) and not (_hex6(color) == primary and _hex6(alternate) in alts)


def espn_color_targets(manifest: list[dict], unlisted: list[dict], listed: list[dict]) -> list[tuple[str, str]]:
    """(league, team_id) of the archive's and the scoreboards' (``unlisted``) ESPN-keyed teams in an ESPN_COLOR_SLUGS
    league that ESPN's teams list (``listed``) or the scoreboard snapshot gives no color. ESPN-keyed: an ESPN mark with
    a numeric id, or a scoreboard team. An id another identity source also keys in the league (an ncaa.com id) may be
    a different team, so it is left out."""
    teams = {(r["league"], r["team_id"]) for r in [*manifest_team_rows(manifest), *unlisted]}
    marks = [r for r in manifest if _is_team_row(r)]
    keyed = {(r["league"], r["entity_id"]) for r in marks if r["source"] == "espn" and r["entity_id"].isdigit()}
    keyed |= {(r["league"], r["team_id"]) for r in unlisted}
    other = {(r["league"], r["entity_id"]) for r in marks if r["source"] in IDENTITY_SOURCES - {"espn"}}
    colored = {
        (r["league"], r["team_id"]) for r in [*listed, *unlisted] if espn_has_color(r["color"], r["alternate_color"])
    }
    return sorted(k for k in teams & keyed - other - colored if k[0] in ESPN_COLOR_SLUGS)


def espn_color_row(league: str, team_id: str, espn_league: str, t: dict) -> dict:
    """One per-team endpoint payload's team as an espn_colors.csv row."""
    return {
        "league": league,
        "team_id": team_id,
        "espn_league": espn_league,
        "display_name": t.get("displayName"),
        "location": t.get("location"),
        "color": t.get("color"),
        "alternate_color": t.get("alternateColor"),
    }


def fetch_espn_colors(s: requests.Session, host: str, targets: list[tuple[str, str]]) -> list[dict]:
    """The per-team endpoint's row for each target in its own league, and for a team of an ESPN_SCHOOL_IDS league it
    gives no color, the same id's row in the others until one has a color. A team its own league does not know stops
    there (no school to compare with); a 400/404 elsewhere is a sport the school does not play."""
    from concurrent.futures import ThreadPoolExecutor

    def one(target: tuple[str, str]) -> list[dict]:
        league, team_id = target
        rows = []
        for lg in [league, *(c for c in ESPN_SCHOOL_IDS if c != league and league in ESPN_SCHOOL_IDS)]:
            sport, el = ESPN_COLOR_SLUGS[lg]
            url = f"https://{host}/apis/site/v2/sports/{sport}/{el}/teams/{team_id}"
            for wait in (2, 4, 8, 16, 0):  # ESPN's edge answers a burst with a passing 403 or 429
                r = s.get(url, timeout=60)
                if r.status_code not in (403, 429) and r.status_code < 500 or not wait:
                    break
                time.sleep(wait)
            if r.status_code not in (400, 404):
                r.raise_for_status()
            t = r.json().get("team") if r.ok else None  # site.web answers some unknown ids 200 with no team
            if not t or str(t.get("id")) != team_id:  # no such team here; never another team's colors
                if lg == league:
                    break
                continue
            rows.append(espn_color_row(league, team_id, lg, t))
            if espn_has_color(t.get("color"), t.get("alternateColor")):
                break
        return rows

    with ThreadPoolExecutor(2) as pool:  # Site v2 tolerates a couple at once; Core v2 would not
        return [row for rows in pool.map(one, targets) for row in rows]


LOGO_SIZE = 128  # px, longest side: enough pixels to count colors, small enough to decode thousands
LOGO_ALPHA = 200  # opaque enough to be the mark, not an anti-aliased edge
LOGO_MIN_SHARE = 0.03  # a cluster smaller than this share of the opaque pixels is an edge blend, not a team color
LOGO_MIN_DISTANCE = 64  # RGB distance below which two clusters are shades of one color


def logo_colors(img: Image.Image) -> tuple[str, str | None] | None:
    """A logo's two dominant colors as "#rrggbb". The opaque pixels are median-cut to 12 colors and the clusters of at
    least LOGO_MIN_SHARE ranked: colors first, then dark and mid neutrals (black, grays), then near-white, each by pixel
    count. The primary is the first; the secondary the next one LOGO_MIN_DISTANCE or more from it (None if none is).
    None for an image with no opaque pixel."""
    from PIL import Image

    px = [p[:3] for p in img.convert("RGBA").get_flattened_data() if p[3] >= LOGO_ALPHA]
    if not px:
        return None
    strip = Image.new("RGB", (len(px), 1))
    strip.putdata(px)
    q = strip.quantize(colors=12, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette() or []
    clusters = [(n, tuple(pal[3 * i : 3 * i + 3])) for n, i in q.getcolors() or [] if n >= LOGO_MIN_SHARE * len(px)]

    def rank(c: tuple[int, tuple]) -> tuple:
        n, rgb = c
        hi, lo = max(rgb), min(rgb)
        neutral = hi < 40 or (hi - lo) < 0.2 * hi  # HSV value under 0.15, or saturation under 0.2
        return (neutral and lo > 230, neutral, -n, rgb)

    ranked = [rgb for _, rgb in sorted(clusters, key=rank)]
    if not ranked:
        return None
    primary = ranked[0]
    far = (c for c in ranked[1:] if sum((a - b) ** 2 for a, b in zip(c, primary, strict=True)) >= LOGO_MIN_DISTANCE**2)
    secondary = next(far, None)
    return "#{:02x}{:02x}{:02x}".format(*primary), ("#{:02x}{:02x}{:02x}".format(*secondary) if secondary else None)


def fetch_logo_colors(teams: list[tuple[str, str]]) -> list[dict]:
    """logo_colors of each team's current default logo, the mark logo_image() draws (through the bundled index, so a
    team newer than it waits for the next run). Every archived team with a logo gets a row, published colors or not: the
    build only reaches for one when no source publishes colors, and the others measure the method (tests)."""
    import warnings
    from concurrent.futures import ThreadPoolExecutor

    from sdvplot._images import load_mark_image
    from sdvplot._marks import select_mark

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # a team with no logo: a warning and None
        chosen = {key: select_mark(key[1], key[0]) for key in teams}
    marks = {row["sha256"]: row for row in chosen.values() if row}

    # one decode per mark, never two threads on one file (teams share marks; Windows refuses replacing an open file)
    with ThreadPoolExecutor(8) as pool:  # the archive CDN: content-addressed, cached
        found = dict(
            zip(marks, pool.map(lambda r: logo_colors(load_mark_image(r, LOGO_SIZE)), marks.values()), strict=True)
        )
    return [
        {"league": league, "team_id": team_id, "primary": got[0], "secondary": got[1] or "", "sha256": row["sha256"]}
        for (league, team_id), row in chosen.items()
        if row and (got := found[row["sha256"]])
    ]


def fetch_colors(s: requests.Session, host: str, manifest: list[dict], listed: list[dict], unlisted: list[dict],
                 write: Callable[[str, list[dict], list[str]], None]) -> None:  # fmt: skip
    """espn_colors.csv and logo_colors.csv (``--colors-only`` refreshes just these two)."""
    write("espn_colors", fetch_espn_colors(s, host, espn_color_targets(manifest, unlisted, listed)), ESPN_COLOR_COLUMNS)
    teams = sorted({(r["league"], r["team_id"]) for r in manifest_team_rows(manifest)})
    write("logo_colors", fetch_logo_colors(teams), LOGO_COLOR_COLUMNS)


def publish_staged(stage: Path, out: Path) -> None:
    """Move every staged snapshot into `out` (only called once every source has succeeded)."""
    out.mkdir(exist_ok=True)
    for f in sorted(stage.glob("*.csv")):
        shutil.move(str(f), out / f.name)  # stage is on /tmp: a different filesystem, so no os.replace


def _get(s: requests.Session, url: str, **kw) -> requests.Response:
    r = s.get(url, timeout=kw.pop("timeout", 60), **kw)
    r.raise_for_status()
    return r


def _is_team_row(r: dict) -> bool:
    return r["level"] == "team"


def _name_rank(r: dict) -> tuple:
    """Current name wins: open-ended valid_to, then latest valid_to, latest last_seen, then the name."""
    return (r["valid_to"] == "", r["valid_to"], r["last_seen"], r["entity_name"])


def manifest_team_rows(rows: list[dict]) -> list[dict]:
    latest: dict[tuple[str, str], dict] = {}
    for r in rows:
        identity = r["source"] in IDENTITY_SOURCES or (r["source"] == "mlbstatic" and r["league"] == "milb")
        if r["source"] == "espn" and not r["entity_id"].isdigit():
            identity = False  # abbreviation-keyed historic logo rows: marks only, not teams
        if not _is_team_row(r) or not identity:
            continue
        key = (r["league"], r["entity_id"])
        if key not in latest or _name_rank(r) > _name_rank(latest[key]):
            latest[key] = r
    return [
        {"league": lg, "team_id": tid, "name": r["entity_name"], "program": r["program"]}
        for (lg, tid), r in sorted(latest.items())
    ]


MARK_COLUMNS = ["league", "source", "entity_id", "entity_name", "valid_from", "valid_to"]


def manifest_mark_rows(rows: list[dict]) -> list[dict]:
    seen = {tuple(r[c] for c in MARK_COLUMNS) for r in rows if _is_team_row(r)}
    return [dict(zip(MARK_COLUMNS, k, strict=True)) for k in sorted(seen)]


# The conference and league marks (sdvplotR's logo_marks rows for its include_conferences rows), with the source URL
# the archive copied: tools/build_index.py joins sdvplotr_conferences.csv's logo_url / logo_dark_url on it
CONFERENCE_MARK_COLUMNS = ["level", "league", "source", "entity_id", "entity_name", "url"]
NON_TEAM_LEVELS = ("conference", "league")


def manifest_conference_rows(rows: list[dict]) -> list[dict]:
    seen = {tuple(r[c] for c in CONFERENCE_MARK_COLUMNS) for r in rows if r["level"] in NON_TEAM_LEVELS}
    return [dict(zip(CONFERENCE_MARK_COLUMNS, k, strict=True)) for k in sorted(seen)]


def nhl_rows(teams_payload: dict, franchise_payload: dict) -> list[dict]:
    fran = {f["id"]: f for f in franchise_payload["data"]}
    out = []
    for t in teams_payload["data"]:
        f = fran.get(t.get("franchiseId"), {})
        out.append(
            {
                "nhl_id": str(t["id"]),
                "franchise_id": str(t.get("franchiseId") or ""),
                "tri_code": t.get("triCode"),
                "full_name": t.get("fullName"),
                "franchise_full_name": f.get("fullName"),
                "franchise_common_name": f.get("teamCommonName"),
            }
        )
    return out


def ncaa_rows(xwalk: dict[str, str]) -> list[dict]:
    return [{"league": "cfb", "ncaa_id": str(k), "team_id": str(v)} for k, v in xwalk.items()]


SR_COLUMNS = ["league", "team_code", "team_name", "valid_from", "valid_to"]


def sr_code_rows(rows: list[dict]) -> list[dict]:
    """One row per (league, team_code): its latest Sports Reference team name and the seasons SR used it. The
    per-season capture is private (R47); only this aggregate, all the build needs, is written."""
    seasons: dict[tuple[str, str], list[tuple[int, str]]] = {}
    for r in rows:
        seasons.setdefault((r["league"], r["team_code"]), []).append((int(r["season"]), r["team_name"]))
    return [
        {"league": lg, "team_code": code, "team_name": max(s)[1], "valid_from": min(s)[0], "valid_to": max(s)[0]}
        for (lg, code), s in seasons.items()
    ]


MLB_HISTORY_COLUMNS = ["mlbstats_id", "abbreviation", "team_code", "name", "valid_from", "valid_to"]
MLB_FIRST_SEASON = 1901


def mlbstats_history_rows(seasons: dict[int, list[dict]]) -> list[dict]:
    """The MLB Stats API codes of today's franchises over time: one row per run of consecutive seasons with the same
    (id, abbreviation, teamCode, name). API team ids are franchise ids (the 1960 Kansas City Athletics are 133, the
    Athletics today), so a code maps to the franchise that used it. Clubs absent from the latest season (the Negro
    League and Federal League teams sportId=1 also lists) have no ESPN team and are left out."""
    current = {t["id"] for t in seasons[max(seasons)]}
    runs: dict[tuple, list[list[int]]] = {}
    for season in sorted(seasons):
        for t in seasons[season]:
            if t["id"] not in current:
                continue
            key = (str(t["id"]), t.get("abbreviation"), t.get("teamCode"), t.get("name"))
            spans = runs.setdefault(key, [])
            if spans and spans[-1][1] == season - 1:
                spans[-1][1] = season
            else:
                spans.append([season, season])
    return [
        dict(zip(MLB_HISTORY_COLUMNS, (*key, lo, hi), strict=True)) for key, spans in runs.items() for lo, hi in spans
    ]


def fetch_mlbstats_seasons(s: requests.Session, last: int) -> dict[int, list[dict]]:
    """Every big-league season's teams, MLB_FIRST_SEASON to ``last`` (plain http: see fetch_all)."""
    out = {}
    for season in range(MLB_FIRST_SEASON, last + 1):
        r = s.get(f"http://statsapi.mlb.com/api/v1/teams?sportId=1&season={season}", timeout=60)
        r.raise_for_status()
        out[season] = r.json().get("teams", [])
        if not out[season]:
            raise RuntimeError(f"mlbstats: no teams for season {season}")
    return out


def main() -> None:
    import tempfile

    p = argparse.ArgumentParser()
    p.add_argument("--sr-manifest", type=Path, help="sdv-assets-private manifest/sr_team_seasons.csv")
    p.add_argument("--ncaa-xwalk", type=Path, help="ncaa-mfb-football-raw mfb/xwalk/espn_team_id.json")
    p.add_argument(
        "--colors-only",
        action="store_true",
        help="refresh only espn_colors.csv and logo_colors.csv, from the committed ESPN team snapshots (no CFBD key)",
    )
    args = p.parse_args()
    stage = Path(tempfile.mkdtemp(prefix="sdvplot-fetch-"))
    try:
        fetch_all(args, stage)
        publish_staged(stage, OUT)  # all sources succeeded
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def fetch_all(args: argparse.Namespace, stage: Path) -> None:
    def write(name: str, rows: list[dict], columns: list[str]) -> None:
        _write(name, rows, columns, stage)

    s = requests.Session()
    s.headers.update(UA)

    text = _get(s, MANIFEST_URL, timeout=120).text
    manifest = list(csv.DictReader(io.StringIO(text)))
    if args.colors_only:
        listed, unlisted = (
            list(csv.DictReader(io.StringIO((OUT / f"{n}.csv").read_text(encoding="utf-8"))))
            for n in ("espn_teams", "espn_unlisted_teams")
        )
        fetch_colors(s, ESPN_HOSTS[0], manifest, listed, unlisted, write)
        return
    archived = manifest_team_rows(manifest)
    write("manifest_teams", archived, ["league", "team_id", "name", "program"])
    write("manifest_marks", manifest_mark_rows(manifest), MARK_COLUMNS)
    write("manifest_conferences", manifest_conference_rows(manifest), CONFERENCE_MARK_COLUMNS)

    espn: list[dict] = []
    hosts = list(ESPN_HOSTS)  # R7: site.web.* may 403 from some networks; fall back to site.api.*
    for league, sport, el in ESPN_LEAGUES:
        while True:
            r = s.get(f"https://{hosts[0]}/apis/site/v2/sports/{sport}/{el}/teams?limit=1000", timeout=60)
            if r.status_code == 403 and len(hosts) > 1:
                print(f"ESPN host {hosts[0]} returned 403; falling back to {hosts[1]}")
                hosts.pop(0)
                continue
            break
        r.raise_for_status()
        got = espn_rows(league, r.json())
        if not got:
            raise RuntimeError(f"espn: no teams for {league}")
        espn += got
    print(f"ESPN host used: {hosts[0]}")
    write("espn_teams", espn, ESPN_TEAM_COLUMNS)
    unlisted = fetch_espn_unlisted_teams(s, hosts[0], espn, archived)
    write("espn_unlisted_teams", unlisted, ESPN_TEAM_COLUMNS)
    abbrs = fetch_espn_team_abbrs(s, hosts[0], espn) + fetch_espn_season_abbrs(s, hosts[0])
    write("espn_abbrs", abbrs, ESPN_ABBR_COLUMNS)
    fetch_colors(s, hosts[0], manifest, espn, unlisted, write)

    nfl = list(csv.DictReader(io.StringIO(_get(s, NFLVERSE_TEAMS_URL).text)))
    write("nflverse_teams", nfl, ["team_abbr", "team_name", "team_nick", "team_color", "team_color2", "team_logo_espn"])

    key = os.environ["CFBD_API_KEY"]
    cfbd = _get(s, "https://api.collegefootballdata.com/teams", headers={"Authorization": f"Bearer {key}"}).json()
    write(
        "cfbd_teams",
        [
            {
                "team_id": str(t["id"]),
                "school": t["school"],
                "abbreviation": t.get("abbreviation"),
                "alternate_names": "|".join(t.get("alternateNames") or []),
            }
            for t in cfbd
        ],
        ["team_id", "school", "abbreviation", "alternate_names"],
    )

    from nba_api.stats.static import teams as nba_teams

    write(
        "nba_api_teams",
        [
            {
                "nba_api_id": str(t["id"]),
                "abbreviation": t["abbreviation"],
                "nickname": t["nickname"],
                "full_name": t["full_name"],
            }
            for t in nba_teams.get_teams()
        ],
        ["nba_api_id", "abbreviation", "nickname", "full_name"],
    )

    nhl = nhl_rows(_get(s, NHL_TEAM_URL).json(), _get(s, NHL_FRANCHISE_URL).json())
    write(
        "nhl_teams",
        nhl,
        ["nhl_id", "franchise_id", "tri_code", "full_name", "franchise_full_name", "franchise_common_name"],
    )

    mlb: list[dict] = []
    direct = requests.Session()  # plain http, no proxy (the MLB Stats API https endpoint is blocked here)
    direct.trust_env = False
    direct.headers.update(UA)
    season = dt.date.today().year
    for sport_id in [1, *MILB_SPORT_IDS]:
        r = direct.get(f"http://statsapi.mlb.com/api/v1/teams?sportId={sport_id}&season={season}", timeout=60)
        r.raise_for_status()
        teams = r.json().get("teams", [])
        if not teams:
            raise RuntimeError(f"mlbstats: no teams for sportId={sport_id}")
        for t in teams:
            mlb.append(
                {
                    "sport_id": sport_id,
                    "mlbstats_id": str(t["id"]),
                    "abbreviation": t.get("abbreviation"),
                    "team_code": t.get("teamCode"),
                    "file_code": t.get("fileCode"),
                    "team_name": t.get("teamName"),
                    "name": t.get("name"),
                }
            )
    write(
        "mlbstats_teams",
        mlb,
        ["sport_id", "mlbstats_id", "abbreviation", "team_code", "file_code", "team_name", "name"],
    )
    write("mlbstats_history", mlbstats_history_rows(fetch_mlbstats_seasons(direct, season)), MLB_HISTORY_COLUMNS)

    import polars as pl

    groups: list[dict] = []
    for league in GROUP_LEAGUES:
        tgs, gs = (
            pl.read_parquet(io.BytesIO(_get(s, GROUPS_URL.format(league=league, table=t), timeout=120).content))
            for t in ("team_group_seasons", "group_seasons")
        )
        latest = (
            tgs.filter(pl.col("team_id_source") == "espn")
            .sort("season")
            .group_by("team_id")
            .last()
            .join(
                gs.select("group_id", "season", "name"),
                left_on=["conference_id", "season"],
                right_on=["group_id", "season"],
                how="left",
            )
        )
        if latest.height == 0:
            raise RuntimeError(f"groups: no espn-keyed rows for {league}")
        for r in latest.iter_rows(named=True):
            groups.append(
                {
                    "league": league,
                    "team_id": r["team_id"],
                    "season": r["season"],
                    "conference_id": r["conference_id"],
                    "conference": r["name"],
                }
            )
    write("groups_latest", groups, ["league", "team_id", "season", "conference_id", "conference"])

    if args.ncaa_xwalk:
        xwalk = json.loads(args.ncaa_xwalk.read_text(encoding="utf-8"))
        write("ncaa_cfb_xwalk", ncaa_rows(xwalk), ["league", "ncaa_id", "team_id"])
    if args.sr_manifest:
        with open(args.sr_manifest, newline="", encoding="utf-8") as f:
            sr = list(csv.DictReader(f))
        write("sr_codes", sr_code_rows(sr), SR_COLUMNS)


if __name__ == "__main__":
    main()

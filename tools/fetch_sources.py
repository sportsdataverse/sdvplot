"""Snapshot every source the team index is built from into data-raw/*.csv. Runs on the droplet (network, the
CFBD key, and the private Sports Reference manifest); CI only runs the pure build (tools/build_index.py).

Usage:
    CFBD_API_KEY=... uv run python tools/fetch_sources.py \
        --sr-manifest /mnt/sdv_repos/sdv-assets-private/manifest/sr_team_seasons.csv \
        --ncaa-xwalk /mnt/sdv_repos/ncaa-mfb-football-raw/mfb/xwalk/espn_team_id.json
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import os
import shutil
from pathlib import Path

import requests

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


def espn_rows(league: str, payload: dict) -> list[dict]:
    teams = [t["team"] for t in payload["sports"][0]["leagues"][0]["teams"]]
    return [
        {
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
        for t in teams
    ]


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


def main() -> None:
    import tempfile

    p = argparse.ArgumentParser()
    p.add_argument("--sr-manifest", type=Path, help="sdv-assets-private manifest/sr_team_seasons.csv")
    p.add_argument("--ncaa-xwalk", type=Path, help="ncaa-mfb-football-raw mfb/xwalk/espn_team_id.json")
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
    write("manifest_teams", manifest_team_rows(manifest), ["league", "team_id", "name", "program"])
    write("manifest_marks", manifest_mark_rows(manifest), MARK_COLUMNS)

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
    write(
        "espn_teams",
        espn,
        [
            "league",
            "team_id",
            "abbreviation",
            "display_name",
            "short_display_name",
            "location",
            "nickname",
            "color",
            "alternate_color",
        ],
    )

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

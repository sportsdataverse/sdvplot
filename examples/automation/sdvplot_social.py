"""Social game-day graphics with sdvplot: season leaderboards, final-score cards and a player-of-the-game card.

Subcommands::

    leaderboard  one league's season leaders as a table image (great_tables, headless Chrome)
    gameday      a final-score card per game on one date (matplotlib), plus a player-of-the-game card
    post         post a run's images to Bluesky; prints the would-be posts unless --post is given

Each run writes PNGs to ``out/<today>/`` and adds its posts (image paths, alt text, caption, hashtags) to
``out/<today>/manifest.json``, which ``post`` reads. Data comes from ESPN's public APIs through the sdv-py
(``sportsdataverse``) wrappers; nothing needs a key. With no finished games on the date, or no leaders yet for the
season, it uses the most recent date or season that has them and says so in the caption.

Run from an sdvplot checkout (``uv sync --all-extras --all-groups`` first)::

    uv run python examples/automation/sdvplot_social.py leaderboard --league nfl
    uv run python examples/automation/sdvplot_social.py gameday --league nba --date 2026-06-13
    uv run python examples/automation/sdvplot_social.py post --manifest out/2026-10-04/manifest.json

``post --post`` publishes with the BSKY_HANDLE and BSKY_APP_PASSWORD environment variables (an app password, never
the account password). See docs/docs/automation/index.md for scheduling it with GitHub Actions.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import importlib
import io
import json
import os
import re
import sys
import time
import unicodedata
import warnings
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # files only; no window, works on a headless runner
import matplotlib.pyplot as plt  # noqa: E402
import polars as pl  # noqa: E402
import requests  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch  # noqa: E402
from PIL import Image  # noqa: E402

import sdvplot  # noqa: E402

# league -> (sport family, default leaders category, hashtag)
LEAGUES = {
    "nfl": ("football", "passingYards", "NFL"),
    "cfb": ("football", "passingYards", "CFB"),
    "nba": ("basketball", "pointsPerGame", "NBA"),
    "wnba": ("basketball", "pointsPerGame", "WNBA"),
    "mlb": ("baseball", "homeRuns", "MLB"),
    "nhl": ("hockey", "points", "NHL"),
}
TWO_YEAR = {"nba", "nhl"}  # seasons spanning two calendar years; ESPN names them by the year they end
SIZES = {"square": (1080, 1080), "landscape": (1200, 675)}
BG, INK, MUTED, NEUTRAL = "#0f1115", "#f5f6f7", "#a3a9b1", "#3a3f47"
CREDIT = "Data: ESPN via sportsdataverse-py  |  Logos, headshots & colors: sdvplot"
MAX_IMAGES, MAX_GRAPHEMES, MAX_BLOB = 4, 300, 1_000_000  # Bluesky's limits per post / per image
CALENDAR_TRIES = 14  # scoreboard days tried per season calendar before stepping back a season
TRIES = 4  # attempts per Bluesky call (429s always; 5xx and network errors except for createRecord)
GITHUB_REPO = "sportsdataverse/sdvplot"  # this example never posts from sdvplot's own CI


class NoData(Exception):
    """No games or leaders were found, even after falling back."""


# ---------------------------------------------------------------------------------------------------------------------
# Data: ESPN through sportsdataverse-py


def espn(league: str, name: str) -> Callable[..., Any]:
    """The sdv-py wrapper ``espn_<league>_<name>``, imported on first use so ``post`` and ``--help`` stay fast."""
    return getattr(importlib.import_module(f"sportsdataverse.{league}"), f"espn_{league}_{name}")


def season_label(league: str, season: int) -> str:
    return f"{season - 1}-{season % 100:02d}" if league in TWO_YEAR else str(season)


def long_date(day: dt.date) -> str:
    return f"{day:%A}, {day:%b} {day.day}, {day.year}"


def current_season(league: str) -> tuple[int, bool]:
    """The season ESPN's scoreboard is on today (the year it ends, for NBA and NHL), and whether it is in its
    regular season (so its leaders are "to date" rather than final)."""
    season = espn(league, "scoreboard")(return_parsed=False)["leagues"][0]["season"]
    return int(season["year"]), str((season.get("type") or {}).get("type", "")) == "2"


def _ref_id(ref: dict[str, Any] | None, kind: str) -> str | None:
    m = re.search(rf"/{kind}/(\d+)", (ref or {}).get("$ref", ""))
    return m.group(1) if m else None


def _stat_text(leader: dict[str, Any]) -> str:
    """The leader's value as shown: ESPN's display value when it is a number, else the value formatted."""
    shown, value = str(leader.get("displayValue", "")), float(leader["value"])
    if re.fullmatch(r"\d+", shown):
        return f"{int(shown):,}"
    if re.fullmatch(r"[\d.,:%+-]+", shown):
        return shown
    if value.is_integer():
        return f"{value:,.0f}"
    return f"{value:.3f}".removeprefix("0") if abs(value) < 1 else f"{value:.2f}"


def fetch_leaders(
    league: str, stat: str, season: int | None = None, top: int = 10
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Season leaders in one ESPN leaders category; with none yet, the most recent of the two seasons before.

    Returns:
        (frame, meta): one row per player (rank, athlete_id, has_headshot, name, position, team_id, display) and
        ``{"season", "stat", "stat_label", "abbr", "to_date", "note"}``.
    """
    from sportsdataverse.errors import NoDataError

    current, in_progress = current_season(league)
    wanted = season or current
    leaders = espn(league, "season_type_leaders")
    for year in (wanted, wanted - 1, wanted - 2):
        try:
            cats = leaders(season=year, season_type=2, return_parsed=False).get("categories") or []
        except NoDataError:  # ESPN has no regular-season leaders for that year (yet)
            continue
        cat = next((c for c in cats if c["name"].lower() == stat.lower()), None)
        if cats and cat is None:
            raise NoData(f"no {stat!r} leaders for {league}; categories: {', '.join(c['name'] for c in cats)}")
        if cat and cat.get("leaders"):
            break
    else:
        raise NoData(f"no {league} {stat} leaders for {wanted} or the two seasons before it")

    rows = cat["leaders"][:top]
    ids = [_ref_id(r.get("athlete"), "athletes") for r in rows]
    core = espn(league, "player_core")
    with ThreadPoolExecutor(max_workers=8) as pool:  # one small request per player
        people = list(pool.map(lambda i: core(athlete_id=i, return_parsed=False), ids))
    values = [float(r["value"]) for r in rows]
    frame = pl.DataFrame(
        {
            "rank": [values.index(v) + 1 for v in values],  # ties share the better rank
            "athlete_id": ids,
            "has_headshot": [bool(p.get("headshot")) for p in people],  # ESPN lists a headshot only when it has one
            "name": [p.get("displayName", "") for p in people],
            "position": [(p.get("position") or {}).get("abbreviation", "") for p in people],
            "team_id": [_ref_id(r.get("team"), "teams") for r in rows],
            "display": [_stat_text(r) for r in rows],
        },
        schema=LEADERS_SCHEMA,
    )
    note = None
    if year != wanted:
        note = (
            f"No {season_label(league, wanted)} regular-season leaders yet, so these are {season_label(league, year)}."
        )
    meta = {
        "season": year,
        "stat": cat["name"],
        "stat_label": cat.get("displayName", cat["name"]),
        "abbr": cat.get("abbreviation") or cat.get("shortDisplayName") or cat["name"],
        "to_date": in_progress and year == current,
        "note": note,
    }
    return frame, meta


LEADERS_SCHEMA = {
    "rank": pl.Int64,
    "athlete_id": pl.Utf8,
    "has_headshot": pl.Boolean,
    "name": pl.Utf8,
    "position": pl.Utf8,
    "team_id": pl.Utf8,
    "display": pl.Utf8,
}


def scoreboard(league: str, day: dt.date) -> dict[str, Any]:
    return espn(league, "scoreboard")(dates=f"{day:%Y%m%d}", return_parsed=False)


def finals(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """The finished games of a scoreboard payload, one flat dict each."""
    games = []
    for event in raw.get("events") or []:
        comp = event["competitions"][0]
        status = comp["status"]["type"]
        if not (status.get("completed") and status.get("name", "").startswith("STATUS_FINAL")):
            continue  # in progress, scheduled, postponed or canceled
        game = {
            "game_id": str(event["id"]),
            "status": status.get("shortDetail") or "Final",
            "phase": (event.get("season") or {}).get("slug", ""),
            "note": ((comp.get("notes") or [{}])[0]).get("headline", ""),
        }
        for side in ("away", "home"):
            c = next(x for x in comp["competitors"] if x["homeAway"] == side)
            rank = (c.get("curatedRank") or {}).get("current")
            game |= {
                f"{side}_id": str(c["team"]["id"]),
                f"{side}_abbr": c["team"].get("abbreviation", ""),
                f"{side}_location": c["team"].get("location", ""),
                f"{side}_name": c["team"].get("name", ""),
                f"{side}_score": int(float(c.get("score") or 0)),
                f"{side}_rank": rank if rank and rank <= 25 else None,
            }
        games.append(game)
    return games


def calendar_days(raw: dict[str, Any], before: dt.date) -> list[dt.date]:
    """The days of the payload's season calendar before ``before``, latest first."""
    days: set[dt.date] = set()
    for item in raw.get("leagues", [{}])[0].get("calendar") or []:
        if isinstance(item, str):  # a list of game days (NBA, WNBA, MLB, NHL)
            days.add(dt.date.fromisoformat(item[:10]))
            continue
        for week in item.get("entries") or []:  # football: season parts holding weeks
            start, end = (dt.date.fromisoformat(week[k][:10]) for k in ("startDate", "endDate"))
            days.update(start + dt.timedelta(days=n) for n in range((end - start).days + 1))
    return sorted((d for d in days if d < before), reverse=True)


def fetch_games(league: str, day: dt.date) -> tuple[dt.date, pl.DataFrame, str | None]:
    """The finished games on ``day``; with none, those of the most recent earlier day that has some.

    Earlier days come from ESPN's season calendar; when the calendar has none before ``day`` (an offseason before the
    first game), the search moves to the season before.

    Returns:
        (the day used, one row per game, a note saying what was substituted or None).
    """
    probe = day
    for _ in range(3):  # this season, then up to two seasons back
        raw = scoreboard(league, probe)
        for cand in [probe, *calendar_days(raw, probe)][:CALENDAR_TRIES]:
            games = finals(raw if cand == probe else scoreboard(league, cand))
            if games:
                tag, note = LEAGUES[league][2], None
                if cand != day:
                    note = f"No {tag} games finished on {long_date(day)}, so these are from {long_date(cand)}."
                return cand, pl.DataFrame(games), note
        probe = dt.date.fromisoformat(raw["leagues"][0]["season"]["startDate"][:10]) - dt.timedelta(days=1)
    raise NoData(f"no finished {league} games on or before {day}")


# ---------------------------------------------------------------------------------------------------------------------
# Player of the game: a simple, documented rule per sport (change it to taste)


def num(stats: dict[str, str], key: str, part: int = 0) -> float:
    """A box-score number; ``part`` picks one side of a pair such as "7-15" or "20/30" (made-attempted).

    A minus after a digit splits a pair; a leading minus is a negative number ("-5" rushing yards). Missing or
    non-numeric values ("--", "") are 0.
    """
    try:
        return float(re.split(r"(?<=\d)[-/]", stats.get(key, ""))[part])
    except (ValueError, IndexError):
        return 0.0


def basketball(s: dict[str, str]) -> tuple[float, list[str]]:
    """John Hollinger's game score."""
    fg, ft = "fieldGoalsMade-fieldGoalsAttempted", "freeThrowsMade-freeThrowsAttempted"
    score = (
        num(s, "points") + 0.4 * num(s, fg) - 0.7 * num(s, fg, 1) - 0.4 * (num(s, ft, 1) - num(s, ft))
        + 0.7 * num(s, "offensiveRebounds") + 0.3 * num(s, "defensiveRebounds") + num(s, "steals")
        + 0.7 * num(s, "assists") + 0.7 * num(s, "blocks") - 0.4 * num(s, "fouls") - num(s, "turnovers")
    )  # fmt: skip
    parts = [f"{num(s, k):.0f} {lab}" for k, lab in (("points", "PTS"), ("rebounds", "REB"), ("assists", "AST"))]
    parts += [f"{num(s, k):.0f} {lab}" for k, lab in (("steals", "STL"), ("blocks", "BLK")) if num(s, k) >= 3]
    return score, [" · ".join(parts)]


def football(s: dict[str, str]) -> tuple[float, list[str]]:
    """Standard fantasy points: a yard of passing is worth 0.04, rushing or receiving 0.1; TDs 4 (pass) or 6."""
    py, ptd, pint = (num(s, f"passing.{k}") for k in ("passingYards", "passingTouchdowns", "interceptions"))
    car, ry, rtd = (num(s, f"rushing.{k}") for k in ("rushingAttempts", "rushingYards", "rushingTouchdowns"))
    rec, yds, td = (num(s, f"receiving.{k}") for k in ("receptions", "receivingYards", "receivingTouchdowns"))
    lines = []
    if "passing.passingYards" in s:
        lines.append(f"{s.get('passing.completions/passingAttempts', '')} · {py:.0f} PASS YDS · {ptd:.0f} TD")
        lines[-1] += f" · {pint:.0f} INT" if pint else ""
    if car and (ry >= 20 or rtd or not lines):
        lines.append(f"{car:.0f} CAR · {ry:.0f} RUSH YDS" + (f" · {rtd:.0f} TD" if rtd else ""))
    if rec:
        lines.append(f"{rec:.0f} REC · {yds:.0f} REC YDS" + (f" · {td:.0f} TD" if td else ""))
    return py * 0.04 + 4 * ptd - 2 * pint + 0.1 * (ry + yds) + 6 * (rtd + td), lines


def hockey(s: dict[str, str]) -> tuple[float, list[str]]:
    """Dom Luszczyszyn's game score, simplified: goals, assists, shots and blocks; saves and goals against."""
    if "goalies.saves" in s:
        sv, ga = num(s, "goalies.saves"), num(s, "goalies.goalsAgainst")
        return 0.1 * sv - 0.75 * ga, [f"{sv:.0f} SAVES · {ga:.0f} GA · {s.get('goalies.savePct', '')} SV%"]
    b = "forwards." if "forwards.goals" in s else "defenses."
    g, a, sog, blk = (num(s, b + k) for k in ("goals", "assists", "shotsTotal", "blockedShots"))
    return 0.75 * g + 0.7 * a + 0.075 * sog + 0.05 * blk, [f"{g:.0f} G · {a:.0f} A · {g + a:.0f} PTS · {sog:.0f} SOG"]


def baseball(s: dict[str, str]) -> tuple[float, list[str]]:
    """Batters: hits, extra credit for home runs, RBIs, runs and walks. Pitchers: outs and strikeouts, less runs."""
    options = []
    if "batting.hits-atBats" in s:
        h, hr, rbi, r, bb = (num(s, f"batting.{k}") for k in ("hits", "homeRuns", "RBIs", "runs", "walks"))
        line = f"{s['batting.hits-atBats']} · {hr:.0f} HR · {rbi:.0f} RBI · {r:.0f} R"
        options.append((h + 3 * hr + rbi + r + 0.5 * bb, [line]))
    if "pitching.fullInnings.partInnings" in s:
        ip = num(s, "pitching.fullInnings.partInnings")
        outs = 3 * int(ip) + round(ip % 1 * 10)
        k, er, h, bb = (num(s, f"pitching.{k}") for k in ("strikeouts", "earnedRuns", "hits", "walks"))
        line = f"{s['pitching.fullInnings.partInnings']} IP · {h:.0f} H · {er:.0f} ER · {k:.0f} K"
        options.append((outs / 2 + 0.5 * k - 1.5 * er - 0.5 * (h + bb), [line]))
    return max(options, default=(0.0, []))


RULES: dict[str, Callable[[dict[str, str]], tuple[float, list[str]]]] = {
    "basketball": basketball,
    "football": football,
    "hockey": hockey,
    "baseball": baseball,
}


def fetch_box(league: str, game_id: str) -> pl.DataFrame:
    """Every player in a game's box score with the sport's player-of-the-game score and a stat line.

    Returns:
        One row per player: game_id, team_id, athlete_id, has_headshot, name, position, score, lines (a list of
        strings).
    """
    raw = espn(league, "summary")(event_id=game_id, return_parsed=False)
    players: dict[str, dict[str, Any]] = {}
    for team in (raw.get("boxscore") or {}).get("players") or []:
        for block in team.get("statistics") or []:
            label = block.get("name") or block.get("type") or ""  # passing, goalies, batting, ... (none in hoops)
            for entry in block.get("athletes") or []:
                a = entry["athlete"]
                p = players.setdefault(
                    str(a["id"]),
                    {
                        "team_id": str(team["team"]["id"]),
                        "has_headshot": bool(a.get("headshot")),
                        "name": a.get("displayName", ""),
                        "position": (a.get("position") or {}).get("abbreviation", ""),
                        "stats": {},
                    },
                )
                keys = [f"{label}.{k}" if label else k for k in block.get("keys") or []]
                p["stats"].update(zip(keys, entry.get("stats") or [], strict=False))
    rule = RULES[LEAGUES[league][0]]
    rows = []
    for athlete_id, p in players.items():
        score, lines = rule(p.pop("stats"))
        rows.append({"game_id": game_id, "athlete_id": athlete_id, "score": score, "lines": lines, **p})
    return pl.DataFrame(rows, schema=BOX_SCHEMA)


BOX_SCHEMA = {
    "game_id": pl.Utf8,
    "team_id": pl.Utf8,
    "athlete_id": pl.Utf8,
    "has_headshot": pl.Boolean,
    "name": pl.Utf8,
    "position": pl.Utf8,
    "score": pl.Float64,
    "lines": pl.List(pl.Utf8),
}


# ---------------------------------------------------------------------------------------------------------------------
# Drawing


def _luminance(color: str) -> float:
    """WCAG relative luminance of a ``#rrggbb`` color (sdvplot's own rule, inlined so the example uses only public
    sdvplot)."""
    rgb = [int(color.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio between two ``#rrggbb`` colors, 1 (same) to 21 (black on white)."""
    dark, light = sorted((_luminance(a), _luminance(b)))
    return (light + 0.05) / (dark + 0.05)


def on_color(background: str) -> str:
    """Black or white, whichever reads better on ``background``."""
    return "#000000" if contrast("#000000", background) >= contrast("#ffffff", background) else "#ffffff"


def team_color(team_id: str, league: str) -> str:
    """The team's primary color from sdvplot's index, or a neutral grey when the team is not in it."""
    return sdvplot.team_colors(league, team_id) or NEUTRAL


def readable_on_white(team_id: str, league: str) -> str:
    """A team color that reads as small text on white (4.5:1): the primary, else the secondary, else dark grey."""
    for which in ("primary", "secondary"):
        color = sdvplot.team_colors(league, team_id, which=which)
        if color and contrast(color, "#ffffff") >= 4.5:
            return str(color)
    return "#4a4f57"


def canvas(size: tuple[int, int], bg: str = BG) -> tuple[Any, Any]:
    """A figure exactly ``size`` pixels, with one Axes whose data coordinates are those pixels."""
    w, h = size
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100, facecolor=bg)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    return fig, ax


def fit(ax: Any, x: float, y: float, text: str, width: float, size: float, **kw: Any) -> Any:
    """Draw ``text``, shrinking the font until it is at most ``width`` pixels wide."""
    t = ax.text(x, y, text, fontsize=size, **kw)
    renderer = ax.figure.canvas.get_renderer()
    while size > 8 and t.get_window_extent(renderer).width > width:
        size -= 1
        t.set_fontsize(size)
    return t


def badge(ax: Any, x: float, y: float, r: float, team_id: str, league: str) -> None:
    """The team's logo on a white disc, so a logo in the team's own color still shows on a team-color panel."""
    ax.add_patch(Circle((x, y), r, facecolor="#ffffff", edgecolor="none", zorder=2))
    sdvplot.add_logos(ax, [x], [y], [team_id], league=league, height=1.25 * r / ax.bbox.height, zorder=3)


def save(fig: Any, path: Path) -> dict[str, Any]:
    fig.savefig(path, dpi=100, facecolor=fig.get_facecolor())
    plt.close(fig)
    with Image.open(path) as im:
        width, height = im.size
    return {"path": path.name, "width": width, "height": height}


def phase(game: dict[str, Any]) -> str:
    """ "PRESEASON" or "POSTSEASON" for games outside the regular season, else ""."""
    return "" if game["phase"] in ("", "regular-season") else game["phase"].replace("-", "").upper()


def panel(ax: Any, x: float, y: float, w: float, h: float, color: str, radius: float) -> None:
    """A rounded panel in ``color``, outlined when the color is too close to the background to show its edge."""
    edge = "#3a3f47" if contrast(color, BG) < 1.5 else "none"
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}", facecolor=color,
                                edgecolor=edge, linewidth=2, zorder=1))  # fmt: skip


def score_card(game: dict[str, Any], league: str, day: dt.date, path: Path) -> dict[str, Any]:
    """A 1200 x 675 final-score card: both teams on their colors, logos on white discs, the winner's score bold."""
    w, h = SIZES["landscape"]
    fig, ax = canvas((w, h))
    tag = LEAGUES[league][2]
    header = "  ·  ".join(x for x in (game["status"].upper(), phase(game)) if x)
    ax.text(32, 636, header, color=INK, fontsize=20, fontweight="bold", va="center")
    ax.text(w - 32, 636, f"{tag}  ·  {long_date(day)}", color=MUTED, fontsize=15, ha="right", va="center")
    if game["note"]:
        fit(ax, w / 2, 596, game["note"], w - 64, 14, color=MUTED, ha="center", va="center")
    for side, x0 in (("away", 24), ("home", w / 2 + 12)):
        pw, color = w / 2 - 36, team_color(game[f"{side}_id"], league)
        ink, cx = on_color(color), x0 + (w / 2 - 36) / 2
        panel(ax, x0, 84, pw, 488, color, 18)
        badge(ax, cx, 464, 92, game[f"{side}_id"], league)
        rank = f"#{game[f'{side}_rank']} " if game[f"{side}_rank"] else ""
        fit(ax, cx, 342, f"{rank}{game[f'{side}_location']}", pw - 40, 20, color=ink, ha="center", va="center")
        fit(ax, cx, 294, game[f"{side}_name"].upper(), pw - 40, 30, color=ink, fontweight="bold", ha="center",
            va="center")  # fmt: skip
        won = game[f"{side}_score"] > game[f"{'home' if side == 'away' else 'away'}_score"]  # a tie bolds neither
        ax.text(cx, 172, str(game[f"{side}_score"]), color=ink, fontsize=104, ha="center", va="center",
                fontweight="bold" if won else "normal", alpha=1 if won else 0.7, zorder=3)  # fmt: skip
    ax.text(32, 40, CREDIT, color=MUTED, fontsize=12, va="center")
    ax.text(w - 32, 40, f"#{tag}", color=MUTED, fontsize=12, va="center", ha="right")
    return save(fig, path)


def potg_card(player: dict[str, Any], game: dict[str, Any], league: str, day: dt.date, path: Path) -> dict[str, Any]:
    """A 1080 x 1080 player-of-the-game card: the headshot on the team's color, the stat line, the result."""
    w, h = SIZES["square"]
    fig, ax = canvas((w, h))
    tag, team = LEAGUES[league][2], player["team_id"]
    color = team_color(team, league)
    ax.text(60, 1010, "PLAYER OF THE GAME", color=INK, fontsize=30, fontweight="bold", va="center")
    ax.text(w - 60, 1010, f"{tag}  ·  {day:%b} {day.day}, {day.year}", color=MUTED, fontsize=17, ha="right",
            va="center")  # fmt: skip
    panel(ax, 60, 460, w - 120, 490, color, 24)
    sdvplot.add_logos(ax, [w - 250], [705], [team], league=league, height=0.36, alpha=0.22, zorder=2)
    if player["has_headshot"]:
        head = 0.42  # of the canvas height: ESPN headshots are 600 x 436, so this draws them near full size
        sdvplot.add_headshots(ax, [400], [460 + head * h / 2], [player["athlete_id"]], league=league, height=head,
                              zorder=3)  # fmt: skip
    else:  # no headshot on file: the team's logo, full strength, in its place
        badge(ax, 330, 705, 175, team, league)
    side = "home" if game["home_id"] == team else "away"
    fit(ax, 60, 380, player["name"], w - 120, 64, color=INK, fontweight="bold", va="center")
    team_name = f"{game[f'{side}_location']} {game[f'{side}_name']}".strip()
    meta = "  ·  ".join(x for x in (player["position"], team_name) if x)
    fit(ax, 62, 312, meta, w - 120, 24, color=MUTED, va="center")
    for i, line in enumerate(list(player["lines"])[:3]):
        fit(ax, 62, 244 - 46 * i, line, w - 120, 30, color=INK, fontweight="bold", va="center")
    score = f"{game['away_abbr']} {game['away_score']}, {game['home_abbr']} {game['home_score']}"
    result = "  ·  ".join(x for x in (score, game["status"], phase(game).lower(), game["note"]) if x)
    fit(ax, 62, 82, result, w - 120, 19, color=MUTED, va="center")
    ax.text(62, 34, CREDIT, color=MUTED, fontsize=12, va="center")
    ax.text(w - 60, 34, f"#{tag}", color=MUTED, fontsize=12, va="center", ha="right")
    return save(fig, path)


def leaderboard_image(
    frame: pl.DataFrame, meta: dict[str, Any], league: str, size: str, today: dt.date, path: Path
) -> dict[str, Any]:
    """The leaders as a great_tables table in the top player's team colors, saved at a social size."""
    from great_tables import GT

    from sdvplot.great_tables import gt_sdv_headshots, gt_sdv_logos, gt_social_crop, gt_theme_sdv_team

    tag = LEAGUES[league][2]
    abbr = dict(sdvplot.teams().filter(pl.col("league") == league).select("team_id", "abbr").iter_rows())
    ids = [sdvplot.resolve(t, league) if t else None for t in frame["team_id"]]

    def cell(name: str, position: str, team: str | None) -> str:  # the name over "POS · TEAM" in a readable team color
        sub = " · ".join(x for x in (position, abbr.get(team or "", "")) if x)
        ink = readable_on_white(team, league) if team else "#4a4f57"
        return (
            f"<div style='font-weight:700'>{html.escape(name)}</div>"
            f"<div style='font-size:0.72em;font-weight:700;color:{ink}'>{html.escape(sub)}</div>"
        )

    player = [cell(*row) for row in zip(frame["name"], frame["position"], ids, strict=True)]
    table = frame.select(
        "rank",
        pl.when(pl.col("has_headshot")).then(pl.col("athlete_id")).alias("headshot"),  # blank: no broken image
        pl.Series("player", player),
        pl.col("team_id").alias("logo"),
        "display",
    )
    when = f"through {today:%b} {today.day}" if meta["to_date"] else "final"
    subtitle = f"{season_label(league, meta['season'])} regular season, {when}"
    gt = (
        GT(table)
        .tab_header(title=f"{tag} {meta['stat_label']} leaders", subtitle=subtitle)
        .fmt(lambda x: x, columns="player")  # the cell is HTML already
        .cols_label(rank="", headshot="", player="Player", logo="", display=meta["abbr"])
        .cols_align("center", columns=["rank", "logo", "display"])
        .cols_width(rank="56px", headshot="96px", logo="84px", display="110px")
        .sub_missing(columns="headshot", missing_text="")
        .tab_source_note(CREDIT)
    )
    if meta["note"]:
        gt = gt.tab_source_note(meta["note"])
    with warnings.catch_warnings():  # the blank headshot cells warn; they are blank on purpose
        warnings.simplefilter("ignore", sdvplot.SdvplotWarning)
        gt = gt_sdv_headshots(gt, "headshot", league=league, height=52)
    gt = gt_sdv_logos(gt, "logo", league=league, height=40)
    leader_team = ids[0] if ids and ids[0] else None
    gt = gt_theme_sdv_team(gt, leader_team, league=league, density="social", table_width="760px")
    w, h = SIZES[size]
    bg = team_color(leader_team, league) if leader_team else BG
    gt_social_crop(gt, path, aspect_ratio=f"{w}:{h}", bg=bg, width=w, whitespace=48)
    with Image.open(path) as im:
        width, height = im.size
    return {"path": path.name, "width": width, "height": height}


# ---------------------------------------------------------------------------------------------------------------------
# Manifest


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def write_manifest(out: Path, posts: list[dict[str, Any]]) -> Path:
    """Add ``posts`` to ``out/manifest.json``, replacing earlier posts of the same threads (a re-run replaces)."""
    path = out / "manifest.json"
    old = json.loads(path.read_text(encoding="utf-8"))["posts"] if path.exists() else []
    threads = {p["thread"] for p in posts}
    manifest = {"version": 1, "date": out.name, "posts": [p for p in old if p["thread"] not in threads] + posts}
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def run_leaderboard(args: argparse.Namespace) -> Path:
    league, today = args.league, dt.date.today()
    top = args.top or (10 if args.size == "square" else 5)
    frame, meta = fetch_leaders(league, args.stat or LEAGUES[league][1], args.season, top)
    out = Path(args.out) / today.isoformat()
    out.mkdir(parents=True, exist_ok=True)
    name = f"{league}-leaders-{slug(meta['stat'])}-{args.size}"
    image = leaderboard_image(frame, meta, league, args.size, today, out / f"{name}.png")
    tag, label = LEAGUES[league][2], season_label(league, meta["season"])
    ranking = "; ".join(f"{r['rank']}. {r['name']} {r['display']}" for r in frame.iter_rows(named=True))
    image["alt"] = f"Table of the {tag} {meta['stat_label']} leaders, {label} regular season: {ranking}."
    when = f"through {today:%b} {today.day}" if meta["to_date"] else "final"
    top_row = frame.row(0, named=True)
    caption = f"{tag} {meta['stat_label']} leaders, {label} regular season ({when}): {top_row['name']} leads with "
    caption += f"{top_row['display']}." + (f" {meta['note']}" if meta["note"] else "")
    # fresh while the season is under way (a new date each run); a final season is the same table every week
    key = f"{league}-leaderboard-{slug(meta['stat'])}-{args.size}-{meta['season']}"
    key += f"-{today.isoformat()}" if meta["to_date"] else ""
    post = {"key": key, "fresh": bool(meta["to_date"]), "thread": name, "league": league, "kind": "leaderboard",
            "caption": caption, "hashtags": [tag, "sdvplot"], "images": [image]}  # fmt: skip
    return write_manifest(out, [post])


def winners(game: dict[str, Any]) -> list[str]:
    """The team ids that did not lose: the winner, or both teams after a tie."""
    return [
        game[f"{s}_id"] for s, o in (("away", "home"), ("home", "away")) if game[f"{s}_score"] >= game[f"{o}_score"]
    ]


def run_gameday(args: argparse.Namespace) -> Path:
    league, tag = args.league, LEAGUES[args.league][2]
    day, games, note = fetch_games(league, args.date)
    ranked = games.with_columns(r=pl.min_horizontal("away_rank", "home_rank").fill_null(99))
    finals_ = list(ranked.sort("r", maintain_order=True).drop("r").iter_rows(named=True))
    out = Path(args.out) / dt.date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{league}-{day:%Y%m%d}"
    cards = []
    for g in finals_[: args.max_games]:
        teams = f"{slug(g['away_abbr'])}-at-{slug(g['home_abbr'])}-{slug(g['game_id'])}"  # the id: doubleheaders
        image = score_card(g, league, day, out / f"{stem}-{teams}.png")
        image["alt"] = (
            f"Final score card, {tag}, {long_date(day)}: {g['away_location']} {g['away_name']} {g['away_score']}, "
            f"{g['home_location']} {g['home_name']} {g['home_score']} ({g['status']}), with both team logos."
        )
        cards.append(image)
    with ThreadPoolExecutor(max_workers=8) as pool:  # every final, drawn or not: one box score each
        boxes = list(pool.map(lambda g: fetch_box(league, g["game_id"]), finals_))
    best = None  # the best rule score on a team that did not lose, across all of the day's finals
    for g, box in zip(finals_, boxes, strict=True):
        box = box.filter(pl.col("team_id").is_in(winners(g))).sort("score", descending=True, maintain_order=True)
        if box.height and (best is None or box["score"][0] > best[0]["score"]):
            best = (box.row(0, named=True), g)
    kind = phase(finals_[0]).lower()  # preseason or postseason, said in the caption
    prefix = f"{kind} " if kind else ""
    images, caption = cards, f"{tag} {prefix}final scores, {long_date(day)}."
    if best:
        player, g = best
        potg = potg_card(player, g, league, day, out / f"{stem}-player-of-the-game.png")
        line = "; ".join(player["lines"])
        who = ", ".join(x for x in (player["name"], player["position"]) if x)
        team = g["home_name"] if g["home_id"] == player["team_id"] else g["away_name"]
        potg["alt"] = (
            f"Player of the game card with a headshot: {who}, {team}: {line}. Final: {g['away_abbr']} "
            f"{g['away_score']}, {g['home_abbr']} {g['home_score']}."
        )
        images = [potg, *cards]
        caption += f" Player of the game: {player['name']}, {line}."
    if note:
        caption += f" {note}"
    chunks = [images[i : i + MAX_IMAGES] for i in range(0, len(images), MAX_IMAGES)]
    posts = [
        {
            "key": f"{league}-gameday-{day.isoformat()}-{i + 1}",
            "fresh": note is None,  # a substituted date (the offseason) is old news
            "thread": stem,
            "league": league,
            "kind": "gameday",
            "caption": caption if i == 0 else f"More {tag} final scores, {long_date(day)} ({i + 1}/{len(chunks)}).",
            "hashtags": [tag, "sdvplot"],
            "images": chunk,
        }
        for i, chunk in enumerate(chunks)
    ]
    return write_manifest(out, posts)


# ---------------------------------------------------------------------------------------------------------------------
# Posting


def graphemes(text: str) -> int:
    """Approximate grapheme count: combining marks, variation selectors and joiners do not count.

    ponytail: overcounts emoji ZWJ sequences (a family emoji counts several), so the 300 limit errs safe; use a
    grapheme library if captions carry many emoji.
    """
    return sum(1 for ch in text if not unicodedata.combining(ch) and ch not in "‍︎️")


def post_text(post: dict[str, Any]) -> str:
    """The caption and hashtags, the caption shortened with an ellipsis to keep within 300 graphemes."""
    tags = " ".join(f"#{t}" for t in post.get("hashtags") or [])
    caption = post["caption"]
    if graphemes(f"{caption}\n\n{tags}") > MAX_GRAPHEMES:  # a grapheme is one or more code points, so slicing is safe
        caption = caption[: max(0, MAX_GRAPHEMES - graphemes(tags) - 3)].rstrip() + "…"
    return f"{caption}\n\n{tags}".strip()


def check_post(post: dict[str, Any], base: Path) -> None:
    """Raise ValueError for a post Bluesky would refuse: over 4 images, a missing file or alt text, too long."""
    images = post.get("images") or []
    if not 1 <= len(images) <= MAX_IMAGES:
        raise ValueError(f"post {post.get('key')!r} has {len(images)} images; Bluesky takes 1 to {MAX_IMAGES}")
    for image in images:
        if not (base / image["path"]).is_file():
            raise ValueError(f"image {image['path']!r} is not in {base}")
        if not image.get("alt"):
            raise ValueError(f"image {image['path']!r} has no alt text")
    if graphemes(post_text(post)) > MAX_GRAPHEMES:
        raise ValueError(f"post {post.get('key')!r} is over {MAX_GRAPHEMES} graphemes even shortened")


def hashtag_facets(text: str) -> list[dict[str, Any]]:
    """Bluesky rich-text facets that make each #tag a link (byte offsets into the UTF-8 text)."""
    facets = []
    for m in re.finditer(r"(?:^|\s)(#[A-Za-z][A-Za-z0-9_]*)", text):
        start = len(text[: m.start(1)].encode())
        facets.append({"index": {"byteStart": start, "byteEnd": start + len(m.group(1).encode())},
                       "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": m.group(1)[1:]}]})  # fmt: skip
    return facets


def image_bytes(path: Path) -> tuple[bytes, str]:
    """The image as PNG, or re-encoded as JPEG when the PNG is over Bluesky's 1 MB blob limit."""
    data = path.read_bytes()
    if len(data) <= MAX_BLOB:
        return data, "image/png"
    with Image.open(path) as im:
        rgb = im.convert("RGB")
    for quality in (92, 85, 75, 65):
        buf = io.BytesIO()
        rgb.save(buf, "JPEG", quality=quality, optimize=True)
        if buf.tell() <= MAX_BLOB:
            return buf.getvalue(), "image/jpeg"
    raise ValueError(f"{path.name} is over 1 MB even as a JPEG")


class PostError(Exception):
    """A Bluesky call failed. The message holds the call, status and Bluesky's error, never credentials.

    ``ambiguous`` is True when a post may have been created anyway (createRecord timed out or got a 5xx answer).
    """

    def __init__(self, message: str, ambiguous: bool = False) -> None:
        super().__init__(message)
        self.ambiguous = ambiguous


class Bluesky:
    """The three Bluesky (AT Protocol) calls a post needs, over plain requests."""

    def __init__(self, session: Any = None, service: str = "https://bsky.social") -> None:
        self.http = session or requests.Session()
        self.service = service.rstrip("/")
        self.jwt: str | None = None
        self.did: str | None = None

    def call(self, method: str, *, retry: bool = True, **kw: Any) -> dict[str, Any]:
        """POST to an XRPC method, waiting out rate limits (429: the request was refused, so a retry is safe).

        With ``retry``, 5xx answers and dropped or timed-out connections are retried too, after 1, 2 and 4 s. Without
        it (createRecord), they end the call as ambiguous, since the post may exist: it is never sent twice blindly.
        """
        headers = {
            **kw.pop("headers", {}),
            **({"Authorization": f"Bearer {self.jwt}"} if self.jwt else {}),
        }
        maybe = "; it may have been posted: check the account before posting it again"
        for attempt in range(TRIES):
            last = attempt == TRIES - 1
            try:
                r = self.http.post(f"{self.service}/xrpc/{method}", headers=headers, timeout=60, **kw)
            except (requests.ConnectionError, requests.Timeout) as e:
                if retry and not last:
                    time.sleep(2**attempt)
                    continue
                tail = f" after {TRIES} tries" if retry else maybe
                raise PostError(f"{method}: {type(e).__name__}{tail}", ambiguous=not retry) from None
            if r.status_code == 429 and not last:
                reset = r.headers.get("ratelimit-reset")
                wait = min(
                    max(
                        float(reset) - time.time() if reset else float(r.headers.get("retry-after", 5)),
                        1,
                    ),
                    60,
                )
                print(f"rate limited by Bluesky; waiting {wait:.0f} s", file=sys.stderr)
                time.sleep(wait)
                continue
            if r.status_code >= 500 and retry and not last:
                time.sleep(2**attempt)
                continue
            break
        if r.status_code >= 400:
            try:
                body = r.json()
            except ValueError:
                body = {}
            message = f"{method}: HTTP {r.status_code} {body.get('error', '')} {body.get('message', '')}".strip()
            ambiguous = r.status_code >= 500 and not retry
            raise PostError(message + (maybe if ambiguous else ""), ambiguous=ambiguous)
        return dict(r.json())

    def login(self, handle: str, app_password: str) -> None:
        out = self.call(
            "com.atproto.server.createSession",
            json={"identifier": handle, "password": app_password},
        )
        self.jwt, self.did = out["accessJwt"], out["did"]

    def upload(self, images: list[dict[str, Any]], base: Path) -> list[dict[str, Any]]:
        """Upload a post's images; their embeds carry the alt text and aspect ratio."""
        embeds = []
        for image in images:
            data, mime = image_bytes(base / image["path"])
            blob = self.call("com.atproto.repo.uploadBlob", data=data, headers={"Content-Type": mime})["blob"]
            embeds.append({"image": blob, "alt": image["alt"],
                           "aspectRatio": {"width": image["width"], "height": image["height"]}})  # fmt: skip
        return embeds

    def create(self, text: str, embeds: list[dict[str, Any]], reply: Any = None) -> dict[str, str]:
        """Create the post; ``reply`` = (root, parent) refs. Never retried after an ambiguous failure."""
        record: dict[str, Any] = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "facets": hashtag_facets(text),
            "langs": ["en"],
            "createdAt": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            "embed": {"$type": "app.bsky.embed.images", "images": embeds},
        }
        if reply:
            record["reply"] = {"root": reply[0], "parent": reply[1]}
        out = self.call(
            "com.atproto.repo.createRecord",
            retry=False,
            json={
                "repo": self.did,
                "collection": "app.bsky.feed.post",
                "record": record,
            },
        )
        return {"uri": out["uri"], "cid": out["cid"]}


def newest_manifest(out: Path) -> Path:
    """The newest ``<out>/<date>/manifest.json`` (the dates sort as text)."""
    found = sorted(out.glob("*/manifest.json"))
    if not found:
        raise PostError(f"no manifest.json under {out}; run leaderboard or gameday first")
    return found[-1]


def skip_reasons(posts: list[dict[str, Any]], ledger: dict[str, Any], include_stale: bool) -> list[str | None]:
    """Why each post is skipped, or None to post it. A thread with a post left out stops there."""
    reasons: list[str | None] = []
    broken: set[str] = set()
    for post in posts:
        entry = ledger.get(post["key"]) or {}
        reason = None
        if entry.get("status") == "posted":
            reason = f"already posted ({entry.get('uri')})"
        elif entry:
            reason = (
                f"pending (an earlier attempt may have posted it; check the account, then delete {post['key']!r} "
                "from the ledger to try again)"
            )
        elif post["thread"] in broken:
            reason = "an earlier post of its thread was not posted"
        elif not post["fresh"] and not include_stale:
            reason = "stale (pass --include-stale to post it)"
        if reason and entry.get("status") != "posted":
            broken.add(post["thread"])
        reasons.append(reason)
    return reasons


def write_ledger(path: Path, ledger: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")


def run_post(args: argparse.Namespace, session: Any = None) -> None:
    manifest_path = Path(args.manifest) if args.manifest else newest_manifest(Path(args.out))
    base = manifest_path.parent
    ledger_path = Path(args.ledger) if args.ledger else base.parent / "posted.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {}
    posts = json.loads(manifest_path.read_text(encoding="utf-8"))["posts"]
    for post in posts:
        check_post(post, base)
    reasons = skip_reasons(posts, ledger, args.include_stale)
    if not args.post:
        print(f"[dry-run] {len(posts)} post(s) from {manifest_path}; nothing sent (add --post to publish)")
        for i, (post, reason) in enumerate(zip(posts, reasons, strict=True), 1):
            text, status = (
                post_text(post),
                f"skipped: {reason}" if reason else "would post",
            )
            print(f"\n--- post {i}/{len(posts)}, {post['key']}: {status} ({graphemes(text)}/{MAX_GRAPHEMES} graphemes)")
            print(text)
            for image in post["images"]:
                kb = (base / image["path"]).stat().st_size / 1000
                print(f"  [image] {image['path']} {image['width']}x{image['height']} {kb:.0f} KB")
                print(f"    alt: {image['alt']}")
        return
    for post, reason in zip(posts, reasons, strict=True):
        if reason:
            print(f"{post['key']}: skipped: {reason}")
    if all(reasons):
        return  # nothing to post: no login
    if os.environ.get("GITHUB_REPOSITORY") == GITHUB_REPO:
        raise PostError(f"refusing to post from {GITHUB_REPO}'s own GitHub Actions; copy the template to your repo")
    handle, password = (
        os.environ.get("BSKY_HANDLE"),
        os.environ.get("BSKY_APP_PASSWORD"),
    )
    if not (handle and password):
        raise PostError("set BSKY_HANDLE and BSKY_APP_PASSWORD (a Bluesky app password) to post")
    client = Bluesky(session, os.environ.get("BSKY_SERVICE") or "https://bsky.social")
    client.login(handle, password)
    threads: dict[str, tuple[dict[str, str], dict[str, str]]] = {}  # thread -> (root, latest) refs
    for post, reason in zip(posts, reasons, strict=True):
        key, thread = post["key"], post["thread"]
        if reason:
            entry = ledger[key] if ledger.get(key, {}).get("status") == "posted" else None
            if entry:  # a later post of this thread replies to it
                ref = {"uri": entry["uri"], "cid": entry["cid"]}
                threads[thread] = (
                    threads[thread][0] if thread in threads else ref,
                    ref,
                )
            continue
        embeds = client.upload(post["images"], base)
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        ledger[key] = {
            "status": "pending",
            "at": now,
        }  # recorded first, so an unclear failure is never re-sent
        write_ledger(ledger_path, ledger)
        try:
            ref = client.create(post_text(post), embeds, threads.get(thread))
        except PostError as e:
            if not e.ambiguous:  # Bluesky refused it: nothing was posted, so a re-run may try again
                del ledger[key]
                write_ledger(ledger_path, ledger)
            raise
        ledger[key] = {
            "status": "posted",
            "uri": ref["uri"],
            "cid": ref["cid"],
            "at": now,
        }
        write_ledger(ledger_path, ledger)  # after every post, so a thread that fails partway resumes there
        threads[thread] = (threads[thread][0] if thread in threads else ref, ref)
        print(f"{key}: posted {ref['uri']}")


# ---------------------------------------------------------------------------------------------------------------------
# CLI


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    lb = sub.add_parser("leaderboard", help="a season leaders table")
    lb.add_argument("--league", required=True, choices=sorted(LEAGUES))
    lb.add_argument(
        "--season",
        type=int,
        help="the season (the year it ends for NBA/NHL); default: the current one",
    )
    lb.add_argument(
        "--stat",
        help="an ESPN leaders category, e.g. rushingYards, assistsPerGame, ERA, goals",
    )
    lb.add_argument("--top", type=int, help="rows (default 10 square, 5 landscape)")
    lb.add_argument("--size", choices=sorted(SIZES), default="square")
    gd = sub.add_parser("gameday", help="final-score cards and a player-of-the-game card")
    gd.add_argument("--league", required=True, choices=sorted(LEAGUES))
    gd.add_argument("--date", type=dt.date.fromisoformat, default=dt.date.today() - dt.timedelta(days=1),
                    help="YYYY-MM-DD (default: yesterday)")  # fmt: skip
    gd.add_argument(
        "--max-games",
        type=int,
        default=8,
        help="cards to draw, ranked teams first (default 8)",
    )
    po = sub.add_parser("post", help="post a manifest's images (dry-run unless --post)")
    po.add_argument("--manifest", help="default: the newest <out>/<date>/manifest.json")
    po.add_argument(
        "--ledger",
        help="the posted-ledger (default: posted.json beside the dated folders)",
    )
    po.add_argument("--network", choices=["bluesky"], default="bluesky")
    po.add_argument(
        "--post",
        action="store_true",
        help="really post (needs BSKY_HANDLE and BSKY_APP_PASSWORD)",
    )
    po.add_argument(
        "--include-stale",
        action="store_true",
        help="also post stale posts (old games, final seasons)",
    )
    for p in (lb, gd, po):
        p.add_argument(
            "--out",
            default="out",
            help="output root; files go to <out>/<today>/ (default out)",
        )
    args = parser.parse_args(argv)
    for name in ("top", "max_games"):
        if getattr(args, name, None) is not None and getattr(args, name) < 1:
            parser.error(f"--{name.replace('_', '-')} must be at least 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    t0 = time.perf_counter()
    try:
        if args.command == "post":
            run_post(args)
            return 0
        manifest = run_leaderboard(args) if args.command == "leaderboard" else run_gameday(args)
    except (NoData, PostError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except requests.RequestException as e:  # the message would name hosts and URLs; the type is enough
        print(
            f"error: network error ({type(e).__name__}); try again later",
            file=sys.stderr,
        )
        return 1
    print(f"wrote {manifest} ({time.perf_counter() - t0:.1f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

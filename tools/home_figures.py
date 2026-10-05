"""Draw the home page figures with sdvplot's matplotlib adapter, in the docs site's light and dark colors.

Usage: uv run python tools/home_figures.py

Writes docs/static/img/home/<name>-light.png and <name>-dark.png, and docs/src/data/home_figures.json (each figure's
name, alt text, caption and pixel size; docs/src/pages/index.tsx reads it). Drawing downloads logos and headshots (the
sdv-assets CDN, ESPN), so this is not part of the offline docs build: the weekly live-tests-cron runs it and opens a
refresh PR when a figure changes. Every plotted value comes from sdvplot itself (teams(), marks(), palette()); the alt
text is computed from the same values. All figures are drawn before anything is written, so a failure leaves the
committed set untouched. Needs the mpl and svg extras (uv sync --all-extras).
"""

from __future__ import annotations

import io
import json
import sys
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import polars as pl  # noqa: E402

import sdvplot  # noqa: E402
from sdvplot._contrast import contrast  # noqa: E402
from sdvplot._errors import SdvplotWarning  # noqa: E402

IMG = ROOT / "docs" / "static" / "img" / "home"
DATA = ROOT / "docs" / "src" / "data" / "home_figures.json"
SIZE = (6.4, 4.0)  # inches; with DPI, 960 x 600 px: sharp at the ~550 px a figure gets in the home grid
DPI = 150
MODES = {  # the family theme's surface, text and border colors (docs/src/css/sdv-theme.css)
    "light": {"bg": "#ffffff", "fg": "#0e1626", "line": "#d8e0eb"},
    "dark": {"bg": "#111b2e", "fg": "#e9eef6", "line": "#223350"},
}
# ESPN athlete ids, one player per league; the names are ESPN's display names for these ids (checked 2026-10-04)
PLAYERS = [
    ("nfl", "3139477", "Patrick Mahomes"),
    ("nba", "3112335", "Nikola Jokic"),
    ("wnba", "3149391", "A'ja Wilson"),
    ("mlb", "30836", "Mike Trout"),
    ("nhl", "3895074", "Connor McDavid"),
]


def nhl_decades(ax: Any, variant: str) -> str:
    """NHL logos stacked by the decade of the first season in each team's archived logo marks."""
    nhl = sdvplot.teams("nhl")
    first = {}
    for team_id, abbr in zip(nhl["team_id"], nhl["abbr"], strict=True):
        season = sdvplot.marks(team_id, "nhl").filter(pl.col("mark_type") == "logo")["valid_from"].min()
        if season is not None:
            first[abbr] = int(season)
    stacks: dict[int, list[str]] = {}
    for abbr, season in sorted(first.items(), key=lambda kv: (kv[1], kv[0])):
        stacks.setdefault(season // 10 * 10, []).append(abbr)
    xs, ys, teams = [], [], []
    for decade, abbrs in stacks.items():
        for i, abbr in enumerate(abbrs):
            xs.append(decade + 5)
            ys.append(i + 1)
            teams.append(abbr)
    ax.set_xlim(1908, 2032)
    ax.set_ylim(0.3, max(ys) + 0.7)
    ax.set_xticks(range(1915, 2030, 20), [f"{d}s" for d in range(1910, 2030, 20)])
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Decade of the first season in the team's archived logos")
    sdvplot.add_logos(ax, xs, ys, teams, league="nhl", height=0.11, variant=variant)
    return "NHL team logos stacked by decade: " + "; ".join(f"{d}s: {', '.join(a)}" for d, a in stacks.items()) + "."


def afc_contrast(ax: Any, variant: str) -> str:
    """Each AFC team's primary-secondary contrast, a bar in its two colors, logos on the axis."""
    afc = sdvplot.teams("nfl").filter(pl.col("conference_id") == "nfl:afc")["abbr"].to_list()
    primary = sdvplot.palette("nfl", teams=afc)
    secondary = sdvplot.palette("nfl", "secondary", teams=afc)
    ratio = {t: contrast(primary[t], secondary[t]) for t in afc}
    order = sorted(afc, key=lambda t: (ratio[t], t))
    ax.bar(
        order,
        [ratio[t] for t in order],
        color=[primary[t] for t in order],
        edgecolor=[secondary[t] for t in order],
        linewidth=2,
    )
    ax.set_ylabel("Contrast, primary to secondary")
    ax.set_ylim(0, max(ratio.values()) * 1.08)
    sdvplot.axis_logos(ax, "x", league="nfl", height=0.09, variant=variant)
    return "Bar chart of the contrast ratio between each AFC team's primary and secondary color, lowest first: " + (
        ", ".join(f"{t} {ratio[t]:.1f}" for t in order) + "."
    )


def montreal_eras(ax: Any, variant: str) -> str:
    """One franchise's logos through time: add_logos with one season per mark, four to a row."""
    marks = sdvplot.marks("MTL", "nhl").filter(
        (pl.col("mark_type") == "logo") & (pl.col("variant") == "default") & pl.col("valid_from").is_not_null()
    )
    seasons, seen = [], set()
    for season in sorted(marks["valid_from"].to_list()):
        url = sdvplot.logo_url("MTL", "nhl", season=season)
        if url not in seen:
            seen.add(url)
            seasons.append(season)
    xs = [i % 4 for i in range(len(seasons))]
    ys = [-(i // 4) for i in range(len(seasons))]
    ax.set_xlim(-0.6, 3.6)
    ax.set_ylim(min(ys) - 0.7, 0.5)
    ax.set_axis_off()
    sdvplot.add_logos(ax, xs, ys, ["MTL"] * len(seasons), league="nhl", season=seasons, height=0.2, variant=variant)
    for x, y, season in zip(xs, ys, seasons, strict=True):
        ax.text(x, y - 0.42, str(season), ha="center", va="center")
    return f"The {len(seasons)} Montreal Canadiens logos in the archive, in order, first used in " + (
        ", ".join(str(s) for s in seasons) + "."
    )


def headshots(ax: Any, variant: str) -> str:
    """One headshot per league, by ESPN athlete id: three on the top row, two below. Headshots have no variant."""
    spots = [(0, 0), (1, 0), (2, 0), (0.5, -1), (1.5, -1)]
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylim(-1.75, 0.45)
    ax.set_axis_off()
    for (x, y), (league, athlete, name) in zip(spots, PLAYERS, strict=True):
        sdvplot.add_headshots(ax, [x], [y], [athlete], league=league, height=0.3)
        ax.text(x, y - 0.5, f"{name}, {league.upper()}", ha="center", va="center")
    return "ESPN headshots of " + ", ".join(f"{name} ({league.upper()})" for league, _, name in PLAYERS) + "."


# name, caption, draw(ax, logo variant) -> alt text
FIGURES: list[tuple[str, str, Callable[[Any, str], str]]] = [
    (
        "nhl-decades",
        "add_logos() as scatter points: NHL teams, stacked by the decade their archived logos begin (marks()).",
        nhl_decades,
    ),
    (
        "afc-colors",
        "Bars in each AFC team's two colors from palette(), their contrast ratio as the height, and axis_logos() "
        "on the axis.",
        afc_contrast,
    ),
    (
        "montreal-eras",
        "One add_logos() call with season=: the mark Montreal used each season, from the logo archive.",
        montreal_eras,
    ),
    (
        "headshots",
        "add_headshots() with ESPN athlete ids, one player from each of five leagues.",
        headshots,
    ),
]


def draw(fn: Callable[[Any, str], str], mode: str) -> tuple[bytes, str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    c = MODES[mode]
    rc = {
        "figure.facecolor": c["bg"],
        "axes.facecolor": c["bg"],
        "axes.edgecolor": c["line"],
        "axes.labelcolor": c["fg"],
        "text.color": c["fg"],
        "xtick.color": c["fg"],
        "ytick.color": c["fg"],
        "font.size": 13,  # in-figure text stays readable where a phone shows the 960 px PNG at ~360 px
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
    with plt.rc_context(rc):
        fig, ax = plt.subplots(figsize=SIZE, dpi=DPI, layout="constrained")
        alt = fn(ax, "dark" if mode == "dark" else "default")  # the archive's marks for a dark background
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=DPI, metadata={"Software": None})  # no version stamp: same data, same bytes
        plt.close(fig)
    return buf.getvalue(), alt


def main() -> int:
    files: dict[str, bytes] = {}
    manifest = []
    try:
        with warnings.catch_warnings():
            # an adapter skips an image it cannot fetch with only an SdvplotWarning: here that is a failed run, not
            # a PNG with a logo missing
            warnings.simplefilter("error", SdvplotWarning)
            for name, caption, fn in FIGURES:
                for mode in MODES:
                    png, alt = draw(fn, mode)
                    files[f"{name}-{mode}.png"] = png
                manifest.append(
                    {
                        "name": name,
                        "alt": alt,
                        "caption": caption,
                        "width": int(SIZE[0] * DPI),
                        "height": int(SIZE[1] * DPI),
                    }
                )
                print(f"drew {name}")
    except Exception as e:  # noqa: BLE001 - nothing has been written yet: the committed set stays as it is
        print(f"failed, nothing written: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    IMG.mkdir(parents=True, exist_ok=True)
    for old in IMG.glob("*.png"):  # every file here is drawn by this script: drop those of removed figures
        old.unlink()
    for file, png in files.items():
        (IMG / file).write_bytes(png)
    DATA.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {len(files)} images to {IMG} and {DATA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

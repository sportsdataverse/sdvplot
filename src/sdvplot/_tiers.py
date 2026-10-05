"""team_tiers' data preparation and look, ported from sdvplotR ``sdv_team_tiers()``: the matplotlib and plotnine
adapters only draw what ``prepare()`` returns, so ranking, tier lines, labels and limits have one implementation."""

from __future__ import annotations

import textwrap
from collections import Counter
from dataclasses import dataclass
from typing import Any, Literal

import narwhals as nw

from sdvplot._index import teams as teams_index
from sdvplot._placement import _missing, _real, _warn_skipped, check_alpha, check_height
from sdvplot._resolve import _unpack, resolve

BG, LINES, MUTED = "#1e1e1e", "#e0e0e0", "#8e8e93"  # sdvplotR's dark theme: background, tier lines, subtitle/caption
# theme -> (background, tier lines, title and labels, subtitle and caption). "light" is sdvplot's: dark logos (Ohio
# State, Texas A&M, Penn State) vanish on sdvplotR's dark background
THEMES: dict[str, tuple[str, str, str, str]] = {
    "dark": (BG, LINES, "#ffffff", MUTED),
    "light": ("#ffffff", "#3a3a3c", "#1e1e1e", "#636366"),
}
# theme -> the mark variant variant="auto" draws: the archive's dark-background logos on "dark". A team with no "dark"
# mark gets its default one from select_mark, so no team drops out (sdvplotR draws the default logo on either)
AUTO_VARIANT = {"dark": "dark", "light": "default"}
SUBTITLE = "created with the #sdvplot Tiermaker"
TIER_DESC = {1: "Elite", 2: "Very Good", 3: "Medium", 4: "Bad", 5: "What are they doing?", 6: "", 7: ""}
# About the largest logo height (a fraction of the panel height) at which 32 square logos in 5 tiers (7, 7, 6, 6,
# 6) neither overlap nor leave the panel at matplotlib's and plotnine's default 6.4 x 4.8 in figure; it stands in for
# sdvplotR's width = 0.075 npc. tests/test_team_tiers.py measures it.
DEFAULT_HEIGHT = 0.1


@dataclass(frozen=True)
class Tiers:
    """What a tier plot draws: one entry per resolved team in x/y/team_ids/labels, then the axes and titles."""

    x: list[Any]  # tier_rank
    y: list[Any]  # tier_no
    team_ids: list[str]
    labels: list[str]  # the team's abbreviation (else the value given), which devel=True draws
    lines: list[float]  # the tier separators, at tier +- 0.5
    breaks: list[Any]  # the tiers, top (smallest tier_no) first
    break_labels: list[str]
    xlim: tuple[float, float]
    ylim: tuple[float, float]  # (top, bottom) in tier_no units
    title: str
    subtitle: str | None
    caption: str | None
    height: float
    alpha: float
    variant: str  # the mark variant the logos are drawn in ("auto" already resolved by the theme)
    bg: str  # the theme's colors (THEMES)
    line_color: str
    text: str
    muted: str


def _wrap(text: str) -> str:
    """R's ``strwrap(text, 15)``: lines under 15 characters, a longer word kept whole."""
    return "\n".join(textwrap.wrap(text, 14, break_long_words=False, break_on_hyphens=False))


def prepare(
    data: Any,
    league: str,
    *,
    title: str | None = None,
    subtitle: str | None = SUBTITLE,
    caption: str | None = None,
    tier_desc: dict[Any, str] | None = None,
    presort: bool = False,
    alpha: float = 0.8,
    height: float | None = None,
    no_line_below_tier: Any = None,
    theme: Literal["dark", "light"] = "dark",
    variant: str = "auto",
) -> Tiers:
    """Validate ``data`` and compute everything a tier plot draws (see the adapters' ``team_tiers``)."""
    if theme not in THEMES:
        raise ValueError(f"theme must be one of {sorted(THEMES)}, got {theme!r}")
    frame = nw.from_native(data, eager_only=True)  # TypeError unless a pandas/polars (narwhals-supported) frame
    missing = [c for c in ("tier_no", "team") if c not in frame.columns]
    if missing:
        raise ValueError(f"data must have the columns tier_no and team; missing {', '.join(missing)}")
    h = DEFAULT_HEIGHT if height is None else check_height(height)
    a = check_alpha(alpha)
    tiers, teams = frame["tier_no"].to_list(), frame["team"].to_list()
    # a pandas column with a NaN is float: 1.0 back to 1, so tier_desc's R-style "1" keys (and the ticks) match
    tiers = [int(t) if isinstance(t, float) and t.is_integer() else t for t in tiers]
    given = frame["tier_rank"].to_list() if "tier_rank" in frame.columns and not presort else None

    absent = {i for i, t in enumerate(tiers) if _missing(t) or (given is not None and _missing(given[i]))}
    _warn_skipped("with a missing tier_no or tier_rank", [teams[i] for i in sorted(absent)])
    rows = [i for i in range(len(tiers)) if i not in absent]
    if not rows:
        raise ValueError("data has no rows with a tier_no")
    if not all(_real(tiers[i]) and (given is None or _real(given[i])) for i in rows):
        raise TypeError("tier_no and tier_rank must hold numbers (tier 1 is the top tier)")
    if presort:  # sdvplotR: arrange(tier_no, team), then rank within the tier
        rows.sort(key=lambda i: (tiers[i], _missing(teams[i]), str(teams[i])))  # a missing team last, as R's NA
    if given is None:
        seen: Counter[Any] = Counter()
        ranks = {}
        for i in rows:
            seen[tiers[i]] += 1
            ranks[i] = seen[tiers[i]]
    else:
        ranks = {i: given[i] for i in rows}

    # Rank first, then resolve, as sdvplotR does: an unknown team keeps its slot (and the x range) but draws nothing.
    ids = resolve([teams[i] for i in rows], league)
    kept = [(i, team_id) for i, team_id in zip(rows, ids, strict=True) if team_id is not None]
    abbr = dict(teams_index(league).select("team_id", "abbr").iter_rows())  # devel draws it, as sdvplotR does
    levels = sorted({tiers[i] for i in rows})
    skip = set(_unpack(no_line_below_tier)[0]) if no_line_below_tier is not None else set()
    desc: dict[Any, str] = TIER_DESC if tier_desc is None else tier_desc
    lo, hi = min(ranks.values()), max(ranks.values())
    pad = 0.5 if lo == hi else 0.05 * (hi - lo)  # a ggplot continuous scale's default expansion
    return Tiers(
        x=[ranks[i] for i, _ in kept],
        y=[tiers[i] for i, _ in kept],
        team_ids=[team_id for _, team_id in kept],
        labels=[abbr.get(team_id) or str(teams[i]) for i, team_id in kept],
        lines=[levels[0] - 0.5] + [t + 0.5 for t in levels if t not in skip],
        breaks=levels,
        break_labels=[_wrap(desc.get(t, desc.get(str(t), ""))) for t in levels],
        xlim=(lo - pad, hi + pad),
        ylim=(levels[0] - 0.6, levels[-1] + 0.6),  # +- 0.5 around the tiers, plus sdvplotR's expansion(add = 0.1)
        title=f"{league.upper()} Team Tiers" if title is None else title,
        subtitle=subtitle,
        caption=caption,
        height=h,
        alpha=a,
        variant=AUTO_VARIANT[theme] if variant == "auto" else variant,  # any other value is select_mark's to check
        bg=THEMES[theme][0],
        line_color=THEMES[theme][1],
        text=THEMES[theme][2],
        muted=THEMES[theme][3],
    )

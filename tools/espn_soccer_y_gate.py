"""ESPN soccer y-orientation gate for pitch_coords(provider="espn") (spec 2026-10-05 §8.2).

Among shots whose ESPN commentary says "from the left/right side of the box", the side must agree with
field_position_y < 0.5 (= the shooter's left, = pitch_y > 0 under opta_y = 100 * (1 - y)) on at least 95%,
over >= 10 completed matches in >= 3 leagues and >= 50 such shots. Needs the network.

Run: uv run --group examples python tools/espn_soccer_y_gate.py [--dates 20250901-20251031] [--per-league 3]
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta

from sportsdataverse import soccer

LEAGUES = ("eng.1", "esp.1", "usa.1", "uefa.champions")
SIDE = re.compile(r"from the (left|right) side of the (?:box|six yard box)")


def _days(span: str) -> list[str]:
    """Expand YYYYMMDD-YYYYMMDD into single days: ESPN's soccer scoreboard rejects a date range (HTTP 400)."""
    a, b = (datetime.strptime(x, "%Y%m%d") for x in span.split("-"))
    return [(a + timedelta(days=i)).strftime("%Y%m%d") for i in range((b - a).days + 1)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--dates", default="20250901-20251031", help="day span YYYYMMDD-YYYYMMDD, scanned one day at a time"
    )
    ap.add_argument("--per-league", type=int, default=3, help="completed matches to read per league")
    a = ap.parse_args(argv)
    agree = total = 0
    used: list[str] = []
    for league in LEAGUES:
        done: list[str] = []
        for day in _days(a.dates):
            if len(done) >= a.per_league:
                break
            board = soccer.espn_soccer_scoreboard(league, dates=day, return_parsed=False)
            done += [e["id"] for e in board.get("events", []) if e.get("status", {}).get("type", {}).get("completed")]
        for event_id in done[: a.per_league]:
            summary = soccer.espn_soccer_summary(league, event_id=int(event_id), return_parsed=False)
            used.append(f"{league}:{event_id}")
            for item in summary.get("commentary", []):
                play = item.get("play") or {}
                m = SIDE.search(item.get("text") or "")
                fx, fy = play.get("fieldPositionX") or 0, play.get("fieldPositionY") or 0
                if not m or (fx == 0 and fy == 0):
                    continue
                total += 1
                agree += (m.group(1) == "left") == (fy < 0.5)
    rate = agree / total if total else 0.0
    leagues = {u.split(":")[0] for u in used}
    print(f"matches={len(used)} leagues={len(leagues)} shots_with_side={total} agree={agree} rate={rate:.3f}")
    print("events:", " ".join(used))
    ok = len(used) >= 10 and len(leagues) >= 3 and total >= 50 and rate >= 0.95
    print("GATE", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

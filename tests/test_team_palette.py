"""The ported team palette (sdvplot._team_palette) against sdvplot-js's team-palette.ts, on the 12 palette cases of the
shared deck.gl fixture (tests/fixtures/deckgl_shared.json, the same bytes sdvplot-js commits as fixtures/deckgl/shared.json):
every NBA, NFL, MLB and NHL team in standard order on #181a1b, #000000 and #ffffff. Needs no optional library.

The port and the fixture are byte-identical copies of the ones on the pydeck branch (sdvplot #132), so the two add the
same files and merge cleanly; tests/test_pydeck_shared.py checks the same 12 cases there."""

import hashlib
import json
import math
import warnings
from pathlib import Path

import pytest

from sdvplot import _team_palette
from sdvplot._team_palette import team_palette

PATH = Path(__file__).parent / "fixtures" / "deckgl_shared.json"
SHA256 = (
    "da15c1e50d487eba07b1b492dc7ba839e3b63efbc4732f59005aac06e69a4484"  # pinned in sdvplot-js's deckgl-shared.test.ts
)
CASES = json.loads(PATH.read_text(encoding="utf-8"))["palettes"]


def test_the_fixture_is_the_file_sdvplot_js_commits_byte_for_byte():
    assert hashlib.sha256(PATH.read_bytes()).hexdigest() == SHA256
    assert len(CASES) == 12
    assert {c["league"] for c in CASES} == {"nba", "nfl", "mlb", "nhl"}
    assert {c["background"] for c in CASES} == {"#181a1b", "#000000", "#ffffff"}


# Python 3.10 has no math.cbrt: the port falls back to t ** (1 / 3); both must give sdvplot-js's colors
CBRT = {"cbrt": getattr(math, "cbrt", None), "fallback": lambda t: t ** (1 / 3)}


@pytest.mark.parametrize("cbrt", CBRT, ids=CBRT.keys())
@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c['league']}-{c['background']}")
def test_the_ported_team_palette_gives_sdvplot_js_colors_on_every_team(monkeypatch, case, cbrt):
    if CBRT[cbrt] is None:
        pytest.skip("math.cbrt is Python 3.11+; this interpreter runs the fallback case")
    monkeypatch.setattr(_team_palette, "_cbrt", CBRT[cbrt])
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        got = team_palette(case["colors"], case["alts"], case["background"], case["labels"])
    assert got == case["expected"]

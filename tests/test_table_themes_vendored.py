"""Drift gate: the vendored table-theme registry must match its sha256 sidecar."""

from __future__ import annotations

import hashlib
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "src" / "sdvplot" / "data"
HINT = "run sdvplot-js/tools/sync-table-themes.mjs"


def test_table_themes_vendored_matches_sha256() -> None:
    js = DATA / "table_themes.json"
    sidecar = DATA / "table_themes.json.sha256"
    assert js.is_file() and sidecar.is_file(), f"vendored registry missing: {HINT}"
    actual = hashlib.sha256(js.read_bytes()).hexdigest()
    expected = sidecar.read_text().strip()
    assert actual == expected, f"table_themes.json drifted from its .sha256 ({actual} != {expected}): {HINT}"

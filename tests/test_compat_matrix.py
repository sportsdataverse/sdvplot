"""docs/COMPATIBILITY.md stays true: every test it names exists."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "COMPATIBILITY.md"


def test_every_test_the_compatibility_page_names_exists():
    refs = set(re.findall(r"`(tests/test_\w+\.py)(?:::(\w+))?`", PAGE.read_text(encoding="utf-8")))
    assert len(refs) >= 20
    missing = []
    for path, name in sorted(refs):
        source = ROOT / path
        if not source.is_file() or (name and not re.search(rf"^def {name}\(", source.read_text("utf-8"), re.M)):
            missing.append(f"{path}::{name}" if name else path)
    assert missing == []

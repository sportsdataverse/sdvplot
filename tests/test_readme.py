"""The root README is the PyPI long description: it must render correctly away from the repository."""

import re
from pathlib import Path

README = (Path(__file__).parents[1] / "README.md").read_text(encoding="utf-8")

# markdown links and images, and HTML href/src attributes
_TARGETS = re.findall(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)", README) + re.findall(
    r"""(?:href|src)\s*=\s*["']([^"']+)""", README
)


def test_no_doctoc_block() -> None:
    assert "<!-- START doctoc" not in README


def test_every_link_is_absolute_or_an_anchor() -> None:
    assert _TARGETS, "the README should have links"
    bad = [t for t in _TARGETS if not (t.startswith("https://") or t.startswith("#"))]
    assert not bad, f"relative or non-https README targets render broken on PyPI: {bad}"

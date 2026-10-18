"""Render the registry table in docs/docs/concepts/table-themes.md from the vendored table_themes.json.

Run: uv run python tools/gen_table_theme_docs.py [--check]   (--check exits 1 when the page is stale)

Only the block between the BEGIN/END markers is generated; the rest of the page is hand-written.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs/docs/concepts/table-themes.md"
DATA = ROOT / "src/sdvplot/data/table_themes.json"
BEGIN, END = "<!-- BEGIN table-themes (tools/gen_table_theme_docs.py) -->", "<!-- END table-themes -->"
IMG = "https://plot.sportsdataverse.org/img/table-themes"


def render() -> str:
    themes = json.loads(DATA.read_text(encoding="utf-8"))["themes"].values()
    rows = ["| Theme | Source | Category | Dark | Preview |", "| --- | --- | --- | --- | --- |"]
    for t in sorted(themes, key=lambda t: (t["category"], t["id"])):
        dark = t["darkPolicy"] != "none"
        links = [f"[light]({IMG}/{t['id']}-light.webp)"] + ([f"[dark]({IMG}/{t['id']}-dark.webp)"] if dark else [])
        rows.append(
            f"| `{t['id']}` | [{t['source']}]({t['url']}) | {t['category']} | {t['darkPolicy']} | {' / '.join(links)} |"
        )
    return "\n".join(rows)


def main(argv: list[str]) -> int:
    text = PAGE.read_text(encoding="utf-8")
    head, rest = text.split(BEGIN, 1)
    tail = rest.split(END, 1)[1]
    new = f"{head}{BEGIN}\n\n{render()}\n\n{END}{tail}"
    if "--check" in argv:
        if new != text:
            print(f"{PAGE.name} is stale: run uv run python tools/gen_table_theme_docs.py", file=sys.stderr)
            return 1
        return 0
    PAGE.write_text(new, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

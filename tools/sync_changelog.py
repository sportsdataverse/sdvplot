"""Copy CHANGELOG.md to the docs site's News page (docs/src/pages/CHANGELOG.md), under the front matter that gives the
page its title and search description. The `sync-docs-changelog` pre-commit hook runs it; tests/test_repo_files.py
checks the copy.

Usage: uv run python tools/sync_changelog.py
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_COPY = ROOT / "docs" / "src" / "pages" / "CHANGELOG.md"
FRONT_MATTER = (
    b"---\n"
    b"title: Changelog\n"
    b"description: Every sdvplot release and what it added, changed and fixed, newest first, with what is on main and "
    b"not yet released at the top.\n"
    b"---\n\n"
)


def main() -> int:
    DOCS_COPY.write_bytes(FRONT_MATTER + (ROOT / "CHANGELOG.md").read_bytes())
    subprocess.run(["git", "add", str(DOCS_COPY)], cwd=ROOT, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Repository-level invariants (line endings, mirrors) that no module test owns."""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


def _tracked() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [ROOT / p for p in out.splitlines()]


def test_no_committed_text_file_has_crlf():
    binary = {".parquet", ".png", ".ico", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".gz", ".woff", ".woff2"}
    bad = [p.relative_to(ROOT).as_posix() for p in _tracked()
           if p.is_file() and p.suffix not in binary and b"\r\n" in p.read_bytes()]
    assert bad == [], f"CRLF in: {bad[:10]}"


DOTFILES = [".markdownlint-cli2.yaml", ".coderabbit.yaml", ".yamlfmt", ".python-version", ".env.example",
            ".vscode/settings.json", ".github/PULL_REQUEST_TEMPLATE.md", ".github/ISSUE_TEMPLATE/bug_report.yml",
            ".github/ISSUE_TEMPLATE/feature_request.yml", ".github/ISSUE_TEMPLATE/wrong_team_or_logo.yml",
            ".github/ISSUE_TEMPLATE/config.yml"]


def test_sdv_py_dotfiles_exist_and_parse():
    import json

    yaml = pytest.importorskip("yaml")  # pyyaml joins the lint group in Task 3
    for rel in DOTFILES:
        p = ROOT / rel
        assert p.is_file(), rel
        if p.suffix in (".yaml", ".yml") or p.name == ".yamlfmt":
            yaml.safe_load(p.read_text(encoding="utf-8"))
        if p.suffix == ".json":
            json.loads(p.read_text(encoding="utf-8"))
    assert (ROOT / ".python-version").read_text().strip() == "3.13"
    assert "SDVPLOT_CACHE_DIR" in (ROOT / ".env.example").read_text()

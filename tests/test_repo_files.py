"""Repository-level invariants (line endings, mirrors) that no module test owns."""

import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parents[1]


def _tracked() -> list[Path]:
    if not (ROOT / ".git").exists():  # an unpacked sdist ships tests/ but is not a checkout
        pytest.skip("not a git checkout")
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [ROOT / p for p in out.splitlines()]


def test_no_committed_text_file_has_crlf():
    binary = {".parquet", ".png", ".ico", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".gz", ".woff", ".woff2"}
    bad = [
        p.relative_to(ROOT).as_posix()
        for p in _tracked()
        if p.is_file() and p.suffix not in binary and b"\r\n" in p.read_bytes()
    ]
    assert bad == [], f"CRLF in: {bad[:10]}"


DOTFILES = [
    ".markdownlint-cli2.yaml",
    ".coderabbit.yaml",
    ".yamlfmt",
    ".python-version",
    ".env.example",
    ".vscode/settings.json",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/wrong_team_or_logo.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
]


def test_sdv_py_dotfiles_exist_and_parse():
    import json

    for rel in DOTFILES:
        p = ROOT / rel
        assert p.is_file(), rel
        if p.suffix in (".yaml", ".yml") or p.name == ".yamlfmt":
            yaml.safe_load(p.read_text(encoding="utf-8"))
        if p.suffix == ".json":
            json.loads(p.read_text(encoding="utf-8"))
    assert (ROOT / ".python-version").read_text().strip() == "3.13"
    assert "SDVPLOT_CACHE_DIR" in (ROOT / ".env.example").read_text()


def test_docs_changelog_mirrors_the_root_changelog():  # Review Focus 5
    root = (ROOT / "CHANGELOG.md").read_bytes()
    assert root.startswith(b"<!-- START doctoc") or root.startswith(b"# Changelog")
    assert (ROOT / "docs" / "src" / "pages" / "CHANGELOG.md").read_bytes() == root


def test_contributor_files_exist():
    for rel in ("CHANGELOG.md", "CONTRIBUTING.md", "CLAUDE.md", ".github/copilot-instructions.md"):
        assert (ROOT / rel).is_file(), rel
    assert "## [Unreleased]" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_unreleased_is_the_first_changelog_section():
    headings = [ln for ln in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines() if ln.startswith("## ")]
    assert headings[0] == "## [Unreleased]"

"""Repository-level invariants (line endings, mirrors) that no module test owns."""

import os
import re
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


# release readiness: release.yml sets SDVPLOT_RELEASE_VERSION to the tag, and the release's test run then refuses a
# README without a PyPI install line (it becomes the PyPI page, immutable for that version) or an undated CHANGELOG

# `pip install sdvplot` or `pip install "sdvplot[mpl]"`, not `pip install "sdvplot[mpl] @ git+https://..."`
_PYPI_INSTALL = re.compile(r'pip install "?sdvplot(?:\[[\w,]*\])?"?(?![\w\[]|\s*@)')


def release_blockers(version: str, readme: str, changelog: str) -> list[str]:
    """What stops ``version`` from being released with this README and CHANGELOG (empty when it is ready)."""
    problems = []
    if "not on PyPI yet" in readme or not _PYPI_INSTALL.search(readme):
        problems.append("README.md does not install from PyPI: merge the install-line PR before tagging")
    if not re.search(rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$", changelog, re.M):
        problems.append(f"CHANGELOG.md has no dated '## [{version}] - YYYY-MM-DD' heading")
    unreleased = re.search(r"^## \[Unreleased\]\n(.*?)(?=^## )", changelog, re.M | re.S)
    if unreleased and unreleased.group(1).strip():
        problems.append(f"CHANGELOG.md's [Unreleased] section still has entries: move them under [{version}]")
    return problems


_READY_README = "pip install sdvplot\n"
_READY_CHANGELOG = "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 2026-10-06\n\n### Added\n- x\n"


@pytest.mark.parametrize(
    "readme",
    [
        _READY_README,
        'pip install "sdvplot[mpl,svg]"\n',
        # a development-version line beside the PyPI one is fine
        "pip install sdvplot\n\nThe development version: pip install git+https://github.com/sportsdataverse/sdvplot\n",
    ],
)
def test_release_blockers_pass_a_ready_release(readme):
    assert release_blockers("0.1.0", readme, _READY_CHANGELOG) == []


@pytest.mark.parametrize(
    ("readme", "changelog", "problem"),
    [
        ("sdvplot is not on PyPI yet. pip install sdvplot", _READY_CHANGELOG, "does not install from PyPI"),
        ('pip install "sdvplot[mpl] @ git+https://github.com/sportsdataverse/sdvplot"', _READY_CHANGELOG, "PyPI"),
        ("pip install git+https://github.com/sportsdataverse/sdvplot", _READY_CHANGELOG, "PyPI"),
        (_READY_README, _READY_CHANGELOG.replace("2026-10-06", "Unreleased"), "no dated"),
        (_READY_README, _READY_CHANGELOG.replace("0.1.0", "0.0.9"), "no dated"),
        (
            _READY_README,
            _READY_CHANGELOG.replace("## [Unreleased]\n", "## [Unreleased]\n\n### Fixed\n- y\n"),
            "still has",
        ),
    ],
)
def test_release_blockers_catch_each_problem(readme, changelog, problem):
    assert any(problem in p for p in release_blockers("0.1.0", readme, changelog))


def test_the_tagged_release_is_ready():
    version = os.environ.get("SDVPLOT_RELEASE_VERSION", "").removeprefix("v")
    if not version:
        pytest.skip("not a release run (release.yml sets SDVPLOT_RELEASE_VERSION)")
    readme, changelog = ((ROOT / f).read_text(encoding="utf-8") for f in ("README.md", "CHANGELOG.md"))
    assert release_blockers(version, readme, changelog) == []


def test_the_release_workflow_keeps_its_hardening():
    """release.yml's guards, which nothing else exercises before release day: dropping one would let an unready README
    or a poisoned cache reach PyPI with every check green."""
    path = ROOT / ".github" / "workflows" / "release.yml"
    if not path.exists():  # an unpacked sdist ships no .github
        pytest.skip("not a checkout")
    jobs = yaml.safe_load(path.read_text(encoding="utf-8"))["jobs"]
    steps = {name: job["steps"] for name, job in jobs.items()}
    run_tests = next(st for st in steps["test"] if st.get("name") == "Run tests")
    assert "github.ref_name" in run_tests["env"]["SDVPLOT_RELEASE_VERSION"]
    for name in ("test", "build"):
        uv = next(st for st in steps[name] if "setup-uv" in st.get("uses", ""))
        assert uv["with"]["enable-cache"] is False and uv["with"]["version"] != "latest", name
        checkout = next(st for st in steps[name] if "actions/checkout" in st.get("uses", ""))
        assert checkout["with"]["persist-credentials"] is False, name
    assert jobs["build"]["needs"] == "test" and jobs["publish-pypi"]["needs"] == "build"
    assert jobs["publish-pypi"]["permissions"] == {"id-token": "write"}
    assert jobs["publish-pypi"]["environment"]["name"] == "pypi"
    assert all("@" in st["uses"] and len(st["uses"].split("@")[1]) == 40 for j in jobs.values() for st in j["steps"]
               if "uses" in st)  # fmt: skip

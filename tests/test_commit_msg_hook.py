import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parents[1] / "tools" / "hooks" / "check_commit_msg.py"


def _run(tmp_path, msg):
    assert HOOK.is_file(), f"missing hook: {HOOK}"
    f = tmp_path / "MSG"
    f.write_text(msg, encoding="utf-8")
    return subprocess.run([sys.executable, str(HOOK), str(f)], capture_output=True, text=True)


def test_conventional_subject_passes(tmp_path):
    assert _run(tmp_path, "feat(marks): era-aware logos\n").returncode == 0


def test_non_conventional_subject_fails(tmp_path):
    r = _run(tmp_path, "added some stuff\n")
    assert r.returncode == 1
    assert "not a Conventional Commit" in r.stdout + r.stderr


def test_ai_coauthor_trailer_fails(tmp_path):
    r = _run(tmp_path, "fix: x\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n")
    assert r.returncode == 1
    assert "AI attribution is forbidden" in r.stdout + r.stderr


def test_generated_with_footer_fails(tmp_path):
    r = _run(tmp_path, "fix: x\n\nGenerated with Claude Code\n")
    assert r.returncode == 1
    assert "AI attribution is forbidden" in r.stdout + r.stderr

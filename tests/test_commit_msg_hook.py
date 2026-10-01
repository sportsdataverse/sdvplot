import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parents[1] / "tools" / "hooks" / "check_commit_msg.py"


def _run(tmp_path, msg):
    f = tmp_path / "MSG"
    f.write_text(msg, encoding="utf-8")
    return subprocess.run([sys.executable, str(HOOK), str(f)], capture_output=True, text=True).returncode


def test_conventional_subject_passes(tmp_path):
    assert _run(tmp_path, "feat(marks): era-aware logos\n") == 0


def test_non_conventional_subject_fails(tmp_path):
    assert _run(tmp_path, "added some stuff\n") != 0


def test_ai_coauthor_trailer_fails(tmp_path):
    assert _run(tmp_path, "fix: x\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n") != 0


def test_generated_with_footer_fails(tmp_path):
    assert _run(tmp_path, "fix: x\n\nGenerated with Claude Code\n") != 0

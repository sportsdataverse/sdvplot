"""Repository-level invariants (line endings, mirrors) that no module test owns."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]


def _tracked() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [ROOT / p for p in out.splitlines()]


def test_no_committed_text_file_has_crlf():
    binary = {".parquet", ".png", ".ico", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".zip", ".gz", ".woff", ".woff2"}
    bad = [p.relative_to(ROOT).as_posix() for p in _tracked()
           if p.is_file() and p.suffix not in binary and b"\r\n" in p.read_bytes()]
    assert bad == [], f"CRLF in: {bad[:10]}"

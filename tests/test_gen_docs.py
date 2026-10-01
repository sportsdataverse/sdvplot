import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("gen_docs", ROOT / "tools" / "gen_docs.py")
gd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gd)


def good(x: int, y: str = "a") -> str:
    """Join things.

    Args:
        x: A number.
        y: A label.

    Returns:
        str: The joined value.

    Example:
        ::

            good(1, "b")
    """
    return f"{x}{y}"


def no_example(x: int) -> int:
    """Double it.

    Args:
        x: A number.

    Returns:
        int: Twice x.
    """
    return 2 * x


def test_a_page_has_signature_params_returns_and_a_fenced_example():
    page, errors = gd.render_function("good", good, position=1)
    assert errors == []
    assert page.startswith("---\ntitle: good\nsidebar_label: good\nsidebar_position: 1\n---\n")
    assert "good(x: int, y: str = 'a') -> str" in page
    assert "| `x` | `int` | A number. |" in page
    assert '```python\ngood(1, "b")\n```' in page
    assert ">>>" not in page


def test_a_missing_example_is_a_validation_error():
    _, errors = gd.render_function("no_example", no_example, position=1)
    assert errors == ["no_example: missing Example:"]


def test_check_mode_detects_drift(tmp_path):
    out = tmp_path / "reference"
    assert gd.main(["--out", str(out)]) == 0
    assert gd.main(["--out", str(out), "--check"]) == 0
    page = next(out.glob("logo_url.md"))
    page.write_text(page.read_text() + "\nhand edit\n")
    assert gd.main(["--out", str(out), "--check"]) == 1


def test_the_committed_reference_is_current():
    assert gd.main(["--check"]) == 0


def optional(size: int | None = None, *names: str, **opts: str) -> str | None:
    """Pick one.

    Args:
        size: A size | or nothing.
        *names: Names.
        **opts: Options.

    Returns:
        str | None: The pick.

    Example:
        ::

            optional()
    """
    return None


def test_pipes_in_types_and_descriptions_do_not_split_table_cells():
    page, errors = gd.render_function("optional", optional, position=1)
    assert errors == []
    rows = [ln for ln in page.splitlines() if ln.startswith("| `")]
    assert len(rows) == 3
    for row in rows:
        assert len(re.split(r"(?<!\\)\|", row.strip().strip("|"))) == 3, row
    assert "| `size` | `int \\| None` | A size \\| or nothing. |" in page
    assert "| `*names` | `str` | Names. |" in page
    assert "| `**opts` | `str` | Options. |" in page

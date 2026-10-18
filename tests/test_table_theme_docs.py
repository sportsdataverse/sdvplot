import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("gen_table_theme_docs", ROOT / "tools" / "gen_table_theme_docs.py")
gtd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gtd)


def test_table_theme_page_is_current():
    """The generated block in concepts/table-themes.md matches the vendored registry."""
    assert gtd.main(["--check"]) == 0, "run: uv run python tools/gen_table_theme_docs.py"

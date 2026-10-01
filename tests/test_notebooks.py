import importlib.util
from pathlib import Path

import nbformat

ROOT = Path(__file__).parents[1]
NB = ROOT / "examples" / "notebooks"
spec = importlib.util.spec_from_file_location("render_notebooks", ROOT / "tools" / "render_notebooks.py")
rn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rn)


def test_every_tutorial_notebook_exists():
    assert [s for s, _, _ in rn.TUTORIALS] == ["01_quickstart", "02_colors", "03_logos_and_seasons", "04_headshots"]
    for stem, _, _ in rn.TUTORIALS:
        assert (NB / f"{stem}.ipynb").is_file(), stem


def test_notebooks_are_committed_without_outputs():  # Review Focus 4
    for path in sorted(NB.glob("*.ipynb")):
        nb = nbformat.read(path, as_version=4)
        for cell in nb.cells:
            if cell.cell_type == "code":
                assert cell.outputs == [] and cell.execution_count is None, f"{path.name} has outputs"


def test_rendered_tutorial_pages_exist():
    for stem, label, _pos in rn.TUTORIALS:
        page = ROOT / "docs" / "docs" / "tutorials" / f"{stem}.md"
        assert page.read_text(encoding="utf-8").startswith(f"---\ntitle: {label} tutorial\n"), stem

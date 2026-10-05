import importlib.util
import re
from pathlib import Path

import nbformat
import polars as pl
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook, new_output

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


def test_every_notebook_has_step_headings():
    for path in sorted(NB.glob("*.ipynb")):
        nb = nbformat.read(path, as_version=4)
        steps = sum(len(re.findall(r"^## ", c.source, re.M)) for c in nb.cells if c.cell_type == "markdown")
        assert steps >= 2, path.name


def _notebook(*outputs):
    nb = new_notebook()
    nb.cells = [new_markdown_cell("# T"), new_code_cell("x")]
    nb.cells[1].outputs = list(outputs)
    return nb


def test_a_cells_outputs_sit_in_one_sdv_output_block_after_its_code(tmp_path, monkeypatch):
    monkeypatch.setattr(rn, "OUT_DIR", tmp_path)
    nb = _notebook(
        new_output("stream", name="stdout", text="hi\n"),
        new_output("execute_result", data={"text/plain": "1"}, execution_count=1),
    )
    assert rn._to_markdown(nb, "t") == (
        '# T\n\n```python\nx\n```\n\n<div class="sdv-output">\n\n```text\nhi\n```\n\n```text\n1\n```\n\n</div>\n'
    )


def test_an_empty_print_draws_no_output_block(tmp_path, monkeypatch):
    monkeypatch.setattr(rn, "OUT_DIR", tmp_path)
    nb = _notebook(new_output("stream", name="stdout", text="\n"))
    assert "sdv-output" not in rn._to_markdown(nb, "t")


def test_a_polars_frame_becomes_a_table_while_a_pandas_frame_and_a_series_stay_text(tmp_path, monkeypatch):  # RF 5
    monkeypatch.setattr(rn, "OUT_DIR", tmp_path)
    nb = _notebook(
        new_output(
            "execute_result", data={"text/html": "<table/>", "text/plain": "| a |\n|---|\n| 1 |"}, execution_count=1
        ),
        new_output("execute_result", data={"text/html": "<table/>", "text/plain": "   a\n0  1"}, execution_count=2),
        new_output("execute_result", data={"text/plain": "shape: (1,)\nSeries: 'a' [i64]"}, execution_count=3),
    )
    rn._clean_outputs(nb)
    body = rn._to_markdown(nb, "t")
    assert "\n\n| a |\n|---|\n| 1 |\n\n" in body
    assert "```text\n   a\n0  1\n```" in body
    assert "```text\nshape: (1,)\nSeries: 'a' [i64]\n```" in body


def test_a_fence_outlasts_backticks_in_the_output():  # Review Focus 4
    assert rn._fence("a ``` b", "text") == "````text\na ``` b\n````"


def test_an_image_output_is_written_once_under_the_page_files(tmp_path, monkeypatch):
    monkeypatch.setattr(rn, "OUT_DIR", tmp_path)
    (tmp_path / "t_files").mkdir()
    (tmp_path / "t_files" / "t_9_0.png").write_bytes(b"stale")
    png = "iVBORw0KGgo="  # base64 of the 8-byte PNG signature
    body = rn._to_markdown(
        _notebook(new_output("display_data", data={"image/png": png, "text/plain": "<Figure>"})), "t"
    )
    assert "![png](t_files/t_1_0.png)" in body and "<Figure>" not in body
    assert sorted(p.name for p in (tmp_path / "t_files").iterdir()) == ["t_1_0.png"]


def test_the_setup_cell_prints_polars_frames_as_markdown_tables():
    with pl.Config():
        exec(rn.SETUP, {})
        text = repr(pl.DataFrame({"team": ["KC"], "epa": [0.12]}))
    assert text.splitlines() == ["| team | epa  |", "|------|------|", "| KC   | 0.12 |"]


def test_rendered_tutorials_have_outputs_headings_and_notebook_links():
    for stem, _, _ in rn.TUTORIALS:
        page = (ROOT / "docs" / "docs" / "tutorials" / f"{stem}.md").read_text(encoding="utf-8")
        assert '<div class="sdv-output">' in page, stem
        assert not re.search("[┌│╞═]", page), stem
        assert len(re.findall(r"^## ", page, re.M)) >= 3, stem  # two step headings and "Run it yourself"
        assert f'<a href="pathname:///notebooks/{stem}.ipynb" download>' in page, stem
        assert f"]({rn.GITHUB_NB}/{stem}.ipynb)" in page, stem


def test_the_downloadable_notebooks_match_the_sources():
    for stem, _, _ in rn.TUTORIALS:
        copy = ROOT / "docs" / "static" / "notebooks" / f"{stem}.ipynb"
        assert copy.read_bytes() == (NB / f"{stem}.ipynb").read_bytes(), stem

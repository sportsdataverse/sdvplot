import importlib.util
import inspect
import json
import re
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("docstring_parser")  # the docs group; the OS and lowest-direct jobs do not install it
pytest.importorskip("ruff")  # the static example check runs `python -m ruff`

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


def _args(tmp_path, *extra):
    return ["--out", str(tmp_path / "reference"), "--data-out", str(tmp_path / "data"), *extra]


@pytest.mark.real_index  # the generator runs against the shipped index, as in CI
def test_check_mode_detects_drift(tmp_path):
    assert gd.main(_args(tmp_path)) == 0
    assert gd.main(_args(tmp_path, "--check")) == 0
    page = tmp_path / "reference" / "logo_url.md"
    page.write_text(page.read_text() + "\nhand edit\n")
    assert gd.main(_args(tmp_path, "--check")) == 1


@pytest.mark.real_index
def test_check_mode_detects_a_stale_data_file(tmp_path):
    assert gd.main(_args(tmp_path)) == 0
    sidebar = tmp_path / "data" / "reference_sidebar.json"
    sidebar.write_text("[]\n")
    assert gd.main(_args(tmp_path, "--check")) == 1


@pytest.mark.real_index
def test_regeneration_removes_the_page_of_a_removed_function(tmp_path):
    out = tmp_path / "reference"
    out.mkdir()
    (out / "renamed_away.md").write_text("old page\n")
    assert gd.main(_args(tmp_path, "--check")) == 1
    assert gd.main(_args(tmp_path)) == 0
    assert not (out / "renamed_away.md").exists()
    assert gd.main(_args(tmp_path, "--check")) == 0


@pytest.mark.real_index
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


def markers(a: int, b: int, /, c: int = 1, *, d: int = 2, e: int = 3) -> int:
    """Add them up.

    Args:
        a: One.
        b: Two.
        c: Three.
        d: Four.
        e: Five.

    Returns:
        int: The sum.

    Example:
        ::

            markers(1, 2)

    See Also:
        sdvplotR: https://sdvplotR.sportsdataverse.org/ ;
        logo_image
    """
    return a + b + c + d + e


def anything(target: Any, *args: Any, **kwargs: Any) -> Any:
    """Route it.

    Args:
        target: The object.
        *args: Positional.
        **kwargs: Keyword.

    Returns:
        object: The target.

    Example:
        ::

            anything(1)
    """
    return target


def test_the_title_is_the_plain_name():
    page, _ = gd.render_function("good", good, position=1)
    assert "\n# good\n" in page
    assert "# `good`" not in page


def test_a_long_signature_puts_one_parameter_per_line_and_keeps_the_markers():  # Review Focus 1
    page, errors = gd.render_function("markers", markers, position=1)
    assert errors == []
    assert (
        '<div class="sdv-signature">\n\n```python\nmarkers(\n    a: int,\n    b: int,\n    /,\n    c: int = 1,\n'
        "    *,\n    d: int = 2,\n    e: int = 3,\n) -> int\n```\n\n</div>"
    ) in page


def test_a_short_signature_stays_on_one_line():
    page, _ = gd.render_function("good", good, position=1)
    assert "```python\ngood(x: int, y: str = 'a') -> str\n```" in page


def test_the_type_column_is_left_out_when_every_parameter_is_any():
    page, errors = gd.render_function("anything", anything, position=1)
    assert errors == []
    assert "| Name | Description |" in page
    assert "| `target` | The object. |" in page
    assert "Type" not in page


def test_see_also_entries_are_links_and_an_entry_without_a_url_is_kept():  # Review Focus 2
    page, _ = gd.render_function("markers", markers, position=1)
    assert "## See also\n\n- [sdvplotR](https://sdvplotR.sportsdataverse.org/)\n- logo_image\n" in page


@pytest.mark.parametrize("name", ["add_logos", "add_wordmarks", "add_headshots", "axis_logos"])
def test_an_adapter_example_draws_on_a_plot_instead_of_raising(name):  # Review Focus 3
    example = gd._example(inspect.getdoc(getattr(gd.sdvplot, name)))
    assert "UnsupportedTargetError" not in example, name
    assert f"sdvplot.{name}(ax, " in example, name


@pytest.mark.real_index
def test_the_sidebar_groups_follow_sections_and_list_every_page_once(tmp_path):
    gd.render(tmp_path / "reference", tmp_path / "data")
    items = json.loads((tmp_path / "data" / "reference_sidebar.json").read_text())
    assert [i["label"] for i in items if i["type"] == "category"] == [t for t, _ in gd.SECTIONS]
    ids = [i["id"] for i in items if i["type"] == "doc"] + [
        d for i in items if i["type"] == "category" for d in i["items"]
    ]
    assert sorted(ids) == sorted(f"reference/{p.stem}" for p in (tmp_path / "reference").glob("*.md"))


@pytest.mark.real_index
def test_the_home_sample_output_is_computed_from_the_sample():
    data = gd.home_data()
    # not on PyPI yet: the git URL is what a visitor can install today
    assert data["install"] == "pip install git+https://github.com/sportsdataverse/sdvplot"
    assert data["sample"].splitlines() == ["import sdvplot", "", *gd.HOME_SAMPLE]
    assert data["output"].splitlines()[0] == "['12', '12', '12']"
    assert len(data["output"].splitlines()) == len(gd.HOME_SAMPLE)
    assert [(s["league"], s["team"]) for s in data["swatches"]] == [(lg.upper(), t) for lg, t in gd.HOME_TEAMS]
    assert len({s["league"] for s in data["swatches"]}) == 3
    for s in data["swatches"]:
        assert re.fullmatch(r"#[0-9a-f]{6}", s["primary"]) and re.fullmatch(r"#[0-9a-f]{6}", s["secondary"]), s


@pytest.mark.real_index
def test_check_mode_detects_a_stale_home_data_file(tmp_path):
    assert gd.main(_args(tmp_path)) == 0
    (tmp_path / "data" / "home.json").write_text("{}\n")
    assert gd.main(_args(tmp_path, "--check")) == 1


def _scratch(monkeypatch, **fns):
    """Install ``sdvplot.scratch`` with the given functions as its ``__all__``."""
    import sys
    import types

    mod = types.ModuleType("sdvplot.scratch")
    mod.__all__ = list(fns)
    for name, fn in fns.items():
        setattr(mod, name, fn)
    monkeypatch.setitem(sys.modules, "sdvplot.scratch", mod)
    monkeypatch.setattr(gd, "public_submodules", lambda: ["scratch"])


def _complete(x: int) -> int:
    """Double it.

    Args:
        x: A number.

    Returns:
        int: Twice ``x``.

    Raises:
        TypeError: If ``x`` is not a number.

    Example:
        ::

            total = 2 * 3

    See Also:
        Python: https://www.python.org/
    """
    return 2 * x


def _drifted(x: int) -> int:
    """Double it.

    Args:
        x: A number.

    Returns:
        int: Twice ``x``.

    Example:
        ::

            _complete(undefined_name)
    """
    return 2 * x


def test_a_complete_submodule_docstring_passes_the_submodule_check(monkeypatch):
    _scratch(monkeypatch, complete=_complete)
    assert gd.check_submodules() == []


def test_a_drifted_submodule_docstring_is_flagged_for_each_missing_part(monkeypatch):
    _scratch(monkeypatch, drifted=_drifted)
    errors = gd.check_submodules()
    assert errors == [
        "sdvplot.scratch.drifted: missing Raises:",
        "sdvplot.scratch.drifted: missing See Also:",
        "sdvplot.scratch.drifted: Example: Undefined name `_complete` (line 1)",
        "sdvplot.scratch.drifted: Example: Undefined name `undefined_name` (line 1)",
    ]


@pytest.mark.real_index
def test_check_mode_fails_on_a_broken_submodule_docstring(monkeypatch, tmp_path, capsys):
    _scratch(monkeypatch, drifted=_drifted)
    assert gd.main(_args(tmp_path, "--check")) == 1
    assert "sdvplot.scratch.drifted: missing See Also:" in capsys.readouterr().err


@pytest.mark.real_index
def test_a_new_public_submodule_is_checked_without_being_listed(monkeypatch, tmp_path, capsys):
    """The gate finds the submodules with pkgutil: an undocumented function in a new one fails --check."""
    import sys

    path = tmp_path / "pkg" / "newmod.py"
    path.parent.mkdir()
    path.write_text('__all__ = ["add_logos"]\n\n\ndef add_logos(target):\n    """Draw logos."""\n')
    spec = importlib.util.spec_from_file_location("sdvplot.newmod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setitem(sys.modules, "sdvplot.newmod", mod)  # removed again at teardown
    monkeypatch.setattr(gd.sdvplot, "__path__", [*gd.sdvplot.__path__, str(path.parent)])
    assert "newmod" in gd.public_submodules()
    assert gd.main(_args(tmp_path, "--check")) == 1
    err = capsys.readouterr().err
    for section in ("Args", "Returns", "Raises", "See Also", "Example"):
        assert f"sdvplot.newmod.add_logos: missing {section}:" in err, section
    assert "sdvplot.newmod: public submodule not placed in a MODULE_SECTIONS group" in err


@pytest.mark.real_index
def test_every_public_submodule_has_one_page_with_a_section_per_name(tmp_path):
    gd.render(tmp_path / "reference", tmp_path / "data")
    for sub in gd.public_submodules():
        page = (tmp_path / "reference" / f"{sub}.md").read_text()
        assert page.startswith(f"---\ntitle: sdvplot.{sub}\n"), sub
        assert f"\n# sdvplot.{sub}\n" in page, sub
        for n in importlib.import_module(f"sdvplot.{sub}").__all__:
            assert f"\n## {n}\n" in page and f"| [{n}](#{n.lower()}) |" in page, (sub, n)
    # a function's section follows the top-level pages' conventions, one heading level down
    gt = (tmp_path / "reference" / "great_tables.md").read_text()
    section = gt.split("\n## gt_theme_athletic\n")[1].split("\n## ")[0]
    assert '<div class="sdv-signature">\n\n```python\ngt_theme_athletic(' in section
    for heading in ("Arguments", "Returns", "Raises", "Example", "See also"):
        assert f"\n### {heading}\n" in section, heading
    # sdvplot.typing's aliases show the values they accept
    assert "Which = Literal['primary', 'secondary']" in (tmp_path / "reference" / "typing.md").read_text()


def test_an_embed_function_must_list_offline_error_in_raises(monkeypatch):
    def embeds(x: int, embed: bool = False) -> int:
        """Echo it.

        Args:
            x: A number.
            embed: Inline it.

        Returns:
            int: ``x``.

        Raises:
            ValueError: If ``x`` is negative.

        Example:
            ::

                total = 1

        See Also:
            Python: https://www.python.org/
        """
        return x

    _scratch(monkeypatch, embeds=embeds)
    errors = gd.check_submodules()
    assert errors == ["sdvplot.scratch.embeds: takes embed= but Raises: does not list OfflineError"]


def test_a_type_renders_under_its_public_module_on_every_python():
    """Python 3.13 moved pathlib.Path into pathlib._local; a page must not change with the Python that renders it."""
    import pathlib

    assert gd._annotation(pathlib.Path) == "pathlib.Path"
    assert gd._annotation(str | pathlib.Path | None) == "str | pathlib.Path | None"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Union[collections.abc.Callable[[Any], Any], Any]", "collections.abc.Callable[[Any], Any] | Any"),
        ("Optional[dict[str, int]]", "dict[str, int] | None"),
        ("list[Union[int, str]] | None", "list[int | str] | None"),
        ("MyUnion[int, str]", "MyUnion[int, str]"),
    ],
)
def test_unions_render_in_the_pipe_form_on_every_python(text, expected):
    """3.10 prints a union with Any as Union[...]; the pages use the | form 3.11+ prints."""
    assert gd._public(text) == expected

"""Generate the API reference pages (docs/docs/reference/) from sdvplot's public docstrings, and the site's data files
(docs/src/data/): the reference sidebar and the home page's code sample, its output and the palette swatches.

Usage: uv run python tools/gen_docs.py [--out DIR] [--data-out DIR] [--check]

Pages are generated, never hand-edited: one per top-level function, one per public submodule (a section per name).
--check renders to a temp dir and byte-compares (exit 1 on drift). Both modes fail when a public function's docstring
misses the standard sections (summary, Args, Returns, Example), and when a public submodule's `__all__` function misses
any of Args, Returns, Raises, Example or See Also, or its Example has a syntax error or an undefined name (found
statically; tests/test_submodule_examples.py runs the examples). The submodules are found with pkgutil, so a new one
is checked at once."""

from __future__ import annotations

import argparse
import filecmp
import importlib
import inspect
import json
import pkgutil
import re
import subprocess
import sys
import tempfile
import textwrap
import typing
from pathlib import Path

import docstring_parser
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import sdvplot  # noqa: E402

OUT = ROOT / "docs" / "docs" / "reference"
DATA = ROOT / "docs" / "src" / "data"
DATA_FILES = ["reference_sidebar.json", "home.json"]
SECTIONS = [
    ("Teams", ["resolve", "suggest", "teams"]),
    ("Colors", ["palette", "team_colors"]),
    ("Logos and headshots", ["logo_url", "logo_image", "marks", "headshot_url"]),
    ("Plots and tables", ["add_logos", "add_wordmarks", "add_headshots", "axis_logos", "surface", "court_coords"]),
    ("Housekeeping", ["versions", "clear_cache"]),
]
ERRORS = [
    "SdvplotWarning",
    "SdvplotDeprecationWarning",
    "SdvplotError",
    "InputError",
    "UnresolvedTeamError",
    "OfflineError",
    "OptionalDependencyError",
    "UnsupportedTargetError",
    "UnsafeDownloadError",
    "UnsafeCachePathError",
]
# One page per public submodule, in the SECTIONS group it belongs to. The docstring gate finds the submodules itself
# (public_submodules), so a new one is checked at once, and fails the build until it is placed here.
MODULE_SECTIONS = {
    "Plots and tables": [
        "matplotlib", "plotnine", "plotly", "altair", "bokeh", "holoviews", "folium", "pygal",
        "great_tables", "reactable", "plottable",
    ],
    "Housekeeping": ["testing", "typing"],
}  # fmt: skip
SIG_WIDTH = 60  # a signature longer than this puts one parameter per line
# The home page: an install line, a sample that runs offline against the bundled index (its output is computed here,
# never typed), and two-color swatches for six teams in three leagues, from palette().
# Not on PyPI yet: switch to "pip install sdvplot" after the first release.
HOME_INSTALL = "pip install git+https://github.com/sportsdataverse/sdvplot"
HOME_SAMPLE = [
    'sdvplot.resolve(["KC", "Kansas City Chiefs", 12], "nfl")',
    'sdvplot.palette("nfl", teams=["KC", "SF"])',
    'sdvplot.team_colors("nba", ["LAL", "BOS"])',
    'sdvplot.team_colors("mlb", "NYY", which="secondary")',
]
HOME_TEAMS = [("nfl", "KC"), ("nfl", "SF"), ("nba", "LAL"), ("nba", "BOS"), ("mlb", "NYY"), ("mlb", "LAD")]


def _section(text: str, header: str) -> str | None:
    """The body of a ``Header:`` block of a dedented docstring (docstring_parser flattens Example indentation and
    drops ``See Also:``, so both are read from the raw text)."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.strip() == f"{header}:" and not ln.startswith(" ")), None)
    if start is None:
        return None
    body: list[str] = []
    for ln in lines[start + 1 :]:
        if ln and not ln.startswith(" "):
            break
        body.append(ln[4:] if ln.startswith("    ") else ln)
    return "\n".join(body).strip("\n")


def _example(text: str) -> str | None:
    body = _section(text, "Example")
    if body is None:
        return None
    body = body.strip()
    if body.startswith("::"):
        body = body[2:]
    return textwrap.dedent(body).strip("\n").rstrip() or None


def _see_also(text: str) -> list[str]:
    """One markdown list item per ``;``-separated entry: ``label: https://...`` becomes a link, anything else stays."""
    items = []
    for entry in " ".join((_section(text, "See Also") or "").split()).split(";"):
        entry = entry.strip()
        m = re.fullmatch(r"(.+?):\s*(https?://\S+)", entry)
        if m:
            items.append(f"- [{m.group(1)}]({m.group(2)})")
        elif entry:
            items.append(f"- {entry}")
    return items


def _cell(text: str) -> str:
    """GFM splits table cells on an unescaped pipe, even inside a code span."""
    return text.replace("|", "\\|")


def _annotation(ann: object) -> str:
    return inspect.formatannotation(ann).replace("typing.", "")


def _signature(name: str, sig: inspect.Signature) -> str:
    """``name(params) -> ret`` on one line, or one parameter per line when that is longer than SIG_WIDTH."""
    one = f"{name}{sig}".replace("typing.", "")
    if len(one) <= SIG_WIDTH:
        return one
    kinds = inspect.Parameter
    params = list(sig.parameters.values())
    parts: list[str] = []
    for i, p in enumerate(params):
        if p.kind is kinds.KEYWORD_ONLY and (
            i == 0 or params[i - 1].kind not in (kinds.KEYWORD_ONLY, kinds.VAR_POSITIONAL)
        ):
            parts.append("*")
        parts.append(str(p).replace("typing.", ""))
        if p.kind is kinds.POSITIONAL_ONLY and (
            i + 1 == len(params) or params[i + 1].kind is not kinds.POSITIONAL_ONLY
        ):
            parts.append("/")
    ret = "" if sig.return_annotation is inspect.Signature.empty else f" -> {_annotation(sig.return_annotation)}"
    return f"{name}(\n" + "".join(f"    {x},\n" for x in parts) + f"){ret}"


def render_function(name: str, fn: object, position: int | None) -> tuple[str, list[str]]:
    """A top-level function's page, or with ``position=None`` its section of a submodule page: no front matter, a
    ``##`` title and every heading one level down."""
    h = "#" if position is not None else "##"
    raw = inspect.getdoc(fn) or ""
    doc = docstring_parser.parse(raw, style=docstring_parser.DocstringStyle.GOOGLE)
    try:  # the package uses `from __future__ import annotations`; resolve them so pages show types, not strings
        from PIL import Image  # imported under TYPE_CHECKING in the package, so that `import sdvplot` stays light

        sig = inspect.signature(fn, eval_str=True, locals={"Image": Image})  # type: ignore[arg-type]
    except NameError:
        sig = inspect.signature(fn)  # type: ignore[arg-type]
    errors: list[str] = []
    if not doc.short_description:
        errors.append(f"{name}: missing summary line")
    if sig.parameters and not doc.params:
        errors.append(f"{name}: missing Args:")
    if not doc.returns:
        errors.append(f"{name}: missing Returns:")
    example = _example(raw)
    if example is None:
        errors.append(f"{name}: missing Example:")
    out = (
        [] if position is None else [f"---\ntitle: {name}\nsidebar_label: {name}\nsidebar_position: {position}\n---\n"]
    )
    out += [
        f"{h} {name}\n",
        f'<div class="sdv-signature">\n\n```python\n{_signature(name, sig)}\n```\n\n</div>\n',
    ]
    if doc.short_description:
        out.append(doc.short_description + "\n")
    if doc.long_description:
        out.append(doc.long_description + "\n")
    if doc.params:
        anns = []
        for p in doc.params:
            param = sig.parameters.get(p.arg_name.lstrip("*"))
            anns.append(param.annotation if param else inspect.Parameter.empty)
        typed = any(a is not inspect.Parameter.empty and _annotation(a) != "Any" for a in anns)
        out.append(f"{h}# Arguments\n")
        out.append("| Name | Type | Description |\n|---|---|---|" if typed else "| Name | Description |\n|---|---|")
        for p, ann in zip(doc.params, anns, strict=True):
            desc = _cell(" ".join((p.description or "").split()))
            if typed:
                typ = "" if ann is inspect.Parameter.empty else f"`{_cell(_annotation(ann))}`"
                out.append(f"| `{p.arg_name}` | {typ} | {desc} |")
            else:
                out.append(f"| `{p.arg_name}` | {desc} |")
        out.append("")
    if doc.returns:
        typ = f"`{doc.returns.type_name}` — " if doc.returns.type_name else ""
        out.append(f"{h}# Returns\n\n{typ}{' '.join((doc.returns.description or '').split())}\n")
    if doc.raises:
        out.append(f"{h}# Raises\n")
        out += [f"- `{r.type_name}`: {' '.join((r.description or '').split())}" for r in doc.raises]
        out.append("")
    if example is not None:
        out.append(f"{h}# Example\n\n```python\n{example}\n```\n")
    see = _see_also(raw)
    if see:
        out.append(f"{h}# See also\n\n" + "\n".join(see) + "\n")
    return "\n".join(out).rstrip() + "\n", errors


def _summary(obj: object) -> str:
    """The first paragraph of a docstring, on one line."""
    return " ".join((inspect.getdoc(obj) or "").split("\n\n")[0].split())


def _is_alias(obj: object) -> bool:
    """A ``Literal`` alias (sdvplot.typing): callable to Python, but a type, with no docstring of its own."""
    return typing.get_origin(obj) is typing.Literal


def render_module(sub: str, position: int) -> str:
    """One page for a public submodule: its summary, a table of its ``__all__``, then a section per name, a function as
    on the top-level pages, a constant or ``Literal`` alias as its value. (Only the module docstring's first paragraph
    is shown: the rest is written for the code's readers and names private hooks.)"""
    mod = importlib.import_module(f"sdvplot.{sub}")
    title = f"sdvplot.{sub}"
    out = [
        f"---\ntitle: {title}\nsidebar_label: {title}\nsidebar_position: {position}\n---\n",
        f"# {title}\n",
        f"{_summary(mod)}\n",
        "| Name | What it is |\n|---|---|",
    ]
    sections = []
    for n in getattr(mod, "__all__", ()):
        obj = getattr(mod, n)
        if callable(obj) and not _is_alias(obj):
            section, _ = render_function(n, obj, None)  # check_submodules reports what the docstring misses
            what = docstring_parser.parse(inspect.getdoc(obj) or "").short_description or ""
        else:
            value = _annotation(obj) if _is_alias(obj) else repr(obj)
            section = f'## {n}\n\n<div class="sdv-signature">\n\n```python\n{n} = {value}\n```\n\n</div>\n'
            what = "The values it accepts (a `Literal` alias)." if _is_alias(obj) else "A constant."
        out.append(f"| [{n}](#{n.lower()}) | {_cell(what)} |")
        sections.append(section)
    return "\n".join(out) + "\n\n" + "\n".join(sections)


def _errors_page(position: int) -> str:
    lines = [
        f"---\ntitle: Errors and warnings\nsidebar_label: Errors and warnings\nsidebar_position: {position}\n---\n",
        "# Errors and warnings\n",
        "| Type | Subclass of | Meaning |",
        "|---|---|---|",
    ]
    for n in ERRORS:
        cls = getattr(sdvplot, n)
        bases = ", ".join(f"`{b.__name__}`" for b in cls.__bases__)
        meaning = " ".join((inspect.getdoc(cls) or "").split())  # one table row, however the docstring wraps
        lines.append(f"| `{n}` | {bases} | {meaning} |")
    return "\n".join(lines) + "\n"


def sidebar_items() -> list[dict[str, object]]:
    """The API reference category's sidebar items: the overview, one category per SECTIONS group (its functions, then
    its submodule pages), the errors page. Doc ids are file paths, so the page URLs do not change."""
    items: list[dict[str, object]] = [{"type": "doc", "id": "reference/index", "label": "Overview"}]
    for title, names in SECTIONS:
        pages = [*names, *MODULE_SECTIONS.get(title, [])]
        items.append({"type": "category", "label": title, "items": [f"reference/{n}" for n in pages]})
    items.append({"type": "doc", "id": "reference/errors", "label": "Errors and warnings"})
    return items


def home_data() -> dict[str, object]:
    """The home page's install line, code sample, the sample's output (one repr per line) and swatches."""
    ns: dict[str, object] = {"sdvplot": sdvplot}
    output = []
    for line in HOME_SAMPLE:
        exec(f"_ = {line}", ns)  # the sample's own text is what runs
        output.append(repr(ns["_"]))
    swatches = []
    for league, team in HOME_TEAMS:
        team_id = sdvplot.resolve(team, league)
        name = sdvplot.teams(league).filter(pl.col("team_id") == team_id)["name"][0]
        primary = sdvplot.palette(league, teams=[team])[team]
        secondary = sdvplot.palette(league, which="secondary", teams=[team])[team]
        swatches.append(
            {"league": league.upper(), "team": team, "name": name, "primary": primary, "secondary": secondary}
        )
    return {
        "install": HOME_INSTALL,
        "sample": "import sdvplot\n\n" + "\n".join(HOME_SAMPLE),
        "output": "\n".join(output),
        "swatches": swatches,
    }


def _write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def public_submodules() -> list[str]:
    """Every public submodule (no leading underscore), found rather than listed, so a new one cannot escape the
    docstring gate (tests/test_api.py finds them the same way)."""
    return sorted(m.name for m in pkgutil.iter_modules(sdvplot.__path__) if not m.name.startswith("_"))


def submodule_examples(submodules: list[str] | None = None) -> dict[str, str]:
    """The Example code of every public submodule function, keyed by ``"<submodule>.<name>"`` (the tests run them)."""
    out: dict[str, str] = {}
    for sub in public_submodules() if submodules is None else submodules:
        mod = importlib.import_module(f"sdvplot.{sub}")
        for n in getattr(mod, "__all__", ()):
            fn = getattr(mod, n)
            if callable(fn) and (example := _example(inspect.getdoc(fn) or "")):
                out[f"{sub}.{n}"] = example
    return out


def _static_example_errors(examples: dict[str, str]) -> list[str]:
    """Syntax errors and undefined or redefined names in the examples, found without running them (one ruff call), so
    an error after a network call cannot hide."""
    with tempfile.TemporaryDirectory() as tmp:
        files = {}
        for i, (label, code) in enumerate(examples.items()):
            path = Path(tmp) / f"ex{i}.py"
            path.write_text(code + "\n", encoding="utf-8")
            files[str(path)] = label
        cmd = [sys.executable, "-m", "ruff", "check", "--isolated", "--no-cache", "--select", "F821,F811"]
        run = subprocess.run([*cmd, "--output-format", "json", tmp], capture_output=True, text=True, check=False)
        if run.returncode not in (0, 1):
            return [f"examples: ruff failed: {run.stderr.strip()}"]
        found = json.loads(run.stdout or "[]")
    return [f"sdvplot.{files[d['filename']]}: Example: {d['message']} (line {d['location']['row']})" for d in found]


def check_submodules(submodules: list[str] | None = None) -> list[str]:
    """Check each public submodule's ``__all__`` functions: sections present, OfflineError listed when ``embed`` is
    taken, and every Example free of syntax errors and undefined names (tests/test_submodule_examples.py runs them)."""
    errors: list[str] = []
    for sub in public_submodules() if submodules is None else submodules:
        mod = importlib.import_module(f"sdvplot.{sub}")
        for n in getattr(mod, "__all__", ()):
            fn = getattr(mod, n)
            if not callable(fn) or _is_alias(fn):  # sdvplot.typing's aliases: their page shows their values
                continue
            label = f"sdvplot.{sub}.{n}"
            raw = inspect.getdoc(fn) or ""
            doc = docstring_parser.parse(raw, style=docstring_parser.DocstringStyle.GOOGLE)
            try:
                params = inspect.signature(fn).parameters
            except (TypeError, ValueError):
                params = {}  # type: ignore[assignment]
            if not doc.short_description:
                errors.append(f"{label}: missing summary line")
            if params and not doc.params:
                errors.append(f"{label}: missing Args:")
            if not doc.returns:
                errors.append(f"{label}: missing Returns:")
            if params and _section(raw, "Raises") is None:
                errors.append(f"{label}: missing Raises:")
            elif "embed" in params and "OfflineError" not in (_section(raw, "Raises") or ""):
                errors.append(f"{label}: takes embed= but Raises: does not list OfflineError")
            if not _see_also(raw):
                errors.append(f"{label}: missing See Also:")
            if _example(raw) is None:
                errors.append(f"{label}: missing Example:")
    errors += _static_example_errors(submodule_examples(submodules))
    return errors


def render(out_dir: Path, data_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("*.md"):  # every page here is generated: drop those of removed functions
        stale.unlink()
    errors: list[str] = []
    index = [
        "---\ntitle: API reference\nsidebar_label: Overview\nsidebar_position: 0\n---\n",
        "# API reference\n",
        "Every public function, grouped by what it works with. Each top-level function has a page, and each public "
        "submodule (the library adapters, the table helpers, `sdvplot.testing` and `sdvplot.typing`) has one page "
        "with a section per name. Each gives the signature, the arguments and what the function returns and raises.\n",
    ]
    pos = 1
    listed = {n for _, names in SECTIONS for n in names}
    missing = sorted(
        n for n in sdvplot.__all__ if callable(getattr(sdvplot, n)) and n not in listed and n not in ERRORS
    )
    errors += [f"{n}: public but not placed in a SECTIONS group" for n in missing]
    placed = {s for subs in MODULE_SECTIONS.values() for s in subs}
    errors += [f"sdvplot.{s}: public submodule not placed in a MODULE_SECTIONS group" for s in public_submodules()
               if s not in placed]  # fmt: skip
    errors += check_submodules()
    for title, names in SECTIONS:
        index.append(f"## {title}\n")
        index.append("| Function | What it does |\n|---|---|")
        for n in names:
            page, errs = render_function(n, getattr(sdvplot, n), pos)
            errors += errs
            (out_dir / f"{n}.md").write_text(page, encoding="utf-8", newline="\n")
            summary = docstring_parser.parse(inspect.getdoc(getattr(sdvplot, n)) or "").short_description or ""
            index.append(f"| [{n}]({n}.md) | {_cell(summary)} |")
            pos += 1
        index.append("")
        if subs := MODULE_SECTIONS.get(title):
            index.append("| Submodule | What it holds |\n|---|---|")
            for s in subs:
                (out_dir / f"{s}.md").write_text(render_module(s, pos), encoding="utf-8", newline="\n")
                summary = _summary(importlib.import_module(f"sdvplot.{s}"))
                index.append(f"| [sdvplot.{s}]({s}.md) | {_cell(summary)} |")
                pos += 1
            index.append("")
    index.append(
        "## Errors and warnings\n\n[Errors and warnings](errors.md): the warning sdvplot emits and the errors it "
        "raises, with what each means.\n"
    )
    (out_dir / "errors.md").write_text(_errors_page(pos), encoding="utf-8", newline="\n")
    (out_dir / "index.md").write_text("\n".join(index).rstrip() + "\n", encoding="utf-8", newline="\n")
    _write_json(data_dir / "reference_sidebar.json", sidebar_items())
    _write_json(data_dir / "home.json", home_data())
    return errors


def _stale(fresh: Path, committed: Path, names: list[str]) -> list[str]:
    """Names that differ between the fresh render and the committed copy, or exist in only one of them."""
    return [
        n
        for n in names
        if (fresh / n).exists() != (committed / n).exists()
        or ((fresh / n).exists() and not filecmp.cmp(fresh / n, committed / n, shallow=False))
    ]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--data-out", type=Path, default=DATA)
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            ref, data = Path(tmp) / "reference", Path(tmp) / "data"
            errors = render(ref, data)
            pages = sorted(
                {f.name for f in ref.glob("*.md")}
                | ({f.name for f in args.out.glob("*.md")} if args.out.exists() else set())
            )
            stale = _stale(ref, args.out, pages) + _stale(data, args.data_out, DATA_FILES)
        for e in errors:
            print(f"docstring: {e}", file=sys.stderr)
        if stale:
            print(
                f"reference is OUT OF DATE ({', '.join(stale)}): run uv run python tools/gen_docs.py", file=sys.stderr
            )
        if not stale and not errors:
            print("reference is current")
        return 1 if (stale or errors) else 0
    errors = render(args.out, args.data_out)
    for e in errors:
        print(f"docstring: {e}", file=sys.stderr)
    print(f"wrote {len(list(args.out.glob('*.md')))} pages to {args.out} and the site data to {args.data_out}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

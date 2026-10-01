"""Generate the API reference pages (docs/docs/reference/) from sdvplot's public docstrings.

Usage: uv run python tools/gen_docs.py [--out DIR] [--check]

Pages are generated, never hand-edited. --check renders to a temp dir and byte-compares (exit 1 on drift). Both modes
fail when a public function's docstring misses the standard sections (summary, Args, Returns, Example)."""

from __future__ import annotations

import argparse
import filecmp
import inspect
import sys
import tempfile
import textwrap
from pathlib import Path

import docstring_parser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import sdvplot  # noqa: E402

OUT = ROOT / "docs" / "docs" / "reference"
SECTIONS = [
    ("Teams", ["resolve", "suggest", "teams"]),
    ("Colors", ["palette", "team_colors"]),
    ("Logos and headshots", ["logo_url", "logo_image", "marks", "headshot_url"]),
    ("Plots and tables", ["add_logos", "add_wordmarks", "add_headshots", "axis_logos"]),
    ("Housekeeping", ["versions", "clear_cache"]),
]
ERRORS = ["SdvplotWarning", "UnresolvedTeamError", "OfflineError", "OptionalDependencyError", "UnsupportedTargetError"]


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


def _see_also(text: str) -> str | None:
    return " ".join((_section(text, "See Also") or "").split()) or None


def _cell(text: str) -> str:
    """GFM splits table cells on an unescaped pipe, even inside a code span."""
    return text.replace("|", "\\|")


def render_function(name: str, fn: object, position: int) -> tuple[str, list[str]]:
    raw = inspect.getdoc(fn) or ""
    doc = docstring_parser.parse(raw, style=docstring_parser.DocstringStyle.GOOGLE)
    try:  # the package uses `from __future__ import annotations`; resolve them so pages show types, not strings
        sig = inspect.signature(fn, eval_str=True)  # type: ignore[arg-type]
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
    out = [
        f"---\ntitle: {name}\nsidebar_label: {name}\nsidebar_position: {position}\n---\n",
        f"# `{name}`\n",
        f"```python\n{name}{sig}\n```\n",
    ]
    if doc.short_description:
        out.append(doc.short_description + "\n")
    if doc.long_description:
        out.append(doc.long_description + "\n")
    if doc.params:
        out.append("## Arguments\n\n| Name | Type | Description |\n|---|---|---|")
        for p in doc.params:
            param = sig.parameters.get(p.arg_name.lstrip("*"))
            ann = param.annotation if param else inspect.Parameter.empty
            typ = "" if ann is inspect.Parameter.empty else f"`{_cell(inspect.formatannotation(ann))}`"
            desc = _cell(" ".join((p.description or "").split()))
            out.append(f"| `{p.arg_name}` | {typ} | {desc} |")
        out.append("")
    if doc.returns:
        typ = f"`{doc.returns.type_name}` — " if doc.returns.type_name else ""
        out.append(f"## Returns\n\n{typ}{' '.join((doc.returns.description or '').split())}\n")
    if doc.raises:
        out.append("## Raises\n")
        out += [f"- `{r.type_name}`: {' '.join((r.description or '').split())}" for r in doc.raises]
        out.append("")
    if example is not None:
        out.append(f"## Example\n\n```python\n{example}\n```\n")
    see = _see_also(raw)
    if see:
        out.append(f"## See also\n\n{see}\n")
    return "\n".join(out).rstrip() + "\n", errors


def _errors_page(position: int) -> str:
    lines = [
        f"---\ntitle: Errors and warnings\nsidebar_label: Errors and warnings\nsidebar_position: {position}\n---\n",
        "# Errors and warnings\n",
        "| Type | Subclass of | Meaning |",
        "|---|---|---|",
    ]
    for n in ERRORS:
        cls = getattr(sdvplot, n)
        lines.append(f"| `{n}` | `{cls.__mro__[1].__name__}` | {inspect.getdoc(cls) or ''} |")
    return "\n".join(lines) + "\n"


def render(out_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    index = ["---\ntitle: API reference\nsidebar_label: Overview\nsidebar_position: 0\n---\n", "# API reference\n"]
    pos = 1
    listed = {n for _, names in SECTIONS for n in names}
    missing = sorted(
        n for n in sdvplot.__all__ if callable(getattr(sdvplot, n)) and n not in listed and n not in ERRORS
    )
    errors += [f"{n}: public but not placed in a SECTIONS group" for n in missing]
    for title, names in SECTIONS:
        index.append(f"## {title}\n")
        for n in names:
            page, errs = render_function(n, getattr(sdvplot, n), pos)
            errors += errs
            (out_dir / f"{n}.md").write_text(page, encoding="utf-8", newline="\n")
            summary = docstring_parser.parse(inspect.getdoc(getattr(sdvplot, n)) or "").short_description or ""
            index.append(f"- [`{n}`]({n}.md): {summary}")
            pos += 1
        index.append("")
    index.append("## Errors and warnings\n\n- [Errors and warnings](errors.md)\n")
    (out_dir / "errors.md").write_text(_errors_page(pos), encoding="utf-8", newline="\n")
    (out_dir / "index.md").write_text("\n".join(index).rstrip() + "\n", encoding="utf-8", newline="\n")
    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=OUT)
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            errors = render(Path(tmp))
            fresh = sorted(f.name for f in Path(tmp).glob("*.md"))
            committed = sorted(f.name for f in args.out.glob("*.md")) if args.out.exists() else []
            stale = [
                n for n in fresh if n not in committed or not filecmp.cmp(Path(tmp) / n, args.out / n, shallow=False)
            ]
            stale += [n for n in committed if n not in fresh]
        for e in errors:
            print(f"docstring: {e}", file=sys.stderr)
        if stale:
            print(
                f"reference is OUT OF DATE ({', '.join(stale)}): run uv run python tools/gen_docs.py", file=sys.stderr
            )
        if not stale and not errors:
            print("reference is current")
        return 1 if (stale or errors) else 0
    errors = render(args.out)
    for e in errors:
        print(f"docstring: {e}", file=sys.stderr)
    print(f"wrote {len(list(args.out.glob('*.md')))} pages to {args.out}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

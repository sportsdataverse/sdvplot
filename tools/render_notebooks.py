"""Execute the example notebooks and render them to Docusaurus tutorial pages.

The example notebooks (``examples/notebooks/*.ipynb``) are committed with their
outputs cleared. This script EXECUTES each one against the real sdvplot package
and renders the executed result (code + outputs, matplotlib figures as PNGs) to a
Docusaurus page under ``docs/docs/tutorials/<stem>.md`` -- so the docs site shows
real values and logos, not just code.

Execution hits the live sdv-assets CDN (logos), ESPN (headshots) and nflverse
(gsis player table), so this is **not** part of the offline docs build. Run it
locally or in a scheduled workflow; the regular doc build just consumes the
committed ``.md``:

    uv run python tools/render_notebooks.py               # execute + render
    uv run python tools/render_notebooks.py --no-execute  # render as-is (no live calls)

Determinism / safety:

* ``JUPYTER_CONFIG_DIR`` is pointed at a throwaway dir so a polluted global
  jupyter/nbconvert config can't inject preprocessors.
* Pages are emitted as ``.md`` (CommonMark via Docusaurus ``format: detect``) so
  bare ``{`` / ``<`` in outputs don't trip the MDX parser. CommonMark still carries
  raw HTML blocks, which is how each cell's outputs get the theme's ``sdv-output`` wrapper.
* Polars frames print as markdown tables (a hidden first cell sets ``pl.Config``), so
  they render as tables rather than box-drawing text.
* The source ``.ipynb`` files are never modified -- execution happens on an
  in-memory copy.
"""

from __future__ import annotations

import argparse
import base64
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

# Avoid loading a polluted global jupyter/nbconvert config (some machines register
# a missing ``jupyter_contrib_nbextensions`` preprocessor that breaks nbconvert).
os.environ["JUPYTER_CONFIG_DIR"] = tempfile.mkdtemp(prefix="sdvplot-nbrender-")

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "examples" / "notebooks"
OUT_DIR = ROOT / "docs" / "docs" / "tutorials"
STATIC_NB = ROOT / "docs" / "static" / "notebooks"  # byte-for-byte copies, served for download
GITHUB_NB = "https://github.com/sportsdataverse/sdvplot/blob/main/examples/notebooks"
# Run before the notebook's own cells, then dropped from the page: frames print as markdown tables.
SETUP = (
    "import polars as pl\n"
    'pl.Config.set_tbl_formatting("MARKDOWN")\n'
    "pl.Config.set_tbl_hide_column_data_types(True)\n"
    "pl.Config.set_tbl_hide_dataframe_shape(True)\n"
    "pl.Config.set_tbl_cols(-1)\n"
    "pl.Config.set_fmt_str_lengths(200)\n"
    "pl.Config.set_tbl_width_chars(10000)\n"
)

# (stem, sidebar label, sidebar_position).
TUTORIALS: list[tuple[str, str, int]] = [
    ("01_quickstart", "Quickstart", 1),
    ("02_colors", "Team colors", 2),
    ("03_logos_and_seasons", "Logos and eras", 3),
    ("04_headshots", "Headshots", 4),
]


def _execute(nb):
    """Execute a notebook in-memory behind the SETUP cell, then drop that cell; raise on the first failing cell."""
    import nbformat
    from nbclient import NotebookClient

    nb.cells.insert(0, nbformat.v4.new_code_cell(SETUP, id="sdvplot-render-setup"))
    try:
        NotebookClient(nb, timeout=180, kernel_name="python3", allow_errors=False).execute()
    finally:
        nb.cells.pop(0)


def _fence(text: str, lang: str) -> str:
    """A fenced block one backtick longer than the longest backtick run inside it."""
    ticks = "`" * max(3, max((len(m) for m in re.findall(r"`+", text)), default=0) + 1)
    return f"{ticks}{lang}\n{text.rstrip(chr(10))}\n{ticks}"


def _output(out, stem: str, cell_index: int, index: int) -> str | None:
    """One cell output as markdown: images to <stem>_files/, markdown (frames) as is, text in a fence."""
    data = out.get("data", {})
    if out.get("output_type") == "stream":
        return _fence(out.get("text", ""), "text")
    if "image/png" in data:
        name = f"{stem}_files/{stem}_{cell_index}_{index}.png"
        dest = OUT_DIR / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(base64.b64decode(data["image/png"]))
        return f"![png]({name})"
    if "text/markdown" in data:
        return data["text/markdown"].strip("\n")
    if "text/plain" in data:
        return _fence(data["text/plain"], "text")
    return None


def _to_markdown(nb, stem: str) -> str:
    """Render an (executed) notebook node to a markdown body string.

    Markdown cells are copied, code cells become ```python fences, and each code cell's outputs sit in one
    ``<div class="sdv-output">`` (styled by the shared theme) so output never reads as more input. The blank lines
    around the fences are what let CommonMark parse markdown inside the HTML block."""
    shutil.rmtree(OUT_DIR / f"{stem}_files", ignore_errors=True)  # no orphaned figures when cells move
    parts: list[str] = []
    for ci, cell in enumerate(nb.cells):
        if cell.get("cell_type") == "markdown":
            parts.append(cell.source)
        elif cell.get("cell_type") == "code":
            parts.append(_fence(cell.source, "python"))
            outs = [md for oi, o in enumerate(cell.get("outputs", [])) if (md := _output(o, stem, ci, oi))]
            if outs:
                parts.append('<div class="sdv-output">\n\n' + "\n\n".join(outs) + "\n\n</div>")
    return "\n\n".join(parts) + "\n"


def _clean_outputs(nb) -> None:
    """In-place: tidy executed cell outputs for clean, theme-safe rendering.

    * Drop ``stderr`` stream outputs (warning noise -- e.g. env-specific version
      warnings -- that isn't pedagogically useful in a rendered tutorial).
    * Prefer the plain-text repr over the styled HTML one: polars / pandas ``text/html``
      carries a scoped ``<style>`` block that can clash with the Docusaurus theme. A
      polars frame's plain text is a markdown table (``SETUP``), so it moves to
      ``text/markdown`` and renders as a table. Image outputs (``image/*``) are kept.
    """
    for cell in nb.cells:
        if cell.get("cell_type") != "code":
            continue
        kept = []
        for o in cell.get("outputs", []):
            ot = o.get("output_type")
            if ot == "stream" and o.get("name") == "stderr":
                continue
            if ot in ("execute_result", "display_data"):
                data = o.get("data", {})
                if "text/html" in data and "text/plain" in data:
                    data.pop("text/html", None)
                    if data["text/plain"].startswith("|"):
                        data["text/markdown"] = data.pop("text/plain")
            kept.append(o)
        cell["outputs"] = kept


def _fix_links(body: str) -> str:
    """Rewrite notebook cross-reference links so they resolve from the rendered page.

    The source notebooks live in ``examples/notebooks/`` and link siblings as
    ``other.ipynb`` -- correct from the notebook's location but broken once rendered under
    ``docs/docs/tutorials/``. Rewrite ``](<anything>/NN_<name>.ipynb)`` to
    ``](NN_<name>.md)`` (sibling tutorial page).
    """
    body = re.sub(r"\]\([^)]*?(\d\d_[a-z0-9_]+)\.ipynb\)", r"](\1.md)", body)
    return body


def _notebook_links(body: str, stem: str) -> str:
    """A closing section: a download of the notebook (a copy served from docs/static/notebooks/; ``pathname://``
    keeps Docusaurus from treating the file as a page) and the notebook on GitHub."""
    return body.rstrip("\n") + (
        "\n\n## Run it yourself\n\n"
        f'<a href="pathname:///notebooks/{stem}.ipynb" download>Download the notebook</a> (outputs cleared) '
        f"or [open it on GitHub]({GITHUB_NB}/{stem}.ipynb).\n"
    )


def _normalize_md(text: str) -> str:
    """Match the repo's whitespace hooks (trailing-whitespace + end-of-file-fixer).

    nbconvert emits trailing spaces / no final newline; those hooks are NOT excluded
    for ``docs/docs/``. Normalizing here keeps the render output byte-identical to
    what a committed-then-hooked file would be, so the weekly cron only opens a PR
    when the *data* changed -- not because of cosmetic whitespace churn."""
    return "\n".join(ln.rstrip() for ln in text.splitlines()).rstrip() + "\n"


def _frontmatter(label: str, position: int) -> str:
    return f"---\ntitle: {label} tutorial\nsidebar_label: {label}\nsidebar_position: {position}\n---\n\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-execute", action="store_true", help="render notebooks as-is (no live API calls)")
    ap.add_argument(
        "--only", action="append", default=[], help="only render this stem (repeatable); for retries/debugging"
    )
    args = ap.parse_args()

    import nbformat

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_NB.mkdir(parents=True, exist_ok=True)

    tutorials = [t for t in TUTORIALS if not args.only or t[0] in args.only]
    failures = []
    for stem, label, position in tutorials:
        src = NB_DIR / f"{stem}.ipynb"
        if not src.exists():
            print(f"  WARNING: missing {src}", file=sys.stderr)
            failures.append(stem)
            continue
        print(f"Rendering {stem} ...", flush=True)
        nb = nbformat.read(src, as_version=4)
        if not args.no_execute:
            try:
                _execute(nb)
            except Exception as e:  # noqa: BLE001 -- surface which notebook broke
                print(f"  EXECUTION FAILED for {stem}: {type(e).__name__}: {str(e)[:160]}", file=sys.stderr)
                failures.append(stem)
                continue
        _clean_outputs(nb)
        body = _notebook_links(_fix_links(_to_markdown(nb, stem)), stem)
        shutil.copyfile(src, STATIC_NB / f"{stem}.ipynb")
        (OUT_DIR / f"{stem}.md").write_text(
            _normalize_md(_frontmatter(label, position) + body), encoding="utf-8", newline="\n"
        )
        print(f"  wrote {OUT_DIR / f'{stem}.md'}")

    if failures:
        print(f"\nFAILED ({len(failures)}): {', '.join(failures)}", file=sys.stderr)
        return 1
    print(f"\nrendered {len(TUTORIALS)} tutorial pages -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
  bare ``{`` / ``<`` in DataFrame reprs don't trip the MDX parser.
* The source ``.ipynb`` files are never modified -- execution happens on an
  in-memory copy.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

# Avoid loading a polluted global jupyter/nbconvert config (some machines register
# a missing ``jupyter_contrib_nbextensions`` preprocessor that breaks nbconvert).
os.environ["JUPYTER_CONFIG_DIR"] = tempfile.mkdtemp(prefix="sdvplot-nbrender-")

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "examples" / "notebooks"
OUT_DIR = ROOT / "docs" / "docs" / "tutorials"

# (stem, sidebar label, sidebar_position).
TUTORIALS: list[tuple[str, str, int]] = [
    ("01_quickstart", "Quickstart", 1),
    ("02_colors", "Team colors", 2),
    ("03_logos_and_seasons", "Logos and eras", 3),
    ("04_headshots", "Headshots", 4),
]


def _execute(nb):
    """Execute a notebook in-memory; raise on the first failing cell."""
    from nbclient import NotebookClient

    NotebookClient(nb, timeout=180, kernel_name="python3", allow_errors=False).execute()


def _to_markdown(nb, stem: str) -> str:
    """Render an (executed) notebook node to a markdown body string."""
    from nbconvert import MarkdownExporter
    from traitlets.config import Config

    cfg = Config()
    # MarkdownExporter already runs ExtractOutputPreprocessor; listing it again extracts every image twice and
    # nbconvert rejects the duplicate filenames. Image outputs land in <stem>_files/ alongside the page.
    cfg.ExtractOutputPreprocessor.output_filename_template = (
        f"{stem}_files/{{unique_key}}_{{cell_index}}_{{index}}{{extension}}"
    )
    exporter = MarkdownExporter(config=cfg)
    body, resources = exporter.from_notebook_node(nb, resources={"unique_key": stem})
    # Persist any extracted image outputs.
    for fname, data in (resources.get("outputs") or {}).items():
        dest = OUT_DIR / fname
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    return body


def _clean_outputs(nb) -> None:
    """In-place: tidy executed cell outputs for clean, theme-safe rendering.

    * Drop ``stderr`` stream outputs (warning noise -- e.g. env-specific version
      warnings -- that isn't pedagogically useful in a rendered tutorial).
    * Prefer the plain-text repr over the styled HTML one for DataFrames: polars /
      pandas ``text/html`` carries a scoped ``<style>`` block that can clash with
      the Docusaurus theme, whereas the ``text/plain`` box-drawing table renders as
      a clean monospace code block. Image outputs (``image/*``) are kept.
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
        body = _fix_links(_to_markdown(nb, stem))
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

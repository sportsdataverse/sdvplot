"""Execute the example notebooks and render them to Docusaurus pages, the gallery included.

Every notebook under ``examples/notebooks/`` (committed with outputs cleared) is EXECUTED against the real sdvplot
package and rendered (code + outputs) to a page, so the docs site shows real values, logos and charts. The folder
picks the section (``SECTIONS``): the top level is the getting-started tutorials, ``leagues/`` the league tutorials,
then ``cookbooks/``, ``recipes/`` and ``leaderboards/``. Each notebook's ``metadata["sdvplot"]`` gives its page
``label`` (sidebar), ``position`` and ``description``, and optionally a per-cell execution ``timeout`` in seconds
(default 600).

Outputs: PNGs are written next to the page (``<stem>_files/``). Interactive outputs become standalone HTML pages under
``docs/static/outputs/<section>/<stem>/<cell>_<output>.html``, shown in an ``<iframe>`` that the site's client module
(``docs/src/clientModules/sdvFrames.ts``) sizes from the height each page posts: Plotly figures (plotly.js from its
CDN), Vega-Lite specs (vega-embed from jsDelivr), widgets such as reactable (the Jupyter widgets HTML manager and the
widget state) and any other HTML (great_tables, folium, Altair, Bokeh and HoloViews, with BokehJS and Panel from their
CDNs). Polars frames print as markdown tables; a pandas frame's HTML gives way to its text.

Gallery: a code cell tagged ``gallery`` (``cell.metadata.tags``, optional ``cell.metadata.sdvplot_gallery`` with
``title`` and ``alt``) contributes its first PNG, downscaled to at most 640 px wide under ``docs/static/img/gallery/``.
Each render writes the notebook's gallery sidecar (``docs/src/data/gallery/<section>__<stem>.json``) and ``gallery.md``
is rebuilt from every sidecar, so a partial ``--only`` run keeps the gallery whole.

Execution hits live sources (the sdv-assets CDN, ESPN, nflverse and SportsDataverse releases), so this is **not** part
of the offline docs build. Run it locally or in the weekly workflow; the regular build consumes the committed pages:

    uv run python tools/render_notebooks.py                     # execute + render every notebook
    uv run python tools/render_notebooks.py --only leagues/nfl  # one notebook, by its path under examples/notebooks/
    uv run python tools/render_notebooks.py --no-execute        # render as committed (no live calls)
    uv run python tools/render_notebooks.py --gallery-only      # rebuild gallery.md from the sidecars only

Determinism / safety:

* ``JUPYTER_CONFIG_DIR`` is pointed at a throwaway dir so a polluted global jupyter/nbconvert config can't inject
  preprocessors.
* Pages are emitted as ``.md`` (CommonMark via Docusaurus ``format: detect``) so bare ``{`` / ``<`` in outputs don't
  trip the MDX parser. CommonMark still carries raw HTML blocks, which is how each cell's outputs get the theme's
  ``sdv-output`` wrapper and the iframes get in.
* Polars frames print as markdown tables (a hidden first cell sets ``pl.Config``).
* Kernels run with ``PYTHONHASHSEED=0``, so set order (Bokeh's glyph columns, for one) is the same in every render,
  and consecutive prints land in one text block however the kernel happened to flush them.
* The source ``.ipynb`` files are never modified -- execution happens on an in-memory copy. A notebook that fails
  keeps its previous page; one that is deleted loses its page, outputs, figures and gallery cards.
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

# Avoid loading a polluted global jupyter/nbconvert config (some machines register
# a missing ``jupyter_contrib_nbextensions`` preprocessor that breaks nbconvert).
os.environ["JUPYTER_CONFIG_DIR"] = tempfile.mkdtemp(prefix="sdvplot-nbrender-")

ROOT = Path(__file__).resolve().parents[1]
NB_DIR = ROOT / "examples" / "notebooks"
DOCS_DIR = ROOT / "docs" / "docs"  # pages
STATIC = ROOT / "docs" / "static"  # served at the site root
STATIC_NB = STATIC / "notebooks"  # byte-for-byte copies, served for download
OUTPUTS = STATIC / "outputs"  # standalone HTML outputs, framed by the pages
GALLERY_IMG = STATIC / "img" / "gallery"
GALLERY_DATA = ROOT / "docs" / "src" / "data" / "gallery"  # one sidecar per notebook with gallery cells
GALLERY_PAGE = DOCS_DIR / "gallery.md"
GITHUB_NB = "https://github.com/sportsdataverse/sdvplot/blob/main/examples/notebooks"
Files = dict[Path, bytes]  # a render's files, staged until all of it has succeeded (_swap_in)
DEFAULT_TIMEOUT = 600  # seconds per cell
FRAME_HEIGHT = 480  # px, an iframe's height until its page reports one (or for good, without JavaScript)
THUMB_WIDTH = 640  # px, the widest a gallery thumbnail gets
# Run before the notebook's own cells, then dropped from the page: frames print as markdown tables, and Altair embeds
# its charts with Vega's SVG renderer (the logo CDN sends no CORS header, so the canvas renderer drops image marks).
SETUP = (
    "import polars as pl\n"
    'pl.Config.set_tbl_formatting("MARKDOWN")\n'
    "pl.Config.set_tbl_hide_column_data_types(True)\n"
    "pl.Config.set_tbl_hide_dataframe_shape(True)\n"
    "pl.Config.set_tbl_cols(-1)\n"
    "pl.Config.set_fmt_str_lengths(200)\n"
    "pl.Config.set_tbl_width_chars(10000)\n"
    "try:\n"
    "    import altair as alt\n"
    '    alt.renderers.set_embed_options(renderer="svg", actions=False)\n'
    "except ImportError:\n"
    "    pass\n"
)

PLOTLY = "application/vnd.plotly.v1+json"
VEGALITE = re.compile(r"application/vnd\.vegalite\.v\d+[.+]json")  # Altair 6 sends ...v6.json, not v6+json
WIDGET_VIEW = "application/vnd.jupyter.widget-view+json"
WIDGET_STATE = "application/vnd.jupyter.widget-state+json"
BOKEH_EXEC = "application/vnd.bokehjs_exec.v0+json"
HOLOVIEWS_EXEC = "application/vnd.holoviews_exec.v0+json"
# output_notebook() / hv.extension(): the JavaScript a notebook front end loads once; a standalone page loads its own.
LOADERS = ("application/vnd.bokehjs_load.v0+json", "application/vnd.holoviews_load.v0+json")
# ... and what else they print: Bokeh's banner, HoloViews' module shim and logo, and Panel's comm document (a
# BrowserInfo + CommManager document with no plot, the extension's last output when logo=False).
EXTENSION_HTML = re.compile(r'bk-notebook-logo|class="logo-block"|type="esms-options"|panel\.models\.comm_manager\.')
# Random per-render ids (_stable_ids): Altair's chart div, uuid4s, and 32-hex ids not inside a URL or a longer hex run.
RANDOM_ID = re.compile(
    r"altair-viz-[0-9a-f]{32}"
    r"|(?<![\w/=.-])[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?![\w-])"
    r"|(?<![0-9a-f/=.])[0-9a-f]{32}(?![0-9a-f])"
)

# Each framed page reports its height to the docs page around it, on load, on resize and when asked
# (docs/src/clientModules/sdvFrames.ts); the html and body boxes cover margins and overflow.
SENDER = """<script>
(function () {
  function send() {
    var h = Math.max(document.documentElement.getBoundingClientRect().height, document.body.scrollHeight);
    parent.postMessage({sdvplotFrameHeight: Math.ceil(h)}, "*");
  }
  addEventListener("load", send);
  addEventListener("message", function (e) { if (e.data === "sdvplot:height?") send(); });
  if (window.ResizeObserver) new ResizeObserver(send).observe(document.body);
})();
</script>"""
PAGE_CSS = (
    "body{margin:0;padding:8px;background:#fff;color:#0e1626;"
    'font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}'
)
WIDGET_HEAD = (  # the Jupyter widgets HTML manager renders <script type="application/vnd.jupyter.widget-view+json">
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.6/require.min.js" '
    'crossorigin="anonymous"></script>\n'
    '<script src="https://cdn.jsdelivr.net/npm/@jupyter-widgets/html-manager@1/dist/embed-amd.js" '
    'crossorigin="anonymous"></script>\n'
)


class Section(NamedTuple):
    folder: str  # under examples/notebooks/ ("." is the top level)
    dir: str  # the pages' dir under docs/docs/; the same path under docs/static/outputs/ and docs/static/img/gallery/
    label: str  # sidebar category and gallery heading
    position: int
    noun: str  # a page's <title> is "<label> <noun>"
    description: str  # the category's index page


SECTIONS = {
    s.folder: s
    for s in (
        # The top-level tutorials sit in the sidebar's "Getting started" category with the intro (docs/sidebars.ts).
        Section(".", "tutorials", "Getting started", 1, "tutorial", "The basics, one notebook per topic."),
        Section(
            "leagues", "tutorials/leagues", "Tutorials by league", 2, "tutorial",
            "Worked examples for each league: logos, colors, headshots and tables with real data.",
        ),
        Section(
            "cookbooks", "cookbooks", "Cookbooks", 3, "cookbook",
            "Task-oriented guides, one plotting or table library or technique per page, across leagues.",
        ),
        Section(
            "recipes", "recipes", "Recipes", 4, "recipe",
            "Real-world charts and tables built end to end: get the data, shape it, plot it, polish it, export it.",
        ),
        Section(
            "leaderboards", "leaderboards", "Leaderboards", 5, "leaderboard",
            "Current-season leaderboards, re-rendered every week from the latest data.",
        ),
    )
}  # fmt: skip


class Notebook(NamedTuple):
    src: Path
    section: Section

    @property
    def stem(self) -> str:
        return self.src.stem

    @property
    def key(self) -> str:
        """The notebook's path under examples/notebooks/ without ``.ipynb`` (``--only`` takes it)."""
        return self.src.relative_to(NB_DIR).with_suffix("").as_posix()

    @property
    def page_dir(self) -> Path:
        return DOCS_DIR / self.section.dir

    @property
    def page(self) -> Path:
        return self.page_dir / f"{self.stem}.md"

    @property
    def outputs_dir(self) -> Path:
        return OUTPUTS / self.section.dir / self.stem

    @property
    def sidecar(self) -> Path:
        return GALLERY_DATA / f"{self.section.dir.replace('/', '-')}__{self.stem}.json"


def discover() -> list[Notebook]:
    """Every notebook under examples/notebooks/, with its section; one in a folder with no section is an error."""
    books = []
    for src in sorted(NB_DIR.rglob("*.ipynb")):
        if ".ipynb_checkpoints" in src.parts:
            continue
        folder = src.parent.relative_to(NB_DIR).as_posix()
        if folder not in SECTIONS:
            raise ValueError(f"{src}: not in a section folder ({', '.join(sorted(SECTIONS))})")
        books.append(Notebook(src, SECTIONS[folder]))
    return books


def _metadata(nb, name: str) -> dict:
    """The notebook's ``metadata["sdvplot"]`` with its timeout defaulted; raise on a missing or mistyped key."""
    meta = dict(nb.metadata.get("sdvplot", {}))
    for key, kind in (("label", str), ("position", int), ("description", str)):
        if not isinstance(meta.get(key), kind) or isinstance(meta.get(key), bool):
            raise ValueError(f"{name}: metadata.sdvplot.{key} must be a {kind.__name__}")
    meta.setdefault("timeout", DEFAULT_TIMEOUT)
    if not isinstance(meta["timeout"], int | float) or meta["timeout"] <= 0:
        raise ValueError(f"{name}: metadata.sdvplot.timeout must be a positive number of seconds")
    return meta


def _execute(nb, timeout: float = DEFAULT_TIMEOUT):
    """Execute a notebook in-memory behind the SETUP cell, then drop that cell; raise on the first failing cell."""
    import nbformat
    from nbclient import NotebookClient

    nb.cells.insert(0, nbformat.v4.new_code_cell(SETUP, id="sdvplot-render-setup"))
    try:
        client = NotebookClient(nb, timeout=timeout, kernel_name="python3", allow_errors=False)
        client.execute(env={**os.environ, "PYTHONHASHSEED": "0"})  # str hashes, so set order, alike in every render
    finally:
        nb.cells.pop(0)


def _fence(text: str, lang: str) -> str:
    """A fenced block one backtick longer than the longest backtick run inside it."""
    ticks = "`" * max(3, max((len(m) for m in re.findall(r"`+", text)), default=0) + 1)
    return f"{ticks}{lang}\n{text.rstrip(chr(10))}\n{ticks}"


def _normalize(text: str) -> str:
    """Match the repo's whitespace hooks (trailing-whitespace + end-of-file-fixer).

    Outputs carry trailing spaces / no final newline, and those hooks cover every generated page and HTML file.
    Normalizing here keeps a render byte-identical to what a committed-then-hooked file would be, so the weekly cron
    only opens a PR when the *data* changed -- not because of cosmetic whitespace churn."""
    return "\n".join(ln.rstrip() for ln in text.splitlines()).rstrip() + "\n"


def _page_html(body: str, head: str = "") -> str:
    """A standalone page for one output: a fragment gets a minimal document; either way the height SENDER is added."""
    if re.match(r"\s*<(!doctype|html)", body, re.I):
        end = body.lower().rfind("</body>")
        return body[:end] + SENDER + body[end:] if end >= 0 else body + SENDER
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<style>{PAGE_CSS}</style>\n{head}</head>\n<body>\n{body}\n{SENDER}\n</body>\n</html>\n"
    )


def _script_json(value) -> str:
    """JSON safe inside a <script> element."""
    return json.dumps(value).replace("</", "<\\/")


def _plotly_html(fig: dict) -> str:
    import plotly.io as pio

    # a fixed div id: a random one would change every render and churn the weekly refresh
    return pio.to_html(
        fig, include_plotlyjs="cdn", full_html=False, default_height="450px", validate=False, div_id="sdvplot-fig"
    )


def _vegalite_html(spec: dict) -> str:
    """vega-embed with the SVG renderer: the logo CDN sends no CORS header, and Vega's canvas renderer loads image
    marks as cross-origin images, which then fail; SVG ``<image>`` elements load them as is."""
    import altair as alt
    from altair.utils.html import spec_to_html

    return spec_to_html(
        spec,
        mode="vega-lite",
        vega_version=alt.VEGA_VERSION,
        vegaembed_version=alt.VEGAEMBED_VERSION,
        vegalite_version=alt.VEGALITE_VERSION,
        embed_options={"renderer": "svg", "actions": False},
        fullhtml=False,
    )


def _widget_html(view: dict, state: dict) -> str:
    """A widget view plus the notebook's whole widget state.

    ponytail: every model, not only those the view references: a reactable table finds its React module and import
    map by name, not by reference. A notebook with many widgets repeats their state in each page."""
    return (
        f'<script type="{WIDGET_STATE}">{_script_json(state)}</script>\n'
        f'<script type="{WIDGET_VIEW}">{_script_json(view)}</script>'
    )


def _bokeh_head(panel: bool) -> str:
    """BokehJS (and Panel, which HoloViews renders through) from their CDNs, at the installed versions."""
    from bokeh.resources import CDN

    urls = list(CDN.js_files)
    if panel:
        from panel.io.resources import CDN_DIST

        urls.append(f"{CDN_DIST}panel.min.js")
    return "".join(f'<script src="{u}" crossorigin="anonymous"></script>\n' for u in urls)


def _stable_ids(html: str, name: str) -> str:
    """Rename the ids a library draws at random on every render to ``sdv_<name>_<n>``, by first appearance and every
    reuse included, so an unchanged output renders byte-identical and the weekly refresh opens no PR for it.

    The ids: great_tables' 10-letter table id (reused in its CSS and, on a table with an id, its column ids),
    Altair's ``altair-viz-<hex>``, and the uuid4 and 32-hex ids of Bokeh, Panel, folium and Jupyter widget models.
    Underscores, not hyphens: folium uses its ids in JavaScript variable names. A token in a URL path or query
    (after ``/``, ``=`` or ``.``) is not an id and stays."""
    tables = [i for i in re.findall(r'<div id="([a-z]{10})"', html) if f"#{i}" in html]
    for n, old in enumerate(dict.fromkeys(tables + RANDOM_ID.findall(html))):
        new = f"sdv_{name}_{n}"
        around = (r"(?<![\w-])", r"(?!\w)") if old in tables else (r"(?<![/=.])", r"(?![0-9a-f])")
        html = re.sub(around[0] + re.escape(old) + around[1], new, html)
    return html


def _frame(book: Notebook, name: str, html: str, title: str, files: Files) -> str:
    """Stage one output's standalone page in ``files`` and return the iframe that shows it."""
    dest = book.outputs_dir / f"{name}.html"
    files[dest] = _normalize(_stable_ids(html, name)).encode()
    src = "/" + dest.relative_to(STATIC).as_posix()
    return f'<iframe class="sdv-frame" src="{src}" title="{title}" height="{FRAME_HEIGHT}" loading="lazy"></iframe>'


def _output(out, book: Notebook, cell_index: int, index: int, widgets: dict | None, files: Files) -> str | None:
    """One cell output as markdown: images to <stem>_files/ and interactive output to a framed page (both staged in
    ``files``), markdown (frames) as is, text in a fence."""
    data = out.get("data", {})
    name = f"{cell_index}_{index}"
    if out.get("output_type") == "stream":
        text = out.get("text", "")
        return _fence(text, "text") if text.strip() else None  # a bare print() draws no empty block
    if "image/png" in data:
        rel = f"{book.stem}_files/{book.stem}_{name}.png"
        files[book.page_dir / rel] = base64.b64decode(data["image/png"])
        return f"![png]({rel})"
    if PLOTLY in data:
        return _frame(book, name, _page_html(_plotly_html(data[PLOTLY])), "Interactive Plotly figure", files)
    if vl := next((m for m in data if VEGALITE.fullmatch(m)), None):
        return _frame(book, name, _page_html(_vegalite_html(data[vl])), "Interactive Vega-Lite chart", files)
    if WIDGET_VIEW in data and widgets:
        head = WIDGET_HEAD
        if any(m.get("state", {}).get("_module") == "reactable" for m in widgets.get("state", {}).values()):
            from importlib.resources import files as package_files  # the styles a notebook gets from embed_css()

            css = package_files("reactable").joinpath("static/reactable-py.esm.css").read_text("utf-8")
            head += f"<style>{css}</style>\n"
        html = _page_html(_widget_html(data[WIDGET_VIEW], widgets), head)
        return _frame(book, name, html, "Interactive widget", files)
    if "text/html" in data:
        html = data["text/html"]
        if HOLOVIEWS_EXEC in data:
            return _frame(book, name, _page_html(html, _bokeh_head(True)), "Interactive HoloViews figure", files)
        if BOKEH_EXEC in data:
            return _frame(book, name, _page_html(html, _bokeh_head(False)), "Interactive Bokeh figure", files)
        return _frame(book, name, _page_html(html), "HTML output", files)
    if "text/markdown" in data:
        return data["text/markdown"].strip("\n")
    if "text/plain" in data:
        return _fence(data["text/plain"], "text")
    return None


def _to_markdown(nb, book: Notebook, files: Files) -> str:
    """Render an (executed) notebook node to a markdown body string, staging its figures and framed pages in
    ``files`` for ``_swap_in``.

    Markdown cells are copied, code cells become ```python fences, and each code cell's outputs sit in one
    ``<div class="sdv-output">`` (styled by the shared theme) so output never reads as more input. The blank lines
    around the fences are what let CommonMark parse markdown inside the HTML block."""
    widgets = nb.metadata.get("widgets", {}).get(WIDGET_STATE)
    parts: list[str] = []
    for ci, cell in enumerate(nb.cells):
        if cell.get("cell_type") == "markdown":
            parts.append(cell.source)
        elif cell.get("cell_type") == "code":
            parts.append(_fence(cell.source, "python"))
            outs = [
                md for oi, o in enumerate(cell.get("outputs", [])) if (md := _output(o, book, ci, oi, widgets, files))
            ]
            if outs:
                parts.append('<div class="sdv-output">\n\n' + "\n\n".join(outs) + "\n\n</div>")
    return "\n\n".join(parts) + "\n"


def _clean_outputs(nb) -> None:
    """In-place: tidy executed cell outputs for clean, theme-safe rendering.

    * Drop ``stderr`` stream outputs (warning noise -- e.g. env-specific version warnings -- that isn't
      pedagogically useful in a rendered tutorial), and join consecutive ``stdout`` outputs into one.
    * A frame's plain text beats its styled HTML: polars / pandas ``text/html`` carries a scoped ``<style>`` block
      that can clash with the Docusaurus theme. A polars frame's plain text is a markdown table (``SETUP``), so it
      moves to ``text/markdown`` and renders as a table. Other HTML (great_tables, folium, ...) stays, for a frame.
    * A front-end extension's outputs (``output_notebook()``, ``hv.extension()``: everything up to its last loader
      or banner) go, printed text aside: each framed page loads the libraries itself. What the cell shows after them
      (``show(p)`` in the same cell) stays.
    * Bokeh's ``show()`` sends a figure's ``<div>`` and its script as two outputs; the script joins the ``<div>``.
    """
    for cell in nb.cells:
        if cell.get("cell_type") != "code":
            continue
        outputs = cell.get("outputs", [])
        last_init = max(
            (
                i
                for i, o in enumerate(outputs)
                if any(m in o.get("data", {}) for m in LOADERS)
                or EXTENSION_HTML.search(o.get("data", {}).get("text/html", ""))
            ),
            default=-1,
        )
        kept: list = []
        joinable = False  # the last kept output is stdout, with only stderr after it: the kernel's flush timer splits
        for i, o in enumerate(outputs):  # prints into one stream output or several, differently from render to render
            ot = o.get("output_type")
            if ot == "stream":
                if o.get("name") == "stderr":
                    continue
                if joinable:
                    kept[-1]["text"] += o.get("text", "")
                else:
                    kept.append(o)
                joinable = True
                continue
            joinable = False
            data = o.get("data", {})
            if i <= last_init:
                continue
            if BOKEH_EXEC in data:
                if kept and "text/html" in kept[-1].get("data", {}):
                    js = data.get("application/javascript", "")
                    kept[-1]["data"]["text/html"] += f'\n<script type="text/javascript">\n{js}\n</script>'
                    kept[-1]["data"][BOKEH_EXEC] = {}
                continue
            html = data.get("text/html", "")
            if (
                re.search(r"(?i)<(style|link)\b", html)
                and not re.sub(r"(?is)<style.*?</style>|<link[^>]*>|</?div[^>]*>", "", html).strip()
            ):
                continue  # styles only (reactable's embed_css()): nothing to show, and each framed page has its own
            if "text/plain" in data and 'class="dataframe"' in html:
                data.pop("text/html")
                if data["text/plain"].startswith("|"):
                    data["text/markdown"] = data.pop("text/plain")
            kept.append(o)
        cell["outputs"] = kept


def _fix_links(body: str, book: Notebook) -> str:
    """Point relative links to other notebooks (``../cookbooks/tables.ipynb#x``) at their rendered pages.

    A link is resolved from the notebook's folder and rewritten relative to the page's, since the pages do not
    mirror the notebook folders (the top level renders to ``tutorials/``). Absolute and unknown links stay."""

    def page_link(m: re.Match) -> str:
        target = (book.src.parent / m.group(1)).resolve()
        try:
            folder = target.parent.relative_to(NB_DIR.resolve()).as_posix()
        except ValueError:
            return m.group(0)
        if folder not in SECTIONS:
            return m.group(0)
        page = DOCS_DIR / SECTIONS[folder].dir / f"{target.stem}.md"
        return f"]({os.path.relpath(page, book.page_dir).replace(os.sep, '/')}{m.group(2) or ''})"

    return re.sub(r"\]\((?![a-z][a-z0-9+.-]*:|/)([^)\s#]+\.ipynb)(#[^)\s]*)?\)", page_link, body)


def _notebook_links(body: str, book: Notebook) -> str:
    """A closing section: a download of the notebook (a copy served from docs/static/notebooks/; ``pathname://``
    keeps Docusaurus from treating the file as a page) and the notebook on GitHub."""
    return body.rstrip("\n") + (
        "\n\n## Run it yourself\n\n"
        f'<a href="pathname:///notebooks/{book.key}.ipynb" download>Download the notebook</a> (outputs cleared) '
        f"or [open it on GitHub]({GITHUB_NB}/{book.key}.ipynb).\n"
    )


def _yaml(value: str) -> str:
    """A frontmatter string, always double-quoted and escaped: labels carry ', & and : ("Men's college basketball",
    "College baseball & softball"), and a JSON string is a valid YAML double-quoted scalar."""
    return json.dumps(value, ensure_ascii=False)


def _frontmatter(meta: dict, section: Section) -> str:
    return (
        f"---\ntitle: {_yaml(meta['label'] + ' ' + section.noun)}\nsidebar_label: {_yaml(meta['label'])}\n"
        f"sidebar_position: {meta['position']}\ndescription: {_yaml(meta['description'])}\n---\n\n"
    )


def _slug(text: str) -> str:
    """The id Docusaurus gives a heading (github-slugger) from its markdown source."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # a link reads as its text
    text = re.sub(r"[`*]", "", text).strip().lower()
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def _gallery_items(nb, book: Notebook, meta: dict, files: Files) -> list[dict]:
    """Thumbnail each ``gallery``-tagged cell's first PNG (staged in ``files``); return the cards, each linked to the
    heading above it."""
    from PIL import Image

    seen: dict[str, int] = {}
    heading, anchor, items = "", "", []
    for ci, cell in enumerate(nb.cells):
        if cell.get("cell_type") == "markdown":
            fenced = False
            for line in cell.source.splitlines():
                if line.lstrip().startswith(("```", "~~~")):
                    fenced = not fenced
                elif not fenced and (m := re.match(r"(#{1,6})\s+(.+?)\s*#*\s*$", line)):
                    slug = base = _slug(m.group(2))
                    while slug in seen:  # repeats get -1, -2, ... as github-slugger numbers them
                        seen[base] += 1
                        slug = f"{base}-{seen[base]}"
                    seen[slug] = 0
                    if len(m.group(1)) > 1:  # the page's h1 is its title, with no anchor
                        heading, anchor = re.sub(r"^\d+\.\s*", "", m.group(2).replace("`", "")), slug
            continue
        if "gallery" not in cell.get("metadata", {}).get("tags", []):
            continue
        png = next((o["data"]["image/png"] for o in cell.get("outputs", []) if "image/png" in o.get("data", {})), None)
        if png is None:
            continue
        img = Image.open(io.BytesIO(base64.b64decode(png)))
        if img.width > THUMB_WIDTH:
            img = img.resize((THUMB_WIDTH, round(img.height * THUMB_WIDTH / img.width)), Image.Resampling.LANCZOS)
        dest = GALLERY_IMG / book.section.dir / f"{book.stem}_{ci}.png"
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        files[dest] = buf.getvalue()
        card = cell.get("metadata", {}).get("sdvplot_gallery", {})
        title = card.get("title") or heading or meta["label"]
        items.append(
            {
                "title": title,
                "alt": card.get("alt") or title,
                "image": "/" + dest.relative_to(STATIC).as_posix(),
                "anchor": anchor,
            }
        )
    return items


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def _md_text(text: str) -> str:
    """Text safe inside a markdown link or image: brackets and backslashes escaped, no raw HTML."""
    return re.sub(r"([\[\]\\])", r"\\\1", text).replace("<", "&lt;").replace("\n", " ")


def _write_gallery(books: list[Notebook]) -> None:
    """Rebuild gallery.md from every notebook's sidecar, grouped by section; a deleted notebook's sidecar goes."""
    known = {b.sidecar for b in books}
    for path in GALLERY_DATA.glob("*.json"):
        if path not in known:
            path.unlink()
    entries = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(GALLERY_DATA.glob("*.json"))]
    lines = [
        "---\ntitle: Gallery\nsidebar_label: Gallery\n"
        "description: Every figure tagged for the gallery in the example notebooks, linked to the example that draws "
        "it.\n---\n\n# Gallery\n\nFigures from the tutorials, cookbooks, recipes and leaderboards. Each card links to "
        "the example that draws it; the pages are rendered from the notebooks in `examples/notebooks/`."
    ]
    for section in sorted(SECTIONS.values(), key=lambda s: s.position):
        cards = [
            # a raw <img>: Docusaurus's markdown-image transform escapes an apostrophe in the alt text twice
            f'[<img src="{item["image"]}" alt="{html.escape(item["alt"])}" loading="lazy"/><br/>'
            f"{_md_text(item['title'])}"
            f"<br/><small>{_md_text(entry['label'])}</small>]({entry['page']}"
            + (f"#{item['anchor']})" if item["anchor"] else ")")
            for entry in sorted(
                (e for e in entries if e["section"] == section.dir), key=lambda e: (e["position"], e["stem"])
            )
            for item in entry["items"]
        ]
        if cards:
            lines.append(
                f"## {section.label}\n\n" + '<div class="sdv-gallery">\n\n' + "\n\n".join(cards) + "\n\n</div>"
            )
    if len(lines) == 1:
        lines.append("No figures yet.")
    GALLERY_PAGE.parent.mkdir(parents=True, exist_ok=True)
    GALLERY_PAGE.write_text(_normalize("\n\n".join(lines)), encoding="utf-8", newline="\n")


def _write_categories(books: list[Notebook]) -> None:
    """Each section with notebooks gets a _category_.json (sidebar label, position, index page) for docs/sidebars.ts.

    The top-level tutorials have none: the sidebar lists them under the intro, in its "Getting started" category."""
    for section in {b.section for b in books if b.section.folder != "."}:
        slug = "/category/" + section.label.lower().replace(" ", "-")
        link = {"type": "generated-index", "slug": slug, "description": section.description}
        _write_json(
            DOCS_DIR / section.dir / "_category_.json",
            {"label": section.label, "position": section.position, "link": link},
        )


def _prune(books: list[Notebook]) -> None:
    """Remove what deleted or moved notebooks left: pages, figures, framed outputs, thumbnails, notebook copies, and
    the category of a section left with no notebooks."""
    for section in SECTIONS.values():
        stems = {b.stem for b in books if b.section == section}
        if not stems and section.folder != ".":
            (DOCS_DIR / section.dir / "_category_.json").unlink(missing_ok=True)
        for page in (DOCS_DIR / section.dir).glob("*.md"):
            if page.stem not in stems:
                page.unlink()
                shutil.rmtree(page.with_name(f"{page.stem}_files"), ignore_errors=True)
        nested = {s.dir for s in SECTIONS.values()}  # outputs/tutorials/ holds outputs/tutorials/leagues/
        for path in (OUTPUTS / section.dir).glob("*"):
            if path.is_dir() and path.name not in stems and f"{section.dir}/{path.name}" not in nested:
                shutil.rmtree(path)
        for thumb in (GALLERY_IMG / section.dir).glob("*.png"):
            if (m := re.fullmatch(r"(.+)_\d+", thumb.stem)) and m.group(1) not in stems:
                thumb.unlink()
    keys = {b.key for b in books}
    for copy in STATIC_NB.rglob("*.ipynb"):
        if copy.relative_to(STATIC_NB).with_suffix("").as_posix() not in keys:
            copy.unlink()


def _swap_in(book: Notebook, files: Files) -> None:
    """Replace a notebook's previous figures, framed pages and thumbnails (no orphans when cells move) with its staged
    files, and write the rest of them."""
    shutil.rmtree(book.page_dir / f"{book.stem}_files", ignore_errors=True)
    shutil.rmtree(book.outputs_dir, ignore_errors=True)
    for old in (GALLERY_IMG / book.section.dir).glob(f"{book.stem}_*.png"):
        if re.fullmatch(re.escape(book.stem) + r"_\d+\.png", old.name):
            old.unlink()
    for path, data in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def render(book: Notebook, *, execute: bool = True) -> None:
    """Execute (unless told not to) and render one notebook: its page, outputs, notebook copy and gallery sidecar."""
    import nbformat

    nb = nbformat.read(book.src, as_version=4)
    meta = _metadata(nb, book.key)
    if execute:
        _execute(nb, meta["timeout"])
    _clean_outputs(nb)
    files: Files = {}
    body = _notebook_links(_fix_links(_to_markdown(nb, book, files), book), book)
    items = _gallery_items(nb, book, meta, files)
    files[book.page] = _normalize(_frontmatter(meta, book.section) + body).encode()
    files[STATIC_NB / f"{book.key}.ipynb"] = book.src.read_bytes()
    _swap_in(book, files)  # only once everything rendered: a failure above leaves the previous render whole
    if items:
        page = book.page.relative_to(DOCS_DIR).as_posix()
        entry = {"section": book.section.dir, "stem": book.stem, "label": meta["label"], "position": meta["position"]}
        _write_json(book.sidecar, {**entry, "page": page, "items": items})
    else:
        book.sidecar.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-execute", action="store_true", help="render notebooks as-is (no live API calls)")
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        help="only render this notebook, by its path under examples/notebooks/ (leagues/nfl); repeatable",
    )
    ap.add_argument(
        "--gallery-only",
        action="store_true",
        help="render nothing: rebuild gallery.md from the committed sidecars (e.g. after a merge conflict in it)",
    )
    args = ap.parse_args(argv)

    books = discover()
    by_key = {b.key: b for b in books}
    only = [re.sub(r"\.ipynb$", "", k.replace("\\", "/")) for k in args.only]
    if unknown := [k for k in only if k not in by_key]:
        print(f"unknown notebook(s): {', '.join(unknown)}; known: {', '.join(by_key)}", file=sys.stderr)
        return 2
    if args.gallery_only:
        _write_gallery(books)
        return 0
    _prune(books)
    _write_categories(books)
    failures = []
    selected = [by_key[k] for k in only] if only else books
    for book in selected:
        print(f"Rendering {book.key} ...", flush=True)
        try:
            render(book, execute=not args.no_execute)
        except Exception as e:  # noqa: BLE001 -- surface which notebook broke; it keeps its previous page
            print(f"  FAILED {book.key}: {type(e).__name__}: {str(e)[:300]}", file=sys.stderr)
            failures.append(book.key)
            continue
        print(f"  wrote {book.page.relative_to(ROOT).as_posix()}")
    _write_gallery(books)

    if failures:
        print(f"\nFAILED ({len(failures)}): {', '.join(failures)}", file=sys.stderr)
        return 1
    print(f"\nrendered {len(selected)} notebook page(s); gallery -> {GALLERY_PAGE.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

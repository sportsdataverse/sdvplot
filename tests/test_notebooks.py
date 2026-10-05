import base64
import importlib.util
import io
import json
import re
from pathlib import Path

import nbformat
import polars as pl
import pytest
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook, new_output
from PIL import Image

ROOT = Path(__file__).parents[1]
NB = ROOT / "examples" / "notebooks"
spec = importlib.util.spec_from_file_location("render_notebooks", ROOT / "tools" / "render_notebooks.py")
rn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rn)

GETTING_STARTED = ["01_quickstart", "02_colors", "03_logos_and_seasons", "04_headshots"]


def _png(width=1000, height=500) -> str:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), "navy").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@pytest.fixture
def site(tmp_path, monkeypatch):
    """The renderer's paths moved under tmp_path: notebooks in nb/, pages in docs/, static files in static/."""
    for name, rel in {
        "ROOT": ".",
        "NB_DIR": "nb",
        "DOCS_DIR": "docs",
        "STATIC": "static",
        "STATIC_NB": "static/notebooks",
        "OUTPUTS": "static/outputs",
        "GALLERY_IMG": "static/img/gallery",
        "GALLERY_DATA": "data/gallery",
        "GALLERY_PAGE": "docs/gallery.md",
    }.items():
        monkeypatch.setattr(rn, name, tmp_path / rel)
    return tmp_path


def _write_nb(site, key, *cells, label="T", position=1, **extra):
    path = site / "nb" / f"{key}.ipynb"
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {"label": label, "position": position, "description": f"About {label}.", **extra}
    nbformat.write(new_notebook(cells=list(cells), metadata={"sdvplot": meta}), path)
    return path


def _notebook(*outputs):
    nb = new_notebook()
    nb.cells = [new_markdown_cell("# T"), new_code_cell("x")]
    nb.cells[1].outputs = list(outputs)
    return nb


def _book(site, key="cookbooks/t"):
    folder, _, stem = key.rpartition("/")
    return rn.Notebook(site / "nb" / (folder or ".") / f"{stem}.ipynb", rn.SECTIONS[folder or "."])


# --- the committed notebooks and pages --------------------------------------------------------------------------


def test_every_notebook_is_in_a_section_with_its_metadata():
    books = rn.discover()
    assert [b.key for b in books if b.section.folder == "."] == GETTING_STARTED
    for book in books:
        meta = rn._metadata(nbformat.read(book.src, as_version=4), book.key)
        assert meta["timeout"] > 0 and meta["description"].endswith("."), book.key


def test_notebooks_are_committed_without_outputs():  # every section folder, not only the top level
    paths = sorted(NB.rglob("*.ipynb"))
    assert paths
    for path in paths:
        nb = nbformat.read(path, as_version=4)
        for cell in nb.cells:
            if cell.cell_type == "code":
                assert cell.outputs == [] and cell.execution_count is None, f"{path.name} has outputs"


def test_every_notebook_has_step_headings():
    for path in sorted(NB.rglob("*.ipynb")):
        nb = nbformat.read(path, as_version=4)
        steps = sum(len(re.findall(r"^## ", c.source, re.M)) for c in nb.cells if c.cell_type == "markdown")
        assert steps >= 2, path.name


def test_rendered_pages_have_frontmatter_outputs_headings_and_notebook_links():
    for book in rn.discover():
        meta = rn._metadata(nbformat.read(book.src, as_version=4), book.key)
        page = book.page.read_text(encoding="utf-8")
        assert page.startswith(rn._frontmatter(meta, book.section)), book.key
        assert '<div class="sdv-output">' in page, book.key
        assert not re.search("[┌│╞═]", page), book.key
        assert len(re.findall(r"^## ", page, re.M)) >= 3, book.key  # two step headings and "Run it yourself"
        assert f'<a href="pathname:///notebooks/{book.key}.ipynb" download>' in page, book.key
        assert f"]({rn.GITHUB_NB}/{book.key}.ipynb)" in page, book.key


def test_the_getting_started_pages_keep_their_urls_and_titles():
    titles = ["Quickstart", "Team colors", "Logos and eras", "Headshots"]
    for stem, label in zip(GETTING_STARTED, titles, strict=True):
        page = (ROOT / "docs" / "docs" / "tutorials" / f"{stem}.md").read_text(encoding="utf-8")
        assert page.startswith(f'---\ntitle: "{label} tutorial"\nsidebar_label: "{label}"\n'), stem


def test_the_downloadable_notebooks_match_the_sources():
    for book in rn.discover():
        copy = rn.STATIC_NB / f"{book.key}.ipynb"
        assert copy.read_bytes() == book.src.read_bytes(), book.key


def test_the_committed_gallery_is_the_one_its_sidecars_make(site):
    sidecars = sorted((ROOT / "docs" / "src" / "data" / "gallery").glob("*.json"))
    assert sidecars  # 02 and 03 tag figures
    (site / "data" / "gallery").mkdir(parents=True)
    for path in sidecars:
        entry = json.loads(path.read_text(encoding="utf-8"))
        assert (ROOT / "docs" / "docs" / entry["page"]).is_file(), path.name
        for item in entry["items"]:
            image = ROOT / "docs" / "static" / item["image"].lstrip("/")
            assert Image.open(image).width <= rn.THUMB_WIDTH, image
        (site / "data" / "gallery" / path.name).write_bytes(path.read_bytes())
    # the repo's notebooks; a sidecar's name depends only on the section and stem
    repo_books = [rn.Notebook(src, rn.SECTIONS[src.parent.relative_to(NB).as_posix()]) for src in NB.rglob("*.ipynb")]
    rn._write_gallery(repo_books)
    assert (site / "docs" / "gallery.md").read_text(encoding="utf-8") == (
        ROOT / "docs" / "docs" / "gallery.md"
    ).read_text(encoding="utf-8")


def test_the_sidebar_lists_every_notebook_section():
    sidebars = (ROOT / "docs" / "sidebars.ts").read_text(encoding="utf-8")
    for section in rn.SECTIONS.values():
        assert f"'{section.dir}'" in sidebars, section.dir


# --- discovery and metadata --------------------------------------------------------------------------------------


def test_discovery_maps_each_folder_to_its_section(site):
    for key in ["01_a", "leagues/nfl", "cookbooks/tables", "recipes/bump", "leaderboards/nba"]:
        _write_nb(site, key)
    (site / "nb" / ".ipynb_checkpoints").mkdir()
    (site / "nb" / ".ipynb_checkpoints" / "01_a-checkpoint.ipynb").write_text("{}")
    books = {b.key: b for b in rn.discover()}
    assert sorted(books) == ["01_a", "cookbooks/tables", "leaderboards/nba", "leagues/nfl", "recipes/bump"]
    assert books["01_a"].page == site / "docs" / "tutorials" / "01_a.md"
    assert books["leagues/nfl"].page == site / "docs" / "tutorials" / "leagues" / "nfl.md"
    assert books["leagues/nfl"].outputs_dir == site / "static" / "outputs" / "tutorials" / "leagues" / "nfl"
    assert books["leagues/nfl"].sidecar == site / "data" / "gallery" / "tutorials-leagues__nfl.json"
    assert books["cookbooks/tables"].page == site / "docs" / "cookbooks" / "tables.md"


def test_a_notebook_outside_the_section_folders_is_an_error(site):
    _write_nb(site, "drafts/x")
    with pytest.raises(ValueError, match="not in a section folder"):
        rn.discover()


def test_metadata_needs_label_position_and_description_and_defaults_the_timeout():
    nb = new_notebook(metadata={"sdvplot": {"label": "NFL", "position": 1, "description": "x."}})
    assert rn._metadata(nb, "n")["timeout"] == 600
    nb.metadata["sdvplot"]["timeout"] = 900
    assert rn._metadata(nb, "n")["timeout"] == 900
    for bad in ({"label": "NFL", "description": "x."}, {"label": "NFL", "position": "1", "description": "x."}):
        with pytest.raises(ValueError, match="metadata.sdvplot.position"):
            rn._metadata(new_notebook(metadata={"sdvplot": bad}), "n")
    with pytest.raises(ValueError, match="metadata.sdvplot.label"):
        rn._metadata(new_notebook(), "n")


def test_frontmatter_values_are_quoted_so_any_label_reads_back_unchanged():
    yaml = pytest.importorskip("yaml")
    meta = {
        "label": 'Men\'s "college" baseball & softball: AHL',
        "position": 2,
        "description": 'Leaders: by week & team (it\'s "live") #1 \\ é.',
    }
    text = rn._frontmatter(meta, rn.SECTIONS["leaderboards"])
    assert text.startswith('---\ntitle: "Men\'s \\"college\\" baseball & softball: AHL leaderboard"\n')
    assert yaml.safe_load(text.split("---\n")[1]) == {
        "title": meta["label"] + " leaderboard",
        "sidebar_label": meta["label"],
        "sidebar_position": 2,
        "description": meta["description"],
    }


# --- outputs -----------------------------------------------------------------------------------------------------


def test_a_cells_outputs_sit_in_one_sdv_output_block_after_its_code(site):
    nb = _notebook(
        new_output("stream", name="stdout", text="hi\n"),
        new_output("execute_result", data={"text/plain": "1"}, execution_count=1),
    )
    assert rn._to_markdown(nb, _book(site)) == (
        '# T\n\n```python\nx\n```\n\n<div class="sdv-output">\n\n```text\nhi\n```\n\n```text\n1\n```\n\n</div>\n'
    )


def test_an_empty_print_draws_no_output_block(site):
    nb = _notebook(new_output("stream", name="stdout", text="\n"))
    assert "sdv-output" not in rn._to_markdown(nb, _book(site))


def test_a_polars_frame_becomes_a_table_while_a_pandas_frame_and_a_series_stay_text(site):  # RF 5
    nb = _notebook(
        new_output(
            "execute_result",
            data={"text/html": '<table class="dataframe"/>', "text/plain": "| a |\n|---|\n| 1 |"},
            execution_count=1,
        ),
        new_output(
            "execute_result",
            data={"text/html": '<table class="dataframe"/>', "text/plain": "   a\n0  1"},
            execution_count=2,
        ),
        new_output("execute_result", data={"text/plain": "shape: (1,)\nSeries: 'a' [i64]"}, execution_count=3),
    )
    rn._clean_outputs(nb)
    body = rn._to_markdown(nb, _book(site))
    assert "\n\n| a |\n|---|\n| 1 |\n\n" in body
    assert "```text\n   a\n0  1\n```" in body
    assert "```text\nshape: (1,)\nSeries: 'a' [i64]\n```" in body
    assert "iframe" not in body


def test_a_fence_outlasts_backticks_in_the_output():  # Review Focus 4
    assert rn._fence("a ``` b", "text") == "````text\na ``` b\n````"


def test_an_image_output_is_written_once_under_the_page_files(site):
    book = _book(site, "01_t")
    (site / "docs" / "tutorials" / "01_t_files").mkdir(parents=True)
    (site / "docs" / "tutorials" / "01_t_files" / "01_t_9_0.png").write_bytes(b"stale")
    body = rn._to_markdown(_notebook(new_output("display_data", data={"image/png": _png(), "text/plain": "<F>"})), book)
    assert "![png](01_t_files/01_t_1_0.png)" in body and "<F>" not in body
    assert sorted(p.name for p in (site / "docs" / "tutorials" / "01_t_files").iterdir()) == ["01_t_1_0.png"]


def _framed(site, *outputs, widgets=None):
    """Render one code cell's outputs; return the page body and the standalone pages written, by name."""
    nb = _notebook(*outputs)
    if widgets:
        nb.metadata["widgets"] = {rn.WIDGET_STATE: widgets}
    rn._clean_outputs(nb)
    book = _book(site)
    body = rn._to_markdown(nb, book)
    pages = {p.name: p.read_text(encoding="utf-8") for p in sorted(book.outputs_dir.glob("*.html"))}
    return body, pages


def test_an_html_output_becomes_a_framed_standalone_page(site):
    gt = '<div id="x"><style>#x table {color: red}</style><table class="gt_table"><tr><td>KC</td></tr></table></div>'
    body, pages = _framed(site, new_output("execute_result", data={"text/html": gt, "text/plain": "GT(...)"}))
    assert body.endswith(
        '<div class="sdv-output">\n\n<iframe class="sdv-frame" src="/outputs/cookbooks/t/1_0.html" '
        'title="HTML output" height="480" loading="lazy"></iframe>\n\n</div>\n'
    )
    assert "GT(...)" not in body
    page = pages["1_0.html"]
    assert page.startswith('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">')
    assert gt in page and rn.SENDER in page and page.endswith("</html>\n")
    assert "sdvplotFrameHeight" in rn.SENDER and "sdvplot:height?" in rn.SENDER
    assert not re.search(r"[ \t]$", page, re.M)  # the whitespace hooks find nothing to rewrite


def test_a_full_html_document_keeps_its_own_head(site):
    doc = "<!DOCTYPE html><html><head><title>x</title></head><body><p>map</p></body></html>"
    _, pages = _framed(site, new_output("display_data", data={"text/html": doc}))
    assert pages["1_0.html"].startswith("<!DOCTYPE html><html><head><title>x</title>")
    assert pages["1_0.html"].index(rn.SENDER) < pages["1_0.html"].index("</body>")


def test_a_plotly_figure_becomes_a_page_with_plotly_js_from_its_cdn(site):
    fig = {"data": [{"type": "scatter", "x": [1, 2], "y": [3, 4]}], "layout": {"title": {"text": "EPA"}}}
    body, pages = _framed(site, new_output("display_data", data={rn.PLOTLY: fig}))
    assert 'title="Interactive Plotly figure"' in body
    page = pages["1_0.html"]
    assert re.search(r'<script charset="utf-8" src="https://cdn\.plot\.ly/plotly-[\d.]+\.min\.js"', page)
    assert 'id="sdvplot-fig"' in page and '"EPA"' in page  # a fixed div id: no churn between renders
    assert rn.SENDER in page


def test_a_vega_lite_spec_becomes_a_page_with_vega_embed(site):
    spec = {"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "mark": "bar", "data": {"values": []}}
    body, pages = _framed(site, new_output("display_data", data={"application/vnd.vegalite.v5+json": spec}))
    assert 'title="Interactive Vega-Lite chart"' in body
    page = pages["1_0.html"]
    assert "https://cdn.jsdelivr.net/npm/vega-embed@" in page and '"mark": "bar"' in page
    # the SVG renderer: the logo CDN sends no CORS header, so canvas image marks would not load
    embed = re.search(r"var embedOpt = (\{.*?\});", page)
    assert embed and json.loads(embed.group(1)) == {"renderer": "svg", "actions": False, "mode": "vega-lite"}
    assert 'vegaEmbed("#vis", spec, embedOpt)' in page


def test_a_vega_lite_mime_key_without_the_plus_still_frames():  # Altair 6 names it application/vnd.vegalite.v6.json
    assert rn.VEGALITE.fullmatch("application/vnd.vegalite.v6.json")
    assert rn.VEGALITE.fullmatch("application/vnd.vegalite.v5+json")


def test_a_real_altair_chart_embeds_with_the_svg_renderer(site):
    # Altair 6's default renderer sends text/html only, so the frame is Altair's own embed; the logo CDN sends no CORS
    # header, so Vega's canvas renderer would drop every image mark while its SVG renderer draws them
    code = (
        "import altair as alt\nimport polars as pl\n"
        "df = pl.DataFrame({'x': [1], 'y': [2], 'logo': ['https://example.org/kc.png']})\n"
        "alt.Chart(df).mark_image(width=40, height=40).encode(x='x', y='y', url='logo')"
    )
    nb = new_notebook(cells=[new_code_cell(code)])
    rn._execute(nb, 120)
    rn._clean_outputs(nb)
    body = rn._to_markdown(nb, _book(site))
    assert 'src="/outputs/cookbooks/t/0_0.html" title="HTML output"' in body
    page = (site / "static" / "outputs" / "cookbooks" / "t" / "0_0.html").read_text(encoding="utf-8")
    assert '"mark": {"type": "image"' in page
    assert '{"renderer": "svg", "actions": false, "mode": "vega-lite"}' in page


def test_bokeh_joins_its_div_and_script_and_loads_bokehjs(site):
    loader = {"application/javascript": "load()", "application/vnd.bokehjs_load.v0+json": "load()"}
    nb = new_notebook()
    nb.cells = [new_code_cell("output_notebook()"), new_code_cell("show(p)")]
    nb.cells[0].outputs = [
        new_output("display_data", data={"text/html": "<div>Loading BokehJS ...</div>"}),
        new_output("display_data", data=loader),
    ]
    nb.cells[1].outputs = [
        new_output("display_data", data={"text/html": '<div id="p1" data-root-id="p2"></div>'}),
        new_output("display_data", data={"application/javascript": "embed()", rn.BOKEH_EXEC: {}}),
    ]
    rn._clean_outputs(nb)
    assert nb.cells[0].outputs == []  # the extension-loading cell shows nothing
    assert len(nb.cells[1].outputs) == 1
    body = rn._to_markdown(nb, _book(site))
    assert body.count("<iframe") == 1 and 'title="Interactive Bokeh figure"' in body
    page = (site / "static" / "outputs" / "cookbooks" / "t" / "1_0.html").read_text(encoding="utf-8")
    assert '<div id="p1" data-root-id="p2"></div>\n<script type="text/javascript">\nembed()\n</script>' in page
    assert re.search(r'<script src="https://cdn\.bokeh\.org/bokeh/release/bokeh-[\d.]+\.min\.js"', page)
    assert "panel.min.js" not in page


def test_an_extension_and_a_figure_in_one_cell_keep_the_figure():
    hv_init = [
        new_output("display_data", data={"text/html": '<script type="esms-options">{}</script>'}),
        new_output("display_data", data={"application/javascript": "x", "application/vnd.holoviews_load.v0+json": "x"}),
        new_output("display_data", data={"text/html": "<div id='c'></div>", rn.HOLOVIEWS_EXEC: {}}),  # Panel's comms
        new_output("display_data", data={"text/html": '<div class="logo-block"><img/></div>'}),
    ]
    figure = new_output("execute_result", data={"text/html": "<div id='f'></div>", rn.HOLOVIEWS_EXEC: {}})
    nb = _notebook(*hv_init, new_output("stream", name="stdout", text="loaded\n"), figure)
    nb.cells[1].outputs.insert(1, new_output("stream", name="stdout", text="hi\n"))
    rn._clean_outputs(nb)
    shown = [o.get("text") or o["data"]["text/html"] for o in nb.cells[1].outputs]
    assert shown == ["hi\n", "loaded\n", "<div id='f'></div>"]


@pytest.mark.parametrize("logo", [True, False])
def test_a_real_holoviews_extension_leaves_no_frame_and_its_figure_stays(logo):
    # without the logo, Panel's comm document (BrowserInfo + CommManager roots, no plot) is the extension's last output
    nb = new_notebook(
        cells=[new_code_cell(f"import holoviews as hv\nhv.extension('bokeh', logo={logo})\nhv.Curve([1, 3, 2])")]
    )
    rn._execute(nb, 120)
    rn._clean_outputs(nb)
    (figure,) = [o for o in nb.cells[0].outputs if o.get("data")]  # an empty display_data renders nothing
    assert figure.output_type == "execute_result" and rn.HOLOVIEWS_EXEC in figure.data
    assert "CommManager" not in figure.data["text/html"]


def test_holoviews_loads_bokehjs_and_panel(site):
    data = {"text/html": "<div id='a'></div><script>embed()</script>", rn.HOLOVIEWS_EXEC: {}, "text/plain": ":Curve"}
    body, pages = _framed(site, new_output("execute_result", data=data))
    assert 'title="Interactive HoloViews figure"' in body
    assert re.search(r'src="https://cdn\.holoviz\.org/panel/[\d.]+/dist/panel\.min\.js"', pages["1_0.html"])
    assert "cdn.bokeh.org/bokeh/release/bokeh-" in pages["1_0.html"]


def test_a_widget_becomes_a_page_with_its_state_and_the_widget_manager(site):
    state = {
        "version_major": 2,
        "version_minor": 0,
        "state": {"m1": {"model_name": "ReactModel", "state": {"_module": "reactable", "props": "</script>"}}},
    }
    view = {"model_id": "m1", "version_major": 2, "version_minor": 1}
    body, pages = _framed(
        site, new_output("execute_result", data={rn.WIDGET_VIEW: view, "text/plain": "W"}), widgets=state
    )
    assert 'title="Interactive widget"' in body
    page = pages["1_0.html"]
    assert "@jupyter-widgets/html-manager@1/dist/embed-amd.js" in page
    assert f'<script type="{rn.WIDGET_STATE}">' in page and f'<script type="{rn.WIDGET_VIEW}">' in page
    assert "<\\/script>" in page and '"props": "</script>"' not in page  # state cannot close its script element
    assert ".rt-table" in page  # reactable-py's styles


def test_a_widget_without_saved_state_falls_back_to_its_text(site):
    body, pages = _framed(
        site, new_output("execute_result", data={rn.WIDGET_VIEW: {"model_id": "m"}, "text/plain": "W"})
    )
    assert "```text\nW\n```" in body and pages == {}


def test_a_styles_only_html_output_is_dropped(site):  # reactable-py's embed_css()
    css = '<div><style>.rt {color: red}</style><link href="/reactable.css" rel="stylesheet"></div>'
    body, pages = _framed(site, new_output("display_data", data={"text/html": css}))
    assert "sdv-output" not in body and pages == {}


def test_moving_a_cell_leaves_no_stale_framed_page(site):
    book = _book(site)
    book.outputs_dir.mkdir(parents=True)
    (book.outputs_dir / "9_0.html").write_text("stale")
    _framed(site, new_output("display_data", data={"text/html": "<p>x</p>"}))
    assert sorted(p.name for p in book.outputs_dir.iterdir()) == ["1_0.html"]


def test_the_setup_cell_prints_polars_frames_as_markdown_tables_and_embeds_altair_as_svg():
    import altair as alt

    options = dict(alt.renderers.options)
    try:
        with pl.Config():
            exec(rn.SETUP, {})
            text = repr(pl.DataFrame({"team": ["KC"], "epa": [0.12]}))
        assert alt.renderers.options["embed_options"] == {"renderer": "svg", "actions": False}
    finally:  # the setup cell sets Altair's global options; leave them as the other tests expect
        alt.renderers.options.clear()
        alt.renderers.options.update(options)
    assert text.splitlines() == ["| team | epa  |", "|------|------|", "| KC   | 0.12 |"]


# --- links -------------------------------------------------------------------------------------------------------


def test_links_to_other_notebooks_point_at_their_pages(site):
    body = "[a](02_b.ipynb) [b](../01_a.ipynb#x) [c](../leagues/nfl.ipynb) [d](https://x.org/n.ipynb) [e](tables.ipynb)"
    assert rn._fix_links(body, _book(site, "cookbooks/t")) == (
        "[a](02_b.md) [b](../tutorials/01_a.md#x) [c](../tutorials/leagues/nfl.md) [d](https://x.org/n.ipynb) "
        "[e](tables.md)"
    )
    assert rn._fix_links("[a](02_b.ipynb) [b](cookbooks/t.ipynb)", _book(site, "01_a")) == (
        "[a](02_b.md) [b](../cookbooks/t.md)"
    )
    assert rn._fix_links("[a](../01_a.ipynb)", _book(site, "leagues/nfl")) == "[a](../01_a.md)"


# --- the gallery, --only and pruning ------------------------------------------------------------------------------


def _gallery_nb(site, key, title=None, **meta):
    fig = new_code_cell("plot()", metadata={"tags": ["gallery"]})
    if title:
        fig.metadata["sdvplot_gallery"] = {"title": title, "alt": f"{title}, described."}
    fig.outputs = [new_output("display_data", data={"image/png": _png(), "text/plain": "<Figure>"})]
    plain = new_code_cell("plot()")
    plain.outputs = [new_output("display_data", data={"image/png": _png(), "text/plain": "<Figure>"})]
    cells = [new_markdown_cell("# Title\n\n## 1. Scatter with `logos`"), plain, new_markdown_cell("## 2. Bars"), fig]
    return _write_nb(site, key, *cells, **meta)


def test_a_tagged_cell_gives_a_thumbnail_and_a_card_linked_to_its_heading(site):
    _gallery_nb(site, "leagues/nfl", title="EPA bars", label="NFL")
    assert rn.main(["--no-execute"]) == 0
    thumb = site / "static" / "img" / "gallery" / "tutorials" / "leagues" / "nfl_3.png"
    assert Image.open(thumb).size == (640, 320)
    sidecar = json.loads((site / "data" / "gallery" / "tutorials-leagues__nfl.json").read_text(encoding="utf-8"))
    assert sidecar == {
        "section": "tutorials/leagues",
        "stem": "nfl",
        "label": "NFL",
        "position": 1,
        "page": "tutorials/leagues/nfl.md",
        "items": [
            {
                "title": "EPA bars",
                "alt": "EPA bars, described.",
                "image": "/img/gallery/tutorials/leagues/nfl_3.png",
                "anchor": "2-bars",
            }
        ],
    }
    page = (site / "docs" / "gallery.md").read_text(encoding="utf-8")
    assert '## Tutorials by league\n\n<div class="sdv-gallery">\n\n' in page
    assert (
        '[<img src="/img/gallery/tutorials/leagues/nfl_3.png" alt="EPA bars, described." loading="lazy"/><br/>EPA bars'
        "<br/><small>NFL</small>]"
        "(tutorials/leagues/nfl.md#2-bars)"
    ) in page


def test_a_card_without_a_title_takes_its_heading(site):
    path = _gallery_nb(site, "recipes/r", label="R")
    nb = nbformat.read(path, as_version=4)
    items = rn._gallery_items(nb, _book(site, "recipes/r"), {"label": "R"})
    assert [(i["title"], i["alt"], i["anchor"]) for i in items] == [("Bars", "Bars", "2-bars")]


def test_heading_anchors_follow_docusaurus_ids():
    assert rn._slug("1. Scatter with `logo_url`") == "1-scatter-with-logo_url"
    assert rn._slug("[Plotly](https://plotly.com) & Altair!") == "plotly--altair"


def test_only_renders_one_notebook_by_its_relative_path_and_keeps_the_whole_gallery(site):
    _gallery_nb(site, "01_a", title="A", label="A")
    _gallery_nb(site, "leagues/nfl", title="N", label="NFL")
    assert rn.main(["--no-execute"]) == 0
    first = (site / "docs" / "tutorials" / "01_a.md").stat().st_mtime_ns
    (site / "docs" / "gallery.md").unlink()
    assert rn.main(["--no-execute", "--only", "leagues/nfl"]) == 0
    assert (site / "docs" / "tutorials" / "01_a.md").stat().st_mtime_ns == first  # not rendered again
    page = (site / "docs" / "gallery.md").read_text(encoding="utf-8")
    assert page.index("## Getting started") < page.index("## Tutorials by league")  # both cards, by section
    assert "(tutorials/01_a.md#2-bars)" in page and "(tutorials/leagues/nfl.md#2-bars)" in page
    assert rn.main(["--no-execute", "--only", "leagues\\nfl.ipynb"]) == 0  # a Windows path to the notebook works too
    assert rn.main(["--no-execute", "--only", "nfl"]) == 2
    (site / "docs" / "gallery.md").write_text("<<<<<<< a merge conflict")
    assert rn.main(["--gallery-only"]) == 0
    assert (site / "docs" / "gallery.md").read_text(encoding="utf-8") == page


def test_each_section_with_notebooks_gets_its_category(site):
    _write_nb(site, "01_a", new_markdown_cell("# A"))
    _write_nb(site, "cookbooks/c", new_markdown_cell("# C"))
    assert rn.main(["--no-execute"]) == 0
    category = json.loads((site / "docs" / "cookbooks" / "_category_.json").read_text(encoding="utf-8"))
    assert category["label"] == "Cookbooks" and category["position"] == 3
    assert category["link"]["type"] == "generated-index" and category["link"]["slug"] == "/category/cookbooks"
    assert not (site / "docs" / "tutorials" / "_category_.json").exists()  # the sidebar's Getting started
    assert not (site / "docs" / "recipes").exists()


def test_a_failed_notebook_keeps_its_page_and_fails_the_run(site):
    _write_nb(site, "01_a", new_markdown_cell("# A"))
    assert rn.main(["--no-execute"]) == 0
    page = (site / "docs" / "tutorials" / "01_a.md").read_text(encoding="utf-8")
    nb = nbformat.read(site / "nb" / "01_a.ipynb", as_version=4)
    del nb.metadata["sdvplot"]["label"]
    nbformat.write(nb, site / "nb" / "01_a.ipynb")
    assert rn.main(["--no-execute"]) == 1
    assert (site / "docs" / "tutorials" / "01_a.md").read_text(encoding="utf-8") == page


def test_a_deleted_notebook_loses_its_page_outputs_copy_and_cards(site):
    _gallery_nb(site, "leagues/nfl", title="N", label="NFL")
    _gallery_nb(site, "leagues/nba", title="B", label="NBA")
    assert rn.main(["--no-execute"]) == 0
    framed = site / "static" / "outputs" / "tutorials" / "leagues" / "nfl"
    framed.mkdir(parents=True)
    (site / "nb" / "leagues" / "nfl.ipynb").unlink()
    assert rn.main(["--no-execute"]) == 0
    assert not (site / "docs" / "tutorials" / "leagues" / "nfl.md").exists()
    assert not (site / "docs" / "tutorials" / "leagues" / "nfl_files").exists()
    assert not framed.exists() and not (site / "static" / "notebooks" / "leagues" / "nfl.ipynb").exists()
    assert not (site / "data" / "gallery" / "tutorials-leagues__nfl.json").exists()
    assert sorted(p.name for p in (site / "static" / "img" / "gallery" / "tutorials" / "leagues").iterdir()) == [
        "nba_3.png"
    ]
    page = (site / "docs" / "gallery.md").read_text(encoding="utf-8")
    assert "nfl" not in page and "(tutorials/leagues/nba.md#2-bars)" in page
    assert (site / "static" / "outputs" / "tutorials").is_dir()  # leagues/ is a section, not an orphan
    (site / "nb" / "leagues" / "nba.ipynb").unlink()
    assert rn.main(["--no-execute"]) == 0
    assert not (site / "docs" / "tutorials" / "leagues" / "_category_.json").exists()  # no empty sidebar category

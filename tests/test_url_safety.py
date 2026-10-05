"""Image URLs from third-party data (the logo manifest's archive_url, nflverse's headshot column) reach the HTML and
<script> blocks the web and table adapters write: a URL that is not a plain https URL is dropped where it enters."""

import io
import json
import time

import polars as pl
import pytest

import sdvplot
from sdvplot import _cache, _manifest, _web
from sdvplot._cache import SAFE_URL, safe_url
from sdvplot._errors import SdvplotWarning
from sdvplot._placement import Placement
from tests.conftest import FIXTURE, FakeResponse, FakeSession

EVIL_LOGO = "https://cdn/1111.png?</script><script>alert('logo')</script>\"><img src=x onerror=alert(1)>"
EVIL_SHOT = "https://static.www.nfl.com/x</script><script>alert('shot')</script>\"><img src=x onerror=alert(2)>"
GSIS = "00-0000001"  # nflverse row with the hostile headshot (and an ESPN id to fall back to)
NFL_SHOT = "https://static.www.nfl.com/image/private/f_auto,q_auto/league/abc"

GOOD = [
    "https://sdv.nyc3.cdn.digitaloceanspaces.com/assets/public/images/ab/ab12.png",
    "https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/3139477.png&w=96",
    NFL_SHOT,
    "https://cdn/1111.png",
    "https://127.0.0.1:8443/a%20b.svg#frag",
]
BAD = [
    "http://cdn/a.png",
    "javascript:alert(1)",
    "data:image/png;base64,AAAA",
    "//cdn/a.png",
    "https://",
    "https:///a.png",
    "https://cdn/a.png?<x>",
    'https://cdn/a.png?"',
    "https://cdn/a.png?'",
    "https://cdn/a b.png",
    "https://cdn/a\\b.png",
    "https://cdn/a.png\n",
    "https://cdn/a\x00.png",
    "https://cdn/é.png",
    EVIL_LOGO,
    EVIL_SHOT,
]


def test_safe_url_takes_plain_https_urls_only_and_polars_reads_the_pattern_the_same_way():
    assert [safe_url(u) for u in GOOD] == [True] * len(GOOD)
    assert [safe_url(u) for u in BAD] == [False] * len(BAD)
    assert safe_url(None) is False
    urls = pl.Series(GOOD + BAD)  # the manifest is filtered by polars (Rust regex), headshots by re
    assert urls.str.contains(f"^(?:{SAFE_URL})$").to_list() == [safe_url(u) for u in urls]


@pytest.fixture
def hostile(cache, monkeypatch):
    """The fixture manifest with LV's default logo pointing at EVIL_LOGO, and an nflverse player table (cached, fresh)
    whose GSIS row has EVIL_SHOT as its headshot."""
    m = pl.read_csv(FIXTURE, infer_schema_length=0)
    m = m.with_columns(pl.col("archive_url").replace("https://cdn/1111.png", EVIL_LOGO))
    buf = io.BytesIO()
    m.write_csv(buf)
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, buf.getvalue())))
    _manifest._read.cache_clear()
    players = cache / "nflverse" / "players.parquet"
    players.parent.mkdir(parents=True)
    pl.DataFrame(
        {"gsis_id": [GSIS, "00-0000002"], "espn_id": ["3139477", None], "headshot": [EVIL_SHOT, NFL_SHOT]},
        schema={"gsis_id": pl.String, "espn_id": pl.String, "headshot": pl.String},
    ).write_parquet(players)
    _cache._meta_path(players).write_text(json.dumps({"fetched_at": time.time()}))
    return cache


def test_a_manifest_row_whose_archive_url_is_not_plain_https_is_dropped_with_one_warning(hostile):
    with pytest.warns(SdvplotWarning, match="dropped 1 logo manifest row") as caught:
        m = _manifest.load_manifest()
    assert len(caught) == 1
    assert EVIL_LOGO not in m["archive_url"].to_list()
    assert m.height == pl.read_csv(FIXTURE).height - 1
    assert "https://cdn/6666.png" in m["archive_url"].to_list()  # the other rows are kept


def test_an_nflverse_headshot_that_is_not_plain_https_is_treated_as_missing(hostile):
    with pytest.warns(SdvplotWarning, match="ignored 1 nflverse headshot") as caught:
        url = sdvplot.headshot_url(GSIS, "nfl", id_system="gsis")
    assert len(caught) == 1
    assert url == sdvplot.headshot_url("3139477", "nfl")  # the ESPN headshot of the player's ESPN id
    good = sdvplot.headshot_url("00-0000002", "nfl", id_system="gsis")  # a plain https headshot is kept
    assert good == "https://static.www.nfl.com/image/private/t_headshot_desktop/f_auto/league/abc.png"


def test_image_src_percent_encodes_what_a_url_may_not_hold():
    p = Placement("13", 0, 0, EVIL_LOGO, 1.0, None)
    src = _web.image_src(p)
    assert not set("<>\"' ") & set(src)
    assert src.startswith("https://cdn/1111.png?%3C/script%3E%3Cscript%3Ealert(%27logo%27)")
    for url in GOOD:  # a plain https URL is passed on unchanged
        assert _web.image_src(Placement("13", 0, 0, url, 1.0, None)) == url


TEAMS, PLAYERS = ["LV", "LAR"], [GSIS, "00-0000002"]


def _great_tables():
    from great_tables import GT

    from sdvplot.great_tables import gt_sdv_headshots, gt_sdv_logos

    logos = gt_sdv_logos(GT(pl.DataFrame({"team": TEAMS})), columns="team", league="nfl").as_raw_html()
    shots = gt_sdv_headshots(GT(pl.DataFrame({"p": PLAYERS})), columns="p", league="nfl", id_system="gsis")
    return logos + shots.as_raw_html()


def _reactable():
    from reactable.models import CellInfo

    from sdvplot.reactable import reactable_sdv_headshots, reactable_sdv_logos

    logos = reactable_sdv_logos(league="nfl", id="team")
    shots = reactable_sdv_headshots(league="nfl", id="p", id_system="gsis")
    return "".join(
        [logos.cell(CellInfo(t, 0, "team")) for t in TEAMS] + [shots.cell(CellInfo(p, 0, "p")) for p in PLAYERS]
    )


def _plotly():
    import plotly.graph_objects as go

    import sdvplot.plotly as sp

    fig = sp.add_logos(go.Figure(go.Scatter(x=[1, 2], y=[1, 2])), [1, 2], [1, 2], TEAMS, league="nfl")
    return sp.add_headshots(fig, [1, 2], [2, 1], PLAYERS, league="nfl", id_system="gsis").to_html()


def _altair():
    import altair as alt

    import sdvplot.altair as sa

    base = alt.Chart(pl.DataFrame({"x": [1, 2], "y": [1, 2]})).mark_point().encode(x="x:Q", y="y:Q")
    logos = sa.add_logos(base, [1, 2], [1, 2], TEAMS, league="nfl").to_html()
    return logos + sa.add_headshots(base, [1, 2], [2, 1], PLAYERS, league="nfl", id_system="gsis").to_html()


def _bokeh_html(fig):
    from bokeh.embed import file_html
    from bokeh.resources import CDN

    return file_html(fig, CDN)


def _bokeh():
    from bokeh.plotting import figure

    import sdvplot.bokeh as sb

    p = figure()
    p.scatter([1, 2], [1, 2])
    sb.add_logos(p, [1, 2], [1, 2], TEAMS, league="nfl")
    return _bokeh_html(sb.add_headshots(p, [1, 2], [2, 1], PLAYERS, league="nfl", id_system="gsis"))


def _holoviews():
    import holoviews as hv

    import sdvplot.holoviews as sh

    hv.extension("bokeh")
    el = sh.add_logos(hv.Scatter([(1, 1), (2, 2)]), [1, 2], [1, 2], TEAMS, league="nfl")
    el = sh.add_headshots(el, [1, 2], [2, 1], PLAYERS, league="nfl", id_system="gsis")
    return _bokeh_html(hv.render(el, backend="bokeh"))


def _folium():
    import folium

    import sdvplot.folium as sf

    m = sf.add_logos(folium.Map(location=[39, -95], zoom_start=4), [-94.5, -118], [39.0, 34], TEAMS, league="nfl")
    m = sf.add_headshots(m, [-90, -100], [35, 40], PLAYERS, league="nfl", id_system="gsis")
    return m.get_root().render()


def _pygal():
    import pygal

    import sdvplot.pygal as sg

    chart = pygal.XY()
    chart.add("a", [(1, 1), (2, 2)])
    sg.add_logos(chart, [1, 2], [1, 2], TEAMS, league="nfl")
    return sg.add_headshots(chart, [1, 2], [2, 1], PLAYERS, league="nfl", id_system="gsis").render().decode()


ADAPTERS = {
    "great_tables": ("great_tables", _great_tables),
    "reactable": ("reactable", _reactable),
    "plotly": ("plotly", _plotly),
    "altair": ("altair", _altair),
    "bokeh": ("bokeh", _bokeh),
    "holoviews": ("holoviews", _holoviews),
    "folium": ("folium", _folium),
    "pygal": ("pygal", _pygal),
}


@pytest.mark.filterwarnings("ignore::sdvplot._errors.SdvplotWarning")  # the drop warnings and the skipped LV logo
@pytest.mark.parametrize("adapter", list(ADAPTERS))
def test_a_hostile_manifest_or_headshot_url_never_reaches_adapter_output_unescaped(hostile, adapter):
    module, render = ADAPTERS[adapter]
    pytest.importorskip(module)
    out = render()
    # a raw "<" before either payload would close the <script> block or the attribute the URL sits in; an escaped
    # copy (&lt;, <) is inert, so only the raw payloads are looked for
    for payload in ("<script>alert(", "<img src=x"):
        assert payload not in out, f"{adapter} wrote a hostile URL into its output unescaped"

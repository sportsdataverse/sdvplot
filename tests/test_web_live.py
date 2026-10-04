"""Live: the web adapters' inputs from the real world (network): the headshot aspect constant and archive URLs."""

import os

import pytest
import requests

import sdvplot
from sdvplot import _web
from sdvplot._images import load_url_image

pytestmark = [
    pytest.mark.real_index,
    pytest.mark.skipif(os.environ.get("SDVPLOT_LIVE_TESTS") != "1", reason="network: set SDVPLOT_LIVE_TESTS=1"),
]


@pytest.mark.parametrize(("player", "league"), [("3139477", "nfl"), ("1966", "nba")])
def test_the_headshot_aspect_matches_real_espn_headshots(player, league, tmp_path, monkeypatch):
    monkeypatch.setenv("SDVPLOT_CACHE_DIR", str(tmp_path))
    img = load_url_image(sdvplot.headshot_url(player, league))
    assert img.width / img.height == pytest.approx(_web.HEADSHOT_ASPECT, rel=0.01)


@pytest.mark.parametrize(("league", "team"), [("nfl", "KC"), ("nba", "LAL"), ("cfb", "Alabama")])
def test_archive_urls_serve_images_a_browser_can_load(league, team, tmp_path, monkeypatch):
    monkeypatch.setenv("SDVPLOT_CACHE_DIR", str(tmp_path))
    r = requests.get(sdvplot.logo_url(team, league), timeout=30)
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("image/")

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


# the league-id CDNs (sdvplotR's league_headshot_url). cdn.nba.com and cdn.wnba.com answer 403 to datacenter IPs: on
# CI that is the block, not a broken template, so it skips; from a residential connection it must be a 200 image.
@pytest.mark.parametrize(
    ("league", "player"), [("nba", "2544"), ("wnba", "1628932"), ("mlb", "660271"), ("nhl", "8478402")]
)
def test_league_id_headshot_cdns_serve_images(league, player):
    url = sdvplot.headshot_url(player, league, id_system="league")
    r = requests.get(url, timeout=30)
    if r.status_code == 403:
        pytest.skip(f"{url}: 403 (a datacenter or cloud IP; the CDN blocks them)")
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("image/")

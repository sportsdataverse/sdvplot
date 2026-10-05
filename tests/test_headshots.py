import io
import os

import numpy as np
import polars as pl
import pytest

from sdvplot import _cache, _headshots
from sdvplot._errors import SdvplotWarning
from tests.conftest import FakeResponse, FakeSession


@pytest.mark.parametrize(
    "player_id",
    [3139477, "3139477", 3139477.0, " 3139477 ", np.int64(3139477)],
)
def test_espn_ids_accept_numeric_variants(player_id):
    """Valid numeric id variants all produce the same URL."""
    result = _headshots.headshot_url(player_id, "nfl")
    assert result == "https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/3139477.png"


@pytest.mark.parametrize("player_id", [None, float("nan"), ""])
def test_espn_ids_return_none_for_null_and_empty(player_id):
    """Null and empty strings return None."""
    result = _headshots.headshot_url(player_id, "nfl")
    assert result is None


# "\u0663\u0661\u0663\u0669\u0664\u0667\u0667": Arabic-Indic digits, which str.isdigit() accepts; an ESPN id is ASCII
@pytest.mark.parametrize("player_id", ["abc", "1.5", 1.5, True, "\u0663\u0661\u0663\u0669\u0664\u0667\u0667"])
def test_espn_ids_return_none_for_invalid_shapes(player_id):
    """Non-numeric ids (letters, decimals, bools, non-ASCII digits) return None, matching sdvplotR."""
    result = _headshots.headshot_url(player_id, "nfl")
    assert result is None


def test_espn_ids_build_the_combiner_url():
    assert (
        _headshots.headshot_url(3139477, "nfl")
        == "https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/3139477.png"
    )
    assert (
        _headshots.headshot_url("4433134", "mbb")
        == "https://a.espncdn.com/combiner/i?img=/i/headshots/mens-college-basketball/players/full/4433134.png"
    )


def test_unsupported_league_is_a_clear_error():
    with pytest.raises(ValueError, match="no ESPN headshots for league 'ohl'"):
        _headshots.headshot_url(1, "ohl")


@pytest.mark.parametrize(
    ("league", "id_system", "match"),
    [("ohl", "espn", "no ESPN headshots for league 'ohl'"), ("nfl", "bogus", "id_system must be")],
)
def test_a_null_id_still_checks_the_league_and_id_system(league, id_system, match):
    with pytest.raises(ValueError, match=match):
        _headshots.headshot_url(None, league, id_system=id_system)


def test_gsis_ids_prefer_nfl_headshot_transformed_or_fall_back_to_espn(cache, monkeypatch):
    buf = io.BytesIO()
    pl.DataFrame(
        {
            "gsis_id": ["00-0033873", "00-0099999", "00-0000001"],
            "espn_id": ["3139477", "4455678", None],
            "headshot": [
                "https://static.www.nfl.com/image/private/f_auto,q_auto/league/abc123",
                None,
                None,
            ],
        }
    ).write_parquet(buf)
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, buf.getvalue())))
    _headshots._players.cache_clear()

    # (a) Prefer transformed NFL.com URL when headshot is present
    result1 = _headshots.headshot_url("00-0033873", "nfl", id_system="gsis")
    assert result1 == "https://static.www.nfl.com/image/private/t_headshot_desktop/f_auto/league/abc123.png"

    # (b) Fall back to ESPN combiner URL when no headshot but espn_id exists
    result2 = _headshots.headshot_url("00-0099999", "nfl", id_system="gsis")
    assert result2 == "https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/4455678.png"

    # (c) Return None when neither headshot nor espn_id
    result3 = _headshots.headshot_url("00-0000001", "nfl", id_system="gsis")
    assert result3 is None

    # (d) Return None for unknown gsis id
    result4 = _headshots.headshot_url("00-0000000", "nfl", id_system="gsis")
    assert result4 is None


def test_a_players_table_missing_a_column_keeps_the_cached_copy(cache, monkeypatch):
    def parquet(**cols):
        buf = io.BytesIO()
        pl.DataFrame(cols).write_parquet(buf)
        return buf.getvalue()

    good = parquet(gsis_id=["00-0033873"], espn_id=["3139477"], headshot=[None])
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, good)))
    _headshots._players.cache_clear()
    espn = "https://a.espncdn.com/combiner/i?img=/i/headshots/nfl/players/full/3139477.png"
    assert _headshots.headshot_url("00-0033873", "nfl", id_system="gsis") == espn
    monkeypatch.setenv("SDVPLOT_CACHE_TTL", "0")
    bad = parquet(gsis_id=["00-0033873"], espn_id=["3139477"])  # nflverse dropped the headshot column
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, bad)))
    with pytest.warns(SdvplotWarning, match="using the cached copy") as w:
        assert _headshots.headshot_url("00-0033873", "nfl", id_system="gsis") == espn
    assert len(w) == 1


def test_a_refreshed_or_cleared_players_table_is_not_kept_in_memory(cache, monkeypatch):  # re-audit, original 5
    buf = io.BytesIO()
    pl.DataFrame({"gsis_id": ["00-0033873"], "espn_id": ["3139477"], "headshot": [None]}).write_parquet(buf)
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, buf.getvalue())))
    _headshots._players.cache_clear()
    assert _headshots.headshot_url("00-0033873", "nfl", id_system="gsis")
    path = _cache.cache_path("nflverse/players.parquet")
    later = path.stat().st_mtime + 60
    os.utime(path, (later, later))  # a refreshed file: its mtime is part of the key
    assert _headshots.headshot_url("00-0033873", "nfl", id_system="gsis")
    assert _headshots._players.cache_info().currsize == 1  # the new table only
    _cache.clear_cache()
    assert _headshots._players.cache_info().currsize == 0

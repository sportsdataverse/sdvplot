"""The shared deck.gl / pydeck fixture (tests/fixtures/deckgl_shared.json): sdvplot-js writes it from its ./deckgl
adapter (tools/oracle/deckgl.ts) and commits the same bytes as fixtures/deckgl/shared.json, so sdvplot.pydeck building
every layer exactly as it is written here is what proves the two languages build the same props from the same rows."""

import hashlib
import json
import re
import warnings
from pathlib import Path

import polars as pl
import pytest

from sdvplot import _cache, _manifest
from sdvplot._team_palette import team_palette
from tests.conftest import FakeResponse, FakeSession

PATH = Path(__file__).parent / "fixtures" / "deckgl_shared.json"
BYTES = PATH.read_bytes()
SHA256 = (
    "acb197164795e8663ccd8e139ca2e847a8f80f5549c0b30aefe18b71ca89ec08"  # pinned in sdvplot-js's deckgl-shared.test.ts
)
FIXTURE = json.loads(BYTES)


@pytest.fixture
def sdeck():
    """sdvplot.pydeck, which needs pydeck at import (the [pydeck] extra). The byte identity and palette tests need
    neither, so they run without it."""
    pytest.importorskip("pydeck")
    import sdvplot.pydeck

    return sdvplot.pydeck


def _snake(key: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()


def _deckgl(props: dict) -> dict:
    """pydeck keyword arguments as deck.gl gets them: keys camelCased, a quoted constant string unquoted."""

    def camel(key: str) -> str:
        head, *rest = key.split("_")
        return head + "".join(w.title() for w in rest)

    def value(v):
        return v[1:-1] if isinstance(v, str) and len(v) > 1 and v[0] == v[-1] == "'" else v

    return {camel(k): value(v) for k, v in props.items()}


@pytest.fixture
def shared_manifest(cache, monkeypatch):
    """The cache with a manifest of the fixture's mark rows: the real archive rows of the logos it draws."""
    body = pl.DataFrame(FIXTURE["inputs"]["marks"]).write_csv().encode()
    monkeypatch.setattr(_cache, "SESSION", FakeSession(FakeResponse(200, body, {"ETag": '"shared"'})))
    _manifest._read.cache_clear()
    _manifest.load_manifest()


def test_the_fixture_is_the_file_sdvplot_js_commits_byte_for_byte():
    assert hashlib.sha256(BYTES).hexdigest() == SHA256
    assert FIXTURE["warnings"] == []


@pytest.mark.real_index
@pytest.mark.parametrize("case", FIXTURE["layers"], ids=lambda c: c["name"])
def test_each_layer_is_rebuilt_exactly_from_the_fixtures_rows_and_options(sdeck, shared_manifest, case):
    rows = FIXTURE["inputs"][case["input"]]["rows"]
    options = {_snake(k): v for k, v in case["options"].items()}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        build = sdeck.logo_icon_layer if case["layer"] == "IconLayer" else sdeck.pass_arc_layer
        props = build(rows, **options)
    assert props.pop("type") == case["layer"]
    assert props.pop("data") == case["data"]
    # pydeck sends each keyword to deck.gl camelCased; an accessor (an unquoted string) names the row field it reads
    assert _deckgl(props) == case["props"]


@pytest.mark.parametrize("case", FIXTURE["surfaces"], ids=lambda c: c["name"])
def test_each_surface_has_the_fixtures_props_fill_colors_and_extent(sdeck, case):
    pytest.importorskip("sportypy")
    kwargs = {"pitch_updates": case["pitch"]} if case.get("pitch") else {}
    props = sdeck.surface_layer(case["sport"], case["league"], **kwargs)
    assert props.pop("type") == "PolygonLayer"
    data = props.pop("data")
    assert _deckgl(props) == case["props"]
    assert sorted({tuple(d["fillColor"]) for d in data}) == sorted(tuple(c) for c in case["fills"])

    def extent(k):
        values = [p[k] for d in data for p in d["polygon"]]
        return [round(min(values), 4), round(max(values), 4)]

    assert extent(0) == case["extent_x"]
    if case["extent_y"] is not None:
        assert extent(1) == case["extent_y"]


@pytest.mark.parametrize("case", FIXTURE["palettes"], ids=lambda c: f"{c['league']}-{c['background']}")
def test_the_ported_team_palette_gives_sdvplot_js_colors_on_every_team(case):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        got = team_palette(case["colors"], case["alts"], case["background"], case["labels"])
    assert got == case["expected"]

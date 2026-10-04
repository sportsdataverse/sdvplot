import pytest

folium = pytest.importorskip("folium")

import sdvplot  # noqa: E402
import sdvplot.folium as sfolium  # noqa: E402
from sdvplot.testing import check_adapter_contract  # noqa: E402


def _map(**kw):
    return folium.Map(location=[0, 0], zoom_start=2, **kw)


def _markers(m):
    (group,) = [c for c in m._children.values() if isinstance(c, folium.FeatureGroup)]
    return [c for c in group._children.values() if isinstance(c, folium.Marker)]


def test_a_map_passes_the_contract(mark_images, headshot_images):
    check_adapter_contract(sfolium, make_target=_map)


def test_x_is_longitude_and_y_latitude(mark_images):
    m = _map()
    assert sdvplot.add_logos(m, [-94.5], [39.0], ["LV"], league="nfl") is m
    (marker,) = _markers(m)
    assert marker.location == [39.0, -94.5]


def test_icons_are_sized_from_a_pixel_map_height(mark_images):
    m = _map(height=600)
    sdvplot.add_logos(m, [10], [-3], ["LV"], league="nfl", height=0.1)
    sdvplot.add_wordmarks(m, [20], [-7], ["LV"], league="nfl", height=0.1)
    logo, wordmark = (marker.icon.options for marker in _markers(m))
    assert (logo["icon_size"], logo["icon_anchor"]) == ((60, 60), (30, 30))
    assert (wordmark["icon_size"], wordmark["icon_anchor"]) == ((150, 60), (75, 30))


def test_a_map_without_a_pixel_height_uses_the_reference_height(mark_images):
    m = _map()  # height "100%"
    sdvplot.add_logos(m, [10], [-3], ["LV"], league="nfl", height=0.1)
    assert _markers(m)[0].icon.options["icon_size"] == (50, 50)  # 0.1 of FOLIUM_REFERENCE_HEIGHT


def test_markers_share_one_feature_group_and_show_the_team_name(mark_images):
    m = _map()
    sdvplot.add_logos(m, [10], [-3], ["LV"], league="nfl")
    sdvplot.add_logos(m, [20], [-7], ["LAR"], league="nfl")
    groups = [c for c in m._children.values() if isinstance(c, folium.FeatureGroup)]
    assert [g.layer_name for g in groups] == ["sdvplot logos"]
    tips = [c.text for marker in _markers(m) for c in marker._children.values() if isinstance(c, folium.Tooltip)]
    assert tips == ["Las Vegas Raiders", "Los Angeles Rams"]


def test_alpha_and_embed_reach_the_html(mark_images):
    m = _map()
    sdvplot.add_logos(m, [10], [-3], ["LV"], league="nfl", alpha=0.5, embed=True)
    html = m.get_root().render()
    assert '"opacity": 0.5' in html and "data:image/png;base64," in html


def test_empty_input_adds_no_feature_group(mark_images):
    m = _map()
    sdvplot.add_logos(m, [], [], [], league="nfl")
    assert not [c for c in m._children.values() if isinstance(c, folium.FeatureGroup)]


def test_axis_logos_name_the_workaround(mark_images):
    with pytest.raises(TypeError, match="add_logos"):
        sdvplot.axis_logos(_map(), "x", league="nfl")


def test_a_folium_object_that_is_not_a_map_is_a_type_error(mark_images):
    with pytest.raises(TypeError, match="draws on a folium.Map"):
        sdvplot.add_logos(folium.FeatureGroup(), [10], [-3], ["LV"], league="nfl")

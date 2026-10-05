import pytest

from sdvplot._contrast import contrast, hex6, luminance, mix, on_color


@pytest.mark.parametrize(
    ("given", "want"),
    [
        ("#ABC", "#aabbcc"),
        ("abc", "#aabbcc"),
        ("#E31837", "#e31837"),
        ("#e31837ff", "#e31837"),
        ("#F00F", "#ff0000"),  # #rgba, opaque
        (" #000000 ", "#000000"),
    ],
)
def test_hex6_normalizes(given, want):
    assert hex6(given) == want


@pytest.mark.parametrize("bad", ["", "#12", "#12345", "#gggggg", "red", "rebeccapurple", (1.0, 0.0, 0.0, 0.5)])
def test_hex6_rejects_non_hex(bad):
    # named colors and rgba tuples were never hex6 input: the tables measure hex colors (CSS-only arguments take names)
    with pytest.raises(ValueError, match="not a hex color"):
        hex6(bad)


@pytest.mark.parametrize(
    ("translucent", "solid"), [("#E3183780", "#e31837"), ("#e3183700", "#e31837"), ("#F008", "#ff0000")]
)
def test_hex6_refuses_a_translucent_color_rather_than_drawing_it_solid(translucent, solid):
    # its callers draw and measure colors opaque (contrast, ramps, theme accents): dropping the alpha changed the color
    with pytest.raises(ValueError, match="has transparency"):
        hex6(translucent)
    assert hex6(translucent, drop_alpha=True) == solid  # for a caller that sets its own alpha


def test_luminance_and_contrast_match_wcag():
    assert luminance("#ffffff") == pytest.approx(1.0)
    assert luminance("#000000") == pytest.approx(0.0)
    assert contrast("#000000", "#ffffff") == pytest.approx(21.0)
    assert contrast("#777777", "#777777") == pytest.approx(1.0)
    assert contrast("#000000", "#ffffff") == contrast("#ffffff", "#000000")


@pytest.mark.parametrize(
    ("bg", "ink"), [("#ffffff", "#000000"), ("#ffc20e", "#000000"), ("#000000", "#ffffff"), ("#003594", "#ffffff")]
)
def test_on_color_picks_the_more_readable_ink(bg, ink):
    assert on_color(bg) == ink


def test_mix_interpolates_in_srgb():
    assert mix("#000000", "#ffffff", 0) == "#000000"
    assert mix("#000000", "#ffffff", 1) == "#ffffff"
    assert mix("#000000", "#ffffff", 0.5) == "#808080"
    with pytest.raises(ValueError):
        mix("#000000", "#ffffff", 1.5)

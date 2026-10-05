"""The deprecation helper: one warning category, naming the replacement and the removal release, at the caller's line."""

import inspect
import warnings

import pytest

import sdvplot
from sdvplot._deprecate import deprecate, deprecated_alias


def test_the_warning_is_a_future_warning_and_an_sdvplot_warning():
    assert issubclass(sdvplot.SdvplotDeprecationWarning, FutureWarning)  # shown by default, unlike DeprecationWarning
    assert issubclass(sdvplot.SdvplotDeprecationWarning, sdvplot.SdvplotWarning)


def test_deprecate_names_the_replacement_and_the_removal_release_at_the_callers_line():
    with pytest.warns(sdvplot.SdvplotDeprecationWarning) as rec:
        deprecate("sdvplot.old_name()", replacement="sdvplot.new_name()", removal="0.3.0")
    assert len(rec) == 1
    assert str(rec[0].message) == (
        "sdvplot.old_name() is deprecated and will be removed in sdvplot 0.3.0; use sdvplot.new_name() instead"
    )
    assert rec[0].filename == __file__


@deprecated_alias(removal="0.3.0", which="kind")
def colors(league, *, kind="primary"):
    """Colors of one kind."""
    return league, kind


def test_a_renamed_keyword_still_works_and_warns_once():
    with pytest.warns(
        sdvplot.SdvplotDeprecationWarning, match=r"colors\(which=...\) is deprecated .* 0\.3\.0; use kind="
    ):
        assert colors("nfl", which="secondary") == ("nfl", "secondary")


def test_the_new_keyword_does_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert colors("nfl", kind="secondary") == ("nfl", "secondary")
        assert colors("nfl") == ("nfl", "primary")


def test_both_names_at_once_is_an_error():
    with pytest.raises(TypeError, match=r"colors\(\) got both which= \(deprecated\) and kind=; pass only kind="):
        colors("nfl", which="secondary", kind="primary")


def test_the_alias_keeps_the_functions_name_doc_and_signature():
    assert colors.__name__ == "colors" and colors.__doc__ == "Colors of one kind."
    assert list(inspect.signature(colors).parameters) == ["league", "kind"]


def test_the_alias_warning_names_the_callers_line():
    with pytest.warns(sdvplot.SdvplotDeprecationWarning) as rec:
        colors("nfl", which="secondary")
    assert [w.filename for w in rec] == [__file__]

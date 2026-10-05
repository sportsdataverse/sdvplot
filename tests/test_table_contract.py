"""The table contract can fail: each mutant adapter below breaks one rule, and the harness must name it."""

import warnings

import pytest

pytest.importorskip("great_tables")
from great_tables import GT, loc  # noqa: E402

import sdvplot.great_tables as sgt  # noqa: E402
from sdvplot._errors import SdvplotWarning  # noqa: E402
from sdvplot.testing import check_table_adapter_contract  # noqa: E402

real_logos = sgt.add_logos


def _check():
    check_table_adapter_contract(sgt, GT)


def test_the_great_tables_adapter_passes_the_table_contract(manifest):
    _check()


def test_rule_t0_catches_a_table_routed_elsewhere(manifest):
    with pytest.raises(AssertionError, match=r"rule T0 \(registration\)"):
        check_table_adapter_contract(sgt, lambda frame: object())


def test_rule_t1_catches_swapped_rows(manifest, monkeypatch):
    def swapped(gt, columns, **kw):
        out = real_logos(gt, columns, **kw)
        return out.text_transform(loc.body(columns), lambda s: s.replace('"13"', '"tmp"').replace('"14"', '"13"'))

    monkeypatch.setattr(sgt, "add_logos", swapped)
    with pytest.raises(AssertionError, match=r"rule T1 \(resolution\)"):
        _check()


def test_rule_t2_catches_an_adapter_that_warns_at_render_time(manifest, monkeypatch):
    def late(gt, columns, **kw):
        def fn(text):
            if text == "XXX":
                warnings.warn("unknown XXX", SdvplotWarning, stacklevel=2)
            return text

        return real_logos(gt, columns, **kw).text_transform(loc.body(columns), fn)

    monkeypatch.setattr(sgt, "add_logos", late)
    with pytest.raises(AssertionError, match=r"rule T2 .*rendering must not warn"):
        _check()


def test_rule_t2_catches_an_adapter_that_blanks_unknown_values(manifest, monkeypatch):
    def blank(gt, columns, **kw):
        return real_logos(gt, columns, **kw).text_transform(loc.body(columns), lambda s: "" if s == "XXX" else s)

    monkeypatch.setattr(sgt, "add_logos", blank)
    with pytest.raises(AssertionError, match=r"rule T2 .*must stay as text"):
        _check()


def test_rule_t1_catches_an_adapter_that_warns_when_nothing_is_skipped(manifest, monkeypatch):
    def chatty(gt, columns, **kw):
        warnings.warn("adding logos", SdvplotWarning, stacklevel=2)
        return real_logos(gt, columns, **kw)

    monkeypatch.setattr(sgt, "add_logos", chatty)
    with pytest.raises(AssertionError, match=r"rule T1 \(resolution\): known values must not warn"):
        _check()


def test_rule_t2_catches_an_adapter_that_warns_once_per_unknown_value(manifest, monkeypatch):
    def per_value(gt, columns, **kw):
        for value in gt._tbl_data[columns]:
            if value.startswith("XXX"):
                warnings.warn(f"unknown {value}", SdvplotWarning, stacklevel=2)  # one per value, not one per call
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SdvplotWarning)
            return real_logos(gt, columns, **kw)

    monkeypatch.setattr(sgt, "add_logos", per_value)
    with pytest.raises(AssertionError, match=r"rule T2 .*all-unknown input must warn exactly once when called"):
        _check()


def test_rule_t4_catches_an_adapter_that_ignores_height(manifest, monkeypatch):
    monkeypatch.setattr(sgt, "add_logos", lambda gt, columns, *, height=30, **kw: real_logos(gt, columns, **kw))
    with pytest.raises(AssertionError, match=r"rule T4 \(height in pixels\)"):
        _check()


def test_rule_t4_catches_an_adapter_that_takes_a_fraction_of_a_pixel(manifest, monkeypatch):
    # a plot's height unit (a fraction) on a table drew a 0.1 px image; the contract makes the adapter refuse it
    def fractional(gt, columns, *, height=30, **kw):
        return real_logos(gt, columns, height=30 if isinstance(height, float) and 0 < height < 1 else height, **kw)

    monkeypatch.setattr(sgt, "add_logos", fractional)
    with pytest.raises(AssertionError, match=r"rule T4 \(height in pixels\).*height=0\.5"):
        _check()


def test_rule_t5_catches_wordmarks_drawn_as_logos(manifest, monkeypatch):
    monkeypatch.setattr(sgt, "add_wordmarks", real_logos)
    with pytest.raises(AssertionError, match=r"rule T5"):
        _check()

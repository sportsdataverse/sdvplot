import pytest

pytest.importorskip("great_tables")
import sdvplot.great_tables as sgt  # noqa: E402

WAVE_C2 = [
    "gt_legend_continuous",
    "gt_legend_discrete",
    "gt_marginalia",
    "gt_outliers",
    "gt_percentile_bar",
    "gt_row_accent",
    "gt_scale_note",
    "gt_set_font",
    "gt_significance",
    "gt_snake",
    "gt_snake_align",
    "gt_social_tag",
    "gt_spotlight",
    "gt_tiers",
    "gt_title_header",
    "gt_watermark",
    "gt_wrap_labels",
]


def test_wave_c2_names_are_exported():
    assert set(WAVE_C2) <= set(sgt.__all__)
    assert all(callable(getattr(sgt, name)) for name in WAVE_C2)
    assert all(getattr(sgt, name).__module__ == "sdvplot.great_tables._layout" for name in WAVE_C2)

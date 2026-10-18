"""Helpers for the great_tables cell tests: build the same data in pandas or polars, read rendered body cells."""

import re

import pandas as pd
import polars as pl
from great_tables._data_color.palettes import GradientPalette

TD = re.compile(r'<td (?:style="([^"]*)" )?class="gt_row[^"]*"[^>]*>(.*?)</td>', re.S)
STUB = re.compile(r'<th (?:style="([^"]*)" )?class="gt_row[^"]*gt_stub[^"]*"[^>]*>(.*?)</th>', re.S)

# great_tables >= 1.1 ties body cells to their headings for screen readers: headers= on each <td>, scope="row" and an id
# on each stub <th>, scope="colgroup" and an id on each row-group heading
A11Y = re.compile(r' (?:headers="[^"]*"|scope="(?:row|colgroup)" id="[^"]*")')


def raw_html(gt, **kwargs):
    """``gt.as_raw_html(**kwargs)`` without the ``A11Y`` attributes, so a test can match cell markup on any version."""
    return A11Y.sub("", gt.as_raw_html(**kwargs))


def ramp(a, b, t):
    """The color ``t`` of the way from ``a`` to ``b`` on great_tables' ``data_color`` gradient, which sdvplot's ramps
    follow: sRGB before great_tables 1.1, CIELAB (R's ``scales::col_numeric``) from 1.1. ``test_gt_cells_colors`` pins
    both against literal colors."""
    return GradientPalette([a, b])([t])[0]


def frame(lib, data):
    """``data`` as a polars frame, or a pandas frame with a non-default index (positions must not use labels)."""
    if lib == "pandas":
        n = len(next(iter(data.values())))
        return pd.DataFrame(data, index=[10 * (i + 1) for i in range(n)])
    return pl.DataFrame(data, strict=False)


def body_rows(gt, pattern=TD):
    """One list per rendered body row of ``(style, text)`` for each body cell (``STUB`` reads the stub instead)."""
    html = raw_html(gt)
    body = html[html.index("<tbody") : html.index("</tbody>")]
    rows = [pattern.findall(tr) for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S)]
    return [r for r in rows if r]

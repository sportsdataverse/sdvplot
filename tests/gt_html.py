"""Helpers for the great_tables cell tests: build the same data in pandas or polars, read rendered body cells."""

import re

import pandas as pd
import polars as pl

TD = re.compile(r'<td (?:style="([^"]*)" )?class="gt_row[^"]*"[^>]*>(.*?)</td>', re.S)
STUB = re.compile(r'<th (?:style="([^"]*)" )?class="gt_row[^"]*gt_stub[^"]*"[^>]*>(.*?)</th>', re.S)


def frame(lib, data):
    """``data`` as a polars frame, or a pandas frame with a non-default index (positions must not use labels)."""
    if lib == "pandas":
        n = len(next(iter(data.values())))
        return pd.DataFrame(data, index=[10 * (i + 1) for i in range(n)])
    return pl.DataFrame(data, strict=False)


def body_rows(gt, pattern=TD):
    """One list per rendered body row of ``(style, text)`` for each body cell (``STUB`` reads the stub instead)."""
    html = gt.as_raw_html()
    body = html[html.index("<tbody") : html.index("</tbody>")]
    rows = [pattern.findall(tr) for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S)]
    return [r for r in rows if r]

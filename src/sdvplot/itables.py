"""itables styling (``pip install sdvplot[itables]``): a surveyed table theme as DataTables CSS and ``show`` options.

The function only builds strings. Show the CSS once, then pass the rest to ``itables.show``.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from sdvplot._errors import InputError, requires_extra

with requires_extra("itables"):
    import itables as _itables  # noqa: F401  (the extra guard: this module is for itables users)

from sdvplot._table_themes import _font_stack, table_theme_spec

__all__ = ["itables_sdv_theme"]


def __dir__() -> list[str]:  # dir() and tab completion show the public API only
    return list(__all__)


_ID = re.compile(r"^[A-Za-z][\w-]*$")


def itables_sdv_theme(
    name: str, *, mode: Literal["light", "dark"] = "light", table_id: str = "sdv-itable"
) -> dict[str, str]:
    """Style an itables table like any of the 122 surveyed themes.

    Args:
        name: The theme id, as listed by ``sdv_table_themes()``.
        mode: ``"light"`` or ``"dark"``.
        table_id: The DOM id the CSS is scoped to; pass the same value to ``show(table_id=...)``. A letter first,
            then letters, digits, ``_`` or ``-``.

    Returns:
        dict: ``classes`` and ``style`` (the ``itables.show`` keywords of those names), and ``css``: a Google Fonts
        ``@import`` then rules, each scoped to ``#<table_id>``. Show the CSS before the table.

    Raises:
        InputError: For an invalid ``table_id``, an unknown ``name`` or ``mode``, or ``mode="dark"`` on a light-only
            theme.

    Example:
        ::

            import pandas as pd
            from IPython.display import HTML, display
            from itables import show
            from sdvplot.itables import itables_sdv_theme

            df = pd.DataFrame({"team": ["KC", "BUF"], "wins": [15, 13]})
            t = itables_sdv_theme("datagolf")
            display(HTML(f"<style>{t['css']}</style>"))
            show(df, table_id="sdv-itable", classes=t["classes"], style=t["style"])

    See Also:
        table_theme_spec: the resolved theme this reads
    """
    if not _ID.match(table_id):
        raise InputError(f"table_id must be a CSS identifier (a letter, then letters, digits, _, -), got {table_id!r}")
    s = table_theme_spec(name, mode)
    p, st, f, z = s.palette, s.structure, s.fonts, s.sizes  # palette, structure, fonts, sizes
    sel = f"#{table_id}"
    weight = {"label": f.get("labelWeight"), "body": f.get("bodyWeight")}
    families = sorted({x for x in (f.get("title"), f.get("label"), f.get("body")) if x})
    imports = "".join(
        f'@import url("https://fonts.googleapis.com/css2?family={x.replace(" ", "+")}&display=swap");\n'
        for x in families
    )

    def rule(selector: str, **decl: Any) -> str:
        body = "; ".join(f"{k.replace('_', '-')}: {v}" for k, v in decl.items() if v is not None)
        return f"{selector} {{ {body}; }}\n"

    head: dict[str, Any] = {
        "background": p["labelBg"],
        "color": p["labelColor"],
        "font_family": _font_stack(f.get("label")),
        "font_size": f"{z['label']}px",
        "font_weight": weight["label"],
        "text_transform": st.get("labelTransform"),
        "letter_spacing": st.get("labelTracking"),
        "padding": f"{z['padY']}px {z['padX']}px",
        "border_top": st.get("labelBorderTop"),
        "border_bottom": st.get("labelBorderBottom"),
    }
    cells: dict[str, Any] = {
        "background": p["bg"],
        "color": p["text"],
        "padding": f"{z['padY']}px {z['padX']}px",
        "border_bottom": st["rowRule"],
        "border_left": st["colRule"],
    }
    css = imports + rule(
        sel,
        **{"--sdv-hline": p["hline"]},
        background=p["bg"],
        color=p["text"],
        font_family=_font_stack(f.get("body")),
        font_size=f"{z['body']}px",
        font_weight=weight["body"],
        border_top=st.get("tableBorderTop"),
        border_bottom=st.get("tableBorderBottom"),
    )
    css += rule(f"{sel} thead th", **head) + rule(f"{sel} tbody td", **cells)
    # stripe the 2nd, 4th, ... body rows, as gt, sdvtables and the other adapters do. DataTables' own "stripe" class
    # shades the 1st, 3rd, ... (its "odd" rows), so it is never set.
    if st["stripe"]:
        css += rule(f"{sel} tbody tr:nth-child(even) td", background=p["stripe"])
    classes = ["nowrap"] + (["compact"] if z["padY"] <= 4 else [])
    return {"classes": " ".join(classes), "style": f"background: {p['bg']}; color: {p['text']}", "css": css}

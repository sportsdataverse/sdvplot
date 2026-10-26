---
title: sdvplot.itables
sidebar_label: sdvplot.itables
sidebar_position: 29
---

# sdvplot.itables

itables styling (``pip install sdvplot[itables]``): a surveyed table theme as DataTables CSS and ``show`` options.

| Name | What it is |
|---|---|
| [itables_sdv_theme](#itables_sdv_theme) | Style an itables table like any of the 122 surveyed themes. |

## itables_sdv_theme

<div class="sdv-signature">

```python
itables_sdv_theme(
    name: str,
    *,
    mode: Literal['light', 'dark'] = 'light',
    table_id: str = 'sdv-itable',
) -> dict[str, str]
```

</div>

Style an itables table like any of the 122 surveyed themes.

### Arguments

| Name | Type | Description |
|---|---|---|
| `name` | `str` | The theme id, as listed by ``sdv_table_themes()``. |
| `mode` | `Literal['light', 'dark']` | ``"light"`` or ``"dark"``. |
| `table_id` | `str` | The DOM id the CSS is scoped to; pass the same value to ``show(table_id=...)``. A letter first, then letters, digits, ``_`` or ``-``. |

### Returns

`dict` — ``classes`` and ``style`` (the ``itables.show`` keywords of those names), and ``css``: a Google Fonts ``@import`` then rules, each scoped to ``#<table_id>``. Show the CSS before the table.

### Raises

- `InputError`: For an invalid ``table_id``, an unknown ``name`` or ``mode``, or ``mode="dark"`` on a light-only theme.

### Example

```python
import pandas as pd
from IPython.display import HTML, display
from itables import show
from sdvplot.itables import itables_sdv_theme

df = pd.DataFrame({"team": ["KC", "BUF"], "wins": [15, 13]})
t = itables_sdv_theme("datagolf")
display(HTML(f"<style>{t['css']}</style>"))
show(df, table_id="sdv-itable", classes=t["classes"], style=t["style"])
```

### See also

- table_theme_spec: the resolved theme this reads

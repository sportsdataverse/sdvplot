---
title: sdv_table_themes
sidebar_label: sdv_table_themes
sidebar_position: 32
---

# sdv_table_themes

<div class="sdv-signature">

```python
sdv_table_themes(
    mode: str | None = None,
    category: str | None = None,
) -> list[dict[str, str]]
```

</div>

List the surveyed table themes, optionally only those usable in a mode or in one category.

## Arguments

| Name | Type | Description |
|---|---|---|
| `mode` | `str \| None` | ``"dark"`` keeps only dark-capable themes; ``"light"`` or ``None`` keeps all. |
| `category` | `str \| None` | Keep only this category (e.g. ``"sports"``). |

## Returns

One dict per theme with ``id``, ``source``, ``category`` and ``dark_policy``.

## Raises

- `InputError`: If ``mode`` is not ``None``, ``"light"`` or ``"dark"``.

## Example

```python
from sdvplot import sdv_table_themes
print(len(sdv_table_themes(mode="dark")))
```

## See also

- table_theme_spec: resolve one theme

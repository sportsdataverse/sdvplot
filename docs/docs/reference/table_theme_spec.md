---
title: table_theme_spec
sidebar_label: table_theme_spec
sidebar_position: 29
---

# table_theme_spec

<div class="sdv-signature">

```python
table_theme_spec(
    name: str,
    mode: Literal['light', 'dark'] = 'light',
) -> sdvplot._table_themes.TableThemeSpec
```

</div>

Resolve a surveyed table theme (e.g. ``datagolf``, ``wikipedia``, ``nejm``) by its source name.

## Arguments

| Name | Type | Description |
|---|---|---|
| `name` | `str` | The theme id, as listed by ``sdv_table_themes()``. ``"espn"``, ``"fivethirtyeight"`` and ``"pff"`` are reactablefmtr ports (``reactable_sdv_theme``), not registry ids; the surveyed look of those sites is ``"espn-site"``, ``"fivethirtyeight-site"`` and ``"pff-site"``. |
| `mode` | `Literal['light', 'dark']` | ``"light"`` or ``"dark"``. Missing palette keys take the shared defaults. |

## Returns

The frozen spec, with the palette complete and every ``{key}`` in the structure's border strings replaced.

## Raises

- `InputError`: For an unknown name (with up to 3 close matches), a reactablefmtr name, an unknown ``mode``, or ``mode="dark"`` on a light-only theme (naming three dark-capable themes in the same category).

## Example

```python
from sdvplot import table_theme_spec
spec = table_theme_spec("datagolf", "dark")
print(spec.palette["bg"])
```

## See also

- sdv_table_themes: list the available ids
- reactable_sdv_theme: reactablefmtr's own 27 themes

---
title: sdvplot.testing
sidebar_label: sdvplot.testing
sidebar_position: 29
---

# sdvplot.testing

Shared behaviour every adapter must have. Adapter test suites call check_adapter_contract().

| Name | What it is |
|---|---|
| [check_adapter_contract](#check_adapter_contract) | Raise an AssertionError naming the broken rule if the adapter breaks the sdvplot adapter contract. |
| [check_table_adapter_contract](#check_table_adapter_contract) | Raise an AssertionError naming the broken rule (T0-T6) if a table adapter breaks the table contract. |

## check_adapter_contract

<div class="sdv-signature">

```python
check_adapter_contract(
    adapter: module,
    make_target: collections.abc.Callable[[], Any],
    *,
    league: str = 'nfl',
    known: tuple[str, str] = ('LV', 'LAR'),
    known_wordmarks: tuple[str, str] = ('LV', 'LAC'),
    players: tuple[str, str] = ('3139477', '4241479'),
    make_axis_target: collections.abc.Callable[[list[str]], Any] | None = None,
) -> None
```

</div>

Raise an AssertionError naming the broken rule if the adapter breaks the sdvplot adapter contract.

The rules, and the test hooks the adapter must expose, are in this module's docstring.

### Arguments

| Name | Type | Description |
|---|---|---|
| `adapter` | `module` | The adapter module under test (it exposes ``add_logos``, ``add_wordmarks``, ``add_headshots``, ``axis_logos`` and the ``_drawn_marks`` hook). |
| `make_target` | `collections.abc.Callable[[], Any]` | Builds a fresh target (a plot) to draw on each time it is called. |
| `league` | `str` | The SDV league key the checks run in. |
| `known` | `tuple[str, str]` | Two team ids of ``league`` that have logos. |
| `known_wordmarks` | `tuple[str, str]` | Two team ids of ``league`` that have wordmarks. |
| `players` | `tuple[str, str]` | Two player ids of ``league`` that have headshots. |
| `make_axis_target` | `collections.abc.Callable[[list[str]], Any] \| None` | ``make_axis_target(categories)`` builds a target whose x axis shows those categories, in order. Required when the adapter supports axis logos (rule 7). |

### Returns

`None` — Returns normally when every rule holds.

### Raises

- `AssertionError`: Naming the broken rule ("rule N: ..."), when the adapter breaks it.
- `UnsupportedTargetError`: (a TypeError) If no adapter is registered for the library of ``make_target()``'s object (register the adapter before checking it).
- `InputError`: (a ValueError) If ``league`` is unknown.
- `OfflineError`: If the logo manifest, which the checks read for the expected marks, is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status). A download error inside an adapter call is reported as the AssertionError of the rule that made the call.
- `UnsafeDownloadError`: (an OSError) If the manifest download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
import matplotlib.pyplot as plt
from sdvplot import matplotlib as adapter
from sdvplot.testing import check_adapter_contract

def make_target():
    _, ax = plt.subplots()
    ax.set_xlim(0, 30)
    ax.set_ylim(-10, 0)
    return ax

def make_axis_target(categories):
    _, ax = plt.subplots()
    ax.bar(categories, range(1, len(categories) + 1))
    return ax

check_adapter_contract(adapter, make_target=make_target, make_axis_target=make_axis_target)
```

### See also

- [Add an adapter](https://sdvplot.sportsdataverse.org/docs/adapters/add-an-adapter)
- sdvplot.testing.check_table_adapter_contract: the harness for table adapters

## check_table_adapter_contract

<div class="sdv-signature">

```python
check_table_adapter_contract(
    adapter: module,
    make_table: collections.abc.Callable[[Any], Any],
    *,
    league: str = 'nfl',
    known: tuple[str, str] = ('LV', 'LAR'),
    known_wordmarks: tuple[str, str] = ('LV', 'LAC'),
    players: tuple[str, str] = ('3139477', '4241479'),
) -> None
```

</div>

Raise an AssertionError naming the broken rule (T0-T6) if a table adapter breaks the table contract.

The rules and the ``_drawn_cells`` and ``_rendered_html`` hooks are in this module's docstring.

### Arguments

| Name | Type | Description |
|---|---|---|
| `adapter` | `module` | The table adapter module under test (it exposes ``add_logos``, ``add_wordmarks``, ``add_headshots`` and the two hooks). |
| `make_table` | `collections.abc.Callable[[Any], Any]` | ``make_table(frame)`` builds the adapter's table from a pandas or polars DataFrame (for great_tables: ``GT``). |
| `league` | `str` | The SDV league key the checks run in. |
| `known` | `tuple[str, str]` | Two team ids of ``league`` that have logos. |
| `known_wordmarks` | `tuple[str, str]` | Two team ids of ``league`` that have wordmarks. |
| `players` | `tuple[str, str]` | Two player ids of ``league`` that have headshots. |

### Returns

`None` — Returns normally when every rule holds.

### Raises

- `AssertionError`: Naming the broken rule ("rule T<n>: ..."), when the adapter breaks it.
- `InputError`: (a ValueError) If ``league`` is unknown.
- `OfflineError`: If the logo manifest, which the checks read for the expected marks, is neither cached nor downloadable (a DownloadError, also an OSError, when the CDN answers with an error status). A download error inside an adapter call is reported as the AssertionError of the rule that made the call.
- `UnsafeDownloadError`: (an OSError) If the manifest download is refused: larger than the byte cap, past the deadline, or redirected away from https.

### Example

```python
from great_tables import GT
from sdvplot import great_tables as adapter
from sdvplot.testing import check_table_adapter_contract

check_table_adapter_contract(adapter, make_table=GT)
```

### See also

- [Add an adapter](https://sdvplot.sportsdataverse.org/docs/adapters/add-an-adapter)
- sdvplot.testing.check_adapter_contract: the harness for plot adapters

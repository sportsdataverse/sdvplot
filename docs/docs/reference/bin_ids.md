---
title: bin_ids
sidebar_label: bin_ids
sidebar_position: 36
---

# bin_ids

<div class="sdv-signature">

```python
bin_ids(
    bins: collections.abc.Sequence[sdvplot._bins.Bin],
    n: int,
) -> list[str]
```

</div>

Each point's bin id: the column that links a point layer or a table row to the cell it is drawn in.

Every binned point is in exactly one bin, so this is the join key both ways: a selected cell's ``id`` picks its
rows (the rows whose bin id is that id), and a selected row picks its cell.

## Arguments

| Name | Type | Description |
|---|---|---|
| `bins` | `collections.abc.Sequence[sdvplot._bins.Bin]` | What ``hexbin``, ``squarebin``, ``binner(...).bins`` or an adapter's ``add_bins`` binned. |
| `n` | `int` | The number of points that were binned (``len(x)``). |

## Returns

`list[str]` — ``n`` strings: the ``id`` of the bin holding each row, or ``""`` for a row in no bin (a missing, NaN or infinite coordinate).

## Raises

- `ValueError`: If a bin holds a row outside ``range(n)``.

## Example

```python
import polars as pl
import sdvplot

shots = pl.DataFrame({"x": [0, -1, -44], "y": [0, 7, 252]})
bins = sdvplot.hexbin(shots["x"], shots["y"], radius=10)
shots.with_columns(bin_id=pl.Series(sdvplot.bin_ids(bins, shots.height)))
```

## See also

- [hexbin](https://sdvplot.sportsdataverse.org/docs/reference/hexbin)

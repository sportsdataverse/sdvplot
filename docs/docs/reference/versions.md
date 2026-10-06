---
title: versions
sidebar_label: versions
sidebar_position: 28
---

# versions

<div class="sdv-signature">

```python
versions() -> dict[str, str | None]
```

</div>

What a bug report needs: the package version, the bundled-index version, and the cached manifest's date.

## Returns

`dict[str, str | None]` — Keys ``sdvplot``, ``index`` and ``manifest_last_modified`` (None until the manifest has been downloaded).

## Example

```python
import sdvplot

sdvplot.versions()["sdvplot"]   # '0.1.0'
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)

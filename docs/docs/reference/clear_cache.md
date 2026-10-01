---
title: clear_cache
sidebar_label: clear_cache
sidebar_position: 15
---

# `clear_cache`

```python
clear_cache() -> None
```

Delete everything sdvplot has cached (manifest, images, rasterized SVGs).

The next call that needs a mark downloads it again. The cache directory is ``SDVPLOT_CACHE_DIR`` when set.

## Returns

`None` — Nothing; the cache subdirectories are removed.

## Example

```python
import sdvplot

sdvplot.clear_cache()   # the next logo_url() / logo_image() re-downloads
```

## See also

sdvplotR: https://sdvplotR.sportsdataverse.org/ ; sdv-py: https://py.sportsdataverse.org/

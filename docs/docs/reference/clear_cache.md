---
title: clear_cache
sidebar_label: clear_cache
sidebar_position: 29
---

# clear_cache

<div class="sdv-signature">

```python
clear_cache() -> None
```

</div>

Delete everything sdvplot has cached (manifest, images, rasters, nflverse, URL images such as headshots).

The next call that needs a mark downloads it again. The cache directory is ``SDVPLOT_CACHE_DIR`` when set. In the
default cache directory every subdirectory above is removed. In a directory you chose with ``SDVPLOT_CACHE_DIR``
only subdirectories sdvplot created (they hold a ``.sdvplot-cache`` marker) are removed; a folder of your own with
the same name is left alone with a warning that names it. A subdirectory that is a symlink is unlinked in the
default directory (what it points to is untouched) and left alone with a warning in one you chose.

## Returns

`None` — Nothing; the cache subdirectories are removed.

## Example

```python
import sdvplot

sdvplot.clear_cache()   # the next logo_url() / logo_image() re-downloads
```

## See also

- [sdvplotR](https://sdvplotR.sportsdataverse.org/)
- [sdv-py](https://py.sportsdataverse.org/)
